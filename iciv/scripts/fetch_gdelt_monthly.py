"""
GDELT monthly signals for the ICIV Pulse.

The GDELT DOC 2.0 API returns timeline points for matching coverage. This
fetcher aggregates those real timeline points by month and leaves the CSV
empty when the public API rate-limits the request. It never manufactures a
replacement series.
"""

from __future__ import annotations

import time
from datetime import date

import pandas as pd
import requests

from iciv.config import settings

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
QUERY = "Venezuela"
START_YEAR = 2015
PAUSE_SECONDS = 12


def _timeline(mode: str) -> pd.DataFrame:
    params = {
        "query": QUERY,
        "mode": mode,
        "format": "json",
        "startdatetime": f"{START_YEAR}0101000000",
        "enddatetime": f"{date.today().year}1231235959",
        "timelinesmooth": 0,
    }
    response = requests.get(BASE_URL, params=params, timeout=120)
    response.raise_for_status()
    payload = response.json()
    points = (payload.get("timeline") or [{}])[0].get("data") or []

    rows: list[dict] = []
    for point in points:
        dt = pd.to_datetime(point.get("date"), errors="coerce")
        value = pd.to_numeric(point.get("value"), errors="coerce")
        if pd.isna(dt) or pd.isna(value):
            continue
        rows.append({"fecha": dt, "valor": float(value)})
    return pd.DataFrame(rows)


def fetch_gdelt_monthly() -> pd.DataFrame:
    """Return long-format monthly tone and coverage volume for Pulse."""
    try:
        tone = _timeline("timelinetone")
        time.sleep(PAUSE_SECONDS)
        volume = _timeline("timelinevolraw")
    except Exception as exc:
        print(f"  GDELT monthly sin datos: {exc}")
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    frames: list[pd.DataFrame] = []
    if not tone.empty:
        by_month = tone.assign(
            año=tone["fecha"].dt.year,
            mes=tone["fecha"].dt.month,
        ).groupby(["año", "mes"], as_index=False)["valor"].mean()
        by_month["variable"] = "gdelt_tono_noticias"
        frames.append(by_month)

    if not volume.empty:
        by_month = volume.assign(
            año=volume["fecha"].dt.year,
            mes=volume["fecha"].dt.month,
        ).groupby(["año", "mes"], as_index=False)["valor"].sum()
        by_month["variable"] = "gdelt_cobertura_vol"
        frames.append(by_month)

    if not frames:
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    result = pd.concat(frames, ignore_index=True)
    result["fuente"] = "GDELT DOC 2.0 API monthly timeline"
    return result[["año", "mes", "variable", "valor", "fuente"]].sort_values(
        ["año", "mes", "variable"]
    ).reset_index(drop=True)


if __name__ == "__main__":
    settings.paths.ensure_exists()
    df = fetch_gdelt_monthly()
    df.to_csv(settings.paths.raw_gdelt_monthly, index=False, encoding="utf-8-sig")
    print(f"GDELT monthly: {len(df)} filas -> {settings.paths.raw_gdelt_monthly}")
