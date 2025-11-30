"""
Comando para poblar la base de datos con datos de prueba.
Uso: python manage.py poblar_db
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from core.models import (
    Rol, Material, Inventario, Configuracion, Local,
    Solicitud, DetalleSolicitud, Movimiento
)


User = get_user_model()


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de prueba para Stocker'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando poblado de base de datos...\n')
        
        # 1. Crear configuración
        self.crear_configuracion()
        
        # 2. Crear roles
        self.crear_roles()
        
        # 3. Crear locales  # AGREGAR ESTA LÍNEA
        self.crear_locales()  # AGREGAR ESTA LÍNEA
        
        # 4. Crear usuarios
        self.crear_usuarios()
        
        # 5. Crear materiales con inventario
        self.crear_materiales()
        
        # 6. Crear solicitudes de prueba
        self.crear_solicitudes()
        
        self.stdout.write(self.style.SUCCESS('\n✓ Base de datos poblada exitosamente!'))

        
    def crear_locales(self):
        """Crea los locales basados en los datos de la imagen"""
        locales_data = [
            {'codigo': 'N802', 'nombre': 'Independencia-Dorsal', 'direccion': 'Av. Independencia', 'numero': '3160', 'comuna': 'Conchalí', 'region': 'metropolitana'},
            {'codigo': 'N759', 'nombre': 'Quinta Normal-S. Gutierrez', 'direccion': 'Salvador Gutiérrez', 'numero': '5496', 'comuna': 'Quinta Normal', 'region': 'metropolitana'},
            {'codigo': 'N589', 'nombre': 'Maipu-La Farfana', 'direccion': 'Av. El Rosal', 'numero': '3999', 'comuna': 'maipu', 'region': 'metropolitana'},
            {'codigo': 'N758', 'nombre': 'Maipu-3 Poniente', 'direccion': 'Av. 3 Poniente', 'numero': '2600', 'comuna': 'maipu', 'region': 'metropolitana'},
            {'codigo': 'N806', 'nombre': 'Maipu-Centro Plaza', 'direccion': 'Av. Los Pajaritos', 'numero': '1948', 'comuna': 'maipu', 'region': 'metropolitana'},
            {'codigo': 'N604', 'nombre': 'Maipu-Pajaritos', 'direccion': 'Av. Los Pajaritos', 'numero': '4909', 'comuna': 'maipu', 'region': 'metropolitana'},
            {'codigo': 'N987', 'nombre': 'Maipu-El Bosque', 'direccion': 'Capellán Florencio Infante', 'numero': '3330', 'comuna': 'maipu', 'region': 'metropolitana'},
            {'codigo': 'N682', 'nombre': 'Santiago-Portugal', 'direccion': 'Portugal', 'numero': '112', 'comuna': 'Santiago', 'region': 'metropolitana'},
            {'codigo': 'N654', 'nombre': 'Maipu-Ciudad Satélite', 'direccion': 'Av. Alcalde José Luis Infante Larraín', 'numero': '1320', 'comuna': 'maipu', 'region': 'metropolitana'},
        ]
        
        for data in locales_data:
            Local.objects.get_or_create(
                codigo=data['codigo'],
                defaults={
                    'nombre': data['nombre'],
                    'direccion': data['direccion'],
                    'numero': data['numero'],
                    'comuna': data['comuna'],
                    'region': data['region']
                }
            )
        
        self.stdout.write(f'✓ {len(locales_data)} locales creados')
    
    def crear_configuracion(self):
        config, created = Configuracion.objects.get_or_create(pk=1)
        config.tiempo_cancelacion_minutos = 5
        config.timer_activo = True
        config.save()
        self.stdout.write('✓ Configuración creada')
    
    def crear_roles(self):
        roles = ['Gerencia', 'Bodega', 'Técnico']
        for nombre in roles:
            Rol.objects.get_or_create(nombre=nombre)
        self.stdout.write(f'✓ {len(roles)} roles creados')
    
    def crear_usuarios(self):
        usuarios_data = [
            {
                'username': 'gerente',
                'email': 'gerente@stocker.com',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'rol': 'GERENCIA',
                'password': 'inacap2025'
            },
            {
                'username': 'bodeguero1',
                'email': 'bodega1@stocker.com',
                'first_name': 'María',
                'last_name': 'González',
                'rol': 'BODEGA',
                'password': 'inacap2025'
            },
            {
                'username': 'bodeguero2',
                'email': 'bodega2@stocker.com',
                'first_name': 'Pedro',
                'last_name': 'Sánchez',
                'rol': 'BODEGA',
                'password': 'inacap2025'
            },
            {
                'username': 'tecnico1',
                'email': 'tecnico1@stocker.com',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'rol': 'TECNICO',
                'password': 'inacap2025'
            },
            {
                'username': 'tecnico2',
                'email': 'tecnico2@stocker.com',
                'first_name': 'Ana',
                'last_name': 'Martínez',
                'rol': 'TECNICO',
                'password': 'inacap2025'
            },
            {
                'username': 'tecnico3',
                'email': 'tecnico3@stocker.com',
                'first_name': 'Luis',
                'last_name': 'Torres',
                'rol': 'TECNICO',
                'password': 'inacap2025'
            },
        ]
        
        for data in usuarios_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'rol': data['rol'],
                    'force_password_change': False,
                    'is_active': True
                }
            )
            if created:
                user.set_password(data['password'])
                user.save()
        
        self.stdout.write(f'✓ {len(usuarios_data)} usuarios creados')
    
    def crear_materiales(self):
        materiales_data = [
            # Herramientas
            {'codigo': 'HER-001', 'descripcion': 'Martillo de goma', 'categoria': 'herramienta', 'unidad_medida': 'unidad', 'stock': 15, 'stock_seg': 5, 'ubicacion': 'Estante A1'},
            {'codigo': 'HER-002', 'descripcion': 'Destornillador plano 6mm', 'categoria': 'herramienta', 'unidad_medida': 'unidad', 'stock': 25, 'stock_seg': 8, 'ubicacion': 'Estante A2'},
            {'codigo': 'HER-003', 'descripcion': 'Alicate universal 8 pulgadas', 'categoria': 'herramienta', 'unidad_medida': 'unidad', 'stock': 12, 'stock_seg': 5, 'ubicacion': 'Estante A3'},
            {'codigo': 'HER-004', 'descripcion': 'Llave inglesa 12 pulgadas', 'categoria': 'herramienta', 'unidad_medida': 'unidad', 'stock': 8, 'stock_seg': 3, 'ubicacion': 'Estante A4'},
            {'codigo': 'HER-005', 'descripcion': 'Taladro eléctrico 500W', 'categoria': 'herramienta', 'unidad_medida': 'unidad', 'stock': 4, 'stock_seg': 2, 'ubicacion': 'Estante A5'},
            
            # Repuestos
            {'codigo': 'REP-001', 'descripcion': 'Filtro de aire industrial', 'categoria': 'repuesto', 'unidad_medida': 'unidad', 'stock': 30, 'stock_seg': 10, 'ubicacion': 'Estante B1'},
            {'codigo': 'REP-002', 'descripcion': 'Rodamiento 6205-2RS', 'categoria': 'repuesto', 'unidad_medida': 'unidad', 'stock': 50, 'stock_seg': 15, 'ubicacion': 'Estante B2'},
            {'codigo': 'REP-003', 'descripcion': 'Correa trapezoidal A-50', 'categoria': 'repuesto', 'unidad_medida': 'unidad', 'stock': 20, 'stock_seg': 8, 'ubicacion': 'Estante B3'},
            {'codigo': 'REP-004', 'descripcion': 'Sello mecánico 25mm', 'categoria': 'repuesto', 'unidad_medida': 'unidad', 'stock': 15, 'stock_seg': 5, 'ubicacion': 'Estante B4'},
            {'codigo': 'REP-005', 'descripcion': 'Válvula solenoide 1/2"', 'categoria': 'repuesto', 'unidad_medida': 'unidad', 'stock': 10, 'stock_seg': 4, 'ubicacion': 'Estante B5'},
            
            # Insumos
            {'codigo': 'INS-001', 'descripcion': 'Aceite hidráulico ISO 68', 'categoria': 'insumo', 'unidad_medida': 'litro', 'stock': 200, 'stock_seg': 50, 'ubicacion': 'Bodega Líquidos'},
            {'codigo': 'INS-002', 'descripcion': 'Grasa multipropósito', 'categoria': 'insumo', 'unidad_medida': 'kg', 'stock': 45, 'stock_seg': 15, 'ubicacion': 'Estante C1'},
            {'codigo': 'INS-003', 'descripcion': 'Cinta aislante eléctrica', 'categoria': 'insumo', 'unidad_medida': 'unidad', 'stock': 100, 'stock_seg': 25, 'ubicacion': 'Estante C2'},
            {'codigo': 'INS-004', 'descripcion': 'Guantes de seguridad', 'categoria': 'insumo', 'unidad_medida': 'unidad', 'stock': 80, 'stock_seg': 20, 'ubicacion': 'Estante C3'},
            {'codigo': 'INS-005', 'descripcion': 'Mascarilla N95', 'categoria': 'insumo', 'unidad_medida': 'unidad', 'stock': 150, 'stock_seg': 40, 'ubicacion': 'Estante C4'},
            {'codigo': 'INS-006', 'descripcion': 'Cable eléctrico AWG 12', 'categoria': 'insumo', 'unidad_medida': 'metro', 'stock': 500, 'stock_seg': 100, 'ubicacion': 'Bodega Cables'},
            {'codigo': 'INS-007', 'descripcion': 'Tornillo hexagonal M8x20', 'categoria': 'insumo', 'unidad_medida': 'unidad', 'stock': 1000, 'stock_seg': 200, 'ubicacion': 'Estante C5'},
            
            # Equipos
            {'codigo': 'EQP-001', 'descripcion': 'Multímetro digital', 'categoria': 'equipo', 'unidad_medida': 'unidad', 'stock': 6, 'stock_seg': 2, 'ubicacion': 'Estante D1'},
            {'codigo': 'EQP-002', 'descripcion': 'Pistola de calor industrial', 'categoria': 'equipo', 'unidad_medida': 'unidad', 'stock': 3, 'stock_seg': 1, 'ubicacion': 'Estante D2'},
            {'codigo': 'EQP-003', 'descripcion': 'Compresor de aire 50L', 'categoria': 'equipo', 'unidad_medida': 'unidad', 'stock': 2, 'stock_seg': 1, 'ubicacion': 'Bodega Equipos'},
            
            # Materiales críticos (stock bajo)
            {'codigo': 'CRI-001', 'descripcion': 'Fusible 20A rápido', 'categoria': 'repuesto', 'unidad_medida': 'unidad', 'stock': 3, 'stock_seg': 10, 'ubicacion': 'Estante E1'},
            {'codigo': 'CRI-002', 'descripcion': 'Relay 24VDC 10A', 'categoria': 'repuesto', 'unidad_medida': 'unidad', 'stock': 2, 'stock_seg': 8, 'ubicacion': 'Estante E2'},
            {'codigo': 'CRI-003', 'descripcion': 'Sensor de proximidad inductivo', 'categoria': 'repuesto', 'unidad_medida': 'unidad', 'stock': 1, 'stock_seg': 5, 'ubicacion': 'Estante E3'},
        ]
        
        for data in materiales_data:
            material, created = Material.objects.get_or_create(
                codigo=data['codigo'],
                defaults={
                    'descripcion': data['descripcion'],
                    'categoria': data['categoria'],
                    'unidad_medida': data['unidad_medida'],
                    'ubicacion': data['ubicacion']
                }
            )
            
            if created:
                Inventario.objects.create(
                    material=material,
                    stock_actual=data['stock'],
                    stock_seguridad=data['stock_seg']
                )
        
        self.stdout.write(f'✓ {len(materiales_data)} materiales creados con inventario')
    
    def crear_solicitudes(self):
        # Obtener usuarios
        tecnico1 = User.objects.get(username='tecnico1')
        tecnico2 = User.objects.get(username='tecnico2')
        bodeguero = User.objects.get(username='bodeguero1')
        
        # Obtener algunos materiales
        materiales = list(Material.objects.all()[:10])
        
        # Solicitud 1: Pendiente
        sol1 = Solicitud.objects.create(
            solicitante=tecnico1,
            motivo='Mantenimiento preventivo mensual - Línea de producción 1',
            estado='pendiente'
        )
        DetalleSolicitud.objects.create(solicitud=sol1, material=materiales[0], cantidad=2)
        DetalleSolicitud.objects.create(solicitud=sol1, material=materiales[1], cantidad=5)
        DetalleSolicitud.objects.create(solicitud=sol1, material=materiales[10], cantidad=10)
        
        # Solicitud 2: Aprobada
        sol2 = Solicitud.objects.create(
            solicitante=tecnico2,
            motivo='Reparación urgente bomba hidráulica',
            estado='aprobada',
            respondido_por=bodeguero,
            fecha_respuesta=timezone.now() - timedelta(hours=2)
        )
        DetalleSolicitud.objects.create(solicitud=sol2, material=materiales[5], cantidad=1, cantidad_aprobada=1)
        DetalleSolicitud.objects.create(solicitud=sol2, material=materiales[11], cantidad=3, cantidad_aprobada=3)
        
        # Solicitud 3: Rechazada
        sol3 = Solicitud.objects.create(
            solicitante=tecnico1,
            motivo='Solicitud duplicada - Cancelar',
            estado='rechazada',
            respondido_por=bodeguero,
            fecha_respuesta=timezone.now() - timedelta(days=1),
            observaciones='Solicitud duplicada con SOL-001'
        )
        DetalleSolicitud.objects.create(solicitud=sol3, material=materiales[2], cantidad=10)
        
        # Solicitud 4: Despachada
        sol4 = Solicitud.objects.create(
            solicitante=tecnico2,
            motivo='Mantenimiento correctivo motor eléctrico',
            estado='despachada',
            respondido_por=bodeguero,
            fecha_respuesta=timezone.now() - timedelta(days=2)
        )
        DetalleSolicitud.objects.create(solicitud=sol4, material=materiales[6], cantidad=2, cantidad_aprobada=2)
        DetalleSolicitud.objects.create(solicitud=sol4, material=materiales[12], cantidad=50, cantidad_aprobada=50)
        
        # Crear movimientos para la solicitud despachada
        for detalle in sol4.detalles.all():
            Movimiento.objects.create(
                material=detalle.material,
                usuario=bodeguero,
                solicitud=sol4,
                tipo='salida',
                cantidad=detalle.cantidad_aprobada,
                detalle=f'Despacho solicitud #{sol4.id}'
            )
        
        self.stdout.write('✓ 4 solicitudes de prueba creadas')
