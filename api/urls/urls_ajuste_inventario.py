from django.urls import path
from api.views import view_ajuste_inventario

urlpatterns = [
    path("ajuste-inventario/", view_ajuste_inventario.ajuste_inventario_list),
    path(
        "ajuste-inventario-reporte/", view_ajuste_inventario.ajuste_inventario_reporte_list
    ),  # para generar el reporte necesitamos todas las venta. no una sola pagina
    path("crear-ajuste-inventario/", view_ajuste_inventario.crear_ajuste_inventario),
]
