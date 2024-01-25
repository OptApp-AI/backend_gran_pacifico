from django.urls import path
from api.views import views_salida_ruta

urlpatterns = [
    path("salida-rutas/", views_salida_ruta.salida_ruta_list),
    path("salida-rutas/<str:pk>/", views_salida_ruta.salida_ruta_detail),
    path("cancelar-salida-ruta/<str:pk>/", views_salida_ruta.cancelar_salida_ruta),
    path("crear-salida-ruta/", views_salida_ruta.crear_salida_ruta),
    path(
        "crear-venta-salida-ruta/<str:pk>/", views_salida_ruta.crear_venta_salida_ruta
    ),
    path(
        "devolver-producto-salida-ruta/<str:pk>/",
        views_salida_ruta.devolver_producto_salida_ruta,
    ),
    path("realizar-aviso-visita/<str:pk>/", views_salida_ruta.realizar_aviso_visita),
    path("devoluciones/", views_salida_ruta.devolucion_list),
    path("devoluciones/<str:pk>/", views_salida_ruta.devolucion_detalles),
    path(
        "realizar-recarga-salida-ruta/<str:pk>/",
        views_salida_ruta.realizar_recarga_salida_ruta,
    ),
]
