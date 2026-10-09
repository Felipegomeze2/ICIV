# Robustez ampliada · revisión de trabajo

Documento generado automáticamente por `iciv/scripts/robustness_review.py`.

Generación UTC: 2026-10-09T13:56:52.038889+00:00. Escenarios: 79.

Alternativas deterministas sobre datos reales; no se generan ni rellenan observaciones. La dispersión entre diseños no es un intervalo de confianza. No se eligieron pesos para maximizar correlación con IED.

Se varían pesos dimensionales ±5/10/20%, normalización, agregación, transformación de inflación, piso de cobertura, exclusión de cada variable y dimensión, y ausencia de datos por dimensión. Se añade la retirada de estimaciones WEO verificadas cuando existe evidencia.

## Mayor diferencia respecto al modelo base

Muestra: años con cobertura base ≥80% y score disponible en ambos diseños. El CSV también muestra todos los años comparables. Comparar n: los pisos más estrictos pueden reducirlo.

| Escenario | n | MAE puntos | Máximo absoluto | Spearman | Cambios de categoría |
|---|---:|---:|---:|---:|---:|
| rank | 14 | 9.495 | 18.110 | 0.982 | 9 |
| geometrico | 14 | 6.294 | 20.550 | 0.978 | 5 |
| sin_datos_D1_macro | 14 | 5.960 | 13.870 | 0.947 | 4 |
| excluir_D1_macro | 14 | 5.960 | 13.870 | 0.947 | 4 |
| piso_100% | 14 | 4.003 | 11.870 | 0.925 | 3 |
| excluir_D4_comercial | 14 | 3.334 | 7.010 | 0.969 | 4 |
| sin_datos_D4_comercial | 14 | 3.334 | 7.010 | 0.969 | 4 |
| excluir_petroleo_crudo_produccion_tbpd | 14 | 3.325 | 6.700 | 0.987 | 2 |
| sin_datos_D2_energia | 14 | 3.325 | 6.700 | 0.987 | 2 |
| excluir_D2_energia | 14 | 3.325 | 6.700 | 0.987 | 2 |
| inflacion_sin_log | 14 | 3.131 | 5.850 | 0.974 | 2 |
| excluir_D3_institucional | 14 | 3.031 | 6.680 | 0.996 | 2 |
| sin_datos_D3_institucional | 14 | 3.031 | 6.680 | 0.996 | 2 |
| winsor05 | 14 | 2.881 | 5.850 | 0.987 | 5 |
| excluir_pib_crecimiento_real_pct | 14 | 2.423 | 3.790 | 0.982 | 3 |

## Composición interanual

La canasta común utiliza los mismos indicadores disponibles en ambos años, mantiene el universo de cobertura y aplica el piso dimensional. El residuo es el efecto neto de composición; no atribuye causas económicas.

| Año | Cambio publicado | Cambio canasta común | Residuo composición | Cobertura común % |
|---|---:|---:|---:|---:|
| 2020 | -11.66 | -11.66 | 0.00 | 95.1 |
| 2021 | 9.14 | 9.14 | 0.00 | 95.1 |
| 2022 | 6.23 | 6.23 | 0.00 | 95.1 |
| 2023 | -3.92 | -3.92 | 0.00 | 95.1 |
| 2024 | 0.34 | -0.30 | 0.64 | 92.6 |
| 2025 | -6.41 | -4.44 | -1.97 | 82.9 |
| 2026 | 16.75 | 3.21 | 13.54 | 41.1 |

Artefactos: `iciv/data/processed/robustness_summary.csv`, `robustness_scenarios.csv`, `annual_composition.csv` y `robustness_run.json`.

Referencia de protocolo: [OECD/JRC, Handbook on Constructing Composite Indicators (2008), análisis de incertidumbre y sensibilidad](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf). Las decisiones concretas y los umbrales son del proyecto; no son una certificación OECD.
