from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.db import transaction  # Import the transaction module
from django.db.models import Prefetch


from api.models import (
    ProductoVenta,
    SalidaRuta,
    ProductoSalidaRuta,
    ClienteSalidaRuta,
    Cliente,
    Producto,
)
from api.serializers import (
    DevolucionSalidaRutaSerializer,
    SalidaRutaSerializer,
    VentaSerializer,
)


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


@api_view(["POST"])
@transaction.atomic
def crear_venta_salida_ruta(request, pk):
    data = request.data

    # 1. Valida data for creating venta
    serializer = VentaSerializer(data=data)
    if serializer.is_valid():
        venta = serializer.save()

        # 2. Create ProductoVenta instances
        productos_venta = data["productosVenta"]
        productos_ids = [
            producto_venta["PRODUCTO_RUTA"] for producto_venta in productos_venta
        ]
        producto_instances = Producto.objects.filter(id__in=productos_ids).only(
            "id", "NOMBRE"
        )
        producto_cantidad_venta_map = {
            producto_venta["PRODUCTO_RUTA"]: producto_venta["cantidadVenta"]
            for producto_venta in productos_venta
        }
        producto_precio_venta_map = {
            producto_venta["PRODUCTO_RUTA"]: producto_venta["precioVenta"]
            for producto_venta in productos_venta
        }
        producto_venta_instances = [
            ProductoVenta(
                VENTA=venta,
                PRODUCTO=producto,
                NOMBRE_PRODUCTO=producto.NOMBRE,
                CANTIDAD_VENTA=producto_cantidad_venta_map[producto.id],
                PRECIO_VENTA=producto_precio_venta_map[producto.id],
            )
            for producto in producto_instances
        ]

        ProductoVenta.objects.bulk_create(producto_venta_instances)

        # 3. Actualizar cliente salida ruta
        ClienteSalidaRuta.objects.filter(
            SALIDA_RUTA=pk, CLIENTE_RUTA=data.get("CLIENTE")
        ).update(STATUS="VISITADO")

        # 4. Actualizar productos salida ruta

        productos_salida_ruta_instances = ProductoSalidaRuta.objects.filter(
            SALIDA_RUTA=pk, PRODUCTO_RUTA__in=productos_ids
        )
        for product_salida_ruta in productos_salida_ruta_instances:
            product_salida_ruta.CANTIDAD_DISPONIBLE -= producto_cantidad_venta_map[
                product_salida_ruta.PRODUCTO_RUTA.id
            ]

            if product_salida_ruta.CANTIDAD_DISPONIBLE == 0:
                product_salida_ruta.STATUS = "VENDIDO"

        ProductoSalidaRuta.objects.bulk_update(
            productos_salida_ruta_instances, ["CANTIDAD_DISPONIBLE", "STATUS"]
        )

        # Obtener todos los  productos de la salida ruta
        salida_ruta = SalidaRuta.objects.get(id=pk)
        clientes_salida_ruta = ClienteSalidaRuta.objects.filter(SALIDA_RUTA=salida_ruta)
        productos_salida_ruta = ProductoSalidaRuta.objects.filter(
            SALIDA_RUTA=salida_ruta
        )

        # Verificar si el STATUS de todos los clientes salida ruta es VISITADO
        all_clientes_visited = all(
            cliente.STATUS == "VISITADO" for cliente in clientes_salida_ruta
        )

        # Verificar si el STATUS de todos los productos salida ruta es VENDIDO
        all_productos_sold = all(
            producto.STATUS == "VENDIDO" for producto in productos_salida_ruta
        )

        # Si esto se cumple cambia el STATUS de salida ruta a realizado
        if all_productos_sold and all_clientes_visited:
            salida_ruta.STATUS = "REALIZADO"
        # Si no se cumple verifica si el STATUS de salida ruta es PENDIENTE
        elif salida_ruta.STATUS == "PENDIENTE":
            # Si esto se cumple cambia el STATUS de salida ruta de PROGRESO
            salida_ruta.STATUS = "PROGRESO"

        salida_ruta.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@transaction.atomic
def devolver_producto_salida_ruta(request, pk):
    salida_ruta = SalidaRuta.objects.get(id=pk)

    try:
        assert salida_ruta.STATUS == "PROGRESO"
    except AssertionError:
        return Response(
            {
                "message": "El STATUS de salida ruta debe ser PROGRESO para poder realizar una devolución"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data

    # 1. Crear devolucion
    serializer = DevolucionSalidaRutaSerializer(data=data)

    if serializer.is_valid():
        serializer.save()

        producto_salida_ruta = ProductoSalidaRuta.objects.get(
            id=data.get("PRODUCTO_DEVOLUCION"), SALIDA_RUTA=data.get("SALIDA_RUTA")
        )

        producto_salida_ruta.CANTIDAD_DISPONIBLE -= data.get("CATIDAD_DEVOLUCION")

        # Revisar si con los productos devueltos ya no hay mas productos disponibles
        if producto_salida_ruta.CANTIDAD_DISPONIBLE == 0:
            producto_salida_ruta.STATUS = "VENDIDO"

        producto_salida_ruta.save()

        # Obtener todos los  productos de la salida ruta

        productos_salida_ruta = ProductoSalidaRuta.objects.filter(
            SALIDA_RUTA=salida_ruta
        )

        # Verificar si el STATUS de todos los productos salida ruta es VENDIDO
        all_productos_sold = all(
            producto.STATUS == "VENDIDO" for producto in productos_salida_ruta
        )

        # Si esto se cumple cambia el STATUS de salida ruta a realizado
        if all_productos_sold:
            salida_ruta.STATUS = "REALIZADO"

        return Response(serializer.data, status=status.HTTP_200_OK)

    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@transaction.atomic
def realizar_aviso_visita(request, pk):
    salida_ruta = SalidaRuta.objects.get(id=pk)

    try:
        assert salida_ruta.STATUS == "PROGRESO"
    except AssertionError:
        return Response(
            {
                "message": "El STATUS de salida ruta debe ser PROGRESO para poder realizar un aviso de visita"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data

    print("DATA", data)
    print("PK", pk)

    try:
        cliente_salida_ruta = ClienteSalidaRuta.objects.get(
            id=data.get("CLIENTE_SALIDA_RUTA")
        )
    except ClienteSalidaRuta.DoesNotExist:
        return Response(
            {"message": "Cliente salida ruta con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        assert cliente_salida_ruta.STATUS == "PENDIENTE"
    except AssertionError:
        return Response(
            {"message": "Cliente salida ruta debe tener STATUS de PENDIENTE"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cliente_salida_ruta.STATUS = "VISITADO"

    cliente_salida_ruta.save()

    clientes_salida_ruta = ClienteSalidaRuta.objects.filter(SALIDA_RUTA=salida_ruta)

    # Verificar si el STATUS de todos los clientes salida ruta es VISITADO
    all_clientes_visited = all(
        cliente.STATUS == "VISITADO" for cliente in clientes_salida_ruta
    )

    # Si esto se cumple cambia el STATUS de salida ruta a realizado
    if all_clientes_visited:
        salida_ruta.STATUS = "REALIZADO"

    return Response(
        {"message": "La salida ruta ha sido actualizada exitosamente"},
        status=status.HTTP_200_OK,
    )

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
