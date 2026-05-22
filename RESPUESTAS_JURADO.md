# RESPUESTAS PREPARADAS PARA EL JURADO — ICIV Venezuela
## 12 preguntas probables con respuestas documentadas

> **Propósito:** Preparar respuestas verbales sólidas a las preguntas que un jurado técnico o económico probablemente formulará.  
> **Principio:** Cada respuesta debe ser honesta sobre las limitaciones del proyecto, no defensiva. Un jurado aprecia más reconocer un límite que ocultarlo.  
> **Fuente de las preguntas:** Sección 12, Plan de Acción Revisión Jurado ICIV (21-may-2026)

---

## Q1. ¿Por qué estas variables y no otras?

**Respuesta:**

La selección de variables sigue tres criterios declarados explícitamente en la metodología:

1. **Relevancia económica para inversión**: cada variable pertenece a una de las 6 dimensiones que la literatura de riesgo-país y clima de inversión identifica como determinantes (Bekaert et al. 1998; OECD Handbook 2008). Por ejemplo, WGI mide gobernanza institucional —la principal causa de desinversión en mercados emergentes.

2. **Disponibilidad internacional verificable**: solo se incluyen variables con fuente pública internacional (Banco Mundial, FMI, EIA, Freedom House, etc.). Se excluyen explícitamente todas las fuentes venezolanas (BCV, INE, PDVSA) por su credibilidad estadística cuestionada (Hanke 2018; Vera 2017).

3. **Cobertura mínima aceptable**: variables sin ningún dato real (como `ofac_sanciones_count` sin histórico, `vuelos_aerolineas_int_count` sin cobertura ADS-B) se mantienen en el catálogo pero se marcan como "sin datos" y no contribuyen al score.

El catálogo completo con justificación por variable está en `VARIABLES_MASTER.md`. En total: 41 variables declaradas, 35 con datos suficientes para el score, 3 con cero cobertura (declarado transparentemente).

---

## Q2. ¿Qué diferencia hay entre clima de inversión, riesgo país y atractivo económico?

**Respuesta:**

Los tres conceptos están relacionados pero tienen objetivos distintos:

| Concepto | Enfoque | Perspectiva |
|----------|---------|-------------|
| **Riesgo país** (EMBI, ICRG) | Probabilidad de default o inestabilidad financiera | Inversionista financiero |
| **Atractivo económico** (WCY, GCI) | Competitividad estructural | Empresa multinacional |
| **Clima de inversión** (ICIV) | Condiciones operativas para hacer negocios | Empresa con presencia física |

El ICIV captura **condiciones operativas** en Venezuela: ¿puede una empresa operar, cumplir contratos, repatriar capital, mantener su personal? No predice default soberano ni rankings de competitividad global.

Esta distinción justifica dimensiones como el Sector Energético (D2) y Capital Humano (D5) que los índices de riesgo-país típicos no incluyen, pero que son determinantes para decidir si es viable tener operaciones físicas en Venezuela.

---

## Q3. ¿Cómo se valida un índice compuesto cuando no existe una "verdad terreno" directa?

**Respuesta:**

La validación de un índice compuesto sin ground truth es un problema reconocido en la literatura (Nardo et al. 2005; OECD Handbook 2008). Se usan cuatro estrategias complementarias:

1. **Validación interna (coherencia)**:
   - Sensibilidad SI = 0.0408 (Robusto, umbral < 0.15)
   - Consistencia AHP: CR = 0.0081 < 0.10 (Saaty 1980)
   - Correlación ICIV lineal vs. geométrico: r = 0.99 — robusto al método de agregación

2. **Validación externa con índices independientes**:
   - Pearson/Spearman ICIV vs. 9 índices no-componentes (HDI, FH, WGI, CPI, V-Dem, WJP, FSI, PTS, RSF)
   - Todos los índices con los que ICIV debería correlacionar positivamente lo hacen

3. **Validación histórica**:
   - 7 eventos políticos documentados con Δ ICIV observado
   - Todos coinciden con la dirección esperada (golpe 2002 → baja; dolarización 2021 → sube)

4. **Triangulación metodológica**:
   - AHP vs. PCA: r = 0.994, PC1 explica 56.5% de varianza — ambos métodos convergen
   - ICIV vs. Granger IED: exploratoria (nota: IED es componente del ICIV → circularity parcial, documentada)

La limitación reconocida: no existe una medida directa del "clima de inversión real en Venezuela" contra la cual calibrar. El índice es un constructo teórico, y sus validaciones son de coherencia y consistencia, no de precisión predictiva.

---

## Q4. ¿Por qué AHP y no pesos iguales o PCA?

**Respuesta:**

Se analizaron las tres alternativas:

- **Pesos iguales**: asume que todas las variables tienen el mismo impacto en el clima de inversión. Esto es contrafactual — el precio del petróleo tiene mayor impacto en Venezuela que la tasa de alfabetización para decisiones de inversión.

- **PCA**: los pesos reflejan varianza estadística en los datos, no importancia económica. Una variable que varía mucho estadísticamente no necesariamente es la más relevante para inversión. Además, PCA requiere más datos de los disponibles para ser estable.

- **AHP (elegido)**: permite incorporar juicio experto con transparencia. La matriz de comparaciones y el CR = 0.0081 están documentados y son auditables. La correlación AHP–PCA de r = 0.994 valida que la asignación de pesos no introduce distorsión grave.

La limitación del AHP aplicado: los juicios provienen del investigador (Felipe), no de un panel de expertos externos. Esto es una limitación reconocida que debe mencionarse en la tesis. El fortalecimiento metodológico natural sería una ronda Delphi con 3–5 economistas venezolistas.

---

## Q5. ¿Quiénes respaldan los juicios del AHP?

**Respuesta:**

Los pesos AHP reflejan el juicio del investigador, calibrado con literatura de riesgo-país y teoría de inversión en mercados emergentes. Las fuentes que respaldan la jerarquía de pesos son:

- **D1 Macro (25%)**: Bekaert & Harvey (1998) — la inestabilidad macro es el primer determinante de IED en mercados emergentes
- **D2 Energía (20%)**: específico a Venezuela — la literatura sobre petro-estados (Sachs & Warner 1995) justifica el alto peso del sector energético
- **D3 Institucional (20%)**: North (1990), World Bank (2005) — governance es el segundo predictor más robusto de IED
- **D4 Comercial (15%)**: UNCTAD World Investment Report — apertura y flujos como indicadores directos
- **D5 Capital Humano (10%)**: Barro & Lee (2013) — capacidad laboral como habilitador de inversión
- **D6 Percepción (10%)**: Reinhart & Rogoff (2009) — el componente de expectativas y reputación

La limitación es honesta: sin panel Delphi, los pesos son proposiciones académicamente justificadas, no consenso empírico. El análisis de sensibilidad (SI = 0.04) valida que pequeños cambios en pesos no alteran cualitativamente las conclusiones.

---

## Q6. ¿Qué ocurre cuando faltan variables en 2025 o 2026?

**Respuesta:**

El pipeline tiene una política explícita de manejo de NaN:

1. **Por variable**: si un año no tiene dato real, esa variable es NaN para ese año. No se imputa con fallback.

2. **Por dimensión**: en cada año, el aggregator calcula el puntaje dimensional solo con las variables que tienen dato real. Los pesos se redistribuyen proporcionalmente entre las variables disponibles.

3. **Por índice**: el ICIV anual se calcula con la suma de dimensiones disponibles, y se reporta la **cobertura** = fracción del peso total del modelo que tiene datos reales ese año.

Los años recientes tienen cobertura reducida porque las fuentes anuales tienen lag de publicación (WGI 2025 → sep-2026; HDI 2024 → sep-2026; WDI 2025 → dic-2026). Esto es una limitación estructural, no del pipeline.

**Por ello**: los scores 2025 (Parcial 51.9%) y 2026 (Provisional 35.1%) se presentan con etiqueta de tier prominente en el dashboard. No se comparan directamente con años históricos (Histórico ≥85%) sin declarar la diferencia de cobertura.

---

## Q7. ¿Cómo se evita que el score reciente sea incomparable con el histórico?

**Respuesta:**

No se puede eliminar completamente la incomparabilidad — sí se puede medir, declarar y gestionar:

1. **Sistema de tiers**: cuatro categorías de cobertura con colores y descripciones en el dashboard:
   - Histórico ≥85%: series completas → análisis estadístico robusto
   - Útil 70–84.9%: mayoría de fuentes → representativo
   - Parcial 50–69.9%: fuentes con lag → indicativo
   - Provisional <50%: solo alta frecuencia → uso exploratorio

2. **Gráfico con bandas**: los puntos con cobertura < 70% se marcan con símbolo distinto (rombo naranja)

3. **Normalización estable**: el Min-Max usa el rango histórico 2000–2026 como referencia fija. Un score de 34 en 2026 significa lo mismo que un score de 34 en 2012 en términos de la escala del índice.

La recomendación de uso: "El score 2026 = 34.3 es indicativo; puede cambiar significativamente cuando se publiquen WGI y HDI en septiembre 2026."

---

## Q8. ¿Cómo se demuestra que una serie manual no fue inventada?

**Respuesta:**

El proyecto tiene una política de verificación explícita para cada serie manual:

| Serie | Evidencia de trazabilidad |
|-------|--------------------------|
| `fsi_manual.csv` | Cada fila tiene URL específica al Excel oficial de Fund for Peace por año |
| `freedom_house.csv` | 2000–2002: fórmula PR/CL documentada (oficial FH); 2003–2025: URLs directas `freedomhouse.org/country/venezuela/freedom-world/[año]` |
| `rsf.csv` | Pre-2022: OWID press-freedom-rsf.csv (violations_score con inversión 100-x documentada); 2022–2025: URLs Statista/RSF |
| `cpi.csv` | Fuente documentada por fila (TI CPI 2025 Americas report) |
| `hdi.csv` | "UNDP HDR serie histórica validada" — fuente genérica (limitación reconocida) |
| `ief.csv` | "Heritage Foundation IEF serie histórica validada" — fuente genérica (limitación reconocida) |

El test de verificación rápida definido en `iciv/CLAUDE.md`:
1. ¿Puedo reproducirlo corriendo `python scripts/fetch_X.py`?
2. ¿La columna `fuente` dice una URL o publicación citable?
3. ¿Si borro el CSV y re-ejecuto, obtengo el mismo número?

Los únicos ítems donde la respuesta a alguna pregunta es "no completamente" son `hdi.csv` e `ief.csv`, donde la fuente es correcta pero genérica. Esto es una limitación reconocida.

---

## Q9. ¿Por qué se excluyen ciertas fuentes?

**Respuesta:**

Se excluyen dos categorías de fuentes con justificación explícita:

**1. Fuentes venezolanas (BCV, INE, PDVSA, Conatel, OVF)**:
- El BCV dejó de publicar cifras entre 2014–2019 (Vera 2017)
- Cuando volvió a publicar, sus cifras fueron cuestionadas metodológicamente (Hanke 2018)
- El FMI, Banco Mundial y analistas independientes usan sus propias estimaciones para Venezuela, no datos del BCV
- Usar fuentes venezolanas no le daría validez adicional al índice sino que introduciría sesgo de fuente cuestionable

**2. Fuentes sin cobertura histórica**:
- `opensky.csv`: OpenSky no tiene datos ADS-B históricos para Venezuela pre-2020
- `ofac_sanciones_count`: OFAC solo publica el snapshot actual, no historial de sanciones por año
- `basel_aml_index`: Basel Institute cambió URLs → descarga manual no disponible

La política es: si no hay dato real de fuente verificable para un año → NaN. No fallback, no estimación. Esto hace que algunas variables tengan cobertura baja, pero preserva la integridad del índice.

---

## Q10. ¿Puede el índice anticipar inversión o solo describir condiciones?

**Respuesta:**

El ICIV tiene **capacidad descriptiva** robusta y **capacidad predictiva** exploratoria. Esta distinción es importante:

**Lo que puede hacer (descriptivo)**:
- Describe el estado del clima de inversión en Venezuela en cada año histórico (2000–2026)
- Permite comparar períodos históricos (2001–2012 vs 2013–2024)
- Identifica qué dimensiones han mejorado o empeorado
- Señala el nivel actual de riesgo para tomar decisiones de entrada/permanencia

**Lo que es exploratorio (predictivo)**:
- El análisis Granger sugiere una relación temporal ICIV→IED, pero con la nota crítica de que IED es componente del ICIV (circularidad). Este resultado debe interpretarse como coherencia interna, no causalidad externa.
- El ICIV Pulse mensual permite detectar tendencias en tiempo real antes de que se publiquen los datos anuales.
- Los escenarios 2027–2030 no son predicciones sino horizontes condicionados a supuestos explícitos.

**Respuesta directa al jurado**: el ICIV no predice cuándo habrá inversión en Venezuela. Describe cuán favorable es el entorno para recibirla. La decisión de invertir depende de factores idiosincráticos de la empresa que ningún índice puede capturar.

---

## Q11. ¿Qué parte del SATV está implementada hoy y qué parte es trabajo futuro?

**Respuesta:**

**Implementado hoy (SATV actual)**:
- Motor de alertas `src/iciv/satv/engine.py` — calcula alertas por dimensión con umbrales configurables
- 4 niveles de alerta: normal, precaución, deterioro, crítico (+ sin_dato para variables con NaN)
- Alertas calculadas sobre datos reales del pipeline (no simuladas)
- Integrado en el dashboard como sección "Alertas SATV"
- Opera sobre datos anuales

**Trabajo futuro declarado**:
- SATV en frecuencia mensual: el módulo Pulse mensual existe pero el motor SATV no está wired a él (las alertas actuales son anuales)
- Umbrales calibrados con datos históricos de crisis: los umbrales actuales son heurísticos (percentiles) y podrían refinarse con análisis de señales en momentos históricos conocidos (2014, 2017, 2019)
- Notificaciones automáticas: el sistema no envía alertas push, solo las muestra en el dashboard estático

Esta distinción entre implementado y trabajo futuro es transparente en el documento y en el dashboard.

---

## Q12. ¿Qué decisión real debería tomar una empresa con este dashboard?

**Respuesta:**

El ICIV es un **instrumento de diligencia debida inicial**, no un sustituto de análisis específico. Las decisiones concretas que puede informar son:

**Decisiones de entrada**:
- ICIV < 25 ("Riesgo Extremo"): no iniciar operaciones sin análisis de proyecto específico con alta prima de riesgo
- ICIV 25–40 ("Riesgo Alto"): evaluación caso a caso; sectores con contexto geopolítico favorable (energía, minería con partner local) podrían ser viables
- ICIV 40–55 ("Riesgo Moderado"): evaluar por sector usando el Radar Sectorial del dashboard

**Decisiones de permanencia**:
- El SATV emite alertas cuando alguna dimensión se deteriora significativamente. Una empresa ya presente puede usar esto para ajustar su exposición.

**Decisiones de timing**:
- El Pulse mensual detecta tendencias de 3–6 meses antes de que los datos anuales se publiquen. Una mejora sostenida del Pulse es señal de ventana de oportunidad.

**Lo que el ICIV NO puede decir**:
- Si un sector específico tiene rentabilidad suficiente para justificar el riesgo
- Si el marco legal favorece al sector específico de la empresa
- Si existen partners locales con reputación sólida

En suma: el ICIV reduce el costo de la diligencia debida macro pero no la reemplaza para decisiones de inversión concretas.

---

## Preguntas adicionales probables (por perfil de jurado)

### Jurado de Ciencia de Datos / Big Data:

**"¿Por qué no un modelo de ML para predecir el score?"**
> El ICIV es un constructo teórico con pesos basados en teoría económica, no en correlaciones estadísticas históricas. Para un modelo ML necesitaría una variable objetivo externa (ground truth de clima de inversión) que no existe. El enfoque AHP con validación de sensibilidad es el estándar para índices compuestos académicos (OECD Handbook 2008).

**"¿Cómo se garantiza reproducibilidad del pipeline?"**
> Todos los scripts fetch son ejecutables (`python scripts/fetch_X.py`) y producen el mismo resultado con la misma API en el mismo momento temporal. Los datos estáticos (CPI, IEF, HDI, FSI) están en `data/raw/` con fuentes documentadas. `main.py --no-fetch` usa los datos cacheados para reproducibilidad exacta.

### Jurado Economista:

**"¿Cómo justificas que Venezuela mejora de 23.4 (2020) a 33.8 (2024)?"**
> El aumento refleja datos reales: recuperación parcial de producción petrolera (863 vs 527 TBPD), leve mejoría en Freedom House (13 vs 10), dolarización de facto que redujo la hiperinflación efectiva. No es que Venezuela sea un buen destino de inversión — 33.8 sigue siendo "Riesgo Alto". Es que el fondo de 2020 (pandemia + sanciones + colapso petrolero) fue excepcionalmente bajo.

**"¿Cómo sabes que el período de normalización (2000–2026) es apropiado?"**
> El período 2000–2026 captura tanto el auge petrolero (2000–2012, pico 72.2 en 2012) como el colapso (2013–2020, mínimo 23.4) y la recuperación parcial. Es el rango de variación más representativo de Venezuela en el siglo XXI. Un período más corto perdería los mejores años históricos y distorsionaría la escala.

---

*Generado: 21 de mayo de 2026 — Auditoría completa Plan de Revisión del Jurado ICIV*
