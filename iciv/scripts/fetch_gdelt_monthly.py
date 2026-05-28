"""
GDELT monthly signals for the ICIV Pulse.

The GDELT DOC 2.0 API returns timeline points for matching coverage. This
fetcher aggregates those real timeline points by month and leaves the CSV
empty when the public API rate-limits the request. It never manufactures a
replacement series.
"""

from __future__ import annotations

import time
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from iciv.config import settings

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
QUERY = "Venezuela"
START_YEAR = 2015
PAUSE_SECONDS = 10
RETRIES = 3
HEADERS = {
    "User-Agent": "ICIV academic dashboard data fetcher (Felipe Gomez, Universidad EIA)",
    "Accept": "application/json,text/plain,*/*",
}


def _status_path() -> Path:
    return settings.paths.raw_gdelt_monthly.with_suffix(".status.json")


def _write_status(ok: bool, message: str, rows: int = 0) -> None:
    payload = {
        "ok": ok,
        "message": message,
        "rows": rows,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "GDELT DOC 2.0 API",
        "policy": "No synthetic fallback; preserve existing non-empty data on fetch failure.",
    }
    _status_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _existing_non_empty() -> pd.DataFrame | None:
    path = settings.paths.raw_gdelt_monthly
    if not path.exists() or path.stat().st_size <= 80:
        return None
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    required = {"año", "mes", "variable", "valor", "fuente"}
    if df.empty or not required.issubset(df.columns):
        return None
    return df


def _timeline(mode: str) -> pd.DataFrame:
    params = {
        "query": QUERY,
        "mode": mode,
        "format": "json",
        "startdatetime": f"{START_YEAR}0101000000",
        "enddatetime": f"{date.today().year}1231235959",
        "timelinesmooth": 0,
    }
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=90)
            response.raise_for_status()
            text = response.text.strip()
            if not text:
                raise ValueError("respuesta vacia")
            payload = response.json()
            break
        except Exception as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(PAUSE_SECONDS * attempt)
    else:
        raise RuntimeError(f"GDELT {mode} no entrego JSON valido: {last_error}")
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
        existing = _existing_non_empty()
        if existing is not None:
            msg = f"fetch fallo; se conserva CSV previo no vacio ({len(existing)} filas): {exc}"
            print(f"  GDELT monthly: {msg}")
            _write_status(False, msg, len(existing))
            return existing
        msg = f"sin datos reales: {exc}"
        print(f"  GDELT monthly {msg}")
        _write_status(False, msg, 0)
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
        _write_status(False, "API respondio pero sin puntos validos", 0)
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    result = pd.concat(frames, ignore_index=True)
    result["fuente"] = "GDELT DOC 2.0 API monthly timeline"
    result = result[["año", "mes", "variable", "valor", "fuente"]].sort_values(
        ["año", "mes", "variable"]
    ).reset_index(drop=True)
    _write_status(True, "fetch exitoso", len(result))
    return result


if __name__ == "__main__":
    settings.paths.ensure_exists()
    df = fetch_gdelt_monthly()
    df.to_csv(settings.paths.raw_gdelt_monthly, index=False, encoding="utf-8-sig")
    print(f"GDELT monthly: {len(df)} filas -> {settings.paths.raw_gdelt_monthly}")
