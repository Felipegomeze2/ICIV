"""
ACLED — Armed Conflict Location & Event Data — Venezuela.

Fuente: ACLED (acleddata.com)
        https://acleddata.com/data-export-tool/

Cobertura Venezuela: ACLED expandió a Latinoamérica en 2018.
  Para años anteriores (2000-2017) no hay datos ACLED de Venezuela.
  Los años sin dato quedan NaN — no se inventa histórico.

Variable: Eventos de violencia política por año (protestas + violencia).
  Incluye: batallas, violencia contra civiles, explosiones, protestas violentas.
  La alta frecuencia de eventos en 2017, 2019 (protestas) es capturada.

Acceso: ACLED requiere registro gratuito + API key.
  Este script usa la API pública ACLED con API key en .env:
    ACLED_EMAIL=tu@email.com
    ACLED_API_KEY=tu_api_key

  Sin API key → variable queda NaN.
  Registro gratuito en: https://developer.acleddata.com/

Salida: data/raw/acled.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_acled.py
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

START  = _CFG["serie"]["start_year"]
END    = _CFG["serie"]["end_year"]
OUTPUT = settings.paths.raw_acled

# Leer credenciales desde .env
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
_ACLED_API_BASE = "https://api.acleddata.com/acled/read/"
_ACLED_FIRST_YEAR = 2018  # ACLED no tiene cobertura Venezuela antes de 2018


def _load_acled_credentials() -> tuple[str | None, str | None]:
    """Lee ACLED_EMAIL y ACLED_API_KEY desde .env o variables de entorno."""
    email   = os.environ.get("ACLED_EMAIL")
    api_key = os.environ.get("ACLED_API_KEY")

    if email and api_key:
        return email, api_key

    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("ACLED_EMAIL="):
                email = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("ACLED_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")

    return email, api_key


def _fetch_acled_year(year: int, email: str, api_key: str) -> int | None:
    """
    Consulta ACLED API para Venezuela en un año específico.
    Retorna el conteo total de eventos de violencia política o None si falla.
    """
    params = {
        "key":        api_key,
        "email":      email,
        "country":    "Venezuela",
        "year":       year,
        "event_type": "Battles|Violence against civilians|Explosions/Remote violence|Protests",
        "fields":     "event_id_cnty,event_date,event_type,fatalities",
        "limit":      0,   # sin límite de resultados
        "export_type": "json",
    }
    try:
        resp = requests.get(_ACLED_API_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        count = int(data.get("count", 0))
        fatalities = sum(int(e.get("fatalities", 0)) for e in data.get("data", []))
        print(f"  ACLED {year}: {count} eventos, {fatalities} fatalidades")
        return count
    except Exception as exc:
        print(f"  ACLED {year} fallo: {exc}")
        return None


def fetch_acled() -> pd.DataFrame:
    """
    Descarga eventos ACLED Venezuela. Solo años 2018+ (cobertura real).
    Sin datos inventados para 2000-2017.
    """
    email, api_key = _load_acled_credentials()

    if not email or not api_key:
        print(
            "\n  ADVERTENCIA: ACLED requiere API key gratuita.\n"
            "  Registrarse en: https://developer.acleddata.com/\n"
            "  Agregar al archivo iciv/.env:\n"
            "    ACLED_EMAIL=tu@email.com\n"
            "    ACLED_API_KEY=tu_api_key\n"
            "  Variable acled_eventos_violencia quedara NaN en el pipeline.\n"
            "  NOTA: ACLED solo tiene datos Venezuela desde 2018."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    rows = []
    current_year = pd.Timestamp.now().year
    for year in range(_ACLED_FIRST_YEAR, min(END, current_year) + 1):
        count = _fetch_acled_year(year, email, api_key)
        if count is not None and count > 0:
            rows.append({
                "año":       year,
                "indicador": "acled_eventos_violencia",
                "valor":     float(count),
                "pais":      "Venezuela",
                "fuente":    (
                    f"ACLED (Armed Conflict Location & Event Data) {year}. "
                    "https://acleddata.com/ — Batallas + Violencia contra civiles "
                    "+ Explosiones + Protestas violentas."
                ),
            })

    if not rows:
        print("  ACLED: 0 eventos encontrados para Venezuela (revisar credenciales)")
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    print(f"\n  ACLED: {len(rows)} anos con datos reales (2018-{current_year})")
    print("  NOTA: anos 2000-2017 quedan NaN (ACLED no cubre Venezuela antes de 2018)")

    df = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 65)
    print("  ACLED — Violencia Politica Venezuela")
    print("  Fuente: ACLED (acleddata.com)")
    print("  Cobertura Venezuela: 2018+ solamente")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_acled()
    if df.empty:
        print("\n  0 anos. acled.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
