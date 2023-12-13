from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from api.serializers import (
    UserSerializer,
)

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AnonymousUser


# @api_view(["GET"])
# def cuenta_detail(request):
#     # the first line of code retrieves the User object associated with the current request by accessing the user attribute of the request object. The request.user attribute is automatically populated by Django's authentication middleware, which verifies the user's credentials based on the authentication backend that is configured in the Django settings.
#     user = request.user

#     serializer = UserSerializer(user)

#     return Response(serializer.data)


@api_view(["PUT"])
def modificar_cuenta(request):
    user = request.user

    if isinstance(user, AnonymousUser):
        return Response(
            {"Detalles": "Necesitar autenticarte para modificar tu usuario"}
        )

    data = request.data
    password = data.get("password")
    imagen = data.get("IMAGEN")

    try:
        # 1. Modificar usuario
        user.username = data["username"]
        if password:
            user.password = make_password(password)
        user.first_name = data["name"].upper()
        user.save()

        # 2. Modificar empleado
        if imagen:
            empleado = user.empleado
            empleado.IMAGEN = data["IMAGEN"]
            empleado.save()

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except:
        return Response(
            {"Detalles": "Un usuario con este username ya existe"},
            status=status.HTTP_400_BAD_REQUEST,
        )
