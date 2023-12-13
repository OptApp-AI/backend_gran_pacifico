from api.serializers import (
    UserSerializer,
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # This calls the parent class's validate method, which performs the necessary checks and creates a token pair
        data = super().validate(attrs)

        serializer = UserSerializer(self.user).data
        # Add user details to the token response
        for k, v in serializer.items():
            data[k] = v

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
