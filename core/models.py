from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


# ==================== CONFIGURACION ====================

class Configuracion(models.Model):
    tiempo_cancelacion_minutos = models.PositiveIntegerField(
        default=5,
        help_text='Minutos permitidos para cancelar una solicitud aprobada.'
    )
    
    timer_activo = models.BooleanField(
        default=True,
        verbose_name='Límite de tiempo activo',
        help_text='Si está desactivado, se permite cancelar solicitudes sin límite de tiempo.'
    )
    
    class Meta:
        verbose_name = 'Configuración'
        verbose_name_plural = 'Configuración'
    
    def save(self, *args, **kwargs):

        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return 'Configuración del Sistema'


# ==================== ROL ====================

class Rol(models.Model):
    nombre = models.CharField(max_length=50)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    

# ==================== LOCAL ====================

class Local(models.Model):
  
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código',
        help_text='Código interno del local'
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre'
    )
    direccion = models.CharField(
        max_length=300,
        verbose_name='Dirección',
        help_text='Calle y número'
    )
    numero = models.CharField(
        max_length=20,
        verbose_name='Número',
        blank=True,
        null=True
    )
    comuna = models.CharField(
        max_length=100,
        verbose_name='Comuna'
    )
    region = models.CharField(
        max_length=100,
        verbose_name='Región'
    )
    activo = models.BooleanField(
        default=True, verbose_name="Activo"
    )
    
    class Meta:
        verbose_name = 'Local'
        verbose_name_plural = 'Locales'
        ordering = ['codigo', 'nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def get_direccion_completa(self):
        """Retorna la dirección completa: Dirección Número, Comuna, Región"""
        direccion_base = f"{self.direccion}"
        if self.numero:
            direccion_base += f" {self.numero}"
        return f"{direccion_base}, {self.comuna}, {self.region}"


# ==================== USUARIO ====================

class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado integrado con Django Auth.
    """
    
    ROL_CHOICES = [
        ('GERENCIA', 'GERENCIA'),
        ('BODEGA', 'BODEGA'),
        ('TECNICO', 'TECNICO'),
        ('SISTEMA', 'SISTEMA'),
    ]
    
    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default='TECNICO',
        verbose_name='Rol'
    )
    
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    
    force_password_change = models.BooleanField(
        default=True,
        verbose_name='Forzar cambio de contraseña'
    )
    
    email_legado = models.EmailField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}".strip() or self.username


# ==================== MATERIALES ====================

class Material(models.Model):
    UNIDAD_CHOICES = [
        ('unidad', 'Unidades'),
        ('kg', 'Kilogramos'),
        ('metro', 'Metros'),
        ('litro', 'Litros'),
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
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_modificacion = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Materiales"
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"
    

# ==================== INVENTARIO ====================

class Inventario(models.Model):
    material = models.OneToOneField(Material, on_delete=models.CASCADE, related_name='inventario')
    stock_actual = models.IntegerField(default=0)
    stock_seguridad = models.IntegerField(default=5)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Inventarios"
        indexes = [models.Index(fields=['material'])]
    
    def __str__(self):
        return f"Inventario: {self.material.descripcion} - Stock: {self.stock_actual}"


# ==================== MENSUAL ====================

class Mensual(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad_promedio = models.FloatField()
    stock_min_dinamico = models.FloatField()
    lead_time_estimado = models.IntegerField()
    lead_time_calculado = models.IntegerField()
    stock_min_calculado = models.FloatField()
    fecha_calculo = models.DateTimeField()
    
    class Meta:
        verbose_name_plural = "Mensuales"
    
    def __str__(self):
        return f"Mensual - {self.material.codigo}"


# ==================== ALERTA ====================

class Alerta(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    usuario_principal = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    stock_actual = models.FloatField()
    stock_min = models.FloatField()
    observacion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Alertas"
    
    def __str__(self):
        return f"Alerta - {self.material.codigo}"


# ==================== SOLICITUD (AHORA CON DETALLES) ====================

class Solicitud(models.Model):
  
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    local_destino = models.ForeignKey(
        'Local', on_delete=models.PROTECT,
        related_name='solicitudes',
        verbose_name='Local de Destino',
        help_text='Local donde se entregarán los materiales',
        null=True,  # Temporal para migración
        blank=True  # Temporal para migración
    )
      
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='solicitudes'
    )
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(default=timezone.now)
    respondido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_respondidas'
    )
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Solicitudes"
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['estado', 'fecha_solicitud']),
            models.Index(fields=['solicitante']),
            models.Index(fields=['estado', 'solicitante']),
        ]
    
    def __str__(self):
        return f"Solicitud #{self.id} - {self.solicitante.username}"
    
    def total_items(self):
        return self.detalles.count()
    
    def total_cantidad(self):
        return sum(detalle.cantidad for detalle in self.detalles.all())


# ==================== DETALLE SOLICITUD ====================

class DetalleSolicitud(models.Model):
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='detalles')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    cantidad_aprobada = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Detalles de Solicitud"
        unique_together = ('solicitud', 'material')
        indexes = [models.Index(fields=['solicitud', 'material'])]
    
    def __str__(self):
        return f"{self.material.descripcion} - Cant: {self.cantidad}"
    
    def stock_disponible(self):
        try:
            return self.material.inventario.stock_actual
        except:
            return 0


# ==================== MOVIMIENTO ====================

class Movimiento(models.Model):
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, 
        related_name='movimientos'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos',
        help_text='Solicitud asociada al movimiento (si aplica)'
    )
    tipo = models.CharField(max_length=20, choices=[
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ])
    cantidad = models.IntegerField()
    detalle = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'movimiento'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.tipo.upper()} - {self.material.codigo} - {self.cantidad}"


# ==================== NOTIFICACION ====================

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('stock_critico', 'Stock Crítico'),
        ('solicitud_pendiente', 'Solicitud Pendiente'),
        ('material_nuevo', 'Material Nuevo'),
        ('aprobacion', 'Aprobación Requerida'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default='material_nuevo')
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    url = models.CharField(max_length=200, blank=True, null=True)
    creada_en = models.DateTimeField(default=timezone.now)
    actualizada_en = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Notificaciones"
        ordering = ['-creada_en']
    
    def __str__(self):
        return f"{self.tipo} - {self.usuario.username}"


# ==================== MLRESULT ====================

class MLResult(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='resultados_ml')
    demanda_promedio = models.FloatField()
    desviacion = models.FloatField()
    leadtime_dias = models.IntegerField()
    stock_min_calculado = models.IntegerField()
    version_modelo = models.CharField(max_length=40, default='v1.0')
    fecha_calculo = models.DateTimeField(default=timezone.now)
    
    stock_seguridad = models.FloatField(default=0.0, help_text="Colchón extra por variabilidad")
    coeficiente_variacion = models.FloatField(default=0.0, help_text="Variabilidad relativa (sigma/media)")
    metodo_utilizado = models.CharField(max_length=50, default="Estandar")
    
    class Meta:
        db_table = 'ml_result'
        ordering = ['-fecha_calculo']
