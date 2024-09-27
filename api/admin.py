from django.contrib import admin
from django.core.exceptions import ValidationError
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


class ClienteAdmin(admin.ModelAdmin):


    list_display = ("NOMBRE", "CIUDAD_REGISTRO", "ciudad")

    def ciudad(self, obj):
        return obj.DIRECCION.CIUDAD

    ciudad.short_description = "CIUDAD"  # Cambia el nombre de la columna


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


# Register your models here.


class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("USUARIO", "CIUDAD_REGISTRO", "is_user_staff")

    def is_user_staff(self, obj):
        return obj.USUARIO.is_staff

    is_user_staff.short_description = "Is Staff"  # Cambia el nombre de la columna

class ProductoAdmin(admin.ModelAdmin):
    list_display = ("NOMBRE", "CANTIDAD", "CIUDAD_REGISTRO")

    list_filter = ("NOMBRE","CIUDAD_REGISTRO")


class AjusteInventarioAdmin(admin.ModelAdmin):
    list_display = ("CAJERO", "BODEGA", "PRODUCTO_NOMBRE", "CANTIDAD", "STATUS", "TIPO_AJUSTE", "FECHA", "CIUDAD_REGISTRO", "OBSERVACIONES")

    list_filter = ("CAJERO", "PRODUCTO_NOMBRE","STATUS","TIPO_AJUSTE","CIUDAD_REGISTRO")

class VentaAdmin(admin.ModelAdmin):
    list_display = ("VENDEDOR", "NOMBRE_CLIENTE", "FECHA", "TIPO_VENTA", "STATUS", "CIUDAD_REGISTRO")

    list_filter = ("VENDEDOR","NOMBRE_CLIENTE","TIPO_VENTA", "STATUS", "CIUDAD_REGISTRO")



admin.site.register(Producto, ProductoAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(PrecioCliente)
admin.site.register(Venta, VentaAdmin)
admin.site.register(ProductoVenta)
admin.site.register(Direccion)
admin.site.register(Empleado, EmpleadoAdmin)
admin.site.register(AjusteInventario,AjusteInventarioAdmin)

# Ruta
admin.site.register(Ruta)
admin.site.register(RutaDia)
admin.site.register(SalidaRuta)
admin.site.register(ClienteSalidaRuta)
admin.site.register(ProductoSalidaRuta)
admin.site.register(DevolucionSalidaRuta)
