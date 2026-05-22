# ICIV — Indicador de Clima de Inversión Venezuela
## Paquete Python `iciv` — Documentación Técnica

> **Tesis de Posgrado:** Especialización Big Data e Inteligencia de Negocios  
> **Autor:** Felipe  
> **Período del modelo:** 2000–2026 (27 años)  
> **Variables:** 25 en 6 dimensiones  
> **Última actualización:** Abril 2026

---

## Estructura del Proyecto

```
iciv/
├── main.py                        ← Punto de entrada principal
├── config/
│   └── settings.yaml              ← Configuración central (rutas, fuentes, pesos AHP)
├── data/
│   ├── raw/                       ← Datos descargados sin modificar (CSV)
│   └── processed/                 ← Datos normalizados y resultados del ICIV
├── output/                        ← Dashboard HTML generado
├── scripts/                       ← Scripts de fetch por fuente
│   ├── fetch_wdi.py               ← World Bank WDI (inflación, PIB, reservas, tipo_cambio, IED, etc.)
│   ├── fetch_wgi.py               ← World Bank WGI (6 indicadores de gobernanza)
│   ├── fetch_static.py            ← CPI, IEF, HDI (descarga manual con parseo)
│   ├── fetch_guardian.py          ← The Guardian API (tono + volumen)
│   ├── fetch_gdelt.py             ← GDELT Project (validación)
│   ├── fetch_freedom_house.py     ← Freedom House (democracia)
│   ├── fetch_ofac.py              ← OFAC / US Treasury (sanciones SDN)
│   ├── fetch_unhcr.py             ← UNHCR / R4V (migración venezolana)
│   ├── fetch_gtrends.py           ← Google Trends (interés de búsqueda)
│   └── validate_model.py          ← Validación: sensibilidad AHP, correlación IED, comparación métodos
└── src/iciv/                      ← Paquete Python instalable
    ├── config/                    ← Pydantic settings (Paths, Sources)
    ├── data/
    │   ├── catalog.py             ← CATALOG: metadata de las 25 variables
    │   ├── models/                ← Pydantic models (VariableMetadata, etc.)
    │   └── loaders/               ← 13 loaders (uno por fuente)
    ├── processing/
    │   ├── pipeline.py            ← ICIVPipeline: orquesta Cleaner→Imputer→Normalizer
    │   └── transformers/          ← Cleaner, Imputer, MinMaxNormalizer
    ├── index/
    │   ├── aggregator.py          ← ICIVAggregator: calcula dimensiones + ICIV compuesto
    │   └── weighting/             ← AHPWeights, FixedWeights, PCAWeights
    ├── satv/
    │   ├── engine.py              ← SATVEngine: alertas tempranas (3 capas)
    │   └── __init__.py
    └── utils/
        └── logging_config.py
```

---

## Ejecución Rápida

```bash
# Instalar dependencias
cd iciv
pip install -e ".[dev]"

# Descargar todos los datos (primera vez o actualización)
python main.py

# Ejecutar sin re-descargar datos
python main.py --no-fetch

# Ejecutar sin abrir el dashboard al final
python main.py --no-fetch --no-open
```

### Opciones de `main.py`

| Flag | Descripción |
|------|-------------|
| `--no-fetch` | Omite la fase de descarga; usa los CSV en `data/raw/` |
| `--no-open` | Genera el HTML pero no lo abre en el navegador |
| `--method ahp` | Usa pesos AHP (default) |
| `--method equal` | Usa pesos iguales (1/6 por dimensión) |

---

## Pipeline de Datos

```
[Fuentes Externas]    [Ingesta]              [Procesamiento]        [Salida]
  WDI / WGI    ──→                           
  EIA          ──→   scripts/fetch_*.py  ──→  ICIVPipeline      ──→  iciv_normalizado.csv
  IMF          ──→   (data/raw/*.csv)         Cleaner                iciv_scores_ahp.csv
  CPI / IEF    ──→                            Imputer           ──→  Dashboard HTML
  HDI          ──→                            MinMaxNormalizer        SATV alertas
  Guardian     ──→                           
  FRED         ──→   ICIVAggregator      ──→  D1…D6 + ICIV score
  FH / OFAC    ──→   (AHP weights)       
  UNHCR        ──→                       
  GoodleTrends ──→                       
```

### Fases de `main.py`

1. **`fase_ingesta()`** — Ejecuta los scripts `fetch_*.py`. Descarga todos los CSV a `data/raw/`. Los scripts tienen fallbacks estáticos integrados para gaps conocidos (reservas, tipo_cambio, alfabetización).

2. **`fase_procesamiento()`** — Carga los CSV raw, construye el DataFrame maestro, aplica transformaciones pre-pipeline (log₁₀ tipo_cambio y deflactor), ejecuta `ICIVPipeline` (Cleaner → Imputer → MinMaxNormalizer). Guarda `iciv_normalizado.csv`.

3. **`fase_modelo()`** — Carga pesos AHP desde `config/settings.yaml`, ejecuta `ICIVAggregator` para calcular D1–D6 y el ICIV compuesto. Guarda `iciv_scores_ahp.csv`.

4. **`fase_satv()`** — Instancia `SATVEngine` con los DataFrames ya computados. Retorna dict con alertas activas, estados por dimensión y timeline histórico.

5. **`fase_dashboard()`** — Genera el HTML completo con todos los datos serializados como JSON inline. Incluye las 7 secciones del dashboard.

---

## El Catálogo — `src/iciv/data/catalog.py`

El `CATALOG` es un dict `{column_name: VariableMetadata}` que es la fuente de verdad de metadatos de todas las variables. Cada entrada incluye: descripción, unidad, dimensión, dirección (positiva/negativa), peso AHP y notas metodológicas.

```python
from iciv.data.catalog import CATALOG

meta = CATALOG["tipo_cambio_oficial_lcu_usd"]
print(meta.description)   # "Tipo de cambio oficial — log₁₀(BsF/USD equiv.)"
print(meta.direction)     # Direction.NEGATIVE
print(meta.dimension)     # Dimension.D1_MACRO
```

---

## SATV — Sistema de Alertas Tempranas Venezuela

El módulo `src/iciv/satv/` implementa tres capas de inteligencia sobre los datos ya computados:

### Capa 1 — Semáforo por dimensión
Clasifica cada dimensión según su score actual:
- **Normal** (≥ 50 pts)
- **Precaución** (25–49 pts)
- **Crítico** (< 25 pts)

### Capa 2 — Tendencia
Calcula deltas respecto a 1, 3 y 5 años anteriores para cada dimensión. Clasifica: deterioro acelerado / deterioro / estable / recuperación / recuperación acelerada.

### Capa 3 — Alertas compuestas (reglas nombradas)
| Alerta | Condición | Nivel |
|--------|-----------|-------|
| Colapso Energético | D2 < 20 pts | Crítico |
| Aislamiento Internacional | Freedom House < 15 AND OFAC score < 10 | Crítico |
| Contagio Sistémico | 4+ dimensiones fuera de zona normal | Crítico/Precaución |
| Deterioro Acelerado | Alguna dimensión Δ1y < −15 pts | Precaución |
| Pre-Colapso ICIV | ICIV < 35 AND 3 años consecutivos de caída | Crítico |
| Señal de Recuperación | ICIV +5 pts en 2 años consecutivos | Normal |

### Uso directo
```python
from iciv.satv import SATVEngine
import pandas as pd

df_norm   = pd.read_csv("data/processed/iciv_normalizado.csv")
df_scores = pd.read_csv("data/processed/iciv_scores_ahp.csv")

engine = SATVEngine(df_norm, df_scores)
result = engine.compute_all()

print(result["resumen"])           # dims_criticas, iciv_tendencia, etc.
print(result["alertas_activas"])   # lista de alertas activas en el año más reciente
print(result["timeline_historico"]) # cuándo se activó cada alerta históricamente
```

---

## Pesos AHP — Dimensiones del ICIV

Los pesos de dimensiones fueron determinados mediante el Proceso de Jerarquía Analítica (Saaty 1980):

| Dimensión | Peso AHP | CR = 0.0081 |
|-----------|----------|-------------|
| D1 — Estabilidad Macroeconómica | 0.25 (25%) | |
| D2 — Sector Energético | 0.20 (20%) | |
| D3 — Entorno Institucional | 0.20 (20%) | |
| D4 — Apertura Comercial | 0.15 (15%) | |
| D5 — Capital Humano | 0.10 (10%) | |
| D6 — Percepción Internacional | 0.10 (10%) | |

CR = 0.0081 < 0.10 → Consistencia aceptable según Saaty (1980).

Los pesos de variables **dentro de cada dimensión** son iguales (1/N), donde N es el número de variables en la dimensión.

---

## Validación del Modelo

Ejecutar `scripts/validate_model.py` para obtener:
- **Análisis de sensibilidad AHP**: índice SI=0.057 (< 0.1, modelo Robusto)
- **Correlación ICIV–IED**: indica si el índice predice flujos de inversión real
- **Comparación lineal vs. geométrica**: diferencia promedio < 5%
- **Comparación AHP vs. PCA**: confirma estabilidad de los pesos

---

## Dependencias Principales

```toml
[project]
dependencies = [
    "pandas>=2.0",
    "numpy>=1.24",
    "requests>=2.28",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "vaderSentiment>=3.3",
    "scikit-learn>=1.3",
]
```

---

*Para el contexto académico y metodológico completo, ver `PROYECTO_ICIV_MASTER.md` y `CATALOGO_DE_DATOS.md` en la raíz del proyecto.*
