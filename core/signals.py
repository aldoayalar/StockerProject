from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Inventario, Movimiento, Usuario, Notificacion, Material


# ------------------ STOCK CRÍTICO ------------------ #
@receiver(post_save, sender=Inventario)
def verificar_stock_critico(sender, instance, **kwargs):
   
    if instance.stock_actual > instance.stock_seguridad:
        return

    material = instance.material

    # Evitar duplicar notificaciones para este material en menos de 24h
    hace_24h = timezone.now() - timedelta(hours=24)
    notificaciones_recientes = Notificacion.objects.filter(
        tipo="stock_critico",
        mensaje__contains=material.codigo,
        creada_en__gte=hace_24h,
    ).count()

    if notificaciones_recientes > 0:
        return

    # Todos los encargados de bodega activos
    encargados_bodega = Usuario.objects.filter(
        rol="BODEGA",
        is_active=True,
    )

    for usuario in encargados_bodega:
        Notificacion.objects.create(
            usuario=usuario,
            tipo="stock_critico",
            mensaje=(
                f"Stock crítico: {material.descripcion} "
                f"({material.codigo}) - Stock: {instance.stock_actual}"
            ),
            url=f"/material/{material.id}/",
        )


# ------------------ MATERIAL NUEVO ------------------ #
@receiver(post_save, sender=Material)
def notificar_material_nuevo(sender, instance, created, **kwargs):
  
    if not created:
        return

    encargados_bodega = Usuario.objects.filter(
        rol="BODEGA",
        is_active=True,
    )

    for usuario in encargados_bodega:
        Notificacion.objects.create(
            usuario=usuario,
            tipo="material_nuevo",
            mensaje=f"Nuevo material creado: {instance.descripcion} ({instance.codigo})",
            url=f"/material/{instance.id}/",
        )


# ------------------ INGRESO INICIAL INVENTARIO ------------------ #
@receiver(post_save, sender=Inventario)
def registrar_ingreso_inicial(sender, instance, created, **kwargs):
   
    if not created or instance.stock_actual <= 0:
        return

    # Buscar un responsable BODEGA activo
    responsable = (
        Usuario.objects.filter(rol="BODEGA", is_active=True)
        .order_by("id")
        .first()
    )

    if not responsable:
        
        return

    Movimiento.objects.create(
        material=instance.material,
        usuario=responsable,
        tipo="entrada",
        cantidad=instance.stock_actual,
        detalle="Ingreso inicial de inventario",
    )
