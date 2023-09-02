from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from api.models import (
    Producto,
    Cliente,
    PrecioCliente,
)
from api.serializers import (
    ProductoSerializer,
    ClienteSerializer,
)


@api_view(["GET"])
def producto_list(request):
    queryset = Producto.objects.all().order_by("-id")

    serializer = ProductoSerializer(queryset, many=True)

    return Response(serializer.data)


@api_view(["POST"])
def crear_producto(request):
    # 1. Crear producto
    serializer = ProductoSerializer(data=request.data)
    if serializer.is_valid():
        producto = serializer.save()

        # 2. Crear un precio cliente para cada cliente existente usando el precio del producto
        queryset = Cliente.objects.all()

        # Creo que es necesario serializar para poder iterar sobre las instancias de Cliente
        clientes_serializer = ClienteSerializer(queryset, many=True)

        # Cuando iteres recuerda usar .data
        for cliente_serializer in clientes_serializer.data:
            precio_cliente = PrecioCliente.objects.create(
                CLIENTE=Cliente.objects.get(pk=cliente_serializer["id"]),
                PRODUCTO=producto,
                PRECIO=producto.PRECIO,  # Asignamos el precio default del producto a cada precio cliente
            )
            precio_cliente.save()

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
