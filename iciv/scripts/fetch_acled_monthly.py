"""
ACLED — eventos de conflicto y protesta mensuales, Venezuela.

Fuente: Armed Conflict Location & Event Data Project (ACLED)
    https://acleddata.com — API OAuth: https://acleddata.com/oauth/token
    Endpoint: https://acleddata.com/api/acled/read
    Cobertura Venezuela: desde 2018 (inicio de cobertura ACLED en LatAm).

Credenciales (NUNCA se escriben en el codigo ni en el repo):
  Variables de entorno ACLED_EMAIL y ACLED_PASSWORD, o un archivo iciv/.env
  (ignorado por git) con lineas:
      ACLED_EMAIL=tu_correo
      ACLED_PASSWORD=tu_contrasena
  En GitHub Actions se inyectan como secrets del repositorio.

Variables de salida (agregacion mensual de eventos):
  - acled_eventos_total      : numero de eventos ACLED en el mes
  - acled_protestas          : eventos con event_type = Protests
  - acled_violencia_politica : Battles + Violence against civilians +
                               Explosions/Remote violence + Riots
  - acled_fatalidades        : suma de fatalities del mes

Rol en el proyecto: capa auxiliar para SATV y analisis de contexto.
NO entra al score ICIV anual ni al Pulse mientras no se decida su peso y se
re-ejecute el backtest (documentado en docs/FUENTES_Y_VARIABLES.md).

Politica de datos: si las credenciales faltan o el API falla, se conserva el
CSV previo si existe y no se escribe nada nuevo. Sin datos inventados.

Salida: data/raw/acled_monthly.csv
Formato: año | mes | variable | valor | fuente

Uso:
    python scripts/fetch_acled_monthly.py
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

_ICIV_DIR = Path(__file__).resolve().parents[1]
_CFG = yaml.safe_load((_ICIV_DIR / "config" / "settings.yaml").read_text(encoding="utf-8"))

START_YEAR = 2018  # inicio de cobertura ACLED para Venezuela
END_YEAR   = _CFG["serie"]["end_year"]

OUTPUT = _ICIV_DIR / "data" / "raw" / "acled_monthly.csv"

_TOKEN_URL = "https://acleddata.com/oauth/token"
_DATA_URL  = "https://acleddata.com/api/acled/read"
_HEADERS   = {"User-Agent": "Mozilla/5.0 (academic research project ICIV)"}

_VIOLENCE_TYPES = {
    "Battles",
    "Violence against civilians",
    "Explosions/Remote violence",
    "Riots",
}

_FUENTE = (
    "ACLED — Armed Conflict Location & Event Data Project, API oficial "
    "(acleddata.com), eventos Venezuela agregados por mes. "
    "Raleigh, Kishi & Linke (2023)."
)


def _load_credentials() -> tuple[str, str] | None:
    """Lee ACLED_EMAIL/ACLED_PASSWORD del entorno o de iciv/.env. Nunca las imprime."""
    env_file = _ICIV_DIR / ".env"
    file_vars: dict[str, str] = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                file_vars[k.strip()] = v.strip().strip('"').strip("'")
    email = os.environ.get("ACLED_EMAIL") or file_vars.get("ACLED_EMAIL")
    password = os.environ.get("ACLED_PASSWORD") or file_vars.get("ACLED_PASSWORD")
    if not email or not password:
        return None
    return email, password


def _get_token(email: str, password: str) -> str:
    resp = requests.post(
        _TOKEN_URL,
        headers={**_HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": email,
            "password": password,
            "grant_type": "password",
            "client_id": "acled",
            "scope": "authenticated",
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _fetch_events(token: str) -> pd.DataFrame:
    """Descarga eventos Venezuela paginados (solo campos necesarios)."""
    frames = []
    page = 1
    while True:
        params = {
            "_format": "json",
            "country": "Venezuela",
            "event_date": f"{START_YEAR}-01-01|{END_YEAR}-12-31",
            "event_date_where": "BETWEEN",
            "fields": "event_date|event_type|fatalities",
            "limit": 5000,
            "page": page,
        }
        resp = requests.get(
            _DATA_URL,
            params=params,
            headers={**_HEADERS, "Authorization": f"Bearer {token}"},
            timeout=120,
        )
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data", [])
        if not data:
            break
        frames.append(pd.DataFrame(data))
        print(f"  ACLED pagina {page}: {len(data)} eventos")
        if len(data) < 5000:
            break
        page += 1
        if page > 40:  # tope de seguridad
            break
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def fetch_acled_monthly() -> pd.DataFrame:
    """Agrega eventos ACLED Venezuela a variables mensuales. Sin datos inventados."""
    creds = _load_credentials()
    if creds is None:
        print(
            "  [WARN] Credenciales ACLED no configuradas.\n"
            "  Definir ACLED_EMAIL y ACLED_PASSWORD como variables de entorno\n"
            "  o en iciv/.env (ignorado por git). No se escribe nada nuevo."
        )
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    try:
        token = _get_token(*creds)
        print("  ACLED: token OAuth obtenido")
        ev = _fetch_events(token)
    except Exception as exc:
        print(f"  [ERROR] ACLED API: {exc}\n  No se escribe nada nuevo.")
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    if ev.empty:
        print("  [WARN] ACLED devolvio 0 eventos para Venezuela.")
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    ev["event_date"] = pd.to_datetime(ev["event_date"], errors="coerce")
    ev["fatalities"] = pd.to_numeric(ev["fatalities"], errors="coerce").fillna(0)
    ev = ev.dropna(subset=["event_date"])
    ev["año"] = ev["event_date"].dt.year
    ev["mes"] = ev["event_date"].dt.month

    rows = []
    for (year, month), grp in ev.groupby(["año", "mes"]):
        metrics = {
            "acled_eventos_total":      len(grp),
            "acled_protestas":          int((grp["event_type"] == "Protests").sum()),
            "acled_violencia_politica": int(grp["event_type"].isin(_VIOLENCE_TYPES).sum()),
            "acled_fatalidades":        int(grp["fatalities"].sum()),
        }
        for var, val in metrics.items():
            rows.append({
                "año": int(year), "mes": int(month),
                "variable": var, "valor": val, "fuente": _FUENTE,
            })

    out = pd.DataFrame(rows).sort_values(["variable", "año", "mes"]).reset_index(drop=True)
    n_meses = out[["año", "mes"]].drop_duplicates().shape[0]
    print(f"  ACLED: {len(ev)} eventos → {n_meses} meses agregados "
          f"({out['año'].min()}-{out['año'].max()})")
    return out


if __name__ == "__main__":
    print("=" * 65)
    print("  ACLED — eventos de conflicto mensuales, Venezuela")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_acled_monthly()
    if df.empty:
        if OUTPUT.exists():
            print("\n  Sin datos nuevos. Se conserva el CSV existente.")
        else:
            print("\n  0 filas. acled_monthly.csv NO creado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} filas)")
