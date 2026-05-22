"""
World Justice Project Rule of Law Index — Venezuela.

Fuente: World Justice Project (worldjusticeproject.org)
        https://worldjusticeproject.org/rule-of-law-index/

Variable: WJP Rule of Law Index Overall Score (0-1, mayor = mejor estado de derecho).
  9 dimensiones: gobierno abierto, ausencia de corrupción, gobierno limitado,
  derechos fundamentales, orden y seguridad, cumplimiento regulatorio,
  justicia civil y justicia penal.

Cobertura: 2007-2025 (con algunos años bianuales al inicio)

Acceso: WJP publica datos en Excel descargable desde su website.
  URL directa cambia cada año. Se intenta URL 2024, luego 2023.
  Para histórico completo: descargar manualmente desde worldjusticeproject.org
  y colocar en data/raw/wjp_manual.csv con columnas: year | score

  También disponible vía Our World in Data:
  https://ourworldindata.org/grapher/rule-of-law-index-wjp

Salida: data/raw/wjp.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_wjp.py
"""

from __future__ import annotations

import sys
from io import BytesIO, StringIO
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

# Our World in Data — grapher CSV endpoint (funciona sin auth)
_OWID_WJP_URL     = "https://ourworldindata.org/grapher/rule-of-law-index-wjp.csv"
_OWID_WJP_ALT     = "https://ourworldindata.org/grapher/rule-of-law-index.csv"

# URL directa WJP Excel — versiones 2024 y 2023
_WJP_EXCEL_URL    = "https://worldjusticeproject.org/sites/default/files/documents/WJP-ROLI-2024-v3-Final.xlsx"
_WJP_EXCEL_2023   = "https://worldjusticeproject.org/sites/default/files/documents/WJP-ROLI-2023-Scores.xlsx"

_MANUAL_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "wjp_manual.csv"
_VEN_NAMES  = {"Venezuela", "Venezuela, RB", "República Bolivariana de Venezuela"}


def _try_wjp_excel(url: str) -> pd.DataFrame | None:
    """Intenta descargar el Excel WJP y extraer Venezuela."""
    try:
        from io import BytesIO
        headers = {"User-Agent": "Mozilla/5.0 (research project)"}
        print(f"  WJP Excel: {url.split('/')[-1]}")
        resp = requests.get(url, timeout=60, headers=headers)
        resp.raise_for_status()
        xls = pd.ExcelFile(BytesIO(resp.content))
        # Buscar hoja con scores
        sheet = xls.sheet_names[0]
        for sh in xls.sheet_names:
            if any(k in sh.lower() for k in ["score", "overall", "country"]):
                sheet = sh
                break
        df = pd.read_excel(BytesIO(resp.content), sheet_name=sheet, header=0)
        # Buscar fila Venezuela
        country_col = df.columns[0]
        ven_mask = df[country_col].astype(str).str.contains("Venezuela", case=False, na=False)
        if not ven_mask.any():
            return None
        ven_row = df[ven_mask].iloc[0]
        # Buscar columna overall score
        score_col = None
        for col in df.columns:
            if any(k in str(col).lower() for k in ["overall", "wjp rule", "score", "index"]):
                try:
                    val = float(ven_row[col])
                    if 0 < val <= 1:
                        score_col = col
                        break
                except (ValueError, TypeError):
                    pass
        if score_col is None:
            return None
        # Inferir año del nombre de archivo
        fname = url.split("/")[-1]
        yr = None
        for part in fname.replace("-", "_").split("_"):
            part_clean = part.split(".")[0]
            if part_clean.isdigit() and 2000 <= int(part_clean) <= 2030:
                yr = int(part_clean)
                break
        if yr is None:
            return None
        val = float(ven_row[score_col])
        print(f"  WJP Excel {yr}: Venezuela = {val:.4f}")
        return pd.DataFrame([{"año": yr, "valor": val}])
    except Exception as exc:
        print(f"  WJP Excel fallo ({url.split('/')[-1]}): {exc}")
        return None


def _try_owid_wjp(url: str) -> pd.DataFrame | None:
    """Intenta obtener WJP series Venezuela desde OWID grapher CSV."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (research project)"}
        resp = requests.get(url, timeout=60, headers=headers)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))

        entity_col = "Entity" if "Entity" in df.columns else df.columns[0]
        year_col   = "Year"   if "Year"   in df.columns else df.columns[1]
        score_col  = None
        for col in df.columns:
            if "rule" in col.lower() or "roli" in col.lower() or "overall" in col.lower():
                score_col = col
                break
        if score_col is None and len(df.columns) > 2:
            score_col = df.columns[2]

        if score_col is None:
            return None

        ven = df[df[entity_col].isin(_VEN_NAMES)].copy()
        if ven.empty:
            ven = df[df[entity_col].str.contains("Venezuela", case=False, na=False)].copy()
        if ven.empty:
            return None

        ven = ven[[year_col, score_col]].rename(
            columns={year_col: "año", score_col: "valor"}
        ).dropna(subset=["valor"])
        ven["año"] = ven["año"].astype(int)
        ven = ven[(ven["año"] >= START) & (ven["año"] <= END)]
        print(f"  OWID WJP ({url.split('/')[-1]}): {len(ven)} anos para Venezuela")
        return ven if not ven.empty else None
    except Exception as exc:
        print(f"  OWID WJP fallo ({url.split('/')[-1]}): {exc}")
        return None


def _try_manual_csv() -> pd.DataFrame | None:
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
        print(f"  Manual CSV WJP: {len(df)} anos cargados")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  Manual CSV error: {exc}")
        return None


def fetch_wjp() -> pd.DataFrame:
    """Descarga WJP Rule of Law Index Venezuela. Sin datos inventados."""
    df_vals = None
    for attempt in [
        lambda: _try_owid_wjp(_OWID_WJP_URL),
        lambda: _try_owid_wjp(_OWID_WJP_ALT),
        lambda: _try_wjp_excel(_WJP_EXCEL_URL),
        lambda: _try_wjp_excel(_WJP_EXCEL_2023),
        _try_manual_csv,
    ]:
        candidate = attempt()
        if candidate is not None and not candidate.empty:
            df_vals = candidate
            break

    if df_vals is None or df_vals.empty:
        print(
            "\n  ADVERTENCIA: WJP Rule of Law no disponible automaticamente.\n"
            "  Descargar desde worldjusticeproject.org/rule-of-law-index/\n"
            "  Guardar en data/raw/wjp_manual.csv con columnas: year | score\n"
            "  Variable wjp_rule_of_law quedara NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    rows = []
    for _, row in df_vals.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "wjp_rule_of_law",
            "valor":     round(float(row["valor"]), 4),
            "pais":      "Venezuela",
            "fuente":    (
                "World Justice Project — Rule of Law Index. "
                "https://worldjusticeproject.org/rule-of-law-index/"
            ),
        })

    return pd.DataFrame(rows).sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 65)
    print("  WJP Rule of Law Index — Venezuela")
    print("  Fuente: World Justice Project")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_wjp()
    if df.empty:
        print("\n  0 anos. wjp.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
