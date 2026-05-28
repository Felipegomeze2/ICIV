# Provenance de datos ICIV

Fecha de corte: 2026-05-28.

Este archivo documenta la trazabilidad vigente. La regla principal es simple:
ningun score debe depender de fuentes originadas en Venezuela, valores inventados
o rellenos artificiales.

## Fuentes que alimentan el core anual

| Grupo | Fuente | Archivo principal |
|---|---|---|
| Macro | IMF, World Bank WDI, FRED | `imf.csv`, `wdi.csv`, `fred.csv` |
| Energia | U.S. EIA, Li et al./Figshare | `eia.csv`, `viirs.csv` |
| Institucional | Transparency International, WGI, Freedom House, WJP, PTS | `cpi.csv`, `wgi.csv`, `freedom_house.csv`, `wjp.csv`, `pts.csv` |
| Comercial | WDI, IMF, UNHCR/R4V, UNCTAD | `wdi.csv`, `imf.csv`, `unhcr.csv`, `unctad.csv` |
| Humano | UNDP/HDI, WHO, WDI, ILOSTAT | `hdi.csv`, `who.csv`, `wdi.csv`, `ilostat.csv` |
| Percepcion | The Guardian Open Platform + VADER | `guardian.csv` |

## Fuentes que alimentan Pulse

| Fuente | Archivo |
|---|---|
| FRED mensual | `fred_monthly.csv` |
| EIA mensual | `eia_monthly.csv` |
| Guardian mensual | `guardian_monthly.csv` |
| GDELT mensual | `gdelt_monthly.csv` cuando existe en el pipeline local o de Actions |

GDELT se trata como fuente mensual opcional por estabilidad de API/rate limit.
Si falta, el dashboard debe mostrar menor cobertura, no inventar el dato.

## Outcome externo

`ied_neta_usd` proviene de WDI y se usa solo para validacion exploratoria
ICIV -> IED. No entra al score anual.

## Dataset publico

El pipeline genera:

- `iciv/data/processed/iciv_dataset_wide.csv`
- `iciv/data/processed/iciv_dataset_largo.csv`
- `iciv/data/releases/latest/`

El paquete `data/releases/latest/` incluye diccionario, cobertura anual,
provenance por fuente, manifest con hashes y copias de los CSV publicos. No
sustituye a los datos crudos; es una capa de auditoria reproducible.

## Fuentes apartadas

Pueden existir CSV o scripts historicos de fuentes apartadas para auditoria o
trabajo futuro. No deben presentarse como parte del score si no aparecen en
`src/iciv/index/dimensions.py` o `src/iciv/index/pulse_aggregator.py`.

## Controles

- `scripts/check_pulse_inputs.py` revisa vigencia de fuentes mensuales.
- `scripts/build_dataset_package.py` reconstruye el paquete de dataset desde
  artefactos procesados.
- `python main.py --no-fetch --no-open` regenera dashboard y dataset.
- `python -m pytest` valida loaders y pipeline basico.
