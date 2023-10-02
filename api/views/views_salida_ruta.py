from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.db import transaction  # Import the transaction module

from api.models import (
    SalidaRuta,
    ProductoSalidaRuta,
    ClienteSalidaRuta,
    Cliente,
    Producto,
    RutaDia,
)
from api.serializers import SalidaRutaSerializer


@api_view(["GET"])
def salida_ruta_list(request):
    queryset = SalidaRuta.objects.all().order_by("-id")

    serializer = SalidaRutaSerializer(queryset, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def salida_ruta_detail(request, pk):
    try:
        salida_ruta = SalidaRuta.objects.get(pk=pk)
    except SalidaRuta.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = SalidaRutaSerializer(salida_ruta)

    return Response(serializer.data)


# Use transaction.atomic to make sure that all the database changes are atomic. This ensures that either all changes are committed, or if an error occurs, all changes are rolled back


@api_view(["PUT"])
@transaction.atomic  # Use the atomic decorator to make sure all DB changes are made atomically
def cancelar_salida_ruta(request, pk):
    print("PKKK", pk)
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

    # Cancel all associated ProductoSalidaRuta instances and revert stock
    for producto_salida in salida_ruta.productos.all():
        producto_salida.STATUS = "CANCELADO"
        producto_salida.save()

        # Revert stock
        producto = producto_salida.PRODUCTO_RUTA
        producto.CANTIDAD += producto_salida.CANTIDAD_RUTA
        producto.save()

    # Cancel all associated ClientesSalidaRuta instances
    for cliente_salida in salida_ruta.clientes.all():
        cliente_salida.STATUS = "CANCELADO"
        cliente_salida.save()

    return Response(
        {
            "message": "La salida ruta y todos los productos y clientes asociados han sido cancelados exitosamente"
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def crear_salida_ruta(request):
    data = request.data

    serializer = SalidaRutaSerializer(data=data)

    if serializer.is_valid():
        salida_ruta = serializer.save()

        # Generar ProductoSalidaRuta
        salida_ruta_productos = data["salidaRutaProductos"]

        for salida_ruta_producto in salida_ruta_productos:
            producto = Producto.objects.get(pk=salida_ruta_producto["productoId"])

            producto_salida_ruta = ProductoSalidaRuta.objects.create(
                SALIDA_RUTA=salida_ruta,
                PRODUCTO_RUTA=producto,
                CANTIDAD_RUTA=salida_ruta_producto["cantidadSalidaRuta"],
                CANTIDAD_DISPONIBLE=salida_ruta_producto["cantidadSalidaRuta"],
                STATUS="CARGADO",
            )

            producto.CANTIDAD -= producto_salida_ruta.CANTIDAD_RUTA
            producto.save()
            producto_salida_ruta.save()

        # Generar ClienteSalidaRuta
        salida_ruta_clientes = data["salidaRutaClientes"]

        for salida_ruta_cliente in salida_ruta_clientes:
            cliente_salida_ruta = ClienteSalidaRuta.objects.create(
                SALIDA_RUTA=salida_ruta,
                CLIENTE_RUTA=Cliente.objects.get(id=salida_ruta_cliente["clienteId"]),
                STATUS="PENDIENTE",
            )

            cliente_salida_ruta.save()

        return Response(serializer.data)
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
