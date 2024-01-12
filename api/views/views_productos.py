from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.db import transaction

from api.models import (
    Producto,
    Cliente,
    PrecioCliente,
)
from api.serializers import (
    ProductoSerializer,
)


@api_view(["GET"])
def producto_list(request):
    queryset = Producto.objects.all().order_by("-id")

    serializer = ProductoSerializer(queryset, many=True)

    return Response(serializer.data)


@api_view(["POST"])
@transaction.atomic
def crear_producto(request):
    # 1. Crear producto
    serializer = ProductoSerializer(data=request.data)
    if serializer.is_valid():
        producto = serializer.save()

        # 2. Crear un precio cliente para cada cliente existente usando el precio del producto

        # Retrieving only the IDs of Cliente using .only("id") is generally efficient because it minimizes the amount of data loaded from the database. However, if you're interested solely in the IDs and not the Cliente model instances, fetching the IDs as a list using .values_list('id', flat=True) would be even more efficient. This is because .values_list() retrieves just the specified fields directly, without constructing model instances, which can save memory when dealing with a large number of objects.
        # clientes = Cliente.objects.only("id")
        cliente_ids = Cliente.objects.values_list("id", flat=True)

        # Crear una lista de objetos PrecioCliente para insertar en lote
        precios_clientes_instances = [
            PrecioCliente(
                # CLIENTE_id=cliente.id,
                CLIENTE_id=cliente_id,
                PRODUCTO=producto,
                PRECIO=producto.PRECIO
                # CLIENTE=cliente, PRODUCTO=producto, PRECIO=producto.PRECIO
            )
            # for cliente in clientes
            for cliente_id in cliente_ids
        ]

        PrecioCliente.objects.bulk_create(precios_clientes_instances)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def producto_detail(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return Response(
            {"message": "El producto con el i dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ProductoSerializer(producto)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "DELETE"])
def modificar_producto(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        # Aqui es donde voy a actualizar el precio de cliente MOSTRADOR Y RUTA (si existen)
        serializer = ProductoSerializer(producto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        producto.delete()
        return Response(
            {"message": "El producto fuel eliminado exitosamente"},
            status=status.HTTP_204_NO_CONTENT,
        )
