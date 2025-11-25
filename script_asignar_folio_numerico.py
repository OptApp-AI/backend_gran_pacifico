from api.models import Venta
from django.db.models import Max

# EJECUTAR ANTES DE LA MIGRACION


def asignar_folios_numerico_a_ventas_existentes_con_folio_none():
    """
    Asigna folios a las ventas que tienen FOLIO=None.
    Mantiene la unicidad por CIUDAD_REGISTRO asignando folios secuenciales.
    """
    # Obtener todas las ciudades
    ciudades = Venta.objects.values_list("CIUDAD_REGISTRO", flat=True).distinct()

    for ciudad in ciudades:
        # Obtener el último folio existente para esta ciudad
        ultimo_folio = (
            Venta.objects.filter(CIUDAD_REGISTRO=ciudad, FOLIO__isnull=False)
            .aggregate(Max("FOLIO"))
            .get("FOLIO__max")
        )

        # Si no hay folios existentes, empezar desde 0
        siguiente_folio = (ultimo_folio + 1) if ultimo_folio is not None else 1

        # Obtener todas las ventas de esta ciudad sin folio, ordenadas por ID
        ventas_sin_folio = Venta.objects.filter(
            CIUDAD_REGISTRO=ciudad, FOLIO__isnull=True
        ).order_by("id")

        # Asignar folios secuenciales
        cantidad_asignados = 0
        folio_inicial = siguiente_folio

        for venta in ventas_sin_folio:
            venta.FOLIO = siguiente_folio
            venta.save()
            siguiente_folio += 1
            cantidad_asignados += 1

        if cantidad_asignados > 0:
            print(
                f"Ciudad {ciudad}: Asignados {cantidad_asignados} folios desde {folio_inicial} hasta {siguiente_folio - 1}"
            )
        else:
            print(f"Ciudad {ciudad}: No hay ventas sin folio")
