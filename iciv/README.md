# Pipeline ICIV

Este directorio contiene el pipeline Python que genera el indice anual, el Pulse
mensual, las alertas SATV Pulse y el dashboard HTML.

## Entrada principal

```bash
pip install -e ".[dev]"
python main.py --no-fetch --no-open
```

`main.py` orquesta:

1. fetch de fuentes cuando no se usa `--no-fetch`;
2. loaders y pipeline de limpieza/normalizacion;
3. agregacion ICIV anual con AHP;
4. agregacion Pulse mensual;
5. SATV sobre componentes Pulse;
6. validacion, visualizaciones y dashboard.

## Directorios

| Ruta | Uso |
|---|---|
| `scripts/` | fetchers y controles operativos |
| `src/iciv/data/` | catalogo, loaders y metadatos |
| `src/iciv/processing/` | limpieza y normalizacion |
| `src/iciv/index/` | dimensiones, pesos y agregadores |
| `src/iciv/satv/` | motores de alertas |
| `src/iciv/ml/` | forecast Pulse y experimentos nowcast |
| `tests/` | pruebas automatizadas |

## Controles utiles

```bash
python scripts/check_pulse_inputs.py
pytest
```

La documentacion metodologica canonica vive en `../docs/`.
