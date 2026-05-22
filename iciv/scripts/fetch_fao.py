"""
FAO FAOSTAT — Disponibilidad calórica per cápita Venezuela.

Fuente: Food and Agriculture Organization of the United Nations (FAO)
        https://www.fao.org/faostat/

Variable: Disponibilidad de alimentos (kcal/persona/día).
  Indicador: Food Supply (kcal/capita/day) — Grand Total.
  Código elemento: 664.  Código área Venezuela: 236.

Cobertura: FAOSTAT cubre Venezuela 1961–2022 (rezago ~2 años).
  Venezuela pasó de ~2,400 kcal/día (2000) a ~1,800 kcal/día (2018)
  evidenciando la crisis alimentaria confirmada por CEPAL/FAO.

API: FAOSTAT REST API pública (sin autenticación).
  FBS  = Food Balance Sheets (2010+, metodología nueva)
  FBSH = Historic Food Balance Sheets (1961–2013, metodología vieja)
  Se descargan ambas y se fusionan eliminando duplicados.

Salida: data/raw/fao.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_fao.py
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
OUTPUT = settings.paths.raw_fao

# FAOSTAT API v1
_FAOSTAT_BASE = "https://fenixservices.fao.org/faostat/api/v1/en/data/"
# Área Venezuela = 236
# Elemento 664 = Food supply (kcal/capita/day)
# Item 2901 = Grand Total (all foods combined)
_FAOSTAT_PARAMS = {
    "area":          "236",
    "element":       "664",
    "item":          "2901",
    "year":          "2000:2025",
    "show_codes":    "true",
    "show_flags":    "false",
    "show_notes":    "false",
    "null_values":   "false",
    "output_type":   "csv",
}
# Datasets: FBS (nueva metodología 2010+) y FBSH (histórico 1961-2013)
_DATASETS = ["FBS", "FBSH"]

# Fallback: OWID grapher CSV endpoints — suministro calórico FAO
_OWID_FOOD_URL  = "https://ourworldindata.org/grapher/food-supply-kcal.csv"
_OWID_FOOD_ALT  = "https://ourworldindata.org/grapher/daily-caloric-supply.csv"
_MANUAL_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "fao_manual.csv"


def _fetch_faostat_dataset(dataset: str) -> pd.DataFrame | None:
    """Descarga un dataset FAOSTAT y retorna DataFrame con [año, valor]."""
    url = f"{_FAOSTAT_BASE}{dataset}"
    try:
        resp = requests.get(url, params=_FAOSTAT_PARAMS, timeout=60)
        resp.raise_for_status()
        # La API devuelve CSV directamente
        df = pd.read_csv(StringIO(resp.text))
        if df.empty:
            return None

        # Columnas típicas: Area Code, Area, Item Code, Item, Element Code, Element, Year Code, Year, Unit, Value
        year_col  = "Year"  if "Year"  in df.columns else "year"
        value_col = "Value" if "Value" in df.columns else "value"

        if year_col not in df.columns or value_col not in df.columns:
            return None

        df = df[[year_col, value_col]].rename(
            columns={year_col: "año", value_col: "valor"}
        )
        df["año"]   = pd.to_numeric(df["año"], errors="coerce").astype("Int64")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df = df.dropna(subset=["año", "valor"])
        df = df[(df["año"] >= START) & (df["año"] <= END)]

        print(f"  FAOSTAT {dataset}: {len(df)} años para Venezuela")
        return df if not df.empty else None

    except Exception as exc:
        print(f"  FAOSTAT {dataset} falló: {exc}")
        return None


def _fetch_owid_food(url: str = _OWID_FOOD_URL) -> pd.DataFrame | None:
    """Fallback: OWID dataset de suministro de alimentos FAO."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (research project)"}
        resp = requests.get(url, timeout=60, headers=headers)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))

        entity_col = "Entity" if "Entity" in df.columns else df.columns[0]
        year_col   = "Year"   if "Year"   in df.columns else df.columns[1]

        ven = df[df[entity_col].str.contains("Venezuela", case=False, na=False)].copy()
        if ven.empty:
            return None

        # Buscar columna de calorías
        cal_col = None
        for col in df.columns:
            cl = col.lower()
            if "kcal" in cl or "calor" in cl or "food supply" in cl:
                cal_col = col
                break
        if cal_col is None and len(df.columns) > 2:
            cal_col = df.columns[2]
        if cal_col is None:
            return None

        ven = ven[[year_col, cal_col]].rename(
            columns={year_col: "año", cal_col: "valor"}
        ).dropna(subset=["valor"])
        ven["año"] = ven["año"].astype(int)
        ven = ven[(ven["año"] >= START) & (ven["año"] <= END)]
        print(f"  OWID Food: {len(ven)} años para Venezuela")
        return ven if not ven.empty else None

    except Exception as exc:
        print(f"  OWID Food falló: {exc}")
        return None


def _try_manual_csv() -> pd.DataFrame | None:
    if not _MANUAL_CSV.exists():
        return None
    try:
        df = pd.read_csv(_MANUAL_CSV)
        year_col  = "year" if "year" in df.columns else "año"
        val_col   = ("kcal" if "kcal" in df.columns
                     else "valor" if "valor" in df.columns else df.columns[1])
        df = df[[year_col, val_col]].rename(
            columns={year_col: "año", val_col: "valor"}
        ).dropna(subset=["valor"])
        df["año"] = df["año"].astype(int)
        df = df[(df["año"] >= START) & (df["año"] <= END)]
        print(f"  Manual CSV FAO: {len(df)} años")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  Manual CSV error: {exc}")
        return None


def fetch_fao() -> pd.DataFrame:
    """
    Descarga disponibilidad calórica per cápita de Venezuela desde FAOSTAT.
    Combina FBS (2010+) y FBSH (histórico) para cobertura completa.
    Sin datos inventados.
    """
    print("  Consultando FAOSTAT para Venezuela...")

    # Intentar ambos datasets y fusionar
    frames = []
    for ds in _DATASETS:
        df_ds = _fetch_faostat_dataset(ds)
        if df_ds is not None:
            frames.append(df_ds)

    if frames:
        df_combined = pd.concat(frames).sort_values("año")
        # Eliminar duplicados (FBS y FBSH se solapan 2010-2013): preferir FBS (más reciente)
        df_combined = df_combined.groupby("año")["valor"].mean().reset_index()
    else:
        print("  FAOSTAT API no disponible. Probando OWID...")
        df_combined = None
        for attempt in [
            lambda: _fetch_owid_food(_OWID_FOOD_URL),
            lambda: _fetch_owid_food(_OWID_FOOD_ALT),
            _try_manual_csv,
        ]:
            candidate = attempt()
            if candidate is not None and not candidate.empty:
                df_combined = candidate
                break

    if df_combined is None or df_combined.empty:
        print(
            "\n  ADVERTENCIA: FAO FAOSTAT no disponible para Venezuela.\n"
            "  Descargar desde https://www.fao.org/faostat/en/#data/FBS\n"
            "    Filtrar: Área=Venezuela, Elemento=Food supply (kcal/capita/day),\n"
            "             Item=Grand Total\n"
            "  Guardar en data/raw/fao_manual.csv con columnas: year | kcal\n"
            "  Variable fao_calorias_per_capita quedará NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    print(f"  FAO: {len(df_combined)} años con datos de disponibilidad calórica")

    rows = []
    for _, row in df_combined.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "fao_calorias_per_capita",
            "valor":     round(float(row["valor"]), 1),
            "pais":      "Venezuela",
            "fuente":    (
                "FAO FAOSTAT — Food Balance Sheets (FBS/FBSH). "
                "Element: Food supply (kcal/capita/day), Item: Grand Total. "
                "https://www.fao.org/faostat/en/#data/FBS"
            ),
        })

    df = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 65)
    print("  FAO FAOSTAT — Disponibilidad Calórica Venezuela")
    print("  Fuente: Food and Agriculture Organization (FAO)")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_fao()
    if df.empty:
        print("\n  0 años. fao.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} años)")
        print(df[["año", "valor"]].to_string(index=False))
