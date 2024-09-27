from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.models import Empleado


def obtener_ciudad_registro(request):

    # auth = request.headers.get("Authorization", None)

    # token = auth.split()[1]
    # decoded_token = JWTAuthentication().get_validated_token(token)
    # user_id = decoded_token["user_id"]  # o 'user' si usas otro campo

    empleado = Empleado.objects.get(USUARIO=request.user)

    ciudad_registro = empleado.CIUDAD_REGISTRO

    return ciudad_registro


def obtener_nombre_usuario(ciudad_registro, username):

    if ciudad_registro == "URUAPAN": 

        return  username + "_urp"
    
    return username + "_laz"