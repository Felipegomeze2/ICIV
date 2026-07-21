"""
Human Development Index (HDI) — Venezuela.

Fuente: UNDP Human Development Report, serie completa del vintage más
reciente, distribuida por Our World in Data:
    https://ourworldindata.org/grapher/human-development-index

Por qué OWID y no un CSV manual: el HDR revisa retroactivamente TODA la
serie en cada edición (cambios de metodología y de insumos). Mezclar
valores de vintages distintos produce una serie inconsistente. Este script
descarga siempre el vintage completo más reciente, de modo que todos los
años provienen de la misma revisión.

NOTA DE AUDITORÍA (2026-07-21):
  El hdi.csv manual anterior mezclaba vintages (ej. 2000=0.671 de un HDR
  antiguo vs 0.703 del vintage actual) y tenía huecos (2001-2004,
  2006-2009). Se reemplazó por la serie completa de un solo vintage.

Salida: data/raw/hdi.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_hdi.py
"""

from __future__ import annotations

import sys
from io import StringIO
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
OUTPUT = settings.paths.raw_hdi

_HEADERS = {"User-Agent": "Mozilla/5.0 (academic research project ICIV)"}
_OWID_HDI_URL = "https://ourworldindata.org/grapher/human-development-index.csv"


def fetch_hdi() -> pd.DataFrame:
    """Descarga la serie HDI completa de Venezuela (un solo vintage HDR)."""
    print("  Descargando HDI (UNDP HDR via Our World in Data)...")
    try:
        resp = requests.get(_OWID_HDI_URL, timeout=60, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as exc:
        print(
            f"  [ERROR] OWID HDI no disponible: {exc}\n"
            "  Se conserva el hdi.csv existente (no se inventa nada)."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    df = pd.read_csv(StringIO(resp.text))
    entity_col = "Entity" if "Entity" in df.columns else df.columns[0]
    year_col   = "Year" if "Year" in df.columns else df.columns[2]
    hdi_col    = next(
        (c for c in df.columns if "human development" in str(c).lower()),
        df.columns[3],
    )

    ven = df[df[entity_col].astype(str) == "Venezuela"].copy()
    if ven.empty:
        print("  [WARN] Venezuela no encontrada en OWID HDI.")
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    ven = ven[[year_col, hdi_col]].dropna()
    ven[year_col] = ven[year_col].astype(int)
    ven = ven[(ven[year_col] >= START) & (ven[year_col] <= END)]

    rows = []
    for _, r in ven.iterrows():
        val = float(r[hdi_col])
        if not (0.0 < val <= 1.0):
            raise ValueError(f"HDI fuera de rango (0,1]: {val}")
        rows.append({
            "año":       int(r[year_col]),
            "indicador": "hdi",
            "valor":     round(val, 4),
            "pais":      "Venezuela",
            "fuente":    (
                "UNDP Human Development Report (vintage vigente completo) "
                "via Our World in Data: "
                "https://ourworldindata.org/grapher/human-development-index"
            ),
        })

    out = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    print(f"    HDI: {len(out)} años ({out['año'].min()}-{out['año'].max()})")
    return out


if __name__ == "__main__":
    print(f"Descargando HDI Venezuela ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_hdi()
    if df.empty:
        print("Sin datos nuevos. hdi.csv NO modificado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"Guardado: {OUTPUT}  ({len(df)} años)")
        print(df[["año", "valor"]].to_string(index=False))
