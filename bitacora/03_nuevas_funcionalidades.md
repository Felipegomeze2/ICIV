# Bitácora 03 — Nuevas Funcionalidades: Monte Carlo, Indicadores Líderes y Comparación Regional

**Fecha:** 22 de abril de 2026  
**Sesión:** Implementación de ideas 2, 3 y 4 (selección del autor)  
**Estado:** Completado y verificado (pipeline en 8.2s sin errores)

---

## Resumen ejecutivo

Se añadieron tres módulos analíticos al ICIV que elevan el proyecto de un índice retrospectivo
a un sistema de **inteligencia predictiva y comparativa**:

| Módulo | Archivo | Método clave |
|--------|---------|--------------|
| Monte Carlo | `src/iciv/scenarios/engine.py` | `compute_monte_carlo()` |
| Indicadores Líderes | `src/iciv/analytics/leading_indicators.py` | `LeadingIndicatorsAnalyzer.compute_all()` |
| Comparación Regional | `src/iciv/analytics/regional.py` | `RegionalComparison.compute_all()` |
| Datos regionales | `scripts/fetch_regional.py` | `fetch_regional()` |

El dashboard (`main.py`) fue extendido con 3 nuevas secciones en el nav y 3 nuevas fases
(3f, 3g, 3h) en el pipeline.

---

## Idea 4 — Monte Carlo sobre escenarios

### Motivación
Los escenarios 2027–2030 usaban bandas ±σ√n fijas (determinísticas). Esto subestima la
incertidumbre real: un inversor en Venezuela necesita saber "¿cuál es la probabilidad de
que en 2030 el ICIV supere 45?", no solo ver una franja simétrica.

### Decisiones de diseño

**Variables estocásticas elegidas (3 "drivers"):**
- `wti_precio_usd` (w_AHP = 0.05): exógeno, log-normal calibrada sobre cambios anuales 2018-2026
- `petroleo_crudo_produccion_tbpd` (w_AHP = 0.10): endógeno, normal truncada [0, 100] en espacio normalizado
- `wgi_promedio_sc` (w_AHP = 0.07): gobernanza, incertidumbre política alta

**Por qué estas 3:** Son las variables con mayor peso AHP dentro de los factores más
inciertos (energía + gobernanza + precios externos). Las 24 restantes se mantienen en su
proyección lineal (escenario base).

**Metodología (random walk acumulativo):**
```
Para s en 1..10_000:
  Para t en 2027..2030:
    ε_i(t) ~ N(µ_i_hist, σ_i_hist)   # calibrado en espacio normalizado (0-100)
    Δiciv(t) = Σ w_i × ε_i(t)        # shock total
    iciv_s(t) = iciv_base(t) + Σ_k Δiciv(k)   # acumulativo
```

La calibración usa los últimos 9 años de cambios anuales en espacio normalizado (no en
valores originales), lo que garantiza que los shocks son comparables a la escala del índice.

**Output clave (resultados con seed=42, n=10,000):**
- P50: 2027=33.3, 2028=33.2, 2029=33.2, 2030=33.1
- P(recuperación 2030 > 45): 0.0% — Venezuela estabilizada en zona de alto riesgo
- P(colapso 2030 < 25): 0.5% — escenario catastrófico marginal

**Interpretación:** La distribución de 10,000 trayectorias converge hacia un rango estrecho
(~28–38), lo que indica que bajo los parámetros históricos recientes, hay muy poca probabilidad
de una recuperación significativa en el corto plazo. Esto es consistente con el análisis
cualitativo del contexto venezolano.

**Referencia:** Bank of England (2013) "Fan Charts and the Analysis of Uncertainty"; 
Kaminsky et al. (1998) IMF Staff Papers 45(1).

---

## Idea 2 — Tablero de Indicadores Líderes

### Motivación
El módulo de correlación (`analytics/correlation.py`) solo probaba ICIV → IED. La pregunta
inversa — ¿qué variables predicen el ICIV futuro? — es más valiosa para inversores que
necesitan anticiparse al deterioro o recuperación.

### Metodología

Para cada una de las 27 variables normalizadas:

1. **Pearson cross-lag** (k=1,2,3): correlación entre `var(t)` e `iciv(t+k)`
2. **Granger causality** (maxlag=2): prueba si `var(t)` contiene información predictiva
   sobre `iciv(t+1)` más allá de la historia propia del ICIV
3. **Early Warning Score (EWS)**: `max|r_k| × (1.0 si Granger p<0.10, sino 0.5)`
4. **Señal actual**: compara `Δ3y` de la variable normalizada vs su dirección esperada

**Por qué maxlag=2 en Granger:** Con n=27 años, usar maxlag=3 consumiría demasiados
grados de libertad. Maxlag=2 es el estándar para series macroeconómicas cortas.

**Prueba de raíz unitaria (ADF):** Si alguna serie es I(1), se diferencia antes del test
de Granger para evitar regresiones espurias. Implementado en el método `_analyze_variable`.

### Resultados (abril 2026)

Top 3 indicadores líderes:
| Variable | EWS | Señal | Rezago óptimo |
|----------|-----|-------|---------------|
| Desempleo (%) | 0.917 | Alerta | 1 año |
| Producción Gas Natural (bcf) | 0.913 | Neutro | 1 año |
| Sanciones OFAC (conteo) | 0.896 | Positivo | 1 año |

**Barómetro agregado:** 61.9 → "Señales de Estabilización"

**Interpretación:** El desempleo como principal indicador líder confirma la literatura sobre
mercados laborales como señales tempranas de deterioro del clima de inversión. Las sanciones
OFAC con señal "positivo" (normalización relativa reciente) sugiere una ligera mejoría en
el entorno de relaciones exteriores.

**Referencia:** Kaminsky, Lizondo & Reinhart (1998) "Leading Indicators of Currency Crises",
IMF Staff Papers 45(1); Granger (1969) Econometrica 37(3).

---

## Idea 3 — Comparación Regional

### Motivación
El ICIV original solo cubre Venezuela. Un inversor necesita contexto: ¿es Venezuela mejor
o peor que Bolivia? ¿Cuánto se ha alejado del promedio andino?

### Decisión clave: variables universales

El ICIV completo usa 27 variables venezolanas-específicas (producción PDVSA, sanciones OFAC,
VIIRS, Google Trends, etc.). Para la comparación regional se usaron **11 variables universales**
disponibles en WDI (World Bank) y WGI para todos los países:

| Dimensión | Variables | Peso |
|-----------|-----------|------|
| D1 Macro (30%) | gdp_growth, inflation_cpi, reserves_months | 30% |
| D2 Energía (15%) | electricity_kwh_pc | 15% |
| D3 Institucional (25%) | wgi_composite (promedio 6 indicadores WGI) | 25% |
| D4 Comercial (20%) | fdi_pct_gdp, exports_pct_gdp, unemployment_pct | 20% |
| D5 Cap. Humano (10%) | life_expectancy, school_enrollment_sec, electricity_access | 10% |

**Nota metodológica crítica:** El ICIV Regional NO es directamente comparable al ICIV
completo (27 vars). Son sistemas de referencia distintos. El ICIV Regional es internamente
consistente para comparar los 5 países entre sí. Ref: OCDE Handbook on Composite Indicators (2008), §4.

### Descarga de datos — incidencias

**WGI via API estándar:** FALLIDA. Los indicadores WGI (CC.EST, GE.EST, etc.) no están
disponibles en el endpoint `api.worldbank.org/v2/country/.../indicator/CC.EST` (retorna
"indicator not found"). Los WGI tienen su propia API separada.

**Solución adoptada:** Descarga del Excel ZIP desde:
`https://databank.worldbank.org/data/download/WGI_EXCEL.zip`
El archivo `WGIEXCEL.xlsx` contiene una hoja "Data" con los indicadores `GOV_WGI_XX.SC`
en escala 0-100 (ya normalizada, distinta a la escala -2.5/+2.5 de los EST).

**SE.SEC.ENRR timeout:** El indicador de matrícula escolar secundaria agotó el timeout
de 30s en una de las descargas. La columna queda ausente del CSV; `RegionalComparison`
maneja vars faltantes re-normalizando los pesos de la dimensión (suma a 1 con las vars disponibles).

### Datos descargados

- `data/raw/regional/wdi_regional.csv`: 125 filas (9 indicadores × ~25 años × 5 países)
- `data/raw/regional/wgi_regional.csv`: 120 filas (5 países × 24 años)

### Resultados (año más reciente con datos completos)

| Rank | País | ICIV Regional | Δ 5 años |
|------|------|--------------|---------|
| 1 | Perú | 76.5 | +2.0 |
| 2 | Colombia | 66.7 | -1.7 |
| 3 | Ecuador | 65.9 | +2.3 |
| 4 | Bolivia | 53.0 | +1.8 |
| 5 | Venezuela | 43.4 | +11.4 |

**Interpretación:** Venezuela se ubica en último lugar pero muestra la mayor recuperación
relativa en 5 años (+11.4 pts), desde el fondo de 2020. Perú lidera la región andina en
clima de inversión. Colombia, históricamente el benchmark positivo, muestra ligero retroceso.

---

## Cambios en main.py

### Nuevas fases en el pipeline

```python
# Fase 3f: Monte Carlo
mc_data = fase_monte_carlo(df_ahp, df_norm, ahp)

# Fase 3g: Indicadores Líderes
lideres_data = fase_indicadores_lideres(df_norm, df_ahp)

# Fase 3h: Comparación Regional
regional_data = fase_regional(settings)
```

### Nuevas secciones en el dashboard HTML

| Sección | ID HTML | Subsecciones |
|---------|---------|--------------|
| Monte Carlo | Sub-tab `#escView-montecarlo` | Fan chart, prob cards, params card |
| Indicadores Líderes | `#lideres` | Barómetro, señales, tabla top-10 |
| Comparación Regional | `#regional` | Evolución, radar, ranking, brecha |

### Nav actualizado (13 secciones)
Score → Evolución → Dimensiones → AHP → Alertas → Correlación → **Indicadores Líderes** → **Comparación Regional** → Sanciones → Mapa → Escenarios (+ sub-tab Monte Carlo) → Validación → Noticias

---

## Validación de la integración

Ejecución: `python main.py --no-fetch --no-open` → completado en **8.2 segundos**, sin errores.

Todas las fases nuevas generaron datos coherentes y el HTML resultante contiene las
3 nuevas secciones con sus scripts JavaScript inline embebidos.
