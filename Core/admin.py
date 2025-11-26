# admin.py

from django.contrib import admin
from .models import (
    Rol, Usuario, Material, Inventario, Mensual, Alerta,
    Solicitud, DetalleSolicitud, Movimiento, Notificacion
)

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'email', 'rol', 'activo']
    list_filter = ['rol', 'activo']
    search_fields = ['nombre', 'apellido', 'email']

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'categoria', 'unidad_medida']
    list_filter = ['categoria']
    search_fields = ['codigo', 'descripcion']

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ['material', 'stock_actual', 'stock_seguridad']

@admin.register(Mensual)
class MensualAdmin(admin.ModelAdmin):
    list_display = ['material', 'cantidad_promedio', 'fecha_calculo']

@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ['material', 'usuario_principal', 'stock_actual', 'stock_min']

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ['material', 'usuario', 'tipo', 'cantidad', 'fecha']

class DetalleSolicitudInline(admin.TabularInline):
    model = DetalleSolicitud
    extra = 1

@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['id', 'solicitante', 'estado', 'fecha_solicitud']
    list_filter = ['estado']
    inlines = [DetalleSolicitudInline]

@admin.register(DetalleSolicitud)
class DetalleSolicitudAdmin(admin.ModelAdmin):
    list_display = ['solicitud', 'material', 'cantidad']

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'leida', 'creada_en']
