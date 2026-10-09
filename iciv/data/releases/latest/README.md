# ICIV Dataset Package

Release: `latest`
Generated at UTC: `2026-10-09T13:56:54.059747+00:00`

This folder is the auditable dataset package for the ICIV project. It contains
derived project data, metadata, coverage tables and provenance. It does not
replace the raw source files in `iciv/data/raw/`.

## Files

| File | Purpose |
|---|---|
| `iciv_dataset_wide.csv` | Annual wide panel: one row per year, one column per published variable. |
| `iciv_dataset_largo.csv` | Annual long panel: one row per year-variable with raw value, normalized value, source, dimension, direction and role. |
| `data_dictionary.csv` | Variable-level dictionary generated from the code catalog. |
| `data_dictionary.md` | Human-readable version of the variable dictionary. |
| `coverage_annual.csv` | Annual coverage by variable. |
| `source_provenance.csv` | Source-level provenance and raw file mapping. |
| `manifest.json` | Release metadata, row counts and SHA-256 hashes. |
| `pulse_forecast_backtest_summary.csv` | Forecast backtesting summary, if available. |
| `pulse_forecast_backtest.csv` | Forecast backtesting detail, if available. |

## Source Policy

- Only international sources are used; no Venezuelan agency (BCV, INE, PDVSA) is a direct source. Some international compilers build their series from information reported by countries; this is declared, not hidden.
- Provider values that are impossible for the series (e.g. 0% exports of GDP) are excluded and logged in `plausibilidad_proveedor.csv`; they are never replaced.
- Provider estimates, projections and partial aggregates are explicitly distinct from observations.
- Publication dates were not archived for historical snapshots; this is not a real-time vintage backtest.
- Missing observations remain missing.
- No synthetic, artificial or invented fallback values are created.
- GDELT and news feeds are optional/contextual when their public APIs fail.

## Recommended Use

Use `iciv_dataset_largo.csv`, `data_dictionary.csv` and `coverage_annual.csv`
for audit and defense. Use `iciv_dataset_wide.csv` for modeling or replication.
