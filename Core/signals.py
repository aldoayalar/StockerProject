from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Inventario, Notificacion, Solicitud, Movimiento, Usuario

@receiver(post_save, sender=Inventario)
def verificar_stock_critico(sender, instance, **kwargs):
    """Genera notificación automática cuando el stock esté crítico"""
    if instance.stock_actual <= instance.stock_seguridad:
        # Evitar duplicados
        if not Notificacion.objects.filter(
            tipo='stock_critico',
            mensaje__contains=instance.material.descripcion,
            leida=False
        ).exists():
            # Notificar a usuarios del grupo Bodega o Gerente
            # Si no tienes grupos, usa User.objects.filter(is_staff=True)
            usuarios_a_notificar = User.objects.filter(is_staff=True)  # se envia por defecto a todos los usuarios, definir a quien se envia
            
            for usuario in usuarios_a_notificar:
                Notificacion.objects.create(
                    usuario=usuario,
                    tipo='stock_critico',
                    mensaje=f'Stock crítico: {instance.material.descripcion} - Quedan {instance.stock_actual} unidades',
                    url=f'/material/{instance.material.id}/'
                )
                
@receiver(post_save, sender=Solicitud)
def procesar_solicitud_aprobada(sender, instance, created, **kwargs):
    """
    Cuando se aprueba una solicitud, crear movimientos y actualizar stock
    """
    # Solo procesar si cambió a 'aprobada' o 'despachada'
    if instance.estado in ['aprobada', 'despachada']:
        # Verificar que no se hayan procesado ya los movimientos
        # (evitar duplicados si se guarda múltiples veces)
        movimientos_existentes = Movimiento.objects.filter(
            detalle__contains=f'Solicitud #{instance.id}'
        ).count()
        
        if movimientos_existentes == 0:
            # Procesar cada detalle de la solicitud
            for detalle in instance.detalles.all():
                material = detalle.material
                cantidad_aprobada = detalle.cantidad_aprobada or detalle.cantidad
                
                # Obtener inventario
                try:
                    inventario = material.inventario
                    stock_anterior = inventario.stock_actual
                    stock_nuevo = stock_anterior - cantidad_aprobada
                    
                    # Actualizar stock
                    inventario.stock_actual = stock_nuevo
                    inventario.save()
                    
                    # Buscar usuario en modelo Usuario personalizado
                    # Si existe, usar ese; si no, crear uno temporal o usar el User de Django
                    try:
                        usuario_movimiento = Usuario.objects.get(
                            email=instance.respondido_por.email
                        )
                    except (Usuario.DoesNotExist, AttributeError):
                        # Si no existe usuario personalizado, crear movimiento sin usuario
                        # o puedes crear uno por defecto
                        usuario_movimiento = None
                    
                    # Crear movimiento (solo si hay usuario)
                    if usuario_movimiento:
                        Movimiento.objects.create(
                            material=material,
                            usuario=usuario_movimiento,
                            tipo='salida',
                            cantidad=cantidad_aprobada,
                            detalle=f'Salida por Solicitud #{instance.id} - Solicitante: {instance.solicitante.username}'
                        )
                    
                except Inventario.DoesNotExist:
                    # Si no existe inventario, crearlo
                    pass


@receiver(post_save, sender=Inventario)
def registrar_ingreso_inicial(sender, instance, created, **kwargs):
    """
    Registrar movimiento cuando se crea un inventario nuevo
    """
    if created and instance.stock_actual > 0:
        # Intentar obtener el usuario que lo creó (esto depende de tu implementación)
        # Por ahora, podrías crear un usuario "Sistema" en tu BD
        try:
            usuario_sistema = Usuario.objects.get(email='sistema@stocker.com')
        except Usuario.DoesNotExist:
            # Si no existe, no crear movimiento o crear con usuario None
            usuario_sistema = None
        
        if usuario_sistema:
            Movimiento.objects.create(
                material=instance.material,
                usuario=usuario_sistema,
                tipo='entrada',
                cantidad=instance.stock_actual,
                detalle='Ingreso inicial de inventario'
            )