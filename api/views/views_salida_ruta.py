from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.db import transaction  # Import the transaction module
from django.db.models import Prefetch


from api.models import (
    SalidaRuta,
    ProductoSalidaRuta,
    ClienteSalidaRuta,
    Cliente,
    Producto,
)
from api.serializers import SalidaRutaSerializer


@api_view(["GET"])
def salida_ruta_list(request):
    productos_salida_ruta_prefetch = Prefetch(
        "productos", queryset=ProductoSalidaRuta.objects.select_related("PRODUCTO_RUTA")
    )

    clientes_salida_ruta_prefetch = Prefetch(
        "clientes", queryset=ClienteSalidaRuta.objects.select_related("CLIENTE_RUTA")
    )
    queryset = (
        SalidaRuta.objects.select_related("RUTA", "REPARTIDOR")
        .prefetch_related(productos_salida_ruta_prefetch, clientes_salida_ruta_prefetch)
        .all()
        .order_by("-id")
    )

    serializer = SalidaRutaSerializer(queryset, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def salida_ruta_detail(request, pk):
    try:
        productos_salida_ruta_prefetch = Prefetch(
            "productos",
            queryset=ProductoSalidaRuta.objects.select_related("PRODUCTO_RUTA"),
        )

        clientes_salida_ruta_prefetch = Prefetch(
            "clientes",
            queryset=ClienteSalidaRuta.objects.select_related("CLIENTE_RUTA"),
        )
        salida_ruta = (
            SalidaRuta.objects.select_related("RUTA", "REPARTIDOR")
            .prefetch_related(
                productos_salida_ruta_prefetch, clientes_salida_ruta_prefetch
            )
            .get(pk=pk)
        )
    except SalidaRuta.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = SalidaRutaSerializer(salida_ruta)

    return Response(serializer.data)


# Use transaction.atomic to make sure that all the database changes are atomic. This ensures that either all changes are committed, or if an error occurs, all changes are rolled back

# The reason why i will delete the clientes and products associated with a cancelled salida ruta is because i want to make more efficient the fetchinh process when requesting all salida rutas


@api_view(["PUT"])
@transaction.atomic  # Use the atomic decorator to make sure all DB changes are made atomically
def cancelar_salida_ruta(request, pk):
    try:
        salida_ruta = SalidaRuta.objects.get(pk=pk)
    except SalidaRuta.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        assert salida_ruta.STATUS == "PENDIENTE"

    except AssertionError:
        return Response(
            {
                "message": "El STATUS de salida ruta debe ser pendiente para que pueda ser cancelado"
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Cancel the SalidaRuta instance
    salida_ruta.STATUS = "CANCELADO"
    salida_ruta.save()

    # Retrieve associated ProductSalidaRutaand ClienteSalidaRuta instances
    productos_salida = list(salida_ruta.productos.all())
    clientes_salida = list(salida_ruta.clientes.all())

    # Update stock for each Producto
    productos_to_update = []
    for producto_salida in productos_salida:
        producto = producto_salida.PRODUCTO_RUTA
        producto.CANTIDAD += producto_salida.CANTIDAD_RUTA
        productos_to_update.append(producto)

    # Bulk update Productos and delete ProductoSalidaRuta and ClienteSalidaRuta instances
    Producto.objects.bulk_update(productos_to_update, ["CANTIDAD"])
    ProductoSalidaRuta.objects.filter(id__in=[p.id for p in productos_salida]).delete()
    ClienteSalidaRuta.objects.filter(id__in=[c.id for c in clientes_salida]).delete()

    return Response(
        {
            "message": "La salida ruta ha sido cancelada y los productos y clientes asociados han sido eliminados de la salida ruta"
        },
        status=status.HTTP_200_OK,
    )


# Stock Quantity Validation: Before subtracting quantities from Producto.CANTIDAD, it's advisable to validate that there's enough stock available. This prevents negative stock values.


@api_view(["POST"])
@transaction.atomic
def crear_salida_ruta(request):
    data = request.data

    serializer = SalidaRutaSerializer(data=data)

    if serializer.is_valid():
        salida_ruta = serializer.save()

        # Get data to create productos salida ruta
        salida_ruta_productos_data = data["salidaRutaProductos"]

        producto_ids = [
            producto["productoId"] for producto in salida_ruta_productos_data
        ]

        productos_to_update_instances = Producto.objects.filter(id__in=producto_ids)

        productos_to_create_instances = []

        producto_cantidad_map = {
            producto["productoId"]: producto["cantidadSalidaRuta"]
            for producto in salida_ruta_productos_data
        }

        for producto in productos_to_update_instances:
            cantidad_ruta = producto_cantidad_map[producto.id]
            nuevo_producto_salida_ruta = ProductoSalidaRuta(
                SALIDA_RUTA=salida_ruta,
                PRODUCTO_RUTA=producto,
                PRODUCTO_NOMBRE=producto.NOMBRE,
                CANTIDAD_RUTA=cantidad_ruta,
                CANTIDAD_DISPONIBLE=cantidad_ruta,
                STATUS="CARGADO",
            )

            productos_to_create_instances.append(nuevo_producto_salida_ruta)

            producto.CANTIDAD -= cantidad_ruta

        # Update productos
        Producto.objects.bulk_update(productos_to_update_instances, ["CANTIDAD"])
        # Create productos salida ruta
        ProductoSalidaRuta.objects.bulk_create(productos_to_create_instances)

        # Get data to create clientes salida ruta
        salida_ruta_clientes_data = data["salidaRutaClientes"]

        cliente_ids = [cliente["clienteId"] for cliente in salida_ruta_clientes_data]

        cliente_instances = Cliente.objects.filter(id__in=cliente_ids)

        clientes_to_create = []
        for cliente in cliente_instances:
            nuevo_cliente_salida_ruta = ClienteSalidaRuta(
                SALIDA_RUTA=salida_ruta,
                CLIENTE_RUTA=cliente,
                CLIENTE_NOMBRE=cliente.NOMBRE,
                STATUS="PENDIENTE",
            )

            clientes_to_create.append(nuevo_cliente_salida_ruta)

        ClienteSalidaRuta.objects.bulk_create(clientes_to_create)

        return Response(serializer.data)
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # # Cancel all associated ProductoSalidaRuta instances and revert stock
    # for producto_salida in salida_ruta.productos.all():
    #     producto_salida.STATUS = "CANCELADO"
    #     producto_salida.save()

    #     # Revert stock
    #     producto = producto_salida.PRODUCTO_RUTA
    #     producto.CANTIDAD += producto_salida.CANTIDAD_RUTA
    #     producto.save()

    # # Cancel all associated ClientesSalidaRuta instances
    # for cliente_salida in salida_ruta.clientes.all():
    #     cliente_salida.STATUS = "CANCELADO"
    #     cliente_salida.save()
