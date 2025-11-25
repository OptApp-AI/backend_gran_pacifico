from api.models import Venta

# EJECUTAR DESPUES DE LA MIGRACION


def convertir_folios_string_numerico_a_prefijado():
    """
    Convierte FOLIOs que actualmente son strings numéricos ("1", "2", ...)
    al nuevo formato con prefijo por tipo y secuencia independiente por ciudad:
      - MOSTRADOR: M-<n>
      - RUTA:      R-<n>

    Reglas:
      - Solo actualiza ventas con FOLIO que coinciden con ^\n\d+$ (string numérico).
      - Mantiene secuencias independientes por CIUDAD_REGISTRO y TIPO_VENTA.
      - Continúa la secuencia desde el máximo ya prefijado para evitar colisiones.
    """

    ciudades = Venta.objects.values_list("CIUDAD_REGISTRO", flat=True).distinct()

    for ciudad in ciudades:
        for tipo_venta, prefijo in (("MOSTRADOR", "M-"), ("RUTA", "R-")):
            # 1) Encontrar el último folio PRE-FIJADO existente para continuar la secuencia
            ultimo_prefijado = (
                Venta.objects.filter(
                    CIUDAD_REGISTRO=ciudad,
                    TIPO_VENTA=tipo_venta,
                    FOLIO__startswith=prefijo,
                )
                .order_by("-id")
                .values_list("FOLIO", flat=True)
                .first()
            )
            try:
                siguiente_num = (
                    int(str(ultimo_prefijado).split("-", 1)[1]) + 1
                    if ultimo_prefijado
                    else 1
                )
            except Exception:
                siguiente_num = 1

            # 2) Obtener ventas con FOLIO que es string numérico puro
            ventas_numericas = (
                Venta.objects.filter(
                    CIUDAD_REGISTRO=ciudad,
                    TIPO_VENTA=tipo_venta,
                    FOLIO__regex=r"^\d+$",
                )
                .only("id", "FOLIO")
                .order_by("id")
            )

            if not ventas_numericas.exists():
                continue

            # 3) Actualizar en memoria y hacer bulk_update por eficiencia
            to_update = []
            for v in ventas_numericas:
                v.FOLIO = f"{prefijo}{siguiente_num}"
                siguiente_num += 1
                to_update.append(v)

            if to_update:
                Venta.objects.bulk_update(to_update, ["FOLIO"])
                print(
                    f"Ciudad {ciudad} {tipo_venta}: actualizados {len(to_update)} folios a formato {prefijo}<n>"
                )


# Si se desea ejecutar directamente desde shell:
# from backend_gran_pacifico.script_asignar_folio_desde_string_numerico import asignar_folios_desde_string_numerico
# asignar_folios_desde_string_numerico()
