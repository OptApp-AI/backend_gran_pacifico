from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
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


@api_view(["GET"])
def cliente_list(request):
    # 1. Filtrar usando parametro clientfiltrarpor
    filtrar_por = request.GET.get("clientefiltrarpor", "")
    buscar = request.GET.get("clientebuscar", "")

    if filtrar_por == "nombre" and buscar:
        queryset = Cliente.objects.filter(NOMBRE__icontains=buscar)
    elif filtrar_por == "contacto":
        queryset = Cliente.objects.filter(CONTACTO__icontains=buscar)
    elif filtrar_por == "tipopago":
        queryset = Cliente.objects.filter(TIPO_PAGO__icontains=buscar)
    else:
        queryset = Cliente.objects.all()

    # 2. Ordenar usando clienteordenarpor
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

    # 3. Paginacion
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

    return Response(
        {"clientes": serializer.data, "page": page, "pages": paginator.num_pages},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def cliente_venta_lista(request):
    queryset = Cliente.objects.all().order_by("-id")

    serializer = ClienteVentaSerializer(queryset, many=True)

    # cliente = Cliente.objects.filter(NOMBRE="MOSTRADOR")

    # serializer = ClienteVentaSerializer(cliente, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def crear_cliente(request):
    data = request.data

    print("DATA---", data)

    # 1. Crear cliente
    serializer = ClienteSerializer(data=data)

    if serializer.is_valid():
        cliente = serializer.save()

        # 2. Crear precios del cliente
        precios_cliente = data["preciosCliente"]
        for precio_cliente in precios_cliente:
            nuevo_precio_cliente = PrecioCliente.objects.create(
                CLIENTE=cliente,
                PRODUCTO=Producto.objects.get(pk=precio_cliente["productoId"]),
                PRECIO=precio_cliente["precioCliente"],
            )

            nuevo_precio_cliente.save()

        # 3. Crear direccion
        direccion = data["direccion"]

        nueva_direccion = Direccion.objects.create(**direccion)

        nueva_direccion.save()

        cliente.DIRECCION = nueva_direccion

        # 4. Crear rutas del cliente
        rutas_ids = data["rutasIds"]
        if rutas_ids:
            rutas = RutaDia.objects.filter(id__in=rutas_ids)
            cliente.RUTAS.set(rutas)

        cliente.save()

        # Es importante tener en cuenta que, aunque creas los objetos PrecioCliente después de haber validado y serializado el objeto Cliente, estos objetos estarán disponibles en la instancia del objeto Cliente y se incluirán en la respuesta cuando se serialice el objeto Cliente utilizando el serializer ClienteSerializer.
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
def modificar_cliente(request, pk):
    try:
        cliente = Cliente.objects.get(pk=pk)
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
            nueva_direccion = data["nuevaDireccion"]

            direccionCliente = Direccion.objects.get(
                pk=nueva_direccion["direccionClienteId"]
            )

            direccionCliente.CALLE = nueva_direccion["CALLE"]
            direccionCliente.NUMERO = nueva_direccion["NUMERO"]
            direccionCliente.COLONIA = nueva_direccion["COLONIA"]
            direccionCliente.CIUDAD = nueva_direccion["CIUDAD"]
            direccionCliente.MUNICIPIO = nueva_direccion["MUNICIPIO"]
            direccionCliente.CP = nueva_direccion["CP"]

            direccionCliente.save()

            # 4. Actualizar rutas del cliente
            nuevas_rutas_ids = data["nuevasRutasIds"]
            if nuevas_rutas_ids:
                ruta_dias = RutaDia.objects.filter(id__in=nuevas_rutas_ids)
                cliente.RUTAS.set(ruta_dias)

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


@api_view(["POST"])
def crear_ruta(request):
    serializer = RutaSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


# QUE CUANDO ELIMINES UNA RUTA TE DE LA OPCIÓN DE ELIMINAR TODAS LAS RUTAS ASOCIADAS,
# SOLO UN ADMINISTRADOR PUEDE ELIMINAR LAS RUTAS (QUIZA NO, PORQUE LOS CAJEROS PASAN MAS TIEMPO USANDO Y CREANDO RUTAS)


# CUANDO EDITAS EL NOMBRE DE LA RUTA TAMBIEN EDITAS EL NOMBRE DEL RESTO DE LAS RUTAS
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
