from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from api.models import (
    Producto,
    Venta,
    ProductoVenta,
)
from api.serializers import (
    VentaSerializer,
    ProductoVentaSerializer,
)
from django.db.models import Case, When, Value, IntegerField
from django.utils.dateparse import parse_date
from django.db.models import Case, When, Value, IntegerField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta
from .utilis.ventas import filter_by_date
from django.db.models import Q
from django.core.cache import cache

# Vistas para ventas


@api_view(["GET"])
def venta_list(request):
    # Generate a unique cache key based on request parameters
    # any change in query parameters will produce a different URL-encoded string
    # cache_key = f"venta_list_{request.GET.urlencode()}"
    # cached_data = cache.get(cache_key)
    # if cached_data:
    #     return Response(cached_data, status=status.HTTP_200_OK)

    filtrar_por = request.GET.get("filtrarpor", "")
    buscar = request.GET.get("buscar", "")
    fechainicio = request.GET.get("fechainicio", "")
    fechafinal = request.GET.get("fechafinal", "")
    ordenar_por = request.GET.get("ordenarpor", "")
    page = request.GET.get("page", "")

    filters = Q()
    if filtrar_por and buscar:
        filters = Q(**{f"{filtrar_por.upper()}__icontains": buscar})

    queryset = (
        Venta.objects.select_related("CLIENTE")
        .prefetch_related("productos_venta")
        .filter(filters)
    )

    queryset = filter_by_date(queryset, fechainicio, fechafinal)

    ordering_dict = {
        "cliente": "NOMBRE_CLIENTE",
        "fecha_recientes": "-FECHA",
        "fecha_antiguos": "FECHA",
        "vendedor": "VENDEDOR",
    }
    queryset = queryset.order_by(ordering_dict.get(ordenar_por, "-id"))

    paginator = Paginator(queryset, 10)
    try:
        ventas = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        ventas = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        ventas = paginator.page(page)

    serializer = VentaSerializer(ventas, many=True)

    response_data = {
        "ventas": serializer.data,
        "page": page,
        "pages": paginator.num_pages,
    }

    # Cache the result
    # cache.set(cache_key, response_data, 60 * 15)  # Cache for 15 minutes

    # Keep track of all cache keys related to venta
    # cache_keys = cache.get("venta_cache_keys", [])
    # cache_keys.append(cache_key)
    # cache.set("venta_cache_keys", cache_keys)

    return Response(response_data, status=status.HTTP_200_OK)


# Vistas para ventas
@api_view(["GET"])
def venta_reporte_list(request):
    # Generate cache key
    # cache_key = f"venta_reporte_list_{request.GET.urlencode()}"

    # Check for cached data
    # cached_data = cache.get(cache_key)
    # if cached_data:
    #     return Response(cached_data, status=status.HTTP_200_OK)

    # Existing logic for filters
    filtrar_por = request.GET.get("filtrarpor", "")
    buscar = request.GET.get("buscar", "")
    fechainicio = request.GET.get("fechainicio", "")
    fechafinal = request.GET.get("fechafinal", "")
    ordenar_por = request.GET.get("ordenarpor", "")

    filters = Q()
    if filtrar_por and buscar:
        filters = Q(**{f"{filtrar_por}__icontains": buscar})

    queryset = (
        Venta.objects.select_related("CLIENTE")
        .prefetch_related("productos_venta")
        .filter(filters)
    )

    queryset = filter_by_date(queryset, fechainicio, fechafinal)

    ordering_dict = {
        "cliente": "NOMBRE_CLIENTE",
        "fecha_recientes": "-FECHA",
        "fecha_antiguos": "FECHA",
        "vendedor": "VENDEDOR",
    }
    queryset = queryset.order_by(ordering_dict.get(ordenar_por, "-id"))

    # Serialize the queryset
    serializer = VentaSerializer(queryset, many=True)
    response_data = serializer.data

    # Cache the result
    # cache.set(cache_key, response_data, 60 * 15)  # Cache for 15 minutes

    # # Keep track of all cache keys related to venta_reporte
    # cache_keys = cache.get("venta_reporte_cache_keys", [])
    # cache_keys.append(cache_key)
    # cache.set("venta_reporte_cache_keys", cache_keys)

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
def crear_venta(request):
    data = request.data

    serializer = VentaSerializer(data=data)

    if serializer.is_valid():
        venta = serializer.save()

        productos_venta = data["productosVenta"]

        print("PRODUCTOS VENTA:-------", productos_venta)

        for producto_venta in productos_venta:
            producto = Producto.objects.get(pk=producto_venta["productoId"])

            nuevo_producto_venta = ProductoVenta.objects.create(
                VENTA=venta,
                PRODUCTO=producto,
                NOMBRE_PRODUCTO=producto.NOMBRE,
                CANTIDAD_VENTA=producto_venta["cantidadVenta"],
                PRECIO_VENTA=producto_venta["precioVenta"],
            )

            if data["STATUS"] == "REALIZADO":
                producto.CANTIDAD -= nuevo_producto_venta.CANTIDAD_VENTA
                producto.save()

            nuevo_producto_venta.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    print("ERRORES:", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def venta_detail(request, pk):
    try:
        venta = Venta.objects.get(pk=pk)

    except Venta.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = VentaSerializer(venta)
    return Response(serializer.data)


@api_view(["PUT", "DELETE"])
def modificar_venta(request, pk):
    try:
        venta = Venta.objects.get(pk=pk)

    except Venta.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        reporte_cambios = {}

        data = request.data

        status_actual = venta.STATUS
        status_cambios = {"ANTES": status_actual}

        status_nuevo = data["STATUS"]

        productos_venta = venta.productos_venta

        serializer = ProductoVentaSerializer(productos_venta, many=True)

        for producto_venta_serializer in serializer.data:
            producto = Producto.objects.get(
                NOMBRE=producto_venta_serializer["NOMBRE_PRODUCTO"]
            )

            producto_cambios = {"ANTES": producto.CANTIDAD}

            cantidad_venta = producto_venta_serializer["CANTIDAD_VENTA"]

            producto.CANTIDAD = calcular_cantidad(
                status_actual, status_nuevo, producto.CANTIDAD, cantidad_venta
            )
            producto.save()
            producto_cambios["DESPUES"] = producto.CANTIDAD

            reporte_cambios[producto.NOMBRE] = producto_cambios

        venta.STATUS = status_nuevo
        venta.save()
        status_cambios["DESPUES"] = venta.STATUS
        reporte_cambios["STATUS"] = status_cambios

        return Response(reporte_cambios)

    elif request.method == "DELETE":
        venta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def calcular_cantidad(status_actual, status, cantidad_antes, cantidad_venta):
    if status_actual == "PENDIENTE":
        if status == "REALIZADO":
            return cantidad_antes - cantidad_venta
        else:
            return cantidad_antes
    elif status_actual == "REALIZADO":
        if status in ["PENDIENTE", "CANCELADO"]:
            return cantidad_antes + cantidad_venta
        else:
            return cantidad_antes
    else:
        return cantidad_antes
