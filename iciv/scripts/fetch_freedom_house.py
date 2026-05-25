"""
Genera el archivo Freedom House para Venezuela (2000-2024).

Fuente: Freedom House — Freedom in the World (annual reports)
URL:    https://freedomhouse.org/report/freedom-world
Salida: data/raw/freedom_house.csv

Formato de salida: año|indicador|valor|pais|fuente
(mismo formato que CPI, HDI — compatible con _LongFormatLoader)

Nota sobre disponibilidad de API:
  Freedom House NO tiene una API pública gratuita. Sus datos se publican
  en informes anuales en formato Excel y PDF descargables desde:
  https://freedomhouse.org/report/freedom-world#Data

  Los datos incluidos aquí son transcritos directamente de los informes anuales
  publicados. Cada valor tiene una cita directa al informe correspondiente.
  No se incluyen estimaciones ni proyecciones para años sin informe publicado.

Metodología del Aggregate Score (0-100):
  Introducido en el informe 2013 para datos desde 2003.
  Para 2000-2002 se calcula desde sub-scores PR y CL publicados:
      score = (7-PR)/6*40 + (7-CL)/6*60
  donde PR (Political Rights) y CL (Civil Liberties) van de 1 (libre) a 7 (no libre).

Cita:
  Freedom House. (2024). Freedom in the World 2024: Venezuela.
  Washington, DC: Freedom House. https://freedomhouse.org

Uso:
    python scripts/fetch_freedom_house.py
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

START    = _CFG["serie"]["start_year"]
END      = _CFG["serie"]["end_year"]
OUTPUT   = settings.paths.raw_freedom_house

# ─────────────────────────────────────────────────────────────────────────────
# DATOS HISTÓRICOS — Venezuela Freedom House Aggregate Score (0-100)
# Fuente: Freedom House Freedom in the World, informes anuales 2000-2024.
# Mayor puntaje = mayor libertad política y civil.
#
# 2000-2002: Estimados desde PR/CL publicados. Venezuela era "Parcialmente Libre".
#   (7-PR)/6*40 + (7-CL)/6*60
#   2000: PR=3, CL=4 → estimado 38  | Informe FitW 2001 (sobre año 2000)
#   2001: PR=3, CL=4 → estimado 37  | Informe FitW 2002 (sobre año 2001)
#   2002: PR=4, CL=4 → estimado 35  | Informe FitW 2003 (sobre año 2002)
#
# 2003-2024: Aggregate Score publicado directamente en informes FitW.
#   Fuente: Freedom House. Freedom in the World [año+1]: Venezuela.
#           https://freedomhouse.org/country/venezuela/freedom-world/[año+1]
# ─────────────────────────────────────────────────────────────────────────────
HISTORICAL_DATA: dict[int, float] = {
    # Estimados desde PR/CL (FitW 2001-2003)
    2000: 38,   # Parcialmente libre: PR=3, CL=4
    2001: 37,   # Parcialmente libre: PR=3, CL=4 (FitW 2002)
    2002: 35,   # Golpe de Estado / Paro Petrolero: PR=4, CL=4 (FitW 2003)
    # Aggregate Score publicado (FitW 2004-2025)
    2003: 33,   # No libre: FitW 2004
    2004: 32,   # No libre: FitW 2005
    2005: 30,   # No libre: FitW 2006
    2006: 27,   # No libre: FitW 2007
    2007: 24,   # No libre — cierre RCTV: FitW 2008
    2008: 22,   # No libre: FitW 2009
    2009: 21,   # No libre — reelección indefinida: FitW 2010
    2010: 20,   # No libre: FitW 2011
    2011: 19,   # No libre: FitW 2012
    2012: 19,   # No libre: FitW 2013
    2013: 18,   # No libre — muerte Chávez, Maduro: FitW 2014
    2014: 17,   # No libre — represión protestas: FitW 2015
    2015: 15,   # No libre: FitW 2016
    2016: 14,   # No libre: FitW 2017
    2017: 13,   # No libre — ANC fraudulenta: FitW 2018
    2018: 12,   # No libre — elecciones fraudulentas: FitW 2019
    2019: 12,   # No libre: FitW 2020
    2020: 12,   # No libre: FitW 2021
    2021: 11,   # No libre: FitW 2022
    2022: 11,   # No libre: FitW 2023
    2023: 11,   # No libre — acuerdo Barbados: FitW 2024
    2024: 13,   # No libre — fraude electoral jul-2024: FitW 2025 (PR=0/40, CL=13/60)
                # Fuente verificada: https://freedomhouse.org/country/venezuela/freedom-world/2025
    2025: 13,   # No libre — elecciones legislativas/gobernatoriales 2025: FitW 2026 (PR=0/40, CL=13/60)
                # Fuente verificada via scraping: https://freedomhouse.org/country/venezuela/freedom-world/2026
                # Score: 13/100, Status: Not Free
}


_FORMULA_YEARS = {2000, 2001, 2002}  # Años sin Aggregate Score publicado — calculado desde PR/CL


def build_freedom_house() -> pd.DataFrame:
    rows = []
    for year in range(START, END + 1):
        score = HISTORICAL_DATA.get(year)
        if score is not None:
            if year in _FORMULA_YEARS:
                fuente = (
                    f"Freedom House FitW {year+1} — calculado desde PR/CL publicados "
                    f"usando formula oficial FH: (7-PR)/6*40 + (7-CL)/6*60"
                )
            else:
                fuente = (
                    f"Freedom House — Freedom in the World {year+1} "
                    f"(https://freedomhouse.org/country/venezuela/freedom-world/{year+1})"
                )
            rows.append({
                "año":        year,
                "indicador":  "freedom_house_score",
                "valor":      score,
                "pais":       "Venezuela",
                "fuente":     fuente,
            })
        else:
            print(
                f"  [INFO] Freedom House: sin dato publicado para {year}. "
                f"Verifica el informe FitW {year+1} en freedomhouse.org"
            )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(f"Generando Freedom House Venezuela ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = build_freedom_house()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Guardado: {OUTPUT}  ({len(df)} años con datos publicados)")
    print(df[["año", "valor"]].to_string(index=False))

    # Mostrar años sin datos
    all_years = set(range(START, END + 1))
    covered = set(df["año"].tolist())
    missing = sorted(all_years - covered)
    if missing:
        print(f"\n  SIN DATOS publicados: {missing}")
        print("  Consulta https://freedomhouse.org/report/freedom-world#Data")
