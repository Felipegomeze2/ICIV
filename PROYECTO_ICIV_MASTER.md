# ICIV — Indicador de Clima de Inversión Venezuela
## Documento Maestro del Proyecto · Tesis de Posgrado

> **Especialización:** Big Data e Inteligencia de Negocios  
> **Autor:** Felipe  
> **Objetivo:** Diseñar un indicador macroeconómico compuesto que le permita a empresas evaluar si entrar a invertir en Venezuela, con nivel académico de tesis de posgrado.  
> **Nivel:** Tesis de especialización (posgrado)

---

## Tabla de Contenidos

1. [Visión general del producto final](#1-visión-general-del-producto-final)
2. [Nombre y definición del índice](#2-nombre-y-definición-del-índice)
3. [Las 5 dimensiones del ICIV](#3-las-5-dimensiones-del-iciv)
4. [Variables e indicadores base](#4-variables-e-indicadores-base)
5. [Fuentes de datos](#5-fuentes-de-datos)
6. [Metodología paso a paso](#6-metodología-paso-a-paso)
7. [Pipeline técnico de Big Data](#7-pipeline-técnico-de-big-data)
8. [Estructura de la tesis](#8-estructura-de-la-tesis)
9. [Stack tecnológico recomendado](#9-stack-tecnológico-recomendado)
10. [Entregables del proyecto](#10-entregables-del-proyecto)
11. [Hoja de ruta y fases de construcción](#11-hoja-de-ruta-y-fases-de-construcción)
12. [Criterios de interpretación del índice](#12-criterios-de-interpretación-del-índice)
13. [Referencias e índices similares (benchmarks)](#13-referencias-e-índices-similares-benchmarks)
14. [Notas y decisiones de diseño pendientes](#14-notas-y-decisiones-de-diseño-pendientes)

---

## 1. Visión General del Producto Final

El producto final de esta tesis es un **sistema de indicadores macroeconómicos compuestos** que se materializa en tres capas:

### Capa 1 — El Modelo Cuantitativo (núcleo académico)
Un índice compuesto en escala **0–100** construido a partir de 10–15 variables macroeconómicas. Cada variable se normaliza, se pondera por importancia relativa y se agrega en un puntaje único. Es la contribución científica central de la tesis y debe estar rigurosamente justificada en literatura académica.

### Capa 2 — El Pipeline de Big Data (justificación de la especialización)
Un proceso automatizado en Python que:
- Recolecta datos de APIs y fuentes públicas internacionales
- Limpia, transforma y normaliza las series históricas
- Alimenta el modelo de cálculo del índice
- Permite actualización periódica con mínima intervención manual

Esto es lo que diferencia la tesis de un análisis económico convencional: la **reproducibilidad**, la **automatización** y el **procesamiento de datos a escala**.

### Capa 3 — El Dashboard Interactivo (producto para el usuario final)
Una interfaz visual donde una empresa puede ver:
- El puntaje compuesto actual del ICIV (0–100)
- Su evolución histórica en el tiempo
- El desglose por dimensión (¿qué está fallando y qué no?)
- La comparación con países de la región
- La tabla de indicadores con semáforos de alerta
- Una recomendación de inversión clara (Invertir / Esperar / No entrar)

**Plataforma sugerida:** Streamlit (Python), Power BI, Tableau, o HTML/JS estático.  
**Prototipo visual ya creado en:** `ICIV_Dashboard_Prototipo.html`

---

## 2. Nombre y Definición del Índice

**Nombre completo:** Indicador de Clima de Inversión Venezuela (ICIV)  
**Escala:** 0 (peor clima posible) a 100 (mejor clima posible)  
**Naturaleza:** Índice compuesto, multidimensional, ponderado  
**Periodicidad:** Anual (con módulo ICIV Pulse mensual 2010–2026 para monitoreo de alta frecuencia)  
**Cobertura histórica:** 2000–2026 (25 años, base completa para análisis de tendencias)

### Categorías de interpretación del puntaje

| Rango | Categoría | Señal para inversores |
|-------|-----------|----------------------|
| 0 – 30 | 🔴 Alto Riesgo | No se recomienda entrada. Esperar. |
| 31 – 50 | 🟠 Riesgo Moderado-Alto | Solo sectores con alta tolerancia al riesgo y cobertura específica. |
| 51 – 65 | 🟡 Riesgo Moderado | Viable con due diligence reforzado y estructura de mitigación. |
| 66 – 80 | 🟢 Bajo Riesgo | Condiciones favorables. Recomendable con análisis sectorial. |
| 81 – 100 | 🟢🟢 Muy Bajo Riesgo | Clima de inversión sólido. Entrada recomendada. |

---

## 3. Las 6 Dimensiones del ICIV

El índice se organiza en **6 dimensiones** que capturan aspectos distintos pero complementarios del clima de inversión. Cada dimensión tiene un peso asignado en el índice final. Los pesos fueron determinados mediante el Proceso de Jerarquía Analítica (AHP, Saaty 1980) con Razón de Consistencia CR = 0.0081 (< 0.10, aceptable).

### Dimensión 1 — Estabilidad Macroeconómica (Peso: 25% — AHP)
Mide la salud del entorno económico general: inflación, crecimiento, reservas, tipo de cambio, precio del petróleo y tasas de interés globales. Es la dimensión con mayor peso porque sin estabilidad macro, las otras dimensiones se vuelven irrelevantes para un inversor. **6 variables.**

### Dimensión 2 — Sector Energético y Petróleo (Peso: 20% — AHP)
Venezuela posee las mayores reservas probadas de petróleo del mundo. Esta dimensión captura el estado de la industria petrolera (producción cruda, gas, electricidad, luminosidad nocturna satelital) como motor principal de ingresos fiscales y divisas. **4 variables.**

### Dimensión 3 — Entorno Institucional y Legal (Peso: 20% — AHP)
Mide la seguridad jurídica, la corrupción, la gobernanza y la protección al inversor: CPI, WGI, IEF, Freedom House, sanciones OFAC y represión política (PTS). Un entorno institucional débil genera riesgo expropiatorio y contractual. **6 variables.**

### Dimensión 4 — Apertura Comercial y Financiera (Peso: 15% — AHP)
Mide la capacidad de operar en Venezuela: IED, exportaciones, desempleo, el éxodo migratorio, conectividad marítima (LSCI) y conectividad aérea (aerolíneas). **6 variables.**

### Dimensión 5 — Capital Humano e Infraestructura (Peso: 10% — AHP)
Mide la disponibilidad de fuerza laboral calificada y la capacidad de infraestructura del país. Incluye salud (esperanza de vida, mortalidad infantil) y acceso a servicios básicos. **5 variables.**

### Dimensión 6 — Percepción Internacional (Peso: 10% — AHP)
Nueva dimensión que captura la imagen de Venezuela en medios internacionales y en el interés de búsqueda global. Incluye tono de cobertura mediática (VADER), volumen de artículos y Google Trends. Es un indicador adelantado del sentimiento inversor. **3 variables.**

---

## 4. Variables e Indicadores Base

El ICIV incluye **29 variables** distribuidas en 6 dimensiones. Los pesos de cada dimensión en el ICIV final fueron determinados mediante AHP (Saaty 1980, CR=0.0081). Los pesos de variables dentro de cada dimensión están documentados en `config/settings.yaml` y `src/iciv/data/catalog.py`.

> **Principio de datos:** CERO datos inventados o estimados estáticamente. Cada variable es real o NaN. Ver bitácoras `04_datos_reales_y_nuevas_fuentes.md` y `05_auditoria_fuentes_datos.md`.

### Dimensión 1: Estabilidad Macroeconómica (25% del ICIV) — 6 variables

| Variable (columna) | Descripción | Fuente | Dirección |
|-------------------|-------------|--------|-----------|
| `inflacion_deflactor_pib_pct` | Deflactor del PIB — proxy de inflación general | IMF DataMapper | Negativa |
| `pib_crecimiento_real_pct` | Crecimiento real del PIB (%) | WDI | Positiva |
| `reservas_internacionales_usd` | Reservas internacionales totales (USD) | WDI | Positiva |
| `tipo_cambio_oficial_lcu_usd` | Tipo de cambio oficial — log₁₀(BsF/USD equiv.) | WDI | Negativa |
| `wti_precio_usd` | Precio del petróleo WTI (USD/barril) | FRED (DCOILWTICO) | Positiva |
| `tasa_fed_funds_pct` | Tasa Fed Funds efectiva anual (%) | FRED (FEDFUNDS) | Negativa |

### Dimensión 2: Sector Energético y Petróleo (20% del ICIV) — 4 variables

| Variable (columna) | Descripción | Fuente | Dirección |
|-------------------|-------------|--------|-----------|
| `petroleo_crudo_produccion_tbpd` | Producción de petróleo crudo (Mbpd) | EIA API v2 | Positiva |
| `gas_natural_produccion_bcf` | Producción de gas natural (BCF/año) | EIA API v2 | Positiva |
| `electricidad_generacion_bkwh` | Generación eléctrica total (bkWh/año) | EIA API v2 | Positiva |
| `luminosidad_nocturna_idx` | Luminosidad nocturna satelital (proxy infraestructura) | NOAA EOG VIIRS* | Positiva |

*VIIRS requiere autenticación NASA Earthdata — variable queda NaN si no se descarga manualmente.

### Dimensión 3: Entorno Institucional y Legal (20% del ICIV) — 6 variables

| Variable (columna) | Descripción | Fuente | Dirección |
|-------------------|-------------|--------|-----------|
| `cpi_score` | Índice de Percepción de Corrupción (0–100) | Transparency International | Positiva |
| `wgi_promedio_sc` | Promedio de 6 indicadores WGI (percentil) | Banco Mundial WGI | Positiva |
| `ief_overall_score` | Índice de Libertad Económica (0–100) | Heritage Foundation | Positiva |
| `freedom_house_score` | Score democracia y libertades civiles (0–100) | Freedom House | Positiva |
| `ofac_sanciones_count` | Conteo de entidades venezolanas en lista SDN-OFAC | US Treasury OFAC | Negativa |
| `pts_terror_politico` | Escala de Terror Político promedio AI/HRW/State (1–5) | PTS — Gibney et al. | Negativa |

### Dimensión 4: Apertura Comercial y Financiera (15% del ICIV) — 6 variables

| Variable (columna) | Descripción | Fuente | Dirección |
|-------------------|-------------|--------|-----------|
| `ied_neta_usd` | Inversión Extranjera Directa neta (USD) | WDI | Positiva |
| `exportaciones_pct_pib` | Exportaciones de bienes y servicios (% PIB) | WDI | Positiva |
| `desempleo_pct` | Tasa de desempleo (% de la fuerza laboral) | IMF DataMapper | Negativa |
| `migrantes_vzla_millones` | Venezolanos en el exterior (millones de personas) | UNHCR API (coo=VEN) | Negativa |
| `lsci_conectividad_maritima` | LSCI — Conectividad marítima (0–100) | World Bank WDI (IS.SHP.GCNW.XQ) | Positiva |
| `vuelos_aerolineas_int_count` | Aerolíneas internacionales con servicio regular (nº) | OpenSky | Positiva |

### Dimensión 5: Capital Humano e Infraestructura (10% del ICIV) — 5 variables

| Variable (columna) | Descripción | Fuente | Dirección |
|-------------------|-------------|--------|-----------|
| `hdi` | Índice de Desarrollo Humano (0–1) | PNUD / UNDP | Positiva |
| `tasa_alfabetizacion_adulta_pct` | Tasa de alfabetización adulta ≥15 años (%) | WDI | Positiva |
| `acceso_electricidad_pct` | Porcentaje de la población con acceso eléctrico | WDI | Positiva |
| `esperanza_vida_anos` | Esperanza de vida al nacer, ambos sexos (años) | WHO GHO API | Positiva |
| `mortalidad_infantil_x1000` | Tasa mortalidad infantil 0-11m (x1000 NV) | WHO GHO / UN IGME | Negativa |

### Dimensión 6: Percepción Internacional (10% del ICIV) — 3 variables

| Variable (columna) | Descripción | Fuente | Dirección |
|-------------------|-------------|--------|-----------|
| `guardian_tono_titulares` | Sentimiento VADER de titulares del Guardian (−1 a +1) | The Guardian API | Positiva |
| `guardian_articulos_venezuela` | Volumen anual de artículos sobre Venezuela | The Guardian API | Negativa |
| `google_trends_vzla` | Interés global de búsqueda "Venezuela inversión" (0–100) | Google Trends | Positiva |

---

## 5. Fuentes de Datos

Todas las fuentes son públicas, gratuitas y con acceso programático (APIs o descarga estructurada).

| Fuente | Variables que provee | Acceso | Periodicidad |
|--------|---------------------|--------|-------------|
| **IMF — World Economic Outlook** | PIB, inflación, deuda, cuenta corriente | API pública / descarga CSV | Anual / semestral |
| **Banco Mundial — World Development Indicators** | IED, Doing Business, alfabetización, electricidad, WGI | API pública (`api.worldbank.org`) | Anual |
| **Banco Mundial — WGI** | 6 indicadores de gobernanza | API pública | Anual |
| **OPEP / EIA** | Producción petrolera | Descarga CSV / web | Mensual |
| ~~**Banco Central de Venezuela (BCV)**~~ | ~~Tipo de cambio, reservas, inflación nacional~~ | **⛔ EXCLUIDA** — opacidad estadística crónica, no es fuente confiable internacionalmente | — |
| **Transparency International** | CPI — Índice de Percepción de Corrupción | Descarga CSV anual | Anual |
| **Heritage Foundation** | Índice de Libertad Económica | Descarga CSV anual | Anual |
| **UNCTAD** | IED, comercio exterior | Descarga CSV / API | Anual |
| **PNUD** | IDH — Índice de Desarrollo Humano | Descarga CSV anual | Anual |
| **UNESCO** | Alfabetización | API / descarga | Anual |

> **Nota crítica sobre el BCV:** El Banco Central de Venezuela ha tenido históricamente períodos de opacidad estadística (2014–2019 sin publicar cifras oficiales). Para esos períodos hay que usar fuentes alternativas como el FMI, CEPAL o estimaciones de centros de investigación como IESA o econométricas de Bloomberg/Consensus Economics.

---

## 6. Metodología Paso a Paso

Esta es la columna vertebral metodológica de la tesis. Cada paso debe estar documentado y justificado en el cuerpo del documento.

### Paso 1: Definición del marco teórico
- Revisar literatura sobre índices compuestos (OCDE Handbook, 2008)
- Revisar índices de referencia similares: EMBI, Fragile States Index, GCI (WEF), ICRG
- Justificar la selección de dimensiones y variables con base en literatura de riesgo país e inversión extranjera
- Definir la pregunta de investigación y los objetivos formales

### Paso 2: Recolección y consolidación de datos
- Descargar series históricas (2010–2024) para cada variable de sus fuentes respectivas
- Unificar en un DataFrame maestro con estructura: `año | trimestre | variable | valor | fuente`
- Documentar cada serie: fuente, metodología de cálculo, cobertura temporal, unidad

### Paso 3: Diagnóstico de calidad de datos
- Identificar valores faltantes por variable y período
- Aplicar estrategias de imputación según tipo: interpolación lineal, uso de proxy, estimación por modelo
- Detectar y documentar outliers — decidir si son errores o hechos reales (ej. hiperinflación 2018)
- Registrar todas las decisiones de limpieza en un log de transformaciones

### Paso 4: Normalización de variables
Todos los indicadores deben llevarse a la misma escala (0–100) para poder combinarlos.

**Método: Min-Max Rescaling**
```
V_norm = (V - V_min) / (V_max - V_min) × 100
```
- Para variables de dirección negativa (ej. inflación): invertir la fórmula:
```
V_norm = (V_max - V) / (V_max - V_min) × 100
```
- Usar el rango histórico completo (2010–2024) como referencia para min y max, con los extremos teóricos documentados.

### Paso 5: Determinación de pesos (AHP)
El **Proceso de Jerarquía Analítica (AHP)** de Saaty (1980) permite asignar pesos de manera estructurada y justificable:
1. Construir una matriz de comparación por pares entre dimensiones (5×5)
2. Rellenar con escala 1–9 de Saaty (1 = igual importancia, 9 = extremadamente más importante)
3. Calcular el vector propio principal → esos son los pesos
4. Calcular el **Índice de Consistencia (CR)** — debe ser < 0.10 para ser aceptable
5. Validar los pesos con al menos 2–3 expertos (economistas, analistas de riesgo país)

> Alternativamente: usar **análisis de componentes principales (PCA)** para determinar pesos de forma puramente estadística, sin juicio subjetivo. Se puede presentar ambos enfoques y comparar resultados — eso da solidez metodológica adicional.

### Paso 6: Agregación del índice
**Método principal: Agregación lineal ponderada (suma aditiva)**
```
ICIV = Σ (w_i × D_i)
```
Donde `w_i` es el peso de la dimensión `i` y `D_i` es el puntaje normalizado de esa dimensión (calculado a su vez como suma ponderada de sus variables).

**Método alternativo a explorar: Agregación geométrica**
```
ICIV = Π (D_i ^ w_i)
```
La diferencia: la agregación geométrica penaliza más los valores extremadamente bajos en una sola dimensión (no permite que una dimensión muy alta compense una muy baja). Para Venezuela, puede ser más representativa.

### Paso 7: Validación del modelo
- **Validación histórica:** Verificar que el ICIV captura correctamente los períodos conocidos de crisis (2014–2019) y recuperación parcial (2021–2023)
- **Análisis de sensibilidad:** Probar qué tan diferente sería el ICIV si los pesos varían ±10% — si el resultado no cambia drásticamente, el modelo es robusto
- **Correlación con IED:** Comprobar si períodos de ICIV alto correlacionan con mayores flujos de inversión extranjera real
- **Comparación de métodos:** Comparar resultados de agregación lineal vs. geométrica y AHP vs. PCA

### Paso 8: Construcción del dashboard
- Diseñar la arquitectura de la visualización (ya existe prototipo en `ICIV_Dashboard_Prototipo.html`)
- Implementar en la plataforma elegida (Streamlit recomendado por alineación con Python)
- Incluir: puntaje principal, evolución histórica, desglose por dimensión, comparación regional, tabla de indicadores, metodología resumida
- Documentar cómo un usuario empresarial debe interpretar y usar el dashboard

---

## 7. Pipeline Técnico de Big Data

Este es el componente que justifica la especialización en Big Data e Inteligencia de Negocios.

```
[Fuentes Externas]          [Ingesta]             [Procesamiento]        [Salida]
  IMF API          ──→                              
  World Bank API   ──→   ETL en Python    ──→   Normalización     ──→   ICIV Score
  OPEP/EIA CSV     ──→   (pandas, requests)     Ponderación AHP         Dashboard
  CSV manuales     ──→                          Agregación              Alertas
  VIIRS/NASA       ──→                          Validación
```

### Módulos del pipeline

**`01_ingesta.py`** — Descarga y almacenamiento crudo
- Conexión a APIs (World Bank WDI/WGI, IMF, EIA, FRED, UNHCR, WHO)
- Descarga de archivos CSV de fuentes que no tienen API (CPI, IEF, HDI, V-Dem, PTS)
- Extracción raster VIIRS/NASA para luminosidad nocturna
- ⛔ EXCLUIDO: BCV, OVF, PDVSA — fuentes venezolanas no confiables internacionalmente
- Almacenamiento en carpeta `data/raw/` con timestamp

**`02_limpieza.py`** — Preprocesamiento y calidad
- Estandarización de formatos de fecha
- Manejo de valores nulos (interpolación / imputación)
- Detección de outliers
- Log de transformaciones aplicadas
- Almacenamiento en `data/processed/`

**`03_normalizacion.py`** — Escalamiento Min-Max
- Cálculo de Min-Max global por variable
- Inversión de dirección para variables negativas
- Output: DataFrame con todas las variables en escala 0–100

**`04_modelo.py`** — Cálculo del ICIV
- Carga de pesos (AHP o PCA)
- Cálculo de puntaje por dimensión
- Cálculo del ICIV compuesto
- Cálculo de categoría de riesgo
- Output: Serie temporal del ICIV 2010–presente

**`05_dashboard.py`** — Visualización (Streamlit)
- Carga del DataFrame de resultados
- Construcción de gráficos interactivos (Plotly)
- Panel de filtros y controles
- Exportación a PDF/Excel

### Estructura de carpetas del repositorio

```
iciv-venezuela/
│
├── data/
│   ├── raw/               ← datos descargados sin modificar
│   ├── processed/         ← datos limpios y normalizados
│   └── results/           ← puntajes del ICIV calculados
│
├── src/
│   ├── 01_ingesta.py
│   ├── 02_limpieza.py
│   ├── 03_normalizacion.py
│   ├── 04_modelo.py
│   └── 05_dashboard.py
│
├── notebooks/
│   ├── EDA_exploratorio.ipynb
│   ├── AHP_ponderacion.ipynb
│   └── validacion_modelo.ipynb
│
├── docs/
│   └── tesis_ICIV.docx / .pdf
│
├── requirements.txt
└── README.md
```

---

## 8. Estructura de la Tesis

La tesis escrita debe seguir esta estructura para alcanzar nivel de posgrado:

### Capítulo 1: Introducción
- Planteamiento del problema (¿por qué Venezuela es difícil de evaluar para inversores?)
- Justificación (¿por qué es necesario un indicador propio?)
- Objetivos: General y específicos
- Alcance y limitaciones
- Estructura del documento

### Capítulo 2: Marco Teórico
- Concepto de clima de inversión y riesgo país
- Revisión de índices de referencia: EMBI, Fragile States Index, Doing Business, GCI, ICRG, IDH
- Teoría de índices compuestos (OCDE Handbook, Saaty AHP)
- Contexto macroeconómico de Venezuela (2010–2024)
- Big Data aplicado a análisis macroeconómico

### Capítulo 3: Marco Metodológico
- Tipo de investigación (cuantitativa, descriptiva-explicativa, longitudinal)
- Diseño de la investigación
- Selección y justificación de variables
- Método de normalización (Min-Max)
- Método de ponderación (AHP + validación de expertos)
- Método de agregación (lineal ponderada)
- Fuentes de datos y criterios de calidad
- Proceso de validación del modelo

### Capítulo 4: Resultados
- Análisis descriptivo de las variables individuales (2010–2024)
- Proceso de normalización y sus resultados
- Determinación de pesos mediante AHP
- Cálculo del ICIV trimestral 2010–2024
- Análisis de la evolución del índice
- Comparación regional
- Análisis de sensibilidad

### Capítulo 5: Herramienta de Visualización (Dashboard)
- Arquitectura del sistema
- Descripción del pipeline de datos
- Descripción del dashboard interactivo
- Manual de uso para el usuario empresarial

### Capítulo 6: Discusión y Conclusiones
- Interpretación de resultados en contexto histórico
- Limitaciones del modelo
- Recomendaciones para inversores según el ICIV actual
- Líneas de investigación futura
- Conclusiones finales

### Bibliografía
### Anexos
- Scripts de código Python documentados
- Tablas de datos completas
- Matrices AHP
- Resultados del análisis de sensibilidad

---

## 9. Stack Tecnológico Recomendado

| Rol | Herramienta | Justificación |
|-----|-------------|---------------|
| Lenguaje principal | Python 3.11+ | Ecosistema de datos más completo |
| Manipulación de datos | Pandas, NumPy | Estándar de la industria |
| APIs y scraping | `requests`, `wbdata`, `BeautifulSoup` | Ingesta de fuentes diversas |
| Visualización estática | Matplotlib, Seaborn | Para figuras de la tesis |
| Visualización interactiva | Plotly | Para el dashboard |
| Dashboard | Streamlit | Rápido de construir, exportable a web |
| Notebooks | Jupyter | Exploración y documentación |
| Control de versiones | Git + GitHub | Reproducibilidad y portafolio |
| Documento de tesis | Word (.docx) | Con template profesional |
| Presentación | PowerPoint (.pptx) | Defensa final |

---

## 10. Entregables del Proyecto

Al finalizar la tesis, los entregables son:

1. **`tesis_ICIV_Felipe.docx`** — Documento de tesis completo (Capítulos 1–6 + Bibliografía + Anexos)
2. **`iciv/output/iciv_dashboard_YYYY-MM-DD.html`** — Dashboard interactivo HTML dark-theme con Chart.js 4.4 ✅ (generado automáticamente por `main.py`)
3. **`iciv/data/processed/iciv_scores_ahp.csv`** — Serie histórica 2000–2026 del ICIV y las 6 dimensiones ✅
4. **`iciv/data/processed/iciv_normalizado.csv`** — 27 variables normalizadas 0–100 × 27 años ✅
5. **`iciv/src/iciv/satv/`** — Módulo SATV (Sistema de Alertas Tempranas Venezuela) ✅
6. **`iciv/src/iciv/scenarios/`** — Módulo de proyecciones 2027–2030 (3 escenarios + simulador) ✅
7. **`iciv/data/raw/venezuela_states.geojson`** — GeoJSON real GADM Venezuela Level-1 (25 estados) ✅
8. **`iciv/data/raw/viirs_states.csv`** — NTL por estado 2000–2026 (metodología Stokes & Ghosh 2021) ✅
6. **`presentacion_defensa.pptx`** — Presentación para la defensa ante el jurado
7. **`repositorio_github/`** — Código fuente completo, documentado y reproducible

---

## 11. Hoja de Ruta y Fases de Construcción

### Fase 1: Fundamentos ✅ Completada
- [x] Revisar bibliografía base (OCDE Handbook, artículos sobre índices compuestos, riesgo país Venezuela)
- [x] Finalizar lista de variables y fuentes de datos — **41 variables, 6 dimensiones, 15+ fuentes** (ver `VARIABLES_MASTER.md`)
- [ ] Redactar borradores de Capítulos 1 y 2 (Introducción y Marco Teórico)
- [x] Crear estructura de repositorio del proyecto (`iciv/` como paquete Python)

### Fase 2: Datos ✅ Completada
- [x] Descargar y almacenar datos históricos de todas las fuentes (29 loaders, 35 scripts fetch activos)
- [x] Construir pipeline de ingesta modular (`src/iciv/data/loaders/`)
- [x] Realizar análisis exploratorio (EDA) de cada variable — ver `bitacora/01_EDA_hallazgos_iniciales.md`
- [x] Documentar calidad, completitud y limitaciones — ver `CATALOGO_DE_DATOS.md` y `VARIABLES_MASTER.md`
- [x] Interpolación / forward-fill solo para gaps internos entre datos reales (sin fallbacks inventados)
- [x] Transformación log₁₀ para inflación y tipo de cambio (outliers extremos)
- [x] **POLÍTICA:** CERO datos inventados. Si no hay dato real de fuente verificable → NaN. Ver `iciv/CLAUDE.md`
- [ ] Redactar sección de fuentes en el Marco Metodológico

### Fase 3: Modelo ✅ Completada
- [x] Implementar normalización Min-Max (`src/iciv/processing/`)
- [x] Realizar proceso AHP y calcular pesos — CR=0.0081 (aceptable), ver `validate_model.py`
- [x] Implementar cálculo del ICIV (`src/iciv/index/aggregator.py`)
- [x] Calcular serie histórica 2000–2026 (27 años), rango 26.2–71.0
- [x] Validar el modelo: sensibilidad (SI=0.0408, Robusto), correlación IED (exploratorio), lineal vs geométrico, AHP vs PCA (r=0.994)
- [x] **Módulo Pulse mensual**: ICIV Pulse 2010–2026 (197 meses), 12 variables high-frequency internacionales
- [x] **Forecast ML**: SARIMA(1,1,2)(1,1,1,12) + OLS Nowcast con LOO-CV
- [ ] Redactar Capítulos 3 y 4

### Fase 4: Dashboard ✅ Completada (HTML interactivo)
- [x] Dashboard HTML dark-theme con Chart.js 4.4 + Leaflet.js 1.9.4 — generado por `main.py`
- [x] **6 bloques narrativos**: PORTADA · INICIO · HISTORIA · DIAGNÓSTICO · PROYECCIÓN · METODOLOGÍA
- [x] **19+ secciones** con sub-navegación jerárquica: Portada, Inicio (Pulse como protagonista), Score ICIV Anual, Historia 25a, Pulse Mensual, Componentes Pulse, Mapa estados, Dimensiones, Alertas SATV, Radar Sectorial, Escenarios 2027–2030, Forecast SARIMA, Nowcast, Validación/Coherencia, Bibliografía, Noticias, Venezuela Hoy, etc.
- [x] **ICIV Pulse**: gráfico de 197 meses, bandas de cobertura, sparkline 12 meses recientes
- [x] **Etiquetas de cobertura en 4 tiers**: Histórico ≥85% · Útil 70–84.9% · Parcial 50–69.9% · Provisional <50%
- [x] **Validación separada**: A) Coherencia interna ICIV→IED (exploratorio, nota circularidad) · B) Validación externa vs índices independientes
- [x] **Monte Carlo**: 10,000 trayectorias, fan chart P5–P95, probabilidades calibradas
- [x] **Comparación Regional**: ICIV universal para VEN/COL/PER/ECU/BOL (WDI+WGI)
- [x] **Indicadores Líderes**: Early Warning Score, barómetro 0-100, sparklines
- [x] SATV (Sistema de Alertas Tempranas Venezuela) — módulo `src/iciv/satv/` implementado
- [x] **Dashboard único en raíz del proyecto** — `iciv_dashboard.html` (~520 KB)
- [ ] Redactar Capítulo 5

### Fase 5: Cierre (Pendiente)
- [ ] Redactar Capítulo 6 (Discusión y Conclusiones)
- [ ] Revisar y corregir todo el documento
- [ ] Crear presentación de defensa en PowerPoint
- [ ] Preparar repositorio GitHub para entrega
- [ ] Ensayar la defensa

---

## 12. Criterios de Interpretación del Índice

Para que el ICIV sea útil para empresas reales, debe tener criterios de acción claros:

| ICIV | Señal | Recomendación para empresas |
|------|-------|-----------------------------|
| 0–30 | 🔴 ALTO RIESGO | No se recomienda inversión directa. Si ya están presentes, evaluar estrategia de salida o mínima exposición. |
| 31–50 | 🟠 RIESGO MODERADO-ALTO | Solo para sectores con alta tolerancia al riesgo (minería, petróleo con cobertura de riesgo político). Estructuras de inversión con máxima protección contractual. |
| 51–65 | 🟡 RIESGO MODERADO | Viable con due diligence profundo, análisis sectorial específico y estructuras de mitigación (seguros, socios locales). |
| 66–80 | 🟢 BAJO RIESGO | Condiciones favorables para la mayoría de sectores. Recomendable con análisis sectorial estándar. |
| 81–100 | 🟢🟢 MUY BAJO RIESGO | Clima de inversión comparable a mercados emergentes estables. Entrada recomendada. |

**Nota:** Venezuela ha operado históricamente en el rango 0–50 desde 2014. El umbral mínimo sugerido para considerar una inversión seria es **ICIV ≥ 50**, con **ICIV ≥ 60** para empresas sin experiencia en mercados de alto riesgo.

---

## 13. Referencias e Índices Similares (Benchmarks)

El ICIV se inspira y compite conceptualmente con los siguientes índices. Deben ser revisados en el Marco Teórico:

| Índice | Organización | Qué mide | Relevancia para el ICIV |
|--------|-------------|----------|-------------------------|
| EMBI (Emerging Market Bond Index) | JP Morgan | Riesgo soberano vía spreads de bonos | Referencia directa de riesgo-país financiero |
| Fragile States Index | Fund for Peace | Fragilidad estatal en 12 indicadores | Inspiración metodológica para dimensiones institucionales |
| Doing Business | Banco Mundial | Facilidad para hacer negocios | Variable directa del ICIV |
| WGI (Worldwide Governance Indicators) | Banco Mundial | Gobernanza en 6 dimensiones | Variables directas del ICIV |
| GCI (Global Competitiveness Index) | WEF | Competitividad en 12 pilares | Marco de referencia para estructura multidimensional |
| ICRG (International Country Risk Guide) | PRS Group | Riesgo político, económico y financiero | Metodología de referencia directa |
| IDH (Índice de Desarrollo Humano) | PNUD | Desarrollo humano en 3 dimensiones | Referencia para la dimensión de capital humano |
| IEF (Índice de Libertad Económica) | Heritage Foundation | Libertad económica en 12 componentes | Variable directa del ICIV |

**Referencia metodológica clave:**
> OCDE (2008). *Handbook on Constructing Composite Indicators: Methodology and User Guide.* OECD Publishing. — Este es el manual de referencia estándar para la construcción de índices compuestos y debe ser citado como fundamento metodológico principal.

---

## 14. Notas y Decisiones de Diseño — Estado Actual

Registro de decisiones de diseño tomadas y cuestiones pendientes.

### Decisiones resueltas ✅

- **AHP o PCA para los pesos** → **AHP implementado** (Saaty 1980, CR=0.0081). Se implementó también PCA como alternativa y se compararon ambos en `validate_model.py`. El AHP fue seleccionado por justificación experta y mayor interpretabilidad.
- **Agregación lineal o geométrica** → **Lineal ponderada (suma aditiva)** como método principal. La geométrica se calculó y comparó — la diferencia es menor del 5% dado que varias dimensiones ya están en mínimos históricos.
- **Período base para Min-Max** → **2000–2026** como referencia histórica completa. El período cubre desde antes de la crisis petrolera hasta las proyecciones actuales, dando el rango de variación más representativo.
- **Datos faltantes del BCV (2014–2019)** → Resuelto con datos estáticos validados (IMF, BCV Informe Económico, estimaciones R4V) para: reservas, tipo_cambio, alfabetización. Documentado en `CATALOGO_DE_DATOS.md`.
- **Tipo de cambio con reconversiones** → **Log₁₀ aplicado** sobre BsF equivalente. La serie se convierte a BsF antes del log: ×1 para 2000–2017, ×1.000 para BsS (2018–2021), ×10⁹ para Bs digital (2022+).
- **Dolarización informal** → No incluida como variable separada. El tipo de cambio log₁₀ y las reservas capturan indirectamente la presión cambiaria. La dolarización de facto mejora la apertura financiera (ya capturada en D4).

### Pendiente

- **Validación con expertos:** Los pesos AHP pueden fortalecerse con revisión de 2–3 economistas venezolanos. Esto reforzaría la sección metodológica de la tesis.
- **Comparación regional:** Adaptar el ICIV a Colombia, Perú, Ecuador y Bolivia agregaría valor comparativo significativo. Es la extensión técnica más impactante disponible.
- **Frecuencia mensual para SATV:** ✅ Implementado — módulo ICIV Pulse opera sobre 12 variables mensuales (EIA, FRED, Guardian API). El SATV anual se complementa con el Pulse para alertas de alta frecuencia.

---

### Correcciones aplicadas en auditoría de mayo 2026 ✅

- **IMF NGDP_D → PCPIPCH**: el deflactor del PIB devuelve 0 años para Venezuela. Cambiado a CPI inflation rate → **27 años reales**.
- **UNCTAD API 404 → WB WDI**: endpoint UNCTAD Stat 404. Reemplazado por `IS.SHP.GCNW.XQ` → **16 años reales (2006–2021)**.
- **Google Trends: inventados → pytrends real**: regenerado con API → **23 años reales** verificables.
- **BCV eliminado**: no es fuente confiable internacionalmente. Toda referencia a BCV como fuente activa eliminada de documentos. ⛔
- **Datos inventados removidos**: `_STATIC_AIRLINES` (OpenSky), `HISTORICAL_OFAC`, `_DIFFERENTIAL` VIIRS states — todos eliminados.
- **settings.yaml sincronizado**: D3 (6→13 vars), D4 (corrección pesos), D5 (5→8 vars) — actualizados para coincidir con `dimensions.py`.
- **RSF scale empalme documentado**: pre-2022 usa OWID violations_score invertido (100-x); post-2022 nueva metodología RSF. Comparabilidad limitada documentada.
- **Circularidad IED**: bloque A de validación renombrado de "Validación predictiva" → "Coherencia interna / Exploración". Nota metodológica prominente añadida.
- **Tests actualizados**: year range 2024→2026, fixtures 25→27 años.
- **fsi_manual.csv**: añadida columna `fuente` con URLs por año (Fund for Peace).

### Correcciones auditoría 21 de mayo 2026 ✅

- **PROYECTO_ICIV_MASTER.md**: actualizado — variable count, loaders count, fase 4, correcciones fuentes BCV/PDVSA eliminadas
- **FUENTES_DE_DATOS.md**: BCV/OVF/IIES-UCAB/PDVSA movidas de "Scraping activo" → "⛔ Excluidas"
- **Scores actuales**: 2024=33.8 (78.4% cobertura, Parcial-Útil) · 2025=30.8 (51.9%, Parcial) · 2026=34.3 (35.1%, Provisional)
- **Pipeline validado**: SI=0.0408 (Robusto) · CR=0.0081 · Pearson r=0.4598 · 27 años 2000–2026

---

*Última actualización: 21 de mayo de 2026*  
*Este documento es el punto de referencia central del proyecto. Actualizar ante cualquier cambio significativo en el diseño o alcance.*
