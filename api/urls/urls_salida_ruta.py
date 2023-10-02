from django.urls import path
from api.views import views_salida_ruta

urlpatterns = [
    path("salida-rutas/", views_salida_ruta.salida_ruta_list),
    path("salida-rutas/<str:pk>/", views_salida_ruta.salida_ruta_detail),
    path("cancelar-salida-ruta/<str:pk>/", views_salida_ruta.cancelar_salida_ruta),
    path("crear-salida-ruta/", views_salida_ruta.crear_salida_ruta),
]