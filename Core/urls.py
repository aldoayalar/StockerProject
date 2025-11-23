from django.urls import path
from . import views

urlpatterns = [

    # Url de Vista del login
    path('', views.login, name='login'),

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
]