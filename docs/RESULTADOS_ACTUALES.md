# Resultados actuales · generados desde la release

Versión metodológica: 2.1.0. Generación: 2026-10-28T20:32:03.722493+00:00.

Documento generado automáticamente por `iciv/scripts/write_results_summary.py`. No copiar estos resultados a una entrega sin citar su manifiesto. Anual: retrospectivo; meses provisionales y estimaciones del proveedor no son observaciones cerradas.

## Índice anual (últimos años)

| Año | ICIV AHP | Cobertura efectiva % | Categoría relativa | Tramo |
|---|---:|---:|---|---|
| 2021 | 29.71 | 95.1 | Muy desfavorable | oficial |
| 2022 | 35.94 | 95.1 | Desfavorable | oficial |
| 2023 | 32.02 | 95.1 | Desfavorable | oficial |
| 2024 | 32.37 | 92.6 | Desfavorable | oficial |
| 2025 | 26.01 | 82.9 | Muy desfavorable | oficial |
| 2026 | 42.33 | 41.1 | Desfavorable | oficial |

Serie oficial 2012–2026: máximo 81.69 (2012), mínimo 20.58 (2020). El tramo anterior es exploratorio: no incluye la dimensión institucional.

## Señal mensual (Pulse)

Último mes publicado: 2026-10, 77.25; cobertura 57.0% (provisional).
Último mes elegible: 2026-06, 56.26; cobertura 100.0%.

Relación con el índice anual (2012–2025, años oficiales con cobertura ≥70%, n=14): correlación de Pearson 0.45 en niveles y 0.16 en cambios anuales. La señal mensual pondera condiciones externas, petróleo y prensa; no replica el índice anual.

## Pronóstico mensual

Backtest: muestra común por horizonte, último vintage, sin simulación de publicaciones históricas. El modelo público es persistencia (naive).

| Modelo | Horizonte meses | n | MAE | RMSE |
|---|---:|---:|---:|---:|
| naive | 1 | 20 | 4.6610 | 6.0014 |
| naive | 3 | 20 | 5.5460 | 7.3292 |
| naive | 6 | 20 | 6.6285 | 8.3434 |
| sarima | 1 | 20 | 8.0876 | 15.4588 |
| sarima | 3 | 20 | 9.3643 | 16.9823 |
| sarima | 6 | 20 | 10.9464 | 17.5759 |
| seasonal_naive | 1 | 20 | 8.6425 | 10.6582 |
| seasonal_naive | 3 | 20 | 7.3715 | 9.2517 |
| seasonal_naive | 6 | 20 | 8.7710 | 9.7614 |

## Validación externa (exploratoria)

Asociaciones retrospectivas, no causales. Holm se aplica dentro de cada tramo.

| Contraste | Tramo | Representación | n | Pearson r | p HAC + Holm |
|---|---|---|---:|---:|---:|
| ICIV_loo_vs_migracion_UNHCR | serie_oficial | niveles | 14 | -0.8504 | 0.0026 |
| ICIV_loo_vs_migracion_UNHCR | serie_oficial | primeras_diferencias | 13 | 0.0790 | 1.0000 |
| ICIV_loo_vs_migracion_UNHCR | serie_completa | niveles | 26 | -0.8868 | 0.0001 |
| ICIV_loo_vs_migracion_UNHCR | serie_completa | primeras_diferencias | 25 | -0.1298 | 1.0000 |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_oficial | niveles | 13 | 0.2259 | — |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_oficial | primeras_diferencias | 12 | 0.0948 | — |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_completa | niveles | 25 | -0.4784 | — |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_completa | primeras_diferencias | 24 | 0.0085 | — |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_oficial | niveles | 11 | 0.8330 | 0.0129 |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_oficial | primeras_diferencias | 10 | 0.1742 | 1.0000 |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_completa | niveles | 11 | 0.8330 | 0.0148 |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_completa | primeras_diferencias | 10 | 0.1742 | 1.0000 |
| ICIV_vs_IED_neta | serie_oficial | niveles | 14 | 0.6990 | 0.0359 |
| ICIV_vs_IED_neta | serie_oficial | primeras_diferencias | 13 | 0.2643 | 1.0000 |
| ICIV_vs_IED_neta | serie_completa | niveles | 26 | 0.5388 | 0.0530 |
| ICIV_vs_IED_neta | serie_completa | primeras_diferencias | 25 | 0.1610 | 1.0000 |
| ICIV_completo_vs_vdem_libdem_index | serie_oficial | niveles | 14 | 0.9163 | 0.0001 |
| ICIV_completo_vs_vdem_libdem_index | serie_oficial | primeras_diferencias | 13 | -0.0713 | 1.0000 |
| ICIV_completo_vs_vdem_libdem_index | serie_completa | niveles | 26 | 0.6848 | 0.0002 |
| ICIV_completo_vs_vdem_libdem_index | serie_completa | primeras_diferencias | 25 | -0.2220 | 1.0000 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_oficial | niveles | 14 | 0.9046 | 0.0002 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_oficial | primeras_diferencias | 13 | 0.0196 | 1.0000 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_completa | niveles | 26 | 0.6648 | 0.0003 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_completa | primeras_diferencias | 25 | -0.1536 | 1.0000 |
| ICIV_completo_vs_vdem_rule_of_law | serie_oficial | niveles | 14 | 0.8986 | 0.0014 |
| ICIV_completo_vs_vdem_rule_of_law | serie_oficial | primeras_diferencias | 13 | 0.1095 | 1.0000 |
| ICIV_completo_vs_vdem_rule_of_law | serie_completa | niveles | 26 | 0.4979 | 0.0332 |
| ICIV_completo_vs_vdem_rule_of_law | serie_completa | primeras_diferencias | 25 | -0.3480 | 1.0000 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_oficial | niveles | 14 | 0.8969 | 0.0026 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_oficial | primeras_diferencias | 13 | 0.2196 | 1.0000 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_completa | niveles | 26 | 0.4768 | 0.0345 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_completa | primeras_diferencias | 25 | -0.2890 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_oficial | niveles | 14 | -0.1970 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_oficial | primeras_diferencias | 13 | 0.1179 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_completa | niveles | 26 | -0.3241 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_completa | primeras_diferencias | 25 | 0.1848 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_oficial | niveles | 14 | -0.1719 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_oficial | primeras_diferencias | 13 | 0.1132 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_completa | niveles | 26 | -0.2984 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_completa | primeras_diferencias | 25 | 0.1734 | 1.0000 |

## Valores del proveedor excluidos o marcados

| Variable | Regla | Acción | Años |
|---|---|---|---|
| exportaciones_pct_pib | valor_imposible | excluido_del_calculo | 2000–2011 (12) |
| mortalidad_infantil_x1000 | valor_repetido | marcado_sin_cambio | 2016–2024 (9) |

Luminosidad satelital (Black Marble y Li et al.) está excluida del índice; el mapa es contexto. Detalle de decisiones en `docs/METODOLOGIA.md` y `docs/CIERRE_PROYECTO.md`.
