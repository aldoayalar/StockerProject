from django.urls import path
from . import views

urlpatterns = [

    #Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Url de Vista del autenticacion
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),

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
    
    # Solicitud de materiales
        # Nuevas rutas de solicitudes multidetalle
    path('solicitud/crear/', views.crear_solicitud, name='crear_solicitud'),
    path('solicitud/mis-solicitudes/', views.mis_solicitudes, name='mis_solicitudes'),
    path('solicitud/<int:solicitud_id>/', views.detalle_solicitud, name='detalle_solicitud'),
    path('solicitud/<int:solicitud_id>/cancelar/', views.cancelar_solicitud, name='cancelar_solicitud'),
        #-----------------------------------------------------------------------------------------
        #Administracion de solicitudes
    path('solicitud/gestionar/', views.gestionar_solicitudes, name='gestionar_solicitudes'),
    path('solicitud/<int:solicitud_id>/aprobar/', views.aprobar_solicitud, name='aprobar_solicitud'),
    path('solicitud/<int:solicitud_id>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),
    
        #historial de solicitudes
    path('historial-solicitudes/', views.historial_solicitudes, name='historial_solicitudes'),
    
    # Movimientos
    path('material/<int:material_id>/entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('material/<int:material_id>/salida/', views.registrar_salida, name='registrar_salida'),
    path('material/<int:material_id>/ajustar/', views.ajustar_inventario, name='ajustar_inventario'),
    path('material/<int:material_id>/movimientos/', views.historial_movimientos, name='historial_movimientos'),
    path('movimientos/', views.historial_movimientos_global, name='historial_movimientos_global'),
    
    #Notificaciones
    path('notificaciones/', views.mis_notificaciones, name='mis_notificaciones'),
    path('notificaciones/<int:id>/leer/', views.marcar_leida, name='marcar_leida'),
    path('notificaciones/marcar-todas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('notificaciones/<int:id>/eliminar/', views.eliminar_notificacion, name='eliminar_notificacion'),
    path('api/notificaciones/', views.obtener_notificaciones_json, name='obtener_notificaciones_json'),
    
    # Exportación a Excel
    path('exportar/inventario/', views.exportar_inventario_excel, name='exportar_inventario_excel'),
    path('exportar/solicitudes/', views.exportar_solicitudes_excel, name='exportar_solicitudes_excel'),
    path('exportar/movimientos/', views.exportar_movimientos_excel, name='exportar_movimientos_excel'),
    path('exportar/reporte-completo/', views.exportar_reporte_completo_excel, name='exportar_reporte_completo'),
]