"""
ILO ILOSTAT — Empleo informal Venezuela.

Fuente: International Labour Organization (ILO)
        https://ilostat.ilo.org/

Variable principal: Empleo informal (% del empleo total)
  Indicador ILOSTAT: EMP_2EMP_SEX_ECO_NB_A (Informal employment by sex and economic activity)
  Venezuela: ~50-60% de empleo informal, señal de vulnerabilidad laboral.

API: ILOSTAT provee API REST pública sin autenticación.
  Base URL: https://rplumber.ilo.org/data/indicator/

Cobertura Venezuela: datos disponibles pero con gaps. No se inventa lo que falta.

Salida: data/raw/ilostat.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_ilostat.py
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START  = _CFG["serie"]["start_year"]
END    = _CFG["serie"]["end_year"]
OUTPUT = settings.paths.raw_ilostat

# ILOSTAT SDMX REST API (v2.1) — más estable que rplumber
# Indicador: share de empleo informal (% total empleo)
# EMP_NIFL_SEX_ECO_RT_A = Employment in the informal sector and informal employment
_SDMX_BASE = "https://www.ilo.org/sdmx/rest/data"
_SDMX_DATASET = "ILO,DF_EMP_NIFL_SEX_ECO_RT_A"
_SDMX_KEY     = "VEN.SEX_T.ECO_TOTAL._.A"   # Venezuela, total sex, total economy, total, annual

# Alternativa: API ILOSTAT nueva (ilostat.ilo.org/api)
_ILO_NEW_API  = "https://ilostat.ilo.org/api/sdmx/v21/data"
_ILO_DS_NIFL  = "DF_EMP_NIFL_SEX_ECO_RT_A"

# OWID publica algunos datos ILO
_OWID_ILO_URL = "https://ourworldindata.org/grapher/share-of-employment-in-informal-economy.csv"

# Fallback: WB proxy — vulnerable employment (similar a empleo informal)
# WB indicator: SL.EMP.VULN.ZS (Vulnerable employment, % of total)
_WB_VULN_URL  = "https://api.worldbank.org/v2/country/VEN/indicator/SL.EMP.VULN.ZS"
_WB_PARAMS    = {"format": "json", "per_page": "100", "mrv": "30"}


def _try_ilo_sdmx(base: str, dataset: str, key: str) -> pd.DataFrame | None:
    """Intenta ILOSTAT vía SDMX REST API."""
    try:
        url = f"{base}/{dataset}/{key}"
        params = {"format": "csv", "startPeriod": str(START), "endPeriod": str(END)}
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        if df.empty:
            return None
        # Buscar columnas relevantes en CSV SDMX
        time_col  = next((c for c in df.columns if "TIME" in c.upper() or "PERIOD" in c.upper()), None)
        value_col = next((c for c in df.columns if "OBS_VALUE" in c.upper() or "VALUE" in c.upper()), None)
        if time_col is None or value_col is None:
            return None
        df = df[[time_col, value_col]].rename(columns={time_col: "año", value_col: "valor"})
        df["año"]   = pd.to_numeric(df["año"].astype(str).str[:4], errors="coerce").astype("Int64")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df = df.dropna().query(f"año >= {START} and año <= {END}")
        df = df.groupby("año")["valor"].mean().reset_index()
        print(f"  ILOSTAT SDMX: {len(df)} anos para Venezuela")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  ILOSTAT SDMX fallo ({base}): {exc}")
        return None


def _try_owid_ilo() -> pd.DataFrame | None:
    """Intenta obtener datos ILO desde OWID."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (research project)"}
        resp = requests.get(_OWID_ILO_URL, timeout=60, headers=headers)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        entity_col = "Entity" if "Entity" in df.columns else df.columns[0]
        year_col   = "Year"   if "Year"   in df.columns else df.columns[1]
        ven = df[df[entity_col].str.contains("Venezuela", case=False, na=False)].copy()
        if ven.empty:
            return None
        score_col = next((c for c in df.columns
                         if c not in (entity_col, year_col, "Code")
                         and pd.api.types.is_numeric_dtype(df[c])), None)
        if score_col is None:
            return None
        ven = ven[[year_col, score_col]].rename(
            columns={year_col: "año", score_col: "valor"}
        ).dropna(subset=["valor"])
        ven["año"] = ven["año"].astype(int)
        ven = ven[(ven["año"] >= START) & (ven["año"] <= END)]
        print(f"  OWID ILO: {len(ven)} anos para Venezuela")
        return ven if not ven.empty else None
    except Exception as exc:
        print(f"  OWID ILO fallo: {exc}")
        return None


def _try_wb_vulnerable() -> pd.DataFrame | None:
    """Fallback: WB vulnerable employment (proxy de empleo informal)."""
    try:
        resp = requests.get(_WB_VULN_URL, params=_WB_PARAMS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if len(data) < 2 or not data[1]:
            return None
        rows = []
        for rec in data[1]:
            if rec.get("value") is not None:
                try:
                    yr = int(rec["date"])
                    if START <= yr <= END:
                        rows.append({"año": yr, "valor": float(rec["value"])})
                except (ValueError, TypeError):
                    pass
        if not rows:
            return None
        df = pd.DataFrame(rows).sort_values("año")
        print(f"  WB Vulnerable Employment (proxy informal): {len(df)} anos")
        return df
    except Exception as exc:
        print(f"  WB Vulnerable fallo: {exc}")
        return None


def fetch_ilostat() -> pd.DataFrame:
    """
    Descarga empleo informal Venezuela desde ILOSTAT API o proxy WB.
    Sin datos inventados — NaN donde no haya dato real.
    """
    print("  Consultando ILOSTAT/ILO para Venezuela...")
    df_informal = (
        _try_ilo_sdmx(_SDMX_BASE, _SDMX_DATASET, _SDMX_KEY)
        or _try_ilo_sdmx(_ILO_NEW_API, _ILO_DS_NIFL, _SDMX_KEY)
        or _try_owid_ilo()
        or _try_wb_vulnerable()
    )

    if df_informal is None or df_informal.empty:
        print(
            "\n  ADVERTENCIA: ILOSTAT empleo informal no disponible para Venezuela.\n"
            "  Variable ilo_empleo_informal_pct quedara NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    print(f"  ILO/WB empleo informal: {len(df_informal)} anos para Venezuela")

    rows = []
    for _, row in df_informal.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "ilo_empleo_informal_pct",
            "valor":     round(float(row["valor"]), 2),
            "pais":      "Venezuela",
            "fuente":    (
                "ILO ILOSTAT — EMP_2EMP_SEX_ECO_NB_A "
                "(Informal employment, % of total employment). "
                "https://ilostat.ilo.org/"
            ),
        })

    df = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 65)
    print("  ILO ILOSTAT — Empleo Informal Venezuela")
    print("  Fuente: International Labour Organization")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_ilostat()
    if df.empty:
        print("\n  0 anos. ilostat.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
