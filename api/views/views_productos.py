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
from api.views.utilis.general import obtener_ciudad_registro


@api_view(["GET"])
def producto_list(request):

    ciudad_registro = obtener_ciudad_registro(request)

    queryset = Producto.objects.filter(CIUDAD_REGISTRO=ciudad_registro).order_by("-id")

    serializer = ProductoSerializer(queryset, many=True)

    return Response(serializer.data)


@api_view(["POST"])
@transaction.atomic
def crear_producto(request):
    # 1. Crear producto

    data = request.data.copy()

    ciudad_registro = ciudad_registro = obtener_ciudad_registro(request)
    data["CIUDAD_REGISTRO"] = ciudad_registro

    serializer = ProductoSerializer(data=data)
    if serializer.is_valid():
        producto = serializer.save()

        # 2. Crear un precio cliente para cada cliente existente usando el precio del producto

        # Retrieving only the IDs of Cliente using .only("id") is generally efficient because it minimizes the amount of data loaded from the database. However, if you're interested solely in the IDs and not the Cliente model instances, fetching the IDs as a list using .values_list('id', flat=True) would be even more efficient. This is because .values_list() retrieves just the specified fields directly, without constructing model instances, which can save memory when dealing with a large number of objects.
        # clientes = Cliente.objects.only("id")
        cliente_ids = Cliente.objects.filter(
            CIUDAD_REGISTRO=ciudad_registro
        ).values_list("id", flat=True)

        # Crear una lista de objetos PrecioCliente para insertar en lote
        precios_clientes_instances = [
            PrecioCliente(
                # CLIENTE_id=cliente.id,
                CLIENTE_id=cliente_id,
                PRODUCTO=producto,
                PRECIO=producto.PRECIO,
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
@transaction.atomic
def modificar_producto(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        data = request.data.copy()  # Create a mutable copy of QueryDict
        precio = data.get("PRECIO")
        producto_id = data.get("productoId")
        del data["PRECIO"]

        serializer = ProductoSerializer(producto, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Aqui es donde voy a actualizar el precio de los clientes
            if data.get("update_price"):
                producto.PRECIO = precio
                actualizar_producto_precio(precio, producto_id)
                producto.save()
            return Response(serializer.data)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        producto.delete()
        return Response(
            {"message": "El producto fuel eliminado exitosamente"},
            status=status.HTTP_204_NO_CONTENT,
        )


def actualizar_producto_precio(precio, producto_id):
    # Update price for all clients in the database
    # Correction, update price for clients from the same CIUDAD_REGISTRO than product
    # I don't need to modify the code because this product_id only exist for clients from that CIUDAD_REGISTRO
    PrecioCliente.objects.filter(PRODUCTO__id=producto_id).update(PRECIO=precio)
