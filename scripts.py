from api.models import Venta

def asignar_folios_existentes():
    ventas = Venta.objects.all()
    for venta in ventas:
        venta.FOLIO = venta.id  # Asigna el id actual como folio
        venta.save()
