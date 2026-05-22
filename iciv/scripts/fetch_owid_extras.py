"""
OWID Extras — Indicadores adicionales desde Our World in Data.

Fuente: Our World in Data (https://ourworldindata.org/)
        OWID redistribuye datasets oficiales (WB, IMF, UN, etc.) bajo licencia
        CC-BY abierta y con ciclos de actualización propios — a veces más
        recientes que los APIs originales.

Propósito académico:
  Complementar variables D4 (Apertura Comercial) y D5 (Capital Humano) para
  años 2024-2026 donde las fuentes originales (WDI, IMF) tienen lag.

Variables aportadas:
  - exportaciones_pct_pib  ← trade-as-share-of-gdp (OWID/WB)
  - desempleo_pct          ← unemployment-rate (OWID/IMF WEO 2026)
  - esperanza_vida_anos    ← life-expectancy (OWID/UN WPP)
  - mortalidad_infantil_x1000 ← infant-mortality (OWID/UN IGME)

Cobertura confirmada (mayo 2026):
  - trade-as-share-of-gdp: 2024
  - unemployment-rate: 2025 (proyección IMF WEO Apr 2026)
  - life-expectancy: 2023
  - infant-mortality: 2023

Método: API CSV de OWID — endpoint público, sin auth.

Salida: data/raw/owid_extras.csv
        Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_owid_extras.py
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

START = _CFG["serie"]["start_year"]
END   = _CFG["serie"]["end_year"]
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "owid_extras.csv"

# Mapa: slug OWID → (variable_name, source_attribution)
_OWID_SLUGS = {
    "trade-as-share-of-gdp": (
        "exportaciones_pct_pib",
        "OWID via World Bank WDI — Trade (% of GDP). https://ourworldindata.org/grapher/trade-as-share-of-gdp",
    ),
    "unemployment-rate": (
        "desempleo_pct",
        "OWID via IMF WEO 2026 — Unemployment rate. https://ourworldindata.org/grapher/unemployment-rate",
    ),
    "life-expectancy": (
        "esperanza_vida_anos",
        "OWID via UN WPP — Life expectancy at birth. https://ourworldindata.org/grapher/life-expectancy",
    ),
    "infant-mortality": (
        "mortalidad_infantil_x1000",
        "OWID via UN IGME — Infant mortality rate. https://ourworldindata.org/grapher/infant-mortality",
    ),
}


def _fetch_owid_slug(slug: str) -> pd.DataFrame:
    """Descarga un dataset de OWID y filtra Venezuela."""
    url = f"https://ourworldindata.org/grapher/{slug}.csv"
    headers = {"User-Agent": "Mozilla/5.0 (ICIV academic research)"}
    resp = requests.get(url, timeout=30, headers=headers)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    # Columns typically: Entity, Code, Year, <indicator>
    if "Code" not in df.columns:
        return pd.DataFrame()
    ven = df[df["Code"] == "VEN"].copy()
    if ven.empty:
        return pd.DataFrame()
    # The indicator value column is typically the 4th column (after Entity, Code, Year)
    value_cols = [c for c in ven.columns if c not in ("Entity", "Code", "Year")]
    if not value_cols:
        return pd.DataFrame()
    value_col = value_cols[0]
    ven = ven[["Year", value_col]].rename(columns={"Year": "año", value_col: "valor"})
    ven["año"] = ven["año"].astype(int)
    ven = ven.dropna(subset=["valor"])
    return ven[(ven["año"] >= START) & (ven["año"] <= END)].reset_index(drop=True)


def fetch_owid_extras() -> pd.DataFrame:
    """Descarga los datasets OWID configurados y los une en long-format."""
    rows: list[dict] = []
    for slug, (var_name, fuente) in _OWID_SLUGS.items():
        try:
            print(f"  Descargando {slug}...")
            df = _fetch_owid_slug(slug)
            if df.empty:
                print(f"    Sin datos para Venezuela en {slug}")
                continue
            for _, r in df.iterrows():
                rows.append({
                    "año": int(r["año"]),
                    "indicador": var_name,
                    "valor": float(r["valor"]),
                    "pais": "Venezuela",
                    "fuente": fuente,
                })
            print(f"    OK: {len(df)} años, último {df['año'].max()} = {df.iloc[-1]['valor']:.3f}")
        except Exception as exc:
            print(f"    ERR: {exc}")

    if not rows:
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    df = pd.DataFrame(rows)
    df = df.sort_values(["indicador", "año"]).reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 65)
    print("  OWID Extras - indicadores complementarios D4/D5 para VEN")
    print("  Fuente: Our World in Data (redistribución oficial)")
    print("=" * 65)
    df = fetch_owid_extras()
    if df.empty:
        print("\n  0 datos. owid_extras.csv NO actualizado.")
        sys.exit(1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\n  Guardado: {OUTPUT}  ({len(df)} filas)")
    print(df.groupby("indicador")["año"].agg(["count", "min", "max"]).to_string())
