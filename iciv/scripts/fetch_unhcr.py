"""
Descarga datos de población venezolana desplazada desde la API de UNHCR.

Fuentes:
  - UNHCR Population Statistics API:
    https://api.unhcr.org/population/v1/population/
    Parámetro clave: coo=VEN (country of origin = venezolanos desplazados al exterior)
    Nota: countries=VEN consulta personas residiendo EN Venezuela (incorrecto para este uso)

Salida: data/raw/unhcr.csv
Formato: año|indicador|valor|pais|fuente

Nota sobre cobertura de la API:
  La API de UNHCR con coo=VEN retorna refugiados y solicitantes de asilo venezolanos
  registrados a nivel global. Cubre 2000-2024 con 25 años de datos.
  El total incluye: refugees + asylum_seekers + other_of_concern.
  No incluye migrantes económicos no registrados (>7M para 2024 según R4V/OIM).

Contexto académico:
  Venezuela ha generado la segunda crisis de desplazamiento más grande del mundo,
  superando 7.7 millones de personas para 2024 (ACNUR/OIM/R4V).

Cita: ACNUR / R4V (2024). Situación Venezuela — Informe Regional.
      https://www.r4v.info/es/situations/platform

Uso:
    python scripts/fetch_unhcr.py
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

START  = _CFG["serie"]["start_year"]
END    = _CFG["serie"]["end_year"]
OUTPUT = settings.paths.raw_unhcr


def build_unhcr() -> pd.DataFrame:
    """
    Descarga datos de UNHCR Population Statistics API para Venezuela.
    Retorna DataFrame con refugiados/solicitantes por año.
    Si la API falla, retorna DataFrame vacío (variable quedará NaN en el pipeline).
    No usa datos de fallback estático.
    """
    print("  Consultando UNHCR Population Statistics API...")

    try:
        # coo=VEN: country of origin = Venezuelan emigrants/refugees abroad
        # yearFrom/yearTo: parameter format required by UNHCR API
        url = (
            "https://api.unhcr.org/population/v1/population/"
            f"?coo=VEN&yearFrom={START}&yearTo={END}&limit=100"
        )
        resp = requests.get(url, timeout=30, headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json().get("items", [])
    except Exception as exc:
        print(
            f"  [ERROR] UNHCR API no disponible: {exc}\n"
            "  La variable migrantes_vzla_millones quedará sin datos.\n"
            "  Para datos completos, descarga manualmente desde:\n"
            "  https://www.r4v.info/es/situations/platform"
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    if not data:
        print(
            "  [WARN] UNHCR API respondió pero no hay datos para Venezuela (VEN).\n"
            "  La variable migrantes_vzla_millones quedará sin datos."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    rows = []
    for item in data:
        yr = item.get("year")
        # Suma de todas las categorías disponibles: refugiados, solicitantes de asilo, otros
        total = (
            (item.get("refugees") or 0)
            + (item.get("asylum_seekers") or 0)
            + (item.get("other_of_concern") or 0)
        )
        if yr and total > 0 and START <= int(yr) <= END:
            rows.append({
                "año":       int(yr),
                "indicador": "migrantes_vzla_millones",
                "valor":     round(total / 1_000_000, 4),
                "pais":      "Venezuela",
                "fuente":    "UNHCR Population Statistics API",
            })

    if not rows:
        print(
            "  [WARN] UNHCR API: datos recibidos pero sin totales válidos.\n"
            "  La variable migrantes_vzla_millones quedará sin datos."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    df = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    print(f"    UNHCR API: {len(df)} años obtenidos ({df['año'].min()}-{df['año'].max()})")
    print(f"    NOTA: Esta cifra refleja solo refugiados/solicitantes de asilo registrados en UNHCR.")
    print(f"    El total de venezolanos desplazados (>7M en 2024) requiere datos R4V adicionales.")
    return df


if __name__ == "__main__":
    print(f"Descargando UNHCR para Venezuela ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = build_unhcr()
    if df.empty:
        print("Sin datos disponibles. El archivo CSV no será generado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"Guardado: {OUTPUT}  ({len(df)} años)")
        print(df[["año", "valor"]].to_string(index=False))
