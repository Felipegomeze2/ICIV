# Provenance de datos ICIV

Fecha de corte: 2026-07-21.

Este archivo documenta la trazabilidad vigente. La regla principal es simple:
ningun score debe depender de fuentes originadas en Venezuela, valores inventados
o rellenos artificiales.

## Auditoria 2026-07-21 (correccion de fuentes institucionales)

Se detectaron y corrigieron tres problemas de atribucion en archivos manuales
del bloque institucional/humano. Detalle completo en
`docs/FUENTES_Y_VARIABLES.md`, seccion "Auditoria de fuentes institucionales":

- `wjp.csv`: contenia la serie V-Dem (fallback OWID) etiquetada como WJP.
  Reemplazado por el Historical Data File oficial del WJP (2012-2025).
- `freedom_house.csv`: valores que no coincidian con los publicados.
  Reemplazado por el Excel oficial All Data FIW + ediciones 2025/2026
  verificadas. Sin Aggregate Score antes de 2012 (NaN).
- `hdi.csv`: mezcla de vintages HDR. Reemplazado por un solo vintage
  (UNDP via OWID, 2000-2023) con nuevo `scripts/fetch_hdi.py`.
- `pts.csv`: actualizado a la edicion PTS 2025 (hasta 2024).

## Fuentes que alimentan el core anual

| Grupo | Fuente | Archivo principal |
|---|---|---|
| Macro | IMF, World Bank WDI, FRED | `imf.csv`, `wdi.csv`, `fred.csv` |
| Energia | U.S. EIA, Li et al./Figshare | `eia.csv`, `viirs.csv` |
| Institucional | Transparency International, WGI, Freedom House, WJP, PTS | `cpi.csv`, `wgi.csv`, `freedom_house.csv`, `wjp.csv`, `pts.csv` |
| Comercial | WDI, IMF, UNHCR/R4V, UNCTADstat | `wdi.csv`, `imf.csv`, `unhcr.csv`, `unctad.csv` |

Nota LSCI (2026-07-21): `unctad.csv` ahora proviene directo del bulk oficial
de UNCTADstat (US.LSCI trimestral, base Q1-2023=100, promedio anual de
trimestres publicados, 2006-2026). Reemplaza a la serie WDI congelada en
2021. Nunca se mezclan ambas bases en una misma serie; el fallback WDI solo
se usa si UNCTADstat no responde, y en ese caso toda la serie es WDI.
| Humano | UNDP/HDI, WHO, WDI, ILOSTAT | `hdi.csv`, `who.csv`, `wdi.csv`, `ilostat.csv` |
| Percepcion | The Guardian Open Platform + VADER | `guardian.csv` |

## Fuentes que alimentan Pulse

| Fuente | Archivo |
|---|---|
| FRED mensual (incluye spread EM ICE BofA desde 2026-07) | `fred_monthly.csv` |
| EIA mensual | `eia_monthly.csv` |
| Guardian mensual | `guardian_monthly.csv` |
| GDELT mensual | `gdelt_monthly.csv` cuando existe en el pipeline local o de Actions |
| IMF IMTS — comercio espejo EEUU-VEN (mirror, reporta EEUU) | `imts_monthly.csv` |
| World Bank Pink Sheet — crudo Dubai | `wb_commodities_monthly.csv` |

Ampliacion 2026-07-21: el Pulse paso de 11 a 15 variables con tres fuentes
nuevas (IMF IMTS, WB Pink Sheet, ICE BofA via FRED). Ninguna es de origen
venezolano; el comercio espejo usa exclusivamente lo reportado por EEUU.
Notas de cobertura: IMTS publica con ~3-6 meses de rezago; FRED solo
redistribuye una ventana movil (~3 anos) del spread ICE BofA, cobertura
desde 2023-07. Faltante es faltante: los pesos se renormalizan por mes.

GDELT se trata como fuente mensual opcional por estabilidad de API/rate limit.
Si falta, el dashboard debe mostrar menor cobertura, no inventar el dato.

## Capas auxiliares (no entran al score ni al Pulse)

| Fuente | Archivo | Cobertura | Nota |
|---|---|---|---|
| ACLED (API OAuth oficial) | `acled_monthly.csv` | 2018-01 a hoy menos ~12 meses | el tier de cuenta actual entrega datos con ~12 meses de rezago; solo contexto historico |
| UN Comtrade v1 (5 socios espejo) | `comtrade_monthly.csv` | 2010-01 a ~2 meses atras | ultimos ~3 meses parciales segun socios que hayan reportado |

Ambas requieren credenciales via secrets/entorno (ACLED_EMAIL,
ACLED_PASSWORD, COMTRADE_API_KEY); sin credenciales el fetch avisa y no
escribe nada. Su eventual entrada al Pulse exige decision de peso
documentada y re-ejecucion del backtest.

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
