"""
Descarga artículos sobre Venezuela desde The Guardian y calcula el tono de los titulares.

Fuente:  The Guardian Open Platform API (key gratuita)
Salida:  data/raw/guardian.csv
         año | guardian_articulos_venezuela | guardian_tono_titulares

Para cada año se obtiene:
  - Total de artículos publicados sobre Venezuela
  - Tono medio de los primeros 50 titulares (VADER compound score, -1..+1)

Uso:
    python scripts/fetch_guardian.py
    # La API key se lee de config/settings.yaml o de la variable de entorno:
    # export GUARDIAN_API_KEY=tu_clave
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import yaml
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START  = _CFG["serie"]["start_year"]
END    = _CFG["serie"]["end_year"]
G_CFG  = _CFG["sources"]["guardian"]

BASE_URL     = G_CFG["base_url"]
QUERY        = G_CFG["query"]
COL_ARTICLES = G_CFG["col_articles"]
COL_TONE     = G_CFG["col_tone"]

API_KEY = os.environ.get(G_CFG.get("api_key_env", ""), "") or G_CFG.get("api_key", "")

OUTPUT = settings.paths.raw_guardian

_VADER = SentimentIntensityAnalyzer()
_HEADLINES_PER_YEAR = 50   # suficiente para estimación de tono anual


def _fetch_year(year: int) -> tuple[int | None, float | None]:
    """
    Consulta artículos de The Guardian para un año y computa el tono.

    Returns:
        (total_articulos, tono_promedio_vader)
        tono_vader en rango -1..+1 (compound score)
    """
    # ── 1. Total de artículos ────────────────────────────────────────────────
    params_count = {
        "q":          QUERY,
        "from-date":  f"{year}-01-01",
        "to-date":    f"{year}-12-31",
        "page-size":  0,
        "api-key":    API_KEY,
    }
    resp = requests.get(BASE_URL, params=params_count, timeout=30)
    resp.raise_for_status()
    total = resp.json().get("response", {}).get("total")

    time.sleep(0.2)

    # ── 2. Titulares para tono ───────────────────────────────────────────────
    params_titles = {
        "q":           QUERY,
        "from-date":   f"{year}-01-01",
        "to-date":     f"{year}-12-31",
        "page-size":   _HEADLINES_PER_YEAR,
        "show-fields": "headline",
        "api-key":     API_KEY,
    }
    resp2 = requests.get(BASE_URL, params=params_titles, timeout=30)
    resp2.raise_for_status()
    results = resp2.json().get("response", {}).get("results", [])

    headlines = [
        r.get("fields", {}).get("headline", "") or r.get("webTitle", "")
        for r in results
        if r.get("fields", {}).get("headline") or r.get("webTitle")
    ]

    if headlines:
        scores = [_VADER.polarity_scores(h)["compound"] for h in headlines]
        tone = round(sum(scores) / len(scores), 4)
    else:
        tone = None

    return total, tone


def fetch_guardian() -> pd.DataFrame:
    """
    Descarga conteo y tono anual de The Guardian sobre Venezuela.

    Returns:
        DataFrame con columnas: año, guardian_articulos_venezuela, guardian_tono_titulares
    """
    if not API_KEY:
        raise ValueError(
            "API key de The Guardian no encontrada. "
            f"Define '{G_CFG.get('api_key_env')}' como variable de entorno "
            "o añade 'api_key' en config/settings.yaml bajo sources.guardian."
        )

    records: list[dict] = []

    for year in range(START, END + 1):
        print(f"  {year} ...", end=" ", flush=True)
        try:
            total, tone = _fetch_year(year)
            records.append({"año": year, COL_ARTICLES: total, COL_TONE: tone})
            print(f"{total} artículos  tono={tone:.3f}" if tone is not None else f"{total} artículos")
        except Exception as exc:
            print(f"ERROR: {exc}")
            records.append({"año": year, COL_ARTICLES: None, COL_TONE: None})

        time.sleep(0.3)

    df = pd.DataFrame(records)
    df[COL_ARTICLES] = pd.to_numeric(df[COL_ARTICLES], errors="coerce")
    df[COL_TONE]     = pd.to_numeric(df[COL_TONE],     errors="coerce")
    return df.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Descargando The Guardian para '{QUERY}' ({START}–{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_guardian()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    n_art  = df[COL_ARTICLES].notna().sum()
    n_tone = df[COL_TONE].notna().sum()
    print(f"\nGuardado: {OUTPUT}  ({n_art} años, {n_tone} años con tono)")
    print(f"Tono promedio global: {df[COL_TONE].mean():.3f}")
