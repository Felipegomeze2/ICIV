"""
Global Hunger Index (GHI) — Venezuela.

Fuente: Welthungerhilfe / Concern Worldwide
        https://www.globalhungerindex.org/

Variable: GHI Score (0-100, mayor = más hambre).
  Componentes: desnutrición, retraso de crecimiento infantil, emaciación
  infantil, mortalidad infantil. Escala: <10=bajo, 10-19.9=moderado,
  20-34.9=serio, >=35=alarmante.

Cobertura: Publicado anualmente. Venezuela pasó de "Bajo" (<10) a "Serio" (~27)
  entre 2000 y 2022. Nota: algunos años GHI no calcula por datos insuficientes
  del país — esos años quedan NaN.

Acceso: Descarga Excel directa desde globalhungerindex.org
  También disponible en Our World in Data.

Salida: data/raw/ghi.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_ghi.py
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
OUTPUT = settings.paths.raw_ghi

# OWID grapher CSV endpoint — datos históricos GHI
_OWID_GHI_URL = "https://ourworldindata.org/grapher/global-hunger-index.csv"
_OWID_GHI_ALT = "https://ourworldindata.org/grapher/hunger-and-undernutrition.csv"
_MANUAL_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "ghi_manual.csv"
_VEN_NAMES  = {"Venezuela", "Venezuela, RB"}


def _try_owid_ghi(url: str) -> pd.DataFrame | None:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (research project)"}
        resp = requests.get(url, timeout=60, headers=headers)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))

        entity_col = "Entity" if "Entity" in df.columns else df.columns[0]
        year_col   = "Year"   if "Year"   in df.columns else df.columns[1]
        score_col  = None
        for col in df.columns:
            cl = col.lower()
            if "ghi" in cl or "hunger" in cl or "score" in cl:
                score_col = col
                break
        if score_col is None and len(df.columns) > 2:
            score_col = df.columns[2]
        if score_col is None:
            return None

        ven = df[df[entity_col].str.contains("Venezuela", case=False, na=False)].copy()
        if ven.empty:
            return None

        ven = ven[[year_col, score_col]].rename(
            columns={year_col: "año", score_col: "valor"}
        ).dropna(subset=["valor"])
        ven["año"] = ven["año"].astype(int)
        ven = ven[(ven["año"] >= START) & (ven["año"] <= END)]
        print(f"  OWID GHI: {len(ven)} anos para Venezuela")
        return ven if not ven.empty else None
    except Exception as exc:
        print(f"  OWID GHI fallo ({url.split('/')[-1]}): {exc}")
        return None


def _try_manual_csv() -> pd.DataFrame | None:
    if not _MANUAL_CSV.exists():
        return None
    try:
        df = pd.read_csv(_MANUAL_CSV)
        year_col  = "year" if "year" in df.columns else "año"
        score_col = "score" if "score" in df.columns else "ghi" if "ghi" in df.columns else df.columns[1]
        df = df[[year_col, score_col]].rename(
            columns={year_col: "año", score_col: "valor"}
        ).dropna(subset=["valor"])
        df["año"] = df["año"].astype(int)
        df = df[(df["año"] >= START) & (df["año"] <= END)]
        print(f"  Manual CSV GHI: {len(df)} anos")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  Manual CSV error: {exc}")
        return None


def fetch_ghi() -> pd.DataFrame:
    """Descarga Global Hunger Index Venezuela. Sin datos inventados."""
    df_vals = None
    for attempt in [
        lambda: _try_owid_ghi(_OWID_GHI_URL),
        lambda: _try_owid_ghi(_OWID_GHI_ALT),
        _try_manual_csv,
    ]:
        candidate = attempt()
        if candidate is not None and not candidate.empty:
            df_vals = candidate
            break

    if df_vals is None or df_vals.empty:
        print(
            "\n  ADVERTENCIA: GHI no disponible automaticamente.\n"
            "  Descargar desde globalhungerindex.org (Data download)\n"
            "  Guardar en data/raw/ghi_manual.csv con columnas: year | score\n"
            "  Variable ghi_score quedara NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    rows = []
    for _, row in df_vals.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "ghi_score",
            "valor":     round(float(row["valor"]), 2),
            "pais":      "Venezuela",
            "fuente":    (
                "Welthungerhilfe / Concern Worldwide — Global Hunger Index. "
                "https://www.globalhungerindex.org/"
            ),
        })

    return pd.DataFrame(rows).sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 65)
    print("  Global Hunger Index — Venezuela")
    print("  Fuente: Welthungerhilfe / Concern Worldwide")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_ghi()
    if df.empty:
        print("\n  0 anos. ghi.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
