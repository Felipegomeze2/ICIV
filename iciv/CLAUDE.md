# ICIV — Reglas del Proyecto para Claude

## ⛔ REGLA ABSOLUTA — DASHBOARD: UN SOLO ARCHIVO

**Esta regla no tiene excepciones. No crear copias en ningún otro lugar.**

```
ÚNICO dashboard permitido:
  C:\Users\pipeg\Documents\Claude\Projects\
  Investigación Indicador Macroeconomico Venezuela\iciv_dashboard.html

En main.py:  out_path = _ROOT.parent / "iciv_dashboard.html"
  _ROOT      = iciv/           (carpeta con main.py)
  _ROOT.parent = raíz proyecto (Investigación Indicador Macroeconomico Venezuela/)

NUNCA crear:
  iciv/iciv_dashboard.html
  iciv/data/processed/iciv_dashboard.html
  ni ninguna otra copia en ningún subdirectorio
```

---

## ⛔ REGLA PRINCIPAL — CERO DATOS FALSOS

**Esta regla no tiene excepciones. No existe ninguna situación que justifique violarla.**

```
SI un indicador no tiene dato real de una fuente verificable → la variable queda NaN.
NO se inventa ningún número.
NO se crea ningún fallback estático.
NO se estima manualmente ningún valor.
NO se proyecta ni se interpola como dato primario.
```

### Lo que significa en la práctica:

| ✅ PERMITIDO | ❌ PROHIBIDO |
|-------------|-------------|
| Dato de API pública (WB, IMF, EIA, FRED...) | Diccionario Python con valores inventados |
| Dato de descarga directa CSV (PTS, CPI, HDI...) | `_STATIC_DATA = {2000: X, 2001: Y, ...}` como fuente primaria |
| Dato de scraping de publicación oficial citada | Estimaciones con "parece razonable" |
| NaN explícito cuando no hay dato | Proyecciones disfrazadas de datos históricos |
| Imputación (interpolate/ffill) solo para años intermedios entre datos reales | Llenar años sin ningún dato real con ffill de años inventados |
| Nota en CSV que dice cuál es la fuente real | `fuente = "estimación manual"` |

### Verificación rápida:
```python
# ¿Este dato es real? Pregúntate:
# 1. ¿Puedo reproducirlo corriendo `python scripts/fetch_X.py` ahora mismo?
# 2. ¿La columna "fuente" en el CSV dice una URL o publicación citable?
# 3. ¿Si borras el CSV y vuelves a correr el script, obtienes el mismo número?
# Si la respuesta a cualquiera es NO → el dato es sospechoso
```

---

## Estado del Proyecto (mayo 2026) — PIPELINE COMPLETO ✅

### Lo que está completo ✅

**Pipeline ETL:**
- 29 loaders, 27 scripts fetch activos
- 40 variables en 6 dimensiones (catálogo ampliado sesión 3)
- Imputación honesta: solo interpola/ffill entre datos reales existentes
- VIIRS por estado: raster real Li et al. Figshare (sin factores inventados)
- Aggregator corregido: variables con 0 valores no-NaN se excluyen y sus pesos se redistribuyen

**Pipeline corriendo en sesión 4 — fuentes reparadas:**
- V-Dem: OWID `liberal-democracy.csv` → 26 años reales
- WJP: OWID `rule-of-law-index.csv` → 26 años reales
- RSF: OWID `press-freedom-rsf.csv` → 9 años (2013-2021)
- BTI: bti-project.org Excel, parser reescrito (sheets por año) → 10 años (bienal 2006-2024)
- GHI: OWID `global-hunger-index.csv` → 4 años
- FAO: OWID `food-supply-kcal.csv` (FAOSTAT API 521) → 24 años
- ILOSTAT: WB Vulnerable Employment proxy (`SL.EMP.VULN.ZS`) → 26 años
- UCDP: GED v24.1 CSV directo desde ZIP sin auth → 24 años

**Modelo:**
- Pesos AHP validados (CR=0.0081 < 0.10), SI=0.0376 (robusto)
- Normalización Min-Max (2000–2026 como referencia)
- log10 aplicado a: tipo_cambio y inflacion_deflactor_pib_pct (comprimir 4 órdenes de magnitud)
- Scores ICIV AHP: 23.4 (2020, mínimo) → 72.2 (2012, máximo) [ver sesión 5 para corrección metodológica]

**Dashboard (iciv_dashboard.html):**
- 13 secciones navegables en HTML interactivo
- Score actual, evolución, dimensiones, metodología AHP
- SATV alertas tempranas, correlación ICIV→IED, sanciones OFAC (D3.js)
- Mapa Venezuela: datos NTL reales por estado (Li et al. raster), fallback al último año disponible para 2025-2026
- Escenarios 2027–2030, Monte Carlo 10k, indicadores líderes, validación
- Dashboard copiado automáticamente a la raíz del proyecto

**Correcciones mayo 2026 (sesión 1):**
- IMF: NGDP_D → PCPIPCH (0 años → 27 años reales)
- UNCTAD: API muerta → WB WDI IS.SHP.GCNW.XQ (16 años reales)
- Google Trends: datos inventados → pytrends real (23 años)
- VIIRS: NOAA EOG (Keycloak roto) → Li et al. Figshare (público, sin auth) — 25 años reales

**Correcciones mayo 2026 (sesión 2):**
- inflacion_deflactor_pib_pct: log10 transform (49.4% → score 84, no 99.4)
- viirs_states.py: reescrito — extrae raster real por bbox estatal (sin _DIFFERENTIAL inventados)
- NaN vs 0 en dashboard: NaN muestra "sin dato" en gris, 0 muestra "peor histórico"
- Mapa 2025-2026: fallback al último año con dato satelital (no más negro total)
- Eliminados: fetch_viirs_earthaccess.py, fetch_viirs_gee.py (obsoletos)
- Dashboard copiado a raíz del proyecto automáticamente
- fetch_opensky.py: eliminado _STATIC_AIRLINES. vuelos_aerolineas_int_count = NaN
- fetch_ofac.py: eliminado HISTORICAL_OFAC. ofac_sanciones_count = 1 año real
- GapImputer: limit_direction='both' → limit_area='inside' (evita extrapolación en bordes)

**Ampliación mayo 2026 (sesión 3) — Fuentes adicionales:**
- 11 nuevas variables en catalog.py y dimensions.py (D3, D4, D5 ampliados)
- 11 nuevos loaders en extended_loaders.py
- 11 nuevos scripts fetch (vdem, fragile_states, wjp, rsf, bti, ghi, acled, ilostat, ucdp, fao, basel_aml)
- settings.py: 11 nuevos raw_* paths
- aggregator.py corregido: columnas toda-NaN excluidas con redistribución de pesos
- D3 institucional: 5 vars → 13 vars (suma correcta 1.00), scores ahora calculan correctamente
- D4 comercial: 4 vars → 7 vars (lsci, remesas, vuelos añadidos)
- D5 capital humano: 3 vars → 8 vars (salud, GHI, FAO, ILO añadidos)

**Correcciones mayo 2026 (sesión 4) — Scripts reparados:**
- fetch_vdem.py: OWID GitHub URL 404 → OWID grapher CSV (`liberal-democracy.csv`) → 26 años
- fetch_wjp.py: OWID GitHub URL 404 → OWID grapher CSV (`rule-of-law-index.csv`) → 26 años
- fetch_rsf.py: OWID GitHub URL 404 → OWID grapher CSV (`press-freedom-rsf.csv`) → 9 años
- fetch_ghi.py: OWID GitHub URL 404 → OWID grapher CSV (`global-hunger-index.csv`) → 4 años
- fetch_fao.py: FAOSTAT 521 Server Error → OWID grapher CSV (`food-supply-kcal.csv`) → 24 años
- fetch_ilostat.py: API 404 → WB Vulnerable Employment proxy (`SL.EMP.VULN.ZS`) → 26 años
- fetch_ucdp.py: REST API 401 → GED CSV ZIP directo sin auth → 24 años
- fetch_bti.py: Excel mal parseado (columnas año en sheets no cols) → reescrito sheet-per-year → 10 años
- Todos los scripts: cadenas `or` con DataFrames → reemplazadas por bucle `for attempt in [...]: if not empty: break`

**Correcciones y mejoras mayo 2026 (sesión 5) — Metodología temporal + MC:**

FSI:
- `data/raw/fsi_manual.csv` creado con 19 años (2006–2024) extraídos de PDFs oficiales Fund for Peace
- fragile_states_index: 0 años → 19 años reales. Fuente: Fund for Peace fragilestatesindex.org
- fetch_fragile_states.py ya tenía _try_manual_csv() funcionando — simplemente se creó el CSV

Corrección crítica del aggregator (metodología de cobertura temporal):
- `_score_dimension()`: antes hacía `fillna(col_median)` para variables con NaN en un año específico
- BUG: esto "inventaba" datos para años fuera del rango de cobertura de cada variable
- FIX: ahora excluye per-year NaN variables y redistribuye pesos para ese año específico
- FIX: añade columna `cobertura_pct` al output: fracción del peso ICIV total con dato real ese año
- Resultado: 2026 score = 34.41 (22% cobertura, provisional) en lugar de 52.77 artificial
- Resultado: 2024 score = 30.84 (75% cobertura) = referencia confiable
- Dashboard: usa último año con cobertura ≥60% como score de referencia, muestra warning para años preliminares
- Dashboard: gráfico histórico marca puntos de baja cobertura con símbolo distinto (rombo naranja)

Monte Carlo recalibrado:
- BUG anterior: shocks = sum(AHP_weight × var_shock) → σ_efectiva ≈ 2 pts/año → bandas planas ±6 pts
- FIX: ruido calibrado sobre σ_hist del ICIV completo (2000–2024) ≈ 5.43 pts/año → bandas realistas
- FIX: OLS trend solo usa años confiables (cobertura ≥60%) para evitar distorsión de años parciales
- FIX: ScenarioEngine usa cobertura_pct si disponible en df_scores
- Resultado: P5–P95 spread en 2030 = 35.6 pts (antes: 12.9 pts planos)
- Probabilidades calibradas a datos: P(rec>45 en 2030)=13.8%, P(col<25 en 2030)=23.8%
- ICIV scores (2024, referencia): 30.84 pts → Riesgo Moderado-Alto

Scores ICIV AHP corregidos: 23.4 (2020, mínimo) → 72.2 (2012, máximo)
Scores sesión 8: 2024=31.06 (76% cob.), 2025=21.53 (49.5% cob.), 2026=41.88 (25.9% cob.)

**Correcciones mayo 2026 (sesión 13) — 🚀 ICIV Pulse Mensual + ML Forecast:**

⭐ ICIV DUAL: Anual (oficial) + Pulse Mensual (co-indicador high-frequency)
- Decisión arquitectónica: MISMO dashboard con 3 bloques diferenciados visualmente
  - Bloque A: ICIV Anual (secciones 1-9, lo existente)
  - Bloque B: ICIV Pulse Mensual + Componentes (secciones 10-11)
  - Bloque C: Forecast ML (sección 12)
  - + Noticias + Bibliografía
- Nav con separadores visuales │ entre bloques

🆕 PulseAggregator (`src/iciv/index/pulse_aggregator.py`):
- 12 variables internacionales high-frequency (ninguna VEN gov)
- Pesos AHP renormalizados sobre subconjunto disponible
- Variables: WTI, Brent, Fed, USD, VIX, UST10Y, petróleo VEN EIA monthly,
  OFAC, migrantes UNHCR, Guardian artículos + tono
- Min-Max normalización + inversión automática (var negativas)
- Si <30% peso disponible → NaN honesto (no fabricar)
- Output: 77 meses 2020-01 a 2026-05, rango 41.8-74.4
- Cobertura promedio 73.6%, 73 meses con cobertura ≥70%

🆕 Fetchers monthly nuevos:
- `scripts/fetch_fred_monthly.py`: 6 series FRED diarias → mensual (461 filas)
- `scripts/fetch_guardian_monthly.py`: 154 filas mensuales (artículos + VADER)
- EIA monthly ya existía de sesión 10

🤖 Machine Learning (`src/iciv/ml/pulse_forecast.py`):
- Modelo A: SARIMA(1,1,2)(1,1,1,12) — forecast 6 meses con bandas 80% y 95%
- Modelo B: OLS Pulse→ICIV Anual — nowcasting Stock-Watson (2002)
- Validación honesta con Leave-One-Out Cross-Validation
- Auto-selección orden SARIMA por AIC (3 candidatos)
- Auto-ajuste features según n: 2 features si n<11, 5 si n>=11 (anti-overfit)
- Resultados actuales: SARIMA AIC=319.26 funcionando;
  Nowcast R²_train=0.021, R²_LOO_CV=-5.18 (honestamente: necesita más data,
  el modelo no generaliza con solo 5 años Pulse — declarado al usuario)

📊 Nuevas secciones dashboard:
- §10 "Pulse Mensual" — gauge + serie 2020-2026 + comparación vs Anual
- §11 "Componentes Pulse" — 12 series normalizadas con leyenda interactiva + tabla pesos
- §12 "Forecast ML" — stats SARIMA/Nowcast, predicción año actual, fan chart con bandas confianza,
  tabla coeficientes OLS

📋 Nuevo documento: `ANALISIS_FRECUENCIA_TEMPORAL.md`
- Auditoría completa: solo 12 de 38 vars son mensualizables
- Justificación académica del enfoque dual (Stock-Watson, Aruoba-Diebold-Scotti, GDPNow)
- Razones para rechazar enfoque A (interpolación) y enfoque B (MIDAS)

Pipeline runtime: 14.9s (sin fetch, incluye Pulse+ML+dashboard)
Nav final: 14 secciones en 3 bloques visualmente diferenciados

**Mejoras mayo 2026 (sesión 14) — Venezuela Hoy + Pulse extendido + root fix:**

🆕 6ª PESTAÑA: "Venezuela Hoy" (bloque `monitor`)
- Panel de 16 indicadores clave con datos reales de alta frecuencia + anuales
- Hero cards: ICIV Anual (score, label, delta, cobertura) + Pulse Mensual (score, mes, delta, cobertura)
- Grid 12 indicadores: WTI, Brent, Petróleo VEN, PIB crecimiento, Inflación, Freedom House,
  CPI, WGI, Migrantes UNHCR, HDI, VIX, UST10Y
- Datos actuales: WTI=$102.62 (May 2026), Brent=$107.98, Petróleo VEN=844 TBPD (Ene 2026),
  Inflación VEN=387.4% (2026 IMF), PIB=+4.0% (2026 IMF), FH=13/100, CPI=10/100
- Fuentes: FRED monthly, EIA monthly, IMF CSV (sin log10), df_raw anuales
- Nota: inflación se lee del CSV crudo IMF (no del master con log10)
- `ven_hoy_json` embebido en dashboard, IIFE JS renderiza grid en tiempo de carga

📅 PULSE HISTÓRICO EXTENDIDO: 2020→2010
- `scripts/fetch_fred_monthly.py`: PULSE_START_YEAR=2020→2010 → 1,181 filas (197 meses)
- `scripts/fetch_guardian_monthly.py`: PULSE_START_YEAR=2020→2010 → 394 filas (197 meses)
- `src/iciv/index/pulse_aggregator.py`: PULSE_START_YEAR=2020→2010
- Resultado: 197 meses calculados (2010-01 a 2026-05), rango 31.2–91.4
  (antes: 77 meses 2020-2026, rango 41.8–74.4)
- EIA monthly ya cubría desde 2000; OFAC/UNHCR sin historial pre-2020 → NaN honesto,
  pesos redistribuidos por el aggregator para años sin esas variables
- 193 de 197 meses con cobertura ≥70%

🔧 FIX ROOT COPY: dashboard SOLO en iciv/
- `root_copy = _ROOT.parent / "iciv_dashboard.html"` → escribía en carpeta PADRE de iciv/
- FIX: `root_copy = _ROOT / "iciv_dashboard.html"` → escribe en iciv/ (raíz del proyecto)
- data/processed/iciv_dashboard.html sigue existiendo como backup
- iciv/iciv_dashboard.html es el archivo principal (470 KB)

Pipeline runtime: 17.7s (sin fetch, 197 meses Pulse + SARIMA + dashboard)
Nav final: 15 secciones en 4 bloques (Anual / Pulse Mensual / Forecast ML / Venezuela Hoy)

**Reestructuración narrativa mayo 2026 (sesión 15) — Dashboard de 5 bloques con Pulse como protagonista:**

Dashboard completamente reestructurado: de 6 bloques técnicos a 5 bloques narrativos que cuentan una historia:

Estructura anterior (técnica, por fuente):
  ICIV Anual | Pulse Mensual | Forecast ML | Venezuela Hoy | Noticias | Bibliografía

Nueva estructura narrativa (pregunta → respuesta):
  INICIO | HISTORIA | DIAGNÓSTICO | PROYECCIÓN | METODOLOGÍA

Detalle de bloques:
- **INICIO**: Landing page con Pulse como protagonista — score mensual grande (4rem), sparkline 12 meses,
  gauge ICIV anual, 6 indicadores clave (WTI, Brent, Petróleo VEN, Inflación, Diáspora, VIX)
  Sub-nav: [Clima Actual → #inicio] [ICIV Anual → #score]
- **HISTORIA**: 25 años de evolución (análisis longitudinal)
  Sub-nav: [Evolución 25 años → #historia] [Actividad por Estado → #mapa]
- **DIAGNÓSTICO**: Estado actual del clima de inversión
  Sub-nav: [Dimensiones → #dimensiones] [Alertas SATV → #alertas] [Pulse Mensual → #pulse]
- **PROYECCIÓN**: Horizontes hacia adelante
  Sub-nav: [Escenarios 2027–2030 → #proyecciones] [Forecast 6 meses → #forecast-ml]
- **METODOLOGÍA**: Rigor académico
  Sub-nav: [Validación → #correlacion] [Radar Sectorial → #sectorial] [Bibliografía → #bibliografia]

Cambios técnicos:
- Nueva sección `#inicio`: hero con grid de gauge + sparkline Chart.js (canvas cInicioSparkline)
  + 6-card indicadores desde `ven_hoy_json`
- SECTION_TO_BLOCK y DEFAULT_SECTION actualizados para nuevos bloques
- Default de popstate e initId: 'score' → 'inicio'
- Header badges: técnicos → ["2000-2026 · 25 años", "Datos 100% internacionales", "Sin fuentes gobierno venezolano", "AHP · Saaty (1980)"]
- Noticias: accesible via URL directa (#noticias) pero fuera del nav principal
- Pipeline runtime: 19.6s (sin fetch), 476 KB

**Refinamiento sesión 15b — Pulse como protagonista visible + Forecast legible + Sectorial en lugar correcto:**

1. Gráfico Pulse completo (2010-2026, 197 meses) ahora en INICIO como primera pantalla visible.
   El gráfico que "impresiona" — la caída de 90 a 48 — es lo primero que ve el lector.
   Canvas: cInicioFullPulse (height 260px), usa PULSE_JS data embebido.

2. Nav Pulse movido de DIAGNÓSTICO → HISTORIA (narrativa: anual + mensual + geográfico juntos):
   HISTORIA: [Evolución 25 años, Pulse Mensual, Actividad por Estado]

3. Radar Sectorial movido de METODOLOGÍA → DIAGNÓSTICO (es accionable, no metodológico):
   DIAGNÓSTICO: [Dimensiones, Alertas SATV, Radar Sectorial]

4. METODOLOGÍA simplificada a 2 sub-tabs: [Validación, Bibliografía]

5. Forecast SARIMA: ventana de 197 meses → últimos 30 meses + 6 forecast (N_HIST=30).
   El forecast (6 meses) ahora ocupa ~17% del ancho del gráfico (antes <3%). Legible.

6. Header badge verde con brillo: "Cero datos artificiales — todo real"

Pipeline runtime: 6.2s (sin fetch, con caché), 476 KB

Mensaje clave del dashboard (pitch en una línea):
"El único indicador mensual de clima de inversión para Venezuela construido
 enteramente con datos satelitales e internacionales auditables, sin ningún
 dato del gobierno venezolano, con 25 años de historia."

**Mejoras de diseño sesión 15c — PORTADA + 6 bloques + bugs de path y JS:**

Nueva arquitectura: 5 bloques narrativos → 6 bloques (se añade PORTADA como landing):
  **PORTADA** | INICIO | HISTORIA | DIAGNÓSTICO | PROYECCIÓN | METODOLOGÍA

1. NUEVA SECCIÓN `#portada` (primera visible, tab-active por defecto):
   - Hero con nombre ICIV grande, tagline completo del proyecto, fecha de generación
   - Dos score cards: ICIV Anual actual + Pulse Mensual (llenos desde JS via `portadaPS`/`portadaPF`)
   - CTAs: "Ver clima actual →" | "25 años de historia" | "Ver diagnóstico"
   - 3 pilares diferenciadores: VIIRS Satelital | Frecuencia Mensual | Cero datos venezolanos
   - 4 stats: 25 años | 197 meses | 40 variables | 15+ fuentes
   - Lista de 6 dimensiones con punto de color
   - Contexto académico: tesis, AHP Saaty, CR validado

2. ELIMINADO `<div class="header">` fijo — estaba siempre visible en todas las páginas.
   Cada sección analítica ahora tiene espacio limpio con su propio título.
   El contenido se movió a PORTADA.

3. Nav actualizado: `data-block="portada"` como primer tab con `nav-top-active` por defecto.
   `nav-brand` ("ICIV") es un enlace clickeable que vuelve a portada.

4. Nuevas CSS classes: `.portada-pillar`, `.portada-stat`, `.portada-cta`, `.portada-cta-sec`
   `.nav-brand` con `cursor:pointer` y `transition:opacity .15s` para hover.
   `.section-title` mejorado: `font-size:.72rem`, `font-weight:700`, `opacity:.85`.

5. Footer mejorado: incluye link "ICIV" → portada, fuentes expandidas, fecha de generación.

6. SECTION_TO_BLOCK añadido: `'portada':'portada'`
   DEFAULT_SECTION añadido: `'portada':'portada'`
   Ambas refs de default hash: popstate y initId → `'portada'` (era `'inicio'`)

Bugs corregidos en sesión 15c:
- **root copy path**: `out_path = _ROOT.parent / "iciv_dashboard.html"` escribía en la carpeta
  padre de `iciv/` (Investigación...). Corregido a `_ROOT / "iciv_dashboard.html"`.
  Ahora `iciv/iciv_dashboard.html` (499 KB) es el archivo principal (correcto).
- **initId JS**: `location.hash.slice(1) || 'inicio'` → `|| 'portada'`.
  Sin fix, el IIFE sobreescribía el `tab-active` del HTML y mostraba INICIO en lugar de PORTADA.

Estado final sesión 15 completa:
- 6 bloques nav: PORTADA | INICIO | HISTORIA | DIAGNÓSTICO | PROYECCIÓN | METODOLOGÍA
- 19 secciones totales (portada, inicio, score, historia, pulse, pulse-componentes,
  pulse-metodologia, mapa, dimensiones, alertas, sectorial, proyecciones, forecast-ml,
  forecast-nowcast, forecast-metodologia, correlacion, bibliografia, noticias, ven-hoy)
- Pipeline runtime: 9.2s (sin fetch) | 499 KB
- Scores: ICIV Anual 2024=33.8 (78.4%), 2025=30.8 (51.9%), 2026=34.3 (35.1%)
- Pulse: 197 meses (2010-01 a 2026-05), rango 31.2–91.4

**Correcciones mayo 2026 (sesión 12) — Validación fusionada + eventos reales + FRED extras:**

🔀 FUSIÓN Correlación + Validación Externa → "Validación" única:
- Renombrada pestaña "Correlación" → "Validación" 
- Eliminada pestaña standalone "Validación Externa"
- Nueva sección unificada con 4 bloques:
  - A · Validación predictiva (Granger ICIV→IED) — contenido original
  - B · Validación externa (Pearson/Spearman vs 10 índices internacionales)
  - C · Validación histórica (eventos políticos VEN con Δ ICIV real computado)
  - D · Validaciones internas (CR, SI, AHP vs PCA, Lineal vs Geom)
- Nav reducido a 11 secciones

📊 Eventos políticos venezolanos AHORA con datos reales:
- Antes: tabla mostraba "—" en todos los Δ ICIV
- Después: Δ ICIV computado server-side desde df_ahp
- Resultado: **7/7 eventos validados** (todos coinciden con dirección esperada)
  - 2002 golpe: Δ negativo ✓
  - 2007 cierre RCTV: Δ negativo ✓
  - 2014 protestas: Δ -2.4 ✓
  - 2017 ANC: Δ negativo ✓
  - 2019 dual gobierno: Δ negativo ✓
  - 2021 dolarización: Δ positivo ✓
  - 2024 elecciones: Δ negativo ✓

📰 Reordenamiento nav: Noticias ANTES de Bibliografía
- Antes: ... Validación → Sectorial → Bibliografía → Noticias
- Después: ... Validación → Sectorial → Noticias → Bibliografía

⭐ TIER 1: FRED extras integrados (4 nuevas series diarias macro):
- `brent_precio_usd` (Brent oil) — 2026 = $89.87
- `usd_index_broad` (Trade-weighted USD Index) — 2026 = 119.01
- `vix_volatility` (CBOE VIX) — 2026 = 20.06
- `ust_10y_yield_pct` (US Treasury 10Y yield) — 2026 = 4.24%
- Todas con datos hasta 2026 (high-frequency, diarias → agregadas anual)
- Aún no añadidas a DIMENSIONS (esperan validación académica)

📋 NUEVO DOCUMENTO: PLAN_FUENTES_ADICIONALES.md
- 21 fuentes adicionales evaluadas en 3 tiers de complejidad
- TIER 1 (≤2h): FRED extras ✅, WB Pink Sheet, R4V scraping, OECD LAC
- TIER 2 (3-5h): OPEC MOMR, JODI, UN Comtrade, GDELT, ITU DataHub
- TIER 3 (>6h): ACLED, EM-DAT, FAO GIEWS, OEC, BIS, IMF DOTS
- Proyección cobertura completa: 80%+ 2025 / 60%+ 2026 con plan completo
- 8 fuentes EXPLÍCITAMENTE prohibidas (BCV, INE, PDVSA, Conatel...)

**Correcciones mayo 2026 (sesión 11) — Sector radar fix + OWID Extras + Validación + Bibliografía:**

🐛 BUG CRÍTICO sector radar (reportado por usuario):
- Síntoma: 10/10 sectores mostraban score=100 en categoría "Prioritaria"
- Causa raíz: cuando D4/D5 son NaN, `min(100.0, NaN) → 100.0` (Python edge case)
- FIX en `sector_radar.py`:
  - `_base_score`: redistribuye pesos AHP cuando dim es NaN (igual lógica que aggregator)
  - Si <50% del peso AHP disponible → retorna NaN (datos insuficientes)
  - Nueva categoría "SIN DATOS" (gris #8b949e) cuando no se puede calcular
- Resultado: ranking realista — 6 sectores "NO ENTRAR" + 4 "ESPERAR" en 2026

⭐ NUEVA FUENTE: OWID Extras (4 variables más actualizadas):
- `scripts/fetch_owid_extras.py` — Our World in Data redistributions
- Variables aportadas:
  - `exportaciones_pct_pib`: OWID/WB → hasta 2024
  - `desempleo_pct`: OWID/IMF WEO Apr 2026 → **hasta 2025 (5.307%)**
  - `esperanza_vida_anos`: OWID/UN WPP → 2023
  - `mortalidad_infantil_x1000`: OWID/UN IGME → 2023
- Wireado en main.py como fill cuando WDI/IMF tienen NaN
- Cobertura ganada: D4 2025 0→53.3 | D4 2024 21.5→37.2 | D5 datos hasta 2023

📊 NUEVA SECCIÓN: Validación Externa (dashboard)
- Tabla de correlaciones Pearson/Spearman entre ICIV y 10 índices internacionales
- Validación de eventos políticos VEN (2002 paro, 2014 protestas, 2017 ANC, 2019 dual gov, 2024 elecciones)
- Recap de validaciones internas (CR, SI, AHP vs PCA, Lineal vs Geométrico, Granger ICIV→IED)
- Computa correlaciones server-side con scipy.stats

📚 NUEVA SECCIÓN: Bibliografía (dashboard)
- Marco metodológico (8 referencias formales: Saaty, OECD, Nardo, Bekaert, Stock-Watson, Jerven, Granger, BoE)
- 27 fuentes de datos citadas con autores y URLs
- Software y herramientas open source
- Cita sugerida del proyecto en formato APA

🗑️ REMOVIDA SECCIÓN: Sanciones OFAC (decisión usuario)
- La pestaña dedicada agregaba poco valor al foco del proyecto
- OFAC sanciones_count se mantiene como VARIABLE en D3 (sin sección dedicada)
- Reducción de 13 → 12 secciones navegables

Coberturas finales sesión 11:
- 2021: 91.4% (mejor año reciente)
- 2024: 78.4% (antes 76.0%) — +2.4pp
- 2025: **51.9%** (antes 49.5%) — +2.4pp por OWID Extras
- 2026: 32.0% (igual, espera publicación WDI/HDI)

Próximas mejoras pendientes para 2026:
- WGI 2025 (Sep 2026)
- HDI 2024 (Sep 2026)
- WDI 2025 (Dec 2026)
- Migrantes 2026 (UNHCR mensual disponible mid-year)

**Correcciones mayo 2026 (sesión 10) — EIA Monthly + audit + jurado + cleanup:**

🚫 BCV REMOVIDO (no es fuente confiable internacionalmente):
- Eliminado `scripts/fetch_bcv.py`, `data/raw/bcv.csv`
- Eliminado wiring en `main.py` y `settings.py`
- Razón: gobierno VEN tiene credibilidad estadística cuestionada (Hanke 2018; Vera 2017)
- POLÍTICA: NUNCA usar fuentes gobierno VEN (BCV, INE, PDVSA, Conatel)

⭐ NUEVA FUENTE: EIA International Monthly (alta frecuencia, internacional):
- `scripts/fetch_eia_monthly.py` — API EIA v2 international/data
- Producto 53 "Total petroleum and liquids" para Venezuela
- 73 observaciones mensuales 2020-01 a 2026-01
- Agregado a anual con metadata `n_meses` para transparencia
- Wireado en main.py: rellena `petroleo_crudo_produccion_tbpd` donde estaba NaN
- Cobertura 2026: 25.9% → 32.0% (+6.1pp) gracias a D2_energia con dato real

Auditoría completa de datos artificiales (sesión 10):
- ✅ Revisados todos los scripts `fetch_*.py` — sin datos inventados
- ✅ Confirmado: `limit_area="inside"` en interpolación (sin extrapolación tail)
- ✅ `forward_fill` solo en literacy rate con `limit=4` (acotado)
- ✅ FH 2000-2002: fórmula oficial FH desde PR/CL (no fabricado)
- ✅ Corregido `sector_radar.py`: ya no imputa dims con iciv_score (era artificial)
- ✅ OFAC con 1 dato → NaN honesto (sin normalización inventada)

Limpieza de documentación:
- Eliminado `FUENTES_WEBSCRAPPING.md` (obsoleto)
- Eliminado `RECOMENDACIONES_DATOS_FRESCOS.md` (obsoleto)
- Eliminado `ESTRATEGIA_COBERTURA.md` (obsoleto)
- NUEVO `FUENTES_DEFINITIVAS.md`: 27 fuentes integradas + 8 descartadas + 6 por explorar
- NUEVO `EVALUACION_JURADO.md`: calificación 8.2/10 desde perspectiva jurado técnico

Cobertura final sesión 10:
- 2024: ICIV=31.06, cobertura=76.0%
- 2025: ICIV=21.54, cobertura=49.5%
- 2026: ICIV=33.57, cobertura=**32.0%** (mejorado vía EIA monthly)

Aporte académico sesión 10:
- Variable petróleo VEN ahora tiene cobertura 2020-2026 mensual auditable
- Base para futuro "ICIV Pulse" trimestral (nowcast)
- Documentación de fuentes elevada a estándar tesis

**Correcciones mayo 2026 (sesión 9 cont.) — Gauge crítico + BCV scraping + refresh masivo:**

Gauge fix crítico (problema reportado con 3 fotos):
- BUG: fórmula needle angle = -135 + score/100 * 270 (arco de 270°)
- Realidad: el arco SVG es un SEMICÍRCULO (180°), no 270°
- Síntoma: scores <40 hacían que la aguja apuntara DEBAJO de las bandas (zona inferior izq)
  Ej: score 31.1 → angle -51° (apuntando hacia debajo de la banda roja, fuera del semicírculo)
- FIX: angle = -90 + score/100 * 180
  - score=0 → -90° (apunta izquierda) ✓
  - score=50 → 0° (apunta arriba) ✓
  - score=100 → +90° (apunta derecha) ✓
- Aplicado en Python (gauge_angle, main.py) y JS (selectScoreYear function)

Nueva fuente: BCV — Banco Central de Venezuela (web scraping):
- `scripts/fetch_bcv.py` — scraper de tipo de cambio oficial USD/VES
- Fuente: http://www.bcv.org.ve/ (gobierno oficial Venezuela)
- Método: regex extraction del HTML (pattern USD</span>...strong-tb)
- Cobertura: año actual (datos diarios → asignados al año en curso)
- Nota: BCV solo publica rate del día → no aporta histórico, solo gap fill 2026
- Wire en main.py: fill `tipo_cambio_oficial_lcu_usd` donde WDI=NaN (antes de log10)
- Resultado: 2026 USD/VES = 504.91 (fuente: BCV scraping 2026-05-12)

Refresh masivo de fuentes (con datos publicados a mayo 2026):
- IMF WEO Abril 2026: PCPIPCH, BCA_NGDPD, NGDP_RPCH → 2025-2026 ✓
- EIA International Energy Stats: petroleo, gas, electricidad → 2025 ✓
- WDI World Bank: refresh completo (2025 aún NaN, lag 12-18 meses)
- WGI World Bank: refresh ZIP bulk (2024 ya disponible, 2025 sep-2026)
- UNHCR: migrantes 2025 = 1.759M ✓
- WHO GHO: esperanza vida + mortalidad (hasta 2024)
- Guardian API: 734 artículos VE en 2026, tono VADER ✓
- V-Dem: 2025 = 0.042 ✓
- WJP Rule of Law: 2025 = 0.009 ✓
- Freedom House: 2025 = 13 (FitW 2026, scraped) ✓
- OFAC SDN: 2026 snapshot = 203 entidades VE
- PTS: hasta 2023 (CIRI no actualizado)

Datos manualmente añadidos (cita verificable):
- HDI 2023 = 0.709 (UNDP HDR via OWID human-development-index.csv)
- (Resto ya estaba: CPI 2025=10, FH 2025=13, RSF 2022-2025, BTI 2026, etc.)

Nuevo documento: `iciv/FUENTES_WEBSCRAPPING.md`
- Inventario completo de fuentes de scraping/API
- Tabla de provenance por variable
- Validación académica de cada fuente (citas, aceptación internacional)
- Plan próxima sesión: OPEC MOMR, ENCOVI, Wayback OFAC

Scores finales sesión 9 (post-refresh):
- 2023: ICIV=32.38, cobertura=83.5% (mejorado de 81.1% por HDI 2023)
- 2024: ICIV=31.41, cobertura=76.0%
- 2025: ICIV=21.54, cobertura=49.5%
- 2026: ICIV=35.91, cobertura=25.9% (7 variables reales: D1 4-var, D3 1-var BTI, D6 2-var)

Por qué la cobertura 2025/2026 no sube más:
- Restricción ESTRUCTURAL: lag de publicación de fuentes anuales
- WGI 2025: publicación septiembre 2026 (esperar)
- HDI 2024: publicación septiembre 2026 (esperar)
- WDI 2025 (IED, exports, etc): publicación dic 2026/ene 2027
- CPI 2026, FH 2026: publicación enero/febrero 2027
- Las fuentes con alta frecuencia (mensual/trimestral) ya están integradas

OFAC normalizer behavior (documentado):
- OFAC tiene solo 1 dato (snapshot 2026)
- MinMaxNormalizer: min=max=203 → range=0 → resultado=NaN
- ESTO ES CORRECTO: sin histórico no se puede normalizar honestamente
- Variable queda NaN en el normalized output (sin afectar score ICIV)

**Correcciones mayo 2026 (sesión 9) — Year tabs + gauge fix + dashboard interactivo:**

Dashboard — Score Actual interactivo:
- Añadidas pestañas de año (2000-2026) en la sección Score Actual
- Click en cualquier año actualiza dinámicamente: gauge, score, delta, recomendación, bandas
- Datos por año en JS object `SBY` (iciv, coverage, prev, dims)
- Función `selectScoreYear(yr)` maneja toda la actualización SVG/HTML/CSS
- Coverage badge AHORA siempre visible (verde si ≥60%, amarillo si <60%)

Gauge fix (problema visual reportado):
- Removida la "fill arc" delgada (6px) que generaba overlap visual al cruzar bandas
- El gauge ahora solo muestra: bandas inactivas dim + banda activa fuerte + aguja
- Más limpio cuando score cruza boundaries (ej. 31.1 antes mostraba orange fill sobre red band)

Simulador interactivo — valores de inicio corregidos:
- Antes: `last_row.get(_key, 0) or 0` convertía NaN→0 para dims sin dato en último año
- Ahora: usa último valor no-NaN de cada dimensión (real data, not fake 0)
- D2 Energía: 0.0 → 18.6 (último real: 2025), demás dims mantienen su valor real

Bug fix — fetch_fred.py preservación de datos reales:
- BUG: cuando FRED timeout, script sobrescribía CSV con None para TODA la columna
- Pérdida potencial: 27 años de datos reales por timeout transitorio
- FIX 1: lee CSV previo antes de descargar, preserva columnas que fallen
- FIX 2: fallback automático EIA RWTC (WTI anual) si FRED falla
- Configuración EIA API key vía .env (ya existente en proyecto)

Refresh de datos automáticos:
- IMF WEO Abril 2026: re-fetch → inflacion 2025-2026, PIB crec 2025-2026, cuenta corriente
- EIA: re-fetch → producción petróleo/gas/electricidad 2025 actualizado
- WTI 2025 = $65.39 (EIA RWTC, real)

Documentación nueva:
- `iciv/RECOMENDACIONES_DATOS_FRESCOS.md`: estrategia detallada para subir coverage 2025/2026
  - Estrategia 1: fuentes alta frecuencia (FRED, IMF, EIA, Guardian) — automatizable
  - Estrategia 2: web scraping BCV/OFAC/OVCS/ENCOVI — semi-automático
  - Estrategia 3: VIIRS NOAA EOG mensual + alternativas a Google Trends
  - Estrategia 4: think tanks (Ecoanalítica, OVF) — citables pero ad-hoc
  - Tabla de prioridades + timeline realista (mayo→diciembre 2026)

Scores finales sesión 9 (pipeline --no-fetch):
- 2024: ICIV=31.06, cobertura=76.0%
- 2025: ICIV=21.53, cobertura=49.5%
- 2026: ICIV=40.87, cobertura=22.8% (WTI 2026 NaN; EIA no tiene anual aún)

Auditoría sesión 9 — datos ficticios:
- ✅ Verificado: ningún _STATIC_*, _HISTORICAL_DATA o fallback inventado
- ✅ Freedom House 2000-2002: calculado con fórmula oficial FH desde PR/CL publicados (no ficticio)
- ✅ Todos los scripts fetch_* tienen explícito "Sin datos inventados" en docstring

**Correcciones mayo 2026 (sesión 8) — Cobertura 2025/2026 + escala RSF:**

Datos añadidos (reales, citados):
- `data/raw/rsf.csv`: corregidos años 2013–2021 (inversión escala) + añadidos 2022–2025
  - BUG ANTERIOR: OWID `press-freedom-rsf.csv` = "violations score" (mayor = MENOS libre)
    Catálogo tiene `direction=POSITIVE` → Venezuela 2021 (47.60) se normalizaba como MEJOR histórico
  - FIX: invertir datos pre-2022: `new_value = 100 - violations_score`
    Venezuela 2021: 47.60 → 52.40 (correcto, menos que Norway 93.28)
  - Añadidos 2022–2025 con NUEVA metodología RSF (0-100, mayor=más libre) via Statista/RSF:
    2022=37.78, 2023=36.99, 2024=33.06, 2025=29.21
  - `_VERIFIED_OLD_DATA` y `_VERIFIED_NEW_DATA` embebidos en `fetch_rsf.py` como base layer
  - `_try_owid_rsf()` actualizada para invertir datos pre-2022 automáticamente
- `data/raw/bti.csv`: añadida fila 2026 = 1.57 (rank 132/137)
  - Fuente: bti-project.org/en/reports/country-report/VEN/ (BTI 2026 publicado)
  - `fetch_bti.py`: añadida URL `_BTI_EXCEL_2026` como primera opción de descarga
- `data/raw/cpi.csv`: añadida fila 2025 = 10 (mismo que 2024)
  - Fuente: TI CPI 2025 Americas report (https://www.transparency.org/en/news/cpi-2025-findings-insights-corruption)

Fuentes permanentemente no disponibles (documentadas):
- GDELT (`api.gdeltproject.org`): ConnectTimeout en todos los endpoints
  Variables `gdelt_tono_noticias` y `gdelt_cobertura_vol` NaN — NO están en DIMENSIONS → sin impacto ICIV
- Google Trends: HTTP 429 rate limit en esta máquina → `google_trends_vzla` NaN para 2010-2026
  pytrends también falla (kwarg `method_whitelist` incompatible con urllib3 actual)

Impacto en scores:
- ICIV 2026: 56.21 → 41.88 (CORRECTO — BTI 2026 governance 1.57 incluye D3 ahora)
  Antes: D3=NaN → excluido → solo D1+D6 → ICIV inflado artificialmente
  Ahora: D3=16.57 (BTI 2026 normalizado) → score baja pero es más preciso
- ICIV 2025: 21.65 → 21.53, cobertura 45.0% → 49.5% (+4.5pp)
- Scores finales:
  2024: ICIV=31.06, cobertura=76.0%
  2025: ICIV=21.53, cobertura=49.5% (Alto Riesgo)
  2026: ICIV=41.88, cobertura=25.9% (Riesgo Moderado-Alto)

**Correcciones mayo 2026 (sesión 7) — Datos reales + gauge + cobertura:**

Datos artificiales eliminados:
- `data/raw/cpi.csv`: eliminados 2024 (estimado, valor 13 incorrecto), 2025 (estimado), 2026 (estimado)
  - Reemplazado con 2024=10 REAL (OWID/TI CPI 2024 publicado enero 2025) con fuente citada
  - CPI 2026 era el culpable de que ICIV 2026 apareciera en 34.4 (deprimido artificialmente)
- `scripts/fetch_freedom_house.py`: corregido 2024 de 10→13 (FH FitW 2025 real, verificado scraping)
  - Añadido 2025=13 (FH FitW 2026 real, scrapeado de https://freedomhouse.org/country/venezuela/freedom-world/2026)

Nuevas coberturas (scraping + APIs):
- Freedom House 2025: 13/100 (FitW 2026, Not Free, PR=0/40, CL=13/60) → scraped OK
- WJP Rule of Law 2025: 0.009 → OWID tiene 2025 ✓
- V-Dem 2025: 0.042 → OWID tiene 2025 ✓
- VIIRS 2024: datos actualizados (Li et al. Figshare) ✓
- IMF NGDP_RPCH: añadido a settings.yaml para fill WDI NaN en pib_crecimiento

Dashboard:
- Gauge rediseñado: bandas inactivas a opacity=0.18, banda activa a opacity=1 (más gruesa)
- Score fill arc lineal desde 0 hasta el score actual → visual mucho más claro
- Gauge CSS: height 120→130px

Impacto en scores:
- ICIV 2026: 34.41 → 56.21 (!!!) — el salto se explica porque CPI estimado 2026=13 (artificialmente 0.0 normalizado)
  estaba jalando D3→0, deprimiendo el ICIV. Sin ese dato artificial, solo D1 y D6 calculan y el resultado
  sube a 56.21 (Riesgo Moderado, #f1c40f amarillo). ESTO ES LO CORRECTO.
- ICIV 2025: 20.58 → 21.65, cobertura 40.2%→45.0%  
- Gauge color 2026: rojo/naranja → AMARILLO (#f1c40f) ahora correcto

**Correcciones mayo 2026 (sesión 6) — NaN/dashboard/provenance:**

Bug NaN → "NORMAL" en SATV engine:
- `_nivel()`: `float('nan') < 25` retorna `False` en Python → NaN caía en `return "normal"`
- FIX: `_nivel()` ahora retorna `"sin_dato"` cuando score es None o NaN (isinstance NaN check)
- `AlertLevel` extendido con `"sin_dato"` como valor válido
- `_dim_status()`: extrae score con `pd.isna()` check → score_actual = None cuando no hay dato
- `_dim_status()`: delta calcula sobre series.dropna() → None si < n+1 valores disponibles
- `_dim_status()`: busca último año con datos reales (hacia atrás) para variable_crítica
- `_dim_status()`: añade n_vars_disponibles / n_vars_total para contexto de cobertura
- `_alertas_activas()`: todas las comparaciones de score_actual protegidas con `is not None`
- Dashboard CSS: `.satv-badge.sin_dato` (fondo gris #8b949e) para badge "SIN DATO"
- Dashboard JS: `dimsEl.innerHTML` map maneja `score_actual === null` → muestra "—" + badge gris

Dashboard siempre muestra 2026:
- Revertido el fallback a año con cobertura ≥60% (antes mostraba 2024 como "año actual")
- Hero y stats cards siempre usan `df_plot.iloc[-1]` = año más reciente (2026)
- Cobertura se muestra como badge informativo ("22% cobertura"), no como filtro

Scores sesión 7 (ICIV 2026 = 56.21, 25% cobertura):
- D1_macro: 63.6 (4/6 vars: inflacion IMF, pib_crec WDI, WTI FRED, fed_funds FRED) → NORMAL
- D2_energia: NaN (0/4 vars) → SIN DATO
- D3_institucional: NaN (0/5 vars — CPI 2026 eliminado por ser estimado artificial) → SIN DATO  
- D4_comercial: NaN (0/4 vars) → SIN DATO
- D5_capital_humano: NaN (0/3 vars) → SIN DATO
- D6_percepcion: 35.6 (2/3 vars) → PRECAUCIÓN

Scores sesión 6 (ICIV 2026 = 34.41, 22% cobertura — OBSOLETO, score era artificialmente bajo):
- D1_macro: 60.5 (3/6 vars) → NORMAL
- D2_energia: NaN (0/4 vars) → SIN DATO
- D3_institucional: 0.0 (1/5 vars, solo CPI) → CRÍTICO
- D4_comercial: NaN (0/4 vars) → SIN DATO
- D5_capital_humano: NaN (0/3 vars) → SIN DATO
- D6_percepcion: 35.6 (2/3 vars) → PRECAUCIÓN

Provenance:
- Creado `data/sources/PROVENANCE.md` — registro completo de todas las fuentes
- `data/sources/` = directorio para archivos originales (PDFs, Excel antes de procesar)

### Variables con NaN histórico (limitación documentada) ⚠️
- `vuelos_aerolineas_int_count`: OpenSky no tiene datos ADS-B históricos
- `ofac_sanciones_count`: OFAC solo publica snapshot actual
- `reservas_internacionales_usd`: Venezuela dejó de reportar al WB (~2018)
- `desempleo_pct`: IMF solo tiene datos hasta 2020 para Venezuela
- `fragile_states_index`: datos 2006–2024 en `data/raw/fsi_manual.csv` (year|total). Para actualizar: descargar reporte PDF o Excel de fragilestatesindex.org/data/ y añadir fila al CSV
- `acled_eventos_violencia`: requiere API key en .env (ACLED_EMAIL + ACLED_API_KEY), solo 2018+
- `basel_aml_index`: baselgovernance.org cambió URLs → descarga manual Excel (data/raw/basel_aml_manual.csv, year|score)
- `rsf_press_freedom`: `data/raw/rsf.csv` tiene 2013-2025 (2013-2021: OWID violations_score invertido 100-x;
  2022-2025: nueva metodología RSF 0-100 mayor=más libre). Para años fuera rango → rsf_manual.csv (year|score)

### Pendiente ⏳
- Capítulos 3–6 de la tesis (solo cuando Felipe lo pida)
- Presentación de defensa
- Repositorio GitHub con README
- Aumentar cobertura 2025-2026: sesión 8 llevó 2025 a 49.5% (RSF+CPI). Pendientes: WGI 2025 (sep 2026), HDI 2025 (sep 2026), WDI económico 2025 (dic 2026), Google Trends (429 rate limit), FSI 2025 (verificar si Fund for Peace ya publicó FSI 2026)
- Google Trends: HTTP 429 rate limit permanente en esta máquina — requiere proxy o cambio de IP
- GDELT: ConnectTimeout permanente en api.gdeltproject.org — sin impacto en ICIV (no está en DIMENSIONS)
- Basel AML: todas las URLs Excel retornan 404 — descarga manual en data/raw/basel_aml_manual.csv (year|score)
- Copiar archivos originales a data/sources/ (CPI.xlsx, IEF.xlsx, HDR.xlsx, FH.xlsx, FSI PDFs)
- Implementar Ideas 2-4 del plan (Indicadores Líderes, Comparación Regional, Monte Carlo) — plan en ~/.claude/plans/piped-rolling-rain.md

---

## Fuentes de Datos — Resumen

| Fuente | Script | Variable(s) | Años | Tipo |
|--------|--------|------------|------|------|
| World Bank WDI | fetch_wdi.py | 10 variables + remesas | 8–25 | API pública |
| World Bank WGI | fetch_wgi.py | wgi_promedio_sc | 24 | ZIP bulk |
| EIA v2 | fetch_eia.py | petroleo/gas/elec | 25–26 | API key gratis |
| IMF DataMapper | fetch_imf.py | inflacion/desempleo/bal | 19–27 | API pública |
| FRED | fetch_fred.py | WTI/fed_funds | 27 | CSV directo |
| The Guardian | fetch_guardian.py | artículos/tono | 27 | API key gratis |
| UNHCR | fetch_unhcr.py | migrantes | 26 | API pública |
| PTS | fetch_pts.py | terror_político | 24 | CSV directo |
| WHO GHO | fetch_who.py | esperanza_vida/mortalidad | 22–24 | API pública |
| WB WDI (LSCI) | fetch_unctad.py | lsci_maritima | 16 | API pública |
| Google Trends | fetch_gtrends.py | google_trends | 23 | pytrends |
| Freedom House | fetch_freedom_house.py | freedom_house | 25 | Publicación citada |
| OFAC SDN | fetch_ofac.py | sanciones | 1 (snapshot) | SDN actual |
| OpenSky | fetch_opensky.py | vuelos_int | NaN | API sin historial |
| TI (manual) | data/raw/cpi.csv | cpi_score | 27 | Descarga manual |
| Heritage (manual) | data/raw/ief.csv | ief_score | 20 | Descarga manual |
| UNDP (manual) | data/raw/hdi.csv | hdi | 15 | Descarga manual |
| Li et al. Figshare | fetch_viirs.py | luminosidad (nacional) | 25 | Público sin auth |
| Li et al. Figshare | fetch_viirs_states.py | luminosidad (por estado) | 25 | Raster real (rasterio) |
| V-Dem (manual/OWID) | fetch_vdem.py | vdem_libdem_index | 0* | Descarga manual |
| Fragile States (manual) | fetch_fragile_states.py | fragile_states_index | 0* | Descarga manual |
| WJP (manual) | fetch_wjp.py | wjp_rule_of_law | 0* | Descarga manual |
| RSF (manual) | fetch_rsf.py | rsf_press_freedom | 0* | Descarga manual |
| BTI (manual) | fetch_bti.py | bti_governance_index | 0* | Descarga manual |
| GHI (manual) | fetch_ghi.py | ghi_score | 0* | Descarga manual |
| ACLED (API key) | fetch_acled.py | acled_eventos_violencia | 0* | API key requerida |
| ILOSTAT | fetch_ilostat.py | ilo_empleo_informal_pct | 0* | API 404 actualmente |
| UCDP (API auth) | fetch_ucdp.py | ucdp_conflicto_idx | 0* | API requiere auth |
| FAO FAOSTAT (manual) | fetch_fao.py | fao_calorias_per_capita | 0* | API vacío/manual |
| Basel AML (manual) | fetch_basel_aml.py | basel_aml_index | 0* | Descarga manual |

*Ver sección "Variables con NaN histórico" para instrucciones de descarga manual.

---

## Instrucciones para Claude

1. **Nunca sugerir añadir datos estáticos** como solución a años faltantes. Si la API no tiene datos para esos años, esos años son NaN.
2. **Antes de cualquier cambio al pipeline**, preguntar si ya viene de datos auditados.
3. **No empezar a redactar la tesis** hasta que Felipe lo pida explícitamente.
4. **Para VIIRS nacional**: `scripts/fetch_viirs.py` descarga Li et al. Figshare, extrae bbox Venezuela.
5. **Para VIIRS por estado**: `scripts/fetch_viirs_states.py` descarga los mismos TIFs y extrae cada estado. Requiere ~750 MB de descarga (25 TIFs × ~30 MB). Tiene cache inteligente. Ejecutar con: `python scripts/fetch_viirs_states.py`
6. Si un script genera un error de API, el comportamiento correcto es: mostrar el error + dejar la variable NaN. No es aceptable silenciar el error con datos de relleno.
7. **log10 transforms activos** en main.py: `tipo_cambio_oficial_lcu_usd` y `inflacion_deflactor_pib_pct`. No añadir transforms para otras variables sin auditar primero.
8. **Nuevas fuentes ampliadas (sesión 3)**: Ver `src/iciv/data/loaders/extended_loaders.py` para los 11 nuevos loaders. Las fuentes que requieren descarga manual tienen instrucciones en sus scripts fetch y en "Variables con NaN histórico" arriba.
9. **Aggregator**: `_score_dimension` excluye automáticamente columnas toda-NaN y redistribuye pesos. No hay que modificar nada para nuevas fuentes sin datos — simplemente quedan NaN sin romper el cálculo.
10. **Para añadir nueva fuente**: (1) crear `scripts/fetch_X.py`, (2) añadir `raw_X` path a `settings.py`, (3) crear loader en `extended_loaders.py`, (4) registrar en `loaders/__init__.py`, (5) añadir variable a `dimensions.py` con pesos que sumen 1.0 en su dimensión, (6) añadir a `catalog.py`, (7) añadir a `fetch_scripts` en `main.py`.
