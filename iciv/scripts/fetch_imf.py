"""
Descarga indicadores macroeconómicos del FMI (IMF DataMapper API).

Fuente:  IMF DataMapper API v1 (sin autenticación)
Salida:  data/raw/imf.csv  (formato ancho: año + columnas macroeconómicas)

Nota sobre cobertura:
  Venezuela dejó de reportar regularmente al FMI en 2018-2019.
  Los años sin datos en la API quedarán como NaN en el CSV.
  El pipeline los propagará como NaN y el dashboard indicará "Sin datos".

Uso:
    python scripts/fetch_imf.py
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

COUNTRY    = _CFG["serie"]["country_imf"]
START      = _CFG["serie"]["start_year"]
END        = _CFG["serie"]["end_year"]
BASE_URL   = _CFG["sources"]["imf"]["base_url"]
INDICATORS: dict[str, str] = _CFG["sources"]["imf"]["indicators"]

OUTPUT = settings.paths.raw_imf


def _fetch_indicator(concept: str) -> dict[int, float]:
    """Descarga una serie del IMF DataMapper y retorna {año: valor}."""
    url = f"{BASE_URL}/{concept}/{COUNTRY}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    country_data: dict = (
        data.get("values", {})
            .get(concept, {})
            .get(COUNTRY, {})
    )
    return {
        int(year): float(val)
        for year, val in country_data.items()
        if val is not None and START <= int(year) <= END
    }


def fetch_imf() -> pd.DataFrame:
    years = list(range(START, END + 1))
    df = pd.DataFrame({"año": years})

    for concept, col_name in INDICATORS.items():
        print(f"  Descargando {concept} -> {col_name} ...")
        try:
            data = _fetch_indicator(concept)
            df[col_name] = df["año"].map(data)
            n_missing = df[col_name].isnull().sum()
            n_present = len(df) - n_missing
            print(f"    OK: {n_present} años con datos, {n_missing} sin datos (NaN)")
        except Exception as exc:
            print(f"    [ERROR] {concept}: {exc} — columna quedará como NaN")
            df[col_name] = None

    return df.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Descargando IMF para {COUNTRY} ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_imf()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Guardado: {OUTPUT}  ({len(df)} años, {len(df.columns)-1} indicadores)")

    # Resumen de cobertura
    for col in df.columns[1:]:
        n_nan = df[col].isnull().sum()
        if n_nan > 0:
            years_missing = df.loc[df[col].isnull(), "año"].tolist()
            print(f"  SIN DATOS en {col}: {years_missing}")
