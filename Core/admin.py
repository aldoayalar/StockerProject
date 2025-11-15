from django.contrib import admin
from .models import Material, Usuario, Solicitud, DetalleSolicitud, Movimiento

admin.site.register(Material)
admin.site.register(Usuario)
admin.site.register(Solicitud)
admin.site.register(DetalleSolicitud)
admin.site.register(Movimiento)