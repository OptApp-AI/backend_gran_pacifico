from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from api.models import AjusteInventario, Producto
from api.serializers import AjusteInventarioSerializer, AjusteInventarioReporteSerializer
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .utilis.ventas import filter_by_date


# I need to add pagination and filtering to this view
@api_view(["GET"])
def ajuste_inventario_list(request):
    filtrar_por = request.GET.get("filtrarpor", "")
    buscar = request.GET.get("buscar", "")
    fechainicio = request.GET.get("fechainicio", "")
    fechafinal = request.GET.get("fechafinal", "")
    ordenar_por = request.GET.get("ordenarpor", "")
    page = request.GET.get("page", "")

    filters = Q()
    if filtrar_por and buscar:
        filters = Q(**{f"{filtrar_por.upper()}__icontains": buscar})

    queryset = AjusteInventario.objects.select_related("PRODUCTO").filter(filters)

    queryset = filter_by_date(queryset, fechainicio, fechafinal)

    ordering_dict = {
        "cajero": "CAJERO",
        "bodega": "BODEGA",
        "administrador": "ADMINISTRADOR",
        "fecha_recientes": "-FECHA",
        "fecha_antiguos": "FECHA",
        "vendedor": "VENDEDOR",
    }
    queryset = queryset.order_by(ordering_dict.get(ordenar_por, "-id"))

    # Pagination
    paginator = Paginator(queryset, 10)

    try:
        ajuste_inventario = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        ajuste_inventario = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        ajuste_inventario = paginator.page(page)

    serializer = AjusteInventarioSerializer(ajuste_inventario, many=True)

    response_data = {
        "ajustes_inventario": serializer.data,
        "page": page,
        "pages": paginator.num_pages,
    }

    return Response(response_data, status=status.HTTP_200_OK)


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




# Vistas para ventas
@api_view(["GET"])
def ajuste_inventario_reporte_list(request):

    # Existing logic for filters
    filtrar_por = request.GET.get("filtrarpor", "")
    buscar = request.GET.get("buscar", "")
    fechainicio = request.GET.get("fechainicio", "")
    fechafinal = request.GET.get("fechafinal", "")
    ordenar_por = request.GET.get("ordenarpor", "")

    # const url = `/ajuste-inventarios?filtrarpor=${filtrarPor}&buscar=${buscar}&ordenarpor=${ordenarPor}&fechainicio=${fechaInicio}&fechafinal=${fechaFinal}`;

    filters = Q()
    if filtrar_por and buscar:
        filters = Q(**{f"{filtrar_por.upper()}__icontains": buscar})

    queryset = AjusteInventario.objects.only(
        "id",
        "CAJERO",
        "BODEGA",
        "ADMINISTRADOR",
        "PRODUCTO",
        "PRODUCTO_NOMBRE",
        "CANTIDAD",
        "TIPO_AJUSTE",
        "STATUS",
        "FECHA",
        "OBSERVACIONES",
        ).filter(filters)

    queryset = filter_by_date(queryset, fechainicio, fechafinal)

    ordering_dict = {
        "cajero": "CAJERO",
        "bodega": "BODEGA",
        "administrador": "ADMINISTRADOR",
        "fecha_recientes": "-FECHA",
        "fecha_antiguos": "FECHA"
    }
    queryset = queryset.order_by(ordering_dict.get(ordenar_por, "-id"))

    # Serialize the queryset
    serializer = AjusteInventarioReporteSerializer(queryset, many=True)
    response_data = serializer.data


    return Response(response_data, status=status.HTTP_200_OK)