from .models import Notificacion

def notificaciones(request):
    if request.user.is_authenticated:
        notificaciones_no_leidas = Notificacion.objects.filter(
            usuario=request.user, 
            leida=False
        )[:5]  # Últimas 5
        count = notificaciones_no_leidas.count()
        return {
            'notificaciones': notificaciones_no_leidas,
            'notificaciones_count': count
        }
    return {'notificaciones': [], 'notificaciones_count': 0}