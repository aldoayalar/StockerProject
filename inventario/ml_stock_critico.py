import pandas as pd
import numpy as np
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, StdDev
from django.db.models.functions import TruncDate
from sklearn.linear_model import LinearRegression
from ..core.models import Material, DetalleSolicitud, MLResult, Inventario, Movimiento
import logging

logger = logging.getLogger(__name__)

class StockCriticoCalculator:
    """
    Calcula el stock crítico dinámico basado en:
    - Demanda histórica
    - Estacionalidad
    - Lead time (tiempo de reposición)
    - Variabilidad de la demanda
    """
    
    def __init__(self, material, dias_historial=180, nivel_servicio=0.95,
                 usar_estacion=True, estacion_manual=None):
        self.material = material
        self.dias_historial = dias_historial
        self.nivel_servicio = nivel_servicio
        self.z_score = 1.65
        self.usar_estacion = usar_estacion
        self.estacion_manual = estacion_manual
        
    def obtener_demanda_historica(self):
        """
        Obtiene el historial de demanda del material
        """
        fecha_inicio = timezone.now() - timedelta(days=self.dias_historial)
        
        # Demanda desde solicitudes aprobadas
        demanda_solicitudes = DetalleSolicitud.objects.filter(
            material=self.material,
            solicitud__estado__in=['aprobada', 'despachada'],
            solicitud__fecha_solicitud__gte=fecha_inicio
        ).annotate(
            fecha=TruncDate('solicitud__fecha_solicitud')
        ).values('fecha').annotate(
            cantidad_diaria=Sum('cantidad')
        ).order_by('fecha')
        
        # Demanda desde movimientos de salida
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
    
    def calcular_estacionalidad(self, df_demanda):
        """
        Detecta patrones estacionales en la demanda
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
        
        return max(0.5, min(2.0, factor_estacional))  # Limitar entre 0.5x y 2x
    
    def estimar_leadtime(self):
        """
        Estima el tiempo de reposición en días
        Por defecto usa 7 días, pero puede ajustarse según histórico
        """
        # Aquí podrías calcular el lead time real desde compras
        # Por ahora usamos un valor por defecto
        return 7  # días
    
    def calcular_stock_critico(self):
        """
        Calcula el stock crítico usando la fórmula:
        Stock_Critico = (Demanda_Promedio * Lead_Time) + (Z * Desviacion * √Lead_Time)
        """
        try:
            df_demanda = self.obtener_demanda_historica()
            
            if df_demanda.empty or len(df_demanda) < 7:
                logger.warning(f"Datos insuficientes para {self.material.codigo}. Usando valores por defecto.")
                # Valores por defecto si no hay suficiente historial
                demanda_promedio = 5.0
                desviacion = 2.0
                leadtime_dias = 7
            else:
                # Calcular métricas básicas
                demanda_promedio = df_demanda['cantidad_diaria'].mean()
                desviacion = df_demanda['cantidad_diaria'].std()
                
                # Ajustar por estacionalidad
                factor_estacional = self.calcular_estacionalidad(df_demanda)
                demanda_promedio *= factor_estacional
                
                # Lead time
                leadtime_dias = self.estimar_leadtime()
            
            # Fórmula del stock crítico (Reorder Point)
            # ROP = (Demanda diaria promedio × Lead time) + Stock de seguridad
            # Stock de seguridad = Z × Desviación × √Lead time
            
            stock_seguridad = self.z_score * desviacion * np.sqrt(leadtime_dias)
            stock_minimo = (demanda_promedio * leadtime_dias) + stock_seguridad
            
            # Redondear al entero más cercano
            stock_min_calculado = max(1, int(np.ceil(stock_minimo)))
            
            # Guardar resultado
            resultado = MLResult.objects.create(
                material=self.material,
                demanda_promedio=round(demanda_promedio, 2),
                desviacion=round(desviacion, 2),
                leadtime_dias=leadtime_dias,
                stock_min_calculado=stock_min_calculado,
                version_modelo='v1.0'
            )
            
            # Actualizar el inventario
            try:
                inventario = self.material.inventario
                inventario.stock_min_dinamico = stock_min_calculado
                inventario.save()
                logger.info(f"Stock crítico actualizado para {self.material.codigo}: {stock_min_calculado}")
            except Inventario.DoesNotExist:
                logger.warning(f"No existe inventario para {self.material.codigo}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error calculando stock crítico para {self.material.codigo}: {str(e)}")
            return None


def ejecutar_calculo_global(usar_estacion=True, estacion_manual=None):
    """
    Ejecuta el cálculo de stock crítico para todos los materiales activos.

    usar_estacion:
        - True  → aplica ajuste estacional
        - False → ignora estación (usa promedio general)

    estacion_manual:
        - None       → detecta estación actual automáticamente
        - 'Verano', 'Otoño', 'Invierno', 'Primavera'
    """
    materiales = Material.objects.filter(inventario__isnull=False)
    resultados = []

    for material in materiales:
        calculator = StockCriticoCalculator(
            material,
            usar_estacion=usar_estacion,
            estacion_manual=estacion_manual,
        )
        resultado = calculator.calcular_stock_critico()
        if resultado:
            resultados.append(resultado)

    logger.info(f"Cálculo completado. {len(resultados)} materiales procesados.")
    return resultados
