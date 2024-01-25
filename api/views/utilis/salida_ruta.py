from api.models import ClienteSalidaRuta, ProductoSalidaRuta, SalidaRuta


# Obtener todos los  productos de la salida ruta


def verificar_salida_ruta_completada(salida_ruta):
    clientes_salida_ruta = ClienteSalidaRuta.objects.filter(SALIDA_RUTA=salida_ruta)
    productos_salida_ruta = ProductoSalidaRuta.objects.filter(SALIDA_RUTA=salida_ruta)

    # Verificar si el STATUS de todos los clientes salida ruta es VISITADO
    all_clientes_visited = all(
        cliente.STATUS == "VISITADO" for cliente in clientes_salida_ruta
    )

    # Verificar si el STATUS de todos los productos salida ruta es VENDIDO
    all_productos_sold = all(
        producto.STATUS == "VENDIDO" for producto in productos_salida_ruta
    )
    # Si esto se cumple cambia el STATUS de salida ruta a realizado
    if all_productos_sold and all_clientes_visited:
        salida_ruta.STATUS = "REALIZADO"
    # Si no se cumple verifica si el STATUS de salida ruta es PENDIENTE
    elif salida_ruta.STATUS == "PENDIENTE":
        # Si esto se cumple cambia el STATUS de salida ruta de PROGRESO
        salida_ruta.STATUS = "PROGRESO"

    salida_ruta.save()


from django.utils.dateparse import parse_date
from datetime import timedelta


# Create a function to handle date filtering
def filter_by_date(queryset, fechainicio, fechafinal):
    if fechainicio:
        fechainicio = parse_date(fechainicio)
    if fechafinal:
        fechafinal = parse_date(fechafinal) + timedelta(days=1)

    if fechainicio and fechafinal:
        print(fechainicio, fechafinal)
        return queryset.filter(FECHA__date__range=[fechainicio, fechafinal])
    elif fechainicio:
        return queryset.filter(FECHA__date__gte=fechainicio)
    elif fechafinal:
        return queryset.filter(FECHA__date__lte=fechafinal)
    return queryset
