"""
Descarga indicadores WDI del Banco Mundial para Venezuela.

Fuente:  World Development Indicators API v2
Salida:  data/raw/wdi.csv  (formato ancho: una columna por indicador)

Nota sobre cobertura:
  Venezuela dejó de reportar varios indicadores al Banco Mundial en 2018.
  Los años sin datos en la API quedarán como NaN en el CSV.
  El pipeline los propagará como NaN y el dashboard indicará "Sin datos".

  Variables con cobertura incompleta conocida:
  - reservas_internacionales_usd: último reporte WDI ~2018
  - tipo_cambio_oficial_lcu_usd: último reporte WDI ~2017
  - tasa_alfabetizacion_adulta_pct: datos muy escasos (encuestas discontinuas)

Uso:
    python scripts/fetch_wdi.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

COUNTRY   = _CFG["serie"]["country_wb"]
START     = _CFG["serie"]["start_year"]
END       = _CFG["serie"]["end_year"]
BASE_URL  = _CFG["sources"]["wdi"]["base_url"]
PARAMS    = _CFG["sources"]["wdi"]["params"]
INDICATORS: dict[str, str] = _CFG["sources"]["wdi"]["indicators"]

OUTPUT = settings.paths.raw_wdi


def _fetch_indicator(indicator_code: str) -> list[dict]:
    """Descarga una serie temporal para Venezuela desde la API WDI."""
    url = BASE_URL.format(country=COUNTRY, indicator=indicator_code)
    params = {**PARAMS, "date": f"{START}:{END}"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if len(data) < 2 or not data[1]:
        return []
    return data[1]


def fetch_wdi() -> pd.DataFrame:
    """Descarga todos los indicadores WDI y devuelve un DataFrame ancho."""
    years = list(range(START, END + 1))
    df = pd.DataFrame({"año": years})

    for api_code, col_name in INDICATORS.items():
        print(f"  Descargando {api_code} -> {col_name} ...")
        try:
            records = _fetch_indicator(api_code)
            series = {
                int(r["date"]): r["value"]
                for r in records
                if r.get("value") is not None
            }
            df[col_name] = df["año"].map(series)
            n_missing = df[col_name].isnull().sum()
            n_present = len(df) - n_missing
            print(f"    OK: {n_present} años con datos, {n_missing} sin datos (NaN)")
        except Exception as exc:
            print(f"    [ERROR] {api_code}: {exc} — columna quedará como NaN")
            df[col_name] = None

    return df.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Descargando WDI para {COUNTRY} ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_wdi()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Guardado: {OUTPUT}  ({len(df)} años, {len(df.columns)-1} indicadores)")

    # Resumen de cobertura
    for col in df.columns[1:]:
        n_nan = df[col].isnull().sum()
        if n_nan > 0:
            years_missing = df.loc[df[col].isnull(), "año"].tolist()
            print(f"  SIN DATOS en {col}: {years_missing}")
