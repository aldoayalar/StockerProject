from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Inventario, Notificacion

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