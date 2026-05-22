"""
Valida y copia los archivos estáticos (CPI, IEF, HDI) a data/raw/.

CPI, IEF y HDI no tienen APIs públicas gratuitas.
Se descargan manualmente y se colocan aquí para que este script los valide.

Fuentes (descarga manual):
  CPI:  https://www.transparency.org/en/cpi           -> cpi_source.csv
  IEF:  https://www.heritage.org/index/download       -> ief_source.csv
  HDI:  https://hdr.undp.org/data-center/documentation-and-downloads -> hdi_source.csv

Formato esperado de cada archivo (CSV largo):
    año,indicador,valor,pais,fuente
    2010,cpi_score,1.9,Venezuela,Transparency International
    ...

Uso:
    1. Descarga los CSV y colócalos en data/raw/ con los nombres *_source.csv
    2. python scripts/fetch_static.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START = _CFG["serie"]["start_year"]
END   = _CFG["serie"]["end_year"]

SOURCES = {
    "cpi": {
        "indicator": _CFG["sources"]["cpi"]["indicator_name"],
        "output":    settings.paths.raw_cpi,
    },
    "ief": {
        "indicator": _CFG["sources"]["ief"]["indicator_name"],
        "output":    settings.paths.raw_ief,
    },
    "hdi": {
        "indicator": _CFG["sources"]["hdi"]["indicator_name"],
        "output":    settings.paths.raw_hdi,
    },
}

REQUIRED_COLS = {"año", "indicador", "valor"}


def validate_static(name: str, path: Path, indicator: str) -> bool:
    """Verifica que el CSV tiene el formato correcto y el indicador esperado."""
    if not path.exists():
        print(f"  [FALTA]  {path.name} — descarga manual requerida")
        return False

    df = pd.read_csv(path, encoding="utf-8-sig")
    missing_cols = REQUIRED_COLS - set(df.columns)
    if missing_cols:
        print(f"  [ERROR]  {path.name}: faltan columnas {missing_cols}")
        return False

    present = df[df["indicador"] == indicator]
    if present.empty:
        print(f"  [ERROR]  {path.name}: indicador '{indicator}' no encontrado")
        return False

    in_range = present[(present["año"] >= START) & (present["año"] <= END)]
    print(f"  [OK]     {path.name}: {len(in_range)} observaciones ({START}-{END})")
    return True


if __name__ == "__main__":
    print(f"Validando fuentes estáticas ...")
    settings.paths.ensure_exists()

    all_ok = True
    for name, cfg in SOURCES.items():
        ok = validate_static(name, cfg["output"], cfg["indicator"])
        if not ok:
            all_ok = False

    if all_ok:
        print("\nTodas las fuentes estáticas están en orden.")
    else:
        print("\nAlgunas fuentes requieren descarga manual. Ver docstring del script.")
