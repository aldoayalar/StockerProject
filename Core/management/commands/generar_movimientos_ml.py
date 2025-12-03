"""
Genera movimientos históricos con fechas distribuidas en 180 días

Uso:
    python manage.py generar_movimientos_ml --cantidad 110 --limpiar
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Material, Movimiento, Usuario
import random


class Command(BaseCommand):
    help = 'Genera movimientos históricos para entrenamiento ML'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Eliminar movimientos antes de generar'
        )
        parser.add_argument(
            '--cantidad',
            type=int,
            default=110,
            help='Movimientos por material (default: 110)'
        )

    def handle(self, *args, **options):
        limpiar = options['limpiar']
        cant_por_material = options['cantidad']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🚀 GENERADOR DE MOVIMIENTOS ML'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Usuario
        usuario = Usuario.objects.filter(rol='BODEGA').first() or Usuario.objects.first()
        if not usuario:
            self.stdout.write(self.style.ERROR('❌ No hay usuarios'))
            return

        # Limpiar
        if limpiar:
            count_prev = Movimiento.objects.count()
            Movimiento.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'🗑️  {count_prev} movimientos eliminados'))

        # Materiales
        materiales = list(Material.objects.all())
        if not materiales:
            self.stdout.write(self.style.ERROR('❌ No hay materiales'))
            return

        self.stdout.write(f'📦 Materiales: {len(materiales)}')
        self.stdout.write(f'🎲 Movimientos/material: {cant_por_material}')
        self.stdout.write('')

        # Patrones de demanda
        patrones = {
            'GAS': (10, 15, 4),
            'CAB': (12, 25, 6),
            'COMP': (2, 4, 1),
            'TUB': (20, 35, 8),
            'MOTOR': (2, 5, 2),
            'BOMB': (3, 8, 2),
            'CAP': (4, 10, 3),
            'VALV': (3, 8, 3),
            'FILT': (5, 12, 4),
            'TERM': (2, 6, 2),
            'SOLD': (6, 15, 4),
            'ACEI': (4, 10, 3),
            'COND': (1, 3, 1),
            'EVAP': (1, 3, 1),
            'MANO': (2, 5, 2),
            'FLUX': (3, 8, 2),
        }

        fecha_base = timezone.now() - timedelta(days=180)
        total_creados = 0
        movimientos_batch = []
        BATCH_SIZE = 1000

        # Generar movimientos
        for idx, material in enumerate(materiales, 1):
            codigo = material.codigo.upper()

            # Determinar patrón
            patron = None
            for prefijo, valores in patrones.items():
                if codigo.startswith(prefijo):
                    patron = valores
                    break

            if not patron:
                patron = (5, 12, 4)

            demanda_min, demanda_max, variacion = patron

            for i in range(cant_por_material):
                # Fecha aleatoria en últimos 180 días
                dias_atras = random.randint(0, 180)
                fecha = fecha_base + timedelta(days=dias_atras)

                # Cantidad
                cantidad = random.randint(demanda_min, demanda_max)
                cantidad += random.randint(-variacion, variacion)
                cantidad = max(1, cantidad)

                # Estacionalidad
                if fecha.month in [12, 1, 2]:
                    cantidad = int(cantidad * 1.5)
                elif fecha.month in [6, 7, 8]:
                    cantidad = max(1, int(cantidad * 0.8))

                # Spike ocasional
                if random.random() < 0.1:
                    cantidad = int(cantidad * 2.5)

                # Agregar a batch
                movimientos_batch.append(
                    Movimiento(
                        material=material,
                        usuario=usuario,
                        tipo='salida',
                        cantidad=cantidad,
                        detalle=f'Movimiento histórico ML',
                        fecha=fecha  # ← Ahora funciona!
                    )
                )
                total_creados += 1

                # Guardar batch
                if len(movimientos_batch) >= BATCH_SIZE:
                    Movimiento.objects.bulk_create(movimientos_batch)
                    movimientos_batch = []

            # Progreso
            barra = '█' * (idx * 40 // len(materiales))
            barra += '░' * (40 - idx * 40 // len(materiales))
            self.stdout.write(
                f'  [{barra}] {idx}/{len(materiales)} | {codigo:20s}'
            )

        # Guardar restantes
        if movimientos_batch:
            Movimiento.objects.bulk_create(movimientos_batch)

        # Resumen
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ GENERACIÓN COMPLETADA'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'📊 Total: {total_creados} movimientos')
        self.stdout.write(f'📦 Materiales: {len(materiales)}')
        self.stdout.write(f'📈 Promedio: {total_creados // len(materiales)}/material')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🚀 Siguiente paso:'))
        self.stdout.write('   python manage.py calcular_stock_critico --sin-estacion')
        self.stdout.write(self.style.SUCCESS('=' * 70))