from django.db import models

class destino(models.Model):
    id = models.BigAutoField(primary_key=True)  # Para coincidir con bigint(20) como clave primaria
    nombre = models.TextField()  # Para coincidir con el tipo TEXT
    latitud = models.FloatField()  # Para coincidir con el tipo double
    longitud = models.FloatField()  # Para coincidir con el tipo double

    class Meta:
        managed = False  # Django no gestionará esta tabla
        db_table = 'destino'  # Nombre exacto de la tabla en la base de datos

class pedido(models.Model):
    id = models.BigAutoField(primary_key=True)  # Para `bigint(20)` como clave primaria autoincremental
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha por defecto: CURRENT_TIMESTAMP
    id_destino = models.BigIntegerField()  # Relacionado con `id_destino`

    class Meta:
        db_table = 'pedido'  # Nombre exacto de la tabla en la base de datos
        managed = True  # Django puede gestionar esta tabla si necesitas migraciones


class producto(models.Model):
    id = models.BigIntegerField(primary_key=True)  # Clave primaria
    nombre = models.TextField()  # Nombre del producto
    precio = models.FloatField()  # Precio del producto, si aplica

    class Meta:
        db_table = 'producto'  # Nombre de la tabla en la base de datos
        managed = False  # Django no gestionará esta tabla


class pedido_producto(models.Model):
    id_pedido = models.BigIntegerField()  # Relacionado con la tabla `pedido`
    id_producto = models.BigIntegerField()  # Relacionado con la tabla `producto`
    cantidad = models.IntegerField()  # Cantidad del producto en el pedido

    class Meta:
        db_table = 'pedido_producto'  # Nombre de la tabla en la base de datos
        managed = False  # Django no gestionará esta tabla
