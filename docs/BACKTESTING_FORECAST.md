# Pronóstico y backtesting · v2

El producto público usa **persistencia (naive)**: cada horizonte conserva el último puntaje elegible. Es una predicción explícita y separada; nunca se introduce como observación ni se activa como sustitución silenciosa de SARIMA.

Las bandas 80% y 95% son cuantiles empíricos de errores absolutos históricos por horizonte, con mínimo 20 pares. No son garantía de cobertura futura ni probabilidades de riesgo económico. El origen puede preceder a los últimos meses provisionales; el gráfico debe conservar una única línea de tiempo y declarar ese origen.

La normalización mensual expansiva no utiliza extremos futuros. El calendario se conserva regular con NaN: eliminar un mes no convierte el mes siguiente en su vecino temporal. La elegibilidad requiere cobertura normalizable ≥70%, producción doméstica y mes cerrado.

Se comparan naive, naive estacional y SARIMA(1,1,1)×(1,1,1,12). SARIMA exige convergencia y parámetros finitos; se registran sus advertencias y fallos. Las métricas comparativas se calculan sobre los mismos pares origen/horizonte para todos los modelos. La tabla de disponibilidad separada permite observar cuánto se pierde por convergencia o falta de meses estacionales; no se deben mezclar los tamaños de muestra al elegir un ganador.

La evaluación se denomina `retrospective_latest_vintage`: no existen vintages históricos ni fechas de publicación completas para simular la información disponible en tiempo real. El desempeño no prueba capacidad de anticipar la economía o el índice anual.

Artefactos: `pulse_forecast_backtest.csv`, `pulse_forecast_backtest_summary.csv` (muestra común), `pulse_forecast_backtest_available_summary.csv`, `pulse_forecast_backtest_failures.csv` y `forecast.json`. Las cifras actualizadas se consultan allí, no en las presentaciones de avances.

Referencia: [Forecasting: Principles and Practice — evaluación temporal](https://otexts.com/fpp3/tscv.html).
