# from django.utils.timezone import utc
# from django.utils.dateparse import parse_date
# from datetime import datetime, timedelta
# import pytz


# def filter_by_date(queryset, fechainicio, fechafinal):
#     # Definir explícitamente la zona horaria de México
#     mexico_tz = pytz.timezone("America/Mexico_City")

#     # Convertir fechainicio a UTC
#     if fechainicio:
#         fechainicio = parse_date(fechainicio)  # Esto devuelve un objeto datetime.date
#         if fechainicio:
#             # Convertir a datetime combinando con una hora (00:00)
#             fechainicio = datetime.combine(fechainicio, datetime.min.time())
#             # Convertir a horario de México y luego a UTC
#             fechainicio = mexico_tz.localize(fechainicio).astimezone(utc)

#     # Convertir fechafinal a UTC
#     if fechafinal:
#         fechafinal = parse_date(fechafinal)
#         if fechafinal:
#             # Convertir a datetime combinando con una hora (23:59)
#             fechafinal = datetime.combine(fechafinal, datetime.min.time())
#             # Añadir un día para incluir el día completo
#             fechafinal = (
#                 mexico_tz.localize(fechafinal) + timedelta(days=1)
#             ).astimezone(utc)

#     # Aplicar los filtros de fecha con UTC
#     if fechainicio and fechafinal:
#         return queryset.filter(FECHA__range=[fechainicio, fechafinal])
#     elif fechainicio:
#         return queryset.filter(FECHA__gte=fechainicio)
#     elif fechafinal:
#         return queryset.filter(FECHA__lte=fechafinal)

#     return queryset
