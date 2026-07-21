"""
Freedom House — Freedom in the World, Aggregate Score — Venezuela.

Fuente OFICIAL: Freedom House "All Data" (Excel), ediciones FIW 2013+.
    https://freedomhouse.org/report/freedom-world#Data
    El archivo publica, por edición, los puntajes PR (0-40), CL (0-60) y
    Total (0-100). Cada edición cubre el año calendario anterior:
    año del dato = Edition - 1.

Cobertura REAL: el Aggregate Score 0-100 existe SOLO desde la edición 2013
(año calendario 2012). Antes de eso Freedom House publicaba únicamente
ratings PR/CL en escala 1-7, que NO son convertibles oficialmente a la
escala 0-100. Los años 2000-2011 quedan NaN en el pipeline.

NOTA DE AUDITORÍA (2026-07-21):
  Una versión anterior de este script contenía valores hardcodeados
  etiquetados como "Aggregate Score publicado" para 2003-2023 que NO
  coincidían con los publicados por Freedom House (ej. año 2012: archivo
  decía 19, publicado 39; año 2022: archivo decía 11, publicado 15).
  Además usaba una fórmula de conversión PR/CL→0-100 presentada como
  "fórmula oficial FH" que Freedom House nunca ha publicado. Todo eso se
  eliminó: ahora los valores se descargan del Excel oficial y solo se
  complementan ediciones recientes verificadas contra la página del país.

Serie oficial Venezuela (verificada 2026-07-21):
  2012:39 2013:38 2014:35 2015:35 2016:30 2017:26 2018:19 2019:16
  2020:14 2021:14 2022:15 2023:15 2024:13 2025:13 — "Not Free" desde 2017.

Salida: data/raw/freedom_house.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_freedom_house.py
"""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START    = _CFG["serie"]["start_year"]
END      = _CFG["serie"]["end_year"]
OUTPUT   = settings.paths.raw_freedom_house

_HEADERS = {"User-Agent": "Mozilla/5.0 (academic research project ICIV)"}

# Excel oficial "All Data" — se intenta la edición más reciente primero.
_FH_ALLDATA_URLS = [
    "https://freedomhouse.org/sites/default/files/2026-02/All_data_FIW_2013-2026.xlsx",
    "https://freedomhouse.org/sites/default/files/2025-02/All_data_FIW_2013-2025.xlsx",
    "https://freedomhouse.org/sites/default/files/2024-02/All_data_FIW_2013-2024.xlsx",
]

# Ediciones recientes que aún no aparecen en el Excel "All Data" disponible.
# Verificadas manualmente contra la página oficial del país (2026-07-21).
# {edición: (total_score, url_verificación)}
_RECENT_EDITIONS_VERIFIED: dict[int, tuple[int, str]] = {
    2025: (13, "https://freedomhouse.org/country/venezuela/freedom-world/2025"),
    2026: (13, "https://freedomhouse.org/country/venezuela/freedom-world/2026"),
}


def _try_fh_alldata(url: str) -> pd.DataFrame | None:
    """Descarga el Excel All Data de FH y extrae los Total de Venezuela por edición."""
    fname = url.split("/")[-1]
    try:
        resp = requests.get(url, timeout=90, headers=_HEADERS)
        if resp.status_code != 200 or "html" in resp.headers.get("Content-Type", "").lower():
            print(f"  FH {fname}: HTTP {resp.status_code} / no-excel — se omite")
            return None
        xls = pd.ExcelFile(BytesIO(resp.content))
        sheet = next((s for s in xls.sheet_names if "FIW" in s.upper()), xls.sheet_names[-1])
        df = pd.read_excel(BytesIO(resp.content), sheet_name=sheet, header=1)

        col_country = next((c for c in df.columns if "Country" in str(c)), df.columns[0])
        if "Edition" not in df.columns or "Total" not in df.columns:
            print(f"  FH {fname}: columnas Edition/Total no encontradas en hoja '{sheet}'")
            return None

        ven = df[df[col_country].astype(str).str.strip() == "Venezuela"].copy()
        if ven.empty:
            print(f"  FH {fname}: Venezuela no encontrada")
            return None

        rows = []
        for _, r in ven.iterrows():
            edition = int(r["Edition"])
            total   = float(r["Total"])
            if not (0 <= total <= 100):
                raise ValueError(f"Total fuera de rango 0-100: {total}")
            rows.append({"edicion": edition, "valor": total})
        out = pd.DataFrame(rows).drop_duplicates(subset="edicion")
        print(f"  FH {fname}: {len(out)} ediciones para Venezuela "
              f"({int(out['edicion'].min())}-{int(out['edicion'].max())})")
        return out
    except Exception as exc:
        print(f"  FH {fname} fallo: {exc}")
        return None


def fetch_freedom_house() -> pd.DataFrame:
    """Serie oficial del Aggregate Score de Venezuela. Solo puntajes publicados."""
    editions: dict[int, tuple[float, str]] = {}

    df_excel = None
    for url in _FH_ALLDATA_URLS:
        df_excel = _try_fh_alldata(url)
        if df_excel is not None:
            for _, r in df_excel.iterrows():
                editions[int(r["edicion"])] = (
                    float(r["valor"]),
                    f"Freedom House — All Data FIW (Excel oficial): {url}",
                )
            break

    if df_excel is None:
        print(
            "  ADVERTENCIA: Excel All Data de Freedom House no disponible.\n"
            "  Se usan solo las ediciones recientes verificadas manualmente."
        )

    # Complementar con ediciones recientes verificadas (no sobrescriben el Excel)
    for ed, (total, ver_url) in _RECENT_EDITIONS_VERIFIED.items():
        if ed not in editions:
            editions[ed] = (
                float(total),
                f"Freedom House — Freedom in the World {ed} ({ver_url})",
            )

    rows = []
    for ed in sorted(editions):
        year = ed - 1  # la edición cubre el año calendario anterior
        if not (START <= year <= END):
            continue
        total, fuente = editions[ed]
        rows.append({
            "año":       year,
            "indicador": "freedom_house_score",
            "valor":     total,
            "pais":      "Venezuela",
            "fuente":    fuente,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        missing = sorted(set(range(START, END + 1)) - set(df["año"]))
        pre2012 = [y for y in missing if y < 2012]
        if pre2012:
            print(
                f"  [INFO] Años sin Aggregate Score publicado (quedan NaN): {pre2012}\n"
                "         FH solo publica el score 0-100 desde la edición 2013 (año 2012)."
            )
    return df


if __name__ == "__main__":
    print(f"Freedom House Venezuela — Aggregate Score oficial ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_freedom_house()
    if df.empty:
        print("Sin datos. freedom_house.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"Guardado: {OUTPUT}  ({len(df)} años con score publicado)")
        print(df[["año", "valor"]].to_string(index=False))
