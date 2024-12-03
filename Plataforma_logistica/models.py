from django.db import models

class destino(models.Model):
    id = models.BigAutoField(primary_key=True)  # Para coincidir con bigint(20) como clave primaria
    nombre = models.TextField()  # Para coincidir con el tipo TEXT
    latitud = models.FloatField()  # Para coincidir con el tipo double
    longitud = models.FloatField()  # Para coincidir con el tipo double

    class Meta:
        managed = False  # Django no gestionará esta tabla
        db_table = 'destino'  # Nombre exacto de la tabla en la base de datos
