from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from api.models import (
    Empleado,
)
from api.serializers import (
    UserSerializer,
)
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db.models.signals import post_save
from api.signals import create_empleado, save_empleado


@api_view(["GET"])
def usuario_list(request):
    nombreUsuario = request.GET.get("nombreUsuario", "")
    if nombreUsuario:
        queryset = User.objects.filter(username=nombreUsuario)
    else:
        queryset = User.objects.all().order_by("-id")

    # Usas el mismo serializador con tu cuenta que con el resto de usuarios! En lugar de esto cambia el serializador para tu cuenta. Use UserSerializerWithToken. De esta manera podras obtener el token de tu cuenta en el frontend.
    serializer = UserSerializer(queryset, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def crear_user(request):
    data = request.data

    # Esta validacion es hecha en el frontend tambien.
    # if data["password1"] != data["password2"]:
    #     return Response(
    #         {"Detalles": "Las constraseñas deben ser iguales"},
    #         status=status.HTTP_400_BAD_REQUEST,
    #     )

    # Desconectar la señal temporalmente para que django no intente crear el empleado dos veces para este mismo usuario
    post_save.disconnect(create_empleado, sender=User)
    post_save.disconnect(save_empleado, sender=User)
    try:
        user = User.objects.create(
            username=data["username"],
            password=make_password(data["password1"]),
            first_name=data["name"].upper(),
            is_staff=data["is_admin"] == "true",
        )
    except:
        return Response(
            {"message": "Usuario con este nombre de usuario ya existe"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Cuando el usuario se crea desde el frontend esto permit crear al empleado y guardar la imagen
    # La funcion create_emplado in signal.py es usada para crear el empleado cuando el usuario es creado del panel de django

    if data.get("IMAGEN"):
        Empleado.objects.create(
            USUARIO=user,
            IMAGEN=data["IMAGEN"],
        )
    else:
        Empleado.objects.create(USUARIO=user)

    # Reconectar la señal
    post_save.connect(create_empleado, sender=User)
    post_save.connect(save_empleado, sender=User)

    # Fijate como usas el mismo serializador (UserSerializer) para tu cuenta y para los usuarios. En realidad, debes crear un serializador llamado UserSerializerWithToken para poder obtener el token de tu cuenta ne el backend
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def usuario_detail(request, pk):
    try:
        usuario = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {"Detalles": "Usuario con el dado id no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = UserSerializer(usuario)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "DELETE"])
def modificar_usuario(request, pk):
    data = request.data

    try:
        usuario = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {"message": "Usuario con el id dado no existe"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "PUT":
        # Modificar permisos
        usuario.is_staff = data["is_admin"] == "true"
        usuario.save()

        serializer = UserSerializer(usuario)

        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "DELETE":
        usuario.delete()
        return Response(
            {"message": "Usuario fue eliminado existosamente"},
            status=status.HTTP_204_NO_CONTENT,
        )
