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

import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings
from iciv.utils import save_dataframe  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START    = _CFG["serie"]["start_year"]
END      = _CFG["serie"]["end_year"]
BASE_URL = _CFG["sources"]["fred"]["base_url"]
SERIES: dict[str, str] = _CFG["sources"]["fred"]["series"]

OUTPUT = settings.paths.raw_fred


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

    # Atomic source refresh: a failure in any series invalidates this download.
    # No alternate providers and no prior values disguised as fresh observations.
    for series_id, col_name in SERIES.items():
        print(f"  Descargando {series_id} -> {col_name} ...")
        try:
            series = _fetch_series_annual(series_id, col_name)
            if series.empty:
                raise ValueError("respuesta sin observaciones")
            df[col_name] = series
        except Exception as exc:
            raise RuntimeError(
                f"FRED {series_id}: descarga fallida; fred.csv no actualizado."
            ) from exc

    df = df.reset_index()
    df = df.rename(columns={"año": "año"})
    return df.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Descargando FRED ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_fred()
    # Guarda: si la descarga no trajo ningun valor, NO se sobrescribe el CSV
    # existente (incidencia 2026-08-03, ver docs/METODOLOGIA.md seccion 9.1).
    save_dataframe(df, OUTPUT)
    print(f"Guardado: {OUTPUT}  ({len(df)} años)")
    print(df.tail(5).to_string(index=False))
