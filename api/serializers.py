from rest_framework import serializers
from .models import (
    Producto,
    Cliente,
    PrecioCliente,
    ProductoVenta,
    Venta,
    Direccion,
    Empleado,
    # Ruta
    Ruta,
    RutaDia,
    ProductoSalidaRuta,
    ClienteSalidaRuta,
    SalidaRuta,
    AjusteInventario,
)
from django.contrib.auth.models import User

# Empleados


class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = ("IMAGEN",)


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    is_admin = serializers.SerializerMethodField(read_only=True)

    # Algo mas sencillo aqui seria crear el campo imagen  en el serializerusando empleado para ello, de esta manera, accedes a image desde usuario y no necesitar usar empleado en el frontend
    empleado = EmpleadoSerializer()

    class Meta:
        model = User

        fields = ("id", "username", "name", "is_admin", "empleado")

    def get_name(self, obj):
        name = obj.first_name
        if not name:
            name = obj.username
        return name

    def get_is_admin(self, obj):
        is_admin = obj.is_staff
        return is_admin


# Productos


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = "__all__"


# Ruta


class RutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruta
        fields = "__all__"


class RutaDiaSerializer(serializers.ModelSerializer):
    NOMBRE = serializers.CharField(source="RUTA.NOMBRE", read_only=True)

    # clientes_ruta = ClienteSerializer

    class Meta:
        model = RutaDia
        fields = "__all__"
        # exclude = ("RUTA",)


class RutaRegistrarClienteSerializer(serializers.ModelSerializer):
    # SerializerMethodField: It's often expensive to use SerializerMethodField. Make sure you are doing only necessary calculations inside them.
    ruta_dias = serializers.SerializerMethodField()

    class Meta:
        model = Ruta
        fields = ["NOMBRE", "ruta_dias"]

    def get_ruta_dias(self, obj):
        return {ruta_dia.DIA: ruta_dia.id for ruta_dia in obj.ruta_dias.all()}


# Deberia ser ClienteRutaDiaSerializer
class ClientesRutaSerializer(serializers.ModelSerializer):
    # SerializerMethodField: It's often expensive to use SerializerMethodField. Make sure you are doing only necessary calculations inside them.
    clientes_ruta = serializers.SerializerMethodField()

    class Meta:
        model = RutaDia
        fields = ("clientes_ruta",)

    def get_clientes_ruta(self, obj):
        # Assuming obj is an instance of RutaDia, we can access its related Cliente instances
        return [cliente.NOMBRE for cliente in obj.clientes_ruta.all()]


# Clientes


class PrecioClienteSerializer(serializers.ModelSerializer):
    # PAra que hago esto si PrecioCliente tiene el campo PRODUCTO_NOMBRE??????????????!!!!!!!!!!!! Olvidalo, no lo tiene, pero deberia
    producto_nombre = serializers.CharField(source="PRODUCTO.NOMBRE", read_only=True)

    # La cantidad es para poder hacer una venta a este cliente, sabiendo cuantos productos tengo disponibles

    # Pero esto solo es necesario cuando realizo una venta, no cuando quiero ver informacion del cliente
    # ERRROR ESTO NO DEBE SER UN INGEGER
    # producto_cantidad = serializers.FloatField(
    #     source="PRODUCTO.CANTIDAD", read_only=True
    # )

    # La imagen es para el momento de hacer la venta
    # Los mismo que dije antes, esto solo es necesario al momento de hacer una venta
    # producto_imagen = serializers.ImageField(source="PRODUCTO.IMAGEN", read_only=True)

    # SerializerMethodField: It's often expensive to use SerializerMethodField. Make sure you are doing only necessary calculations inside them.
    porcentage_precio = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PrecioCliente
        # fields = "__all__"
        fields = ("id", "PRECIO", "producto_nombre", "porcentage_precio")

    def get_porcentage_precio(self, obj):
        precio_publico = obj.PRODUCTO.PRECIO if obj.PRODUCTO.PRECIO else 1
        precio_cliente = obj.PRECIO if obj.PRECIO else 0

        if precio_publico == 0:
            return "NO DISPONIBLE"

        descuento = (1 - (precio_cliente / precio_publico)) * 100

        return round(descuento, 2)


class DireccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direccion
        fields = "__all__"


class ClienteSerializer(serializers.ModelSerializer):
    # Debo cambia el serializador de precios, remover producto_cantidad,  producto_imagen
    precios_cliente = PrecioClienteSerializer(many=True, read_only=True)

    DIRECCION = DireccionSerializer(required=False)

    RUTAS = RutaDiaSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = "__all__"


class PrecioClienteVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="PRODUCTO.NOMBRE", read_only=True)

    # La cantidad es para poder hacer una venta a este cliente, sabiendo cuantos productos tengo disponibles

    # Pero esto solo es necesario cuando realizo una venta, no cuando quiero ver informacion del cliente
    # ERRROR ESTO NO DEBE SER UN INGEGER
    producto_cantidad = serializers.FloatField(
        source="PRODUCTO.CANTIDAD", read_only=True
    )

    # La imagen es para el momento de hacer la venta
    # Los mismo que dije antes, esto solo es necesario al momento de hacer una venta
    producto_imagen = serializers.ImageField(source="PRODUCTO.IMAGEN", read_only=True)

    # Esto solo se necesaita cuando quiero ver informacion del cliente, no al momento de realizar la venta
    # porcentage_precio = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PrecioCliente
        # fields = "__all__"
        fields = (
            "id",
            "PRECIO",
            "producto_nombre",
            "producto_cantidad",
            "producto_imagen",
            "PRECIO",
            # This field is necessary in order to know what product we need to remove stock from
            "PRODUCTO",  # product id
        )


class ClienteVentaSerializer(serializers.ModelSerializer):
    precios_cliente = PrecioClienteVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        # For clientes ventas i only need a few fields. Is this expensive?
        # Limit Fields: If you are serializing models with many fields but only need a subset, use the only method to limit the fields that Django has to pull into Python from the DB.
        # AS YOU CAN SEE I DON'T USE THE DIRECCION NOR THE RUTAS FIELD IN ANY PLACE, SO WHY SHOULD I USE select_related, and prefetch_related to get those fields??????
        fields = ("id", "precios_cliente", "NOMBRE")


# Venta


class ProductoVentaSerializer(serializers.ModelSerializer):
    # producto_nombre = serializers.CharField(source="PRODUCTO.NOMBRE", read_only=True)

    class Meta:
        model = ProductoVenta
        fields = "__all__"
        # fiels = ("id", "NOMBRE_PRODUCTO") Quiza esto es mejor para el rendimiento


class VentaSerializer(serializers.ModelSerializer):
    productos_venta = ProductoVentaSerializer(many=True, read_only=True)

    # cliente_nombre = serializers.CharField(source="CLIENTE.NOMBRE", read_only=True)

    class Meta:
        model = Venta
        fields = "__all__"


# Salida Ruta


class ProductoSalidaRutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoSalidaRuta
        fields = "__all__"


class ClienteSalidaRutaSerializer(serializers.ModelSerializer):
    # Accedemos a los atributos especificos de un hermano mediante un metodo
    precios_cliente = serializers.SerializerMethodField()

    class Meta:
        model = ClienteSalidaRuta
        fields = "__all__"

    # Asi accedo a los atributos de un hermano desde el serializador
    def get_precios_cliente(self, obj):
        precios_cliente = []
        # PrecioCliente es hermano de ClienteSalida porque los dos son hijos de Cliente

        # Dame todos las instancias de PRecioCliente que son hijas de mi papa (Cliente)
        for precio in PrecioCliente.objects.filter(CLIENTE=obj.CLIENTE_RUTA):
            # Serializa a mi hermano
            serializer = PrecioClienteSerializer(precio)
            # Usa la informacion en mi hermano serializado para crear un objeto y agregarlo a precios_cliente
            precios_cliente.append(
                {
                    "precio": serializer.data["PRECIO"],
                    "producto_nombre": serializer.data["producto_nombre"],
                    "productoId": serializer.data["PRODUCTO"],
                    "producto_imagen": serializer.data["producto_imagen"],
                }
            )
            # precios_cliente.append(serializer.data)
        return precios_cliente


class SalidaRutaSerializer(serializers.ModelSerializer):
    productos = ProductoSalidaRutaSerializer(many=True, read_only=True)

    clientes = ClienteSalidaRutaSerializer(many=True, read_only=True)

    class Meta:
        model = SalidaRuta
        fields = "__all__"


class ClienteRealizarSalidaRutaSerializer(serializers.ModelSerializer):
    ruta_dia_ids = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Cliente
        fields = ("NOMBRE", "id", "ruta_dia_ids")

    def get_ruta_dia_ids(self, obj):
        ruta_dias = obj.RUTAS

        ruta_dia_ids = [ruta.id for ruta in ruta_dias.all()]

        return ruta_dia_ids


class RutasDiaRealizarSalidaRutaSerializer(serializers.ModelSerializer):
    repartidor_id = serializers.IntegerField(source="REPARTIDOR.id", read_only=True)

    class Meta:
        model = RutaDia
        fields = (
            "id",
            "repartidor_id",
            "DIA",
        )


class RutasRealizarSalidaRutaSerializer(serializers.ModelSerializer):
    ruta_dias = RutasDiaRealizarSalidaRutaSerializer(many=True, read_only=True)

    class Meta:
        model = Ruta
        fields = ("NOMBRE", "id", "ruta_dias")


class AjusteInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AjusteInventario
        fields = "__all__"
