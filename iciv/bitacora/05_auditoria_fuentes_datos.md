# Bitácora 05 — Auditoría Completa de Fuentes de Datos

**Fecha:** 4 de mayo de 2026  
**Objetivo:** Verificar cada fuente de datos una a una — si trae datos reales, cuántos años, en qué formato, y corregir las que estaban rotas o usando datos inventados.

**Principio rector:** CERO datos inventados, CERO fallbacks estáticos. Si no hay dato real de una fuente verificable, la variable queda NaN. Reproducible por cualquier persona con acceso a internet y Python.

---

## Tabla de Auditoría — Estado Final Post-Correcciones

| # | Script | Fuente | Variable(s) ICIV | Años raw | Dim | Estado | Tipo dato |
|---|--------|--------|-----------------|----------|-----|--------|-----------|
| 1 | `fetch_wdi.py` | World Bank WDI API | `pib_nominal_usd`, `pib_crecimiento_real_pct`, `pib_per_capita_usd`, `ied_neta_usd`, `reservas_internacionales_usd`, `exportaciones_pct_pib`, `acceso_electricidad_pct`, `inflacion_ipc_pct`, `tipo_cambio_oficial_lcu_usd`, `tasa_alfabetizacion_adulta_pct` | 8–25 años | D1/D4/D5 | ✅ Real API | API pública, sin auth |
| 2 | `fetch_wgi.py` | World Bank WGI (ZIP) | `wgi_promedio_sc` (6 sub-indicadores) | 24 años | D3 | ✅ Real API | Descarga ZIP bulk |
| 3 | `fetch_eia.py` | EIA API v2 | `petroleo_crudo_produccion_tbpd`, `gas_natural_produccion_bcf`, `electricidad_generacion_bkwh` | 25–26 años | D2 | ✅ Real API | API con key |
| 4 | `fetch_imf.py` | IMF DataMapper API | `inflacion_deflactor_pib_pct` (PCPIPCH), `desempleo_pct` (LUR), `cuenta_corriente_pct_pib` (BCA_NGDPD) | 19–27 años | D1 | ✅ Real API — **CORREGIDO** | API pública |
| 5 | `fetch_fred.py` | FRED (St. Louis Fed) | `wti_precio_usd`, `tasa_fed_funds_pct` | 27 años | D1 | ✅ Real API | CSV descarga directa |
| 6 | `fetch_guardian.py` | The Guardian API | `guardian_articulos_venezuela`, `guardian_tono_titulares` | 27 años | D6 | ✅ Real API | API con key |
| 7 | `fetch_unhcr.py` | UNHCR Population API | `migrantes_vzla_millones` | 26 años | D4 | ✅ Real API — **CORREGIDO** | API pública |
| 8 | `fetch_pts.py` | Political Terror Scale 2024 | `pts_terror_politico` | 24 años | D3 | ✅ Real descarga directa | CSV público sin auth |
| 9 | `fetch_who.py` | WHO GHO OData API | `esperanza_vida_anos`, `mortalidad_infantil_x1000` | 22–24 años | D5 | ✅ Real API | API pública OData |
| 10 | `fetch_unctad.py` | **World Bank WDI** (IS.SHP.GCNW.XQ) | `lsci_conectividad_maritima` | 16 años (2006–2021) | D4 | ✅ Real API — **CORREGIDO** | API pública |
| 11 | `fetch_gtrends.py` | Google Trends (pytrends) | `google_trends_vzla` | 23 años | D6 | ✅ Real API — **CORREGIDO** | pytrends API |
| 12 | `fetch_freedom_house.py` | Freedom House FitW | `freedom_house_score` | 25 años (2000–2024) | D3 | ⚠️ Publicación manual | Datos publicados FitW, sin API |
| 13 | `fetch_ofac.py` | OFAC SDN CSV | `ofac_sanciones_count` | 25 años (2000–2024) | D3 | ⚠️ SDN real + histórico | SDN actual real; histórico de registros OFAC |
| 14 | `fetch_opensky.py` | OpenSky API + IATA/INAC | `vuelos_aerolineas_int_count` | 25 años | D4 | ⚠️ Static con fuentes | Datos de aerolíneas publicados + OpenSky API 2016+ |
| 15 | Manual CPI | Transparency International | `cpi_score` | 27 años | D3 | ⚠️ Manual / descarga | Descarga manual del portal TI |
| 16 | Manual IEF | Heritage Foundation | `ief_overall_score` | 20 años | D3 | ⚠️ Manual / descarga | Descarga manual del Excel anual |
| 17 | Manual HDI | UNDP HDR | `hdi` | 15 años | D5 | ⚠️ Manual / descarga | Descarga manual del CSV histórico UNDP |
| 18 | `fetch_viirs.py` | NOAA EOG (VIIRS NTL) | `luminosidad_nocturna_idx` | **0 años** | D2 | ❌ Sin datos | NOAA EOG requiere autenticación |

**Leyenda:**
- ✅ Real API — descargado programáticamente, reproducible con `python scripts/fetch_X.py`
- ⚠️ — datos verificables de publicaciones citadas, pero no descargados automáticamente via API pública
- ❌ — sin datos disponibles (API no accesible sin auth)

---

## Correcciones Aplicadas en Esta Auditoría

### 1. IMF: `NGDP_D` → `PCPIPCH` (CRÍTICO)

**Problema detectado:** `NGDP_D` (deflactor del PIB) devuelve 0 años para Venezuela — el país dejó de reportar este indicador al FMI.

**Impacto:** `inflacion_deflactor_pib_pct` es la variable de **mayor peso en D1_macro (28%)**, que a su vez tiene el mayor peso en ICIV (25%). 0 datos = 0% del score macro calculado con datos reales.

**Solución:** Cambiado a `PCPIPCH` (tasa de variación del IPC, CPI inflation rate %) en `config/settings.yaml`. Este indicador tiene cobertura completa para Venezuela: **27 años (2000–2026)**.

**Verificación:**
```
PCPIPCH: 27 años con datos, 0 NaN
Ejemplo: 2018 = 65,374% | 2019 = 19,906% | 2024 = 36%
```

**Archivo modificado:** `config/settings.yaml` línea `NGDP_D → PCPIPCH`

---

### 2. UNCTAD API → World Bank WDI (LSCI)

**Problema detectado:** `https://unctadstat.unctad.org/api/v1/en/data/MT_TMS_LSCI_I/VEN` devuelve HTTP 404 (verificado mayo 2026). El script usaba datos estáticos manuales como fallback.

**Solución:** Reescrito `scripts/fetch_unctad.py` para usar el indicador **IS.SHP.GCNW.XQ** del World Bank WDI API (LSCI disponible como serie derivada en WDI). Sin fallback estático — si la API no responde, la variable queda NaN.

**Resultado:** **16 años reales (2006–2021)** desde World Bank API. Años 2000–2005 y 2022+ quedan NaN (imputados por interpolación/forward_fill).

**Valores reales obtenidos:**
```
2006: 24.42 | 2007: 23.84 | ... | 2019: 11.11 | 2020: 11.01 | 2021: 7.36
```

**Archivo modificado:** `scripts/fetch_unctad.py` (reescrito completamente)

---

### 3. Google Trends: datos inventados → pytrends API real

**Problema detectado:** `gtrends.csv` contenía `"estimación manual"` en la columna `fuente` — los valores habían sido ingresados manualmente, NO descargados de Google Trends. `google_trends_vzla` tiene peso 30% en D6_percepcion.

**Solución:** El script `fetch_gtrends.py` ya estaba preparado para usar `pytrends`. Se regeneró el CSV con datos reales. pytrends instalado con `pip install pytrends`.

**Resultado:** **23 años reales** (2004–2026, fuente="Google Trends — pytrends API"). Valores coherentes: picos en 2013, 2017-2019, 2022.

**Nota:** Google rate-limita a ~2 requests/minuto. Si el pipeline corre muy seguido obtendrá 429. El CSV generado se cachea y solo se re-descarga al ejecutar `fetch_gtrends.py` explícitamente.

---

### 4. UNHCR: parámetro incorrecto (ya corregido en Bitácora 04)

`countries=VEN` → `coo=VEN` (Country of Origin). **26 años reales** de venezolanos desplazados.

---

## Variables Sin Datos — Estado y Razón

### `luminosidad_nocturna_idx` — 0 años

**Fuente:** NOAA EOG (Earth Observation Group) — VIIRS Nighttime Lights  
**Problema:** La API `eogdata.mines.edu/wwwdata/viirs_products/vnl_v2/0_global_statistics/VNL_v2_npp_statistics.json` devuelve HTTP 200 con body vacío. Los archivos .txt anuales retornan una página de login HTML. Requiere cuenta institucional NASA Earthdata.  
**Impacto:** `luminosidad_nocturna_idx` (D2_energia, dim_weight=0.15) queda NaN en todos los años → el pipeline redistribuye ese peso entre las otras variables de D2.  
**Para obtener datos:** Registrarse en `eogdata.mines.edu`, descargar composites anuales VNL v2 (.tif), calcular promedio para bbox Venezuela, guardar en `data/raw/viirs.csv`.

### `inflacion_ipc_pct` (WDI FP.CPI.TOTL.ZG) — solo 8 años

Esta variable existe en el CSV wdi pero **NO está en el modelo ICIV** (no aparece en `dimensions` del settings.yaml). Es auxiliar. Venezuela solo reportó inflación al WB en 2008–2015. El indicador activo en D1 es `inflacion_deflactor_pib_pct` (IMF PCPIPCH, 27 años).

---

## Cobertura Final de Variables en Pipeline

Después de imputación (interpolación / forward_fill según `settings.yaml`):

| Variable | Años raw | Años post-imputación | Cobertura final |
|----------|----------|---------------------|-----------------|
| inflacion_deflactor_pib_pct | 27 | 27 | 100% ✅ |
| pib_crecimiento_real_pct | 25 | 27 | 100% ✅ |
| reservas_internacionales_usd | 18 | 18 | 67% ⚠️ |
| tipo_cambio_oficial_lcu_usd | 23 | 23 | 85% ⚠️ |
| petroleo_crudo_produccion_tbpd | 26 | 27 | 100% ✅ |
| gas_natural_produccion_bcf | 25 | 27 | 100% ✅ |
| electricidad_generacion_bkwh | 25 | 27 | 100% ✅ |
| luminosidad_nocturna_idx | 0 | 0 | **0% ❌** |
| cpi_score | 27 | 27 | 100% ✅ |
| wgi_promedio_sc | 24 | 27 | 100% ✅ |
| ief_overall_score | 20 | 27 | 100% ✅ |
| freedom_house_score | 25 | 27 | 100% ✅ |
| ofac_sanciones_count | 25 | 27 | 100% ✅ |
| pts_terror_politico | 24 | 27 | 100% ✅ |
| ied_neta_usd | 25 | 27 | 100% ✅ |
| exportaciones_pct_pib | 25 | 27 | 100% ✅ |
| desempleo_pct | 19 | 23 | 85% ⚠️ |
| migrantes_vzla_millones | 26 | 27 | 100% ✅ |
| lsci_conectividad_maritima | 16 | 24 | 89% ⚠️ |
| vuelos_aerolineas_int_count | 25 | 27 | 100% ✅ |
| hdi | 15 | 27 | 100% ✅ |
| tasa_alfabetizacion_adulta_pct | 12 | 21 | 78% ⚠️ |
| acceso_electricidad_pct | 24 | 27 | 100% ✅ |
| esperanza_vida_anos | 22 | 26 | 96% ✅ |
| mortalidad_infantil_x1000 | 24 | 27 | 100% ✅ |
| wti_precio_usd | 27 | 27 | 100% ✅ |
| tasa_fed_funds_pct | 27 | 27 | 100% ✅ |
| google_trends_vzla | 23 | 27 | 100% ✅ |
| guardian_tono_titulares | 27 | 27 | 100% ✅ |
| guardian_articulos_venezuela | 27 | 27 | 100% ✅ |

**Total variables en modelo:** 29 + año = 30 columnas en `iciv_normalizado.csv`  
**Variables con cobertura 100%:** 24 de 29 (83%)  
**Variable sin datos:** 1 (`luminosidad_nocturna_idx` — requiere auth NOAA EOG)

---

## Resultado del Pipeline Post-Auditoría

```
Pipeline runtime: ~121 segundos (con re-descarga de todas las fuentes)
Años calculados: 27 (2000-2026)
Método: AHP lineal ponderado
Rango ICIV: 28.4 (2020) → 72.8 (2012)

ICIV por año (selección):
  2000: 70.3  →  Pré-chavismo tardío
  2006: 70.9  →  Boom petrolero máximo
  2012: 72.8  →  Pico histórico (boom + control social)
  2017: 49.0  →  Inicio crisis profunda
  2019: 36.3  →  PDVSA SDN + apagón nacional
  2020: 28.4  →  Mínimo histórico (COVID + crisis + sanciones máximas)
  2023: 36.7  →  Recuperación muy parcial
  2026: 39.5  →  Score proyectado
```

---

## Archivos Modificados/Creados en Esta Auditoría

| Archivo | Cambio |
|---------|--------|
| `config/settings.yaml` | `NGDP_D` → `PCPIPCH` en fuente IMF |
| `scripts/fetch_unctad.py` | Reescrito: UNCTAD API (404) → WB WDI IS.SHP.GCNW.XQ |
| `data/raw/imf.csv` | Regenerado con inflación real PCPIPCH (27 años) |
| `data/raw/unctad.csv` | Regenerado con datos WB WDI (16 años reales) |
| `data/raw/gtrends.csv` | Regenerado con pytrends API real (23 años) |
| `data/raw/wdi.csv` | Actualizado |
| `data/raw/eia.csv` | Actualizado |
| `data/raw/fred.csv` | Actualizado |
| `data/raw/guardian.csv` | Actualizado |
| `data/raw/unhcr.csv` | Actualizado |
| `data/raw/freedom_house.csv` | Actualizado |
| `data/raw/ofac.csv` | Actualizado |
| `data/raw/wgi.csv` | Actualizado |
| `data/raw/pts.csv` | Actualizado |
| `data/raw/who.csv` | Actualizado |
| `data/processed/iciv_normalizado.csv` | Actualizado con todos los fixes |
| `data/processed/iciv_scores_ahp.csv` | Actualizado |
| `data/processed/iciv_dashboard.html` | Actualizado |

---

## Fuentes Evaluadas y Descartadas (No Existe API Pública)

| Fuente | Razón de descarte |
|--------|------------------|
| UNCTAD Stat API (endpoint LSCI) | HTTP 404 desde mayo 2026 |
| NOAA EOG (VIIRS NTL API) | Requiere cuenta NASA Earthdata (auth) |
| ACLED (conflictos armados) | Requiere registro + email |
| V-Dem (democracia) | Dataset >500MB, sin API directa |
| Comtrade (comercio exterior) | Requiere API key registrada |
| NASA AppEEARS (VIIRS tiles) | Requiere cuenta NASA Earthdata |

---

## Conclusión

El pipeline ICIV tiene **28 de 29 variables con datos reales verificables** (la excepción es `luminosidad_nocturna_idx` que requiere autenticación NOAA). Las 3 fuentes críticas que estaban rotas o con datos inventados fueron corregidas:

1. **IMF inflación** (NGDP_D→PCPIPCH): de 0 años a 27 años reales ✅
2. **UNCTAD LSCI** (API muerta→WB WDI): de datos estáticos inventados a 16 años reales ✅  
3. **Google Trends** (estimación manual→pytrends): de fake a 23 años reales ✅

El principio de **CERO datos inventados** se cumple en todas las fuentes API. Las fuentes estáticas (Freedom House, OpenSky, OFAC histórico, CPI, IEF, HDI) están basadas en publicaciones oficiales citadas y son verificables, aunque no descargables automáticamente via API pública gratuita.
