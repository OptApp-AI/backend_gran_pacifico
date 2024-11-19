from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Empleado(models.Model):
    # The related_name is the way I access the empleado instance from the user instance
    USUARIO = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="empleado"
    )
    # El problema de este codigo es que para los empleados creados sin subir una imagen, su imagen vive en default folder, y cuando se borranr se borra tambien la imagen de default
    # IMAGEN = models.ImageField(
    #     default='imagenes/default/usuario_default.png', upload_to='imagenes/empleados')

    IMAGEN = models.ImageField(upload_to="imagenes/empleados", null=True, blank=True)

    ROLE = models.CharField(
        max_length=255,
        choices=(
            ("GERENTE", "GERENTE"),
            ("CAJERO", "CAJERO"),
            ("REPARTIDOR", "REPARTIDOR"),
        ),
        default="CAJERO",
    )

    CIUDAD_REGISTRO = models.CharField(
        choices=(("LAZARO", "LAZARO"), ("URUAPAN", "URUAPAN")),
        max_length=15,
        default="URUAPAN",
        blank=False,
        db_index=True,
    )

    def __str__(self):
        return f"Empleado con usuario: {self.USUARIO.username}"


# Mostrador 7


# Create your models here.
class Producto(models.Model):
    NOMBRE = models.CharField(max_length=100)

    CANTIDAD = models.FloatField(validators=[MinValueValidator(0)])

    PRECIO = models.FloatField(validators=[MinValueValidator(0)])

    # IMAGEN = models.ImageField(
    #     default='imagenes/default/producto_default.jpg', upload_to='imagenes/productos')

    IMAGEN = models.ImageField(upload_to="imagenes/productos", null=True, blank=True)

    CIUDAD_REGISTRO = models.CharField(
        choices=(("LAZARO", "LAZARO"), ("URUAPAN", "URUAPAN")),
        max_length=15,
        default="URUAPAN",
        blank=False,
        db_index=True,
    )

    # RECUERDA NO PONER NADA QUE SE PUEDE VOLVER NULL AQUI
    def __str__(self):
        return f"{self.NOMBRE}, {self.CANTIDAD}, {self.PRECIO}"

    def save(self, *args, **kwargs):
        self.NOMBRE = self.NOMBRE.upper()

        if self.CANTIDAD < 0:
            raise ValidationError("La cantidad del producto no puede ser negativa.")

        super().save(*args, **kwargs)


# El ajuste de inventario va a quedar como pendiente hasta que un administrador lo autorice
class AjusteInventario(models.Model):
    # quiza deberia poner un foreign key a un empleado aqui
    CAJERO = models.CharField(max_length=200)

    BODEGA = models.CharField(max_length=200)
    # Should I add the admin filed in order to know who authorized this adjustemnt to inventory
    ADMINISTRADOR = models.CharField(max_length=200, blank=True)

    PRODUCTO = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    # The reason why i add the product name and not just the foreign key relationship is because if i delete the product, i want to have a way to know what product was used for this ajuste inventario row
    PRODUCTO_NOMBRE = models.CharField(max_length=200)

    CANTIDAD = models.FloatField(validators=[MinValueValidator(0)])

    TIPO_AJUSTE = models.CharField(
        max_length=10,
        choices=(
            ("FALTANTE", "FALTANTE"),
            ("SOBRANTE", "SOBRANTE"),
            ("PRODUCCION", "PRODUCCION"),
        ),
    )
    # status is pendiente until an admin changes the status to relizado
    # La cajera realiza el ajuste inventario, pero mientras el administrador no la autorice, el STATUS permanece como pendiente y la cajera no puede realizar el corte

    STATUS = models.CharField(
        max_length=200,
        choices=(("REALIZADO", "REALIZADO"), ("PENDIENTE", "PENDIENTE")),
        default="PENDIENTE",
    )

    FECHA = models.DateTimeField(auto_now=True)

    OBSERVACIONES = models.CharField(max_length=200, blank=True)

    CIUDAD_REGISTRO = models.CharField(
        choices=(("LAZARO", "LAZARO"), ("URUAPAN", "URUAPAN")),
        max_length=15,
        default="URUAPAN",
        blank=False,
        db_index=True,
    )

    def save(self, *args, **kwargs):
        self.PRODUCTO_NOMBRE = self.PRODUCTO_NOMBRE.upper()
        self.CAJERO = self.CAJERO.upper()
        self.BODEGA = self.BODEGA.upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.PRODUCTO_NOMBRE}, {self.TIPO_AJUSTE}, {self.CANTIDAD}"


# This model is just on allow model clients to add address information without creating too many fileds in Client model
class Direccion(models.Model):
    CALLE = models.CharField(max_length=200)
    NUMERO = models.CharField(max_length=200)
    COLONIA = models.CharField(max_length=200, null=True, blank=True)
    CIUDAD = models.CharField(max_length=200)
    MUNICIPIO = models.CharField(max_length=200, null=True, blank=True)
    CP = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)

    class Meta:
        verbose_name_plural = "Direcciones"

    def __str__(self):
        return f"{self.CALLE}, {self.NUMERO}, {self.COLONIA}"

    def save(self, *args, **kwargs):
        self.CALLE = self.CALLE.upper()
        if self.COLONIA:
            self.COLONIA = self.COLONIA.upper()
        self.CIUDAD = self.CIUDAD.upper()
        if self.MUNICIPIO:
            self.MUNICIPIO = self.MUNICIPIO.upper()
        super().save(*args, **kwargs)


# Cache: If your data doesn't change often, consider using caching mechanisms to serve your requests faster.
class Cliente(models.Model):
    TIPOS_DE_PAGO = (
        ("EFECTIVO", "EFECTIVO"),
        ("CREDITO", "CREDITO"),
    )

    NOMBRE = models.CharField(max_length=200, db_index=True)

    CONTACTO = models.CharField(max_length=200, null=True, blank=True)

    # Is this expensive?
    # Maybe I should add a select_related for this field?
    DIRECCION = models.OneToOneField(
        Direccion,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    # El telefono SIMEPRE es un CharField!
    TELEFONO = models.CharField(max_length=200)
    CORREO = models.CharField(max_length=200, null=True, blank=True)
    TIPO_PAGO = models.CharField(max_length=200, choices=TIPOS_DE_PAGO)

    OBSERVACIONES = models.CharField(max_length=200, blank=True)

    # Is this expensive?
    # Un cliente puede tener muchas rutas
    # Query Optimization: Use select_related or prefetch_related if your serialized model has ForeignKey or ManyToManyField to reduce database hits.
    RUTAS = models.ManyToManyField("RutaDia", blank=True, related_name="clientes_ruta")

    CIUDAD_REGISTRO = models.CharField(
        choices=(("LAZARO", "LAZARO"), ("URUAPAN", "URUAPAN")),
        max_length=15,
        default="URUAPAN",
        blank=False,
        db_index=True,
    )

    def save(self, *args, **kwargs):
        self.NOMBRE = self.NOMBRE.upper()
        if self.CONTACTO:
            self.CONTACTO = self.CONTACTO.upper()

        # Save the Cliente instance first
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the associated Direccion if it exists
        if self.DIRECCION:
            self.DIRECCION.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return str(self.NOMBRE)


# Is this expensive?
class PrecioCliente(models.Model):
    # Debido a que si se borrar cliente se debe de borrar el correspondiente precio(s). Aqui si tiene sentido usar el foreigkey y no solo el nombre del cliente. Los mismo para producto.
    CLIENTE = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="precios_cliente"
    )

    # Here i won't add CLIENTE_NOMBRE because it doesn't make sense to have a price of this client if the client  has been deleted.

    PRODUCTO = models.ForeignKey(Producto, on_delete=models.CASCADE)
    # si borro el producto no tiene caso tener el nombre del producto, por eso no lo puse aqui como otro campo

    PRECIO = models.FloatField(validators=[MinValueValidator(0)])  # REMOVE THIS FIELD
    # Maybe for the general code we should consider using relative prices just as Gabriel said
    # DESCUENTO = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)]) # ADD THIS FIELD

    # En este metodo nunca debes de poner algo que se pueda volver None. Por ejemplo, en este caso estamos seguros de que CLIENTE y PRODUCTO siempre seran valores distintos de None
    def __str__(self):
        return f"{self.CLIENTE.NOMBRE}, {self.PRODUCTO.NOMBRE}, {self.PRECIO}"


# Esta tabla se usa para registrar tanto ventas a mostrador como ventas en salida ruta

# Vamos a hacer la prueba de concepto con la tabla de ventas, luego lo hacemos con lo demas 
class Venta(models.Model):
    VENDEDOR = models.CharField(max_length=100)
    # Para ventas a mostrador existe el cliente mostrador que siempre tiene los precios generales de cada producto sin ningun descuento.

    # De igual forma, para las ventas en salida ruta debe existir un cliente para realizar ventas sin descuento (RUTA)
    CLIENTE = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)

    NOMBRE_CLIENTE = models.CharField(max_length=200, db_index=True)

    FECHA = models.DateTimeField(auto_now=True)

    MONTO = models.FloatField(validators=[MinValueValidator(0)])

    # Esto de tipo de pago sirve principalmente para distinguir entre ventas a mostrador y las ventas en salida ruta. Deberia de existir un campo adicional para identificar a que salida ruta pertenece la venta
    TIPO_VENTA = models.CharField(
        max_length=100, choices=(("MOSTRADOR", "MOSTRADOR"), ("RUTA", "RUTA"))
    )

    TIPO_PAGO = models.CharField(
        max_length=100,
        choices=(
            ("CONTADO", "CONTADO"),
            ("CREDITO", "CREDITO"),
            ("CORTESIA", "CORTESIA"),
        ),
    )

    STATUS = models.CharField(
        max_length=100,
        choices=(
            ("REALIZADO", "REALIZADO"),
            ("PENDIENTE", "PENDIENTE"),
            ("CANCELADO", "CANCELADO"),
        ),
    )

    OBSERVACIONES = models.CharField(max_length=100, blank=True)

    DESCUENTO = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    CIUDAD_REGISTRO = models.CharField(
        choices=(("LAZARO", "LAZARO"), ("URUAPAN", "URUAPAN")),
        max_length=15,
        default="URUAPAN",
        blank=False,
        db_index=True,
    )
    
    FOLIO = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['FOLIO', 'CIUDAD_REGISTRO'],
                name='unique_folio_ciudad'
            )
        ] 


    def __str__(self):
        return f"{self.TIPO_VENTA}, {self.MONTO}, {self.TIPO_PAGO}"


class ProductoVenta(models.Model):
    VENTA = models.ForeignKey(
        Venta, on_delete=models.CASCADE, related_name="productos_venta"
    )
    # SI CAMBIO STATUS DE PENDIENTE A CANCELADO O REALIZADO ES A TRAVES DE ESTA RELACION QUE PUEDO REGRESAR PRODUCTO AL STOCK
    PRODUCTO = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    # usando un ternario en js puedo decir que si el producto es null entonces en lugar de usar el producto.nombre se use el nombre_producto
    NOMBRE_PRODUCTO = models.CharField(max_length=200)

    CANTIDAD_VENTA = models.FloatField(validators=[MinValueValidator(0)])
    # quiza no requiero precio venta en el frontend?
    PRECIO_VENTA = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.VENTA}, {self.NOMBRE_PRODUCTO}"


# RUTA #################################################################################################################################
class Ruta(models.Model):
    NOMBRE = models.CharField(max_length=100, unique=True)

    REPARTIDOR = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True)
    # the reason why we add the delivery man name and not just the foreign key is because in case the emplado is deleted we need a way to know who was the delivery man for this ruta.

    # This is a valid approach for maintaining historical data, but it also means you need to ensure that REPARTIDOR_NOMBRE is updated whenever REPARTIDOR changes. This logic should be handled in the save method of your Ruta model or through Django signals.
    REPARTIDOR_NOMBRE = models.CharField(max_length=200)

    CIUDAD_REGISTRO = models.CharField(
        choices=(("LAZARO", "LAZARO"), ("URUAPAN", "URUAPAN")),
        max_length=15,
        default="URUAPAN",
        blank=False,
        db_index=True,
    )

    def save(self, *args, **kwargs):
        # Transform NAME to uppercase
        self.NOMBRE = self.NOMBRE.upper()
        self.REPARTIDOR_NOMBRE = self.REPARTIDOR_NOMBRE.upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.NOMBRE}, {self.REPARTIDOR_NOMBRE}"


class RutaDia(models.Model):
    # With cascade i make sure ruta dias are deleted when ruta is deleted
    RUTA = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name="ruta_dias")

    REPARTIDOR = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True)
    # This is a valid approach for maintaining historical data, but it also means you need to ensure that REPARTIDOR_NOMBRE is updated whenever REPARTIDOR changes. This logic should be handled in the save method of your Ruta model or through Django signals.
    REPARTIDOR_NOMBRE = models.CharField(max_length=200)

    DIA = models.CharField(
        max_length=100,
        choices=(
            ("LUNES", "LUNES"),
            ("MARTES", "MARTES"),
            ("MIERCOLES", "MIERCOLES"),
            ("JUEVES", "JUEVES"),
            ("VIERNES", "VIERNES"),
            ("SABADO", "SABADO"),
            ("DOMINGO", "DOMINGO"),
        ),
    )

    def save(self, *args, **kwargs):
        # Transform NAME to uppercase
        self.REPARTIDOR_NOMBRE = self.REPARTIDOR_NOMBRE.upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.RUTA.NOMBRE}, {self.DIA}, {self.REPARTIDOR_NOMBRE}"


# 1. LOS PRODUCTOS DE SALIDA A RUTA SE RETIRAN DEL STOCK CUANDO SE GENERA LA SALIDA RUTA
# 2. EXISTEN TRES STATUS PARA LA SALIDA RUTA: PENDIENTE, REALIZADO, CANCELADO. SIEMPRE SE GENERA CON STATUS PENDIENTE
# 3. EN GENERAL LOS CAMPOS SON SIMIILARES (ATIENDE, FECHA, OBSERVACIONES, ETC.) A LA TABLA VENTA
# 4. SE PUEDEN HACER DEVOLUCIONES. LAS DEVOLUCIONES LAS PUEDEN HACER CAJEROS PERO DEBEN SER AUTORIZADAS POR LOS ADMINISTRADORES
# 5. AL HACER UNA DEVOLUCION SE GENERA CON STATUS DE PENDIENTE. SOLO HASTA QUE EL ADMI CAMBIA SU STATUS A REALIZADO ES QUE SE REGRESAN LOS PRODUCTOS AL STOCK
# 6. CUANDO EL CAJERO ENTRE A LA SALIDARUTA, SOLO PUEDE DEVOLVER LOS PRODUCTOS CON STATUS DE CARGADO
class SalidaRuta(models.Model):
    ATIENDE = models.CharField(max_length=100)
    RUTA = models.ForeignKey(
        RutaDia,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="salida_rutas",
    )
    RUTA_NOMBRE = models.CharField(max_length=200, blank=True)
    FECHA = models.DateTimeField(auto_now=True)

    REPARTIDOR = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True)
    REPARTIDOR_NOMBRE = models.CharField(max_length=200)
    # Si hubo una devolucion en esta salida a ruta el administrador va a hacer la devolucion aqui
    OBSERVACIONES = models.CharField(max_length=200, blank=True)
    STATUS = models.CharField(
        max_length=100,
        choices=(
            # Sale como pendiente y permanece asi mientras no venda productos. Mientras el status sea pendiente se pueden cancelar siempre.
            ("PENDIENTE", "PENDIENTE"),
            # Una vez que se realiza una venta el status cambia a progreso. Si al final del corte hay productos, se requiere una devolucion para poder cambiar el status a realizado. De igual forma, si al momento de realizar el corte existen clientes sin visitar el status continuara siendo progreso y se requiere realizar un aviso de visita para cada cliente al que no se le ha vendido producto. Cuando el status es progreso se pueden realizar recargas con el fin de agregar mas producto a la salida ruta
            ("PROGRESO", "PROGRESO"),
            # Cambia a realizado cuando se vendieron todos los productos y se visito a todos los clientes.
            # Cada vez que se realiza una venta se verifica esto para ver si se debe cambiar el status a realizado
            ("REALIZADO", "REALIZADO"),
            # Se puede cancelar y todos los productos se regresan al almacen. Todos los ProductoSalidaRuta y ClienteSalidaRuta se cancelan.
            #  NO ES POSIBLE CANCELAR SI YA SE VENDIO ALGO (status es progreso) SOLO SE PUEDE CANCELAR UNA SALIDA RUTA CON STATUS DE PENDIENTE
            ("CANCELADO", "CANCELADO"),
        ),
    )

    CIUDAD_REGISTRO = models.CharField(
        choices=(("LAZARO", "LAZARO"), ("URUAPAN", "URUAPAN")),
        max_length=15,
        default="URUAPAN",
        blank=False,
        db_index=True,
    )

    def __str__(self):
        return f"{self.ATIENDE}, {self.REPARTIDOR_NOMBRE}"


# El status cambia a vendido hasta que todo el producto se vendio
class ProductoSalidaRuta(models.Model):
    # Si la salida a ruta se cancela los ProductoSalidaRuta se cancelan
    SALIDA_RUTA = models.ForeignKey(
        SalidaRuta, on_delete=models.CASCADE, related_name="productos"
    )
    # Aqui si usamos el objeto producto porque sera necesario acceder a este para hacer las devoluciones y tambien para cancelar salida ruta
    PRODUCTO_RUTA = models.ForeignKey(Producto, on_delete=models.CASCADE)
    PRODUCTO_NOMBRE = models.CharField(max_length=200)
    CANTIDAD_RUTA = models.FloatField(validators=[MinValueValidator(0)])
    CANTIDAD_DISPONIBLE = models.FloatField(validators=[MinValueValidator(0)])
    # SI CANCELAN LA SALIDARUTA LOS PRODUCTOS SE CANCELAN TAMBIEN. Una devolucion tambien ocasiona que los productos se cancelen
    # CANCELAR UN PRODUCTO ES LO QUE USARE PARA REGRESAR EL PRODUCTO AL STOCK

    STATUS = models.CharField(
        max_length=100,
        choices=(
            ("CARGADO", "CARGADO"),
            ("VENDIDO", "VENDIDO"),
        ),
    )

    def __str__(self):
        return f"{self.SALIDA_RUTA}, {self.PRODUCTO_NOMBRE}"


# No tiene el precio, pero accede a ellos mediante su hermano PrecioCliente.
class ClienteSalidaRuta(models.Model):
    # Si la salida ruta se cancela los ClienteSalidaRuta se cancelan
    SALIDA_RUTA = models.ForeignKey(
        SalidaRuta, on_delete=models.CASCADE, related_name="clientes"
    )

    CLIENTE_RUTA = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    CLIENTE_NOMBRE = models.CharField(max_length=200)
    STATUS = models.CharField(
        max_length=100,
        choices=(
            ("PENDIENTE", "PENDIENTE"),
            ("VISITADO", "VISITADO"),
        ),
    )

    def __str__(self):
        return f"{self.SALIDA_RUTA}, {self.CLIENTE_RUTA}"


# Las devoluciones tienen que ser devoluciones reales, si el repartidor regresa para hacer una recarga no se va a devolver todo lo que se cargo, en todo caso la salida ruta debe poder ser actualizada para agregar mas productos (o clientes). Esto implicaria crear una vista que permita actualizar la salida ruta y crear mas productos salida ruta.
# En el frontend esto va a ser una recarga de salida ruta
class DevolucionSalidaRuta(models.Model):
    REPARTIDOR = models.CharField(max_length=200)
    ATIENDE = models.CharField(max_length=200)
    ADMINISTRADOR = models.CharField(max_length=200, blank=True)
    SALIDA_RUTA = models.ForeignKey(
        SalidaRuta, on_delete=models.CASCADE, related_name="salida_ruta_devoluciones"
    )
    PRODUCTO_DEVOLUCION = models.ForeignKey(
        Producto, on_delete=models.SET_NULL, null=True
    )
    PRODUCTO_NOMBRE = models.CharField(max_length=200)
    CANTIDAD_DEVOLUCION = models.FloatField(validators=[MinValueValidator(0)])
    # La cajera realiza la devolución, pero mientras el administrador no la autorice, el STATUS permanece como pendiente y la cajera no puede realizar el corte
    STATUS = models.CharField(
        max_length=200,
        choices=(("REALIZADO", "REALIZADO"), ("PENDIENTE", "PENDIENTE")),
        default="PENDIENTE",
    )
    OBSERVACIONES = models.CharField(max_length=200, blank=True)

    FECHA = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.SALIDA_RUTA}, {self.CANTIDAD_DEVOLUCION}"
