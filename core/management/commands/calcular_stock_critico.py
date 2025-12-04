"""
Comando Django simplificado para calcular stock crítico desde BD.

Uso:
    python manage.py calcular_stock_ml
    python manage.py calcular_stock_ml --formula estandar
    python manage.py calcular_stock_ml --estacion Verano

Autor: Sistema ML Stocker (versión simplificada)
"""

from django.core.management.base import BaseCommand
from core.services.ml_service import ejecutar_calculo_global, detectar_estacion_actual


class Command(BaseCommand):
    help = 'Calcula el stock crítico usando Machine Learning desde la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--formula',
            type=str,
            choices=['conservadora', 'estandar'],
            default='conservadora',
            help="Fórmula: 'conservadora' (7d + 2.5σ) o 'estandar' (ROP)"
        )
        parser.add_argument(
            '--estacion',
            type=str,
            choices=['Verano', 'Otoño', 'Invierno', 'Primavera'],
            help='Estación específica (default: automática)'
        )
        parser.add_argument(
            '--sin-estacion',
            action='store_true',
            help='No filtrar por estación (usar todos los datos)'
        )

    def handle(self, *args, **options):
        # Configuración
        usar_conservadora = options['formula'] == 'conservadora'
        estacion_manual = options.get('estacion')
        usar_estacion = not options['sin_estacion']

        # Mostrar configuración
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS("CÁLCULO DE STOCK CRÍTICO CON ML"))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f"Fórmula: {'Conservadora (7d + 2.5σ)' if usar_conservadora else 'Estándar (ROP)'}")
        self.stdout.write(f"Filtrar por estación: {'Sí' if usar_estacion else 'No'}")

        if estacion_manual:
            self.stdout.write(f"Estación manual: {estacion_manual}")
        elif usar_estacion:
            estacion = detectar_estacion_actual()
            self.stdout.write(f"Estación detectada: {estacion}")

        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Ejecutar cálculo
        self.stdout.write("Iniciando cálculo desde base de datos...")
        self.stdout.write("")

        try:
            resultados = ejecutar_calculo_global(
                usar_formula_conservadora=usar_conservadora,
                usar_estacion=usar_estacion
            )

            # Resumen de resultados
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS("RESUMEN DE RESULTADOS"))
            self.stdout.write(self.style.SUCCESS('=' * 60))

            if resultados:
                self.stdout.write(f"✓ {len(resultados)} materiales procesados exitosamente")

                # Distribución por rangos
                rangos = {'1-10': 0, '11-30': 0, '31-60': 0, '61+': 0}
                for r in resultados:
                    stock = r.stock_min_calculado
                    if stock <= 10:
                        rangos['1-10'] += 1
                    elif stock <= 30:
                        rangos['11-30'] += 1
                    elif stock <= 60:
                        rangos['31-60'] += 1
                    else:
                        rangos['61+'] += 1

                self.stdout.write("Distribución de stock crítico:")
                for rango, cantidad in rangos.items():
                    if cantidad > 0:
                        self.stdout.write(f"  {rango}: {cantidad} materiales")

                # Ejemplos
                self.stdout.write("Primeros 3 ejemplos:")
                for i, resultado in enumerate(resultados[:3], 1):
                    self.stdout.write(
                        f"  {i}. {resultado.material.codigo}: "
                        f"{resultado.stock_min_calculado} "
                        f"(demanda: {resultado.demanda_promedio:.1f}, "
                        f"σ: {resultado.desviacion:.1f})"
                    )
            else:
                self.stdout.write(self.style.WARNING("No se procesaron materiales"))

            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("✓ Cálculo completado exitosamente!"))
            self.stdout.write(self.style.SUCCESS("Dashboard: http://localhost:8000/prediccion-stock/"))

        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Error de importación: {str(e)}"
                    "Verifica que exista: inventario/services/ml_service_mejorado.py"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))