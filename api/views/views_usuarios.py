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
from django.db import transaction


@api_view(["GET"])
def usuario_list(request):
    # I imagine that i use this for checking username availability?
    # nombreUsuario = request.GET.get("nombreUsuario", "")
    # if nombreUsuario:
    #     queryset = User.objects.prefetch_related("empleado").filter(
    #         username=nombreUsuario
    #     )
    # else:

    role = request.GET.get("role", "")

    if role == "repartidor":
        queryset = (
            User.objects.prefetch_related("empleado")
            .filter(empleado__ROLE="REPARTIDOR")
            .order_by("-id")
        )
    else:
        queryset = User.objects.prefetch_related("empleado").all().order_by("-id")

    # This serializer returns basic information about the users but not their token. The only way to obtain the token is through the login endpoint
    serializer = UserSerializer(queryset, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


# Si te fijas, necesitas crear el usuario sin usar el UserSerializer debido a que estas usando el modelo User de Django y eso limita la manera en que defines los campos. Por eso es mejor crear tu propio modelo User
@api_view(["POST"])
@transaction.atomic
def crear_user(request):
    data = request.data

    print("DATA", data)
    # Desconectar la señal temporalmente para que django no intente crear el empleado dos veces para este mismo usuario
    post_save.disconnect(create_empleado, sender=User)
    post_save.disconnect(save_empleado, sender=User)
    try:
        user = User.objects.create(
            username=data["username"],
            password=make_password(data["password1"]),
            first_name=data["name"].upper(),
            # The reason why we need to write this is because the content-type in the request is multipart/form-data which transforms all fields into files and strings
            is_staff=data["is_admin"] == "true",
        )
    except:
        return Response(
            {"message": "Usuario con este nombre de usuario ya existe"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Cuando el usuario se crea desde el frontend esto permit crear al empleado y guardar la imagen
    # Las funciones create_emplado y save_emplado en signal.py son usadas para crear y guardar el empleado de forma automatica cuando el usuario es creado del panel de Django. Por esa razon estas funciones deben ser desconectadas cuando el usuario se crea desde el frontend, para que no se intente crear o guardar el empleados dos veces.

    if data.get("IMAGEN"):
        Empleado.objects.create(USUARIO=user, IMAGEN=data["IMAGEN"], ROLE=data["role"])
    else:
        Empleado.objects.create(USUARIO=user, ROLE=data["role"])

    # Reconectar la señal
    post_save.connect(create_empleado, sender=User)
    post_save.connect(save_empleado, sender=User)

    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def usuario_detail(request, pk):
    try:
        usuario = User.objects.prefetch_related("empleado").get(pk=pk)
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
        # PORQUE SERA QUE EL FRONTEND envia "true" como string y no True?
        # aqui si debe enviar True
        usuario.is_staff = data["is_admin"]
        usuario.save()

        serializer = UserSerializer(usuario)

        empleado = Empleado.objects.get(USUARIO=usuario)

        empleado.ROLE = data.get("role")

        empleado.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "DELETE":
        usuario.delete()
        return Response(
            {"message": "Usuario fue eliminado existosamente"},
            status=status.HTTP_204_NO_CONTENT,
        )
