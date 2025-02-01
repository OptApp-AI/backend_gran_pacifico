from api.models import ClienteSalidaRuta, ProductoSalidaRuta, SalidaRuta,  Empleado

from django.core.exceptions import ObjectDoesNotExist

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





def getLastSalidaRutaIdValido(username):
    # Obtener el empleado relacionado al usuario
    try:
        empleado = Empleado.objects.get(USUARIO__username=username)
    except ObjectDoesNotExist:
        return 0  # Si el usuario no existe, devolvemos 0
    
    # Obtener solo el ID de la última SalidaRuta válida
    salida_ids = SalidaRuta.objects.filter(
        REPARTIDOR=empleado, STATUS__in=["PENDIENTE", "PROGRESO"]
    ).order_by("-FECHA").values_list("id", flat=True)

    print(salida_ids)

    # Si no hay ninguna o hay más de una, devolvemos 0
    # return salida_ids[0] if len(salida_ids) == 1 else 0
    return salida_ids[0]  if len(salida_ids) > 0 else 0