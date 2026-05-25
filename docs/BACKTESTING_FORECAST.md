# Backtesting del forecast Pulse

Fecha de corte: 2026-05-25.

El forecast visible del dashboard es una prediccion SARIMA a seis meses sobre el
ICIV Pulse mensual. Para defenderlo mejor, el siguiente paso metodologico es
probar que ese modelo mejora frente a baselines simples fuera de muestra.

## Objetivo

Evaluar si el modelo SARIMA tiene capacidad predictiva real sobre meses que ya
ocurrieron, sin mirar el futuro durante el entrenamiento.

## Metodo recomendado

Usar backtesting rolling-origin:

1. Ordenar la serie Pulse mensual por fecha.
2. Filtrar o marcar observaciones con cobertura baja.
3. Elegir una ventana inicial minima, por ejemplo 36 meses confiables.
4. Entrenar el modelo con datos hasta el mes `t`.
5. Predecir `t+1`, `t+3` y `t+6`.
6. Comparar la prediccion contra el valor observado.
7. Mover el origen un mes hacia adelante y repetir.

## Modelos a comparar

| Modelo | Razon |
|---|---|
| Naive | predice que el siguiente mes sera igual al ultimo observado |
| Seasonal naive | predice igual al mismo mes del ano anterior |
| ETS / Exponential Smoothing | baseline clasico para series mensuales |
| SARIMA actual | modelo publicado en el dashboard |

SARIMA solo gana puntos si mejora fuera de muestra contra estos baselines.

## Metricas minimas

| Metrica | Uso |
|---|---|
| MAE | error medio absoluto, facil de explicar |
| RMSE | castiga errores grandes |
| MAPE o sMAPE | opcional; cuidado si el denominador se acerca a cero |
| Coverage 80/95 | porcentaje de valores observados que caen dentro de bandas |
| Bias medio | detecta si el modelo tiende a sobreestimar o subestimar |

## Tratamiento de cobertura

Recomendacion defendible:

- Entrenar el modelo principal solo con meses de cobertura confiable.
- Mantener una evaluacion secundaria con todos los meses, pero etiquetada como
  `incluye meses provisionales`.
- No imputar meses faltantes salvo gaps internos pequenos y documentados.

## Artefacto esperado

Crear un script:

```text
iciv/scripts/backtest_pulse_forecast.py
```

Salidas:

```text
iciv/data/processed/pulse_forecast_backtest.csv
iciv/data/processed/pulse_forecast_backtest_summary.csv
```

Columnas sugeridas del archivo largo:

```text
origin_date
target_date
horizon
model
y_true
y_pred
lower_80
upper_80
lower_95
upper_95
coverage_pct_target
absolute_error
squared_error
inside_80
inside_95
```

## Como mostrarlo en defensa

No hace falta meter otra pestana grande. Basta con una tarjeta dentro de
`Prediccion Pulse`:

- Mejor modelo por MAE.
- MAE SARIMA vs naive.
- Cobertura real de intervalos.
- Nota sobre meses provisionales.

Si SARIMA no gana, se debe decir y usar el baseline ganador. Eso no debilita el
proyecto; al contrario, muestra disciplina metodologica.

## Criterio de aprobacion

El forecast queda defendible si:

- SARIMA supera naive o seasonal naive en MAE/RMSE, o
- se conserva como baseline academico pero el dashboard reconoce que no supera
  al modelo simple, y
- las bandas tienen cobertura empirica razonable.
