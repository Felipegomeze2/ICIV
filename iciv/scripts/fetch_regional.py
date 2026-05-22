"""
Descarga datos de WDI y WGI para comparación regional ICIV.

Países: Venezuela (VEN), Colombia (COL), Perú (PER), Ecuador (ECU), Bolivia (BOL)

Indicadores WDI descargados (World Bank Data API v2):
  NY.GDP.MKTP.KD.ZG   PIB crecimiento real (%)
  FP.CPI.TOTL.ZG      Inflación IPC (%)
  FI.RES.TOTL.MO      Reservas en meses de importaciones
  EG.USE.ELEC.KH.PC   Consumo eléctrico per capita (kWh)
  BX.KLT.DINV.WD.GD.ZS  IED neta (% del PIB)
  NE.EXP.GNFS.ZS      Exportaciones bienes y servicios (% PIB)
  SL.UEM.TOTL.ZS      Desempleo (% fuerza laboral)
  SP.DYN.LE00.IN      Esperanza de vida al nacer
  SE.SEC.ENRR         Matrícula escolar secundaria (%)
  EG.ELC.ACCS.ZS      Acceso a electricidad (% población)

Indicadores WGI descargados (Worldwide Governance Indicators API):
  CC.EST  Control of Corruption
  GE.EST  Government Effectiveness
  PV.EST  Political Stability
  RL.EST  Rule of Law
  RQ.EST  Regulatory Quality
  VA.EST  Voice and Accountability
  → Se promedian en wgi_composite (0-100 normalizado desde -2.5/+2.5)

Uso:
  python scripts/fetch_regional.py
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import pandas as pd
import requests

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

COUNTRIES   = ["VEN", "COL", "PER", "ECU", "BOL"]
START_YEAR  = 2000
END_YEAR    = 2024   # WDI lag: datos hasta 2023-2024 según indicador

WDI_INDICATORS = {
    "NY.GDP.MKTP.KD.ZG":    "gdp_growth_pct",
    "FP.CPI.TOTL.ZG":       "inflation_cpi_pct",
    "FI.RES.TOTL.MO":       "reserves_months_imports",
    "EG.USE.ELEC.KH.PC":    "electricity_kwh_pc",
    "BX.KLT.DINV.WD.GD.ZS":"fdi_pct_gdp",
    "NE.EXP.GNFS.ZS":       "exports_pct_gdp",
    "SL.UEM.TOTL.ZS":       "unemployment_pct",
    "SP.DYN.LE00.IN":       "life_expectancy",
    "SE.SEC.ENRR":          "school_enrollment_sec_pct",
    "EG.ELC.ACCS.ZS":       "electricity_access_pct",
}

# WGI bulk ZIP: indicadores con sufijo .SC (escala -2.5/+2.5)
WGI_INDICATORS = [
    "GOV_WGI_CC.SC",   # Control of Corruption
    "GOV_WGI_GE.SC",   # Government Effectiveness
    "GOV_WGI_PV.SC",   # Political Stability
    "GOV_WGI_RL.SC",   # Rule of Law
    "GOV_WGI_RQ.SC",   # Regulatory Quality
    "GOV_WGI_VA.SC",   # Voice and Accountability
]
WGI_EXCEL_URL = "https://databank.worldbank.org/data/download/WGI_EXCEL.zip"

OUTPUT_DIR = _ROOT / "data" / "raw" / "regional"


def _wdi_fetch(indicator_code: str, countries: list[str]) -> pd.DataFrame:
    """Descarga un indicador WDI para múltiples países vía API."""
    ctry_str = ";".join(countries)
    url = (
        f"https://api.worldbank.org/v2/country/{ctry_str}/indicator/{indicator_code}"
        f"?format=json&per_page=2000&mrv={END_YEAR - START_YEAR + 5}"
    )
    rows = []
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) < 2:
            return pd.DataFrame()
        for item in data[1] or []:
            year = int(item.get("date", 0))
            val  = item.get("value")
            iso3 = (item.get("countryiso3code") or "").upper()
            if iso3 and year >= START_YEAR and year <= END_YEAR and val is not None:
                rows.append({"pais_iso3": iso3, "año": year, "value": float(val)})
    except Exception as exc:
        logger.warning("    WARN %s: %s", indicator_code, exc)
    return pd.DataFrame(rows)


def _wgi_fetch(countries: list[str]) -> pd.DataFrame:
    """
    Descarga el bulk ZIP del WGI y extrae datos para los países indicados.
    Usa el mismo archivo que fetch_wgi.py (databank.worldbank.org/data/download/WGI_csv.zip).
    """
    import io, zipfile

    logger.info("      Descargando WGI Excel ZIP (~1 MB) ...")
    try:
        import io as _io, zipfile as _zf
        import openpyxl as _opxl
        resp = requests.get(WGI_EXCEL_URL, timeout=120)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("    WARN WGI Excel ZIP descarga fallida: %s", exc)
        return pd.DataFrame()

    try:
        with _zf.ZipFile(_io.BytesIO(resp.content)) as zf:
            xlsx_names = [n for n in zf.namelist() if n.endswith(".xlsx")]
            if not xlsx_names:
                logger.warning("    WARN WGI: no se encontró XLSX en el ZIP")
                return pd.DataFrame()
            with zf.open(xlsx_names[0]) as xf:
                wb  = _opxl.load_workbook(xf, read_only=True, data_only=True)
                ws  = wb["Data"]
                all_data = list(ws.iter_rows(values_only=True))
    except Exception as exc:
        logger.warning("    WARN WGI Excel lectura fallida: %s", exc)
        return pd.DataFrame()

    headers = [str(h) for h in all_data[0]]
    df_raw  = pd.DataFrame(all_data[1:], columns=headers)

    # Los scores 0-100 tienen código GOV_WGI_XX.SC
    df_filt = df_raw[
        df_raw["Country Code"].isin(countries) &
        df_raw["Indicator Code"].isin(WGI_INDICATORS)
    ].copy()

    year_cols = [c for c in headers if c.isdigit() and START_YEAR <= int(c) <= END_YEAR]
    if not year_cols:
        logger.warning("    WARN WGI: no se encontraron columnas de años en el Excel")
        return pd.DataFrame()

    all_rows: list[dict] = []
    for _, row in df_filt.iterrows():
        iso3 = str(row["Country Code"]).upper()
        for yc in year_cols:
            val = row.get(yc)
            if val is not None and pd.notna(val):
                try:
                    all_rows.append({
                        "pais_iso3": iso3,
                        "año":       int(yc),
                        "indicator": str(row["Indicator Code"]),
                        "value":     float(val),
                    })
                except (ValueError, TypeError):
                    pass

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    # Promediar los 6 indicadores SC (ya están en escala 0-100)
    composite = df.groupby(["pais_iso3", "año"])["value"].mean().reset_index()
    composite["value"] = composite["value"].clip(0, 100)
    composite.rename(columns={"value": "wgi_composite"}, inplace=True)
    logger.info("      WGI: %d filas (países: %s)", len(composite),
                composite["pais_iso3"].unique().tolist())
    return composite


def fetch_regional() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Descarga todos los datos regionales y guarda los CSVs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── WDI ──────────────────────────────────────────────────────────────────
    logger.info("\n  [->] WDI — %d indicadores × %d países", len(WDI_INDICATORS), len(COUNTRIES))
    wdi_frames: list[pd.DataFrame] = []

    for code, col_name in WDI_INDICATORS.items():
        logger.info("      %s → %s", code, col_name)
        df_ind = _wdi_fetch(code, COUNTRIES)
        if df_ind.empty:
            logger.warning("      (vacío)")
            continue
        df_ind = df_ind.rename(columns={"value": col_name})
        wdi_frames.append(df_ind)
        time.sleep(0.3)

    if wdi_frames:
        from functools import reduce
        df_wdi = reduce(
            lambda a, b: pd.merge(a, b, on=["pais_iso3", "año"], how="outer"),
            wdi_frames
        ).sort_values(["pais_iso3", "año"]).reset_index(drop=True)
        out_wdi = OUTPUT_DIR / "wdi_regional.csv"
        df_wdi.to_csv(out_wdi, index=False, encoding="utf-8-sig")
        logger.info("  OK WDI → %s  (%d filas)", out_wdi.name, len(df_wdi))
    else:
        df_wdi = pd.DataFrame()
        logger.warning("  WARN WDI: sin datos")

    # ── WGI ──────────────────────────────────────────────────────────────────
    logger.info("\n  [->] WGI — 6 indicadores de gobernanza × %d países", len(COUNTRIES))
    df_wgi = _wgi_fetch(COUNTRIES)
    if not df_wgi.empty:
        out_wgi = OUTPUT_DIR / "wgi_regional.csv"
        df_wgi.to_csv(out_wgi, index=False, encoding="utf-8-sig")
        logger.info("  OK WGI → %s  (%d filas)", out_wgi.name, len(df_wgi))
    else:
        logger.warning("  WARN WGI: sin datos")

    return df_wdi, df_wgi


if __name__ == "__main__":
    fetch_regional()
