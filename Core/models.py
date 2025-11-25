from django.db import models, migrations
from django.contrib.auth.models import User
from django.utils import timezone

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
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Materiales"
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

class Inventario(models.Model):
    material = models.OneToOneField(Material, on_delete=models.CASCADE, related_name='inventario')
    stock_actual = models.IntegerField(default=0)
    stock_seguridad = models.IntegerField(default=5)
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
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-creada_en']
    
    def __str__(self):
        return f"{self.tipo} - {self.usuario.username}"
    

class Solicitud(models.Model):
    """
    Cabecera de la solicitud (ahora sin material ni cantidad directa)
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('despachada', 'Despachada'),
    ]
    
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes')
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    respondido_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='solicitudes_respondidas'
    )
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"Solicitud #{self.id} - {self.solicitante.username} ({self.estado})"
    
    def total_items(self):
        """Retorna el número total de ítems en esta solicitud"""
        return self.detalles.count()
    
    def total_cantidad(self):
        """Retorna la cantidad total solicitada"""
        return sum(detalle.cantidad for detalle in self.detalles.all())

class DetalleSolicitud(models.Model):
    """
    Detalle de cada material solicitado en una solicitud
    """
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='detalles')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    cantidad_aprobada = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Detalles de Solicitud"
        unique_together = ('solicitud', 'material')  # Un material solo puede aparecer una vez por solicitud
    
    def __str__(self):
        return f"{self.material.descripcion} - Cant: {self.cantidad}"
    
    def stock_disponible(self):
        """Retorna el stock disponible del material"""
        try:
            return self.material.inventario.stock_actual
        except:
            return 0

class Movimiento(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50)
    cantidad = models.FloatField()
    fecha = models.DateTimeField(auto_now_add=True)
    detalle = models.TextField(null=True, blank=True)
    

    

