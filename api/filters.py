from django.contrib.admin import SimpleListFilter


# Filtro personalizado para cambiar el título del filtro 'is_staff'
class AdminStatusFilter(SimpleListFilter):
    title = "Admin Status"  # Cambia el título aquí
    parameter_name = "admin_status"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Admin"),
            ("no", "Non-Admin"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(USUARIO__is_staff=True)
        if self.value() == "no":
            return queryset.filter(USUARIO__is_staff=False)


class ProductoNombreFilter(SimpleListFilter):
    title = "Nombre Producto"  # Aquí defines el nuevo título
    parameter_name = "PRODUCTO__NOMBRE"

    def lookups(self, request, model_admin):
        # Define las opciones de filtrado que quieres mostrar
        productos = set([p.PRODUCTO for p in model_admin.model.objects.all()])
        return [(p.pk, p.NOMBRE) for p in productos]

    def queryset(self, request, queryset):
        # Filtra el queryset basado en el valor seleccionado
        if self.value():
            return queryset.filter(PRODUCTO__pk=self.value())
        return queryset
