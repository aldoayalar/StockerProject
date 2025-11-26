from django.core.management.base import BaseCommand
from core.ml_stock_critico import ejecutar_calculo_global

class Command(BaseCommand):
    help = 'Calcula el stock crítico dinámico para todos los materiales'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando cálculo de stock crítico...')
        resultados = ejecutar_calculo_global()
        self.stdout.write(
            self.style.SUCCESS(f'Cálculo completado. {len(resultados)} materiales procesados.')
        )
