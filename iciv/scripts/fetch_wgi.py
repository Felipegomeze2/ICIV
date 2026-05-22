"""
Descarga indicadores WGI (World Governance Indicators) del Banco Mundial.

Fuente:  Bulk download ZIP del Banco Mundial (DataBank)
Salida:  data/raw/wgi.csv  (formato ancho: año + 6 columnas SC)

Uso:
    python scripts/fetch_wgi.py
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

COUNTRY    = _CFG["serie"]["country_wb"]
START      = _CFG["serie"]["start_year"]
END        = _CFG["serie"]["end_year"]
ZIP_URL    = _CFG["sources"]["wgi"]["data_url"]
INDICATORS = _CFG["sources"]["wgi"]["indicators"]

OUTPUT = settings.paths.raw_wgi


def fetch_wgi() -> pd.DataFrame:
    """Descarga el ZIP del WGI, extrae Venezuela y devuelve DataFrame ancho."""
    print(f"  Descargando ZIP desde {ZIP_URL} ...")
    resp = requests.get(ZIP_URL, timeout=120)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        # El archivo principal suele llamarse WGIData.csv o similar
        csv_names = [n for n in zf.namelist() if n.endswith(".csv") and "Data" in n]
        if not csv_names:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
        print(f"  Archivos encontrados en ZIP: {csv_names}")
        raw = pd.read_csv(zf.open(csv_names[0]), encoding="utf-8-sig", low_memory=False)

    # Filtrar Venezuela y los indicadores SC que nos interesan
    ven = raw[raw["Country Code"] == COUNTRY].copy()
    available = [c for c in INDICATORS if c in ven["Indicator Code"].values]
    ven = ven[ven["Indicator Code"].isin(available)]

    # Pivotar: filas = año, columnas = indicador
    year_cols = [str(y) for y in range(START, END + 1) if str(y) in ven.columns]
    df_long = ven.melt(
        id_vars=["Indicator Code"],
        value_vars=year_cols,
        var_name="año",
        value_name="valor",
    )
    df_long["año"] = df_long["año"].astype(int)

    df_wide = df_long.pivot(index="año", columns="Indicator Code", values="valor").reset_index()
    df_wide.columns.name = None

    # Asegurar que todas las columnas requeridas estén presentes
    for col in INDICATORS:
        if col not in df_wide.columns:
            df_wide[col] = None

    return df_wide.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Descargando WGI para {COUNTRY} ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_wgi()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Guardado: {OUTPUT}  ({len(df)} años, {len(df.columns)-1} indicadores)")
