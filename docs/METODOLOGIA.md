# Metodología ICIV — documento canónico

Este documento recoge **toda la metodología del proyecto**. Hasta agosto de 2026
buena parte vivía dentro del dashboard (pestañas de Validación, Metodología Pulse,
Metodología Forecast y Bibliografía). El dashboard pasó a ser el producto para el
usuario final y esas pestañas se retiraron; su contenido quedó aquí, sin recortes.

Documentos complementarios:

- [FUENTES_Y_VARIABLES.md](./FUENTES_Y_VARIABLES.md) — catálogo de variables, fuentes y política de cobertura.
- [MODEL_CARD.md](./MODEL_CARD.md) — alcance, límites y riesgos del modelo.
- [BACKTESTING_FORECAST.md](./BACKTESTING_FORECAST.md) — evaluación fuera de muestra del forecast.
- [VALIDACION_EXTERNA.md](./VALIDACION_EXTERNA.md) — validación leave-one-out no circular.
- [BIBLIOGRAFIA.md](./BIBLIOGRAFIA.md) — referencias académicas y fuentes de datos.
- [DATASET_ICIV.md](./DATASET_ICIV.md) — estructura del paquete público.
- [../iciv/data/sources/PROVENANCE.md](../iciv/data/sources/PROVENANCE.md) — trazabilidad por artefacto.

---

## 1. Escala e interpretación

El ICIV es un índice compuesto en escala **0–100**, donde un valor mayor
significa mejor clima de inversión.

### Bandas de riesgo

| Rango | Categoría | Lectura para el inversionista |
|---|---|---|
| 0–30 | Alto Riesgo | No se recomienda inversión directa |
| 31–50 | Riesgo Moderado-Alto | Solo sectores con alta tolerancia al riesgo |
| 51–65 | Riesgo Moderado | Viable con due diligence reforzado |
| 66–80 | Bajo Riesgo | Condiciones favorables con análisis sectorial |
| 81–100 | Muy Bajo Riesgo | Comparable a mercados emergentes estables |

Las bandas son de interpretación, no de decisión financiera: el ICIV no sustituye
due diligence sectorial ni análisis legal de sanciones.

### Niveles de cobertura

La cobertura es el porcentaje del peso total del modelo que efectivamente tenía
dato ese año o mes. Se publica siempre junto al score, nunca por separado.

| Cobertura | Etiqueta | Significado |
|---|---|---|
| ≥ 85 % | Histórico | Series completas, publicación oficial cerrada |
| 70 – 84,9 % | Útil | Mayoría de fuentes disponibles |
| 50 – 69,9 % | Parcial | Fuentes anuales con rezago; año reciente |
| < 50 % | Provisional | Solo fuentes de alta frecuencia |

En el dashboard, los años con cobertura **inferior al 60 %** (`_COVERAGE_THRESHOLD`
en `main.py`) se dibujan con marcador distinto en la serie histórica.

**Advertencia que hay que saber explicar:** un año reciente puede mostrar un score
alto simplemente porque las dimensiones que aún no publicaron no participan en el
promedio. El salto de 2026 es un artefacto de cobertura, no una recuperación. Por
eso el producto muestra siempre score y cobertura juntos, y las barras de
diagnóstico usan el último año con dato real de cada dimensión.

---

## 2. ICIV anual

### 2.1 Dimensiones y pesos

Seis dimensiones, **21 variables core**, ponderación por AHP (Saaty, 1980).
El core paso de 26 a 21 en la purga del 2026-08-11 (§2.8).

| Dimensión | Nombre | Peso ICIV |
|---|---|---:|
| D1 | Estabilidad Macroeconómica | 0,25 |
| D2 | Sector Energético y Petróleo | 0,20 |
| D3 | Entorno Institucional y Legal | 0,20 |
| D4 | Apertura Comercial y Financiera | 0,15 |
| D5 | Capital Humano e Infraestructura Social | 0,10 |
| D6 | Percepción Internacional | 0,10 |
| | **Total** | **1,00** |

> **Incidencia D6 (3–11 ago 2026) — RESUELTA.** Entre esas fechas el índice se
> publicó sin D6: una corrida automática sobrescribió `data/raw/guardian.csv` con
> NaN en los 27 años. Se restauró el 11-ago-2026 al renovar la clave de la API.
> Los pesos de esta tabla vuelven a describir el cálculo real. Detalle en la
> sección 9.1.

### 2.2 Pesos dentro de cada dimensión

Definidos en `iciv/src/iciv/index/dimensions.py`.

**D1 — Estabilidad Macroeconómica (0,25)**

| Variable | Peso intra-dimensión | Peso final en el índice |
|---|---:|---:|
| `inflacion_deflactor_pib_pct` | 0,4000 | 10,00 % |
| `pib_crecimiento_real_pct` | 0,3143 | 7,86 % |
| `wti_precio_usd` | 0,1714 | 4,29 % |
| `tasa_fed_funds_pct` | 0,1143 | 2,86 % |

**D2 — Sector Energético y Petróleo (0,20)**

| Variable | Peso intra-dimensión | Peso final en el índice |
|---|---:|---:|
| `petroleo_crudo_produccion_tbpd` | 0,7500 | 15,00 % |
| `luminosidad_nocturna_idx` | 0,2500 | 5,00 % |

**D3 — Entorno Institucional y Legal (0,20)**

| Variable | Peso intra-dimensión | Peso final en el índice |
|---|---:|---:|
| `cpi_score` | 0,2400 | 4,80 % |
| `wgi_promedio_sc` | 0,2400 | 4,80 % |
| `freedom_house_score` | 0,1800 | 3,60 % |
| `wjp_rule_of_law` | 0,1800 | 3,60 % |
| `pts_terror_politico` | 0,1600 | 3,20 % |

**D4 — Apertura Comercial y Financiera (0,15)**

| Variable | Peso intra-dimensión | Peso final en el índice |
|---|---:|---:|
| `exportaciones_pct_pib` | 0,4474 | 6,71 % |
| `migrantes_vzla_millones` | 0,3158 | 4,74 % |
| `lsci_conectividad_maritima` | 0,2368 | 3,55 % |

**D5 — Capital Humano e Infraestructura Social (0,10)**

| Variable | Peso intra-dimensión | Peso final en el índice |
|---|---:|---:|
| `hdi` | 0,2800 | 2,80 % |
| `esperanza_vida_anos` | 0,1800 | 1,80 % |
| `mortalidad_infantil_x1000` | 0,1800 | 1,80 % |
| `acceso_electricidad_pct` | 0,1800 | 1,80 % |
| `ilo_empleo_informal_pct` | 0,1800 | 1,80 % |

**D6 — Percepción Internacional (0,10)**

| Variable | Peso intra-dimensión | Peso final en el índice |
|---|---:|---:|
| `guardian_tono_titulares` | 0,6500 | 6,50 % |
| `guardian_articulos_venezuela` | 0,3500 | 3,50 % |
> **Cambio de fuente en D5 (2026-08-11).** `esperanza_vida_anos` y
> `mortalidad_infantil_x1000` pasaron de WHO GHO al World Bank
> (`SP.DYN.LE00.IN`, `SP.DYN.IMRT.IN`), que publica hasta 2024 mientras la OMS
> se quedaba en 2021 y 2023. Se verificó la comparabilidad antes de migrar:
> diferencia media de 1,68 % en esperanza de vida (22 años solapados) y 0,62 %
> en mortalidad (24 años). Se toma la serie **completa** del WB como vintage
> único; **no se empalman** las dos fuentes. El loader de la OMS salió del panel
> maestro; `fetch_who.py` y `who.csv` se conservan para auditoría.

**D6 — Percepción Internacional (0,10)**

| Variable | Peso intra-dimensión |
|---|---:|
| `guardian_tono_titulares` | 0,65 |
| `guardian_articulos_venezuela` | 0,35 |

El peso final de una variable es `peso_dimensión × peso_intra_dimensión`.
Ejemplo: `inflacion_deflactor_pib_pct` pesa 0,25 × 0,28 = 0,07 del índice.

### 2.3 AHP y consistencia

Los pesos salen del vector propio principal de una matriz de comparación por
pares construida a partir de los ratios entre pesos core
(`iciv/src/iciv/index/weighting/ahp_weights.py`).

La consistencia se mide con la Razón de Consistencia de Saaty, `CR = CI / RI`,
donde `CI = (λmax − n) / (n − 1)` y `RI` es el índice aleatorio para matrices de
tamaño `n`. Un juicio es aceptable académicamente si **CR < 0,10**.

Valores de la matriz de dimensiones (n = 6):

| Métrica | Valor |
|---|---:|
| λmax | 6,0501 |
| CI | 0,0100 |
| RI (n = 6) | 1,24 |
| **CR** | **0,0081** |
| ¿Consistente? | Sí (CR < 0,10) |

### 2.4 Tratamiento de los datos

1. Cada loader conserva las observaciones tal como las publica su fuente.
2. El pipeline limpia tipos y aplica transformaciones justificadas.
   Se usa `log10` en `tipo_cambio_oficial_lcu_usd` e `inflacion_deflactor_pib_pct`
   porque su rango cubre varios órdenes de magnitud durante la hiperinflación.
3. Normalización **Min-Max a 0–100** sobre el rango histórico observado.
4. Las variables de riesgo se invierten (`score_inv = 100 − score_norm`) para que
   un valor mayor signifique siempre mejor clima.
5. **Renormalización por disponibilidad:** si una observación falta, su peso se
   redistribuye entre las variables presentes y la cobertura baja. Nunca se
   sustituye por un valor inventado, ni se hace forward-fill sobre el rezago.

### 2.5 Reconversión monetaria del tipo de cambio

El WDI publica el tipo de cambio de cada año en la denominación vigente ese año,
sin unificar. Venezuela redenominó tres veces:

| Fecha | Nueva unidad | Equivalencia | Ceros |
|---|---|---|---:|
| 2008-01-01 | Bolívar Fuerte (Bs.F) | 1 Bs.F = 1.000 Bs | 3 |
| 2018-08-20 | Bolívar Soberano (Bs.S) | 1 Bs.S = 100.000 Bs.F | 5 |
| 2021-10-01 | Bolívar Digital (Bs.D) | 1 Bs.D = 1.000.000 Bs.S | 6 |

El pipeline lleva todo a Bs.F equivalente (`Bs.S × 1e5`, `Bs.D × 1e11`) y aplica
`log10` antes de normalizar.

**Corrección 2026-08-11.** Los factores anteriores eran `1e3` y `1e9`: usaban
1.000 para la reconversión de 2018, que en realidad quitó cinco ceros y no tres.
Ambos estaban 100× por debajo, lo que comprimía el salto real 2017→2020 de 9,5 a
7,5 órdenes de magnitud y desplazaba la normalización Min-Max de toda la serie.
Hay tests de regresión en `tests/test_processing/test_reconversion_monetaria.py`.

### 2.6 Año en curso de la producción petrolera

`petroleo_crudo_produccion_tbpd` pesa 9 % del índice, más que ninguna otra
variable, y la serie anual de EIA llega con cerca de un año de rezago. Desde
2026-08-11 el año en curso se completa con el promedio de los meses ya
publicados de la serie **mensual del mismo producto**.

Esto no es una estimación ni un relleno: es el mismo estadístico, de la misma
fuente, en la misma unidad. Se verificó antes de implementarlo.

| Producto EIA | Descripción | Uso |
|---:|---|---|
| 53 | Total petroleum and other liquids | Pulse mensual |
| **57** | **Crude oil including lease condensate** | **ICIV anual** |

El promedio de los meses del producto **57** reproduce la serie anual con una
diferencia media del **0,05 %** (máx. 0,16 %) sobre 11 años completos. El
producto 53 **no** la reproduce: difiere entre 3 % y 13 %, porque incluye otros
líquidos. Confundirlos habría sido mezclar bases.

Reglas de la anualización:

- Solo se completan años cuyo valor anual es NaN. Nunca se pisa un dato real.
- Se exige un mínimo de 3 meses publicados para no extrapolar de una observación.
- El valor es el promedio del **año corrido**, no una proyección del año completo.
- Cada anualización queda registrada en `data/processed/anualizacion_parcial.csv`
  con el número de meses usados, para que sea auditable.

### 2.8 Purga de variables sin fuente viva (2026-08-11)

El core pasó de **26 a 21 variables**. Se eliminaron cinco que arrastraban peso
muerto: o su fuente dejó de publicar, o publica con un rezago que impide
describir el presente.

| Variable | Dim | Peso que tenía | Motivo |
|---|---|---:|---|
| `reservas_internacionales_usd` | D1 | 4,5 % | El WB no publica desde 2017. Probados sin éxito `FI.RES.XGLD.CD` (2017), `FI.RES.TOTL.MO` (2016), `FI.RES.TOTL.DT.ZS` (sin serie). |
| `tipo_cambio_oficial_lcu_usd` | D1 | 3,0 % | El WB **retiró** los valores 2020-2024 en agosto de 2026. Muere en 2017. |
| `desempleo_pct` | D4 | 3,6 % | El IMF WEO dejó de publicarlo en 2018. Sustitución por OIT descartada (§9.6). |
| `gas_natural_produccion_bcf` | D2 | 5,0 % | Solo existe anual en EIA, con ~2 años de rezago. Verificado: **no hay serie mensual** para Venezuela. |
| `electricidad_generacion_bkwh` | D2 | 3,0 % | Igual que el gas: solo anual, sin equivalente mensual. |

Los pesos internos de D1, D2 y D4 se renormalizaron conservando la proporción
entre las variables que quedan. Las matrices AHP se actualizaron en paralelo;
la consistencia se mantiene (CR = 0,008 en la matriz de dimensiones).

**Los datos no se borran.** Los fetchers siguen descargando estas series y los
CSV permanecen en `data/raw/` como contexto y para auditoría. Lo que cambia es
que dejan de contar en el score y en la cobertura.

**Criterio para futuras purgas:** una variable sale del core cuando su fuente
no publica desde hace más de tres años y no existe sustituto verificado, o
cuando su rezago estructural le impide cubrir el año anterior al corriente.

### 2.9 Regla fundamental

**Cero datos inventados, cero fallbacks estáticos.** Si una fuente no responde o
no ha publicado, la cobertura lo refleja. No se crean series sustitutas y no se
mezclan bases distintas de un mismo indicador (por ejemplo, LSCI de UNCTAD y de
WDI tienen bases distintas y nunca se empalman).

---

## 3. ICIV Pulse mensual

Co-indicador de alta frecuencia con **15 variables mensuales** observadas, desde
enero de 2010. No reemplaza al ICIV anual: cubre el hueco entre publicaciones
anuales, que tienen rezagos de 12 a 18 meses.

Marco teórico: Aruoba, Diebold & Scotti (2009) y Stock & Watson (2002).

La tabla completa de variables, fuentes y pesos está en
[FUENTES_Y_VARIABLES.md](./FUENTES_Y_VARIABLES.md#variables-pulse).
Estructura por bloques tras la ampliación de julio de 2026: macro externo 35 %,
energía 25 %, comercio espejo 10 %, percepción 30 %.

### 3.3 Comercio espejo: de IMF IMTS a aduana de EEUU vía FRED (2026-08-11)

El bloque de comercio espejo (10 % del Pulse) usaba IMF IMTS, que llega con
**cuatro meses** de rezago. Se sustituyó por dos series de FRED:

| Serie | Qué mide | Historia | Rezago |
|---|---|---:|---:|
| `IR14270` → `importaciones_eeuu_crudo_ven_tbpd` | Importaciones de crudo venezolano por EEUU (miles b/d) | 198 meses | **2 meses** |
| `IR14260` → `importaciones_eeuu_productos_ven_tbpd` | Importaciones de productos petroleros | 198 meses | **2 meses** |

Mismo concepto económico —comercio real observado por el socio, sin tocar
fuentes venezolanas— pero con la mitad del rezago, volumen físico en lugar de
valor declarado, y más historia. `imts_monthly.csv` se conserva como capa de
contexto y validación cruzada.

**Efecto en la oportunidad del Pulse:** el último mes con cobertura ≥70 % pasó
de **t−4 a t−2**. La cobertura media de la serie completa es del 90,4 % y 198 de
200 meses superan el umbral del 70 %.

Estructura de rezago resultante:

| Rezago | Peso | Fuentes |
|---|---:|---|
| 0 meses | 61 % | FRED global (7), Guardian (2), GDELT (2) |
| 1 mes | 4 % | WB Pink Sheet |
| 2 meses | 10 % | Comercio espejo EEUU (FRED) |
| 4 meses | 25 % | Producción petrolera EIA |

El mes en curso no puede superar el 61 % porque ese es el peso de las fuentes
sin rezago. No es un defecto corregible añadiendo fuentes: es la consecuencia de
que la producción petrolera —la variable más importante para Venezuela— se
publica con cuatro meses de retraso. Bajarle el peso para maquillar la cobertura
sería falsear la metodología. Por eso el producto muestra como referencia el
último mes con cobertura suficiente, y el mes corriente como avance.

### 3.1 Algoritmo de construcción

Para cada mes `t` (`iciv/src/iciv/index/pulse_aggregator.py`):

1. Recopilar todas las variables con dato real disponible ese mes.
2. Normalizar cada variable con Min-Max sobre su rango histórico en el panel.
3. Invertir las variables de dirección negativa: `score_inv = 100 − score_norm`.
4. Calcular el peso disponible = suma de los pesos de las variables con dato.
5. **Si el peso disponible < 0,30 → `Pulse(t) = NaN`.** Con menos del 30 % del
   modelo presente no se publica un score.
6. Renormalizar los pesos sobre las variables disponibles.
7. `Pulse(t) = Σ(peso_renormalizado × score_normalizado)`.
8. Publicar `cobertura_pct` (= peso disponible × 100) y `n_vars` junto al score.

Un score con cobertura inferior al 70 % debe leerse como provisional.

### 3.2 Limitaciones declaradas

- Se excluyen por política todas las fuentes originadas en Venezuela.
- La cobertura varía mes a mes según la disponibilidad de las APIs.
- GDELT aplica rate limit por frecuencia de peticiones; si un tramo falla, la
  cobertura baja y no se fabrica una serie sustituta. El fetch deja constancia
  en `gdelt_monthly.status.json`.
- WTI y Brent son factores exógenos globales, no medidas de Venezuela.
- `em_bond_spread_pct` solo cubre desde 2023-07: FRED redistribuye una ventana
  móvil de ~3 años por licenciamiento.

---

## 4. Predicción del Pulse

### 4.1 SARIMA — la única predicción visible

Implementado en `iciv/src/iciv/ml/pulse_forecast.py`.

- **Especificación:** SARIMA(p,d,q)(P,D,Q)ₛ con s = 12, para capturar tendencia,
  estacionalidad anual y autocorrelación.
- **Selección de orden:** se ajustan tres candidatos y se elige el de menor AIC
  (Akaike Information Criterion):
  - (1,1,1)(1,1,1,12)
  - (1,1,2)(1,1,1,12)
  - (2,1,1)(1,1,1,12)

  El orden y el AIC elegidos quedan en el payload del forecast
  (`sarima_best_order`, `sarima_aic`).
- **Entrada:** solo meses con `cobertura_pct ≥ 70`. Huecos internos se imputan
  linealmente con `limit=2`. Si la serie tiene menos de 24 observaciones, se omite.
- **Horizonte:** 6 meses.
- **Intervalos:** 80 % (`alpha = 0,20`) y 95 % (`alpha = 0,05`).
- **Recorte:** las predicciones y las bandas se recortan al dominio [0, 100].

La evaluación fuera de muestra (rolling-origin contra naive, seasonal naive y ETS)
está en [BACKTESTING_FORECAST.md](./BACKTESTING_FORECAST.md).

### 4.2 Nowcast OLS Pulse → ICIV anual

Modelo auxiliar que estima el ICIV anual del año en curso a partir de los meses
Pulse ya disponibles. **No se muestra en el producto**; se conserva en el pipeline.

- **Features:** `pulse_avg` (promedio de meses disponibles) y `pulse_trend`
  (cambio contra el año anterior). Con `n ≥ 11` años de entrenamiento se añaden
  `pulse_min`, `pulse_max` y `pulse_std`.
- **Anti-sobreajuste:** con `n < 11` solo se usan 2 features.
- **Validación:** Leave-One-Out Cross-Validation, más honesta que el R² dentro de
  muestra cuando `n` es pequeño.
- **Datos:** se usa `dropna()`, nunca `fillna(0)`. Solo entran años con ambos
  datos reales.
- Referencia: Stock & Watson (2002), *JBES* 20(2), 147–162.

---

## 5. SATV — alertas del Pulse

El SATV no es un segundo índice: traduce el Pulse en alertas de cobertura, nivel
y tendencia reciente. Se alimenta exclusivamente del Pulse para que la frecuencia
de las alertas sea coherente (mensual), y no mezcla señales anuales con mensuales.

Resume tres grupos de señales observadas — macro global, energía y noticias
internacionales — y marca cobertura parcial, Pulse bajo y deterioros sostenidos
de tres meses. Es un monitor operacional, no una predicción ni una validación
retrospectiva del ICIV anual.

En el producto solo se muestran las alertas activas. El detalle por grupo de
señales y el histórico de meses en zona crítica quedaron fuera de la vista de
usuario por decisión de diseño (agosto 2026).

---

## 6. Investment Entry Radar Sectorial

Implementado en `iciv/src/iciv/analytics/sector_radar.py` (v1.0).

**Score base:** `Σ DimScore(d) × PesoSectorial(s,d)` — cada sector tiene su propio
vector de sensibilidad a las seis dimensiones del ICIV.

**Ajustadores aplicados sobre el score base:**

- Penalización regulatoria.
- Penalización CAPEX: solo se activa cuando el ICIV está por debajo del umbral
  configurado y escala linealmente con la distancia a ese umbral.
- Bonus de demanda defensiva, para sectores cuya demanda no colapsa con el ciclo.

**Manejo de faltantes:** si una dimensión es NaN se excluye y los pesos se
renormalizan sobre las disponibles — la misma lógica del agregador ICIV. Si todas
son NaN, el sector devuelve NaN en vez de un cero engañoso.

**Umbrales de recomendación:**

| Score | Recomendación |
|---|---|
| ≤ 35 | No entrar |
| 36 – 50 | Esperar |
| 51 – 65 | Piloto |
| 66 – 80 | Entrada |
| > 80 | Prioritaria |

---

## 7. Validación

### 7.1 Validación externa no circular (leave-one-out)

Es la validación principal del proyecto. Se recalcula el ICIV **excluyendo** la
variable contra la que se va a validar (y redistribuyendo su peso), y se
correlaciona ese ICIV reducido contra la serie cruda excluida. Así el score
validado no contiene información directa del validador.

Resultados y detalle en [VALIDACION_EXTERNA.md](./VALIDACION_EXTERNA.md).
Script: `iciv/scripts/external_validation.py`.

### 7.2 Coherencia interna: ICIV → IED (exploratorio)

`ied_neta_usd` **no entra al score core**. Se reserva como outcome económico
externo para preguntar si un mejor clima antecede flujos de inversión más
favorables. El análisis incluye correlación de Pearson, regresión OLS y prueba de
causalidad de Granger sobre 2000–2026.

**Este bloque es exploratorio, no prueba causal.** El tamaño muestral anual, los
rezagos de publicación y la dinámica de desinversión en Venezuela impiden leerlo
como evidencia suficiente. Se documenta como tal para que el jurado no lo
sobreinterprete.

### 7.3 Validaciones internas del modelo

Generadas por `iciv/scripts/validate_model.py`, que produce el informe
independiente `iciv/data/processed/iciv_validacion.html`:

- **Análisis de sensibilidad (SI):** cuánto se mueve el score al perturbar pesos.
- **Consistencia AHP:** CR de la matriz de comparación por pares.
- **Lineal vs geométrico:** MAD y correlación entre ambas formas de agregación.
- **AHP vs PCA:** compara los pesos de juicio experto contra los pesos empíricos
  del primer componente principal, y reporta la varianza explicada por PC1.

Este informe **no** depende del dashboard: se genera aparte y sobrevive a
cualquier cambio de la capa visual.

---

## 8. Capas auxiliares (no entran al score)

Se documentan en detalle en [FUENTES_Y_VARIABLES.md](./FUENTES_Y_VARIABLES.md) y
[MODEL_CARD.md](./MODEL_CARD.md).

| Capa | Qué aporta | Estado |
|---|---|---|
| NASA Black Marble VNP46A3 | Radiancia nocturna absoluta por estado, 25 estados, 149 meses (2014–2026) | Visible en el producto como mapa único |
| Comercio espejo multi-socio | IMF IMTS (EEUU) + UN Comtrade (España, Brasil, India, Türkiye, China) | Contextual |
| ACLED | Eventos de conflicto, protestas y fatalidades | Contextual; el tier gratuito entrega con ~12 meses de rezago |

**Decisión sobre Black Marble (julio 2026):** se evaluaron cinco agregaciones
(media, mediana, logmedia, p90, fracción iluminada) contra la serie anual de
Li et al. La media es la que mejor correlaciona (Pearson r = +0,649, p = 0,031);
las agregaciones robustas no mejoran. Conclusión honesta: capturan una señal
distinta, no mejor. Black Marble queda como capa auxiliar de alta frecuencia y
subnacional, y **no entra al Pulse**, porque la media ya está representada en la
luminosidad anual del score.

---

## 9. Incidencias

### 9.1 D6 vacía del 3 al 11 de agosto de 2026 — RESUELTA

**Qué pasó.** `iciv/scripts/fetch_guardian.py` recorre año por año; si una
petición falla, registra `None` y **continúa**. Al terminar escribe el CSV
siempre, sin comprobar si obtuvo algún dato. Cuando la clave de la API dejó de
funcionar, todos los años fallaron y el script sobrescribió 27 años de datos
buenos con NaN, terminando con código de salida 0.

**Trazabilidad.** `guardian.csv` tenía 27/27 valores hasta el commit `53fb2be`
(2026-07-30) y quedó en 0/27 en `e9089f5` (2026-08-03).

**Impacto.** D6 Percepción Internacional pesa 0,10 del índice y no aporta nada
desde esa fecha. El agregador renormaliza sobre D1–D5, así que los scores
publicados el 3 y el 10 de agosto ya salieron sin esa dimensión. También afecta
al simulador del Laboratorio, que queda con cinco palancas.

**Lo que NO afecta.** `guardian_monthly.csv` está intacto (398/398 filas): el
Pulse conserva sus dos variables Guardian. La incidencia es solo de la serie
anual.

**Resolución (11-ago-2026).** Se renovó la clave de la API y la corrida
automática repobló la serie: 27/27 valores en ambas columnas. D6 volvió al
índice y, como efecto colateral, desapareció una discrepancia que se creía
independiente — el simulador del Laboratorio marcaba 21,4 frente a un índice
2025 de 22,6; con D6 restaurada ambos coinciden en 22,7.

**Corrección de fondo aplicada.** Se añadió `iciv/src/iciv/utils/safe_save.py`
con `save_dataframe()`: si la descarga no trae ningún valor, lanza `NoDataError`
y **no toca el archivo existente**. La auditoría encontró que seis fetchers
anuales compartían el patrón destructivo — `fetch_eia`, `fetch_fred`,
`fetch_guardian`, `fetch_imf`, `fetch_wdi` y `fetch_wgi`, es decir las fuentes
que alimentan D1, D2 y D3. Los seis usan ahora la guarda. En el workflow cada
fetcher está envuelto en `|| echo WARN`, así que un fallo queda visible en el
log en vez de vaciar el índice en silencio.

### 9.2 `manifest.json` declaraba 11 variables Pulse — RESUELTA

`n_pulse_variables` se contaba sobre `entra_pulse_mensual` del catálogo anual,
que no incluye las cuatro variables solo-mensuales de julio de 2026 (IMF IMTS ×2,
WB Pink Sheet, spread EM). Ahora se cuenta sobre `PULSE_WEIGHTS`, la fuente de
verdad del Pulse. El manifest declara 15.

### 9.3 Comentario desactualizado en `pulse_forecast.py` — RESUELTA

El comentario y el docstring decían "2 modelos" cuando `candidates` tiene tres
órdenes SARIMA. Corregidos.

### 9.4 Variables sin fuente viva — DECISIÓN PENDIENTE

Dos variables del core no tienen ya fuente publicada y arrastran peso muerto:

| Variable | Peso | Último dato | Estado de la fuente |
|---|---:|---:|---|
| `reservas_internacionales_usd` | 4,5 % | 2017 | El WB no publica más allá de 2017. Se probaron `FI.RES.XGLD.CD` (2017), `FI.RES.TOTL.MO` (2016) y `FI.RES.TOTL.DT.ZS` (sin serie). Sin sustituto. |
| `tipo_cambio_oficial_lcu_usd` | 3,0 % | 2017 | El WB **retiró** los valores 2020–2024 entre julio y agosto de 2026. El refetch del 2026-08-11 los perdió. |

Juntas son **7,5 % del modelo** que nunca se llena. Son la razón de que ni
siquiera un año completo pase de ~90 % de cobertura.

**Consecuencia visible de la retirada del tipo de cambio:** esa variable
puntuaba 0,00 en 2024 (la peor lectura posible). Al desaparecer, el agregador
renormaliza sobre las restantes y el score **sube sin que nada haya mejorado**:
2024 pasó de 28,31 a 36,59 y 2023 de 30,67 a 35,31. Es un artefacto de
disponibilidad, no una recuperación. Debe explicarse así.

Las tres salidas posibles, ninguna aplicada todavía porque cambian el modelo:

1. **Retirar ambas** y redistribuir su peso entre las 24 variables restantes.
   Sube la cobertura de todos los años (2024 llegaría a ~93 %) pero reduce el
   core de 26 a 24 variables. Hay que declararlo, no presentarlo como "subí la
   cobertura".
2. **Restaurar el tipo de cambio** desde el histórico de git (los valores son
   reales y están en `wdi.csv` antes del commit `918cf09`), documentando el
   vintage. Conserva la serie, pero el dato ya no es verificable en la fuente.
3. **Dejarlo como está**: NaN honesto y cobertura baja.

### 9.5 GDELT: tramos que no completan (abierta, sin impacto)

`gdelt_monthly.status.json` reporta `ok: false` de forma recurrente. En la
corrida del 11-ago-2026 fallaron los seis intentos (2026, 2016 y 2015) y no
entró ningún tramo nuevo. **El CSV se conserva** — a diferencia de Guardian,
este fetcher sí protege los datos previos, así que la serie mantiene sus 232
filas hasta 2026-08. Los años 2015 y 2016 llevan varias corridas sin cerrar.
El diseño acumulativo los reintenta cada semana; no requiere acción.

### 9.6 Desempleo: sustitución descartada tras verificarla

El WB publica `SL.UEM.TOTL.ZS` (estimación modelada de la OIT) con datos hasta
**2025**, mientras la serie actual (IMF WEO `LUR`) muere en **2018**. Parecía la
mejor oportunidad de cobertura del proyecto: 3,6 % de peso × 7 años.

**Se descartó al comprobar que no son comparables.** En los 19 años solapados la
diferencia media es del 23 % y llega al 85 %:

| Año | IMF WEO | OIT modelado | Diferencia |
|---:|---:|---:|---:|
| 2016 | 20,9 % | 5,3 % | −74,6 % |
| 2017 | 27,9 % | 5,0 % | −81,9 % |
| 2018 | 35,6 % | 5,5 % | −84,6 % |

El modelo de la OIT no captura el colapso laboral venezolano ni la emigración
masiva: sostiene un desempleo del 5 % durante toda la crisis. Empalmarlas habría
metido en el índice la señal de que el mercado laboral venezolano está sano.
Es exactamente el error que ya se cometió una vez al mezclar bases del LSCI.

`desempleo_pct` se queda con la fuente del IMF y su hueco desde 2019.

### 9.7 ACLED con 12 meses de rezago (abierta, limitación del proveedor)

El tier gratuito entrega los datos con un año de retraso: la serie termina en
2025-08. Es limitación de la cuenta, no del código. Para uso en tiempo real
haría falta acceso académico de ACLED.

---

## 10. Reproducir

```bash
cd iciv
pip install -e ".[dev]"
python main.py --no-fetch --no-open
```

Validación del modelo por separado:

```bash
cd iciv
python main.py --validate-only
```

Control de vigencia de las fuentes Pulse:

```bash
cd iciv
python scripts/check_pulse_inputs.py
```

Las credenciales nunca se versionan: se leen de variables de entorno o de
`iciv/.env` (ignorado por git). Ver `iciv/.env.example` para la lista completa.
