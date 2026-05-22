"""
Guardian Monthly — artículos sobre Venezuela agregados por mes.

A diferencia de `fetch_guardian.py` (anual), este preserva granularidad mensual
para el ICIV Pulse.

Fuente: The Guardian Open Platform API (https://open-platform.theguardian.com/)
Variables:
  - guardian_articulos_venezuela : volumen mensual de cobertura
  - guardian_tono_titulares      : tono VADER mensual de hasta 30 titulares

Cobertura: 2020-01 al mes actual.

Método: API REST + VADER sentiment analysis (Hutto & Gilbert 2014).

Salida: data/raw/guardian_monthly.csv
        Formato: año | mes | variable | valor | fuente

Uso:
    python scripts/fetch_guardian_monthly.py
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import yaml
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

PULSE_START_YEAR = 2010
END_YEAR = _CFG["serie"]["end_year"]
G_CFG = _CFG["sources"]["guardian"]

BASE_URL = G_CFG["base_url"]
QUERY    = G_CFG["query"]
API_KEY  = os.environ.get(G_CFG.get("api_key_env", ""), "") or G_CFG.get("api_key", "")

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "guardian_monthly.csv"

_VADER = SentimentIntensityAnalyzer()
_HEADLINES_PER_MONTH = 30

_FUENTE = "The Guardian Open Platform API + VADER sentiment (Hutto & Gilbert, 2014). https://open-platform.theguardian.com/"


def _fetch_month(year: int, month: int) -> tuple[int | None, float | None]:
    """Cuenta artículos + computa tono VADER mensual."""
    last_day = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd()
    from_date = f"{year}-{month:02d}-01"
    to_date = last_day.strftime("%Y-%m-%d")

    # Total artículos
    try:
        resp = requests.get(BASE_URL, params={
            "q": QUERY, "from-date": from_date, "to-date": to_date,
            "page-size": 0, "api-key": API_KEY,
        }, timeout=20)
        resp.raise_for_status()
        total = resp.json().get("response", {}).get("total")
    except Exception:
        return None, None

    time.sleep(0.2)

    # Titulares para tono
    try:
        resp = requests.get(BASE_URL, params={
            "q": QUERY, "from-date": from_date, "to-date": to_date,
            "page-size": _HEADLINES_PER_MONTH, "api-key": API_KEY,
        }, timeout=20)
        resp.raise_for_status()
        results = resp.json().get("response", {}).get("results", [])
        scores = []
        for art in results:
            title = art.get("webTitle", "")
            if title:
                scores.append(_VADER.polarity_scores(title)["compound"])
        tono = sum(scores) / len(scores) if scores else None
    except Exception:
        tono = None

    return total, tono


def fetch_guardian_monthly() -> pd.DataFrame:
    """Descarga artículos + tono mensual desde 2020-01 hasta mes actual."""
    if not API_KEY:
        raise RuntimeError("GUARDIAN_API_KEY no encontrado en .env")

    now = datetime.now()
    rows: list[dict] = []
    for year in range(PULSE_START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            # No descargar meses futuros
            if year > now.year or (year == now.year and month > now.month):
                continue
            total, tono = _fetch_month(year, month)
            if total is None and tono is None:
                continue
            if total is not None:
                rows.append({
                    "año": year, "mes": month,
                    "variable": "guardian_articulos_venezuela",
                    "valor": float(total),
                    "fuente": _FUENTE,
                })
            if tono is not None:
                rows.append({
                    "año": year, "mes": month,
                    "variable": "guardian_tono_titulares",
                    "valor": float(tono),
                    "fuente": _FUENTE,
                })
        print(f"  {year}: {sum(1 for r in rows if r['año']==year)} filas mensuales")

    if not rows:
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])
    return pd.DataFrame(rows).sort_values(["variable", "año", "mes"]).reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 65)
    print("  Guardian Monthly - Venezuela coverage + VADER sentiment")
    print(f"  Periodo: {PULSE_START_YEAR}-01 a {END_YEAR}-12 (hasta mes actual)")
    print("=" * 65)
    df = fetch_guardian_monthly()
    if df.empty:
        print("\n  0 datos.")
        sys.exit(1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\n  Guardado: {OUTPUT}  ({len(df)} filas)")
    print(df.groupby("variable").agg(
        n_meses=("año", "count"),
        primer_yr=("año", "min"),
        ultimo_yr=("año", "max"),
    ).to_string())
