"""
Descarga series macroeconómicas globales desde FRED (Federal Reserve St. Louis).

Fuente: FRED — https://fred.stlouisfed.org/
Salida: data/raw/fred.csv  (formato ancho: año + columnas de series)

No requiere API key. Descarga directa de CSV por serie.

Series descargadas:
  - DCOILWTICO : Precio WTI del petróleo crudo (USD/barril) — promedio anual
  - FEDFUNDS   : Tasa de fondos federales EE.UU. (%) — promedio anual

Relevancia académica:
  - WTI: Venezuela genera >95% de divisas del petróleo. El precio WTI es el
    driver externo más importante del ciclo económico venezolano.
  - FEDFUNDS: Ciclos de política monetaria de EE.UU. determinan flujos de
    capital hacia mercados emergentes — tasa alta = desincentivo a IED en EM.

Uso:
    python scripts/fetch_fred.py
"""

from __future__ import annotations

import os
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

START    = _CFG["serie"]["start_year"]
END      = _CFG["serie"]["end_year"]
BASE_URL = _CFG["sources"]["fred"]["base_url"]
SERIES: dict[str, str] = _CFG["sources"]["fred"]["series"]

OUTPUT = settings.paths.raw_fred


def _fetch_wti_from_eia() -> pd.Series:
    """
    Fallback: descarga WTI desde EIA cuando FRED está caído.
    EIA serie RWTC = WTI Cushing spot, anual.
    """
    # Buscar EIA API key
    api_key = None
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("EIA_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not api_key:
        api_key = os.environ.get("EIA_API_KEY", "")
    if not api_key:
        raise RuntimeError("EIA_API_KEY no encontrado en .env ni en entorno")

    url = (
        f"https://api.eia.gov/v2/petroleum/pri/spt/data/"
        f"?frequency=annual&data[0]=value&facets[series][]=RWTC"
        f"&start={START}&end={END}&api_key={api_key}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("response", {}).get("data", [])
    rows = [(int(d["period"]), float(d["value"])) for d in data]
    if not rows:
        raise RuntimeError("EIA WTI no devolvió datos")
    df = pd.DataFrame(rows, columns=["year", "value"]).groupby("year")["value"].mean()
    return df.rename("wti_precio_usd")


def _fetch_series_annual(series_id: str, col_name: str) -> pd.Series:
    """
    Descarga una serie FRED y calcula promedio anual.
    Retorna una Series con index=año, values=promedio anual.
    """
    url = f"{BASE_URL}?id={series_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    df = pd.read_csv(StringIO(resp.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["year"] = df["date"].dt.year

    annual = (
        df[df["year"].between(START, END)]
        .groupby("year")["value"]
        .mean()
        .rename(col_name)
    )
    return annual


def fetch_fred() -> pd.DataFrame:
    years = list(range(START, END + 1))
    df = pd.DataFrame({"año": years}).set_index("año")

    # Preserve previous data on transient API failures (don't overwrite real data with None)
    prior_df = None
    if OUTPUT.exists():
        try:
            prior_df = pd.read_csv(OUTPUT).set_index("año")
        except Exception:
            prior_df = None

    for series_id, col_name in SERIES.items():
        print(f"  Descargando {series_id} -> {col_name} ...")
        try:
            s = _fetch_series_annual(series_id, col_name)
            df[col_name] = s
        except Exception as exc:
            print(f"    ERROR FRED: {exc}")
            # Fallback 1: EIA para WTI (datos reales equivalentes)
            if series_id == "DCOILWTICO":
                try:
                    s = _fetch_wti_from_eia()
                    df[col_name] = s
                    print(f"    OK fallback EIA RWTC: {len(s)} años")
                    continue
                except Exception as e2:
                    print(f"    Fallback EIA también falló: {e2}")
            # Fallback 2: preservar dato anterior del CSV (no sobrescribir real data con None)
            if prior_df is not None and col_name in prior_df.columns:
                df[col_name] = prior_df[col_name]
                print(f"    Preservado dato anterior de {col_name} (CSV previo)")
            else:
                df[col_name] = None

    df = df.reset_index()
    df = df.rename(columns={"año": "año"})
    return df.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Descargando FRED ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_fred()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Guardado: {OUTPUT}  ({len(df)} años)")
    print(df.tail(5).to_string(index=False))
