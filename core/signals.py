# signals.py - VERSIÓN COMPLETA CON NOTIFICACIONES

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Solicitud, Inventario, Movimiento, Usuario, Notificacion

User = get_user_model()

@receiver(post_save, sender=Solicitud)
def procesar_solicitud_aprobada(sender, instance, created, **kwargs):
    """
    Cuando se aprueba una solicitud, crear movimientos y actualizar stock
    También genera notificaciones
    """
    # Si es una solicitud nueva, notificar a staff
    if created:
        # Notificar a todos los usuarios staff
        usuarios_staff = User.objects.filter(is_staff=True, is_active=True)
        for staff_user in usuarios_staff:
            Notificacion.objects.create(
                usuario=staff_user,
                tipo='solicitud_pendiente',
                mensaje=f'Nueva solicitud #{instance.id} de {instance.solicitante.username}',
                url=f'/solicitudes/{instance.id}/'
            )
    
    # Solo procesar si cambió a 'aprobada' o 'despachada'
    if instance.estado in ['aprobada', 'despachada']:
        # Verificar que no se hayan procesado ya los movimientos
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
                    try:
                        usuario_movimiento = Usuario.objects.get(
                            email=instance.respondido_por.email
                        )
                    except (Usuario.DoesNotExist, AttributeError):
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
                    pass
        
        # Notificar al solicitante que su solicitud fue aprobada
        Notificacion.objects.create(
            usuario=instance.solicitante,
            tipo='aprobacion',
            mensaje=f'Tu solicitud #{instance.id} ha sido aprobada',
            url=f'/solicitudes/{instance.id}/'
        )
    
    # Si fue rechazada, notificar al solicitante
    elif instance.estado == 'rechazada':
        Notificacion.objects.create(
            usuario=instance.solicitante,
            tipo='aprobacion',
            mensaje=f'Tu solicitud #{instance.id} ha sido rechazada',
            url=f'/solicitudes/{instance.id}/'
        )


@receiver(post_save, sender=Inventario)
def verificar_stock_critico(sender, instance, **kwargs):
    """
    Verificar si el stock está crítico y notificar
    """
    if instance.stock_actual <= instance.stock_seguridad:
        material = instance.material
        
        # Evitar duplicar notificaciones (solo si no hay una reciente)
        from django.utils import timezone
        from datetime import timedelta
        hace_24h = timezone.now() - timedelta(hours=24)
        
        notificaciones_recientes = Notificacion.objects.filter(
            tipo='stock_critico',
            mensaje__contains=material.codigo,
            creada_en__gte=hace_24h
        ).count()
        
        if notificaciones_recientes == 0:
            # Notificar a todos los usuarios staff
            usuarios_staff = User.objects.filter(is_staff=True, is_active=True)
            for staff_user in usuarios_staff:
                Notificacion.objects.create(
                    usuario=staff_user,
                    tipo='stock_critico',
                    mensaje=f'Stock crítico: {material.descripcion} ({material.codigo}) - Stock: {instance.stock_actual}',
                    url=f'/materiales/{material.id}/'
                )


@receiver(post_save, sender=Inventario)
def registrar_ingreso_inicial(sender, instance, created, **kwargs):
    """
    Registrar movimiento cuando se crea un inventario nuevo
    """
    if created and instance.stock_actual > 0:
        try:
            usuario_sistema = Usuario.objects.get(email='sistema@stocker.com')
        except Usuario.DoesNotExist:
            usuario_sistema = None
        
        if usuario_sistema:
            Movimiento.objects.create(
                material=instance.material,
                usuario=usuario_sistema,
                tipo='entrada',
                cantidad=instance.stock_actual,
                detalle='Ingreso inicial de inventario'
            )
