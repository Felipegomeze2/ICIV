# VARIABLES MASTER — ICIV Venezuela
## Fuente única de verdad del índice. Versión congelada: 21 mayo 2026.

> **Este documento es la referencia canónica del índice.**
> Todo conteo en tesis, README, catálogo y dashboard debe coincidir con este archivo.
> Cualquier discrepancia entre este documento y otro artefacto → este documento gana.

---

## Resumen ejecutivo del índice

| Campo | Valor |
|---|---|
| Nombre oficial | ICIV — Indicador de Clima de Inversión Venezuela |
| Período histórico | 2000–2026 |
| Periodicidad del índice anual | Anual |
| Co-indicador de alta frecuencia | ICIV Pulse Mensual (2010–2026, 197 meses) |
| Dimensiones | 6 (D1–D6) |
| Variables en score final | **37** (ver tabla abajo) |
| Variables declaradas pero sin datos | 2 (`ofac_sanciones_count`, `vuelos_aerolineas_int_count`) → excluidas del score efectivo |
| Variables con datos insuficientes (< 50% cobertura) | 2 (`google_trends_vzla` 22%, `rsf_press_freedom` 48%) → rol experimental |
| Método de normalización | Min-Max (rango 2000–2026) |
| Método de ponderación | AHP Saaty (1980), CR = 0.0081 < 0.10 |
| Método de agregación | Lineal ponderada con redistribución de pesos ante NaN |
| Fuentes venezolanas | **Ninguna** (regla absoluta del proyecto) |
| Datos inventados / fallbacks | **Ninguno** (regla absoluta del proyecto) |

---

## Pesos de dimensiones (AHP validado, CR = 0.0081)

| Dim | Nombre | Peso ICIV |
|---|---|---:|
| D1 | Estabilidad Macroeconómica | 25.0% |
| D2 | Sector Energético y Petróleo | 20.0% |
| D3 | Entorno Institucional y Legal | 20.0% |
| D4 | Apertura Comercial y Financiera | 15.0% |
| D5 | Capital Humano e Infraestructura Social | 10.0% |
| D6 | Percepción Internacional | 10.0% |
| **Total** | | **100.0%** |

---

## Tabla maestra de variables

### Convenciones
- **Cobertura**: años con dato real sobre 27 años totales (2000–2026)
- **Dirección**: `+` = mayor valor → mejor clima | `−` = mayor valor → peor clima
- **Rol**: `score` = entra al ICIV final | `experimental` = disponible pero cobertura baja | `sin_datos` = declarado pero sin cobertura | `auxiliar` = usado en contexto/dashboard, no en score
- **Acceso**: `API` = descarga automática reproducible | `CSV_manual` = transcripción o descarga manual archivada | `calc` = derivado de campos publicados

---

### D1 — Estabilidad Macroeconómica (peso: 25%)

| variable_id | nombre_humano | peso_dim | fuente | acceso | cobertura | rango | dirección | faltantes | rol |
|---|---|---:|---|---|---|---|:---:|---|---|
| `inflacion_deflactor_pib_pct` | Inflación (deflactor PIB) | 28% | IMF WEO | API | 27/27 (100%) | 2000–2026 | − | NaN | **score** |
| `pib_crecimiento_real_pct` | Crecimiento PIB real | 22% | IMF WEO / WDI | API | 27/27 (100%) | 2000–2026 | + | NaN | **score** |
| `reservas_internacionales_usd` | Reservas internacionales | 18% | WDI World Bank | API | 18/27 (67%) | 2000–2017 | + | Venezuela dejó de reportar ~2018 | **score** |
| `tipo_cambio_oficial_lcu_usd` | Tipo de cambio oficial | 12% | WDI World Bank | API | 23/27 (85%) | 2000–2024 | − | NaN pre-2000 y reciente | **score** |
| `wti_precio_usd` | Precio WTI (petróleo) | 12% | FRED / EIA | API | 27/27 (100%) | 2000–2026 | + | NaN | **score** |
| `tasa_fed_funds_pct` | Tasa Fed Funds (EEUU) | 8% | FRED | API | 27/27 (100%) | 2000–2026 | − | NaN | **score** |

**Nota D1**: `inflacion_deflactor_pib_pct` y `tipo_cambio_oficial_lcu_usd` tienen transformación log10 aplicada en pipeline para comprimir 4 órdenes de magnitud. Reversible y documentada en `main.py`.

---

### D2 — Sector Energético y Petróleo (peso: 20%)

| variable_id | nombre_humano | peso_dim | fuente | acceso | cobertura | rango | dirección | faltantes | rol |
|---|---|---:|---|---|---|---|:---:|---|---|
| `petroleo_crudo_produccion_tbpd` | Producción crudo (TBPD) | 45% | EIA International | API | 27/27 (100%) | 2000–2026 | + | NaN | **score** |
| `gas_natural_produccion_bcf` | Producción gas natural | 25% | EIA International | API | 25/27 (93%) | 2000–2024 | + | NaN 2025–2026 (lag publicación) | **score** |
| `electricidad_generacion_bkwh` | Generación eléctrica | 15% | EIA International | API | 25/27 (93%) | 2000–2024 | + | NaN 2025–2026 (lag publicación) | **score** |
| `luminosidad_nocturna_idx` | Luminosidad nocturna VIIRS | 15% | Li et al. Figshare (VIIRS/DMSP) | Descarga pública | 25/27 (93%) | 2000–2024 | + | NaN 2025–2026 (publicación pendiente) | **score** |

---

### D3 — Entorno Institucional y Legal (peso: 20%)

| variable_id | nombre_humano | peso_dim | fuente | acceso | cobertura | rango | dirección | faltantes | rol |
|---|---|---:|---|---|---|---|:---:|---|---|
| `cpi_score` | CPI Transparencia Internacional | 14% | TI / OWID | CSV_manual | 26/27 (96%) | 2000–2025 | + | NaN 2026 (publica ene 2027) | **score** |
| `wgi_promedio_sc` | WGI Gobernanza (promedio 6 ind.) | 14% | WGI World Bank | API | 25/27 (93%) | 2000–2024 | + | NaN 2025–2026 (publica sep 2026) | **score** |
| `ief_overall_score` | IEF Libertad Económica | 11% | Heritage Foundation | CSV_manual | 26/27 (96%) | 2000–2025 | + | NaN 2026 (publica ene 2027) | **score** |
| `freedom_house_score` | Freedom House (FitW) | 10% | Freedom House | CSV_manual + calc | 26/27 (96%) | 2000–2025 | + | NaN 2026 (publica ene 2027) | **score** |
| `vdem_libdem_index` | V-Dem Democracia Liberal | 10% | V-Dem / OWID | API (OWID) | 26/27 (96%) | 2000–2025 | + | NaN 2026 | **score** |
| `wjp_rule_of_law` | WJP Estado de Derecho | 9% | WJP / OWID | API (OWID) | 26/27 (96%) | 2000–2025 | + | NaN 2026 | **score** |
| `fragile_states_index` | Fragile States Index | 8% | Fund for Peace | CSV_manual | 19/27 (70%) | 2006–2024 | − | Pre-2006 sin publicación | **score** |
| `pts_terror_politico` | PTS Terror Político | 7% | Political Terror Scale | API | 24/27 (89%) | 2000–2023 | − | NaN 2024–2026 (lag) | **score** |
| `rsf_press_freedom` | RSF Libertad de Prensa | 4% | RSF / OWID | CSV_manual | 13/27 (48%) | 2013–2025 | + | Pre-2013 metodología distinta; empalme documentado | **experimental** |
| `bti_governance_index` | BTI Gobernanza | 4% | Bertelsmann / bti-project.org | CSV_manual | 21/27 (78%) | 2006–2026 | + | Bienal hasta 2024, luego anual | **score** |
| `ofac_sanciones_count` | Sanciones OFAC | 5% | US Treasury OFAC SDN | API (snapshot) | 0/27 (0%) | — | Solo snapshot actual, sin histórico | **sin_datos** |
| `ucdp_conflicto_idx` | Índice conflicto UCDP | 1% | UCDP GED | API | 24/27 (89%) | 2000–2023 | − | NaN 2024–2026 (lag) | **score** |
| `basel_aml_index` | Basel AML Index | 3% | Basel Governance | CSV_manual | 0/27 (0%) | — | URLs rotas; requiere descarga manual | **sin_datos** |

**Notas D3**:
- `ofac_sanciones_count` y `basel_aml_index` declaradas en `dimensions.py` pero **efectivamente excluidas del score** por cobertura cero. El aggregator redistribuye sus pesos automáticamente.
- `rsf_press_freedom` marcada `experimental`: cobertura 48%, empalme de escalas pre/post 2022 documentado.
- `freedom_house_score` 2000–2002: calculado desde PR/CL publicados con fórmula oficial FH — auditable.

---

### D4 — Apertura Comercial y Financiera (peso: 15%)

| variable_id | nombre_humano | peso_dim | fuente | acceso | cobertura | rango | dirección | faltantes | rol |
|---|---|---:|---|---|---|---|:---:|---|---|
| `ied_neta_usd` | IED neta (USD) | 28% | WDI World Bank | API | 25/27 (93%) | 2000–2024 | + | NaN 2025–2026 (lag) | **score** |
| `exportaciones_pct_pib` | Exportaciones % PIB | 22% | WDI / OWID | API | 25/27 (93%) | 2000–2024 | + | NaN 2025–2026 | **score** |
| `desempleo_pct` | Desempleo | 16% | IMF / OWID | API | 26/27 (96%) | 2000–2025 | − | NaN 2026 | **score** |
| `migrantes_vzla_millones` | Diáspora venezolana (millones) | 14% | UNHCR | API | 26/27 (96%) | 2000–2025 | − | NaN 2026 (pendiente publicación) | **score** |
| `lsci_conectividad_maritima` | LSCI Conectividad marítima | 10% | UNCTAD / WDI | API | 16/27 (59%) | 2006–2021 | + | Pre-2006 y post-2021 sin datos | **score** |
| `remesas_recibidas_usd` | Remesas recibidas (USD) | 6% | WDI World Bank | API | 17/27 (63%) | 2000–2016 | + | Post-2016 Venezuela dejó de reportar al WB | **score** |
| `vuelos_aerolineas_int_count` | Vuelos internacionales | 4% | OpenSky Network | API (sin histórico) | 0/27 (0%) | — | OpenSky sin cobertura histórica ADS-B | **sin_datos** |

**Nota D4**: `ied_neta_usd` participa en el score Y en el análisis de coherencia interna (sección Validación del dashboard). Ver Fase 4 del plan: ese análisis está etiquetado como exploratorio/descriptivo, no como validación externa.

---

### D5 — Capital Humano e Infraestructura Social (peso: 10%)

| variable_id | nombre_humano | peso_dim | fuente | acceso | cobertura | rango | dirección | faltantes | rol |
|---|---|---:|---|---|---|---|:---:|---|---|
| `hdi` | IDH / HDI | 24% | UNDP HDR / OWID | API (OWID) | 24/27 (89%) | 2000–2023 | + | NaN 2024–2026 (publica sep 2026) | **score** |
| `esperanza_vida_anos` | Esperanza de vida | 16% | WHO / WDI | API | 24/27 (89%) | 2000–2023 | + | NaN 2024–2026 (lag) | **score** |
| `mortalidad_infantil_x1000` | Mortalidad infantil | 14% | UN IGME / WDI | API | 24/27 (89%) | 2000–2023 | − | NaN 2024–2026 (lag) | **score** |
| `tasa_alfabetizacion_adulta_pct` | Tasa de alfabetización | 14% | WDI World Bank | API | 21/27 (78%) | 2001–2021 | + | Sporádico; WB no actualiza frecuentemente | **score** |
| `acceso_electricidad_pct` | Acceso electricidad | 14% | WDI World Bank | API | 24/27 (89%) | 2000–2023 | + | NaN 2024–2026 (lag) | **score** |
| `ghi_score` | Global Hunger Index | 8% | IFPRI / OWID | API (OWID) | 16/27 (59%) | 2000–2021 | − | Bienal hasta 2022 | **score** |
| `fao_calorias_per_capita` | Calorías per cápita (FAO) | 6% | FAO / OWID | API (OWID) | 24/27 (89%) | 2000–2023 | + | NaN 2024–2026 (lag) | **score** |
| `ilo_empleo_informal_pct` | Empleo informal (ILO proxy) | 4% | ILO / WDI (SL.EMP.VULN.ZS) | API | 26/27 (96%) | 2000–2025 | − | NaN 2026 | **score** |

---

### D6 — Percepción Internacional (peso: 10%)

| variable_id | nombre_humano | peso_dim | fuente | acceso | cobertura | rango | dirección | faltantes | rol |
|---|---|---:|---|---|---|---|:---:|---|---|
| `guardian_tono_titulares` | Tono titulares The Guardian | 45% | The Guardian API + VADER | API | 27/27 (100%) | 2000–2026 | + | NaN | **score** |
| `guardian_articulos_venezuela` | Volumen artículos Guardian | 25% | The Guardian API | API | 27/27 (100%) | 2000–2026 | − | NaN | **score** |
| `google_trends_vzla` | Google Trends Venezuela | 30% | Google Trends / pytrends | API | 6/27 (22%) | 2004–2009 | + | HTTP 429 rate limit en máquina actual; datos solo 2004–2009 | **experimental** |

**Nota D6**: `google_trends_vzla` es experimental por cobertura 22% (6 años, rango 2004–2009). No representa el período más reciente. Peso redistribuido entre las otras dos variables del Pulse.

---

## Resumen de variables por rol

| Rol | Count | Variables |
|---|:---:|---|
| **score** (entra al ICIV final) | 35 | Ver tabla arriba |
| **experimental** (disponible, cobertura baja) | 2 | `rsf_press_freedom`, `google_trends_vzla` |
| **sin_datos** (declarada, 0 cobertura) | 3 | `ofac_sanciones_count`, `vuelos_aerolineas_int_count`, `basel_aml_index` |
| **Total declaradas en dimensions.py** | 40 | |

> **Conteo oficial del índice: 35 variables en score + 2 experimentales = 37 variables con datos.**
> Las 3 `sin_datos` están declaradas en el código pero el aggregator las excluye automáticamente (NaN total → peso redistribuido).

---

## Variables con advertencia de interpretación en años recientes

| Variable | Problema | Acción documentada |
|---|---|---|
| `reservas_internacionales_usd` | Venezuela dejó de reportar al WB ~2018 | NaN desde 2018, documentado |
| `remesas_recibidas_usd` | Venezuela dejó de reportar post-2016 | NaN desde 2017, documentado |
| `ofac_sanciones_count` | OFAC solo publica snapshot, sin histórico | 0/27, excluida del score |
| `google_trends_vzla` | Rate limit HTTP 429; datos incompletos | 6/27, rol experimental |
| `rsf_press_freedom` | Cambio metodológico RSF en 2022 (escala invertida) | Empalme documentado en fetch_rsf.py |
| `basel_aml_index` | URLs de descarga rotas en sitio oficial | 0/27, excluida del score |

---

## Cobertura del score por año (referencia)

| Año | Cobertura ICIV AHP | Categoría |
|---|---:|---|
| 2000–2020 | 80%–95% | Histórico confiable |
| 2021–2023 | 78%–85% | Histórico útil con advertencia |
| 2024 | 78.4% | Útil con advertencia |
| 2025 | 51.9% | **Parcial — interpretar con cautela** |
| 2026 | 35.1% | **Provisional / experimental** |

Umbrales de interpretación (definidos en este documento, aplicados en dashboard y tesis):

| Cobertura | Etiqueta | Interpretación |
|---|---|---|
| ≥ 85% | Histórico | Score representativo del período |
| 70%–84.9% | Útil con advertencia | Score fiable, señalar limitación |
| 50%–69.9% | Parcial | Interpretar con cautela, no comparar directamente |
| < 50% | Provisional | No usar como referencia primaria de decisión |

---

## Política de datos del proyecto (cláusula formal)

> El ICIV adopta una política restrictiva de datos. Para la versión defendida del índice solo se aceptan observaciones trazables a fuentes internacionales aprobadas y verificables. Cuando una observación no está disponible bajo esa regla, se conserva como valor faltante y su ausencia se refleja en la cobertura anual del índice. El proyecto no completa series con valores inventados, proxies manuales no auditables ni fuentes excluidas por criterio de origen. Ninguna fuente de origen venezolano (BCV, INE, PDVSA, Conatel, OVF, IIES, UCAB) entra al score final.

---

*Generado: 21 mayo 2026 | Referencia: PLAN_DE_ACCION_REVISION_JURADO_ICIV.md*
*Próxima revisión: al congelar versión para defensa*
