# Bitácora 04 — Auditoría de Datos Reales y Nuevas Fuentes

**Fecha:** 27 de abril de 2026  
**Objetivo:** Eliminar todos los datos inventados/estimados del pipeline y agregar nuevas fuentes verificadas.

---

## 1. Auditoría de Datos Inventados — Cambios Realizados

Durante una revisión exhaustiva del pipeline se detectaron datos estáticos fabricados (fallbacks/estimaciones manuales) en los siguientes scripts. **Todos fueron eliminados.** El principio es: si no hay dato real de la fuente, la variable queda NaN en el pipeline.

### Scripts modificados:

| Script | Datos eliminados | Estado actual |
|--------|-----------------|---------------|
| `fetch_gtrends.py` | `FALLBACK_DATA` dict (2000-2026, manual) | API real o RuntimeError |
| `fetch_viirs.py` | `VIIRS_DATA` dict (2000-2026, estimado) | API real o DataFrame vacío |
| `fetch_imf.py` | `_STATIC_DEFLATOR` + `_STATIC_DESEMPLEO` | Solo API IMF DataMapper |
| `fetch_wdi.py` | `_STATIC_RESERVAS` + `_STATIC_TIPO_CAMBIO` + `_STATIC_ALFABETIZACION` | Solo API WDI |
| `fetch_eia.py` | `_STATIC_OIL_TBPD` + `_STATIC_GAS_BCF` + `_STATIC_ELEC_BKWH` | Solo API EIA v2 |
| `fetch_unhcr.py` | `MIGRATION_DATA` dict (2000-2026, R4V estimado) | API real corregida |
| `fetch_viirs_states.py` | Importación de `VIIRS_DATA` (eliminada) | Retorna vacío si no hay CSV |
| `fetch_freedom_house.py` | Proyecciones 2025-2026 | Solo datos publicados 2000-2024 |
| `fetch_opensky.py` | Proyecciones 2025-2026 | Solo datos validados 2000-2024 |
| `fetch_ofac.py` | Proyecciones 2025-2026 | Solo datos registrados 2000-2024 |
| `fetch_unctad.py` | Proyecciones 2025-2026 | Solo datos UNCTAD 2000-2024 |

---

## 2. Correcciones de APIs — Bugs Encontrados y Resueltos

### 2.1 EIA API v2 — Formato de facets deprecado

**Problema:** Los 3 scripts de EIA usaban `facets[seriesId][]=INTL.57-1-VEN-TBPD.A`, que fue deprecado por EIA en la v2 de su API.

**Solución implementada:** Se creó la función `_parse_intl_series_id()` que parsea el formato legacy y genera los nuevos facets:
```python
facets[productId][]  = "57"   # Petróleo crudo
facets[activityId][] = "1"    # Producción
facets[countryRegionId][] = "VEN"
facets[unit][] = "TBPD"
```

**Resultado:** EIA ahora entrega datos reales:
- Petróleo: 26 años (2000-2024)
- Gas natural: 25 años (2000-2024)  
- Electricidad: 25 años (2000-2024)

### 2.2 WGI Bulk Download — URL 404

**Problema:** `WGI_csv.zip` devolvía 404 porque el Banco Mundial renombró el archivo.

**Solución:** Se actualizó `config/settings.yaml`:
- **Antes:** `WGI_csv.zip`  
- **Después:** `WGI_CSV.zip` (mayúsculas correctas)

**Resultado:** WGI descarga correctamente — 24 años de datos (2000-2023).

### 2.3 UNHCR API — Parámetro incorrecto

**Problema:** El código usaba `countries=VEN` que devuelve personas *residentes en Venezuela* (≈1 fila), no venezolanos desplazados al exterior.

**Solución:** Se cambió a `coo=VEN` (Country of Origin = Venezuela):
```python
# Antes (incorrecto):
url = "...?countries=VEN&year={START}:{END}"

# Después (correcto):
url = "...?coo=VEN&yearFrom={START}&yearTo={END}&limit=100"
```

**Resultado:** UNHCR entrega 26 años de datos reales (2000-2025) de venezolanos desplazados.

### 2.4 VIIRS/NOAA EOG — API Devuelve Body Vacío

**Problema:** La API JSON `VNL_v2_npp_statistics.json` devuelve HTTP 200 pero con body vacío. La segunda alternativa (archivos txt anuales) devuelve una página de login HTML.

**Estado:** La variable `luminosidad_nocturna_idx` queda como NaN. El pipeline maneja esto correctamente con el mensaje de error apropiado.

**Alternativa manual:** Descargar composites anuales desde `https://eogdata.mines.edu/products/vnl/` (requiere cuenta institucional).

---

## 3. Nuevas Fuentes Implementadas

### 3.1 Political Terror Scale (PTS) — `scripts/fetch_pts.py`

**Fuente:** Political Terror Scale 2024 — Gibney, Cornett, Wood, Haschke & Arnon  
**URL:** `https://www.politicalterrorscale.org/Data/Files/PTS-2024.csv`  
**Acceso:** Descarga directa, sin autenticación  

**Metodología:**
- Promedio de PTS_A (Amnesty Intl), PTS_H (Human Rights Watch), PTS_S (State Dept)
- Escala 1–5: 1 = país sin represión sistemática; 5 = terror generalizado
- Solo se promedian los indicadores disponibles cada año (PTS_H solo desde 2013)

**Cobertura Venezuela:** 24 años (2000–2023)

**Serie histórica notable:**
- 2000: 2.50 → 2020: 5.00 (máximo histórico, durante pandemia+represión DGCIM)
- 2023: 4.33 (continúa en nivel de represión severa)

**Integración:**
- Dimensión: D3 Institucional, `dim_weight = 0.10`
- Dirección: NEGATIVE (mayor score = peor clima inversión)
- Loader: `PTSLoader` en `src/iciv/data/loaders/pts_loader.py`
- Archivo salida: `data/raw/pts.csv`

### 3.2 WHO Global Health Observatory — `scripts/fetch_who.py`

**Fuente:** WHO GHO OData API — `https://ghoapi.azureedge.net/api`  
**Acceso:** API pública, sin autenticación requerida  

**Indicadores descargados:**

| Código GHO | Variable ICIV | Cobertura |
|------------|--------------|-----------|
| `WHOSIS_000001` | `esperanza_vida_anos` | 22 años (2000–2021) |
| `MDG_0000000001` | `mortalidad_infantil_x1000` | 24 años (2000–2023) |

**Datos notables Venezuela:**
- Esperanza de vida cayó de 74.7 años (2005-2006) a 71.2 años (2021) — retroceso de 25 años de progreso
- Mortalidad infantil mínimo: 14.3 x1000 (2008); máximo reciente: 21.5 x1000 (2016+)
- La reversión post-2015 es la más pronunciada de América Latina (ENCOVI/IIES-UCAB)

**Nota:** Datos post-2016 son estimaciones OMS/IGME (Venezuela suspendió reportes epidemiológicos 2016-2019)

**Integración:**
- Dimensión: D5 Capital Humano
  - `esperanza_vida_anos`: `dim_weight = 0.20`, dirección POSITIVE
  - `mortalidad_infantil_x1000`: `dim_weight = 0.10`, dirección NEGATIVE
- Loader: `WHOLoader` en `src/iciv/data/loaders/who_loader.py` (pivota formato largo → ancho)
- Archivo salida: `data/raw/who.csv`

---

## 4. Fuentes Evaluadas y Descartadas

Las siguientes fuentes se evaluaron pero no se implementaron por las razones indicadas:

| Fuente | Razón de descarte |
|--------|------------------|
| ACLED (conflictos) | Requiere registro obligatorio (key + email) |
| V-Dem (democracia) | Dataset >500MB, sin API directa; requiere procesamiento local |
| NASA VIIRS/AppEEARS | Requiere cuenta NASA Earthdata (registro obligatorio) |
| Comtrade (comercio) | Requiere API key, cuotas limitadas sin registro |
| PRIO-GRID (violencia) | Formato shapefile, requiere procesamiento GIS |

---

## 5. Ajuste de Pesos en Dimensiones

Con la adición de nuevas variables, se rebalancearon los pesos intra-dimensión para que sumen 1.0:

### D3 Institucional (antes 5 variables → ahora 6):

| Variable | Peso anterior | Peso nuevo |
|----------|-------------|-----------|
| cpi_score | 0.28 | 0.25 |
| wgi_promedio_sc | 0.28 | 0.25 |
| ief_overall_score | 0.20 | 0.18 |
| freedom_house_score | 0.16 | 0.14 |
| ofac_sanciones_count | 0.08 | 0.08 |
| **pts_terror_politico** | — | **0.10** |
| **Total** | **1.00** | **1.00** |

### D5 Capital Humano (antes 3 variables → ahora 5):

| Variable | Peso anterior | Peso nuevo |
|----------|-------------|-----------|
| hdi | 0.40 | 0.30 |
| tasa_alfabetizacion_adulta_pct | 0.30 | 0.20 |
| acceso_electricidad_pct | 0.30 | 0.20 |
| **esperanza_vida_anos** | — | **0.20** |
| **mortalidad_infantil_x1000** | — | **0.10** |
| **Total** | **1.00** | **1.00** |

---

## 6. Estado del Pipeline Post-Cambios

```
Fuentes activas (18 loaders):
  WDI, WGI, EIA, IMF, CPI, IEF, HDI, Guardian, FRED, Freedom House,
  UNHCR, OFAC, GTrends, VIIRS*, UNCTAD, OpenSky, PTS, WHO

  * VIIRS: sin datos (NOAA EOG requiere autenticación); variable NaN.

Variables en el modelo: 29 (más año)
Dimensiones: 6 (D1-D6)
Período: 2000-2026 (27 años)

ICIV AHP — Rango histórico: 29.0 (2020) → 74.2 (2000)
Pipeline runtime: ~5 segundos (datos en caché)
```

---

## 7. Archivos Modificados

| Archivo | Tipo de cambio |
|---------|---------------|
| `scripts/fetch_unhcr.py` | Bug fix: parámetro API correcto |
| `scripts/fetch_pts.py` | **NUEVO** |
| `scripts/fetch_who.py` | **NUEVO** |
| `src/iciv/config/settings.py` | +2 rutas: `raw_pts`, `raw_who` |
| `src/iciv/data/models/indicators.py` | +2 SourceIDs: PTS, WHO |
| `src/iciv/data/catalog.py` | +3 variables; pesos rebalanceados en D3 y D5 |
| `src/iciv/data/loaders/pts_loader.py` | **NUEVO** |
| `src/iciv/data/loaders/who_loader.py` | **NUEVO** |
| `src/iciv/data/loaders/__init__.py` | +PTSLoader, +WHOLoader, ALL_LOADERS actualizado |
| `config/settings.yaml` | +sources PTS/WHO; pesos D3/D5 actualizados; imputation rules |
| `main.py` | +fetch_pts, +fetch_who en fase_fetch() |
