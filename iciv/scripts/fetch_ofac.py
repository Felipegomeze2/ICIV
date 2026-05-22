"""
Sanciones OFAC vigentes hacia Venezuela — descarga SDN actual.

Fuente: US Treasury OFAC — Specially Designated Nationals (SDN) List
        CSV: https://www.treasury.gov/ofac/downloads/sdn.csv
        Actualización: diaria (OFAC publica cambios en tiempo real)

Lo que este script provee:
  - Conteo de entidades venezolanas en la lista SDN ACTUAL (año de ejecución)
  - La lista SDN es un SNAPSHOT del día de la descarga, no una serie histórica
  - Para años anteriores: no existe fuente pública reproducible con conteos anuales
    → los años históricos quedan NaN en el pipeline

Nota académica sobre limitación:
  OFAC no publica una API con series históricas de conteos por año-país.
  Los CRS Reports (R45046, RL32488) describen cualitativamente la escalada
  de sanciones pero no proveen tablas de conteo anual verificables y reproducibles.
  Dado el principio CERO datos inventados del proyecto, el histórico queda NaN.

Cita: U.S. Treasury OFAC. (2024). Venezuela-Related Sanctions.
      https://ofac.treasury.gov/sanctions-programs-and-country-information/venezuela-related-sanctions

Salida: data/raw/ofac.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_ofac.py
"""

from __future__ import annotations

import sys
from datetime import date
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

SDN_URL  = _CFG["sources"]["ofac"]["sdn_csv_url"]
OUTPUT   = settings.paths.raw_ofac

_VEN_TOKENS = ['"VEN "', '"VENEZUELA"', 'VENEZUELAN']


def build_ofac() -> pd.DataFrame:
    """
    Descarga la lista SDN actual de OFAC y cuenta entidades venezolanas.
    Solo retorna el año actual con el conteo real.
    Sin datos históricos hardcodeados — esos años quedan NaN en el pipeline.
    """
    current_year = date.today().year

    print("  Descargando lista SDN actual de OFAC...")
    try:
        resp = requests.get(SDN_URL, timeout=60)
        resp.raise_for_status()
    except Exception as exc:
        print(f"  ERROR: No se pudo descargar SDN: {exc}")
        print("  La variable ofac_sanciones_count quedara NaN este ano.")
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    lines = resp.text.splitlines()
    count = sum(
        1 for line in lines
        if any(tok in line.upper() for tok in _VEN_TOKENS)
    )
    print(f"  SDN actual: {count} entidades venezolanas")

    if count == 0:
        print("  ADVERTENCIA: 0 entidades encontradas — revisar tokens de busqueda.")
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    row = {
        "año":       current_year,
        "indicador": "ofac_sanciones_count",
        "valor":     float(count),
        "pais":      "Venezuela",
        "fuente":    (
            f"US Treasury OFAC SDN List descargada {date.today().isoformat()} — "
            f"https://www.treasury.gov/ofac/downloads/sdn.csv"
        ),
    }
    return pd.DataFrame([row])


if __name__ == "__main__":
    print("=" * 60)
    print("  OFAC SDN — Sanciones Venezuela")
    print("  Solo dato del ano actual (SDN es snapshot en tiempo real)")
    print("  Anos historicos: NaN (sin fuente reproducible disponible)")
    print("=" * 60)
    settings.paths.ensure_exists()

    df = build_ofac()

    if df.empty:
        print("\n  Sin datos — ofac.csv no actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}")
        print(df[["año", "valor"]].to_string(index=False))
