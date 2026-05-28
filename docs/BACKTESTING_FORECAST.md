# Backtesting del forecast Pulse

Fecha de corte: 2026-05-28.

El forecast visible del dashboard usa el ICIV Pulse mensual como serie de alta
frecuencia. Para que la prediccion sea defendible, el proyecto ya incluye
backtesting rolling-origin: el modelo se entrena solo con informacion disponible
hasta un mes `t` y se evalua contra meses posteriores ya observados.

## Artefactos implementados

```text
iciv/scripts/backtest_pulse_forecast.py
iciv/src/iciv/ml/pulse_backtest.py
iciv/data/processed/pulse_forecast_backtest.csv
iciv/data/processed/pulse_forecast_backtest_summary.csv
```

El pipeline tambien ejecuta el backtesting durante `python main.py --no-fetch
--no-open` y muestra el resumen en la seccion `Prediccion Pulse`.

## Metodo

1. Ordena la serie Pulse mensual por fecha.
2. Usa por defecto solo meses con `cobertura_pct >= 70`.
3. Define una ventana inicial de 60 meses confiables.
4. Entrena con datos hasta el origen `t`.
5. Predice horizontes `t+1`, `t+3` y `t+6`.
6. Compara la prediccion contra el Pulse observado.
7. Avanza el origen y repite.

La evaluacion conserva la regla de oro del proyecto: no se inventan datos y no
se rellenan huecos para mejorar metricas.

## Modelos comparados

| Modelo | Uso |
|---|---|
| Naive | predice que el siguiente valor sera igual al ultimo observado |
| Seasonal naive | usa el mismo mes del ano anterior |
| ETS | suavizamiento exponencial clasico para series mensuales |
| SARIMA | modelo academico de series de tiempo usado para el forecast visible |

Para que el pipeline semanal sea sostenible, SARIMA se evalua en origenes
anuales dentro del rolling-origin. Los modelos base se evaluan en todos los
origenes. Si se quiere una auditoria mas pesada, ejecutar:

```bash
cd iciv
python scripts/backtest_pulse_forecast.py --sarima-origin-step-months 3
```

## Resultado actual

Ultima ejecucion local: 2026-05-28.

| Horizonte | Mejor modelo | MAE | RMSE |
|---:|---|---:|---:|
| 1 mes | SARIMA | 1.71 | 2.61 |
| 3 meses | Naive | 4.27 | 5.62 |
| 6 meses | SARIMA | 3.77 | 4.93 |

Interpretacion: SARIMA aporta valor en 1 y 6 meses, pero no domina todos los
horizontes. Eso es positivo metodologicamente porque el dashboard no vende el
modelo como infalible; muestra una comparacion fuera de muestra y permite
defender el forecast con evidencia.

## Columnas del archivo largo

```text
origin_date
target_date
horizon
model
model_spec
aic
y_true
y_pred
lower_80
upper_80
lower_95
upper_95
coverage_pct_target
absolute_error
squared_error
bias_error
inside_80
inside_95
```

## Criterio de defensa

El forecast queda defendible si:

- se reporta MAE/RMSE por horizonte;
- se compara contra naive, seasonal naive y ETS;
- se reconoce cuando un baseline simple gana;
- las bandas SARIMA se muestran como incertidumbre, no como certeza;
- los meses de baja cobertura quedan excluidos o etiquetados.

## Proximos pasos

1. Agregar backtesting visual historico con errores por fecha.
2. Evaluar una segunda corrida que incluya meses provisionales, etiquetada como
   sensibilidad.
3. Probar regresores exogenos solo si mejoran MAE/RMSE fuera de muestra.
4. Versionar el resultado de backtesting por release metodologico.
