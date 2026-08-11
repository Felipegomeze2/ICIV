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

Seis dimensiones, 26 variables core, ponderación por AHP (Saaty, 1980).

| Dimensión | Nombre | Peso ICIV |
|---|---|---:|
| D1 | Estabilidad Macroeconómica | 0,25 |
| D2 | Sector Energético y Petróleo | 0,20 |
| D3 | Entorno Institucional y Legal | 0,20 |
| D4 | Apertura Comercial y Financiera | 0,15 |
| D5 | Capital Humano e Infraestructura Social | 0,10 |
| D6 | Percepción Internacional | 0,10 |
| | **Total** | **1,00** |

> **Estado de D6 al 11-ago-2026 — incidencia abierta.** La corrida automática del
> 3 de agosto de 2026 sobrescribió `data/raw/guardian.csv` con NaN en los 27 años
> (el fetch anual falló contra la API y aun así reescribió el archivo). Desde esa
> fecha **D6 no aporta nada al índice**: el agregador renormaliza sobre las cinco
> dimensiones restantes. Los pesos de esta tabla describen el diseño; mientras la
> incidencia siga abierta, el ICIV publicado se calcula de facto con D1–D5.
> Detalle y solución en la sección 10.

### 2.2 Pesos dentro de cada dimensión

Definidos en `iciv/src/iciv/index/dimensions.py`.

**D1 — Estabilidad Macroeconómica (0,25)**

| Variable | Peso intra-dimensión |
|---|---:|
| `inflacion_deflactor_pib_pct` | 0,28 |
| `pib_crecimiento_real_pct` | 0,22 |
| `reservas_internacionales_usd` | 0,18 |
| `tipo_cambio_oficial_lcu_usd` | 0,12 |
| `wti_precio_usd` | 0,12 |
| `tasa_fed_funds_pct` | 0,08 |

**D2 — Sector Energético y Petróleo (0,20)**

| Variable | Peso intra-dimensión |
|---|---:|
| `petroleo_crudo_produccion_tbpd` | 0,45 |
| `gas_natural_produccion_bcf` | 0,25 |
| `electricidad_generacion_bkwh` | 0,15 |
| `luminosidad_nocturna_idx` | 0,15 |

**D3 — Entorno Institucional y Legal (0,20)**

| Variable | Peso intra-dimensión |
|---|---:|
| `cpi_score` | 0,24 |
| `wgi_promedio_sc` | 0,24 |
| `freedom_house_score` | 0,18 |
| `wjp_rule_of_law` | 0,18 |
| `pts_terror_politico` | 0,16 |

**D4 — Apertura Comercial y Financiera (0,15)**

| Variable | Peso intra-dimensión |
|---|---:|
| `exportaciones_pct_pib` | 0,34 |
| `desempleo_pct` | 0,24 |
| `migrantes_vzla_millones` | 0,24 |
| `lsci_conectividad_maritima` | 0,18 |

**D5 — Capital Humano e Infraestructura Social (0,10)**

| Variable | Peso intra-dimensión |
|---|---:|
| `hdi` | 0,28 |
| `esperanza_vida_anos` | 0,18 |
| `mortalidad_infantil_x1000` | 0,18 |
| `acceso_electricidad_pct` | 0,18 |
| `ilo_empleo_informal_pct` | 0,18 |

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

### 2.5 Regla fundamental

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

## 9. Incidencias abiertas

### 9.1 D6 vacía desde el 3 de agosto de 2026 (crítica)

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

**Solución.** Con la clave renovada (11-ago-2026), volver a poblar la serie:

```bash
cd iciv
python scripts/fetch_guardian.py
python main.py --no-fetch --no-open
```

**Corrección de fondo pendiente:** el fetcher no debe sobrescribir el CSV cuando
no obtuvo ningún dato. La política del proyecto es no fabricar datos, pero
destruir los existentes es peor que no escribir nada. Falta añadir esa guarda —
y revisar si otros fetchers anuales comparten el patrón.

### 9.2 `manifest.json` declara 11 variables Pulse en vez de 15

`n_pulse_variables` sale de contar `entra_pulse_mensual` en el catálogo anual
(`iciv/src/iciv/data/dataset_package.py`), que no incluye las cuatro variables
incorporadas en julio de 2026 (IMF IMTS ×2, WB Pink Sheet, spread EM). Es un
error de metadato en el paquete público; no afecta a ningún cálculo.

### 9.3 Comentario desactualizado en `pulse_forecast.py`

El comentario dice "Probar 2 modelos" pero la lista `candidates` tiene tres
órdenes SARIMA. Los tres reales están documentados en la sección 4.1. Cosmético.

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
