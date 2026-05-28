"""Build an auditable ICIV dataset package.

The package is a derived, documented release of the project's real data. It
does not fetch sources, impute unavailable observations, or create synthetic
values.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from iciv.config import Settings
from iciv.data.catalog import CATALOG
from iciv.index.dimensions import DIMENSIONS
from iciv.index.pulse_aggregator import PULSE_WEIGHTS


SOURCE_DETAILS: dict[str, dict[str, str]] = {
    "WDI": {
        "source_name": "World Bank World Development Indicators",
        "origin": "international",
        "raw_files": "wdi.csv",
    },
    "WGI": {
        "source_name": "World Bank Worldwide Governance Indicators",
        "origin": "international",
        "raw_files": "wgi.csv",
    },
    "EIA": {
        "source_name": "U.S. Energy Information Administration International",
        "origin": "international",
        "raw_files": "eia.csv; eia_monthly.csv",
    },
    "IMF": {
        "source_name": "International Monetary Fund",
        "origin": "international",
        "raw_files": "imf.csv",
    },
    "CPI": {
        "source_name": "Transparency International CPI",
        "origin": "international",
        "raw_files": "cpi.csv",
    },
    "HDI": {
        "source_name": "UNDP Human Development Report",
        "origin": "international",
        "raw_files": "hdi.csv",
    },
    "GDELT": {
        "source_name": "GDELT DOC 2.0 API",
        "origin": "international",
        "raw_files": "gdelt_monthly.csv; gdelt_monthly.status.json",
    },
    "GUARDIAN": {
        "source_name": "The Guardian Open Platform",
        "origin": "international",
        "raw_files": "guardian.csv; guardian_monthly.csv",
    },
    "FRED": {
        "source_name": "Federal Reserve Bank of St. Louis FRED",
        "origin": "international",
        "raw_files": "fred.csv; fred_monthly.csv",
    },
    "FREEDOM_HOUSE": {
        "source_name": "Freedom House",
        "origin": "international",
        "raw_files": "freedom_house.csv",
    },
    "UNHCR": {
        "source_name": "UNHCR/R4V",
        "origin": "international",
        "raw_files": "unhcr.csv",
    },
    "VIIRS": {
        "source_name": "Li et al./Figshare harmonized nighttime lights",
        "origin": "international",
        "raw_files": "viirs.csv; viirs_states.csv",
    },
    "UNCTAD": {
        "source_name": "UNCTAD",
        "origin": "international",
        "raw_files": "unctad.csv",
    },
    "PTS": {
        "source_name": "Political Terror Scale",
        "origin": "international",
        "raw_files": "pts.csv",
    },
    "WHO": {
        "source_name": "World Health Organization",
        "origin": "international",
        "raw_files": "who.csv",
    },
    "WJP": {
        "source_name": "World Justice Project",
        "origin": "international",
        "raw_files": "wjp.csv",
    },
    "ILOSTAT": {
        "source_name": "International Labour Organization / ILOSTAT",
        "origin": "international",
        "raw_files": "ilostat.csv",
    },
}


@dataclass(frozen=True)
class DatasetPackageResult:
    release_dir: Path
    manifest_path: Path
    files: list[Path]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _role_for_variable(variable: str) -> str:
    core_vars = {v.column for dim in DIMENSIONS.values() for v in dim.variables}
    if variable in core_vars:
        return "core_anual"
    if variable == "ied_neta_usd":
        return "outcome_externo"
    if variable in PULSE_WEIGHTS:
        return "pulse_mensual"
    return "auxiliar"


def _is_core_variable(variable: str) -> bool:
    return any(variable == v.column for dim in DIMENSIONS.values() for v in dim.variables)


def _is_pulse_variable(variable: str) -> bool:
    return variable in PULSE_WEIGHTS


def _dimension_weight(variable: str) -> float:
    for dim in DIMENSIONS.values():
        for item in dim.variables:
            if item.column == variable:
                return dim.iciv_weight * item.weight
    return 0.0


def build_data_dictionary(df_raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for variable, meta in CATALOG.items():
        present = variable in df_raw.columns
        role = _role_for_variable(variable)
        source = meta.source.value
        source_info = SOURCE_DETAILS.get(source, {})
        rows.append(
            {
                "variable": variable,
                "descripcion": meta.description,
                "rol": role,
                "entra_iciv_anual": _is_core_variable(variable),
                "entra_pulse_mensual": _is_pulse_variable(variable),
                "entra_validacion_outcome": variable == "ied_neta_usd",
                "dimension": meta.dimension.value,
                "fuente_id": source,
                "fuente_nombre": source_info.get("source_name", source),
                "origen_fuente": source_info.get("origin", "international"),
                "unidad": meta.unit,
                "direccion": meta.direction.value,
                "peso_dimension": meta.dim_weight,
                "peso_iciv_total": round(_dimension_weight(variable), 6),
                "desde_catalogo": meta.available_from,
                "incluida_en_dataset_wide": present,
                "notas": meta.notes,
            }
        )
    return pd.DataFrame(rows)


def build_annual_coverage(df_raw: pd.DataFrame) -> pd.DataFrame:
    year_col = df_raw.columns[0]
    years = sorted(df_raw[year_col].dropna().astype(int).unique().tolist())
    total_years = len(years)
    rows: list[dict] = []
    for variable, meta in CATALOG.items():
        if variable not in df_raw.columns:
            rows.append(
                {
                    "variable": variable,
                    "rol": _role_for_variable(variable),
                    "fuente_id": meta.source.value,
                    "n_years_with_data": 0,
                    "total_years": total_years,
                    "coverage_pct": 0.0,
                    "first_year": "",
                    "last_year": "",
                    "missing_years": ";".join(str(y) for y in years),
                }
            )
            continue
        subset = df_raw[[year_col, variable]].copy()
        non_null = subset.dropna(subset=[variable])
        present_years = set(non_null[year_col].astype(int).tolist())
        missing_years = [y for y in years if y not in present_years]
        rows.append(
            {
                "variable": variable,
                "rol": _role_for_variable(variable),
                "fuente_id": meta.source.value,
                "n_years_with_data": len(present_years),
                "total_years": total_years,
                "coverage_pct": round((len(present_years) / total_years * 100.0) if total_years else 0.0, 1),
                "first_year": min(present_years) if present_years else "",
                "last_year": max(present_years) if present_years else "",
                "missing_years": ";".join(str(y) for y in missing_years),
            }
        )
    return pd.DataFrame(rows)


def build_source_provenance(dictionary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for source_id, group in dictionary.groupby("fuente_id", sort=True):
        info = SOURCE_DETAILS.get(source_id, {})
        variables = sorted(group["variable"].tolist())
        roles = sorted(group["rol"].unique().tolist())
        rows.append(
            {
                "fuente_id": source_id,
                "fuente_nombre": info.get("source_name", source_id),
                "origen_fuente": info.get("origin", "international"),
                "raw_files": info.get("raw_files", ""),
                "n_variables_catalogadas": len(variables),
                "n_variables_iciv_anual": int(group["entra_iciv_anual"].sum()),
                "n_variables_pulse_mensual": int(group["entra_pulse_mensual"].sum()),
                "roles": ";".join(roles),
                "variables": ";".join(variables),
                "politica": "Solo fuentes externas a Venezuela; sin valores inventados ni fallback sintetico.",
            }
        )
    return pd.DataFrame(rows)


def _write_readme(release_dir: Path, manifest: dict) -> Path:
    path = release_dir / "README.md"
    text = f"""# ICIV Dataset Package

Release: `{manifest["release_id"]}`
Generated at UTC: `{manifest["generated_at_utc"]}`

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

- No Venezuelan government/local-origin sources are accepted for the score.
- Missing observations remain missing.
- No synthetic, artificial or invented fallback values are created.
- GDELT and news feeds are optional/contextual when their public APIs fail.

## Recommended Use

Use `iciv_dataset_largo.csv`, `data_dictionary.csv` and `coverage_annual.csv`
for audit and defense. Use `iciv_dataset_wide.csv` for modeling or replication.
"""
    path.write_text(text, encoding="utf-8")
    return path


def _write_dictionary_md(dictionary: pd.DataFrame, release_dir: Path) -> Path:
    path = release_dir / "data_dictionary.md"
    cols = [
        "variable", "rol", "entra_iciv_anual", "entra_pulse_mensual", "dimension", "fuente_id", "unidad",
        "direccion", "peso_iciv_total", "descripcion",
    ]
    table = dictionary[cols].copy()
    lines = ["# Data dictionary", "", "| Variable | Rol | ICIV anual | Pulse mensual | Dimension | Fuente | Unidad | Direccion | Peso ICIV | Descripcion |", "|---|---|---:|---:|---|---|---|---|---:|---|"]
    for _, row in table.iterrows():
        lines.append(
            "| {variable} | {rol} | {entra_iciv_anual} | {entra_pulse_mensual} | {dimension} | {fuente_id} | {unidad} | {direccion} | {peso_iciv_total} | {descripcion} |".format(
                **{k: str(row[k]).replace("|", "/") for k in cols}
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_dataset_package(
    df_raw: pd.DataFrame,
    wide_path: Path,
    long_path: Path,
    settings: Settings,
    release_id: str = "latest",
) -> DatasetPackageResult:
    """Builds `data/releases/<release_id>` from generated real artifacts."""
    release_dir = settings.paths.data_releases / release_id
    release_dir.mkdir(parents=True, exist_ok=True)

    dictionary = build_data_dictionary(df_raw)
    coverage = build_annual_coverage(df_raw)
    provenance = build_source_provenance(dictionary)

    files: list[Path] = []
    for src in [wide_path, long_path]:
        if src.exists():
            dst = release_dir / src.name
            shutil.copy2(src, dst)
            files.append(dst)

    dict_csv = release_dir / "data_dictionary.csv"
    cov_csv = release_dir / "coverage_annual.csv"
    prov_csv = release_dir / "source_provenance.csv"
    dictionary.to_csv(dict_csv, index=False, encoding="utf-8-sig")
    coverage.to_csv(cov_csv, index=False, encoding="utf-8-sig")
    provenance.to_csv(prov_csv, index=False, encoding="utf-8-sig")
    files.extend([dict_csv, cov_csv, prov_csv])
    files.append(_write_dictionary_md(dictionary, release_dir))

    for optional_name in [
        "pulse_forecast_backtest_summary.csv",
        "pulse_forecast_backtest.csv",
    ]:
        src = settings.paths.data_processed / optional_name
        if src.exists():
            dst = release_dir / optional_name
            shutil.copy2(src, dst)
            files.append(dst)

    manifest = {
        "release_id": release_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_policy": "external_non_venezuelan_sources_only; no synthetic fallback values",
        "annual_year_min": int(df_raw[df_raw.columns[0]].min()),
        "annual_year_max": int(df_raw[df_raw.columns[0]].max()),
        "n_catalog_variables": int(len(CATALOG)),
        "n_core_variables": int((dictionary["rol"] == "core_anual").sum()),
        "n_pulse_variables": int(dictionary["entra_pulse_mensual"].sum()),
        "n_outcome_variables": int((dictionary["rol"] == "outcome_externo").sum()),
        "files": {},
    }
    files.append(_write_readme(release_dir, manifest))
    for path in sorted(files):
        try:
            rows = len(pd.read_csv(path)) if path.suffix.lower() == ".csv" else None
        except Exception:
            rows = None
        manifest["files"][path.name] = {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "rows": rows,
        }

    manifest_path = release_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return DatasetPackageResult(release_dir=release_dir, manifest_path=manifest_path, files=files + [manifest_path])
