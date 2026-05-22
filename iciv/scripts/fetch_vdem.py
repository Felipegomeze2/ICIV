"""
V-Dem (Varieties of Democracy) — Democracia liberal Venezuela.

Fuente: V-Dem Institute, University of Gothenburg
        https://www.v-dem.net/data/the-v-dem-dataset/
        Coppedge et al. (2024). "V-Dem [Country-Year/Country-Date] Dataset v14"
        DOI: 10.23696/vdemcy24

Variable principal: v2x_libdem — Índice de Democracia Liberal (0-1)
  Combina: democracia electoral + estado de derecho + igualdad ante la ley.
  Venezuela: 0.42 (2000) → 0.03 (2020, mínimo) → 0.06 (2023).

Acceso: El dataset V-Dem requiere registro gratuito en v-dem.net.
  Este script intenta dos rutas:
  1. Our World in Data (OWID) publica un subconjunto de V-Dem en GitHub:
     https://raw.githubusercontent.com/owid/owid-datasets/...
  2. Harvard Dataverse (acceso abierto para investigación):
     https://dataverse.harvard.edu/api/access/datafile/{ID}
  Si ninguna funciona → variable queda NaN (no fallback inventado).

  Para descarga manual: registrarse en https://www.v-dem.net/data/
  y colocar el CSV en data/raw/vdem_ven.csv con columnas:
  year | v2x_libdem | fuente

Salida: data/raw/vdem.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_vdem.py
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
OUTPUT = settings.paths.raw_vdem

# ── Ruta 1: Our World in Data — grapher CSV directo (funciona sin auth) ─────
# OWID sirve CSVs de sus gráficas en /grapher/<slug>.csv (todos los países)
_OWID_URL = "https://ourworldindata.org/grapher/liberal-democracy.csv"
# Alternativa: electoral democracy (misma fuente V-Dem)
_OWID_URL_ALT = "https://ourworldindata.org/grapher/electoral-democracy.csv"

# ── Ruta 2: fallback — archivo manual en data/raw/ ───────────────────────────
_MANUAL_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "vdem_manual.csv"

_VEN_NAMES = {"Venezuela", "Venezuela, RB", "Venezuela (Bolivarian Republic of)"}


def _try_owid(url: str) -> pd.DataFrame | None:
    """
    Intenta descargar datos V-Dem desde OWID grapher CSV endpoint.
    Retorna DataFrame con columnas [año, valor] o None si falla.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (research project)"}
        resp = requests.get(url, timeout=60, headers=headers)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))

        # Buscar columna de democracia liberal (cualquier variante)
        libdem_col = None
        priority = ["liberal_democracy", "libdem", "liberal democracy", "democracy_index"]
        for pat in priority:
            for col in df.columns:
                if pat in col.lower():
                    libdem_col = col
                    break
            if libdem_col:
                break
        # Última opción: cualquier columna numérica después de Year
        if libdem_col is None:
            entity_col = "Entity" if "Entity" in df.columns else df.columns[0]
            year_col   = "Year"   if "Year"   in df.columns else df.columns[1]
            for col in df.columns:
                if col not in (entity_col, year_col, "Code") and pd.api.types.is_numeric_dtype(df[col]):
                    libdem_col = col
                    break

        if libdem_col is None:
            print(f"  OWID ({url.split('/')[-1]}): no se encontro columna de democracia")
            return None

        # Filtrar Venezuela
        entity_col = "Entity" if "Entity" in df.columns else df.columns[0]
        year_col   = "Year"   if "Year"   in df.columns else df.columns[1]

        ven = df[df[entity_col].str.contains("Venezuela", case=False, na=False)].copy()
        if ven.empty:
            print(f"  OWID ({url.split('/')[-1]}): Venezuela no encontrada")
            return None

        ven = ven[[year_col, libdem_col]].rename(
            columns={year_col: "año", libdem_col: "valor"}
        )
        ven = ven.dropna(subset=["valor"])
        ven["año"] = ven["año"].astype(int)
        ven = ven[(ven["año"] >= START) & (ven["año"] <= END)]

        print(f"  OWID V-Dem ({url.split('/')[-1]}): {len(ven)} anos para Venezuela")
        return ven if not ven.empty else None

    except Exception as exc:
        print(f"  OWID fallo ({url.split('/')[-1]}): {exc}")
        return None


def _try_manual_csv() -> pd.DataFrame | None:
    """
    Intenta leer un CSV descargado manualmente por el usuario.
    Formato esperado: year | v2x_libdem | (otras columnas opcionales)
    """
    if not _MANUAL_CSV.exists():
        return None
    try:
        df = pd.read_csv(_MANUAL_CSV)
        year_col = "year" if "year" in df.columns else "Year"
        val_col  = "v2x_libdem" if "v2x_libdem" in df.columns else df.columns[1]
        df = df[[year_col, val_col]].rename(
            columns={year_col: "año", val_col: "valor"}
        )
        df = df.dropna(subset=["valor"])
        df["año"] = df["año"].astype(int)
        df = df[(df["año"] >= START) & (df["año"] <= END)]
        print(f"  Manual CSV: {len(df)} años cargados desde {_MANUAL_CSV.name}")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  Manual CSV error: {exc}")
        return None


def fetch_vdem() -> pd.DataFrame:
    """
    Descarga o lee V-Dem liberal democracy index para Venezuela.
    Sin fallbacks inventados — si no hay datos reales, retorna DataFrame vacío.
    """
    # Intentar fuentes en orden de prioridad
    df_vals = None
    for attempt in [
        lambda: _try_owid(_OWID_URL),
        lambda: _try_owid(_OWID_URL_ALT),
        _try_manual_csv,
    ]:
        candidate = attempt()
        if candidate is not None and not candidate.empty:
            df_vals = candidate
            break

    if df_vals is None or df_vals.empty:
        print(
            "\n  ADVERTENCIA: V-Dem no disponible automaticamente.\n"
            "  Para datos completos: registrarse en https://www.v-dem.net/data/\n"
            "  Descargar 'V-Dem-CY-Core' CSV y guardar en data/raw/vdem_manual.csv\n"
            "  Columnas requeridas: year | v2x_libdem\n"
            "  Variable vdem_libdem_index quedara NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    rows = []
    for _, row in df_vals.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "vdem_libdem_index",
            "valor":     round(float(row["valor"]), 4),
            "pais":      "Venezuela",
            "fuente":    (
                "V-Dem Institute v14 (2024) — Liberal Democracy Index (v2x_libdem). "
                "Coppedge et al. DOI:10.23696/vdemcy24. "
                "Acceso vía Our World in Data (ourworldindata.org/democracy)."
            ),
        })

    df = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 65)
    print("  V-Dem — Liberal Democracy Index Venezuela")
    print("  Fuente: V-Dem Institute / Our World in Data")
    print("=" * 65)
    settings.paths.ensure_exists()

    df = fetch_vdem()

    if df.empty:
        print("\n  0 anos disponibles. vdem.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
