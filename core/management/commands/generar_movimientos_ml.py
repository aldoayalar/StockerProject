"""
Genera movimientos históricos con patrones estacionales realistas (frecuencia + cantidad).
Uso:
    python manage.py generar_movimientos_ml --cantidad 300 --dias 365 --limpiar
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Material, Movimiento, Usuario
import random
import math

class Command(BaseCommand):
    help = 'Genera movimientos históricos con patrones estacionales realistas para ML'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Eliminar movimientos antes de generar'
        )
        parser.add_argument(
            '--cantidad',
            type=int,
            default=300,
            help='Movimientos promedio por material (default: 300)'
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=365,
            help='Días de historial a generar (default: 365)'
        )

    def handle(self, *args, **options):
        limpiar = options['limpiar']
        cant_promedio = options['cantidad']
        dias_historial = options['dias']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🚀 GENERADOR DE MOVIMIENTOS ML MEJORADO'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Usuario BODEGA (para movimientos de salida manual)
        usuario = Usuario.objects.filter(rol='BODEGA').first() or Usuario.objects.first()
        if not usuario:
            self.stdout.write(self.style.ERROR('❌ No hay usuarios'))
            return

        # Limpiar
        if limpiar:
            count_prev = Movimiento.objects.count()
            Movimiento.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'🗑️  {count_prev} movimientos eliminados'))

        materiales = list(Material.objects.all())
        if not materiales:
            self.stdout.write(self.style.ERROR('❌ No hay materiales'))
            return

        self.stdout.write(f'📦 Materiales: {len(materiales)}')
        self.stdout.write(f'📅 Historial: {dias_historial} días')
        self.stdout.write('')

        # Definición de patrones estacionales (Pesos por mes: Ene...Dic)
        # 1.0 = demanda normal, >1.0 = alta, <1.0 = baja
        
        # Verano fuerte (Gases, Aire Acondicionado) - Alta en Dic-Feb
        patron_verano = [1.5, 1.5, 1.2, 0.8, 0.6, 0.5, 0.5, 0.6, 0.8, 1.0, 1.2, 1.5]
        
        # Invierno fuerte (Calefacción, Soldadura, Cables) - Alta en Jun-Ago
        patron_invierno = [0.6, 0.6, 0.8, 1.0, 1.2, 1.5, 1.5, 1.4, 1.0, 0.8, 0.6, 0.5]
        
        # Constante (Ferretería general, tornillos, aceites)
        patron_plano = [1.0] * 12

        # Asignación de patrones por código
        config_materiales = {
            'GAS':  {'patron': patron_verano,   'base': (10, 20)}, # Gases
            'COMP': {'patron': patron_verano,   'base': (2, 5)},   # Compresores
            'CAP':  {'patron': patron_verano,   'base': (5, 12)},  # Capacitores
            'MOT':  {'patron': patron_verano,   'base': (1, 3)},   # Motores
            
            'CAB':  {'patron': patron_invierno, 'base': (15, 40)}, # Cables
            'SOLD': {'patron': patron_invierno, 'base': (5, 15)},  # Soldadura
            'TERM': {'patron': patron_invierno, 'base': (4, 10)},  # Termostatos
            
            'TUB':  {'patron': patron_plano,    'base': (20, 50)}, # Tuberías
            'VALV': {'patron': patron_plano,    'base': (5, 10)},  # Válvulas
            'FILT': {'patron': patron_plano,    'base': (8, 15)},  # Filtros
        }

        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=dias_historial)
        
        total_creados = 0
        movimientos_batch = []
        BATCH_SIZE = 2000

        for idx, material in enumerate(materiales, 1):
            codigo = material.codigo.upper()
            
            # Detectar configuración
            config = {'patron': patron_plano, 'base': (5, 15)} # Default
            for prefijo, conf in config_materiales.items():
                if codigo.startswith(prefijo):
                    config = conf
                    break
            
            pesos_mensuales = config['patron']
            rango_base = config['base']
            
            # Generar fechas distribuidas según pesos mensuales
            # Algoritmo: Iterar día a día y decidir si generar movimiento basado en probabilidad
            
            # Ajustar probabilidad diaria para alcanzar el target de cantidad aprox.
            probabilidad_base = cant_promedio / dias_historial 
            
            movs_material = 0
            current_date = fecha_inicio
            
            while current_date <= fecha_fin:
                mes_idx = current_date.month - 1
                peso_mes = pesos_mensuales[mes_idx]
                
                # Probabilidad de que haya movimiento este día
                # Se multiplica la prob. base por el peso estacional
                if random.random() < (probabilidad_base * peso_mes):
                    
                    # Calcular cantidad (también afectada levemente por la estación)
                    cant_min, cant_max = rango_base
                    cantidad = random.randint(cant_min, cant_max)
                    
                    # En temporada alta, también sube un poco el volumen por pedido (20%)
                    if peso_mes > 1.2:
                        cantidad = int(cantidad * 1.2)
                    
                    # Spike ocasional (urgencia) - 5% de las veces
                    if random.random() < 0.05:
                        cantidad = int(cantidad * 2.0)
                        detalle = 'Salida URGENTE ML'
                    else:
                        detalle = 'Consumo normal ML'

                    cantidad = max(1, cantidad)

                    movimientos_batch.append(
                        Movimiento(
                            material=material,
                            usuario=usuario,
                            tipo='salida',
                            cantidad=cantidad,
                            detalle=detalle,
                            fecha=current_date
                        )
                    )
                    movs_material += 1
                    total_creados += 1
                
                current_date += timedelta(days=1)
            
            # Bulk create parcial
            if len(movimientos_batch) >= BATCH_SIZE:
                Movimiento.objects.bulk_create(movimientos_batch)
                movimientos_batch = []

            # Barra de progreso
            progreso = idx / len(materiales)
            largo_barra = 40
            llenos = int(progreso * largo_barra)
            barra = '█' * llenos + '░' * (largo_barra - llenos)
            self.stdout.write(f'\r [{barra}] {idx}/{len(materiales)} | {codigo:10s} | {movs_material} movs', ending='')

        # Guardar remanentes
        if movimientos_batch:
            Movimiento.objects.bulk_create(movimientos_batch)

        self.stdout.write('\n')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'✅ Proceso finalizado. Total: {total_creados} movimientos.')
        self.stdout.write(f'📊 Promedio real: {total_creados // len(materiales)} movs/material')
        self.stdout.write(self.style.SUCCESS('=' * 70))
