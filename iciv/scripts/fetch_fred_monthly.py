"""
FRED Monthly — agregación mensual de series macro globales desde FRED.

A diferencia de `fetch_fred.py` (anual), este script preserva la granularidad
mensual para alimentar el ICIV Pulse mensual.

Fuente: Federal Reserve Bank of St. Louis — FRED Economic Data
        https://fred.stlouisfed.org/

Series descargadas (todas DIARIAS o MENSUALES nativas):
  - DCOILWTICO   : Precio WTI del petróleo (USD/barril) — diaria → mensual
  - FEDFUNDS     : Tasa fondos federales EE.UU. (%) — mensual nativa
  - DCOILBRENTEU : Brent oil (USD/bbl) — diaria → mensual
  - DTWEXBGS     : Trade-weighted USD Index (Broad) — diaria → mensual
  - VIXCLS       : CBOE VIX volatility — diaria → mensual
  - DGS10        : US Treasury 10Y yield (%) — diaria → mensual

Método: agregación por promedio mensual desde el CSV diario.

Cobertura: 2010-01 hasta el mes anterior al día actual (lag ~1-7 días).
Nota: USD Index (DTWEXBGS) empieza en 2006-01; los demás desde 1986/1990.
Para el Pulse pre-2015 los pesos se redistribuyen sobre las variables disponibles.

Salida: data/raw/fred_monthly.csv
        Formato: año | mes | variable | valor | fuente

Uso:
    python scripts/fetch_fred_monthly.py
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

# Extendido a 2010: FRED series (WTI, Brent, Fed Funds, VIX, UST10Y) disponibles desde 1986-2006.
# USD Index (DTWEXBGS broad) disponible desde 2006-01.
# Pre-2020: cobertura Pulse será menor (sin UNHCR/OFAC) pero pesos se redistribuyen.
PULSE_START_YEAR = 2010
END_YEAR = _CFG["serie"]["end_year"]

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "fred_monthly.csv"

_BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_SERIES = {
    "DCOILWTICO":   "wti_precio_usd",
    "FEDFUNDS":     "tasa_fed_funds_pct",
    "DCOILBRENTEU": "brent_precio_usd",
    "DTWEXBGS":     "usd_index_broad",
    "VIXCLS":       "vix_volatility",
    "DGS10":        "ust_10y_yield_pct",
}

_FUENTE_BASE = (
    "Federal Reserve Bank of St. Louis - FRED Economic Data. "
    "https://fred.stlouisfed.org/series/{series_id}"
)


def _fetch_monthly(series_id: str, col_name: str) -> pd.DataFrame:
    """Descarga CSV diario y agrega a mensual."""
    url = f"{_BASE_URL}?id={series_id}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna()
    df["año"] = df["date"].dt.year
    df["mes"] = df["date"].dt.month

    monthly = (
        df[df["año"] >= PULSE_START_YEAR]
        .groupby(["año", "mes"], as_index=False)["value"]
        .mean()
        .rename(columns={"value": "valor"})
    )
    monthly["variable"] = col_name
    monthly["fuente"] = _FUENTE_BASE.format(series_id=series_id)
    return monthly[["año", "mes", "variable", "valor", "fuente"]]


def fetch_fred_monthly() -> pd.DataFrame:
    """Descarga las 6 series FRED a granularidad mensual."""
    all_rows: list[pd.DataFrame] = []
    for series_id, col_name in _SERIES.items():
        print(f"  Descargando {series_id} -> {col_name} (mensual)...")
        try:
            m = _fetch_monthly(series_id, col_name)
            print(f"    OK: {len(m)} meses, rango {m['año'].min()}-{m['mes'].min():02d} a {m['año'].max()}-{m['mes'].max():02d}")
            all_rows.append(m)
        except Exception as exc:
            print(f"    ERR FRED {series_id}: {exc}")

    if not all_rows:
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])
    df = pd.concat(all_rows, ignore_index=True)
    df = df.sort_values(["variable", "año", "mes"]).reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 65)
    print("  FRED Monthly - WTI, Brent, Fed Funds, USD, VIX, UST 10Y")
    print(f"  Periodo: {PULSE_START_YEAR}-01 a {END_YEAR}-12")
    print("=" * 65)
    df = fetch_fred_monthly()
    if df.empty:
        print("\n  0 datos. fred_monthly.csv NO actualizado.")
        sys.exit(1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\n  Guardado: {OUTPUT}  ({len(df)} filas)")
    print(df.groupby("variable").agg(
        n_meses=("año", "count"),
        primer=("año", "min"),
        ultimo=("año", "max"),
    ).to_string())
