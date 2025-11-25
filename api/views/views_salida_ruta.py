from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.db import transaction  # Import the transaction module
from django.db.models import Prefetch
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone

from api.models import (
    Venta,
    ProductoVenta,
    SalidaRuta,
    ProductoSalidaRuta,
    ClienteSalidaRuta,
    Cliente,
    Producto,
    DevolucionSalidaRuta,
)
from api.serializers import (
    DevolucionSalidaRutaSerializer,
    ProductoSalidaRutaSerializer,
    SalidaRutaReporteSerializer,
    SalidaRutaSerializer,
    SalidaRutaSerializerAcciones,
    SalidaRutaSerializerResumen,
    SalidaRutaSerializerSinClientes,
    VentaSerializer,
    SalidaRutaSerializerLigero,
)
from api.views.utilis.salida_ruta import (
    verificar_salida_ruta_completada,
)
from django.db.models import Case, When, Value, IntegerField

from api.views.utilis.general import obtener_ciudad_registro, filter_by_date

from datetime import datetime


@api_view(["GET"])
def salida_ruta_list(request):
    filtrar_por = request.GET.get("filtrarpor", "")
    buscar = request.GET.get("buscar", "")
    fechainicio = request.GET.get("fechainicio", "")
    fechafinal = request.GET.get("fechafinal", "")
    ordenar_por = request.GET.get("ordenarpor", "")
    page = request.GET.get("page", "")
    role = request.GET.get("role", "")

    ciudad_registro = ciudad_registro = obtener_ciudad_registro(request)

    filters = Q()
    if filtrar_por and buscar:
        filters = Q(**{f"{filtrar_por.upper()}__icontains": buscar})

    productos_salida_ruta_prefetch = Prefetch(
        "productos", queryset=ProductoSalidaRuta.objects.select_related("PRODUCTO_RUTA")
    )

    clientes_salida_ruta_prefetch = Prefetch(
        "clientes", queryset=ClienteSalidaRuta.objects.select_related("CLIENTE_RUTA")
    )
    queryset = (
        SalidaRuta.objects.select_related("RUTA", "REPARTIDOR")
        .prefetch_related(productos_salida_ruta_prefetch, clientes_salida_ruta_prefetch)
        .filter(filters, CIUDAD_REGISTRO=ciudad_registro)
    )

    queryset = filter_by_date(queryset, fechainicio, fechafinal)

    # Chech if the user is a delivery man
    if role == "REPARTIDOR":
        queryset = queryset.filter(REPARTIDOR__USUARIO__username=request.user.username)

    ordering_dict = {
        "atiende": "ATIENDE",
        "repartidor": "REPARTIDOR_NOMBRE",
        "fecha_recientes": "-FECHA",
        "fecha_antiguos": "FECHA",
    }
    queryset = queryset.order_by(ordering_dict.get(ordenar_por, "-id"))

    # Pagination
    paginator = Paginator(queryset, 10)

    try:
        salida_rutas = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        salida_rutas = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        salida_rutas = paginator.page(page)

    serializer = SalidaRutaSerializerLigero(salida_rutas, many=True)

    response_data = {
        "salida_rutas": serializer.data,
        "page": page,
        "pages": paginator.num_pages,
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
def salida_ruta_reporte_list(request):
    filtrar_por = request.GET.get("filtrarpor", "")
    buscar = request.GET.get("buscar", "")
    fechainicio = request.GET.get("fechainicio", "")
    fechafinal = request.GET.get("fechafinal", "")
    ordenar_por = request.GET.get("ordenarpor", "")
    role = request.GET.get("role", "")

    ciudad_registro = ciudad_registro = obtener_ciudad_registro(request)

    filters = Q()
    if filtrar_por and buscar:
        filters = Q(**{f"{filtrar_por.upper()}__icontains": buscar})

    queryset = SalidaRuta.objects.only(
        "id",
        "ATIENDE",
        "FECHA",
        "REPARTIDOR_NOMBRE",
        "OBSERVACIONES",
        "STATUS",
    ).filter(filters, CIUDAD_REGISTRO=ciudad_registro)

    queryset = filter_by_date(queryset, fechainicio, fechafinal)

    # Chech if the user is a delivery man
    if role == "REPARTIDOR":
        queryset = queryset.filter(REPARTIDOR__USUARIO__username=request.user.username)

    ordering_dict = {
        "atiende": "ATIENDE",
        "repartidor": "REPARTIDOR_NOMBRE",
        "fecha_recientes": "-FECHA",
        "fecha_antiguos": "FECHA",
    }
    queryset = queryset.order_by(ordering_dict.get(ordenar_por, "-id"))

    serializer = SalidaRutaReporteSerializer(queryset, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def salida_ruta_detail(request, pk):
    try:
        productos_salida_ruta_prefetch = Prefetch(
            "productos",
            queryset=ProductoSalidaRuta.objects.select_related("PRODUCTO_RUTA"),
        )

        salida_ruta = (
            SalidaRuta.objects.select_related("RUTA", "REPARTIDOR")
            .prefetch_related(productos_salida_ruta_prefetch)
            .get(pk=pk)
        )
    except SalidaRuta.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = SalidaRutaSerializerAcciones(salida_ruta)

    return Response(serializer.data)


@api_view(["GET"])
def salida_ruta_venta(request, pk):

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


@api_view(["GET"])
def salida_ruta_resumen(request, pk):
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

    serializer = SalidaRutaSerializerResumen(salida_ruta)

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

    data = request.data.copy()

    ciudad_registro = ciudad_registro = obtener_ciudad_registro(request)
    data["CIUDAD_REGISTRO"] = ciudad_registro

    ultimo_folio = (
        SalidaRuta.objects.filter(
            CIUDAD_REGISTRO=ciudad_registro,
        )
        .order_by("-id")
        .values_list("FOLIO", flat=True)
        .first()
    )

    print("ULTIMO FOLIO", ultimo_folio)
    if ultimo_folio is not None:
        data["FOLIO"] = ultimo_folio + 1
    else:
        data["FOLIO"] = 1

    serializer = SalidaRutaSerializerSinClientes(data=data)

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

        # ESTA ES LA PARTE QUE QUIERO OPTIMIZAR

        # cliente_instances = Cliente.objects.filter(id__in=cliente_ids).only(
        #     "NOMBRE", "id"
        # )
        # OPTIMIZED USING in_bulk
        cliente_instances_dict = Cliente.objects.in_bulk(cliente_ids)

        # Extract only the required fields (NOMBRE, id) manually
        cliente_instances = [
            {"id": cliente.id, "NOMBRE": cliente.NOMBRE}
            for cliente in cliente_instances_dict.values()
        ]

        # Crear una lista de objetos ClienteSalidaRuta
        clientes_to_create = [
            ClienteSalidaRuta(
                SALIDA_RUTA=salida_ruta,
                CLIENTE_RUTA_id=cliente["id"],
                CLIENTE_NOMBRE=cliente["NOMBRE"],
                STATUS="PENDIENTE",
            )
            for cliente in cliente_instances
        ]

        # Esto puede causar un problema, si hay más de un cliente con nombre salida ruta
        try:
            cliente_ruta = Cliente.objects.get(
                NOMBRE="RUTA", CIUDAD_REGISTRO=ciudad_registro
            )

            nuevo_cliente_salida_ruta = ClienteSalidaRuta(
                SALIDA_RUTA=salida_ruta,
                CLIENTE_RUTA=cliente_ruta,
                CLIENTE_NOMBRE="RUTA",
                STATUS="VISITADO",
            )

            clientes_to_create.append(nuevo_cliente_salida_ruta)

        except Cliente.DoesNotExist:
            print("Cliente con nombre RUTA no existe")

        ClienteSalidaRuta.objects.bulk_create(clientes_to_create)

        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@transaction.atomic
def crear_venta_salida_ruta(request, pk):
    data = request.data.copy()

    ciudad_registro = obtener_ciudad_registro(request)

    data["CIUDAD_REGISTRO"] = ciudad_registro

    # Asignar folio con prefijo por TIPO_VENTA y secuencia independiente por ciudad
    tipo_venta = data.get("TIPO_VENTA")
    prefijo = "M-" if tipo_venta == "MOSTRADOR" else "R-"
    ultimo_folio = (
        Venta.objects.filter(
            CIUDAD_REGISTRO=ciudad_registro,
            TIPO_VENTA=tipo_venta,
            FOLIO__startswith=prefijo,
        )
        .order_by("-id")
        .values_list("FOLIO", flat=True)
        .first()
    )
    try:
        siguiente_num = (
            int(str(ultimo_folio).split("-", 1)[1]) + 1 if ultimo_folio else 1
        )
    except Exception:
        siguiente_num = 1
    data["FOLIO"] = f"{prefijo}{siguiente_num}"

    if "FECHA" not in data:
        data["FECHA"] = timezone.now()

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

        salida_ruta = SalidaRuta.objects.get(id=pk)

        verificar_salida_ruta_completada(salida_ruta)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@transaction.atomic
def devolver_producto_salida_ruta(request, pk):
    salida_ruta = SalidaRuta.objects.get(id=pk)

    try:
        assert salida_ruta.STATUS in [
            "PROGRESO",
            "PENDIENTE",
        ]  # Por ahora vamos a permitir que se puedan hacer devoluciones incluso si el status es pendiente
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

        # 2. Devolver producto al almacen
        producto_salida_ruta = ProductoSalidaRuta.objects.get(
            id=data.get("PRODUCTO_SALIDA_RUTA"),
        )

        producto_salida_ruta.CANTIDAD_DISPONIBLE -= data.get("CANTIDAD_DEVOLUCION")

        producto = Producto.objects.get(id=data.get("PRODUCTO_DEVOLUCION"))

        producto.CANTIDAD += data.get("CANTIDAD_DEVOLUCION")

        producto.save()

        # Revisar si con los productos devueltos ya no hay mas productos disponibles
        if producto_salida_ruta.CANTIDAD_DISPONIBLE == 0:
            producto_salida_ruta.STATUS = "VENDIDO"

        producto_salida_ruta.save()

        # Obtener todos los  productos de la salida ruta

        verificar_salida_ruta_completada(salida_ruta)

        return Response(serializer.data, status=status.HTTP_200_OK)

    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@transaction.atomic
def realizar_aviso_visita(request, pk):
    salida_ruta = SalidaRuta.objects.get(id=pk)

    data = request.data

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

    verificar_salida_ruta_completada(salida_ruta)

    return Response(
        {"message": "La salida ruta ha sido actualizada exitosamente"},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def devolucion_list(request):
    filtrar_por = request.GET.get("filtrarpor", "")
    buscar = request.GET.get("buscar", "")
    fechainicio = request.GET.get("fechainicio", "")
    fechafinal = request.GET.get("fechafinal", "")
    ordenar_por = request.GET.get("ordenarpor", "")
    page = request.GET.get("page", "")

    ciudad_registro = obtener_ciudad_registro(request)

    filters = Q()
    if filtrar_por and buscar:
        filters = Q(**{f"{filtrar_por.upper()}__icontains": buscar})

    queryset = DevolucionSalidaRuta.objects.select_related(
        "SALIDA_RUTA", "PRODUCTO_DEVOLUCION"
    ).filter(filters, SALIDA_RUTA__CIUDAD_REGISTRO=ciudad_registro)

    queryset = filter_by_date(queryset, fechainicio, fechafinal)

    # The problem is in here. I want the rows without administrador (null) to go last when ordering, not first
    ordering_dict = {
        "atiende": "ATIENDE",
        "repartidor": "REPARTIDOR",
        "administrador": "ADMINISTRADOR",
        "fecha_recientes": "-FECHA",
        "fecha_antiguos": "FECHA",
    }

    if ordenar_por == "administrador":
        # Rows with 'administrador' as an empty string will be ordered last
        queryset = queryset.annotate(
            admin_order=Case(
                When(ADMINISTRADOR="", then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by("admin_order", ordering_dict[ordenar_por])
    else:
        queryset = queryset.order_by(ordering_dict.get(ordenar_por, "-id"))

    # Pagination
    paginator = Paginator(queryset, 10)

    try:
        devoluciones = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        devoluciones = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        devoluciones = paginator.page(page)

    serializer = DevolucionSalidaRutaSerializer(devoluciones, many=True)

    response_data = {
        "devoluciones": serializer.data,
        "page": page,
        "pages": paginator.num_pages,
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET", "PUT"])
def devolucion_detalles(request, pk):
    try:
        devolucion = DevolucionSalidaRuta.objects.get(id=pk)

    except DevolucionSalidaRuta.DoesNotExist:
        return Response(
            {"message": "Devolución con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        serializer = DevolucionSalidaRutaSerializer(devolucion)

        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "PUT":
        data = request.data

        devolucion.STATUS = data.get("STATUS")
        devolucion.ADMINISTRADOR = data.get("ADMINISTRADOR")
        devolucion.save()

        return Response(
            {"message": "Devolución ha sido actualizada exitosamente"},
            status=status.HTTP_200_OK,
        )


@api_view(["PUT"])
@transaction.atomic
def realizar_recarga_salida_ruta(request, pk):
    data = request.data

    producto_id = data.get("PRODUCTO_RUTA")
    cantidad = data.get("CANTIDAD_RECARGA", 0)

    # Validating the input
    if not producto_id or cantidad <= 0:
        return Response(
            {
                "message": "Datos invalidos: PRODUCTO_RUTA o CANTIDAD_RECARGA no proporcionados o incorrectos"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 1. Remover producto de almacen
    try:
        producto = Producto.objects.get(id=producto_id)

        if cantidad > producto.CANTIDAD:
            return Response(
                {
                    "message": "Cantidad de recarga excede la cantidad disponible en almacen"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        producto.CANTIDAD -= cantidad
        producto.save()
    except Producto.DoesNotExist:
        return Response(
            {"message": "Producto con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 2. Agregar producto a salida ruta
    try:
        producto_salida_ruta = ProductoSalidaRuta.objects.get(
            SALIDA_RUTA_id=pk, PRODUCTO_RUTA_id=producto_id
        )
        producto_salida_ruta.CANTIDAD_DISPONIBLE = data.get(
            "CANTIDAD_DISPONIBLE", producto_salida_ruta.CANTIDAD_DISPONIBLE
        )
        producto_salida_ruta.CANTIDAD_RUTA = data.get(
            "CANTIDAD_RUTA", producto_salida_ruta.CANTIDAD_RUTA
        )
        producto_salida_ruta.STATUS = data.get("STATUS", producto_salida_ruta.STATUS)
        producto_salida_ruta.save()
    except ProductoSalidaRuta.DoesNotExist:
        serializer = ProductoSalidaRutaSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Salida ruta creada exitosamente"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {"message": "Salida ruta actualizada exitosamente"},
        status=status.HTTP_200_OK,
    )
