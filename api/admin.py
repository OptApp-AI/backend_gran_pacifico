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


admin.site.register(Producto)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(PrecioCliente)
admin.site.register(Venta)
admin.site.register(ProductoVenta)
admin.site.register(Direccion)
admin.site.register(Empleado, EmpleadoAdmin)

# Ruta
admin.site.register(Ruta)
admin.site.register(RutaDia)
admin.site.register(SalidaRuta)
admin.site.register(ClienteSalidaRuta)
admin.site.register(ProductoSalidaRuta)
admin.site.register(AjusteInventario)
admin.site.register(DevolucionSalidaRuta)
