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
    #path('solicitud/', views.solicitud, name='solicitud'),
    path('inventario/', views.inventario, name='inventario'),
    path('material/<int:id>/', views.detalle_material, name='detalle_material'),
    path('material/<int:id>/editar/', views.editar_material, name='editar_material'),
    path('ingreso-material/', views.ingreso_material, name='ingreso_material'),
    path('materiales/nuevo/', views.crear_material, name='material_crear'),
    path("inventario/carga-masiva/", views.carga_masiva_stock, name="carga_masiva_stock"),
    path('inventario/descargar-plantilla/', views.descargar_plantilla_stock, name='descargar_plantilla_stock'),
    path("inventario/recalcular-ml/", views.recalcular_stock_ml, name="recalcular_stock_ml"),

    
    # Solicitud de materiales
        #tecnico
    path('solicitud/crear/', views.crear_solicitud, name='crear_solicitud'),
    path('solicitud/mis-solicitudes/', views.mis_solicitudes, name='mis_solicitudes'),
       
    # Administración de solicitudes
    path('solicitud/gestionar/', views.gestionar_solicitudes, name='gestionar_solicitudes'),
    path('solicitud/<int:solicitud_id>/', views.detalle_solicitud, name='detalle_solicitud'),
    path('solicitud/<int:solicitud_id>/cancelar/', views.cancelar_solicitud, name='cancelar_solicitud'),
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
    path('notificaciones/<int:id>/leer/', views.leer_notificacion, name='leer_notificacion'),
    path('notificaciones/<int:id>/marcar/', views.marcar_leida, name='marcar_leida'),
    path('notificaciones/marcar-todas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('notificaciones/<int:id>/eliminar/', views.eliminar_notificacion, name='eliminar_notificacion'),
    path('api/notificaciones/', views.obtener_notificaciones_json, name='obtener_notificaciones_json'),
    
    # Exportación a Excel
    path('exportar/inventario/', views.exportar_inventario_excel, name='exportar_inventario_excel'),
    path('exportar/solicitudes/', views.exportar_solicitudes_excel, name='exportar_solicitudes_excel'),
    path('exportar/movimientos/', views.exportar_movimientos_excel, name='exportar_movimientos_excel'),
    path('exportar/movimientos/<int:material_id>/', views.exportar_movimientos_excel, name='exportar_movimientos_excel'),
    path('exportar/reporte-completo/', views.exportar_reporte_completo_excel, name='exportar_reporte_completo'),
    
    # Gestión de Locales
    path('locales/', views.gestion_locales, name='gestion_locales'),
    path('locales/crear/', views.local_crear, name='local_crear'),
    path('locales/<int:local_id>/editar/', views.local_editar, name='local_editar'),
    path('locales/<int:local_id>/eliminar/', views.local_eliminar, name='local_eliminar'),
    path('locales/<int:local_id>/reactivar/', views.local_reactivar, name='local_reactivar'),

    
    # Gestión de usuarios
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/crear/', views.usuario_crear, name='usuario_crear'),
    path('usuarios/<int:usuario_id>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:usuario_id>/eliminar/', views.usuario_eliminar, name='usuario_eliminar'),
    path('usuarios/<int:usuario_id>/toggle/', views.usuario_toggle_estado, name='usuario_toggle_estado'),
    
    #calculo Stock Critico
    path('prediccion-stock/', views.prediccion_stock, name='prediccion_stock'),
    
    #HOME sistema
    path('sistema/', views.sistema_home, name='sistema_home'),

]