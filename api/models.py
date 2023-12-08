from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Empleado(models.Model):
    USUARIO = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="empleado"
    )
    # El problema de este codigo es que para los empleados creados sin subir una imagen, su imagen vive en default folder, y cuando se borranr se borra tambien la imagen de default
    # IMAGEN = models.ImageField(
    #     default='imagenes/default/usuario_default.png', upload_to='imagenes/empleados')

    IMAGEN = models.ImageField(upload_to="imagenes/empleados", null=True, blank=True)

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

    # RECUERDA NO PONER NADA QUE SE PUEDE VOLVER NULL AQUI
    def __str__(self):
        return f"{self.NOMBRE}, {self.CANTIDAD}, {self.PRECIO}"

    def save(self, *args, **kwargs):
        self.NOMBRE = self.NOMBRE.upper()

        super().save(*args, **kwargs)


class AjusteInventario(models.Model):
    CAJERO = models.CharField(max_length=200)

    BODEGA = models.CharField(max_length=200)
    # ADMINISTRADOR = models.CharField(max_length=200)

    PRODUCTO = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    # The reason why i add the product name and not just the foreign key relationship is because if i delete the product, i want to have a way to know what product was used for this ajuste inventario row
    PRODUCTO_NOMBRE = models.CharField(max_length=200)

    CANTIDAD = models.FloatField(validators=[MinValueValidator(0)])

    TIPO_AJUSTE = models.CharField(
        max_length=10, choices=(("FALTANTE", "FALTANTE"), ("SOBRANTE", "SOBRANTE"))
    )

    STATUS = models.CharField(
        max_length=200,
        choices=(("REALIZADO", "REALIZADO"), ("PENDIENTE", "PENDIENTE")),
        default="PENDIENTE",
    )

    OBSERVACIONES = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        self.PRODUCTO_NOMBRE = self.PRODUCTO_NOMBRE.upper()
        self.CAJERO = self.CAJERO.upper()
        self.BODEGA = self.BODEGA.upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.PRODUCTO_NOMBRE}, {self.TIPO_AJUSTE}, {self.CANTIDAD}"


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

    NOMBRE = models.CharField(max_length=200)

    CONTACTO = models.CharField(max_length=200, null=True, blank=True)

    # Is this expensive?
    DIRECCION = models.OneToOneField(
        Direccion, on_delete=models.CASCADE, blank=True, null=True
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

    PRODUCTO = models.ForeignKey(Producto, on_delete=models.CASCADE)
    # si borro el producto no tiene caso tener el nombre del producto, por eso no lo puse aqui como otro campo

    PRECIO = models.FloatField(validators=[MinValueValidator(0)])  # REMOVE THIS FIELD
    # DESCUENTO = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)]) # ADD THIS FIELD

    # En este metodo nunca debes de poner algo que se pueda volver None. Por ejemplo, en este caso estamos seguros de que CLIENTE y PRODUCTO siempre seran valores distintos de None
    def __str__(self):
        return f"{self.CLIENTE.NOMBRE}, {self.PRODUCTO.NOMBRE}, {self.PRECIO}"


class Venta(models.Model):
    VENDEDOR = models.CharField(max_length=100)

    # Creo que deberia cambia el foreigkey por un charfield
    # no necesito el cliente entero para registrar una venta, solo necesito su nombre
    # Ya lo puedo borrar (Lo voy a dejar por ahora, pero no lo necesito)
    CLIENTE = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    # la razon por la que registro el nombre del cliente ademas del foreign key es porque en caso de borrar el cliente quiero saber a que cliente se le realizo la venta, incluso si ese cliente no existe en la base de datos
    NOMBRE_CLIENTE = models.CharField(max_length=200)

    FECHA = models.DateTimeField(auto_now=True)

    MONTO = models.FloatField(validators=[MinValueValidator(0)])

    # Esto de tipo de pago sirve principalmente para distinguir entre ventas a mostrador y las ventas en salida ruta
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

    def __str__(self):
        return f"{self.TIPO_VENTA}, {self.MONTO}, {self.TIPO_PAGO}"


class ProductoVenta(models.Model):
    VENTA = models.ForeignKey(
        Venta, on_delete=models.CASCADE, related_name="productos_venta"
    )
    # Tampoco necesito el id del producto, solo su nombre. En realidad no es tan importante dejar o no esta relacion. Lo que importa es que hacer cuando un producto es eliminado, en este caso el producto venta permanece con producto igual a null.
    # Una razon para usar el id y no el nombre al momento de registrar el producto venta, es si es importante actualizar el producto venta cuando el producto es actualizado, por ejemplo, cambiar el nombre.
    PRODUCTO = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    NOMBRE_PRODUCTO = models.CharField(max_length=200)

    CANTIDAD_VENTA = models.FloatField(validators=[MinValueValidator(0)])
    PRECIO_VENTA = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.VENTA}, {self.NOMBRE_PRODUCTO}"


# RUTA 6


class Ruta(models.Model):
    NOMBRE = models.CharField(max_length=100, unique=True)

    REPARTIDOR = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True)
    # the reason why we add the delivery man name and not just the foreign key is because in case the emplado is deleted we need a way to know who was the delivery man for this ruta
    REPARTIDOR_NOMBRE = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        # Transform NAME to uppercase
        self.NOMBRE = self.NOMBRE.upper()
        self.REPARTIDOR_NOMBRE = self.REPARTIDOR_NOMBRE.upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.NOMBRE}, {self.REPARTIDOR_NOMBRE}"


class RutaDia(models.Model):
    RUTA = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name="ruta_dias")

    REPARTIDOR = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True)
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


# 1. LOS PRODUCTOS DE SALIDA A RUTA SE RETIRAN DEL STOCK SIEMPRE. NO IMPORTA EL STATUS
# 2. EXISTEN LOS MISMOS TRES STATUS: PENDIENTE, REALIZADO, CANCELADO. SIEMPRE SE GENERA CON STATUS PENDIENTE
# 3. EN GENERAL LOS CAMPOS SON SIMIILARES (ATIENDE, FECHA, OBSERVACIONES, ETC.)
# 5. SE PUEDEN HACER DEVOLUCIONES. LAS DEVOLUCIONES LAS PUEDEN HACER CAJEROS (LUEGO VEMOS A LOS ADMIS)
# 6. AL HACER ESTO SE GENERA UNA DEVOLUCION CON STATUS DE PENDIENTE. SOLO HASTA QUE EL ADMI CAMBIA SU STATUS A REALIZADO ES QUE SE REGRESAN LOS PRODUCTOS AL STOCK
# ESTA ES UNA PREGUNTA IMPORTANTE ¿DEBERIAN DE REGRESARSE LOS PRODUCTOS AL STOCK EN EL MOMENTO QUE EL CAJERO REALIZA LA DEVOLUCION, O ESPERAMOS HASTA QUE EL ADMIN LA AUTORIZA?
# 7. CUANDO EL CAJERO ENTRE A LA SALIDARUTA, SOLO PUEDE DEVOLVER LOS PRODUCTOS CON STATUS DE CARGADO
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

    # Aquí cambiar esto por un Empleado. PARA QUE QUIERES AL EMPLEADO, NECESITAS ACCEDER A ALGUN DATOS DEL EMPLEADO DESDE LA SALIDA RUTA
    # CUANDO EL REPARTIDOR INICIE SESSION, COMO VA A ACCEDER A LA SalidRuta. DEBERIA DE TENER SOLO UNA SalidaRuta con STATUS de pendiente o progreso, y es a traves de este campo que el va a acceder.
    REPARTIDOR = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True)
    REPARTIDOR_NOMBRE = models.CharField(max_length=200)
    # Si hubo una devolucion en esta salida a ruta el administrador va a hacer la devolucion aqui
    OBSERVACIONES = models.CharField(max_length=200, blank=True)
    STATUS = models.CharField(
        max_length=100,
        choices=(
            # Sale como pendiente mientras no venda todos los productos. Si al final del corte hay productos y se requiere una devolucion. Es necesario hacer una devolucion para cambiar el status a realizado. O bien, se pueden cancelar.
            ("PENDIENTE", "PENDIENTE"),
            ("PROGRESO", "PROGRESO"),
            # Cambia a realizado cuando vendio todos los productos
            # Cada vez que se vende un ProductoSalidaRuta de esta salida ruta se verifica esto para ver si se debe cambiar
            ("REALIZADO", "REALIZADO"),
            # Se puede cancelar y todos los productos se regresan al almacen. Todos los ProductoSalidaRuta y ClienteSalidaRuta se cancelan.
            #  NO ES POSIBLE CANCELAR SI YA SE VENDIO ALGO
            ("CANCELADO", "CANCELADO"),
        ),
    )

    def __str__(self):
        # DESPUES HAY QUE CAMBIAR ESTO PORQUE SI SE BORRA EL ATIENDE O REPARTIDOR VAN A EXISTIR PROBLEMAS. NO EN REALIDAD PORQUE ATIENDE ES UN CHARFIELD, usar empleado_nombre EN LUGAR DE EMPLEADO, para que no haya problemas
        return f"{self.ATIENDE}, {self.REPARTIDOR_NOMBRE}"


# El status cambia a vendido hasta que todo el producto se vendio
class ProductoSalidaRuta(models.Model):
    # Si la salida a ruta se cancela los ProductoSalidaRuta se cancelan
    SALIDA_RUTA = models.ForeignKey(
        SalidaRuta, on_delete=models.CASCADE, related_name="productos"
    )
    # Aqui si usamos el objeto producto porque sera necesario acceder a este para hacer las devoluciones
    PRODUCTO_RUTA = models.ForeignKey(Producto, on_delete=models.CASCADE)
    PRODUCTO_NOMBRE = models.CharField(max_length=200)
    CANTIDAD_RUTA = models.IntegerField(validators=[MinValueValidator(0)])
    CANTIDAD_DISPONIBLE = models.IntegerField(validators=[MinValueValidator(0)])
    # SI CANCELAN LA SALIDARUTA LOS PRODUCTOS SE CANCELAN TAMBIEN. Una devolucion tambien ocasiona que los productos se cancelen
    # CANCELAR UN PRODUCTO ES LO QUE USARE PARA REGRESAR EL PRODUCTO AL STOCK

    # REMOVER ESTE CAMPO
    STATUS = models.CharField(
        max_length=100,
        choices=(
            ("CARGADO", "CARGADO"),
            ("VENDIDO", "VENDIDO"),
            ("CANCELADO", "CANCELADO"),
        ),
    )

    def __str__(self):
        return f"{self.SALIDA_RUTA}, {self.PRODUCTO_NOMBRE}"


# No tiene el precio, pero accede a ellos mediante su hermano PrecioCliente.
class ClienteSalidaRuta(models.Model):
    # Si la salida ruta se cancela los ClienteSalidaRuta se eliminan
    SALIDA_RUTA = models.ForeignKey(
        SalidaRuta, on_delete=models.CASCADE, related_name="clientes"
    )
    # Aqui no uso el objeto cliente porque no ocupo acceder a el para nada. Por ejemplo, no hay que regresar clientes al sotck. Con su nombre me basta (NO ES CORRECTO)
    # LA RAZON POR LA QUE USO EL OBJETO CLIENTE Y NO UN NOMBRE, ES PORQUE EL TENER A FOREIG KEY AL OBJETO CLIENTE ME PERMITE ACCEDER A LOS HERMANOS DE CLIENTESALIDARUTA, ES DECIR, ME PERMITE ACCEDER A LOS PRECIOSCLIENTE
    # LO OTRO QUE QUERÍAS HACER NO FUNCIONARIA SI CAMBIAN EL PRECIO DEL CLIENTE Y LA SALIDARUTA YA SE REGISTRO CON PRECIOS ANTERIORES
    CLIENTE_RUTA = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    CLIENTE_NOMBRE = models.CharField(max_length=200)
    STATUS = models.CharField(
        max_length=100,
        choices=(
            ("PENDIENTE", "PENDIENTE"),
            ("VISITADO", "VISITADO"),
            ("CANCELADO", "CANCELADO"),
        ),
    )

    def __str__(self):
        return f"{self.SALIDA_RUTA}, {self.CLIENTE_RUTA}"


class DevolucionSalidaRuta(models.Model):
    REPARTIDOR = models.CharField(max_length=200)
    ATIENDE = models.CharField(max_length=200)
    ADMINISTRADOR = models.CharField(max_length=200, blank=True)
    SALIDA_RUTA = models.ForeignKey(
        SalidaRuta, on_delete=models.CASCADE, related_name="salida_ruta_devoluciones"
    )
    PRODUCTO_DEVOLUCION = models.ForeignKey(Producto, on_delete=models.CASCADE)
    PRODUCTO_NOMBRE = models.CharField(max_length=200)
    CATIDAD_DEVOLUCION = models.IntegerField(validators=[MinValueValidator(0)])
    # La cajera realiza la devolución, pero mientras el administrador no la autorice, el STATUS permanece como pendiente y la cajera no puede realizar el corte
    STATUS = models.CharField(
        max_length=200, choices=(("REALIZADO", "REALIZADO"), ("PENDIENTE", "PENDIENTE"))
    )
    OBSERVACIONES = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.SALIDA_RUTA}, {self.CATIDAD_DEVOLUCION}"
