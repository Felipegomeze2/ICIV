# Resultados actuales · generados desde la release

Versión metodológica: 2.1.0. Generación: 2026-10-19T14:38:02.351593+00:00.

Documento generado automáticamente por `iciv/scripts/write_results_summary.py`. No copiar estos resultados a una entrega sin citar su manifiesto. Anual: retrospectivo; meses provisionales y estimaciones del proveedor no son observaciones cerradas.

## Índice anual (últimos años)

| Año | ICIV AHP | Cobertura efectiva % | Categoría relativa | Tramo |
|---|---:|---:|---|---|
| 2021 | 29.70 | 95.1 | Muy desfavorable | oficial |
| 2022 | 35.93 | 95.1 | Desfavorable | oficial |
| 2023 | 32.01 | 95.1 | Desfavorable | oficial |
| 2024 | 32.36 | 92.6 | Desfavorable | oficial |
| 2025 | 25.98 | 82.9 | Muy desfavorable | oficial |
| 2026 | 42.19 | 41.1 | Desfavorable | oficial |

Serie oficial 2012–2026: máximo 81.67 (2012), mínimo 20.56 (2020). El tramo anterior es exploratorio: no incluye la dimensión institucional.

## Señal mensual (Pulse)

Último mes publicado: 2026-10, 76.65; cobertura 30.0% (provisional).
Último mes elegible: 2026-06, 56.26; cobertura 100.0%.

Relación con el índice anual (2012–2025, años oficiales con cobertura ≥70%, n=14): correlación de Pearson 0.45 en niveles y 0.16 en cambios anuales. La señal mensual pondera condiciones externas, petróleo y prensa; no replica el índice anual.

## Pronóstico mensual

Backtest: muestra común por horizonte, último vintage, sin simulación de publicaciones históricas. El modelo público es persistencia (naive).

| Modelo | Horizonte meses | n | MAE | RMSE |
|---|---:|---:|---:|---:|
| naive | 1 | 20 | 4.6720 | 6.0067 |
| naive | 3 | 20 | 5.5465 | 7.3298 |
| naive | 6 | 20 | 6.6295 | 8.3447 |
| sarima | 1 | 20 | 6.6526 | 9.8030 |
| sarima | 3 | 20 | 7.5544 | 10.3300 |
| sarima | 6 | 20 | 9.3405 | 12.1581 |
| seasonal_naive | 1 | 20 | 8.6530 | 10.6691 |
| seasonal_naive | 3 | 20 | 7.3715 | 9.2521 |
| seasonal_naive | 6 | 20 | 8.7735 | 9.7641 |

## Validación externa (exploratoria)

Asociaciones retrospectivas, no causales. Holm se aplica dentro de cada tramo.

| Contraste | Tramo | Representación | n | Pearson r | p HAC + Holm |
|---|---|---|---:|---:|---:|
| ICIV_loo_vs_migracion_UNHCR | serie_oficial | niveles | 14 | -0.8504 | 0.0026 |
| ICIV_loo_vs_migracion_UNHCR | serie_oficial | primeras_diferencias | 13 | 0.0791 | 1.0000 |
| ICIV_loo_vs_migracion_UNHCR | serie_completa | niveles | 26 | -0.8868 | 0.0001 |
| ICIV_loo_vs_migracion_UNHCR | serie_completa | primeras_diferencias | 25 | -0.1297 | 1.0000 |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_oficial | niveles | 13 | 0.2260 | — |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_oficial | primeras_diferencias | 12 | 0.0951 | — |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_completa | niveles | 25 | -0.4784 | — |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_completa | primeras_diferencias | 24 | 0.0087 | — |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_oficial | niveles | 11 | 0.8330 | 0.0129 |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_oficial | primeras_diferencias | 10 | 0.1742 | 1.0000 |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_completa | niveles | 11 | 0.8330 | 0.0149 |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_completa | primeras_diferencias | 10 | 0.1742 | 1.0000 |
| ICIV_vs_IED_neta | serie_oficial | niveles | 13 | 0.5382 | 0.3820 |
| ICIV_vs_IED_neta | serie_oficial | primeras_diferencias | 12 | 0.1206 | 1.0000 |
| ICIV_vs_IED_neta | serie_completa | niveles | 25 | 0.3553 | 0.3487 |
| ICIV_vs_IED_neta | serie_completa | primeras_diferencias | 24 | 0.0915 | 1.0000 |
| ICIV_completo_vs_vdem_libdem_index | serie_oficial | niveles | 14 | 0.9162 | 0.0001 |
| ICIV_completo_vs_vdem_libdem_index | serie_oficial | primeras_diferencias | 13 | -0.0712 | 1.0000 |
| ICIV_completo_vs_vdem_libdem_index | serie_completa | niveles | 26 | 0.6849 | 0.0002 |
| ICIV_completo_vs_vdem_libdem_index | serie_completa | primeras_diferencias | 25 | -0.2219 | 1.0000 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_oficial | niveles | 14 | 0.9046 | 0.0002 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_oficial | primeras_diferencias | 13 | 0.0194 | 1.0000 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_completa | niveles | 26 | 0.6649 | 0.0003 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_completa | primeras_diferencias | 25 | -0.1537 | 1.0000 |
| ICIV_completo_vs_vdem_rule_of_law | serie_oficial | niveles | 14 | 0.8985 | 0.0014 |
| ICIV_completo_vs_vdem_rule_of_law | serie_oficial | primeras_diferencias | 13 | 0.1093 | 1.0000 |
| ICIV_completo_vs_vdem_rule_of_law | serie_completa | niveles | 26 | 0.4979 | 0.0332 |
| ICIV_completo_vs_vdem_rule_of_law | serie_completa | primeras_diferencias | 25 | -0.3481 | 1.0000 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_oficial | niveles | 14 | 0.8969 | 0.0026 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_oficial | primeras_diferencias | 13 | 0.2197 | 1.0000 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_completa | niveles | 26 | 0.4769 | 0.0345 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_completa | primeras_diferencias | 25 | -0.2891 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_oficial | niveles | 14 | -0.1971 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_oficial | primeras_diferencias | 13 | 0.1176 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_completa | niveles | 26 | -0.3242 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_completa | primeras_diferencias | 25 | 0.1846 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_oficial | niveles | 14 | -0.1719 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_oficial | primeras_diferencias | 13 | 0.1130 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_completa | niveles | 26 | -0.2985 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_completa | primeras_diferencias | 25 | 0.1732 | 1.0000 |

## Valores del proveedor excluidos o marcados

| Variable | Regla | Acción | Años |
|---|---|---|---|
| exportaciones_pct_pib | valor_imposible | excluido_del_calculo | 2000–2011 (12) |
| mortalidad_infantil_x1000 | valor_repetido | marcado_sin_cambio | 2016–2024 (9) |

Luminosidad satelital (Black Marble y Li et al.) está excluida del índice; el mapa es contexto. Detalle de decisiones en `docs/METODOLOGIA.md` y `docs/CIERRE_PROYECTO.md`.
