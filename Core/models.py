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
    UNIDAD_CHOICES = [
        ('unidad', 'Unidad'),
        ('kg', 'Kilogramo'),
        ('metro', 'Metro'),
        ('litro', 'Litro'),
    ]
    
    CATEGORIA_CHOICES = [
        ('herramienta', 'Herramienta'),
        ('repuesto', 'Repuesto'),
        ('insumo', 'Insumo'),
        ('equipo', 'Equipo'),
    ]
    
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=200)
    unidad_medida = models.CharField(max_length=20, choices=UNIDAD_CHOICES, default='unidad')
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='insumo')
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps automáticos
    fecha_creacion = models.DateTimeField(auto_now_add=True)  # Solo al crear
    fecha_modificacion = models.DateTimeField(auto_now=True)  # Se actualiza siempre
    
    class Meta:
        verbose_name_plural = "Materiales"
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

class Inventario(models.Model):
    material = models.OneToOneField(Material, on_delete=models.CASCADE, related_name='inventario')
    stock_actual = models.IntegerField(default=0)
    stock_seguridad = models.IntegerField(default=5)
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Inventarios"
    
    def __str__(self):
        return f"Inventario: {self.material.descripcion} - Stock: {self.stock_actual}"


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
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default='material_nuevo')
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    url = models.CharField(max_length=200, blank=True, null=True)
    
    # Timestamps
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-creada_en']
    
    def __str__(self):
        return f"{self.tipo} - {self.usuario.username}"
    
class Migration(migrations.Migration):
    operations = [
        migrations.RenameField(
            model_name='notificacion',
            old_name='descripcion',
            new_name='mensaje',
        ),
    ]

class Solicitud(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('despachada', 'Despachada'),
    ]
    
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes')
    material = models.ForeignKey('Material', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Timestamps automáticos
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)  # Nuevo
    
    respondido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_respondidas')
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"Solicitud #{self.id} - {self.material.descripcion} ({self.estado})"
    
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes')
    material = models.ForeignKey('Material', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()  # <-- Agrega default=1
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    respondido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_respondidas')
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"Solicitud #{self.id} - {self.material.descripcion} ({self.estado})"

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
    

    

