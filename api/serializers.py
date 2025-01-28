from rest_framework import serializers
from .models import (
    DevolucionSalidaRuta,
    Empleado,
    # Ventas
    Direccion,
    Cliente,
    Producto,
    AjusteInventario,
    PrecioCliente,
    Venta,
    ProductoVenta,
    # Ruta
    Ruta,
    RutaDia,
    ProductoSalidaRuta,
    ClienteSalidaRuta,
    SalidaRuta,
)
from django.contrib.auth.models import User

# Empleados


# The only purpose of the model Empleado and the EmpleadoSerializer serializer is to add an image to the default User model
# I could remove this serializer and use serializers.SerializerMethodField in order to obtain the empleado with the image, or even better just the image
class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = ("IMAGEN", "ROLE", "CIUDAD_REGISTRO")


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    is_admin = serializers.SerializerMethodField(read_only=True)
    role = serializers.CharField(source="empleado.ROLE")
    empleado_id = serializers.CharField(source="empleado.id", read_only=True)

    # Algo mas sencillo aqui seria crear el campo imagen  en el serializer usando empleado para ello, de esta manera, accedes a image desde usuario y no necesitas usar empleado en el frontend
    empleado = EmpleadoSerializer()

    class Meta:
        model = User
        # User model from Django has many fields, I only need a few of them
        fields = (
            "id",
            "username",
            "name",
            "is_admin",
            "empleado",
            "role",
            "empleado_id",
        )

    def get_name(self, obj):
        name = obj.first_name
        if not name:
            name = obj.username
        return name

    def get_is_admin(self, obj):
        is_admin = obj.is_staff
        return is_admin


# Mostrador X


# Productos


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = "__all__"


class AjusteInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AjusteInventario
        fields = "__all__"


class AjusteInventarioReporteSerializer(AjusteInventarioSerializer):
    class Meta(AjusteInventarioSerializer.Meta):
        fields = [
            "id",
            "CAJERO",
            "BODEGA",
            "PRODUCTO_NOMBRE",
            "CANTIDAD",
            "TIPO_AJUSTE",
            "FECHA",
            "OBSERVACIONES",
        ]


# Clientes


class DireccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direccion
        fields = "__all__"


class BasePrecioClienteSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="PRODUCTO.NOMBRE", read_only=True)

    producto_imagen = serializers.ImageField(source="PRODUCTO.IMAGEN", read_only=True)

    class Meta:
        model = PrecioCliente
        fields = "__all__"


class PrecioClienteSerializer(BasePrecioClienteSerializer):
    porcentage_precio = serializers.SerializerMethodField(read_only=True)

    class Meta(BasePrecioClienteSerializer.Meta):
        fields = (
            "id",
            "producto_nombre",
            "producto_imagen",
            "porcentage_precio",
            "PRECIO",
            "PRODUCTO",
        )

    def get_porcentage_precio(self, obj):
        precio_publico = obj.PRODUCTO.PRECIO or 1
        precio_cliente = obj.PRECIO or 0

        if precio_publico == 0:
            return "NO DISPONIBLE"

        descuento = (1 - (precio_cliente / precio_publico)) * 100

        return round(descuento, 2)


class RutaDiaSerializer(serializers.ModelSerializer):
    NOMBRE = serializers.CharField(source="RUTA.NOMBRE", read_only=True)

    class Meta:
        model = RutaDia
        fields = "__all__"
        # exclude = ("RUTA",)


# Cuando creo la salida ruta deberia enviar esto en lugar de ClienteConRutaDiaSerializer
# class RutaDiaSalidaRutaSerializer(serializers.ModelSerializer):
#     clientes_ruta = serializers.SerializerMethodField(read_only=True)

#     class Meta:
#         model = RutaDia
#         fields = ("id", "clientes_ruta")

#     def get_clientes_ruta(self, obj):
#         return [
#             {"clienteId": cliente.id, "NOMBRE": cliente.NOMBRE}
#             for cliente in obj.clientes_ruta.all()
#         ]


class ClienteSerializer(serializers.ModelSerializer):
    precios_cliente = PrecioClienteSerializer(many=True, read_only=True)

    DIRECCION = DireccionSerializer(required=False)

    RUTAS = RutaDiaSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = "__all__"


# Esto se usa al momento de generar una salida ruta
# Este serializador me permite seleccionar a los clientes y sus respectivas rutas dia
class ClienteConRutaDiaSerializer(serializers.ModelSerializer):
    ruta_dia_ids = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Cliente
        fields = ("NOMBRE", "id", "ruta_dia_ids")

    def get_ruta_dia_ids(self, obj):
        return [ruta.id for ruta in obj.RUTAS.all()]


# Clientes para realizar venta
class PrecioClienteVentaSerializer(BasePrecioClienteSerializer):
    producto_cantidad = serializers.FloatField(
        source="PRODUCTO.CANTIDAD", read_only=True
    )

    class Meta(BasePrecioClienteSerializer.Meta):
        fields = (
            "id",
            "producto_nombre",
            "producto_imagen",
            "producto_cantidad",
            "PRECIO",
            # This field is necessary in order to know what product we need to remove stock from
            "PRODUCTO",  # product id
        )


class ClienteVentaSerializer(serializers.ModelSerializer):
    precios_cliente = PrecioClienteVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente

        fields = ("id", "precios_cliente", "NOMBRE", "CIUDAD_REGISTRO")


# Venta


class ProductoVentaSerializer(serializers.ModelSerializer):
    # producto_nombre = serializers.CharField(source="PRODUCTO.NOMBRE", read_only=True)

    class Meta:
        model = ProductoVenta
        fields = "__all__"
        # fiels = ("id", "NOMBRE_PRODUCTO") Quiza esto es mejor para el rendimiento


class BaseVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = "__all__"


class VentaSerializer(BaseVentaSerializer):
    productos_venta = ProductoVentaSerializer(many=True, read_only=True)

    class Meta(BaseVentaSerializer.Meta):
        fields = "__all__"


class VentaReporteSerializer(BaseVentaSerializer):
    class Meta(BaseVentaSerializer.Meta):
        fields = [
            # "id",
            "FOLIO",
            "VENDEDOR",
            "NOMBRE_CLIENTE",
            "FECHA",
            "MONTO",
            "TIPO_VENTA",
            "TIPO_PAGO",
            "STATUS",
            "OBSERVACIONES",
            "DESCUENTO",
        ]


# Ruta


class BaseRutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruta
        fields = "__all__"


class RutaSerializer(BaseRutaSerializer):
    class Meta(BaseRutaSerializer.Meta):
        model = Ruta
        fields = "__all__"


class RutaRegistrarClienteSerializer(BaseRutaSerializer):
    # SerializerMethodField: It's often expensive to use SerializerMethodField. Make sure you are doing only necessary calculations inside them.
    ruta_dias = serializers.SerializerMethodField()
    # "ruta_dias": {
    #             "LUNES": 1,
    #             "MARTES": 2,
    #             "MIERCOLES": 3,
    #             "JUEVES": 4,
    #             "VIERNES": 5,
    #             "SABADO": 6,
    #             "DOMINGO": 7
    #         }

    class Meta(BaseRutaSerializer.Meta):
        model = Ruta
        fields = ["NOMBRE", "ruta_dias"]

    # Cada ruta dia tiene un id especifico que necesito usar cuando se registra el cliente, De esta manera asocio el cliente con un especifico conjunto de rutas
    def get_ruta_dias(self, obj):
        return {ruta_dia.DIA: ruta_dia.id for ruta_dia in obj.ruta_dias.all()}


class RutasConRutaDiaSerializer(serializers.ModelSerializer):
    # ruta_dias = RutasDiaRealizarSalidaRutaSerializer(many=True, read_only=True)
    ruta_dias = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ruta
        fields = ("NOMBRE", "id", "ruta_dias")

    def get_ruta_dias(self, obj):
        return [
            {
                "id": ruta_dia.id,
                "repartidor_id": (
                    ruta_dia.REPARTIDOR.id if ruta_dia.REPARTIDOR else None
                ),
                "DIA": ruta_dia.DIA,
            }
            for ruta_dia in obj.ruta_dias.all()
        ]


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

        # Dame todos las instancias de PrecioCliente que son hijas de mi papa (Cliente)
        for precio in PrecioCliente.objects.filter(CLIENTE=obj.CLIENTE_RUTA):
            # Serializar a mi hermano
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
        return precios_cliente


# I should use prefetch related for clients and products
class SalidaRutaSerializer(serializers.ModelSerializer):
    # Para esto si podria valer la pena usar prefetch_related
    productos = ProductoSalidaRutaSerializer(many=True, read_only=True)

    clientes = ClienteSalidaRutaSerializer(many=True, read_only=True)

    class Meta:
        model = SalidaRuta
        fields = "__all__"


class SalidaRutaSerializerSinClientes(serializers.ModelSerializer):

    # Asumiendo que ya tienes estos Serializers definidos correctamente
    productos = ProductoSalidaRutaSerializer(many=True, read_only=True)
    # Para clientes, podemos agregar el serializer si lo activas después
    # clientes = ClienteSalidaRutaSerializer(many=True, read_only=True)

    class Meta:
        model = SalidaRuta

        fields = "__all__"
        extra_kwargs = {
            "RUTA": {"write_only": True},
            "RUTA_NOMBRE": {"write_only": True},
            "REPARTIDOR": {"write_only": True},
            "STATUS": {"write_only": True},
        }


# LIGERO (Se usa en la lista de salida ruta)
class ProductoSalidaRutaSerializerLigero(serializers.ModelSerializer):
    class Meta:
        model = ProductoSalidaRuta
        fields = (
            # "id",
            "PRODUCTO_NOMBRE",
            "CANTIDAD_RUTA",
            "CANTIDAD_DISPONIBLE",
            "STATUS",
        )


class ClienteSalidaRutaSerializerLigero(serializers.ModelSerializer):
    # Accedemos a los atributos especificos de un hermano mediante un metodo

    class Meta:
        model = ClienteSalidaRuta
        fields = ("CLIENTE_NOMBRE", "STATUS")


class SalidaRutaSerializerLigero(serializers.ModelSerializer):
    # Para esto si podria valer la pena usar prefetch_related
    productos = ProductoSalidaRutaSerializerLigero(many=True, read_only=True)

    clientes = ClienteSalidaRutaSerializerLigero(many=True, read_only=True)

    class Meta:
        model = SalidaRuta
        fields = "__all__"


class DevolucionSalidaRutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DevolucionSalidaRuta
        fields = "__all__"


# Resumen
class ProductoSalidaRutaSerializerResumen(serializers.ModelSerializer):
    class Meta:
        model = ProductoSalidaRuta
        fields = (
            "id",
            "PRODUCTO_NOMBRE",
            "PRODUCTO_RUTA",
            "CANTIDAD_RUTA",
            "CANTIDAD_DISPONIBLE",
            "STATUS",
        )


class ClienteSalidaRutaSerializerResumen(serializers.ModelSerializer):
    # Accedemos a los atributos especificos de un hermano mediante un metodo

    class Meta:
        model = ClienteSalidaRuta
        fields = ("id", "CLIENTE_NOMBRE", "STATUS")


class SalidaRutaSerializerResumen(serializers.ModelSerializer):
    # Para esto si podria valer la pena usar prefetch_related
    productos = ProductoSalidaRutaSerializerResumen(many=True, read_only=True)

    clientes = ClienteSalidaRutaSerializerResumen(many=True, read_only=True)

    class Meta:
        model = SalidaRuta
        fields = (
            "id",
            "STATUS",
            "REPARTIDOR_NOMBRE",
            "ATIENDE",
            "productos",
            "clientes",
        )


# Salida Ruta acciones


class ProductoSalidaRutaSerializerAcciones(serializers.ModelSerializer):
    class Meta:
        model = ProductoSalidaRuta
        fields = (
            "id",
            "PRODUCTO_NOMBRE",
            "PRODUCTO_RUTA",
            "CANTIDAD_RUTA",
            "CANTIDAD_DISPONIBLE",
            "STATUS",
            "CANTIDAD RECARGA"
        )


class SalidaRutaSerializerAcciones(serializers.ModelSerializer):
    # Para esto si podria valer la pena usar prefetch_related
    productos = ProductoSalidaRutaSerializerAcciones(many=True, read_only=True)

    class Meta:
        model = SalidaRuta
        # fields = "__all__"
        fields = ("id", "STATUS", "productos", 
            # Hicimos cambios de prueba para arreglar ticket recarga
            "REPARTIDOR_NOMBRE",
            "ATIENDE",          
        )


class SalidaRutaReporteSerializer(BaseVentaSerializer):
    class Meta:

        model = SalidaRuta
        fields = [
            "id",
            "ATIENDE",
            "FECHA",
            "REPARTIDOR_NOMBRE",
            "OBSERVACIONES",
            "STATUS",
        ]
