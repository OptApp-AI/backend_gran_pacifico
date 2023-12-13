from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from api.models import AjusteInventario, Producto
from api.serializers import AjusteInventarioSerializer


# I need to add pagination and filtering to this view
@api_view(["GET"])
def ajuste_inventario_list(request):
    ajuste_inventarios = (
        AjusteInventario.objects.select_related("PRODUCTO").all().order_by("-id")
    )

    serializer = AjusteInventarioSerializer(ajuste_inventarios, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@transaction.atomic  # Ensures atomic
def crear_ajuste_inventario(request):
    data = request.data

    try:
        producto = Producto.objects.get(id=data.get("PRODUCTO"))
    except Producto.DoesNotExist:
        return Response(
            {"message": "Producto con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = AjusteInventarioSerializer(data=data)
    if serializer.is_valid():
        # Validacion de suficiente cantidad en inventario
        tipo_ajuste = data.get("TIPO_AJUSTE")
        cantidad = data.get("CANTIDAD")

        # Validación para asegurar que producto.CANTIDAD no se vuelva negativo
        if tipo_ajuste == "FALTANTE" and producto.CANTIDAD < cantidad:
            return Response(
                {
                    "message": "No hay suficiente cantidad en el inventario para este ajuste."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        if tipo_ajuste == "FALTANTE":
            producto.CANTIDAD -= cantidad

        elif tipo_ajuste == "SOBRANTE":
            producto.CANTIDAD += cantidad

        producto.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
