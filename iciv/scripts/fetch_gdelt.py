"""
Descarga el tono y volumen de cobertura internacional sobre Venezuela desde GDELT.

Fuente:  GDELT Project — DOC 2.0 API (sin autenticación)
Salida:  data/raw/gdelt.csv
         año | gdelt_tono_noticias | gdelt_cobertura_vol

Estrategia: 2 peticiones totales (una para tono, una para volumen) cubriendo
el rango completo 2015–2024. GDELT devuelve puntos semanales para rangos largos,
que se agregan a promedios/sumas anuales.

Cobertura: 2015–2024 (GDELT DOC 2.0 API).
           Pre-2015 queda como NaN — se imputa en el pipeline.

Uso:
    python scripts/fetch_gdelt.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START     = _CFG["serie"]["start_year"]
END       = _CFG["serie"]["end_year"]
GDELT_CFG = _CFG["sources"]["gdelt"]

BASE_URL  = GDELT_CFG["base_url"]
QUERY     = GDELT_CFG["query"]
COL_TONE  = GDELT_CFG["col_tone"]
COL_VOL   = GDELT_CFG["col_volume"]

GDELT_START = max(START, 2015)
OUTPUT = settings.paths.raw_gdelt

_PAUSE_BETWEEN = 15   # segundos entre la petición de tone y la de vol


def _fetch_full_range(mode: str) -> pd.DataFrame:
    """
    Descarga el timeline completo 2015–END en una sola petición.

    GDELT devuelve granularidad semanal para rangos de ~10 años.
    Se parsea la fecha y se agrega a nivel anual.

    Args:
        mode: 'timelinetone' → promedio anual | 'timelinevol' → suma anual

    Returns:
        DataFrame con columnas: año, value
    """
    params = {
        "query":         QUERY,
        "mode":          mode,
        "format":        "json",
        "startdatetime": f"{GDELT_START}0101000000",
        "enddatetime":   f"{END}1231235959",
    }
    print(f"  Consultando {mode} ({GDELT_START}–{END}) ...", end=" ", flush=True)
    resp = requests.get(BASE_URL, params=params, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    entries = data.get("timeline", [])
    if not entries:
        print("sin datos")
        return pd.DataFrame(columns=["año", "value"])

    points = entries[0].get("data", [])
    if not points:
        print("sin datos")
        return pd.DataFrame(columns=["año", "value"])

    rows = []
    for pt in points:
        raw_date = pt.get("date", "")
        val = pt.get("value")
        if val is None or not raw_date:
            continue
        # Formato: "20240101T000000Z"
        try:
            year = int(raw_date[:4])
        except ValueError:
            continue
        rows.append({"año": year, "value": float(val)})

    df = pd.DataFrame(rows)
    n = len(df)
    print(f"{n} puntos descargados")
    return df


def fetch_gdelt() -> pd.DataFrame:
    """
    Descarga tono y volumen anuales de GDELT para Venezuela.

    Returns:
        DataFrame con columnas: año, gdelt_tono_noticias, gdelt_cobertura_vol
    """
    years_all = list(range(START, END + 1))
    result = pd.DataFrame({"año": years_all})

    # ── Tono ──────────────────────────────────────────────────────────────────
    try:
        df_tone = _fetch_full_range("timelinetone")
        if not df_tone.empty:
            annual_tone = df_tone.groupby("año")["value"].mean().round(4)
            result[COL_TONE] = result["año"].map(annual_tone)
        else:
            result[COL_TONE] = None
    except Exception as exc:
        print(f"  ERROR tono: {exc}")
        result[COL_TONE] = None

    print(f"  Pausa de {_PAUSE_BETWEEN}s para no saturar el rate limit ...")
    time.sleep(_PAUSE_BETWEEN)

    # ── Volumen ───────────────────────────────────────────────────────────────
    try:
        df_vol = _fetch_full_range("timelinevol")
        if not df_vol.empty:
            annual_vol = df_vol.groupby("año")["value"].sum().astype(int)
            result[COL_VOL] = result["año"].map(annual_vol)
        else:
            result[COL_VOL] = None
    except Exception as exc:
        print(f"  ERROR volumen: {exc}")
        result[COL_VOL] = None

    result[COL_TONE] = pd.to_numeric(result[COL_TONE], errors="coerce")
    result[COL_VOL]  = pd.to_numeric(result[COL_VOL],  errors="coerce")
    return result.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Descargando GDELT para '{QUERY}' ({GDELT_START}–{END}) ...")
    print(f"  Nota: años {START}–{GDELT_START - 1} quedarán como NaN (sin API histórica gratuita)")
    settings.paths.ensure_exists()

    df = fetch_gdelt()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    n_tone = df[COL_TONE].notna().sum()
    n_vol  = df[COL_VOL].notna().sum()
    print(f"\nGuardado: {OUTPUT}  ({n_tone} años con tono, {n_vol} años con volumen)")

    if n_tone > 0:
        print("\nResumen tono por año:")
        for _, row in df.dropna(subset=[COL_TONE]).iterrows():
            print(f"  {int(row['año'])}: tono={row[COL_TONE]:.3f}  vol={int(row[COL_VOL]) if pd.notna(row[COL_VOL]) else 'N/A'}")
