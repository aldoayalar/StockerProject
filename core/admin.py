from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import (
    Rol, Material, Inventario, Mensual, Alerta,
    Solicitud, DetalleSolicitud, Movimiento, Notificacion,
    Configuracion, Local
)

# Obtener el modelo de Usuario personalizado
Usuario = get_user_model()


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']
    search_fields = ['nombre']


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """
    Admin personalizado para Usuario que extiende AbstractUser.
    Incluye los campos personalizados: rol, telefono, force_password_change
    """
    # Campos mostrados en la lista
    list_display = [
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'rol',
        'rut',
        'is_active',
        'is_staff',
        'date_joined'
    ]
    
    # Filtros laterales
    list_filter = [
        'rol', 
        'is_active', 
        'is_staff', 
        'is_superuser',
        'date_joined'
    ]
    
    # Campos de búsqueda
    search_fields = [
        'rut',
        'username', 
        'email', 
        'first_name', 
        'last_name'
    ]
    
    # Ordenamiento por defecto
    ordering = ['-date_joined']
    
    # Configuración de campos en la vista de detalle
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'rut', 'email', 'telefono')
        }),
        ('Rol y Permisos', {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Configuración Adicional', {
            'fields': ('force_password_change', 'email_legado'),
            'classes': ('collapse',)  # Colapsado por defecto
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Configuración para crear nuevos usuarios
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 
                'email',
                'first_name',
                'last_name',
                'password1', 
                'password2',
                'rol',
                'rut',
                'is_staff',
                'is_active'
            ),
        }),
    )
    
    # Hacer que algunos campos sean de solo lectura
    readonly_fields = ['last_login', 'date_joined']
    
    # Acciones personalizadas
    actions = ['activar_usuarios', 'desactivar_usuarios', 'resetear_password_flag']
    
    def activar_usuarios(self, request, queryset):
        """Activar usuarios seleccionados"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} usuario(s) activado(s) exitosamente.')
    activar_usuarios.short_description = "Activar usuarios seleccionados"
    
    def desactivar_usuarios(self, request, queryset):
        """Desactivar usuarios seleccionados"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} usuario(s) desactivado(s) exitosamente.')
    desactivar_usuarios.short_description = "Desactivar usuarios seleccionados"
    
    def resetear_password_flag(self, request, queryset):
        """Forzar cambio de contraseña en próximo login"""
        updated = queryset.update(force_password_change=True)
        self.message_user(request, f'{updated} usuario(s) deberán cambiar su contraseña.')
    resetear_password_flag.short_description = "Forzar cambio de contraseña"


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'categoria', 'unidad_medida', 'ubicacion', 'fecha_creacion']
    list_filter = ['categoria', 'unidad_medida', 'fecha_creacion']
    search_fields = ['codigo', 'descripcion', 'ubicacion']
    ordering = ['codigo']
    date_hierarchy = 'fecha_creacion'
    
    # Campos de solo lectura
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'descripcion', 'categoria', 'unidad_medida')
        }),
        ('Ubicación', {
            'fields': ('ubicacion',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ['material', 'stock_actual', 'stock_seguridad', 'estado_stock', 'fecha_actualizacion']
    list_filter = ['fecha_actualizacion']
    search_fields = ['material__codigo', 'material__descripcion']
    ordering = ['stock_actual']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def estado_stock(self, obj):
        """Indicador visual del estado del stock"""
        if obj.stock_actual <= obj.stock_seguridad:
            return "🔴 CRÍTICO"
        elif obj.stock_actual <= obj.stock_seguridad * 1.5:
            return "🟡 BAJO"
        return "🟢 NORMAL"
    estado_stock.short_description = "Estado"


@admin.register(Mensual)
class MensualAdmin(admin.ModelAdmin):
    list_display = ['material', 'cantidad_promedio', 'stock_min_dinamico', 'fecha_calculo']
    list_filter = ['fecha_calculo']
    search_fields = ['material__codigo', 'material__descripcion']
    ordering = ['-fecha_calculo']
    date_hierarchy = 'fecha_calculo'


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ['material', 'usuario_principal', 'stock_actual', 'stock_min', 'creado_en']
    list_filter = ['creado_en']
    search_fields = ['material__codigo', 'material__descripcion', 'observacion']
    ordering = ['-creado_en']
    date_hierarchy = 'creado_en'
    readonly_fields = ['creado_en']


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ['material', 'usuario', 'tipo', 'cantidad', 'solicitud', 'fecha']
    list_filter = ['tipo', 'fecha']
    search_fields = ['material__codigo', 'material__descripcion', 'detalle']
    ordering = ['-fecha']
    date_hierarchy = 'fecha'
    readonly_fields = ['fecha']
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('material', 'tipo', 'cantidad', 'usuario')
        }),
        ('Solicitud Asociada', {
            'fields': ('solicitud',),
            'description': 'Solicitud relacionada con este movimiento (si aplica)'
        }),
        ('Detalles Adicionales', {
            'fields': ('detalle', 'fecha')
        }),
    )


class DetalleSolicitudInline(admin.TabularInline):
    """Inline para mostrar detalles dentro de Solicitud"""
    model = DetalleSolicitud
    extra = 1
    fields = ['material', 'cantidad', 'cantidad_aprobada']
    autocomplete_fields = ['material']  # Autocompletado para materiales


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'solicitante', 
        'estado', 
        'total_items', 
        'fecha_solicitud',
        'respondido_por',
        'fecha_respuesta'
    ]
    list_filter = ['estado', 'fecha_solicitud', 'fecha_respuesta']
    search_fields = ['id', 'solicitante__username', 'motivo', 'observaciones']
    ordering = ['-fecha_solicitud']
    date_hierarchy = 'fecha_solicitud'
    inlines = [DetalleSolicitudInline]
    
    readonly_fields = ['fecha_solicitud', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información de la Solicitud', {
            'fields': ('solicitante', 'motivo', 'estado')
        }),
        ('Respuesta', {
            'fields': ('respondido_por', 'fecha_respuesta', 'observaciones'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def total_items(self, obj):
        """Mostrar total de items en la solicitud"""
        return obj.total_items()
    total_items.short_description = "Total Items"


@admin.register(DetalleSolicitud)
class DetalleSolicitudAdmin(admin.ModelAdmin):
    list_display = ['solicitud', 'material', 'cantidad', 'cantidad_aprobada', 'stock_disponible']
    list_filter = ['solicitud__estado']
    search_fields = ['solicitud__id', 'material__codigo', 'material__descripcion']
    autocomplete_fields = ['material', 'solicitud']
    
    def stock_disponible(self, obj):
        """Mostrar stock disponible del material"""
        return obj.stock_disponible()
    stock_disponible.short_description = "Stock Disponible"


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'mensaje_corto', 'leida', 'creada_en']
    list_filter = ['tipo', 'leida', 'creada_en']
    search_fields = ['usuario__username', 'mensaje']
    ordering = ['-creada_en']
    date_hierarchy = 'creada_en'
    readonly_fields = ['creada_en', 'actualizada_en']
    
    actions = ['marcar_como_leidas', 'marcar_como_no_leidas']
    
    def mensaje_corto(self, obj):
        """Mostrar versión corta del mensaje"""
        return obj.mensaje[:50] + '...' if len(obj.mensaje) > 50 else obj.mensaje
    mensaje_corto.short_description = "Mensaje"
    
    def marcar_como_leidas(self, request, queryset):
        """Marcar notificaciones como leídas"""
        updated = queryset.update(leida=True)
        self.message_user(request, f'{updated} notificación(es) marcada(s) como leída(s).')
    marcar_como_leidas.short_description = "Marcar como leídas"
    
    def marcar_como_no_leidas(self, request, queryset):
        """Marcar notificaciones como no leídas"""
        updated = queryset.update(leida=False)
        self.message_user(request, f'{updated} notificación(es) marcada(s) como no leída(s).')
    marcar_como_no_leidas.short_description = "Marcar como no leídas"


@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    """
    Admin para Configuración (Singleton).
    Solo debe existir un registro con pk=1
    """
    list_display = ['__str__', 'tiempo_cancelacion_minutos', 'timer_activo']
    
    def has_add_permission(self, request):
        """Evitar crear más de una configuración"""
        return not Configuracion.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Evitar eliminar la configuración"""
        return False
    
    fieldsets = (
        ('Configuración de Solicitudes', {
            'fields': ('tiempo_cancelacion_minutos', 'timer_activo'),
            'description': 'Parámetros para el manejo de solicitudes en el sistema.'
        }),
    )

@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'direccion', 'numero', 'comuna', 'region']
    list_filter = ['region', 'comuna']
    search_fields = ['codigo', 'nombre', 'direccion', 'comuna']
    ordering = ['codigo']


# Personalización del Admin Site
admin.site.site_header = "Stocker - Administración"
admin.site.site_title = "Stocker Admin"
admin.site.index_title = "Panel de Administración"
