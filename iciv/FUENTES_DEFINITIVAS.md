# Fuentes de Datos Definitivas — ICIV Venezuela
**Última actualización:** 12 mayo 2026 — Sesión 10

> **Principio fundamental:** Solo fuentes **internacionales** con **reconocimiento académico** comprobable. **NUNCA** fuentes oficiales del gobierno venezolano (BCV, INE, Conatel) ya que su credibilidad estadística internacional está cuestionada (Hanke 2018; Vera 2017).

---

## ✅ FUENTES INTEGRADAS Y FUNCIONANDO (28)

### ⭐ NUEVO sesión 11 — OWID Extras (redistribución oficial)

| Variable | Origen real | Frecuencia | Cobertura ganada |
|----------|-------------|-----------|------------------|
| `exportaciones_pct_pib` | World Bank vía OWID | Anual | hasta 2024 |
| `desempleo_pct` | **IMF WEO Apr 2026 vía OWID** | Anual + proyección | **hasta 2025 (5.307%)** |
| `esperanza_vida_anos` | UN WPP vía OWID | Anual | hasta 2023 |
| `mortalidad_infantil_x1000` | UN IGME vía OWID | Anual | hasta 2023 |

**Por qué OWID:** Redistribuye datasets oficiales (WB, IMF, UN) con licencia CC-BY abierta
y ciclos de actualización propios — a veces **más recientes** que los APIs originales.
Académicamente aceptable: ~10k citas en Google Scholar.



### Organismos multilaterales (10)

| Fuente | Variables | Frecuencia | Método | Citas académicas |
|--------|-----------|-----------|--------|------------------|
| **World Bank WDI** | 10 variables macro/social | Anual | API REST | >500k citas; estándar de facto |
| **World Bank WGI** | wgi_promedio_sc (6 sub-indicators) | Anual | ZIP bulk | Kaufmann et al. (2010), >40k citas |
| **IMF DataMapper** | inflación, desempleo, BCA, PIB crec | Anual + WEO Apr/Oct | API REST | Estándar internacional |
| **EIA (US Energy Info Admin)** | petroleo, gas, electricidad | **Anual + Mensual** | API v2 (key) | Referencia mundial energía |
| **EIA International Monthly** ⭐ | petroleo_crudo VEN (2020-2026) | **Mensual** | API v2 | Sesión 10 — nowcast |
| **WHO Global Health Observatory** | esperanza vida, mortalidad infantil | Anual | API REST | OMS oficial |
| **UNHCR Refugee Statistics** | migrantes_vzla_millones | Anual (data mensual) | API pública | ONU oficial |
| **UNCTAD/WB LSCI** | conectividad marítima | Anual | API WB | UNCTAD legacy |
| **UNDP HDR** | hdi | Anual (sep) | OWID redistribution | PNUD oficial |
| **FAO/OWID** | calorías per capita | Anual | OWID redistribution | FAOSTAT oficial |

### Institutos académicos / NGOs reconocidos (12)

| Fuente | Variables | Frecuencia | Método | Aceptación académica |
|--------|-----------|-----------|--------|---------------------|
| **Transparency International** | cpi_score | Anual (ene) | CSV manual | Estándar corrupción, >20k citas |
| **Heritage Foundation** | ief_overall_score | Anual (ene) | Excel manual | Estándar libertad económica |
| **Freedom House** | freedom_house_score | Anual (feb) | Web scraping | FitW estándar libertades |
| **V-Dem Institute** | vdem_libdem_index | Anual | OWID CSV | >15k citas, Univ. Gothenburg |
| **World Justice Project** | wjp_rule_of_law | Anual (oct) | OWID CSV | Estándar Rule of Law |
| **Reporters Without Borders** | rsf_press_freedom | Anual (may) | OWID + Statista | Estándar libertad de prensa |
| **Bertelsmann Stiftung BTI** | bti_governance_index | Bienal (mar) | Excel | >10k citas, gobernanza |
| **Fund for Peace FSI** | fragile_states_index | Anual | PDF manual | Estándar fragilidad estatal |
| **PTS (Gibney et al.)** | pts_terror_politico | Anual | CSV directo | Political Terror Scale académico |
| **Global Hunger Index** | ghi_score | Anual | OWID CSV | Welthungerhilfe/Concern |
| **Uppsala UCDP** | ucdp_conflicto_idx | Anual | CSV ZIP | Pettersson et al., estándar |
| **ACLED** (req. API key) | acled_eventos_violencia | Semanal | API REST | Académico, requiere registro |

### Fuentes US gobierno + medios + datos satelitales (5)

| Fuente | Variables | Frecuencia | Método | Aceptación |
|--------|-----------|-----------|--------|------------|
| **FRED St. Louis Fed** | WTI, Fed Funds | Diaria + Mensual | CSV directo | Reserva Federal oficial |
| **US Treasury OFAC** | ofac_sanciones_count | Diario (snapshot) | SDN CSV | Citas en derecho internacional |
| **The Guardian** | tono + volumen artículos | Diaria (agregada) | API key | Newspaper of record UK |
| **NOAA/Li et al. VIIRS** | luminosidad_nocturna_idx | Anual | Raster Figshare | Estándar nighttime lights |
| **ILOSTAT (via WB proxy)** | empleo informal | Anual | WB API | ILO/OIT oficial |

---

## ❌ FUENTES DESCARTADAS — NO REINTRODUCIR

### Fuentes venezolanas (gobierno) — RAZÓN: credibilidad cuestionada

| Fuente | Por qué descartada |
|--------|--------------------|
| **BCV (Banco Central Venezuela)** | Manipulación estadística documentada 2014-2019. Hanke (2018) calcula inflación real 10x mayor que la oficial. **Removida en sesión 10**. |
| **INE Venezuela** | No publica datos macroeconómicos desde 2015. Datos sociales suspendidos. |
| **Ministerio Energía/PDVSA** | Datos contradichos por OPEP, EIA, IEA. |
| **CONATEL** | Reportes irregulares, definiciones cambiantes. |

### Fuentes con API rota/inaccesible — RAZÓN: técnica

| Fuente | Problema detectado | Workaround posible |
|--------|--------------------|--------------------|
| **CEPALSTAT (UN ECLAC)** | API documentada retorna 404 en todos los endpoints | Esperar API formal o descarga manual |
| **GDELT Project** | `api.gdeltproject.org` ConnectTimeout desde esta red | Otra red o proxy |
| **Google Trends (pytrends)** | HTTP 429 rate limit permanente esta IP | SerpAPI (~$50/mes) o VPN |
| **Heritage IEF scraping** | 403 Forbidden a partir de mayo 2026 | Descarga manual Excel anual |
| **OpenSky Network ADS-B** | Sin historial >7 días | Flightradar24 ($$) o eliminar variable |
| **Basel AML Index** | URLs Excel todas 404 | Descarga manual desde baselgovernance.org |
| **UN Comtrade v1** | Requiere API key (401 sin auth) | Registrar key gratuita |
| **IMF IFS SDMX** | `dataservices.imf.org` DNS no resuelve | Usar IMF DataMapper en su lugar |

### Fuentes evaluadas y RECHAZADAS por baja calidad

| Fuente | Por qué rechazada |
|--------|-------------------|
| **Trading Economics** | Paywall; metodología propietaria opaca |
| **Ecoanalítica** | Datos no publicados sistemáticamente; solo Twitter/X |
| **Stratfor** | Análisis cualitativo, no cuantitativo verificable |
| **El Universal / El Nacional** | Medios, no datos primarios |
| **Bloomberg Terminal** | Costo prohibitivo + licencia restrictiva |

---

## 🟡 FUENTES POR EXPLORAR (no críticas)

| Fuente | Variable potencial | Esfuerzo estimado |
|--------|-------------------|-------------------|
| **OPEC Monthly Oil Market Report (PDF)** | producción crudo mensual (independent secondary sources) | 4h (pdfplumber + regex) |
| **JODI Oil/Gas** | datos mensuales oil/gas | 2h (CSV directo si URL correcta) |
| **ENCOVI (UCAB)** | pobreza, empleo informal, inseguridad alimentaria | 4h (PDFs anuales) |
| **OVCS (Observatorio Conflictividad)** | protestas mensuales | 3h (web scraping mensual) |
| **OVF (Observatorio Finanzas)** | inflación mensual independiente | 2h (scraping web) |
| **Wayback Machine (OFAC)** | snapshots históricos sanciones | 3h (CDX API) |

---

## 📐 TÉCNICAS UTILIZADAS

### 1. APIs REST públicas (con/sin key)
- **WDI, IMF, EIA, FRED, Guardian, UNHCR, WHO, OFAC, WGI** — endpoints REST documentados
- Cache local en `data/raw/*.csv` para reproducibilidad

### 2. Web scraping
- **Freedom House:** `requests` + `BeautifulSoup` con regex sobre HTML
- **Heritage IEF:** descarga manual (sitio bloquea bots con 403)

### 3. Procesamiento de archivos especiales
- **VIIRS:** descarga Figshare (TIF) + extracción raster con `rasterio` por bbox GADM
- **BTI Excel:** `pandas.read_excel` con detección automática de hojas por año
- **FSI PDFs:** transcripción manual a CSV (data/raw/fsi_manual.csv)
- **CPI/IEF/HDI Excel:** transcripción manual a CSV con citación

### 4. Datos longitudinales agregados
- **EIA Monthly → Annual:** promedio de meses disponibles + metadata `n_meses` para transparencia
- **The Guardian:** agregación VADER sobre articulos diarios

### 5. Datos redistribuidos por OWID
- Our World in Data **republishes** V-Dem, WJP, RSF, GHI, HDI bajo licencia abierta
- Más estables que los sitios originales (que cambian URLs frecuentemente)

---

## 🎯 PROPUESTA SESIÓN 10: ICIV PULSE (NOWCAST TRIMESTRAL)

**Idea académica:** Mantener el ICIV anual como indicador principal (28 variables) y crear un **sub-indicador trimestral** (ICIV Pulse) con solo variables de alta frecuencia para el año en curso.

### Variables del ICIV Pulse propuesto:

| Variable | Fuente | Frecuencia nativa | Peso ICIV original |
|----------|--------|-------------------|--------------------|
| WTI precio | FRED DCOILWTICO | Diario | 4% |
| Fed Funds | FRED FEDFUNDS | Mensual | 4% |
| Producción petróleo VEN | EIA monthly | Mensual | 10% |
| Sentimiento Guardian | Guardian API | Diario | 5% |
| OFAC sanciones | Treasury SDN | Diario (snapshot) | 3% |
| Migrantes UNHCR | UNHCR API | Mensual | 6% |

**Total cobertura:** ~32% del peso AHP del ICIV, pero **observable mensualmente**.

**Justificación académica:** Stock-Watson (2002, JBES) — "nowcasting" en macroeconomía usa indicadores de alta frecuencia para estimar variables de baja frecuencia. Aplicación estándar.

**Implementación:** pendiente para sesión 11 (~6h).

---

## 📅 CRONOGRAMA DE PUBLICACIÓN DE FUENTES

| Mes 2026 | Fuente publicada | Impacto en cobertura |
|----------|------------------|----------------------|
| Mayo (ya) | RSF, BTI, ICIV scores actuales | — |
| Junio | EIA monthly Feb/Mar 2026 | +1% D2 nowcast 2026 |
| Septiembre | **WGI 2025**, **HDI 2024** | **+12% cobertura 2025** |
| Octubre | IMF WEO 2026 final | +2% D1 2025-2026 |
| Diciembre | **WDI 2025** (IED, exports, GDP) | **+10% D4 2025** |
| Enero 2027 | **CPI 2026**, **TI/Heritage 2027** | **+6% D3 2026** |
| Febrero 2027 | **FH FitW 2027** | +3% D3 2026 |

**Proyección:** cobertura 2025 → 75-80% en sep-2026, 90%+ en ene-2027.
**Proyección:** cobertura 2026 → 50-55% en dic-2026, 70%+ en feb-2027.

---

## ✅ CHECKLIST DE INTEGRIDAD

- [x] CERO datos artificiales/inventados
- [x] CERO fuentes gubernamentales venezolanas (BCV removido sesión 10)
- [x] CERO fallbacks estáticos (`_STATIC_*`, `_HISTORICAL_*` borrados)
- [x] Imputación solo en gaps internos (`limit_area="inside"`)
- [x] sector_radar sin imputación artificial (corregido sesión 10)
- [x] Cobertura per-año publicada en cada score
- [x] Cada CSV tiene columna `fuente` con URL/cita
- [x] Pipeline reproducible end-to-end con `python main.py`

---

*Documento definitivo de fuentes — reemplaza FUENTES_WEBSCRAPPING.md y RECOMENDACIONES_DATOS_FRESCOS.md*
