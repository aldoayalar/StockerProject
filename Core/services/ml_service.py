import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import TruncDate
import logging

from core.models import Material, DetalleSolicitud, Movimiento, MLResult, Inventario

logger = logging.getLogger(__name__)


# ==================== UTILIDADES ====================

def detectar_estacion_actual() -> str:
    """
    Detecta la estación actual según el mes del sistema (hemisferio sur - Chile).

    - Verano: Diciembre, Enero, Febrero
    - Otoño: Marzo, Abril, Mayo
    - Invierno: Junio, Julio, Agosto
    - Primavera: Septiembre, Octubre, Noviembre
    """
    mes = datetime.now().month
    if mes in (12, 1, 2):
        return "Verano"
    if mes in (3, 4, 5):
        return "Otoño"
    if mes in (6, 7, 8):
        return "Invierno"
    return "Primavera"


def es_material_critico(codigo: str) -> bool:
    """
    Determina si un material es crítico basado en su código.

    Materiales críticos:
    - GAS-*: Gases refrigerantes
    - CAB-*: Cables
    - COMP-*: Compresores

    Estos materiales tienen un piso mínimo de stock mayor.
    """
    codigo_upper = codigo.upper()
    return codigo_upper.startswith("GAS") or codigo_upper.startswith("CAB") or codigo_upper.startswith("COMP")


def obtener_meses_por_estacion(estacion: str) -> list:
    """Retorna los meses correspondientes a una estación."""
    meses_map = {
        'Verano': [12, 1, 2],
        'Otoño': [3, 4, 5],
        'Invierno': [6, 7, 8],
        'Primavera': [9, 10, 11],
    }
    return meses_map.get(estacion, [])


# ==================== CALCULADORA DE STOCK CRÍTICO ====================

class StockCriticoCalculatorMejorado:
    """
    Calculadora mejorada de stock crítico que combina:
    - Análisis de demanda histórica desde solicitudes y movimientos
    - Detección automática de estacionalidad
    - Clasificación de materiales críticos
    - Múltiples fórmulas de cálculo
    """

    def __init__(self, material, dias_historial=180, nivel_servicio=0.95, estacion_manual=None):
        self.material = material
        self.dias_historial = dias_historial
        self.nivel_servicio = nivel_servicio
        self.z_score = 1.65  # Para 95% de nivel de servicio
        self.estacion = estacion_manual or detectar_estacion_actual()

    def obtener_demanda_historica(self):
        """
        Obtiene el historial de demanda del material desde:
        1. DetalleSolicitud (solicitudes aprobadas/despachadas)
        2. Movimiento (salidas de inventario)

        Retorna un DataFrame con fecha y cantidad diaria.
        """
        fecha_inicio = timezone.now() - timedelta(days=self.dias_historial)

        # Fuente 1: Demanda desde solicitudes aprobadas
        demanda_solicitudes = DetalleSolicitud.objects.filter(
            material=self.material,
            solicitud__estado__in=['aprobada', 'despachada'],
            solicitud__fecha_solicitud__gte=fecha_inicio
        ).annotate(
            fecha=TruncDate('solicitud__fecha_solicitud')
        ).values('fecha').annotate(
            cantidad_diaria=Sum('cantidad')
        ).order_by('fecha')

        # Fuente 2: Demanda desde movimientos de salida
        demanda_movimientos = Movimiento.objects.filter(
            material=self.material,
            tipo='salida',
            fecha__gte=fecha_inicio
        ).annotate(
            fecha_corta=TruncDate('fecha')
        ).values('fecha_corta').annotate(
            cantidad_diaria=Sum('cantidad')
        ).order_by('fecha_corta')

        # Combinar ambas fuentes
        df_solicitudes = pd.DataFrame(list(demanda_solicitudes))
        df_movimientos = pd.DataFrame(list(demanda_movimientos))

        if not df_solicitudes.empty:
            df_solicitudes.rename(columns={'fecha': 'fecha_corta'}, inplace=True)

        # Unir datasets
        if not df_solicitudes.empty and not df_movimientos.empty:
            df_demanda = pd.concat([df_solicitudes, df_movimientos]).groupby('fecha_corta').sum().reset_index()
        elif not df_solicitudes.empty:
            df_demanda = df_solicitudes
        elif not df_movimientos.empty:
            df_demanda = df_movimientos
        else:
            return pd.DataFrame()

        return df_demanda

    def obtener_demanda_por_estacion(self):
        """
        Filtra la demanda histórica por la estación actual.
        Esto permite análisis estacional más preciso.
        """
        df_demanda = self.obtener_demanda_historica()

        if df_demanda.empty:
            return pd.DataFrame()

        # Agregar columna de mes
        df_demanda['mes'] = pd.to_datetime(df_demanda['fecha_corta']).dt.month

        # Filtrar por meses de la estación
        meses_estacion = obtener_meses_por_estacion(self.estacion)
        df_estacion = df_demanda[df_demanda['mes'].isin(meses_estacion)]

        return df_estacion

    def calcular_factor_estacional(self, df_demanda):
        """
        Calcula el factor de estacionalidad comparando la demanda 
        del mes actual vs el promedio histórico.
        """
        if df_demanda.empty or len(df_demanda) < 30:
            return 1.0  # Sin ajuste estacional

        df_demanda['mes'] = pd.to_datetime(df_demanda['fecha_corta']).dt.month
        demanda_por_mes = df_demanda.groupby('mes')['cantidad_diaria'].mean()

        if demanda_por_mes.empty:
            return 1.0

        mes_actual = timezone.now().month
        demanda_mes_actual = demanda_por_mes.get(mes_actual, demanda_por_mes.mean())
        factor_estacional = demanda_mes_actual / demanda_por_mes.mean()

        # Limitar entre 0.5x y 2.5x para evitar valores extremos
        return max(0.5, min(2.5, factor_estacional))

    def estimar_leadtime(self):
        """
        Estima el tiempo de reposición en días.

        Valores por defecto según tipo de material:
        - Materiales críticos (GAS, CAB, COMP): 14 días
        - Materiales normales: 7 días

        TODO: Implementar cálculo real desde histórico de compras/reposiciones.
        """
        if es_material_critico(self.material.codigo):
            return 14  # Lead time más largo para materiales críticos
        return 7  # Lead time estándar

    def calcular_con_formula_estandar(self, demanda_promedio, desviacion, leadtime_dias):
        """
        Fórmula estándar de Reorder Point (ROP):

        Stock_Crítico = (Demanda_Promedio × Lead_Time) + (Z × Desviación × √Lead_Time)

        Donde Z = 1.65 para 95% de nivel de servicio.
        """
        stock_seguridad = self.z_score * desviacion * np.sqrt(leadtime_dias)
        stock_critico = (demanda_promedio * leadtime_dias) + stock_seguridad
        return int(np.ceil(stock_critico))

    def calcular_con_formula_conservadora(self, promedio_diario, desviacion):
        """
        Fórmula conservadora (del otro proyecto):

        Stock_Crítico = (Promedio_Diario x 7 días) + (Desviación x 2.5)

        Proporciona mayor cobertura (1 semana) con factor de seguridad amplio.
        """
        cobertura_semanal = promedio_diario * 7
        factor_seguridad = desviacion * 2.5
        stock_critico = cobertura_semanal + factor_seguridad
        return int(np.ceil(stock_critico))

    def calcular_stock_critico(self, usar_formula_conservadora=False, usar_estacion=True):
        """
        Calcula el stock crítico usando el algoritmo seleccionado.

        Parámetros:
        - usar_formula_conservadora: Si True, usa la fórmula conservadora (7 días + 2.5)
        - usar_estacion: Si True, filtra datos por estación del año

        Retorna:
        - Objeto MLResult con el resultado del cálculo
        """
        try:
            # Obtener demanda histórica
            if usar_estacion:
                df_demanda = self.obtener_demanda_por_estacion()
                logger.info(f"Analizando {self.material.codigo} para estación: {self.estacion}")
            else:
                df_demanda = self.obtener_demanda_historica()

            # Validar datos suficientes
            if df_demanda.empty or len(df_demanda) < 7:
                logger.warning(
                    f"Datos insuficientes para {self.material.codigo}. "
                    f"Registros: {len(df_demanda)}. Usando valores por defecto."
                )
                # Valores por defecto conservadores
                demanda_promedio = 5.0
                desviacion = 2.0
                leadtime_dias = self.estimar_leadtime()
                stock_min_calculado = 20  # Valor mínimo por defecto
            else:
                # Calcular métricas estadísticas
                demanda_promedio = float(df_demanda['cantidad_diaria'].mean())
                desviacion = float(df_demanda['cantidad_diaria'].std())

                # Manejar caso de desviación nula
                if pd.isna(desviacion) or desviacion == 0:
                    desviacion = demanda_promedio * 0.3  # 30% de la demanda promedio

                # Ajustar por estacionalidad
                if not usar_estacion:
                    factor_estacional = self.calcular_factor_estacional(df_demanda)
                    demanda_promedio *= factor_estacional
                    logger.info(f"Factor estacional aplicado: {factor_estacional:.2f}")

                # Obtener lead time
                leadtime_dias = self.estimar_leadtime()

                # Calcular stock crítico según fórmula seleccionada
                if usar_formula_conservadora:
                    stock_min_calculado = self.calcular_con_formula_conservadora(
                        demanda_promedio, desviacion
                    )
                    logger.info(f"Usando fórmula conservadora (7 días + 2.5)")
                else:
                    stock_min_calculado = self.calcular_con_formula_estandar(
                        demanda_promedio, desviacion, leadtime_dias
                    )
                    logger.info(f"Usando fórmula estándar (ROP)")

            # Aplicar piso mínimo para materiales críticos
            if es_material_critico(self.material.codigo):
                stock_min_calculado = max(stock_min_calculado, 10)
                logger.info(f"{self.material.codigo} es crítico. Piso mínimo: 10 unidades")
            else:
                stock_min_calculado = max(stock_min_calculado, 1)

            # Guardar resultado en MLResult
            resultado = MLResult.objects.create(
                material=self.material,
                demanda_promedio=round(demanda_promedio, 2),
                desviacion=round(desviacion, 2),
                leadtime_dias=leadtime_dias,
                stock_min_calculado=stock_min_calculado,
                version_modelo='v2.0-mejorado'
            )

            # Actualizar el inventario con validación
            try:
                inventario = self.material.inventario
                stock_anterior = inventario.stock_seguridad

                # Actualizar stock_seguridad con el valor calculado
                inventario.stock_seguridad = stock_min_calculado
                inventario.save(update_fields=['stock_seguridad'])

                # Verificar que se guardó correctamente
                inventario.refresh_from_db()
                if inventario.stock_seguridad == stock_min_calculado:
                    logger.info(
                        f"✓ Stock crítico actualizado para {self.material.codigo}: "
                        f"{stock_anterior} → {stock_min_calculado}"
                    )
                else:
                    logger.error(
                        f"✗ Error de verificación para {self.material.codigo}. "
                        f"Esperado: {stock_min_calculado}, Guardado: {inventario.stock_seguridad}"
                    )
            except Inventario.DoesNotExist:
                logger.warning(f"No existe inventario para {self.material.codigo}")

            return resultado

        except Exception as e:
            logger.error(f"Error calculando stock crítico para {self.material.codigo}: {str(e)}")
            return None


# ==================== FUNCIONES DE ALTO NIVEL ====================

def ejecutar_calculo_global(usar_formula_conservadora=True, usar_estacion=True):
    """
    Ejecuta el cálculo de stock crítico para todos los materiales activos.

    Parámetros:
    - usar_formula_conservadora: Si True, usa fórmula conservadora (recomendado)
    - usar_estacion: Si True, filtra por estación actual (recomendado)

    Retorna:
    - Lista de resultados MLResult
    """
    materiales = Material.objects.filter(inventario__isnull=False)
    resultados = []
    errores = 0

    estacion = detectar_estacion_actual()
    logger.info(f"========== INICIANDO CÁLCULO ML ==========")
    logger.info(f"Estación detectada: {estacion}")
    logger.info(f"Fórmula: {'Conservadora (7d + 2.5)' if usar_formula_conservadora else 'Estándar (ROP)'}")
    logger.info(f"Materiales a procesar: {materiales.count()}")
    logger.info("=" * 45)

    for material in materiales:
        try:
            calculator = StockCriticoCalculatorMejorado(
                material, 
                dias_historial=180,
                estacion_manual=estacion if usar_estacion else None
            )
            resultado = calculator.calcular_stock_critico(
                usar_formula_conservadora=usar_formula_conservadora,
                usar_estacion=usar_estacion
            )

            if resultado:
                resultados.append(resultado)
        except Exception as e:
            logger.error(f"Error procesando {material.codigo}: {str(e)}")
            errores += 1

    logger.info("=" * 45)
    logger.info(f"✓ Cálculo completado.")
    logger.info(f"  - Materiales procesados: {len(resultados)}")
    logger.info(f"  - Errores: {errores}")
    logger.info("=" * 45)

    return resultados


def calcular_para_material(codigo_material, usar_formula_conservadora=True):
    """
    Calcula el stock crítico para un material específico.

    Útil para recálculos individuales o pruebas.
    """
    try:
        material = Material.objects.get(codigo=codigo_material)
        calculator = StockCriticoCalculatorMejorado(material)
        resultado = calculator.calcular_stock_critico(
            usar_formula_conservadora=usar_formula_conservadora
        )
        return resultado
    except Material.DoesNotExist:
        logger.error(f"Material {codigo_material} no encontrado")
        return None