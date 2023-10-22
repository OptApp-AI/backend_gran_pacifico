from django.utils.dateparse import parse_date
from datetime import timedelta


# Create a function to handle date filtering
def filter_by_date(queryset, fechainicio, fechafinal):
    if fechainicio:
        fechainicio = parse_date(fechainicio)
    if fechafinal:
        fechafinal = parse_date(fechafinal) + timedelta(days=1)

    if fechainicio and fechafinal:
        return queryset.filter(FECHA__date__range=[fechainicio, fechafinal])
    elif fechainicio:
        return queryset.filter(FECHA__date__gte=fechainicio)
    elif fechafinal:
        return queryset.filter(FECHA__date__lte=fechafinal)
    return queryset
