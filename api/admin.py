from django.contrib import admin
from django.core.exceptions import ValidationError

from api.filters import AdminStatusFilter, ProductoNombreFilter
from .models import (
    Producto,
    Cliente,
    PrecioCliente,
    Venta,
    ProductoVenta,
    Direccion,
    Empleado,
    # Rutas
    Ruta,
    RutaDia,
    SalidaRuta,
    ClienteSalidaRuta,
    ProductoSalidaRuta,
    AjusteInventario,
    DevolucionSalidaRuta,
)


class EmpleadoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "ROLE",
        "CIUDAD_REGISTRO",
        "username",
        "is_user_staff",
        "is_user_superuser",
    )

    list_filter = (
        "ROLE",
        "CIUDAD_REGISTRO",
        AdminStatusFilter,  # Usa el filtro personalizado en lugar de USUARIO__is_staff
        "USUARIO__is_superuser",
    )

    sortable_by = [
        "nombre",
        "username",
    ]

    def nombre(self, obj):

        return obj.USUARIO.first_name

    nombre.admin_order_field = "USUARIO__first_name"

    def username(self, obj):

        return obj.USUARIO.username

    username.admin_order_field = "USUARIO__username"

    def is_user_staff(self, obj):
        return obj.USUARIO.is_staff

    def is_user_superuser(self, obj):
        return obj.USUARIO.is_superuser

    is_user_staff.short_description = "ADMINISTRADOR"  # Cambia el nombre de la columna


class ProductoAdmin(admin.ModelAdmin):
    list_display = ("NOMBRE", "CANTIDAD", "PRECIO", "CIUDAD_REGISTRO")

    list_filter = ("NOMBRE", "CIUDAD_REGISTRO")

    sortable_by = ["NOMBRE", "CANTIDAD", "PRECIO"]


class AjusteInventarioAdmin(admin.ModelAdmin):
    list_display = (
        "CAJERO",
        "BODEGA",
        "PRODUCTO_NOMBRE",
        "CANTIDAD",
        # "STATUS",
        "TIPO_AJUSTE",
        "FECHA",
        "CIUDAD_REGISTRO",
        "OBSERVACIONES",
    )

    list_filter = (
        "CAJERO",
        "PRODUCTO_NOMBRE",
        # "STATUS",
        "TIPO_AJUSTE",
        "CIUDAD_REGISTRO",
    )

    sortable_by = [
        "CAJERO",
        "BODEGA",
        "PRODUCTO_NOMBRE",
        "CANTIDAD",
        "FECHA",
    ]


class DireccionAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "CALLE",
        "NUMERO",
        "COLONIA",
        "CIUDAD",
        "ciudad_registro",
    )

    list_filter = ("cliente__CIUDAD_REGISTRO", "CIUDAD")

    sortable_by = [
        "cliente",
        "CALLE",
        "COLONIA",
        "CIUDAD",
    ]

    def cliente(self, obj):

        return obj.cliente.NOMBRE

    cliente.admin_order_field = "cliente__NOMBRE"

    def ciudad_registro(self, obj):

        return obj.cliente.CIUDAD_REGISTRO


class ClienteAdmin(admin.ModelAdmin):

    list_display = ("NOMBRE", "CIUDAD_REGISTRO", "ciudad")
    list_filter = ("CIUDAD_REGISTRO", "DIRECCION__CIUDAD")

    sortable_by = ["NOMBRE", "CIUDAD_REGISTRO", "ciudad"]

    def ciudad(self, obj):
        return obj.DIRECCION.CIUDAD

    ciudad.admin_order_field = "DIRECCION__CIUDAD"
    # ciudad.short_description = "CIUDAD"  # Cambia el nombre de la columna

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        instance = form.instance
        routes = instance.RUTAS.all()
        route_names = [ruta.RUTA.NOMBRE for ruta in routes]

        if len(set(route_names)) > 1:
            instance.delete()
            raise ValidationError(
                "All routes associated with a client must have the same name."
            )


class PrecioClienteAdmin(admin.ModelAdmin):
    list_display = ("cliente", "producto", "PRECIO", "ciudad_registro")

    list_filter = ("CLIENTE__CIUDAD_REGISTRO", ProductoNombreFilter)

    sortable_by = ["cliente", "producto", "PRECIO", "ciudad_registro"]

    def cliente(self, obj):
        return obj.CLIENTE.NOMBRE

    cliente.admin_order_field = "CLIENTE__NOMBRE"  # Ordenar por nombre del cliente

    def producto(self, obj):
        return obj.PRODUCTO.NOMBRE

    producto.admin_order_field = "PRODUCTO__NOMBRE"  # Ordenar por nombre del producto

    def ciudad_registro(self, obj):
        return obj.CLIENTE.CIUDAD_REGISTRO

    ciudad_registro.admin_order_field = (
        "CLIENTE__CIUDAD_REGISTRO"  # Ordenar por ciudad de registro del cliente
    )


# Register your models here.


class VentaAdmin(admin.ModelAdmin):
    list_display = (
        "VENDEDOR",
        "NOMBRE_CLIENTE",
        "FECHA",
        "TIPO_VENTA",
        "STATUS",
        "CIUDAD_REGISTRO",
    )

    list_filter = (
        "VENDEDOR",
        "NOMBRE_CLIENTE",
        "TIPO_VENTA",
        "STATUS",
        "CIUDAD_REGISTRO",
    )


class ProductoVentaAdmin(admin.ModelAdmin):
    list_display = (
        "VENTA",
        "NOMBRE_PRODUCTO",
        "CANTIDAD_VENTA",
        "PRECIO_VENTA",
        "ciudad_registro",
    )

    list_filter = (
        "NOMBRE_PRODUCTO",
        "VENTA__CIUDAD_REGISTRO",
    )

    def ciudad_registro(self, obj):

        return obj.VENTA.CIUDAD_REGISTRO


admin.site.register(Producto, ProductoAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(PrecioCliente, PrecioClienteAdmin)
admin.site.register(Venta, VentaAdmin)
admin.site.register(ProductoVenta, ProductoVentaAdmin)
admin.site.register(Direccion, DireccionAdmin)
admin.site.register(Empleado, EmpleadoAdmin)
admin.site.register(AjusteInventario, AjusteInventarioAdmin)

# Ruta


class RutaAdmin(admin.ModelAdmin):
    list_display = ("NOMBRE", "REPARTIDOR_NOMBRE", "CIUDAD_REGISTRO")

    list_filter = ("NOMBRE", "REPARTIDOR_NOMBRE", "CIUDAD_REGISTRO")


class RutaDiaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "REPARTIDOR_NOMBRE", "DIA", "ciudad_registro")

    list_filter = ("RUTA__NOMBRE", "REPARTIDOR_NOMBRE", "DIA")

    def nombre(self, obj):
        return obj.RUTA.NOMBRE

    def ciudad_registro(self, obj):
        return obj.RUTA.CIUDAD_REGISTRO

    # nombre.short_description = "NOMBRE"  # Cambia el nombre de la


class SalidaRutaAdmin(admin.ModelAdmin):
    list_display = (
        "ATIENDE",
        "RUTA_NOMBRE",
        "FECHA",
        "REPARTIDOR_NOMBRE",
        "STATUS",
        "CIUDAD_REGISTRO",
    )

    list_filter = (
        "ATIENDE",
        "RUTA_NOMBRE",
        "FECHA",
        "REPARTIDOR_NOMBRE",
        "STATUS",
        "CIUDAD_REGISTRO",
    )


class ProductoSalidaRutaAdmin(admin.ModelAdmin):
    list_display = (
        "PRODUCTO_NOMBRE",
        "CANTIDAD_RUTA",
        "CANTIDAD_DISPONIBLE",
        "STATUS",
        "ciudad_registro",
    )

    list_filter = (
        "PRODUCTO_NOMBRE",
        "STATUS",
        "SALIDA_RUTA__CIUDAD_REGISTRO",
    )

    def ciudad_registro(self, obj):

        return obj.SALIDA_RUTA.CIUDAD_REGISTRO


class ClienteSalidaRutaAdmin(admin.ModelAdmin):
    list_display = (
        "CLIENTE_NOMBRE",
        "STATUS",
        "ciudad_registro",
    )

    list_filter = (
        "CLIENTE_NOMBRE",
        "STATUS",
        "SALIDA_RUTA__CIUDAD_REGISTRO",
    )

    def ciudad_registro(self, obj):

        return obj.SALIDA_RUTA.CIUDAD_REGISTRO


class DevolucionSalidaRutaRutaAdmin(admin.ModelAdmin):
    list_display = (
        "REPARTIDOR",
        "ATIENDE",
        "ADMINISTRADOR",
        "FECHA",
        "PRODUCTO_NOMBRE",
        "CANTIDAD_DEVOLUCION",
        "STATUS",
    )

    list_filter = (
        "REPARTIDOR",
        "ATIENDE",
        "ADMINISTRADOR",
        "FECHA",
        "PRODUCTO_NOMBRE",
        "CANTIDAD_DEVOLUCION",
        "STATUS",
    )


admin.site.register(Ruta, RutaAdmin)
admin.site.register(RutaDia, RutaDiaAdmin)
admin.site.register(SalidaRuta, SalidaRutaAdmin)
admin.site.register(ClienteSalidaRuta, ClienteSalidaRutaAdmin)
admin.site.register(ProductoSalidaRuta, ProductoSalidaRutaAdmin)
admin.site.register(DevolucionSalidaRuta, DevolucionSalidaRutaRutaAdmin)
