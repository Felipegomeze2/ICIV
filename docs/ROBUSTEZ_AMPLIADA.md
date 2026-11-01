# Robustez ampliada · revisión de trabajo

Documento generado automáticamente por `iciv/scripts/robustness_review.py`.

Generación UTC: 2026-11-01T15:11:36.583622+00:00. Escenarios: 79.

Alternativas deterministas sobre datos reales; no se generan ni rellenan observaciones. La dispersión entre diseños no es un intervalo de confianza. No se eligieron pesos para maximizar correlación con IED.

Se varían pesos dimensionales ±5/10/20%, normalización, agregación, transformación de inflación, piso de cobertura, exclusión de cada variable y dimensión, y ausencia de datos por dimensión. Se añade la retirada de estimaciones WEO verificadas cuando existe evidencia.

## Mayor diferencia respecto al modelo base

Muestra: años con cobertura base ≥80% y score disponible en ambos diseños. El CSV también muestra todos los años comparables. Comparar n: los pisos más estrictos pueden reducirlo.

| Escenario | n | MAE puntos | Máximo absoluto | Spearman | Cambios de categoría |
|---|---:|---:|---:|---:|---:|
| rank | 14 | 9.474 | 18.070 | 0.982 | 9 |
| geometrico | 14 | 6.096 | 20.580 | 0.978 | 5 |
| sin_datos_D1_macro | 14 | 5.941 | 13.860 | 0.947 | 4 |
| excluir_D1_macro | 14 | 5.941 | 13.860 | 0.947 | 4 |
| sin_datos_D4_comercial | 14 | 3.345 | 6.990 | 0.969 | 5 |
| excluir_D4_comercial | 14 | 3.345 | 6.990 | 0.969 | 5 |
| sin_datos_D2_energia | 14 | 3.340 | 6.700 | 0.987 | 2 |
| excluir_petroleo_crudo_produccion_tbpd | 14 | 3.340 | 6.700 | 0.987 | 2 |
| excluir_D2_energia | 14 | 3.340 | 6.700 | 0.987 | 2 |
| piso_100% | 14 | 3.311 | 6.700 | 0.969 | 2 |
| inflacion_sin_log | 14 | 3.131 | 5.850 | 0.974 | 2 |
| excluir_D3_institucional | 14 | 2.993 | 6.640 | 0.996 | 2 |
| sin_datos_D3_institucional | 14 | 2.993 | 6.640 | 0.996 | 2 |
| winsor05 | 14 | 2.924 | 5.910 | 0.987 | 5 |
| excluir_pib_crecimiento_real_pct | 14 | 2.419 | 3.730 | 0.987 | 3 |

## Composición interanual

La canasta común utiliza los mismos indicadores disponibles en ambos años, mantiene el universo de cobertura y aplica el piso dimensional. El residuo es el efecto neto de composición; no atribuye causas económicas.

| Año | Cambio publicado | Cambio canasta común | Residuo composición | Cobertura común % |
|---|---:|---:|---:|---:|
| 2020 | -11.69 | -11.69 | 0.00 | 95.1 |
| 2021 | 9.13 | 9.13 | 0.00 | 95.1 |
| 2022 | 6.23 | 6.23 | 0.00 | 95.1 |
| 2023 | -3.92 | -3.92 | 0.00 | 95.1 |
| 2024 | 0.35 | -0.29 | 0.64 | 92.6 |
| 2025 | -5.72 | -4.64 | -1.08 | 86.1 |
| 2026 | 15.68 | 2.72 | 12.96 | 41.1 |

Artefactos: `iciv/data/processed/robustness_summary.csv`, `robustness_scenarios.csv`, `annual_composition.csv` y `robustness_run.json`.

Referencia de protocolo: [OECD/JRC, Handbook on Constructing Composite Indicators (2008), análisis de incertidumbre y sensibilidad](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf). Las decisiones concretas y los umbrales son del proyecto; no son una certificación OECD.
