from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from api.models import (
    Cliente,
    Producto,
    Venta,
    ProductoVenta,
)
from api.serializers import (
    VentaReporteSerializer,
    VentaSerializer,
)
from django.db.models import Case, When, Value, IntegerField
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta

from api.views.utilis.general import obtener_ciudad_registro, filter_by_date

from django.db.models import Q
from django.core.cache import cache
from django.db.models import Prefetch
from django.db import transaction
from django.utils import timezone

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
    ciudad_registro = obtener_ciudad_registro(request)

    # One of the reasons I added NOMBRE_CLIENTE is to use this field as filtering
    filters = Q()
    if filtrar_por and buscar:
        filters = Q(**{f"{filtrar_por.upper()}__icontains": buscar})

    productos_venta_prefetch = Prefetch(
        "productos_venta", queryset=ProductoVenta.objects.select_related("PRODUCTO")
    )
    queryset = (
        Venta.objects.select_related("CLIENTE")
        .prefetch_related(productos_venta_prefetch)
        .filter(filters, CIUDAD_REGISTRO=ciudad_registro)
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

    ciudad_registro = obtener_ciudad_registro(request)

    filters = Q()
    if filtrar_por and buscar:
        filters = Q(**{f"{filtrar_por.upper()}__icontains": buscar})

    queryset = Venta.objects.only(
        "id",
        "FOLIO",
        "VENDEDOR",
        "NOMBRE_CLIENTE",
        "FECHA",
        "MONTO",
        "TIPO_VENTA",
        "TIPO_PAGO",
        "OBSERVACIONES",
        "DESCUENTO",
    ).filter(filters, CIUDAD_REGISTRO=ciudad_registro)

    queryset = filter_by_date(queryset, fechainicio, fechafinal)

    ordering_dict = {
        "cliente": "NOMBRE_CLIENTE",
        "fecha_recientes": "-FECHA",
        "fecha_antiguos": "FECHA",
        "vendedor": "VENDEDOR",
    }
    queryset = queryset.order_by(ordering_dict.get(ordenar_por, "-id"))

    # Serialize the queryset
    serializer = VentaReporteSerializer(queryset, many=True)
    response_data = serializer.data

    # Cache the result
    # cache.set(cache_key, response_data, 60 * 15)  # Cache for 15 minutes

    # # Keep track of all cache keys related to venta_reporte
    # cache_keys = cache.get("venta_reporte_cache_keys", [])
    # cache_keys.append(cache_key)
    # cache.set("venta_reporte_cache_keys", cache_keys)

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@transaction.atomic
def crear_venta(request):
    data = request.data.copy()

    ciudad_registro = obtener_ciudad_registro(request)

    data["CIUDAD_REGISTRO"] = ciudad_registro
    
    client = Cliente.objects.get(pk=data['CLIENTE'])
    if data['TIPO_PAGO'] == 'CREDITO' and client.TIPO_PAGO != 'CREDITO':
        raise ValueError("No puede utilizarse crédito en un usuario no habilitado para usarlo")

    if 'FECHA' not in data:
        data['FECHA'] = timezone.now()

    # Obtener solo el valor del último folio
    ultimo_folio = Venta.objects.filter(CIUDAD_REGISTRO=ciudad_registro).order_by('-FOLIO').values_list('FOLIO', flat=True).first()

    print("ULTIMO FOLIO", ultimo_folio)
    
    if ultimo_folio is not None:
        data["FOLIO"] = ultimo_folio+1
        print(data)
    else:
        raise ValueError("Un valor de folio para la venta anteriror se requiere")

    # Aqui la data va a cambiar para ventas en salida ruta, en especifico tipo_venta es ruta
    serializer = VentaSerializer(data=data)
    if serializer.is_valid():
        venta = serializer.save()
        productos_venta = data["productosVenta"]
        productos_ids = [
            producto_venta["productoId"] for producto_venta in productos_venta
        ]
        producto_instances = Producto.objects.filter(id__in=productos_ids)
        producto_cantidad_venta_map = {
            producto_venta["productoId"]: producto_venta["cantidadVenta"]
            for producto_venta in productos_venta
        }
        producto_precio_venta_map = {
            producto_venta["productoId"]: producto_venta["precioVenta"]
            for producto_venta in productos_venta
        }
        producto_venta_instances = []
        for producto in producto_instances:
            nuevo_producto_venta = ProductoVenta(
                VENTA=venta,
                PRODUCTO=producto,
                NOMBRE_PRODUCTO=producto.NOMBRE,
                CANTIDAD_VENTA=producto_cantidad_venta_map[producto.id],
                PRECIO_VENTA=producto_precio_venta_map[producto.id],
            )
            producto_venta_instances.append(nuevo_producto_venta)
            # Aqui tampoco quiero descontar cantidad del producto si la venta es en salida ruta, porque el producto ya fue descontado del inventario al generar la salida ruta
            if data["STATUS"] == "REALIZADO":
                producto.CANTIDAD -= nuevo_producto_venta.CANTIDAD_VENTA
        Producto.objects.bulk_update(producto_instances, ["CANTIDAD"])
        ProductoVenta.objects.bulk_create(producto_venta_instances)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def venta_detail(request, pk):
    try:
        productos_venta_prefetch = Prefetch(
            "productos_venta", queryset=ProductoVenta.objects.select_related("PRODUCTO")
        )
        venta = (
            Venta.objects.select_related("CLIENTE")
            .prefetch_related(productos_venta_prefetch)
            .get(pk=pk)
        )

    except Venta.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = VentaSerializer(venta)
    return Response(serializer.data)


@api_view(["PUT", "DELETE"])
@transaction.atomic
def modificar_venta(request, pk):
    try:
        productos_venta_prefetch = Prefetch(
            "productos_venta", queryset=ProductoVenta.objects.select_related("PRODUCTO")
        )
        venta = Venta.objects.prefetch_related(productos_venta_prefetch).get(pk=pk)

    except Venta.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        return modificar_venta_put(request, venta)

    elif request.method == "DELETE":
        venta.delete()
        return Response(
            {"message": "Product has been deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


def modificar_venta_put(request, venta):
    data = request.data.get("STATUS")

    if data is None:
        return Response(
            {"error": "STATUS is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    status_actual = venta.STATUS
    status_cambios = {"ANTES": status_actual, "DESPUES": data}

    tipo_venta = venta.TIPO_VENTA

    reporte_cambios = {}
    if tipo_venta == "RUTA":
        venta.STATUS = data
        venta.save()
        reporte_cambios["STATUS"] = status_cambios
        return Response(reporte_cambios)

    # Obtener productos venta de la venta
    productos_venta = venta.productos_venta.all()

    productos_to_update = []

    for producto_venta in productos_venta:
        # This is why i need the foreign key relationship from producto_venta to producto
        producto = producto_venta.PRODUCTO
        print(producto, data)
        producto_cambios = {"ANTES": producto.CANTIDAD}

        cantidad_venta = producto_venta.CANTIDAD_VENTA
        producto.CANTIDAD = calcular_cantidad(
            status_actual, data, producto.CANTIDAD, cantidad_venta
        )

        try:
            assert producto.CANTIDAD >= 0
        except AssertionError:
            return Response(
                {
                    "message": "No existen productos suficientes para realizar esta operación"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        productos_to_update.append(producto)

        producto_cambios["DESPUES"] = producto.CANTIDAD
        reporte_cambios[producto.NOMBRE] = producto_cambios

    Producto.objects.bulk_update(productos_to_update, ["CANTIDAD"])

    venta.STATUS = data
    if data == 'CANCELADO':
        venta.MONTO = 0
    venta.save()

    reporte_cambios["STATUS"] = status_cambios
    return Response(reporte_cambios)


def calcular_cantidad(status_actual, status, cantidad_antes, cantidad_venta):
    if status_actual == "PENDIENTE":
        if status == "REALIZADO":
            return cantidad_antes - cantidad_venta
        else:
            return cantidad_antes  # cancelado
    if status_actual == "REALIZADO":
        if status in ["CANCELADO", "PENDIENTE"]:
            return cantidad_antes + cantidad_venta
        return cantidad_antes
    else:
        return cantidad_antes
