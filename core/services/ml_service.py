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

def detectar_estacion_por_mes(mes: int) -> str:
    """Retorna la estación dado un número de mes (1-12)"""
    if mes in (12, 1, 2):
        return "Verano"
    if mes in (3, 4, 5):
        return "Otoño"
    if mes in (6, 7, 8):
        return "Invierno"
    return "Primavera"

def detectar_estacion_actual() -> str:
    return detectar_estacion_por_mes(datetime.now().month)

def es_material_critico(codigo: str) -> bool:
    """
    Determina si un material es crítico basado en su código.
    Materiales críticos: GAS-*, CAB-*, COMP-*
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
        
        # Aquí está la corrección clave: Si viene manual, úsala. Si no, detecta.
        if estacion_manual:
            self.estacion = estacion_manual
        else:
            self.estacion = detectar_estacion_actual()

    def obtener_demanda_historica(self):
        fecha_inicio = timezone.now() - timedelta(days=self.dias_historial)

        # Fuente 1: Demanda desde solicitudes aprobadas
        demanda_solicitudes = DetalleSolicitud.objects.filter(
            material=self.material,
            solicitud__estado__in=['aprobada'],
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

        # Filtrar por meses de la estación configurada en self.estacion
        meses_estacion = obtener_meses_por_estacion(self.estacion)
        df_estacion = df_demanda[df_demanda['mes'].isin(meses_estacion)]

        return df_estacion

    def calcular_factor_estacional(self, df_demanda):
        if df_demanda.empty or len(df_demanda) < 30:
            return 1.0 

        df_demanda['mes'] = pd.to_datetime(df_demanda['fecha_corta']).dt.month
        demanda_por_mes = df_demanda.groupby('mes')['cantidad_diaria'].mean()

        if demanda_por_mes.empty:
            return 1.0

        # Si estamos forzando una estación manual, tomamos el promedio de los meses de ESA estación
        meses_estacion = obtener_meses_por_estacion(self.estacion)
        # Tomamos el primer mes de esa estación como referencia para el factor (o el promedio de ellos)
        mes_referencia = meses_estacion[0] if meses_estacion else timezone.now().month
        
        demanda_mes_referencia = demanda_por_mes.get(mes_referencia, demanda_por_mes.mean())
        factor_estacional = demanda_mes_referencia / demanda_por_mes.mean()

        return max(0.5, min(2.5, factor_estacional))

    def estimar_leadtime(self):
        if es_material_critico(self.material.codigo):
            return 14 
        return 7 

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
        try:
            # 1. Obtener demanda histórica
            if usar_estacion:
                df_demanda = self.obtener_demanda_por_estacion()
                logger.info(f"Analizando {self.material.codigo} para estación FORZADA: {self.estacion}")
            else:
                df_demanda = self.obtener_demanda_historica()

            demanda_promedio = 0.0
            desviacion = 0.0
            coeficiente_variacion = 0.0
            stock_seguridad_valor = 0.0
            metodo = "Desconocido"

            # 3. Validar datos (Ahora permitimos calcular aunque sea con pocos datos si es simulación)
            if df_demanda.empty:
                # Si no hay datos en esa estación específica, intentamos obtener un promedio general y aplicar factor
                logger.warning(f"Sin datos históricos para {self.estacion} en {self.material.codigo}. Usando general con factor.")
                df_general = self.obtener_demanda_historica()
                
                if not df_general.empty:
                     # Usamos datos generales pero aplicamos un factor manual según la estación teórica
                     demanda_promedio = float(df_general['cantidad_diaria'].mean())
                     desviacion = float(df_general['cantidad_diaria'].std())
                     if pd.isna(desviacion): desviacion = demanda_promedio * 0.3
                     
                     # Ajuste manual simple: Invierno consume más gas, Verano menos (ejemplo)
                     # Aquí podrías poner lógica de negocio específica. Por ahora mantenemos el promedio.
                     metodo = f"Promedio General (Sin datos {self.estacion})"
                else:
                     # Sin datos absolutos
                     demanda_promedio = 5.0
                     desviacion = 2.0
                     metodo = "Por defecto (Sin historia)"
                
                stock_min_calculado = 20 # Valor base seguro
                leadtime_dias = self.estimar_leadtime()

            else:
                # Calcular métricas estadísticas reales de la estación filtrada
                demanda_promedio = float(df_demanda['cantidad_diaria'].mean())
                desviacion = float(df_demanda['cantidad_diaria'].std())

                if pd.isna(desviacion) or desviacion == 0:
                    desviacion = demanda_promedio * 0.3 
                
                coeficiente_variacion = (desviacion / demanda_promedio) if demanda_promedio > 0 else 0.0

                if not usar_estacion:
                    factor_estacional = self.calcular_factor_estacional(df_demanda)
                    demanda_promedio *= factor_estacional

                leadtime_dias = self.estimar_leadtime()

                if usar_formula_conservadora:
                    stock_min_calculado = self.calcular_con_formula_conservadora(demanda_promedio, desviacion)
                    stock_seguridad_valor = desviacion * 2.5
                    metodo = f"Conservadora ({self.estacion})"
                else:
                    stock_min_calculado = self.calcular_con_formula_estandar(demanda_promedio, desviacion, leadtime_dias)
                    stock_seguridad_valor = self.z_score * desviacion * np.sqrt(leadtime_dias)
                    metodo = f"Estándar ROP ({self.estacion})"

            # 5. Aplicar piso mínimo
            if es_material_critico(self.material.codigo):
                stock_min_calculado = max(stock_min_calculado, 10)
            else:
                stock_min_calculado = max(stock_min_calculado, 1)

            desc_modelo = f"F:{'Cons' if usar_formula_conservadora else 'Std'} | Est:{self.estacion}"

            resultado = MLResult.objects.create(
                material=self.material,
                demanda_promedio=round(demanda_promedio, 2),
                desviacion=round(desviacion, 2),
                leadtime_dias=leadtime_dias,
                stock_min_calculado=stock_min_calculado,
                version_modelo=desc_modelo,
                fecha_calculo=timezone.now(),
                stock_seguridad=round(stock_seguridad_valor, 2),
                coeficiente_variacion=round(coeficiente_variacion, 2),
                metodo_utilizado=metodo 
            )

            try:
                inventario = self.material.inventario
                inventario.stock_seguridad = stock_min_calculado
                inventario.save(update_fields=['stock_seguridad'])
            except Inventario.DoesNotExist:
                pass

            return resultado

        except Exception as e:
            logger.error(f"Error calculando stock crítico para {self.material.codigo}: {str(e)}")
            return None


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
    
    if estacion_manual:
        estacion_final = estacion_manual
    elif usar_estacion:
        estacion_final = detectar_estacion_actual()
    else:
        estacion_final = None

    logger.info("========== INICIANDO CÁLCULO ML ==========")
    logger.info(f"Estación Activa: {estacion_final or 'Promedio Global'}")

    for material in materiales:
        try:
            calculator = StockCriticoCalculatorMejorado(
                material=material,
                dias_historial=dias_historial,
                nivel_servicio=nivel_servicio,
                estacion_manual=estacion_final,  
            )

            resultado = calculator.calcular_stock_critico(
                usar_formula_conservadora=usar_formula_conservadora,
                usar_estacion=usar_estacion, 
            )

            if resultado:
                resultados.append(resultado)
        except Exception as e:
            errores += 1

    return resultados
