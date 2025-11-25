from api.models import SalidaRuta
from django.db.models import Max


# EJECUTAR DESPUES DE LA MIGRACION
def asignar_folios_salida_ruta_existentes():
    """
    Asigna folios numéricos positivos a las SalidaRuta con FOLIO=None.
    Mantiene secuencias independientes por CIUDAD_REGISTRO.
    """
    ciudades = SalidaRuta.objects.values_list("CIUDAD_REGISTRO", flat=True).distinct()

    for ciudad in ciudades:
        # Obtener el último folio existente para esta ciudad
        ultimo_folio = (
            SalidaRuta.objects.filter(CIUDAD_REGISTRO=ciudad, FOLIO__isnull=False)
            .aggregate(Max("FOLIO"))
            .get("FOLIO__max")
        )

        siguiente_folio = (ultimo_folio + 1) if ultimo_folio is not None else 1

        # Todas las filas sin folio en esta ciudad, ordenadas por id para estabilidad
        salidas_ruta_sin_folio = (
            SalidaRuta.objects.filter(CIUDAD_REGISTRO=ciudad, FOLIO__isnull=True)
            .only("id", "FOLIO")
            .order_by("id")
        )

        asignados = 0
        folio_inicial = siguiente_folio
        to_update = []
        for salida_ruta in salidas_ruta_sin_folio:
            salida_ruta.FOLIO = siguiente_folio
            siguiente_folio += 1
            asignados += 1
            to_update.append(salida_ruta)

        if to_update:
            SalidaRuta.objects.bulk_update(to_update, ["FOLIO"])

        if asignados > 0:
            print(
                f"Ciudad {ciudad}: Asignados {asignados} folios de salida ruta desde {folio_inicial} hasta {siguiente_folio - 1}"
            )
        else:
            print(f"Ciudad {ciudad}: No hay SalidaRuta sin folio")


# Uso desde shell Django:
# from backend_gran_pacifico.script_asignar_folio_salida_ruta_numerico import asignar_folios_salida_ruta_existentes
# asignar_folios_salida_ruta_existentes()
