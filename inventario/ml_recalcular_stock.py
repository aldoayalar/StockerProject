"""
Comando de gestión para recalcular el stock crítico sugerido usando ML.
"""
from django.core.management.base import BaseCommand
from core.services.ml_service import recalcular_stock_critico


class Command(BaseCommand):
    help = 'Recalcula el stock crítico sugerido para todos los materiales usando Machine Learning'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando cálculo de stock crítico con ML...'))
        
        resultados = recalcular_stock_critico()
        
        self.stdout.write('\n--- Resultados del Cálculo ML ---\n')
        
        for sku, datos in resultados.items():
            self.stdout.write(f'Material: {sku}')
            self.stdout.write(f'  Stock Crítico Sugerido: {datos["stock_critico"]}')
            self.stdout.write(f'  Promedio Diario: {datos["promedio_diario"]}')
            self.stdout.write(f'  Desviación Estándar: {datos["desviacion"]}')
            if 'lead_time' in datos:
                self.stdout.write(f'  Lead Time: {datos["lead_time"]} días')
                self.stdout.write(f'  Movimientos Analizados: {datos["movimientos_analizados"]}')
                self.stdout.write(f'  Días con Movimientos: {datos["dias_con_movimientos"]}')
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('✓ Cálculo de stock crítico completado!'))
