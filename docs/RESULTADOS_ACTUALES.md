# Resultados actuales · generados desde la release

Versión metodológica: 2.1.0. Generación: 2026-11-02T17:02:00.356066+00:00.

Documento generado automáticamente por `iciv/scripts/write_results_summary.py`. No copiar estos resultados a una entrega sin citar su manifiesto. Anual: retrospectivo; meses provisionales y estimaciones del proveedor no son observaciones cerradas.

## Índice anual (últimos años)

| Año | ICIV AHP | Cobertura efectiva % | Categoría relativa | Tramo |
|---|---:|---:|---|---|
| 2021 | 29.71 | 95.1 | Muy desfavorable | oficial |
| 2022 | 35.94 | 95.1 | Desfavorable | oficial |
| 2023 | 32.02 | 95.1 | Desfavorable | oficial |
| 2024 | 32.37 | 92.6 | Desfavorable | oficial |
| 2025 | 26.66 | 86.1 | Muy desfavorable | oficial |
| 2026 | 42.33 | 41.1 | Desfavorable | oficial |

Serie oficial 2012–2026: máximo 81.69 (2012), mínimo 20.58 (2020). El tramo anterior es exploratorio: no incluye la dimensión institucional.

## Señal mensual (Pulse)

Último mes publicado: 2026-10, 74.73; cobertura 57.0% (provisional).
Último mes elegible: 2026-06, 56.26; cobertura 100.0%.

Relación con el índice anual (2012–2025, años oficiales con cobertura ≥70%, n=14): correlación de Pearson 0.45 en niveles y 0.16 en cambios anuales. La señal mensual pondera condiciones externas, petróleo y prensa; no replica el índice anual.

## Pronóstico mensual

Backtest: muestra común por horizonte, último vintage, sin simulación de publicaciones históricas. El modelo público es persistencia (naive).

| Modelo | Horizonte meses | n | MAE | RMSE |
|---|---:|---:|---:|---:|
| naive | 1 | 20 | 4.6610 | 6.0018 |
| naive | 3 | 20 | 5.5460 | 7.3295 |
| naive | 6 | 20 | 6.6295 | 8.3449 |
| sarima | 1 | 20 | 6.6593 | 9.8020 |
| sarima | 3 | 20 | 7.5479 | 10.3296 |
| sarima | 6 | 20 | 9.3357 | 12.1586 |
| seasonal_naive | 1 | 20 | 8.6425 | 10.6582 |
| seasonal_naive | 3 | 20 | 7.3710 | 9.2515 |
| seasonal_naive | 6 | 20 | 8.7725 | 9.7631 |

## Validación externa (exploratoria)

Asociaciones retrospectivas, no causales. Holm se aplica dentro de cada tramo.

| Contraste | Tramo | Representación | n | Pearson r | p HAC + Holm |
|---|---|---|---:|---:|---:|
| ICIV_loo_vs_migracion_UNHCR | serie_oficial | niveles | 14 | -0.8494 | 0.0027 |
| ICIV_loo_vs_migracion_UNHCR | serie_oficial | primeras_diferencias | 13 | 0.0659 | 1.0000 |
| ICIV_loo_vs_migracion_UNHCR | serie_completa | niveles | 26 | -0.8862 | 0.0001 |
| ICIV_loo_vs_migracion_UNHCR | serie_completa | primeras_diferencias | 25 | -0.1367 | 1.0000 |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_oficial | niveles | 13 | 0.2260 | — |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_oficial | primeras_diferencias | 12 | 0.0952 | — |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_completa | niveles | 25 | -0.4783 | — |
| ICIV_loo_vs_luminosidad_2000_2024 | serie_completa | primeras_diferencias | 24 | 0.0087 | — |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_oficial | niveles | 11 | 0.8331 | 0.0128 |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_oficial | primeras_diferencias | 10 | 0.1750 | 1.0000 |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_completa | niveles | 11 | 0.8331 | 0.0148 |
| ICIV_loo_vs_luminosidad_era_VIIRS | serie_completa | primeras_diferencias | 10 | 0.1750 | 1.0000 |
| ICIV_vs_IED_neta | serie_oficial | niveles | 14 | 0.6987 | 0.0376 |
| ICIV_vs_IED_neta | serie_oficial | primeras_diferencias | 13 | 0.2756 | 1.0000 |
| ICIV_vs_IED_neta | serie_completa | niveles | 26 | 0.5386 | 0.0546 |
| ICIV_vs_IED_neta | serie_completa | primeras_diferencias | 25 | 0.1654 | 1.0000 |
| ICIV_completo_vs_vdem_libdem_index | serie_oficial | niveles | 14 | 0.9158 | 0.0001 |
| ICIV_completo_vs_vdem_libdem_index | serie_oficial | primeras_diferencias | 13 | -0.0688 | 1.0000 |
| ICIV_completo_vs_vdem_libdem_index | serie_completa | niveles | 26 | 0.6846 | 0.0002 |
| ICIV_completo_vs_vdem_libdem_index | serie_completa | primeras_diferencias | 25 | -0.2202 | 1.0000 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_oficial | niveles | 14 | 0.9046 | 0.0002 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_oficial | primeras_diferencias | 13 | 0.0195 | 1.0000 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_completa | niveles | 26 | 0.6647 | 0.0003 |
| ICIV_sinD3_vs_vdem_libdem_index | serie_completa | primeras_diferencias | 25 | -0.1536 | 1.0000 |
| ICIV_completo_vs_vdem_rule_of_law | serie_oficial | niveles | 14 | 0.8988 | 0.0014 |
| ICIV_completo_vs_vdem_rule_of_law | serie_oficial | primeras_diferencias | 13 | 0.1144 | 1.0000 |
| ICIV_completo_vs_vdem_rule_of_law | serie_completa | niveles | 26 | 0.4977 | 0.0334 |
| ICIV_completo_vs_vdem_rule_of_law | serie_completa | primeras_diferencias | 25 | -0.3466 | 1.0000 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_oficial | niveles | 14 | 0.8969 | 0.0027 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_oficial | primeras_diferencias | 13 | 0.2196 | 1.0000 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_completa | niveles | 26 | 0.4768 | 0.0346 |
| ICIV_sinD3_vs_vdem_rule_of_law | serie_completa | primeras_diferencias | 25 | -0.2890 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_oficial | niveles | 14 | -0.1960 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_oficial | primeras_diferencias | 13 | 0.1168 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_completa | niveles | 26 | -0.3234 | 1.0000 |
| ICIV_completo_vs_vdem_corrupcion_pol | serie_completa | primeras_diferencias | 25 | 0.1837 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_oficial | niveles | 14 | -0.1719 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_oficial | primeras_diferencias | 13 | 0.1134 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_completa | niveles | 26 | -0.2984 | 1.0000 |
| ICIV_sinD3_vs_vdem_corrupcion_pol | serie_completa | primeras_diferencias | 25 | 0.1735 | 1.0000 |

## Valores del proveedor excluidos o marcados

| Variable | Regla | Acción | Años |
|---|---|---|---|
| exportaciones_pct_pib | valor_imposible | excluido_del_calculo | 2000–2011 (12) |
| mortalidad_infantil_x1000 | valor_repetido | marcado_sin_cambio | 2016–2024 (9) |

Luminosidad satelital (Black Marble y Li et al.) está excluida del índice; el mapa es contexto. Detalle de decisiones en `docs/METODOLOGIA.md` y `docs/CIERRE_PROYECTO.md`.
