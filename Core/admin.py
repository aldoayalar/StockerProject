from django.contrib import admin
from .models import Material, Inventario, Solicitud, DetalleSolicitud, Notificacion, Usuario, Movimiento


@admin.register(Usuario)
@admin.register(Movimiento)

# Registro de Material
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'categoria', 'unidad_medida']
    list_filter = ['categoria']
    search_fields = ['codigo', 'descripcion']

# Registro de Inventario
@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ['material', 'stock_actual', 'stock_seguridad']
    list_filter = ['stock_actual']

# Inline para DetalleSolicitud
class DetalleSolicitudInline(admin.TabularInline):
    model = DetalleSolicitud
    extra = 1
    fields = ['material', 'cantidad', 'cantidad_aprobada']

# Registro de Solicitud CON INLINE (SOLO UNA VEZ)
@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['id', 'solicitante', 'estado', 'fecha_solicitud', 'total_items']
    list_filter = ['estado', 'fecha_solicitud']
    search_fields = ['id', 'solicitante__username', 'motivo']
    inlines = [DetalleSolicitudInline]
    readonly_fields = ['fecha_solicitud', 'fecha_respuesta']
    
    def total_items(self, obj):
        return obj.total_items()
    total_items.short_description = 'Total Ítems'

# Registro de DetalleSolicitud
@admin.register(DetalleSolicitud)
class DetalleSolicitudAdmin(admin.ModelAdmin):
    list_display = ['solicitud', 'material', 'cantidad', 'cantidad_aprobada']
    list_filter = ['solicitud__estado']
    search_fields = ['material__descripcion', 'solicitud__id']

# Registro de Notificacion
@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'leida', 'creada_en']
    list_filter = ['tipo', 'leida']
    search_fields = ['usuario__username', 'mensaje']