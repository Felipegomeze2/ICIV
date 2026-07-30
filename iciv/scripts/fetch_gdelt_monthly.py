"""
GDELT monthly signals for the ICIV Pulse.

The GDELT DOC 2.0 API returns timeline points for matching coverage. This
fetcher aggregates those real timeline points by month and never manufactures
a replacement series.

RATE LIMIT (diagnosticado 2026-07-29): el API publico responde HTTP 429 de
forma intermitente por FRECUENCIA de peticiones, no por tamano de ventana
(una ventana de 3 meses paso mientras una de 1 mes fallo segundos antes).
Estrategia:

  1. La serie se pide en TRAMOS ANUALES en vez de un unico rango de 11 anos.
  2. Cada tramo reintenta con backoff creciente.
  3. Los tramos que ya estan completos en el CSV no se vuelven a pedir
     (excepto el ano en curso, que siempre se refresca).
  4. Lo que se logra descargar se ACUMULA sobre el CSV previo: una corrida
     parcial mejora la cobertura sin borrar lo ya obtenido.

Asi la serie se completa a lo largo de varias corridas semanales sin inventar
un solo dato. El status JSON registra que anos se lograron y cuales faltan.
"""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from iciv.config import settings

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
QUERY = "Venezuela"
START_YEAR = 2015
PAUSE_SECONDS = 8          # pausa base entre peticiones consecutivas
RETRIES = 3
BACKOFF = (10, 30, 60)     # espera tras cada fallo, en segundos
HEADERS = {
    "User-Agent": "ICIV academic dashboard data fetcher (Felipe Gomez, Universidad EIA)",
    "Accept": "application/json,text/plain,*/*",
}

_MODES = {
    "timelinetone": ("gdelt_tono_noticias", "mean"),
    "timelinevolraw": ("gdelt_cobertura_vol", "sum"),
}


def _status_path() -> Path:
    return settings.paths.raw_gdelt_monthly.with_suffix(".status.json")


def _write_status(ok: bool, message: str, rows: int, detail: dict | None = None) -> None:
    payload = {
        "ok": ok,
        "message": message,
        "rows": rows,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "GDELT DOC 2.0 API",
        "policy": "No synthetic fallback; yearly chunks accumulate across runs.",
    }
    if detail:
        payload.update(detail)
    _status_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _existing() -> pd.DataFrame:
    """CSV previo en formato largo, o vacio si no hay nada usable."""
    cols = ["año", "mes", "variable", "valor", "fuente"]
    path = settings.paths.raw_gdelt_monthly
    if not path.exists() or path.stat().st_size <= 80:
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=cols)
    if df.empty or not set(cols).issubset(df.columns):
        return pd.DataFrame(columns=cols)
    return df[cols]


def _complete_years(df: pd.DataFrame, current_year: int) -> set[int]:
    """Anos con las 2 variables y 12 meses ya presentes (el ano en curso nunca cuenta)."""
    if df.empty:
        return set()
    done: set[int] = set()
    for year, grp in df.groupby("año"):
        year = int(year)
        if year >= current_year:
            continue
        if grp["variable"].nunique() >= 2 and grp[["mes"]].drop_duplicates().shape[0] >= 12:
            done.add(year)
    return done


def _timeline_year(mode: str, year: int) -> pd.DataFrame:
    """Puntos diarios de un ano para un modo. Lanza si el API no entrega JSON."""
    params = {
        "query": QUERY,
        "mode": mode,
        "format": "json",
        "startdatetime": f"{year}0101000000",
        "enddatetime": f"{year}1231235959",
        "timelinesmooth": 0,
    }
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=90)
            response.raise_for_status()
            text = response.text.strip()
            if not text:
                raise ValueError("respuesta vacia")
            payload = response.json()
            points = (payload.get("timeline") or [{}])[0].get("data") or []
            rows = []
            for point in points:
                dt = pd.to_datetime(point.get("date"), errors="coerce")
                value = pd.to_numeric(point.get("value"), errors="coerce")
                if pd.isna(dt) or pd.isna(value):
                    continue
                rows.append({"fecha": dt, "valor": float(value)})
            return pd.DataFrame(rows)
        except Exception as exc:
            last_error = exc
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF[min(attempt, len(BACKOFF) - 1)])
    raise RuntimeError(f"{mode} {year}: {last_error}")


def _aggregate(points: pd.DataFrame, variable: str, how: str) -> pd.DataFrame:
    if points.empty:
        return pd.DataFrame(columns=["año", "mes", "variable", "valor"])
    grouped = points.assign(
        año=points["fecha"].dt.year,
        mes=points["fecha"].dt.month,
    ).groupby(["año", "mes"], as_index=False)["valor"]
    by_month = grouped.mean() if how == "mean" else grouped.sum()
    by_month["variable"] = variable
    return by_month


def fetch_gdelt_monthly(max_years: int = 0) -> pd.DataFrame:
    """Serie mensual de tono y volumen GDELT, acumulada por tramos anuales.

    max_years > 0 limita cuantos tramos se piden en esta corrida (el resto
    queda para la siguiente). Sirve para que cada ejecucion termine en un
    tiempo acotado y la serie se complete progresivamente.
    """
    current_year = date.today().year
    previous = _existing()
    done = _complete_years(previous, current_year)
    years = [y for y in range(START_YEAR, current_year + 1) if y not in done]
    # Prioriza los anos mas recientes (los que mas importan para el Pulse)
    years = sorted(years, reverse=True)
    if max_years > 0:
        years = years[:max_years]

    print(f"  GDELT: {len(done)} anos ya completos, {len(years)} por pedir en esta corrida")
    if not years:
        msg = f"serie completa {START_YEAR}-{current_year - 1}; nada por pedir"
        print(f"  GDELT: {msg}")
        _write_status(True, msg, len(previous), {"years_complete": sorted(done)})
        return previous

    new_frames: list[pd.DataFrame] = []
    ok_years: list[int] = []
    failed: list[str] = []
    first_request = True

    for year in years:
        year_frames: list[pd.DataFrame] = []
        for mode, (variable, how) in _MODES.items():
            if not first_request:
                time.sleep(PAUSE_SECONDS)
            first_request = False
            try:
                points = _timeline_year(mode, year)
                year_frames.append(_aggregate(points, variable, how))
            except Exception as exc:
                failed.append(f"{year}/{mode}")
                print(f"  [WARN] GDELT {year} {mode}: {str(exc)[:90]}")
        if year_frames:
            got = pd.concat(year_frames, ignore_index=True)
            if not got.empty:
                new_frames.append(got)
                ok_years.append(year)
                n_meses = got[["mes"]].drop_duplicates().shape[0]
                print(f"  GDELT {year}: OK ({n_meses} meses, {got['variable'].nunique()} variables)")

    if not new_frames:
        if not previous.empty:
            msg = f"ningun tramo nuevo; se conserva CSV previo ({len(previous)} filas). Fallos: {failed}"
            print(f"  GDELT: {msg}")
            _write_status(False, msg, len(previous), {"years_complete": sorted(done), "failed": failed})
            return previous
        msg = f"sin datos reales; todos los tramos fallaron: {failed}"
        print(f"  GDELT: {msg}")
        _write_status(False, msg, 0, {"failed": failed})
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    fresh = pd.concat(new_frames, ignore_index=True)
    fresh["fuente"] = "GDELT DOC 2.0 API monthly timeline (tramos anuales)"
    fresh = fresh[["año", "mes", "variable", "valor", "fuente"]]

    # Acumular sobre lo previo: los tramos nuevos reemplazan sus propios meses
    _parts = [d for d in (previous, fresh) if not d.empty]
    merged = pd.concat(_parts, ignore_index=True) if len(_parts) > 1 else _parts[0].copy()
    merged = merged.drop_duplicates(subset=["año", "mes", "variable"], keep="last")
    merged = merged.sort_values(["año", "mes", "variable"]).reset_index(drop=True)

    n_meses = merged[["año", "mes"]].drop_duplicates().shape[0]
    msg = f"tramos nuevos {ok_years}; total {n_meses} meses"
    if failed:
        msg += f"; fallaron {failed}"
    print(f"  GDELT: {msg}")
    _write_status(
        not failed, msg, len(merged),
        {"years_complete": sorted(done | set(ok_years)), "failed": failed, "months": n_meses},
    )
    return merged


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GDELT mensual por tramos anuales")
    parser.add_argument("--years", type=int, default=0,
                        help="max tramos anuales por corrida (0 = todos los faltantes)")
    args = parser.parse_args()

    settings.paths.ensure_exists()
    df = fetch_gdelt_monthly(max_years=args.years)
    if df.empty:
        print("GDELT monthly: 0 filas — CSV no modificado")
    else:
        df.to_csv(settings.paths.raw_gdelt_monthly, index=False, encoding="utf-8-sig")
        print(f"GDELT monthly: {len(df)} filas -> {settings.paths.raw_gdelt_monthly}")
