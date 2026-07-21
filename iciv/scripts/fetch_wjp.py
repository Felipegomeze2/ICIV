"""
World Justice Project Rule of Law Index — Venezuela.

Fuente OFICIAL: World Justice Project — Historical Data File
    https://worldjusticeproject.org/rule-of-law-index/
    Archivo: {edicion}_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx
    Hoja "Historical Data", columna "WJP Rule of Law Index: Overall Score".

Variable: wjp_rule_of_law — Overall Score (0-1, mayor = mejor estado de derecho).
  9 factores: gobierno limitado, ausencia de corrupción, gobierno abierto,
  derechos fundamentales, orden y seguridad, cumplimiento regulatorio,
  justicia civil y justicia penal.

Cobertura REAL del índice: ediciones 2012-2013 en adelante. El índice WJP
NO existe antes de 2012; los años 2000-2011 quedan NaN en el pipeline.
Las ediciones dobles (2012-2013, 2017-2018) se asignan a ambos años
calendario, tal como las nombra el propio WJP.

Rango de referencia: Venezuela puntúa ~0.36 (2012) a ~0.26 (2024-2025),
último lugar del ranking global. Cualquier valor fuera de [0.15, 1.0] se
rechaza como error de escala.

NOTA DE AUDITORÍA (2026-07-21):
  Una versión anterior de este script tenía como fallback el grapher de OWID
  "rule-of-law-index.csv", que corresponde al índice Rule of Law de V-DEM
  (escala distinta, valores cercanos a 0 para Venezuela). Ese fallback
  contaminó wjp.csv con datos de otra fuente etiquetados como WJP
  (2000-2025, valores 0.211→0.009). Se eliminó todo fallback que no sea el
  archivo oficial WJP o un CSV manual descargado del propio WJP.

Fallback manual: data/raw/wjp_manual.csv con columnas year|score, solo si
  proviene de worldjusticeproject.org.

Salida: data/raw/wjp.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_wjp.py
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

START  = _CFG["serie"]["start_year"]
END    = _CFG["serie"]["end_year"]
OUTPUT = settings.paths.raw_wjp

_HEADERS = {"User-Agent": "Mozilla/5.0 (academic research project ICIV)"}

# Archivo histórico oficial WJP — se intenta la edición más reciente primero.
_WJP_HISTORICAL_URLS = [
    "https://worldjusticeproject.org/rule-of-law-index/downloads/2026_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx",
    "https://worldjusticeproject.org/rule-of-law-index/downloads/2025_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx",
    "https://worldjusticeproject.org/rule-of-law-index/downloads/2024_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx",
]

_MANUAL_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "wjp_manual.csv"

# Sanidad de escala: el Overall Score WJP nunca baja de ~0.25 (Venezuela es
# el mínimo global). Valores fuera de este rango indican mezcla de fuentes.
_SCORE_MIN, _SCORE_MAX = 0.15, 1.0


def _expand_edition_years(year_label: str) -> list[int]:
    """'2012-2013' -> [2012, 2013]; '2019' -> [2019]."""
    label = str(year_label).strip()
    if "-" in label:
        parts = label.split("-")
        try:
            return list(range(int(parts[0]), int(parts[1]) + 1))
        except ValueError:
            return []
    try:
        return [int(float(label))]
    except ValueError:
        return []


def _try_wjp_historical(url: str) -> pd.DataFrame | None:
    """Descarga el Historical Data File oficial WJP y extrae Venezuela."""
    fname = url.split("/")[-1]
    try:
        resp = requests.get(url, timeout=90, headers=_HEADERS)
        if resp.status_code != 200 or "html" in resp.headers.get("Content-Type", "").lower():
            print(f"  WJP {fname}: HTTP {resp.status_code} / no-excel — se omite")
            return None
        xls = pd.ExcelFile(BytesIO(resp.content))
        if "Historical Data" not in xls.sheet_names:
            print(f"  WJP {fname}: sin hoja 'Historical Data'")
            return None
        df = pd.read_excel(BytesIO(resp.content), sheet_name="Historical Data")

        code_col = "Country Code" if "Country Code" in df.columns else None
        if code_col:
            ven = df[df[code_col].astype(str) == "VEN"].copy()
        else:
            ven = df[df[df.columns[0]].astype(str).str.contains(
                "Venezuela", case=False, na=False)].copy()
        if ven.empty:
            print(f"  WJP {fname}: Venezuela no encontrada")
            return None

        score_col = None
        for col in df.columns:
            if "overall score" in str(col).lower():
                score_col = col
                break
        if score_col is None:
            print(f"  WJP {fname}: columna Overall Score no encontrada")
            return None

        year_col = "Year" if "Year" in ven.columns else ven.columns[1]
        rows = []
        for _, r in ven.iterrows():
            val = float(r[score_col])
            if not (_SCORE_MIN <= val <= _SCORE_MAX):
                raise ValueError(
                    f"Score fuera de rango WJP ({val}) — posible mezcla de escalas"
                )
            edition = str(r[year_col]).strip()
            for yr in _expand_edition_years(edition):
                if START <= yr <= END:
                    rows.append({"año": yr, "valor": round(val, 4), "edicion": edition})
        if not rows:
            return None
        out = pd.DataFrame(rows)
        out.attrs["source_url"] = url
        print(f"  WJP {fname}: {len(out)} años para Venezuela")
        return out
    except Exception as exc:
        print(f"  WJP {fname} fallo: {exc}")
        return None


def _try_manual_csv() -> pd.DataFrame | None:
    """CSV manual descargado del propio WJP (year|score)."""
    if not _MANUAL_CSV.exists():
        return None
    try:
        df = pd.read_csv(_MANUAL_CSV)
        year_col  = "year" if "year" in df.columns else "año"
        score_col = "score" if "score" in df.columns else df.columns[1]
        df = df[[year_col, score_col]].rename(
            columns={year_col: "año", score_col: "valor"}
        ).dropna(subset=["valor"])
        df["año"] = df["año"].astype(int)
        df = df[(df["año"] >= START) & (df["año"] <= END)]
        bad = df[(df["valor"] < _SCORE_MIN) | (df["valor"] > _SCORE_MAX)]
        if not bad.empty:
            print("  Manual CSV WJP: valores fuera de escala WJP — rechazado")
            return None
        df["edicion"] = df["año"].astype(str)
        df.attrs["source_url"] = "wjp_manual.csv (descarga manual worldjusticeproject.org)"
        print(f"  Manual CSV WJP: {len(df)} años cargados")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  Manual CSV error: {exc}")
        return None


def fetch_wjp() -> pd.DataFrame:
    """Descarga WJP Rule of Law Venezuela desde el archivo oficial. Sin fallbacks de otras fuentes."""
    df_vals = None
    for attempt in [
        *[lambda u=u: _try_wjp_historical(u) for u in _WJP_HISTORICAL_URLS],
        _try_manual_csv,
    ]:
        candidate = attempt()
        if candidate is not None and not candidate.empty:
            df_vals = candidate
            break

    if df_vals is None or df_vals.empty:
        print(
            "\n  ADVERTENCIA: WJP Rule of Law no disponible automaticamente.\n"
            "  Descargar el Historical Data File desde\n"
            "  worldjusticeproject.org/rule-of-law-index/ y guardar en\n"
            "  data/raw/wjp_manual.csv con columnas: year | score\n"
            "  La variable wjp_rule_of_law quedara NaN en el pipeline.\n"
            "  NO usar fuentes distintas al WJP (p.ej. V-Dem via OWID)."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    src = df_vals.attrs.get("source_url", "worldjusticeproject.org")
    rows = []
    for _, row in df_vals.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "wjp_rule_of_law",
            "valor":     round(float(row["valor"]), 4),
            "pais":      "Venezuela",
            "fuente":    (
                f"World Justice Project — Rule of Law Index, edicion {row['edicion']}, "
                f"Overall Score. Historical Data File oficial: {src}"
            ),
        })

    return pd.DataFrame(rows).sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 65)
    print("  WJP Rule of Law Index — Venezuela (archivo historico oficial)")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_wjp()
    if df.empty:
        print("\n  0 anos. wjp.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
