from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    # This is only for updating account, Account info is obtained in the login
    path("api/", include("api.urls.urls_cuenta")),
    path("api/", include("api.urls.urls_productos")),
    path("api/", include("api.urls.urls_clientes")),
    path("api/", include("api.urls.urls_ventas")),
    path("api/", include("api.urls.urls_usuarios")),
    path("api/", include("api.urls.urls_salida_ruta")),
    path("api/", include("api.urls.urls_ajuste_inventario")),
    # Login
    path("api/token/", views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
