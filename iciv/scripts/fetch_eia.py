"""
Descarga series energéticas de Venezuela desde la EIA (International Energy).

Fuente:  EIA International Data API v2
Salida:  data/raw/eia.csv  (formato ancho: año + 3 columnas energéticas)

Requiere:  variable de entorno EIA_API_KEY
           Obtener clave gratuita en: https://www.eia.gov/opendata/register.php

Nota sobre cobertura:
  Si EIA_API_KEY no está definida o la API falla, las columnas energéticas
  quedarán como NaN. El pipeline lo propagará y el dashboard indicará
  "Sin datos: requiere EIA_API_KEY".

Uso:
    export EIA_API_KEY=tu_clave_aqui
    python scripts/fetch_eia.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START     = _CFG["serie"]["start_year"]
END       = _CFG["serie"]["end_year"]
BASE_URL  = _CFG["sources"]["eia"]["base_url"]
KEY_ENV   = _CFG["sources"]["eia"]["api_key_env"]
FREQUENCY = _CFG["sources"]["eia"]["frequency"]
SERIES: dict[str, str] = _CFG["sources"]["eia"]["series"]

OUTPUT = settings.paths.raw_eia


def _get_api_key() -> str:
    key = os.environ.get(KEY_ENV, "") or _CFG["sources"]["eia"].get("api_key", "")
    if not key:
        raise EnvironmentError(
            f"API key de EIA no encontrada.\n"
            f"Define la variable de entorno '{KEY_ENV}' con tu clave gratuita.\n"
            f"Regístrate en: https://www.eia.gov/opendata/register.php\n"
            f"Las variables energéticas quedarán como NaN hasta que se configure."
        )
    return key


def _parse_intl_series_id(series_id: str) -> tuple[str, str, str, str]:
    """
    Parsea el formato INTL.{product}-{activity}-{country}-{unit}.A
    Retorna (productId, activityId, countryId, unit).
    Ejemplo: INTL.57-1-VEN-TBPD.A → ('57', '1', 'VEN', 'TBPD')
    """
    # Quitar prefijo INTL. y sufijo .A
    core = series_id.removeprefix("INTL.").removesuffix(".A")
    parts = core.split("-")
    # Formato: productId - activityId - countryId - unit (country tiene 3 chars)
    # INTL.57-1-VEN-TBPD.A → ['57', '1', 'VEN', 'TBPD']
    # INTL.2-12-VEN-BKWH.A → ['2', '12', 'VEN', 'BKWH']
    if len(parts) >= 4:
        return parts[0], parts[1], parts[2], parts[3]
    raise ValueError(f"No se puede parsear el series_id EIA: {series_id}")


def _fetch_series(series_id: str, api_key: str) -> dict[int, float]:
    """
    Descarga una serie EIA y retorna un dict {año: valor}.
    Usa el formato de facets del API v2 (productId + activityId + countryRegionId + unit).
    El formato antiguo facets[seriesId][] fue deprecado.
    """
    product_id, activity_id, country_id, unit = _parse_intl_series_id(series_id)
    params = {
        "api_key": api_key,
        "frequency": FREQUENCY,
        "data[]": "value",
        "facets[productId][]": product_id,
        "facets[activityId][]": activity_id,
        "facets[countryRegionId][]": country_id,
        "facets[unit][]": unit,
        "start": str(START),
        "end": str(END),
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 100,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    records = resp.json().get("response", {}).get("data", [])
    return {
        int(r["period"]): float(r["value"])
        for r in records
        if r.get("value") is not None
        and START <= int(r["period"]) <= END
    }


def fetch_eia() -> pd.DataFrame:
    years = list(range(START, END + 1))
    df = pd.DataFrame({"año": years})

    # Inicializar columnas como NaN
    for col_name in SERIES.values():
        df[col_name] = None

    try:
        api_key = _get_api_key()
    except EnvironmentError as e:
        print(f"  [ERROR] EIA: {e}")
        return df.sort_values("año").reset_index(drop=True)

    for series_id, col_name in SERIES.items():
        print(f"  Descargando {series_id} -> {col_name} ...")
        try:
            data = _fetch_series(series_id, api_key)
            if data:
                df[col_name] = df["año"].map(data)
                n_missing = df[col_name].isnull().sum()
                n_present = len(df) - n_missing
                print(f"    OK: {n_present} años con datos, {n_missing} sin datos (NaN)")
            else:
                print(f"    [WARN] {series_id}: API no devolvió datos — columna quedará como NaN")
        except Exception as exc:
            print(f"    [ERROR] {series_id}: {exc} — columna quedará como NaN")

    return df.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Descargando EIA ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_eia()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Guardado: {OUTPUT}  ({len(df)} años, {len(df.columns)-1} series)")

    # Resumen de cobertura
    for col in df.columns[1:]:
        n_nan = df[col].isnull().sum()
        if n_nan > 0:
            print(f"  SIN DATOS en {col}: {n_nan} años")
