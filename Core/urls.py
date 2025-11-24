from django.urls import path
from . import views

urlpatterns = [

    # Url de Vista del login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Urls de Vistas basadas en roles
    path('tecnico/', views.tecnico, name='tecnico'),
    path('bodega/', views.bodega, name='bodega'),
    path('chofer/', views.chofer, name='chofer'),
    path('gerente/', views.gerente, name='gerente'),

    # Urls de Vistas basadas en funcionalidades
    path('historial_tecnico/', views.historial_tecnico, name='historial_tecnico'),
    path('solicitud/', views.solicitud, name='solicitud'),
    path('inventario/', views.inventario, name='inventario'),
    path('material/<int:id>/', views.detalle_material, name='detalle_material'),
    path('material/<int:id>/editar/', views.editar_material, name='editar_material'),
    path('ingreso-material/', views.ingreso_material, name='ingreso_material'),
    
    #Notificaciones
    path('notificacion/<int:id>/leer/', views.marcar_leida, name='marcar_leida'),
    path('notificaciones/leer-todas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
]