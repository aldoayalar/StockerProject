from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Material, Movimiento, Usuario, Solicitud, DetalleSolicitud, Local
import random

class Command(BaseCommand):
    help = 'Genera historial realista con Locales, Solicitudes y Movimientos para ML'

    def add_arguments(self, parser):
        parser.add_argument('--limpiar', action='store_true', help='Eliminar todo antes de generar')
        parser.add_argument('--cantidad', type=int, default=300, help='Movimientos promedio por material')
        parser.add_argument('--dias', type=int, default=365, help='Días de historial')

    def handle(self, *args, **options):
        limpiar = options['limpiar']
        cant_promedio = options['cantidad']
        dias_historial = options['dias']

        self.stdout.write(self.style.SUCCESS('🚀 GENERADOR AVANZADO (Locales + Solicitudes + Movs)'))

        # 1. Usuarios y Locales
        usuario = Usuario.objects.filter(rol='BODEGA').first() or Usuario.objects.first()
        locales = list(Local.objects.all())
        
        if not usuario:
            self.stdout.write(self.style.ERROR('❌ Falta Usuario'))
            return
        if not locales:
            self.stdout.write(self.style.WARNING('⚠️ No hay locales. Creando "Local Central" por defecto...'))
            local_def = Local.objects.create(codigo="CEN01", nombre="Local Central", direccion="Calle Falsa 123", comuna="Santiago", region="RM")
            locales = [local_def]

        # 2. Limpieza
        if limpiar:
            self.stdout.write('🗑️  Limpiando datos antiguos...')
            Movimiento.objects.all().delete()
            DetalleSolicitud.objects.all().delete()
            Solicitud.objects.all().delete()

        materiales = list(Material.objects.all())
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=dias_historial)

        # Configuración de Patrones (Igual que antes)
        patron_verano = [1.5, 1.5, 1.2, 0.8, 0.6, 0.5, 0.5, 0.6, 0.8, 1.0, 1.2, 1.5]
        patron_invierno = [0.6, 0.6, 0.8, 1.0, 1.2, 1.5, 1.5, 1.4, 1.0, 0.8, 0.6, 0.5]
        patron_plano = [1.0] * 12
        
        config_materiales = {
            'GAS': {'patron': patron_verano, 'base': (10, 20)},
            'CAB': {'patron': patron_invierno, 'base': (15, 40)},
            # ... tus otras configs ...
        }

        # Contenedores para Bulk Create
        solicitudes_batch = []
        detalles_batch = []
        movimientos_batch = []
        
        # Diccionario auxiliar para asignar IDs de solicitudes en memoria antes de guardar
        # Nota: Bulk create de relaciones complejas es difícil en Django puro sin guardar ids.
        # Para simplificar y mantener rendimiento decente, guardaremos Solicitudes en bloques pequeños
        # y luego sus detalles.
        
        BATCH_SIZE = 500
        total_creados = 0

        self.stdout.write('⏳ Generando datos...')

        for idx, material in enumerate(materiales, 1):
            codigo = material.codigo.upper()
            
            # Detectar config
            config = {'patron': patron_plano, 'base': (5, 15)}
            for prefijo, conf in config_materiales.items():
                if codigo.startswith(prefijo):
                    config = conf
                    break
            
            pesos = config['patron']
            rango = config['base']
            probabilidad = cant_promedio / dias_historial
            
            current_date = fecha_inicio
            
            while current_date <= fecha_fin:
                mes_idx = current_date.month - 1
                peso = pesos[mes_idx]
                
                if random.random() < (probabilidad * peso):
                    # Datos aleatorios
                    local = random.choice(locales)
                    cant_min, cant_max = rango
                    cantidad = random.randint(cant_min, cant_max)
                    
                    if peso > 1.2: cantidad = int(cantidad * 1.2)
                    cantidad = max(1, cantidad)

                    # 1. Crear Solicitud (Guardamos de una vez para tener ID)
                    solicitud = Solicitud.objects.create(
                        solicitante=usuario,
                        local_destino=local,
                        motivo="Generado por ML Script",
                        estado='aprobada',
                        fecha_solicitud=current_date,
                        fecha_respuesta=current_date,
                        respondido_por=usuario
                    )

                    # 2. Crear Detalle
                    detalles_batch.append(DetalleSolicitud(
                        solicitud=solicitud,
                        material=material,
                        cantidad=cantidad,
                        cantidad_aprobada=cantidad
                    ))

                    # 3. Crear Movimiento (Vinculado a la solicitud y local indirectamente)
                    movimientos_batch.append(Movimiento(
                        material=material,
                        usuario=usuario,
                        solicitud=solicitud, # <--- Aquí está la clave para el ML
                        tipo='salida',
                        cantidad=cantidad,
                        detalle=f"Despacho a {local.nombre}",
                        fecha=current_date
                    ))
                    
                    total_creados += 1

                current_date += timedelta(days=1)
            
            # Guardar lotes por material para no saturar RAM
            if detalles_batch:
                DetalleSolicitud.objects.bulk_create(detalles_batch)
                Movimiento.objects.bulk_create(movimientos_batch)
                detalles_batch = []
                movimientos_batch = []
            
            # Progreso
            if idx % 10 == 0:
                self.stdout.write(f'\r Procesando material {idx}/{len(materiales)}...', ending='')

        self.stdout.write('\n✅ Finalizado.')
