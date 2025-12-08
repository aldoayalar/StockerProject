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
    
    meses_map = {
        'Verano': [12, 1, 2],
        'Otoño': [3, 4, 5],
        'Invierno': [6, 7, 8],
        'Primavera': [9, 10, 11],
    }
    return meses_map.get(estacion, [])


# ==================== CALCULADORA DE STOCK CRÍTICO ====================

class StockCriticoCalculatorMejorado:

    def __init__(self, material, dias_historial=180, nivel_servicio=0.95, estacion_manual=None):
        self.material = material
        self.dias_historial = dias_historial
        self.nivel_servicio = nivel_servicio
        self.z_score = 1.65  # Para 95% de nivel de servicio
        self.estacion = estacion_manual or detectar_estacion_actual()

    def obtener_demanda_historica(self):
       
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
       
        if es_material_critico(self.material.codigo):
            return 14  # Lead time más largo para materiales críticos
        return 7  # Lead time estándar

    def calcular_con_formula_estandar(self, demanda_promedio, desviacion, leadtime_dias):
        
        stock_seguridad = self.z_score * desviacion * np.sqrt(leadtime_dias)
        stock_critico = (demanda_promedio * leadtime_dias) + stock_seguridad
        return int(np.ceil(stock_critico))

    def calcular_con_formula_conservadora(self, promedio_diario, desviacion):
      
        cobertura_semanal = promedio_diario * 7
        factor_seguridad = desviacion * 2.5
        stock_critico = cobertura_semanal + factor_seguridad
        return int(np.ceil(stock_critico))

    def calcular_stock_critico(self, usar_formula_conservadora=False, usar_estacion=True):
        """
        Calcula el stock crítico usando el algoritmo seleccionado.
        Retorna un objeto MLResult con el resultado detallado.
        """
        try:
            # 1. Obtener demanda histórica
            if usar_estacion:
                df_demanda = self.obtener_demanda_por_estacion()
                logger.info(f"Analizando {self.material.codigo} para estación: {self.estacion}")
            else:
                df_demanda = self.obtener_demanda_historica()

            # 2. Inicializar variables por defecto
            demanda_promedio = 0.0
            desviacion = 0.0
            coeficiente_variacion = 0.0
            stock_seguridad_valor = 0.0
            metodo = "Desconocido"

            # 3. Validar si hay datos suficientes (mínimo 7 días con movimientos)
            if df_demanda.empty or len(df_demanda) < 7:
                logger.warning(
                    f"Datos insuficientes para {self.material.codigo}. "
                    f"Registros: {len(df_demanda)}. Usando valores por defecto."
                )
                # Valores por defecto de emergencia
                demanda_promedio = 5.0
                desviacion = 2.0
                leadtime_dias = self.estimar_leadtime()
                stock_min_calculado = 20
                metodo = "Por defecto (Sin datos)"
            else:
                # Calcular métricas estadísticas reales
                demanda_promedio = float(df_demanda['cantidad_diaria'].mean())
                desviacion = float(df_demanda['cantidad_diaria'].std())

                # Manejar caso de desviación nula o NaN
                if pd.isna(desviacion) or desviacion == 0:
                    desviacion = demanda_promedio * 0.3  # Asumir 30% si no hay variabilidad
                
                # Calcular Coeficiente de Variación (CV)
                coeficiente_variacion = (desviacion / demanda_promedio) if demanda_promedio > 0 else 0.0

                # Ajustar por estacionalidad (si NO se usó filtro de estación, aplicamos factor manual)
                if not usar_estacion:
                    factor_estacional = self.calcular_factor_estacional(df_demanda)
                    demanda_promedio *= factor_estacional
                    logger.info(f"Factor estacional aplicado: {factor_estacional:.2f}")

                # Obtener lead time
                leadtime_dias = self.estimar_leadtime()

                # 4. Calcular stock crítico según fórmula seleccionada
                if usar_formula_conservadora:
                    # Fórmula: (Promedio * 7) + (Desviacion * 2.5)
                    # Aquí el "Stock de seguridad" es implícitamente todo el término de desviación + el exceso de días (7 vs leadtime real)
                    # Para simplificar el reporte, asumimos que el componente de seguridad es (Desviacion * 2.5)
                    stock_min_calculado = self.calcular_con_formula_conservadora(demanda_promedio, desviacion)
                    stock_seguridad_valor = desviacion * 2.5
                    metodo = "Conservadora (7d + 2.5σ)"
                    logger.info("Usando fórmula conservadora")
                else:
                    # Fórmula Estándar (ROP): (Promedio * LT) + (Z * Desviacion * sqrt(LT))
                    stock_min_calculado = self.calcular_con_formula_estandar(demanda_promedio, desviacion, leadtime_dias)
                    stock_seguridad_valor = self.z_score * desviacion * np.sqrt(leadtime_dias)
                    metodo = "Estándar ROP"
                    logger.info("Usando fórmula estándar")

            # 5. Aplicar piso mínimo para materiales críticos
            if es_material_critico(self.material.codigo):
                stock_min_calculado = max(stock_min_calculado, 10)
            else:
                stock_min_calculado = max(stock_min_calculado, 1)

            # 6. Construir string descriptivo de los parámetros usados
            desc_modelo = f"F:{'Cons' if usar_formula_conservadora else 'Std'} | Hist:{self.dias_historial}d | Est:{self.estacion}"

            # 7. Guardar resultado en MLResult
            # Nota: Asegúrate de que tu modelo MLResult tenga los campos stock_seguridad y coeficiente_variacion.
            # Si no los has creado en models.py, comenta esas dos líneas abajo.
            resultado = MLResult.objects.create(
                material=self.material,
                demanda_promedio=round(demanda_promedio, 2),
                desviacion=round(desviacion, 2),
                leadtime_dias=leadtime_dias,
                stock_min_calculado=stock_min_calculado,
                version_modelo=desc_modelo,
                fecha_calculo=timezone.now(),
                
                # Campos nuevos (asegúrate de tenerlos en models.py o coméntalos)
                stock_seguridad=round(stock_seguridad_valor, 2),
                coeficiente_variacion=round(coeficiente_variacion, 2),
                metodo_utilizado=metodo 
            )

            # 8. Actualizar el inventario operativo (stock_seguridad / stock_minimo)
            try:
                inventario = self.material.inventario
                stock_anterior = inventario.stock_seguridad
                
                # Guardamos el cálculo como el nuevo stock de seguridad/mínimo del sistema
                inventario.stock_seguridad = stock_min_calculado
                inventario.save(update_fields=['stock_seguridad'])
                
                logger.info(f"✓ Stock actualizado para {self.material.codigo}: {stock_anterior} -> {stock_min_calculado}")
                
            except Inventario.DoesNotExist:
                logger.warning(f"No existe inventario para {self.material.codigo}")

            return resultado

        except Exception as e:
            logger.error(f"Error calculando stock crítico para {self.material.codigo}: {str(e)}")
            return None



# ==================== FUNCIONES DE ALTO NIVEL ====================

def ejecutar_calculo_global(
    usar_formula_conservadora: bool = True,
    usar_estacion: bool = True,
    estacion_manual: str | None = None,
    dias_historial: int = 180,
    nivel_servicio: float = 0.95,
):
   
    materiales = Material.objects.filter(inventario__isnull=False)
    resultados = []
    errores = 0

    count_deleted = MLResult.objects.all().delete()[0]
    logger.info(f"Limpieza previa: se eliminaron {count_deleted} resultados antiguos.")
    
    if usar_estacion:
        if estacion_manual:
            estacion = estacion_manual
        else:
            estacion = detectar_estacion_actual()
    else:
        estacion = None

    logger.info("========== INICIANDO CÁLCULO ML ==========")
    logger.info(f"Estación usada: {estacion or 'SIN ESTACIÓN'}")
    logger.info(
        "Fórmula: "
        f"{'Conservadora (7d + 2.5σ)' if usar_formula_conservadora else 'Estándar (ROP)'}"
    )
    logger.info(f"Días de historial: {dias_historial}")
    logger.info(f"Nivel de servicio: {nivel_servicio}")
    logger.info(f"Materiales a procesar: {materiales.count()}")
    logger.info("=" * 45)

    for material in materiales:
        try:
            calculator = StockCriticoCalculatorMejorado(
                material=material,
                dias_historial=dias_historial,
                nivel_servicio=nivel_servicio,
                estacion_manual=estacion,  # puede ser None
            )

            resultado = calculator.calcular_stock_critico(
                usar_formula_conservadora=usar_formula_conservadora,
                usar_estacion=usar_estacion,
            )

            if resultado:
                resultados.append(resultado)
        except Exception as e:
            logger.error(f"Error procesando {material.codigo}: {str(e)}")
            errores += 1

    logger.info("=" * 45)
    logger.info("✓ Cálculo completado.")
    logger.info(f"  - Materiales procesados: {len(resultados)}")
    logger.info(f"  - Errores: {errores}")
    logger.info("=" * 45)

    return resultados



def calcular_para_material(codigo_material, usar_formula_conservadora=True):
 
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