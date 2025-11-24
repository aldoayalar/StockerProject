from django.db import models, migrations
from django.contrib.auth.models import User

class Rol(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

class Material(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    unidad_medida = models.CharField(max_length=30)
    categoria = models.CharField(max_length=30)
    ubicacion = models.CharField(max_length=30)

class Inventario(models.Model):
    material = models.OneToOneField(Material, on_delete=models.CASCADE)
    stock_actual = models.PositiveIntegerField()
    stock_seguridad = models.PositiveIntegerField()
    actualizado_en = models.DateTimeField(auto_now=True)


class Mensual(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad_promedio = models.FloatField()
    stock_min_dinamico = models.FloatField()
    lead_time_estimado = models.IntegerField()
    lead_time_calculado = models.IntegerField()
    stock_min_calculado = models.FloatField()
    fecha_calculo = models.DateTimeField()

class Alerta(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    usuario_principal = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    stock_actual = models.FloatField()
    stock_min = models.FloatField()
    observacion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('stock_critico', 'Stock Crítico'),
        ('solicitud_pendiente', 'Solicitud Pendiente'),
        ('material_nuevo', 'Material Nuevo'),
        ('aprobacion', 'Aprobación Requerida'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(
        max_length=30, 
        choices=TIPO_CHOICES,
        default='material_nuevo'
    )
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    url = models.CharField(max_length=200, blank=True, null=True)
    creada_en = models.DateTimeField(auto_now_add=True)

class Solicitud(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    estado = models.CharField(max_length=50)
    creada_en = models.DateTimeField(auto_now_add=True)

class DetalleSolicitud(models.Model):
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='detalles')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad_solicitada = models.FloatField()
    cantidad_entregada = models.FloatField(null=True, blank=True)

class Movimiento(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50)
    cantidad = models.FloatField()
    fecha = models.DateTimeField(auto_now_add=True)
    detalle = models.TextField(null=True, blank=True)
    
class Migration(migrations.Migration):
    operations = [
        migrations.RenameField(
            model_name='notificacion',
            old_name='descripcion',
            new_name='mensaje',
        ),
    ]
    

