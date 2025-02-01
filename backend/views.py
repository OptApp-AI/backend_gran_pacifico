from api.serializers import (
    UserSerializer,
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from api.views.utilis.salida_ruta import getLastSalidaRutaIdValido



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # This calls the parent class's validate method, which performs the necessary checks and creates a token pair
        data = super().validate(attrs)


        request = self.context.get("request")  # Obtiene el request desde el contexto
        origin = request.META.get("HTTP_ORIGIN", "") if request else ""

        if origin == "http://localhost:3000":
            username = attrs['username']

            salidaRutaId = getLastSalidaRutaIdValido(username)

            data["salida_ruta_id"] = salidaRutaId


        serializer = UserSerializer(self.user).data
        # Add user details to the token response
        for k, v in serializer.items():
            data[k] = v

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
