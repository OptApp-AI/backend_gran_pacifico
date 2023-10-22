from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status, serializers
from api.models import (
    Producto,
    Cliente,
    PrecioCliente,
    Direccion,
    # Ruta
    Ruta,
    RutaDia,
)
from api.serializers import (
    ClienteSerializer,
    ClienteVentaSerializer,
    # Ruta
    RutaSerializer,
    RutaDiaSerializer,
    ClientesRutaSerializer,
    RutaRegistrarClienteSerializer,
    ClienteRealizarSalidaRutaSerializer,
    RutasRealizarSalidaRutaSerializer,
)
from django.db.models import Case, When, Value, IntegerField
from django.db.models import Case, When, Value, IntegerField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache

# Changes
from django.db.models import Q
from django.db import transaction


@api_view(["GET"])
def cliente_list(request):
    # Generate a unique cache key based on request parameters
    # any change in query parameters will produce a different URL-encoded string
    cache_key = f"cliente_list_{request.GET.urlencode()}"

    cached_data = cache.get(cache_key)

    if cached_data:
        return Response(cached_data, status=status.HTTP_200_OK)

    # Construct a Q object for filtering
    q_objects = Q()

    # Filtrar usando clientefiltrarpor y clientebuscar
    filtrar_por = request.GET.get("clientefiltrarpor", "").upper()
    buscar = request.GET.get("clientebuscar", "")

    if filtrar_por and buscar:
        q_objects = Q(**{f"{filtrar_por}__icontains": buscar})

    # prefetch_related with a reverse relation like precios_cliente makes sense if you expect to access the related PrecioCliente objects when dealing with a Cliente object. Doing so will fetch the related PrecioCliente objects in a single query, reducing the number of database hits when you loop through Cliente objects later on.
    queryset = Cliente.objects.filter(q_objects).prefetch_related(
        "RUTAS", "precios_cliente"
    )

    # Ordenar usando clienteordenarpor
    ordenar_por = request.GET.get("clienteordenarpor", "")

    if ordenar_por == "nombre":
        queryset = queryset.order_by("NOMBRE")
    elif ordenar_por == "contacto":
        # Primero ordenamos de tal forma que los clientes
        # con contacto distinto de '' esten al inicio
        # Luego, como segundo criterio ordenamos con respecto al nombre del contacto
        queryset = queryset.annotate(
            is_empty=Case(
                When(CONTACTO="", then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by("is_empty", "CONTACTO")
    else:
        queryset = queryset.order_by("-id")

    # Paginacion
    page = request.GET.get("page")
    paginator = Paginator(queryset, 5)

    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        clientes = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        clientes = paginator.page(page)

    serializer = ClienteSerializer(clientes, many=True)

    response_data = {
        "clientes": serializer.data,
        "page": page,
        "pages": paginator.num_pages,
    }

    # Cache the result
    cache.set(
        cache_key,
        response_data,
        60 * 15,
    )  # Cache for 15 minutes

    # A list of all the cache keys related to cliente is maintained. This list itself is stored in the cache. When new data is cached, its key is added to this list.
    cache_keys = cache.get("cliente_cache_keys", [])
    cache_keys.append(cache_key)
    cache.set("cliente_cache_keys", cache_keys)

    return Response(
        {"clientes": serializer.data, "page": page, "pages": paginator.num_pages},
        status=status.HTTP_200_OK,
    )


# I apologize for the oversight. You are correct: if the serializer is not using the DIRECCION and RUTAS fields, then there's no reason to use select_related and prefetch_related in the query. These methods are intended for optimizing access to related fields, and if those fields aren't being accessed, then using them will actually make the query less efficient by retrieving unnecessary data


# When you use the .values() or .only() methods, Django returns a queryset that only includes the fields you specified. This means it won't automatically evaluate related fields when serializing, even if the serializer is configured to include them. That's likely why precios_cliente is missing in the frontend.


# This way, you're fetching only the id and NOMBRE fields from the Cliente model while still allowing the ClienteVentaSerializer to fetch the precios_cliente through its nested serializer (PrecioClienteSerializer).
@api_view(["GET"])
def cliente_venta_lista(request):
    nombre = request.GET.get("nombre", "")
    cache_key = f"cliente_venta_lista:{nombre}"

    # Try to fetch from cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data, status=status.HTTP_200_OK)

    if nombre:
        # Use .only() to limit the fields fetched from the Cliente model.
        queryset = (
            Cliente.objects.filter(NOMBRE__icontains=nombre)
            .only("id", "NOMBRE")
            .order_by("NOMBRE")
            .prefetch_related("precios_cliente")[:5]
        )
        if not queryset.exists():
            queryset = (
                Cliente.objects.filter(NOMBRE="MOSTRADOR")
                .only("id", "NOMBRE")
                .prefetch_related("precios_cliente")
            )
    else:
        queryset = (
            Cliente.objects.filter(NOMBRE="MOSTRADOR")
            .only("id", "NOMBRE")
            .prefetch_related("precios_cliente")
        )

    # Serialize data manually. This is necessary in order to obtain precios_cliente. Even though I don't understand why.
    # After you've obtained the queryset, iterate through the instances to call the ClienteVentaSerializer.
    # serialized_data = [ClienteVentaSerializer(instance).data for instance in queryset]
    serialized_data = ClienteVentaSerializer(queryset, many=True).data

    # Cache for 5 minutes
    cache.set(cache_key, serialized_data, 60 * 15)

    # A list of all the cache keys related to cliente is maintained. This list itself is stored in the cache. When new data is cached, its key is added to this list.
    cache_keys = cache.get("cliente_cache_keys", [])
    cache_keys.append(cache_key)
    cache.set("cliente_cache_keys", cache_keys)

    return Response(serialized_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@transaction.atomic  # Ensures atomic transaction
def crear_cliente(request):
    data = request.data

    try:
        # 1. Create Cliente
        serializer = ClienteSerializer(data=data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)

        cliente = serializer.save()

        # 2. Create PrecioCliente
        precios_cliente = data["preciosCliente"]
        precio_cliente_objs = [
            PrecioCliente(
                CLIENTE=cliente,
                PRODUCTO=Producto.objects.get(pk=precio_cliente["precioClienteId"]),
                PRECIO=precio_cliente["nuevoPrecioCliente"],
            )
            for precio_cliente in precios_cliente
        ]
        PrecioCliente.objects.bulk_create(precio_cliente_objs)

        # 3. Create Direccion
        direccion = data["direccion"]
        print("DIRECCION", direccion)
        nueva_direccion = Direccion.objects.create(**direccion)
        cliente.DIRECCION = nueva_direccion
        print("CLIENTE", cliente)

        # 4. Set Rutas
        rutas_ids = data.get("rutasIds", [])
        if rutas_ids:
            rutas = RutaDia.objects.filter(id__in=rutas_ids)
            cliente.RUTAS.set(rutas)

        cliente.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("ERROR", str(e))
        # Any exception will cause a rollback
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def cliente_detail(request, pk):
    try:
        cliente = Cliente.objects.get(pk=pk)
    except Cliente.DoesNotExist:
        return Response(
            {"message": "Cliente con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ClienteSerializer(cliente)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "DELETE"])
# Cache Invalidation: You need to think about how to invalidate or update the cache when the underlying data changes. Otherwise, you might serve stale or incorrect data.
@transaction.atomic  # Ensures atomic transaction
def modificar_cliente(request, pk):
    try:
        cliente = (
            Cliente.objects.select_related("DIRECCION")
            .prefetch_related("RUTAS")
            .get(pk=pk)
        )
    except Cliente.DoesNotExist:
        return Response(
            {"message": "Cliente con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "PUT":
        data = request.data
        # 1. Actualizar cliente
        serializer = ClienteSerializer(cliente, data=data)

        if serializer.is_valid():
            serializer.save()

            # 2. Modificar el precio de los clientes
            nuevos_precios_cliente = data["nuevosPreciosCliente"]

            for nuevo_precio_cliente in nuevos_precios_cliente:
                precioCliente = PrecioCliente.objects.get(
                    pk=nuevo_precio_cliente["precioClienteId"]
                )
                precioCliente.PRECIO = nuevo_precio_cliente["nuevoPrecioCliente"]
                precioCliente.save()

            # 3. Modificar la direccion
            # nueva_direccion = data["nuevaDireccion"]

            # direccionCliente = Direccion.objects.get(
            #     pk=nueva_direccion["direccionClienteId"]
            # )

            # direccionCliente.CALLE = nueva_direccion["CALLE"]
            # direccionCliente.NUMERO = nueva_direccion["NUMERO"]
            # direccionCliente.COLONIA = nueva_direccion["COLONIA"]
            # direccionCliente.CIUDAD = nueva_direccion["CIUDAD"]
            # direccionCliente.MUNICIPIO = nueva_direccion["MUNICIPIO"]
            # direccionCliente.CP = nueva_direccion["CP"]

            # direccionCliente.save()

            # 3. Update Address
            nueva_direccion = data["nuevaDireccion"]
            direccion_id = nueva_direccion.pop(
                "direccionClienteId"
            )  # Remove and retrieve 'direccionClienteId'

            print("NUEVA DIRECCION", nueva_direccion)
            Direccion.objects.filter(pk=direccion_id).update(**nueva_direccion)

            # 4. Actualizar rutas del cliente
            # nuevas_rutas_ids = data["nuevasRutasIds"]
            # if nuevas_rutas_ids:
            #     ruta_dias = RutaDia.objects.filter(id__in=nuevas_rutas_ids)
            #     cliente.RUTAS.set(ruta_dias)
            # 4. Update Client Routes
            nuevas_rutas_ids = data.get("nuevasRutasIds", [])
            if nuevas_rutas_ids:
                cliente.RUTAS.set(RutaDia.objects.filter(id__in=nuevas_rutas_ids))

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        cliente.delete()

        return Response(
            {"message": "Cliente fue eliminado exitosamente"},
            status=status.HTTP_204_NO_CONTENT,
        )


# Rutas


@api_view(["GET"])
def ruta_list(request):
    rutas = Ruta.objects.all().order_by("-id")

    serializer = RutaSerializer(rutas, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def ruta_detail(request, pk):
    try:
        ruta = Ruta.objects.get(id=pk)
    except Ruta.DoesNotExist:
        return Response(
            {"message": "Ruta con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = RutaSerializer(ruta)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def crear_ruta(request):
    serializer = RutaSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT", "DELETE"])
def modificar_ruta(request, pk):
    try:
        ruta = Ruta.objects.get(id=pk)
    except Ruta.DoesNotExist:
        return Response(
            {"message": "Ruta con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "PUT":
        serializer = RutaSerializer(instance=ruta, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        ruta.delete()

        return Response(
            {"message": "Ruta ha sido eliminada exitosamente"},
            status=status.HTTP_204_NO_CONTENT,
        )


# Ruta Dia


@api_view(["GET"])
def ruta_dias_list(request, pk):
    ruta_dias = RutaDia.objects.filter(RUTA=pk)

    serializer = RutaDiaSerializer(ruta_dias, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def ruta_dias_detail(request, pk):
    try:
        ruta_dia = RutaDia.objects.get(id=pk)
    except RutaDia.DoesNotExist:
        return Response({"message": "Ruta con el id dado no existe"})

    serializer = RutaDiaSerializer(ruta_dia)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def modificar_ruta_dia(request, pk):
    try:
        ruta_dia = RutaDia.objects.get(id=pk)
    except RutaDia.DoesNotExist:
        return Response(
            {"message": "Ruta con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    data = request.data

    # REPARTIDOR = data.get("REPARTIDOR")
    # REPARTIDOR_NOMBRE = data.get("REPARTIDOR_NOMBRE")

    # ruta_dia.REPARTIDOR = REPARTIDOR
    # ruta_dia.REPARTIDOR_NOMBRE = REPARTIDOR_NOMBRE
    # ruta_dia.save()

    # return Response({"Ruta ha sido actualizada exitosamente"}, status=status.HTTP_200_OK)

    serializer = RutaDiaSerializer(instance=ruta_dia, data=data)

    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Clientes de la ruta dia
# Esta vista me permite acceder a los clientes que pertenecen a una ruta dia. La vista se usa al ver detalles de ruta dia en el modal
@api_view(["GET"])
def clientes_ruta(request, pk):
    try:
        ruta_dia = RutaDia.objects.get(id=pk)
    except RutaDia.DoesNotExist:
        return Response(
            {"message": "Ruta con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # clientes = Cliente.objects.filter(RUTA=pk)

    serializer = ClientesRutaSerializer(ruta_dia)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def rutas_registrar_cliente(request):
    rutas = Ruta.objects.all()
    serializer = RutaRegistrarClienteSerializer(rutas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Esta vista permite obtener los clientes en el formato "NOMBRE", "id", "ruta_dia_ids" para poder seleccionar los clientes de una ruta dia es espefifico
@api_view(["GET"])
def clientes_salida_ruta_list(request):
    clientes = Cliente.objects.all()

    serializer = ClienteRealizarSalidaRutaSerializer(clientes, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def ruta_salida_ruta_list(request):
    rutas = Ruta.objects.all()

    serializer = RutasRealizarSalidaRutaSerializer(rutas, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)
