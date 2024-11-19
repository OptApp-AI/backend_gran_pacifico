from django.utils.timezone import utc
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
import pytz
from api.models import Empleado


def obtener_ciudad_registro(request):

    # auth = request.headers.get("Authorization", None)

    # token = auth.split()[1]
    # decoded_token = JWTAuthentication().get_validated_token(token)
    # user_id = decoded_token["user_id"]  # o 'user' si usas otro campo

    try:
        print("USER", request.user)
        empleado = Empleado.objects.get(USUARIO=request.user)

        ciudad_registro = empleado.CIUDAD_REGISTRO
    except:

        print("BEOOOO", request)
        ciudad_registro = "URUAPAN"

    return ciudad_registro


def obtener_nombre_con_sufijo(ciudad_registro, username):

    if ciudad_registro == "URUAPAN":

        return username + "_urp"

    return username + "_laz"


def filter_by_date(queryset, fechainicio, fechafinal):
    # Definir explícitamente la zona horaria de México
    mexico_tz = pytz.timezone("America/Mexico_City")

    # Convertir fechainicio a UTC
    if fechainicio:
        fechainicio = parse_date(fechainicio)  # Esto devuelve un objeto datetime.date
        if fechainicio:
            # Convertir a datetime combinando con una hora (00:00)
            fechainicio = datetime.combine(fechainicio, datetime.min.time())
            # Convertir a horario de México y luego a UTC
            fechainicio = mexico_tz.localize(fechainicio).astimezone(utc)

    # Convertir fechafinal a UTC
    if fechafinal:
        fechafinal = parse_date(fechafinal)
        if fechafinal:
            # Convertir a datetime combinando con una hora (23:59)
            fechafinal = datetime.combine(fechafinal, datetime.min.time())
            # Añadir un día para incluir el día completo
            fechafinal = (
                mexico_tz.localize(fechafinal) + timedelta(days=1)
            ).astimezone(utc)

    # Aplicar los filtros de fecha con UTC
    if fechainicio and fechafinal:
        return queryset.filter(FECHA__range=[fechainicio, fechafinal])
    elif fechainicio:
        return queryset.filter(FECHA__gte=fechainicio)
    elif fechafinal:
        return queryset.filter(FECHA__lte=fechafinal)

    return queryset
