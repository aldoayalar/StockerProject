"""
Comando para poblar la base de datos con datos completos para ML.
Incluye: usuarios, roles, locales, materiales con stock optimizado,
solicitudes históricas y movimientos.

python manage.py poblar_db
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
from django.db.models import F
from core.models import (
    Rol, Local, Material, Inventario, Configuracion,
    Solicitud, DetalleSolicitud, Movimiento
)
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos completos para entrenamiento ML'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🚀 INICIANDO POBLADO COMPLETO DE BASE DE DATOS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Confirmación
        self.stdout.write(self.style.WARNING('\n⚠️  Este comando eliminará todos los datos existentes.'))
        confirm = input('¿Deseas continuar? (escribe SI para confirmar): ')

        if confirm != 'SI':
            self.stdout.write(self.style.ERROR('❌ Operación cancelada'))
            return

        self.stdout.write('\n')

        # Limpieza previa
        self.limpiar_bd()

        # Población en orden
        self.crear_configuracion()
        self.crear_roles()
        self.crear_locales()
        self.crear_usuarios()
        self.crear_materiales_base()
        self.crear_solicitudes_historicas()
        self.crear_movimientos_salida()
        self.crear_materiales_adicionales()

        # Resumen final
        self.mostrar_resumen()

        self.stdout.write('\n' + self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ BASE DE DATOS POBLADA EXITOSAMENTE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('\n💡 Credenciales de acceso:')
        self.stdout.write('   Usuario: SuperAdmin')
        self.stdout.write('   Contraseña: Inacap2025\n')

    def limpiar_bd(self):
        """Elimina todos los datos existentes"""
        self.stdout.write('🗑️  Limpiando base de datos...')

        Movimiento.objects.all().delete()
        DetalleSolicitud.objects.all().delete()
        Solicitud.objects.all().delete()
        Inventario.objects.all().delete()
        Material.objects.all().delete()
        Local.objects.all().delete()
        User.objects.all().delete()
        Rol.objects.all().delete()
        Configuracion.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('   ✓ Base de datos limpiada\n'))

    def crear_configuracion(self):
        """Crea configuración global del sistema"""
        self.stdout.write('⚙️  Creando configuración del sistema...')

        config = Configuracion.get_solo()
        config.tiempo_cancelacion_minutos = 5
        config.timer_activo = True
        config.save()

        self.stdout.write(self.style.SUCCESS('   ✓ Configuración creada\n'))

    def crear_roles(self):
        """Crea los roles del sistema"""
        self.stdout.write('👥 Creando roles...')

        roles = ['GERENCIA', 'BODEGA', 'TECNICO', 'SISTEMA']
        for rol_nombre in roles:
            Rol.objects.create(nombre=rol_nombre)

        self.stdout.write(self.style.SUCCESS(f'   ✓ {len(roles)} roles creados\n'))

    def crear_locales(self):
        """Crea los locales/sucursales"""
        self.stdout.write('📍 Creando locales...')

        locales_data = [
            {
                'codigo': 'N802',
                'nombre': 'Independencia-Dorsal',
                'direccion': 'Av. Independencia',
                'numero': '3160',
                'comuna': 'Conchalí',
                'region': 'Metropolitana'
            },
            {
                'codigo': 'N759',
                'nombre': 'Quinta Normal-S. Gutierrez',
                'direccion': 'Salvador Gutiérrez',
                'numero': '5496',
                'comuna': 'Quinta Normal',
                'region': 'Metropolitana'
            },
            {
                'codigo': 'N589',
                'nombre': 'Maipu-La Farfana',
                'direccion': 'Av. El Rosal',
                'numero': '3999',
                'comuna': 'Maipú',
                'region': 'Metropolitana'
            },
            {
                'codigo': 'N758',
                'nombre': 'Maipu-3 Poniente',
                'direccion': 'Av. 3 Poniente',
                'numero': '2600',
                'comuna': 'Maipú',
                'region': 'Metropolitana'
            },
            {
                'codigo': 'N806',
                'nombre': 'Maipu-Centro Plaza',
                'direccion': 'Av. Los Pajaritos',
                'numero': '1948',
                'comuna': 'Maipú',
                'region': 'Metropolitana'
            },
            {
                'codigo': 'N604',
                'nombre': 'Maipu-Pajaritos',
                'direccion': 'Av. Los Pajaritos',
                'numero': '4909',
                'comuna': 'Maipú',
                'region': 'Metropolitana'
            },
            {
                'codigo': 'N987',
                'nombre': 'Maipu-El Bosque',
                'direccion': 'Capellán Florencio Infante',
                'numero': '3330',
                'comuna': 'Maipú',
                'region': 'Metropolitana'
            },
            {
                'codigo': 'N682',
                'nombre': 'Santiago-Portugal',
                'direccion': 'Portugal',
                'numero': '112',
                'comuna': 'Santiago',
                'region': 'Metropolitana'
            },
            {
                'codigo': 'N654',
                'nombre': 'Maipu-Ciudad Satélite',
                'direccion': 'Av. Alcalde José Luis Infante Larraín',
                'numero': '1320',
                'comuna': 'Maipú',
                'region': 'Metropolitana'
            },
        ]

        for data in locales_data:
            Local.objects.create(**data)

        self.stdout.write(self.style.SUCCESS(f'   ✓ {len(locales_data)} locales creados\n'))

    def crear_usuarios(self):
        """Crea usuarios del sistema con ID controlado"""
        self.stdout.write('👤 Creando usuarios...')
        
        # Resetear el AUTO_INCREMENT para MariaDB/MySQL
        from django.db import connection
        with connection.cursor() as cursor:
            # Obtener el nombre de la tabla del modelo Usuario
            tabla = User._meta.db_table
            # Resetear el AUTO_INCREMENT a 1
            cursor.execute(f"ALTER TABLE {tabla} AUTO_INCREMENT = 1;")
        
        # Usuario administrador (será creado con ID=1 automáticamente)
        admin = User.objects.create_superuser(
            username='SuperAdmin',
            email='admin@stocker.cl',
            password='Inacap2025',
            first_name='Administrador',
            last_name='Sistema',
            rol='BODEGA',
            force_password_change=False
        )
        
        # Bodeguero
        User.objects.create_user(
            username='bodega',
            email='bodega@stocker.cl',
            password='Bodega2025',
            first_name='Diana',
            last_name='Aroca',
            rol='BODEGA',
            force_password_change=False
        )
        
        # Técnicos
        tecnicos = [
            {'username': 'dulloa', 'first_name': 'Deavis', 'last_name': 'Ulloa'},
            {'username': 'aayala', 'first_name': 'Aldo', 'last_name': 'Ayala'},
            {'username': 'ovargas', 'first_name': 'Oscar', 'last_name': 'Vargas'},
            {'username': 'tenico', 'first_name': 'Tecnico', 'last_name': 'Pruebas'},
        ]
        
        for tec in tecnicos:
            User.objects.create_user(
                username=tec['username'],
                email=f"{tec['username']}@stocker.cl",
                password='Tecnico2025',
                first_name=tec['first_name'],
                last_name=tec['last_name'],
                rol='TECNICO',
                force_password_change=False
            )
        
        total_usuarios = User.objects.count()
        self.stdout.write(self.style.SUCCESS(f'   ✓ {total_usuarios} usuarios creados\n'))

    def crear_materiales_base(self):
        """Crea los 15 materiales base con stock optimizado"""
        self.stdout.write('📦 Creando materiales base con inventario...')

        materiales_base = [
            {
                'codigo': 'MAT0001',
                'descripcion': 'Gas Refrigerante R410A',
                'unidad_medida': 'kg',
                'categoria': 'insumo',
                'ubicacion': 'Bodega A1',
                'stock_actual': 376,
                'stock_seguridad': 40
            },
            {
                'codigo': 'MAT0002',
                'descripcion': 'Compresor 2 HP',
                'unidad_medida': 'unidad',
                'categoria': 'equipo',
                'ubicacion': 'Bodega C3',
                'stock_actual': 384,
                'stock_seguridad': 41
            },
            {
                'codigo': 'MAT0003',
                'descripcion': 'Válvula de expansión termostática',
                'unidad_medida': 'unidad',
                'categoria': 'repuesto',
                'ubicacion': 'Estante B5',
                'stock_actual': 272,
                'stock_seguridad': 27
            },
            {
                'codigo': 'MAT0004',
                'descripcion': 'Filtro deshidratador 5/8',
                'unidad_medida': 'unidad',
                'categoria': 'repuesto',
                'ubicacion': 'Bodega E2',
                'stock_actual': 212,
                'stock_seguridad': 20
            },
            {
                'codigo': 'MAT0005',
                'descripcion': 'Aceite refrigerante POE 68',
                'unidad_medida': 'litro',
                'categoria': 'insumo',
                'ubicacion': 'Estante F1',
                'stock_actual': 190,
                'stock_seguridad': 17
            },
            {
                'codigo': 'MAT0006',
                'descripcion': 'Tubo de cobre 3/8 pulgadas',
                'unidad_medida': 'metro',
                'categoria': 'insumo',
                'ubicacion': 'Bodega D4',
                'stock_actual': 186,
                'stock_seguridad': 17
            },
            {
                'codigo': 'MAT0007',
                'descripcion': 'Cable eléctrico 2x1.5mm',
                'unidad_medida': 'metro',
                'categoria': 'insumo',
                'ubicacion': 'Estante H2',
                'stock_actual': 174,
                'stock_seguridad': 15
            },
            {
                'codigo': 'MAT0008',
                'descripcion': 'Manómetro digital',
                'unidad_medida': 'unidad',
                'categoria': 'herramienta',
                'ubicacion': 'Caja herramientas 1',
                'stock_actual': 168,
                'stock_seguridad': 14
            },
            {
                'codigo': 'MAT0009',
                'descripcion': 'Bomba de vacío 4 CFM',
                'unidad_medida': 'unidad',
                'categoria': 'equipo',
                'ubicacion': 'Bodega C1',
                'stock_actual': 140,
                'stock_seguridad': 11
            },
            {
                'codigo': 'MAT0010',
                'descripcion': 'Termostato digital',
                'unidad_medida': 'unidad',
                'categoria': 'repuesto',
                'ubicacion': 'Estante B3',
                'stock_actual': 50,
                'stock_seguridad': 10
            },
            {
                'codigo': 'MAT0011',
                'descripcion': 'Condensador 12000 BTU',
                'unidad_medida': 'unidad',
                'categoria': 'repuesto',
                'ubicacion': 'Bodega C2',
                'stock_actual': 50,
                'stock_seguridad': 10
            },
            {
                'codigo': 'MAT0012',
                'descripcion': 'Motor ventilador 1/4 HP',
                'unidad_medida': 'unidad',
                'categoria': 'repuesto',
                'ubicacion': 'Bodega C3',
                'stock_actual': 50,
                'stock_seguridad': 10
            },
            {
                'codigo': 'MAT0013',
                'descripcion': 'Capacitor 45 MFD',
                'unidad_medida': 'unidad',
                'categoria': 'repuesto',
                'ubicacion': 'Estante B1',
                'stock_actual': 50,
                'stock_seguridad': 10
            },
            {
                'codigo': 'MAT0014',
                'descripcion': 'Soldadura 15% plata',
                'unidad_medida': 'unidad',
                'categoria': 'insumo',
                'ubicacion': 'Estante F2',
                'stock_actual': 50,
                'stock_seguridad': 10
            },
            {
                'codigo': 'MAT0015',
                'descripcion': 'Llave inglesa 12 pulgadas',
                'unidad_medida': 'unidad',
                'categoria': 'herramienta',
                'ubicacion': 'Caja herramientas 2',
                'stock_actual': 50,
                'stock_seguridad': 10
            }
        ]

        for data in materiales_base:
            stock_actual = data.pop('stock_actual')
            stock_seguridad = data.pop('stock_seguridad')

            material = Material.objects.create(**data)
            Inventario.objects.create(
                material=material,
                stock_actual=stock_actual,
                stock_seguridad=stock_seguridad
            )

        self.stdout.write(self.style.SUCCESS(f'   ✓ {len(materiales_base)} materiales base creados\n'))

    def crear_solicitudes_historicas(self):
        """Crea solicitudes históricas para entrenamiento ML"""
        self.stdout.write('📋 Creando solicitudes históricas...')
        
        # Obtener usuario de bodega para responder
        usuario_bodega = User.objects.get(username='bodega')
        
        # Obtener todos los técnicos
        tecnicos = list(User.objects.filter(rol='TECNICO'))
        
        if not tecnicos:
            self.stdout.write(self.style.WARNING(' ⚠️ No hay técnicos disponibles'))
            return
        
        solicitudes_data = self.get_solicitudes_data()
        solicitudes_creadas = 0
        detalles_creados = 0
        
        # Distribuir solicitudes entre técnicos de forma aleatoria
        for sol_data in solicitudes_data:
            # Seleccionar un técnico aleatorio como solicitante
            tecnico_solicitante = random.choice(tecnicos)
            
            # Crear solicitud
            solicitud = Solicitud.objects.create(
                solicitante=tecnico_solicitante,  # CAMBIO AQUÍ
                respondido_por=usuario_bodega,    # Bodega responde
                motivo=sol_data['motivo'],
                estado=sol_data['estado'],
                fecha_solicitud=sol_data['fecha_solicitud'],
                fecha_respuesta=sol_data['fecha_respuesta'],
                fecha_actualizacion=sol_data['fecha_actualizacion']
            )
            
            solicitudes_creadas += 1
            
            # Crear detalles
            for det in sol_data['detalles']:
                try:
                    material = Material.objects.get(codigo=det['material_codigo'])
                    cantidad_aprobada = det['cantidad'] if sol_data['estado'] in ['aprobada', 'despachada'] else None
                    
                    DetalleSolicitud.objects.create(
                        solicitud=solicitud,
                        material=material,
                        cantidad=det['cantidad'],
                        cantidad_aprobada=cantidad_aprobada
                    )
                    
                    detalles_creados += 1
                except Material.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f' ⚠️ Material {det["material_codigo"]} no encontrado'))
            
        self.stdout.write(self.style.SUCCESS(
            f' ✓ {solicitudes_creadas} solicitudes con {detalles_creados} detalles creados'
        ))
        
        # Mostrar distribución por técnico
        self.stdout.write('\n   Distribución de solicitudes:')
        for tecnico in tecnicos:
            count = Solicitud.objects.filter(solicitante=tecnico).count()
            self.stdout.write(f'   - {tecnico.get_full_name()}: {count} solicitudes')
        self.stdout.write('')

    def crear_movimientos_salida(self):
        """Crea movimientos de salida para solicitudes despachadas"""
        self.stdout.write('📤 Creando movimientos de salida...')
        
        usuario_bodega = User.objects.filter(rol='BODEGA').first()
        solicitudes_despachadas = Solicitud.objects.filter(estado='despachada')
        movimientos_creados = 0
        
        for solicitud in solicitudes_despachadas:
            for detalle in solicitud.detalles.all():
                cantidad = detalle.cantidad_aprobada or detalle.cantidad
                
                # Crear movimiento
                Movimiento.objects.create(
                    material=detalle.material,
                    usuario=usuario_bodega,  # Bodega realiza el movimiento
                    solicitud=solicitud,     # Vinculado a la solicitud del técnico
                    tipo='salida',
                    cantidad=cantidad,
                    detalle=f'Despacho solicitud #{solicitud.id} - Técnico: {solicitud.solicitante.get_full_name()}',
                    fecha=solicitud.fecha_respuesta
                )
                
                # Actualizar inventario
                inventario = detalle.material.inventario
                inventario.stock_actual -= cantidad
                inventario.save()
                
                movimientos_creados += 1
        
        self.stdout.write(self.style.SUCCESS(f' ✓ {movimientos_creados} movimientos creados\n'))

    def crear_materiales_adicionales(self):
        """Crea materiales adicionales para mayor diversidad"""
        self.stdout.write('➕ Creando materiales adicionales...')

        materiales_adicionales = [
            {'codigo': 'GAS-R22', 'descripcion': 'Gas Refrigerante R22', 'unidad': 'kg', 
             'categoria': 'insumo', 'stock': 45, 'stock_seg': 15},
            {'codigo': 'GAS-R134A', 'descripcion': 'Gas Refrigerante R134A', 'unidad': 'kg', 
             'categoria': 'insumo', 'stock': 38, 'stock_seg': 12},
            {'codigo': 'COMP-3HP', 'descripcion': 'Compresor 3 HP', 'unidad': 'unidad', 
             'categoria': 'equipo', 'stock': 12, 'stock_seg': 4},
            {'codigo': 'COMP-5HP', 'descripcion': 'Compresor 5 HP', 'unidad': 'unidad', 
             'categoria': 'equipo', 'stock': 8, 'stock_seg': 3},
            {'codigo': 'VALV-EXP-1/2', 'descripcion': 'Válvula expansión 1/2"', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 35, 'stock_seg': 10},
            {'codigo': 'VALV-EXP-3/8', 'descripcion': 'Válvula expansión 3/8"', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 42, 'stock_seg': 12},
            {'codigo': 'FILT-DESH-3/8', 'descripcion': 'Filtro deshidratador 3/8"', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 55, 'stock_seg': 15},
            {'codigo': 'FILT-DESH-1/2', 'descripcion': 'Filtro deshidratador 1/2"', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 48, 'stock_seg': 14},
            {'codigo': 'ACEI-POE-32', 'descripcion': 'Aceite POE 32', 'unidad': 'litro', 
             'categoria': 'insumo', 'stock': 28, 'stock_seg': 10},
            {'codigo': 'ACEI-MIN-68', 'descripcion': 'Aceite Mineral 68', 'unidad': 'litro', 
             'categoria': 'insumo', 'stock': 32, 'stock_seg': 10},
            {'codigo': 'TUB-COBRE-1/4', 'descripcion': 'Tubo cobre 1/4"', 'unidad': 'metro', 
             'categoria': 'insumo', 'stock': 150, 'stock_seg': 40},
            {'codigo': 'TUB-COBRE-1/2', 'descripcion': 'Tubo cobre 1/2"', 'unidad': 'metro', 
             'categoria': 'insumo', 'stock': 120, 'stock_seg': 35},
            {'codigo': 'TUB-COBRE-5/8', 'descripcion': 'Tubo cobre 5/8"', 'unidad': 'metro', 
             'categoria': 'insumo', 'stock': 95, 'stock_seg': 30},
            {'codigo': 'CAB-ELEC-3X2.5', 'descripcion': 'Cable eléctrico 3x2.5mm', 'unidad': 'metro', 
             'categoria': 'insumo', 'stock': 180, 'stock_seg': 50},
            {'codigo': 'CAB-ELEC-4X4', 'descripcion': 'Cable eléctrico 4x4mm', 'unidad': 'metro', 
             'categoria': 'insumo', 'stock': 140, 'stock_seg': 40},
            {'codigo': 'TERM-MECA', 'descripcion': 'Termostato mecánico', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 25, 'stock_seg': 8},
            {'codigo': 'TERM-DIGI-LCD', 'descripcion': 'Termostato digital LCD', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 18, 'stock_seg': 6},
            {'codigo': 'COND-9000BTU', 'descripcion': 'Condensador 9000 BTU', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 14, 'stock_seg': 5},
            {'codigo': 'COND-18000BTU', 'descripcion': 'Condensador 18000 BTU', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 10, 'stock_seg': 4},
            {'codigo': 'EVAP-9000BTU', 'descripcion': 'Evaporador 9000 BTU', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 12, 'stock_seg': 4},
            {'codigo': 'MOTOR-1/6HP', 'descripcion': 'Motor ventilador 1/6 HP', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 22, 'stock_seg': 7},
            {'codigo': 'MOTOR-1/3HP', 'descripcion': 'Motor ventilador 1/3 HP', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 18, 'stock_seg': 6},
            {'codigo': 'CAP-30MFD', 'descripcion': 'Capacitor 30 MFD', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 45, 'stock_seg': 12},
            {'codigo': 'CAP-60MFD', 'descripcion': 'Capacitor 60 MFD', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 38, 'stock_seg': 10},
            {'codigo': 'CAP-80MFD', 'descripcion': 'Capacitor 80 MFD', 'unidad': 'unidad', 
             'categoria': 'repuesto', 'stock': 32, 'stock_seg': 9},
            {'codigo': 'SOLD-5%PLATA', 'descripcion': 'Soldadura 5% plata', 'unidad': 'unidad', 
             'categoria': 'insumo', 'stock': 60, 'stock_seg': 18},
            {'codigo': 'SOLD-45%PLATA', 'descripcion': 'Soldadura 45% plata', 'unidad': 'unidad', 
             'categoria': 'insumo', 'stock': 35, 'stock_seg': 12},
            {'codigo': 'FLUX-PASTA', 'descripcion': 'Flux en pasta', 'unidad': 'unidad', 
             'categoria': 'insumo', 'stock': 42, 'stock_seg': 12},
            {'codigo': 'MANO-ANALOGICO', 'descripcion': 'Manómetro analógico', 'unidad': 'unidad', 
             'categoria': 'herramienta', 'stock': 15, 'stock_seg': 5},
            {'codigo': 'BOMB-VACIO-6CFM', 'descripcion': 'Bomba vacío 6 CFM', 'unidad': 'unidad', 
             'categoria': 'equipo', 'stock': 8, 'stock_seg': 3},
        ]

        ubicaciones = ['Bodega A1', 'Bodega A2', 'Bodega B1', 'Bodega C1', 
                      'Bodega C2', 'Bodega C3', 'Estante E1', 'Estante E2', 
                      'Estante F1', 'Estante F2']

        for data in materiales_adicionales:
            material = Material.objects.create(
                codigo=data['codigo'],
                descripcion=data['descripcion'],
                unidad_medida=data['unidad'],
                categoria=data['categoria'],
                ubicacion=random.choice(ubicaciones)
            )
            Inventario.objects.create(
                material=material,
                stock_actual=data['stock'],
                stock_seguridad=data['stock_seg']
            )

        self.stdout.write(self.style.SUCCESS(f'   ✓ {len(materiales_adicionales)} materiales adicionales creados\n'))

    def mostrar_resumen(self):
        """Muestra resumen de datos creados"""
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('📊 RESUMEN DE BASE DE DATOS')
        self.stdout.write('=' * 70)

        # Contar registros
        stats = {
            'Configuración': 1,
            'Roles': Rol.objects.count(),
            'Locales': Local.objects.count(),
            'Usuarios': User.objects.count(),
            'Materiales': Material.objects.count(),
            'Inventarios': Inventario.objects.count(),
            'Solicitudes': Solicitud.objects.count(),
            'Detalles Solicitud': DetalleSolicitud.objects.count(),
            'Movimientos': Movimiento.objects.count(),
        }

        for key, value in stats.items():
            self.stdout.write(f'   {key:.<25} {value:>6}')

        # Stock crítico
        stock_critico = Inventario.objects.filter(
            stock_actual__lte=F('stock_seguridad')
        ).count()

        self.stdout.write('\n' + '-' * 70)
        self.stdout.write(f'   Materiales en stock crítico: {stock_critico}')
        self.stdout.write('=' * 70)

    def get_solicitudes_data(self):
        """Retorna los datos de las 72 solicitudes históricas"""
        # Aquí van los datos de las solicitudes
        return [
            {
                'motivo': '''Mantenimiento preventivo equipo refrigeración comercial''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-06-15T10:30:00Z',
                'fecha_respuesta': '2025-06-15T11:00:00Z',
                'fecha_actualizacion': '2025-06-15T11:00:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 3},
                    {'material_codigo': 'MAT0002', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Instalación sistema refrigeración industrial''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-06-20T14:20:00Z',
                'fecha_respuesta': '2025-06-20T15:00:00Z',
                'fecha_actualizacion': '2025-06-20T15:00:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 2},
                    {'material_codigo': 'MAT0003', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Reparación urgente compresor''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-07-05T09:15:00Z',
                'fecha_respuesta': '2025-07-05T09:45:00Z',
                'fecha_actualizacion': '2025-07-05T09:45:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 4},
                    {'material_codigo': 'MAT0004', 'cantidad': 2},
                ]
            },
            {
                'motivo': '''Mantenimiento cámara frigorífica''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-07-18T11:30:00Z',
                'fecha_respuesta': '2025-07-18T12:00:00Z',
                'fecha_actualizacion': '2025-07-18T12:00:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 6},
                    {'material_codigo': 'MAT0005', 'cantidad': 3},
                ]
            },
            {
                'motivo': '''Instalación unidad condensadora''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-08-02T08:45:00Z',
                'fecha_respuesta': '2025-08-02T09:15:00Z',
                'fecha_actualizacion': '2025-08-02T09:15:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 5},
                    {'material_codigo': 'MAT0003', 'cantidad': 7},
                ]
            },
            {
                'motivo': '''Servicio técnico preventivo''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-08-15T13:20:00Z',
                'fecha_respuesta': '2025-08-15T14:00:00Z',
                'fecha_actualizacion': '2025-08-15T14:00:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 4},
                    {'material_codigo': 'MAT0006', 'cantidad': 2},
                ]
            },
            {
                'motivo': '''Reparación sistema de enfriamiento''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-09-03T10:00:00Z',
                'fecha_respuesta': '2025-09-03T10:30:00Z',
                'fecha_actualizacion': '2025-09-03T10:30:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 3},
                    {'material_codigo': 'MAT0004', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Instalación equipo nuevo cliente''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-09-20T09:30:00Z',
                'fecha_respuesta': '2025-09-20T10:00:00Z',
                'fecha_actualizacion': '2025-09-20T10:00:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 8},
                    {'material_codigo': 'MAT0005', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Mantenimiento correctivo urgente''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-10-08T14:45:00Z',
                'fecha_respuesta': '2025-10-08T15:15:00Z',
                'fecha_actualizacion': '2025-10-08T15:15:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 6},
                    {'material_codigo': 'MAT0003', 'cantidad': 3},
                ]
            },
            {
                'motivo': '''Reposición materiales bodega''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-10-22T11:00:00Z',
                'fecha_respuesta': '2025-10-22T11:30:00Z',
                'fecha_actualizacion': '2025-10-22T11:30:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 5},
                    {'material_codigo': 'MAT0007', 'cantidad': 2},
                ]
            },
            {
                'motivo': '''Proyecto instalación cámara frigorífica grande''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-11-05T08:30:00Z',
                'fecha_respuesta': '2025-11-05T09:00:00Z',
                'fecha_actualizacion': '2025-11-05T09:00:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 7},
                    {'material_codigo': 'MAT0004', 'cantidad': 6},
                    {'material_codigo': 'MAT0008', 'cantidad': 3},
                ]
            },
            {
                'motivo': '''Servicio técnico mensual''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-11-18T10:15:00Z',
                'fecha_respuesta': '2025-11-18T10:45:00Z',
                'fecha_actualizacion': '2025-11-18T10:45:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 4},
                    {'material_codigo': 'MAT0005', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Servicio técnico preventivo trimestral''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-07-04T08:04:00Z',
                'fecha_respuesta': '2025-07-04T09:56:00Z',
                'fecha_actualizacion': '2025-07-04T09:56:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 4},
                    {'material_codigo': 'MAT0006', 'cantidad': 4},
                    {'material_codigo': 'MAT0002', 'cantidad': 3},
                    {'material_codigo': 'MAT0008', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Reparación válvula expansión''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-07-31T14:16:00Z',
                'fecha_respuesta': '2025-07-31T15:01:00Z',
                'fecha_actualizacion': '2025-07-31T15:01:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0005', 'cantidad': 4},
                    {'material_codigo': 'MAT0001', 'cantidad': 8},
                    {'material_codigo': 'MAT0009', 'cantidad': 1},
                    {'material_codigo': 'MAT0002', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Mantenimiento preventivo mensual''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-11-02T12:47:00Z',
                'fecha_respuesta': '2025-11-02T13:41:00Z',
                'fecha_actualizacion': '2025-11-02T13:41:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0003', 'cantidad': 3},
                    {'material_codigo': 'MAT0001', 'cantidad': 5},
                    {'material_codigo': 'MAT0007', 'cantidad': 3},
                ]
            },
            {
                'motivo': '''Instalación termostatos digitales''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-08-10T09:24:00Z',
                'fecha_respuesta': '2025-08-10T11:17:00Z',
                'fecha_actualizacion': '2025-08-10T11:17:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 8},
                    {'material_codigo': 'MAT0007', 'cantidad': 1},
                ]
            },
            {
                'motivo': '''Cambio filtros deshidratadores''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-07-06T10:47:00Z',
                'fecha_respuesta': '2025-07-06T11:57:00Z',
                'fecha_actualizacion': '2025-07-06T11:57:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 7},
                    {'material_codigo': 'MAT0004', 'cantidad': 2},
                ]
            },
            {
                'motivo': '''Cambio compresor averiado''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-07-04T11:36:00Z',
                'fecha_respuesta': '2025-07-04T13:20:00Z',
                'fecha_actualizacion': '2025-07-04T13:20:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 5},
                    {'material_codigo': 'MAT0004', 'cantidad': 5},
                    {'material_codigo': 'MAT0005', 'cantidad': 1},
                ]
            },
            {
                'motivo': '''Instalación equipo cliente comercial''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-08-26T16:14:00Z',
                'fecha_respuesta': '2025-08-26T18:07:00Z',
                'fecha_actualizacion': '2025-08-26T18:07:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 5},
                    {'material_codigo': 'MAT0008', 'cantidad': 3},
                    {'material_codigo': 'MAT0007', 'cantidad': 5},
                    {'material_codigo': 'MAT0005', 'cantidad': 1},
                ]
            },
            {
                'motivo': '''Reparación sistema control temperatura''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-07-26T17:19:00Z',
                'fecha_respuesta': '2025-07-26T19:15:00Z',
                'fecha_actualizacion': '2025-07-26T19:15:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0003', 'cantidad': 7},
                    {'material_codigo': 'MAT0005', 'cantidad': 1},
                    {'material_codigo': 'MAT0009', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Reparación fuga refrigerante''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-09-18T08:02:00Z',
                'fecha_respuesta': '2025-09-18T09:32:00Z',
                'fecha_actualizacion': '2025-09-18T09:32:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0008', 'cantidad': 5},
                    {'material_codigo': 'MAT0001', 'cantidad': 5},
                    {'material_codigo': 'MAT0002', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Reparación fuga refrigerante''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-07-21T14:02:00Z',
                'fecha_respuesta': '2025-07-21T15:42:00Z',
                'fecha_actualizacion': '2025-07-21T15:42:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0003', 'cantidad': 7},
                    {'material_codigo': 'MAT0008', 'cantidad': 5},
                    {'material_codigo': 'MAT0004', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Instalación sistema aire acondicionado''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-07-26T10:19:00Z',
                'fecha_respuesta': '2025-07-26T12:19:00Z',
                'fecha_actualizacion': '2025-07-26T12:19:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0008', 'cantidad': 1},
                    {'material_codigo': 'MAT0001', 'cantidad': 6},
                    {'material_codigo': 'MAT0009', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Instalación unidad condensadora nueva''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-10-28T13:24:00Z',
                'fecha_respuesta': '2025-10-28T15:24:00Z',
                'fecha_actualizacion': '2025-10-28T15:24:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0007', 'cantidad': 4},
                    {'material_codigo': 'MAT0005', 'cantidad': 2},
                    {'material_codigo': 'MAT0003', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Cambio compresor averiado''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-07-04T11:15:00Z',
                'fecha_respuesta': '2025-07-04T12:18:00Z',
                'fecha_actualizacion': '2025-07-04T12:18:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 7},
                    {'material_codigo': 'MAT0005', 'cantidad': 5},
                    {'material_codigo': 'MAT0001', 'cantidad': 7},
                ]
            },
            {
                'motivo': '''Reposición stock materiales críticos''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-07-23T13:10:00Z',
                'fecha_respuesta': '2025-07-23T14:32:00Z',
                'fecha_actualizacion': '2025-07-23T14:32:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0004', 'cantidad': 5},
                    {'material_codigo': 'MAT0007', 'cantidad': 1},
                    {'material_codigo': 'MAT0001', 'cantidad': 6},
                    {'material_codigo': 'MAT0003', 'cantidad': 7},
                ]
            },
            {
                'motivo': '''Servicio técnico correctivo''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-06-03T13:26:00Z',
                'fecha_respuesta': '2025-06-03T14:08:00Z',
                'fecha_actualizacion': '2025-06-03T14:08:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0007', 'cantidad': 4},
                    {'material_codigo': 'MAT0008', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Instalación sistema aire acondicionado''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-06-21T11:27:00Z',
                'fecha_respuesta': '2025-06-21T12:35:00Z',
                'fecha_actualizacion': '2025-06-21T12:35:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 5},
                    {'material_codigo': 'MAT0009', 'cantidad': 3},
                    {'material_codigo': 'MAT0005', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Instalación equipo cliente comercial''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-09-23T13:55:00Z',
                'fecha_respuesta': '2025-09-23T15:54:00Z',
                'fecha_actualizacion': '2025-09-23T15:54:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0009', 'cantidad': 2},
                    {'material_codigo': 'MAT0004', 'cantidad': 2},
                ]
            },
            {
                'motivo': '''Instalación termostatos digitales''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-11-15T12:04:00Z',
                'fecha_respuesta': '2025-11-15T12:58:00Z',
                'fecha_actualizacion': '2025-11-15T12:58:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 4},
                    {'material_codigo': 'MAT0007', 'cantidad': 2},
                    {'material_codigo': 'MAT0006', 'cantidad': 3},
                    {'material_codigo': 'MAT0005', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Mantenimiento preventivo equipo refrigeración''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-09-27T08:48:00Z',
                'fecha_respuesta': '2025-09-27T10:19:00Z',
                'fecha_actualizacion': '2025-09-27T10:19:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0005', 'cantidad': 1},
                    {'material_codigo': 'MAT0009', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Servicio técnico correctivo''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-06-12T16:18:00Z',
                'fecha_respuesta': '2025-06-12T17:54:00Z',
                'fecha_actualizacion': '2025-06-12T17:54:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0007', 'cantidad': 1},
                    {'material_codigo': 'MAT0004', 'cantidad': 5},
                    {'material_codigo': 'MAT0005', 'cantidad': 4},
                    {'material_codigo': 'MAT0001', 'cantidad': 8},
                ]
            },
            {
                'motivo': '''Cambio filtros deshidratadores''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-08-20T15:03:00Z',
                'fecha_respuesta': '2025-08-20T16:46:00Z',
                'fecha_actualizacion': '2025-08-20T16:46:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0009', 'cantidad': 2},
                    {'material_codigo': 'MAT0005', 'cantidad': 2},
                    {'material_codigo': 'MAT0008', 'cantidad': 2},
                    {'material_codigo': 'MAT0006', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Instalación equipo cliente comercial''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-05-26T11:05:00Z',
                'fecha_respuesta': '2025-05-26T13:01:00Z',
                'fecha_actualizacion': '2025-05-26T13:01:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0009', 'cantidad': 5},
                    {'material_codigo': 'MAT0007', 'cantidad': 5},
                    {'material_codigo': 'MAT0004', 'cantidad': 5},
                    {'material_codigo': 'MAT0003', 'cantidad': 2},
                ]
            },
            {
                'motivo': '''Instalación unidad condensadora nueva''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-08-25T09:39:00Z',
                'fecha_respuesta': '2025-08-25T10:20:00Z',
                'fecha_actualizacion': '2025-08-25T10:20:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0005', 'cantidad': 4},
                    {'material_codigo': 'MAT0004', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Instalación termostatos digitales''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-09-11T08:04:00Z',
                'fecha_respuesta': '2025-09-11T09:42:00Z',
                'fecha_actualizacion': '2025-09-11T09:42:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0007', 'cantidad': 1},
                    {'material_codigo': 'MAT0003', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Mantenimiento cámara frigorífica''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-11-03T12:08:00Z',
                'fecha_respuesta': '2025-11-03T13:47:00Z',
                'fecha_actualizacion': '2025-11-03T13:47:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0001', 'cantidad': 7},
                    {'material_codigo': 'MAT0002', 'cantidad': 7},
                ]
            },
            {
                'motivo': '''Mantenimiento preventivo equipo refrigeración''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-10-01T13:47:00Z',
                'fecha_respuesta': '2025-10-01T14:54:00Z',
                'fecha_actualizacion': '2025-10-01T14:54:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0007', 'cantidad': 3},
                    {'material_codigo': 'MAT0006', 'cantidad': 5},
                ]
            },
            {
                'motivo': '''Reparación sistema control temperatura''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-06-20T11:33:00Z',
                'fecha_respuesta': '2025-06-20T12:23:00Z',
                'fecha_actualizacion': '2025-06-20T12:23:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0007', 'cantidad': 3},
                    {'material_codigo': 'MAT0001', 'cantidad': 4},
                    {'material_codigo': 'MAT0002', 'cantidad': 7},
                ]
            },
            {
                'motivo': '''Servicio urgente refrigeración industrial''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-08-08T08:09:00Z',
                'fecha_respuesta': '2025-08-08T08:49:00Z',
                'fecha_actualizacion': '2025-08-08T08:49:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0002', 'cantidad': 8},
                    {'material_codigo': 'MAT0001', 'cantidad': 3},
                ]
            },
            {
                'motivo': '''Mantenimiento compresores industriales''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-06-30T15:50:00Z',
                'fecha_respuesta': '2025-06-30T16:27:00Z',
                'fecha_actualizacion': '2025-06-30T16:27:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0007', 'cantidad': 4},
                    {'material_codigo': 'MAT0003', 'cantidad': 5},
                    {'material_codigo': 'MAT0001', 'cantidad': 8},
                ]
            },
            {
                'motivo': '''Mantenimiento compresores industriales''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-11-09T17:55:00Z',
                'fecha_respuesta': '2025-11-09T19:11:00Z',
                'fecha_actualizacion': '2025-11-09T19:11:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0004', 'cantidad': 3},
                    {'material_codigo': 'MAT0008', 'cantidad': 1},
                ]
            },
            {
                'motivo': '''Mantenimiento preventivo mensual''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-07-29T12:16:00Z',
                'fecha_respuesta': '2025-07-29T13:27:00Z',
                'fecha_actualizacion': '2025-07-29T13:27:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0004', 'cantidad': 3},
                    {'material_codigo': 'MAT0006', 'cantidad': 3},
                    {'material_codigo': 'MAT0008', 'cantidad': 2},
                    {'material_codigo': 'MAT0001', 'cantidad': 2},
                ]
            },
            {
                'motivo': '''Mantenimiento preventivo mensual''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-09-25T15:11:00Z',
                'fecha_respuesta': '2025-09-25T15:45:00Z',
                'fecha_actualizacion': '2025-09-25T15:45:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0005', 'cantidad': 1},
                    {'material_codigo': 'MAT0006', 'cantidad': 3},
                ]
            },
            {
                'motivo': '''Reparación válvula expansión''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-09-17T08:41:00Z',
                'fecha_respuesta': '2025-09-17T09:35:00Z',
                'fecha_actualizacion': '2025-09-17T09:35:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0008', 'cantidad': 4},
                    {'material_codigo': 'MAT0002', 'cantidad': 7},
                    {'material_codigo': 'MAT0005', 'cantidad': 2},
                ]
            },
            {
                'motivo': '''Reemplazo componentes refrigeración''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-09-05T13:30:00Z',
                'fecha_respuesta': '2025-09-05T14:09:00Z',
                'fecha_actualizacion': '2025-09-05T14:09:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0008', 'cantidad': 5},
                    {'material_codigo': 'MAT0002', 'cantidad': 8},
                    {'material_codigo': 'MAT0004', 'cantidad': 4},
                    {'material_codigo': 'MAT0006', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Mantenimiento preventivo equipo refrigeración''',
                'estado': 'aprobada',
                'fecha_solicitud': '2025-06-09T13:09:00Z',
                'fecha_respuesta': '2025-06-09T15:07:00Z',
                'fecha_actualizacion': '2025-06-09T15:07:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0003', 'cantidad': 4},
                    {'material_codigo': 'MAT0002', 'cantidad': 3},
                    {'material_codigo': 'MAT0009', 'cantidad': 1},
                ]
            },
            {
                'motivo': '''Reparación sistema de enfriamiento''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-08-12T15:43:00Z',
                'fecha_respuesta': '2025-08-12T16:55:00Z',
                'fecha_actualizacion': '2025-08-12T16:55:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0006', 'cantidad': 4},
                    {'material_codigo': 'MAT0002', 'cantidad': 3},
                    {'material_codigo': 'MAT0001', 'cantidad': 5},
                    {'material_codigo': 'MAT0005', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Mantenimiento compresores industriales''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-10-21T14:39:00Z',
                'fecha_respuesta': '2025-10-21T15:17:00Z',
                'fecha_actualizacion': '2025-10-21T15:17:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0007', 'cantidad': 4},
                    {'material_codigo': 'MAT0002', 'cantidad': 4},
                    {'material_codigo': 'MAT0008', 'cantidad': 4},
                ]
            },
            {
                'motivo': '''Instalación unidad condensadora nueva''',
                'estado': 'despachada',
                'fecha_solicitud': '2025-10-07T11:27:00Z',
                'fecha_respuesta': '2025-10-07T12:07:00Z',
                'fecha_actualizacion': '2025-10-07T12:07:00Z',
                'detalles': [
                    {'material_codigo': 'MAT0005', 'cantidad': 4},
                    {'material_codigo': 'MAT0007', 'cantidad': 5},
                ]
            },
        ]