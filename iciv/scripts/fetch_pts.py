"""
Political Terror Scale (PTS) — Venezuela (2000–última edición disponible).

El PTS mide el nivel de represión política y violencia de Estado en un país,
codificado anualmente desde tres fuentes independientes de derechos humanos:
  - PTS_A: Amnesty International Annual Report
  - PTS_H: Human Rights Watch World Report
  - PTS_S: U.S. State Department Country Report on Human Rights Practices

Escala: 1 (mejor) — 5 (peor)
  1: Países con un sistema judicial seguro y estable; no existen encarcelamientos
     políticos
  2: Se producen encarcelamientos limitados por activismo no violento
  3: Existen encarcelamientos extensos de activistas y otras medidas de represión
  4: Los asesinatos, desapariciones y torturas son habituales
  5: El terror se extiende a toda la población; las muertes son numerosas

Cobertura Venezuela: 2000–2023 (24 años). PTS_H disponible desde 2013.
Fuente: Political Terror Scale (2024). Gibney, Cornett, Wood, Haschke & Arnon.

Metodología de agregación:
  Se calcula el promedio de los tres indicadores disponibles para cada año.
  Si hay un solo indicador disponible, se usa ese valor directamente.
  Si no hay ninguno, el año queda como NaN.

Relevancia para el ICIV:
  Captura la represión sistemática del Estado venezolano sobre la sociedad
  civil: detenciones arbitrarias de opositores, torturas documentadas por el
  CICPC/SEBIN/DGCIM, y asesinatos extrajudiciales (OVV 2020–2024).
  Es un indicador cuantitativo y citable del deterioro del Estado de Derecho,
  complementario al WGI y al CPI que miden corrupción e institucionalidad.

Citas:
  Gibney, M., Cornett, L., Wood, R., Haschke, P., & Arnon, D. (2024).
  Political Terror Scale 1976–2023. http://www.politicalterrorscale.org
  Amnesty International (2024). Venezuela: Estado de derechos humanos 2023.
  Human Rights Watch (2024). Venezuela: Informe Mundial 2024.

Fuente directa: https://www.politicalterrorscale.org/Data/Files/PTS-2024.csv
Salida: data/raw/pts.csv (año|indicador|valor|pais|fuente)

Uso:
    python scripts/fetch_pts.py
"""

from __future__ import annotations

import io
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
OUTPUT = settings.paths.raw_pts

# Se intenta la edición más reciente primero; la edición N cubre hasta el año N-1.
PTS_URLS = [
    ("2026", "https://www.politicalterrorscale.org/Data/Files/PTS-2026.csv"),
    ("2025", "https://www.politicalterrorscale.org/Data/Files/PTS-2025.csv"),
    ("2024", "https://www.politicalterrorscale.org/Data/Files/PTS-2024.csv"),
]


def fetch_pts() -> pd.DataFrame:
    """
    Descarga el Political Terror Scale y extrae la serie de Venezuela.
    Promedia PTS_A, PTS_H, PTS_S cuando están disponibles.
    Retorna DataFrame con columnas: año|indicador|valor|pais|fuente
    """
    resp = None
    edition = None
    for ed, url in PTS_URLS:
        print(f"  Descargando Political Terror Scale {ed}...")
        try:
            r = requests.get(
                url, timeout=60,
                headers={"User-Agent": "Mozilla/5.0 (academic research project ICIV)"},
            )
            r.raise_for_status()
            resp, edition = r, ed
            break
        except Exception as exc:
            print(f"    PTS {ed} no disponible: {exc}")
    if resp is None:
        print("  [ERROR] Ninguna edición PTS disponible. pts_terror_politico quedará sin datos.")
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    df_raw = pd.read_csv(io.StringIO(resp.text))

    # Filtrar Venezuela
    ven = df_raw[df_raw["Country"].str.contains("Venezuela", na=False, case=False)].copy()
    if ven.empty:
        print("  [WARN] PTS: no hay datos para Venezuela en el dataset.")
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    # Calcular promedio de los 3 indicadores disponibles por año
    rows = []
    for _, row in ven.iterrows():
        yr = int(row["Year"])
        if not (START <= yr <= END):
            continue
        scores = []
        for col in ("PTS_A", "PTS_H", "PTS_S"):
            val = row.get(col)
            if pd.notna(val) and val > 0:
                scores.append(float(val))
        if not scores:
            continue
        avg = round(sum(scores) / len(scores), 2)
        rows.append({
            "año":       yr,
            "indicador": "pts_terror_politico",
            "valor":     avg,
            "pais":      "Venezuela",
            "fuente":    (
                f"Political Terror Scale {edition} — Gibney et al. "
                f"(https://www.politicalterrorscale.org/Data/Files/PTS-{edition}.csv)"
            ),
        })

    if not rows:
        print("  [WARN] PTS: sin datos válidos para Venezuela en el rango de años.")
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    df = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    print(f"    PTS: {len(df)} años obtenidos ({df['año'].min()}-{df['año'].max()})")
    return df


if __name__ == "__main__":
    print(f"Descargando PTS Venezuela ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_pts()
    if df.empty:
        print("Sin datos disponibles.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"Guardado: {OUTPUT}  ({len(df)} años)")
        print(df[["año", "valor"]].to_string(index=False))
