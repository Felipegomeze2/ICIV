# Robustez ampliada · revisión de trabajo

Generación UTC: 2026-09-18T01:19:04.064163+00:00. Escenarios: 79.

Alternativas deterministas sobre datos reales; no se generan ni rellenan observaciones. La dispersión entre diseños no es un intervalo de confianza. No se eligieron pesos para maximizar correlación con IED.

Se varían pesos dimensionales ±5/10/20%, normalización, agregación, transformación de inflación, piso de cobertura, exclusión de cada variable y dimensión, y ausencia de datos por dimensión. Se añade la retirada de estimaciones WEO verificadas cuando existe evidencia.

## Mayor diferencia respecto al modelo base

Muestra: años con cobertura base ≥80% y score disponible en ambos diseños. El CSV también muestra todos los años comparables. Comparar n: los pisos más estrictos pueden reducirlo.

| Escenario | n | MAE puntos | Máximo absoluto | Spearman | Cambios de categoría |
|---|---:|---:|---:|---:|---:|
| rank | 13 | 9.671 | 18.320 | 0.989 | 10 |
| geometrico | 13 | 5.718 | 22.760 | 0.978 | 6 |
| sin_datos_D1_macro | 13 | 5.161 | 13.190 | 0.945 | 6 |
| excluir_D1_macro | 13 | 5.161 | 13.190 | 0.945 | 6 |
| piso_100% | 13 | 3.598 | 7.180 | 0.967 | 2 |
| excluir_petroleo_crudo_produccion_tbpd | 13 | 3.557 | 7.180 | 0.984 | 2 |
| sin_datos_D2_energia | 13 | 3.557 | 7.180 | 0.984 | 2 |
| excluir_D2_energia | 13 | 3.557 | 7.180 | 0.984 | 2 |
| inflacion_sin_log | 13 | 3.075 | 5.860 | 0.962 | 0 |
| excluir_D3_institucional | 13 | 3.000 | 7.080 | 0.995 | 0 |
| sin_datos_D3_institucional | 13 | 3.000 | 7.080 | 0.995 | 0 |
| excluir_D4_comercial | 13 | 2.768 | 7.020 | 0.989 | 2 |
| sin_datos_D4_comercial | 13 | 2.768 | 7.020 | 0.989 | 2 |
| winsor05 | 13 | 2.547 | 5.790 | 0.995 | 3 |
| excluir_pib_crecimiento_real_pct | 13 | 2.308 | 3.560 | 0.967 | 3 |

## Composición interanual

La canasta común utiliza los mismos indicadores disponibles en ambos años, mantiene el universo de cobertura y aplica el piso dimensional. El residuo es el efecto neto de composición; no atribuye causas económicas.

| Año | Cambio publicado | Cambio canasta común | Residuo composición | Cobertura común % |
|---|---:|---:|---:|---:|
| 2020 | -9.40 | -9.40 | 0.00 | 95.1 |
| 2021 | 8.99 | 8.99 | 0.00 | 95.1 |
| 2022 | 6.17 | 6.17 | 0.00 | 95.1 |
| 2023 | -3.99 | -3.99 | 0.00 | 95.1 |
| 2024 | 0.32 | -0.31 | 0.63 | 92.6 |
| 2025 | -6.47 | -4.55 | -1.92 | 78.2 |
| 2026 | 14.95 | 3.36 | 11.59 | 41.1 |

Artefactos: `iciv/data/processed/robustness_summary.csv`, `robustness_scenarios.csv`, `annual_composition.csv` y `robustness_run.json`.

Referencia de protocolo: [OECD/JRC, Handbook on Constructing Composite Indicators (2008), análisis de incertidumbre y sensibilidad](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf). Las decisiones concretas y los umbrales son del proyecto; no son una certificación OECD.
