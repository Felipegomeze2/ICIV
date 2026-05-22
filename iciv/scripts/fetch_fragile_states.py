"""
Fragile States Index (Fund for Peace) — Fragilidad estatal Venezuela.

Fuente: Fund for Peace
        https://fragilestatesindex.org/data/
        FSI Annual Report, descarga Excel directa.

Variable: FSI Total Score (0-120, mayor = más frágil).
  Venezuela pasó de ~63 (2005, "En Advertencia") a ~98 (2023, "Alta Alerta").
  12 indicadores: cohesión (seguridad, facciones, legitimidad), economía
  (declive, desigualdad, pobreza), política (estado de derecho, DDHH, presión
  demográfica), social (refugiados, intervención externa).

Acceso: El Excel está disponible sin registro en fragilestatesindex.org/data/
  El script descarga el archivo más reciente usando la URL directa conocida.
  Si la URL cambia → usa archivo manual en data/raw/fsi_manual.xlsx

Cobertura: 2005-2024 (anual desde 2013, bienal 2005-2012)

Salida: data/raw/fragile_states.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_fragile_states.py
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
OUTPUT = settings.paths.raw_fragile

# URLs directas confirmadas desde fragilestatesindex.org/excel/
# Los filenames usan -DOWNLOAD o -download (no solo el año)
_FSI_URLS = [
    # 2024 (puede no existir aún — Fund for Peace publica anualmente en mayo/junio)
    "https://fragilestatesindex.org/wp-content/uploads/2024/06/FSI-2024-DOWNLOAD.xlsx",
    "https://fragilestatesindex.org/wp-content/uploads/2024/06/fsi-2024-download.xlsx",
    # 2023 — URL confirmada
    "https://fragilestatesindex.org/wp-content/uploads/2023/06/FSI-2023-DOWNLOAD.xlsx",
    # 2022 — URL confirmada
    "https://fragilestatesindex.org/wp-content/uploads/2022/07/fsi-2022-download.xlsx",
    # 2021
    "https://fragilestatesindex.org/wp-content/uploads/2021/05/fsi-2021.xlsx",
    # 2020
    "https://fragilestatesindex.org/wp-content/uploads/2020/05/fsi-2020.xlsx",
    # 2019
    "https://fragilestatesindex.org/wp-content/uploads/2019/04/fsi-2019.xlsx",
    # 2018
    "https://fragilestatesindex.org/wp-content/uploads/2018/04/fsi-2018.xlsx",
    # 2017
    "https://fragilestatesindex.org/wp-content/uploads/2017/05/fsi-2017.xlsx",
    # 2016
    "https://fragilestatesindex.org/wp-content/uploads/2016/07/fsi-2016.xlsx",
    # 2015
    "https://fragilestatesindex.org/wp-content/uploads/2015/06/fsi-2015.xlsx",
    # 2014
    "https://fragilestatesindex.org/wp-content/uploads/2014/06/fsi-2014.xlsx",
    # 2013
    "https://fragilestatesindex.org/wp-content/uploads/2013/06/fsi-2013.xlsx",
]
# OWID no publica FSI
_OWID_FSI_URL = "https://ourworldindata.org/grapher/fragile-states-index.csv"
# CSV con datos históricos combinados (si existe manual)
_MANUAL_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "fsi_manual.csv"

_VEN_NAMES = {"Venezuela", "Venezuela, RB"}


def _try_owid_fsi() -> pd.DataFrame | None:
    """Intenta obtener FSI desde OWID grapher CSV."""
    try:
        from io import StringIO as _StringIO
        headers = {"User-Agent": "Mozilla/5.0 (research project)"}
        resp = requests.get(_OWID_FSI_URL, timeout=60, headers=headers)
        resp.raise_for_status()
        df = pd.read_csv(_StringIO(resp.text))
        entity_col = "Entity" if "Entity" in df.columns else df.columns[0]
        year_col   = "Year"   if "Year"   in df.columns else df.columns[1]
        score_col  = None
        for col in df.columns:
            if any(k in col.lower() for k in ["fragile", "fsi", "score", "index"]):
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
        if ven.empty:
            return None
        print(f"  OWID FSI: {len(ven)} anos para Venezuela")
        return ven
    except Exception as exc:
        print(f"  OWID FSI fallo: {exc}")
        return None


def _try_download_fsi_excel(url: str) -> pd.DataFrame | None:
    """Descarga el Excel FSI y extrae la fila de Venezuela."""
    try:
        print(f"  Descargando FSI desde {url.split('/')[-1]}...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, timeout=60, headers=headers)
        resp.raise_for_status()
        df_raw = pd.read_excel(BytesIO(resp.content), sheet_name=0, header=0)

        # Buscar columna de país
        country_col = None
        for col in df_raw.columns:
            if "country" in str(col).lower():
                country_col = col
                break
        if country_col is None:
            country_col = df_raw.columns[0]

        # Buscar fila Venezuela
        ven_mask = df_raw[country_col].astype(str).str.strip().isin(_VEN_NAMES)
        if not ven_mask.any():
            # Búsqueda parcial
            ven_mask = df_raw[country_col].astype(str).str.contains("Venezuela", case=False, na=False)

        if not ven_mask.any():
            print("  FSI Excel: Venezuela no encontrada en el archivo")
            return None

        ven_row = df_raw[ven_mask].iloc[0]

        # Buscar columna de Total Score o Year
        score_col = None
        year_from_file = None
        for col in df_raw.columns:
            col_str = str(col).lower()
            if "total" in col_str:
                score_col = col
                break
        # Si hay columna "Year" o "year" (solo si el valor está en rango razonable)
        for col in df_raw.columns:
            if "year" in str(col).lower():
                try:
                    candidate_yr = int(df_raw[col].iloc[0])
                    if 2000 <= candidate_yr <= 2030:
                        year_from_file = candidate_yr
                except (ValueError, TypeError):
                    pass

        if score_col is None:
            # Intentar la columna numérica más cercana al "Total"
            # El formato FSI suele tener la columna Total cerca del final
            numeric_cols = df_raw.select_dtypes(include="number").columns.tolist()
            if len(numeric_cols) > 0:
                score_col = numeric_cols[0]  # primera numérica (suele ser el total)

        if score_col is None:
            print("  FSI Excel: no se encontro columna de score")
            return None

        score = float(ven_row[score_col])
        # El año lo infiere del nombre del archivo si no está en el Excel
        if year_from_file is None:
            fname = url.split("/")[-1]
            for part in fname.split("-"):
                part_clean = part.split(".")[0]
                if part_clean.isdigit() and 2000 <= int(part_clean) <= 2030:
                    year_from_file = int(part_clean)
                    break

        if year_from_file is None:
            print("  FSI Excel: no se pudo determinar el año")
            return None

        print(f"  FSI {year_from_file}: Venezuela = {score:.1f}")
        return pd.DataFrame([{"año": year_from_file, "valor": score}])

    except Exception as exc:
        print(f"  FSI descarga fallo: {exc}")
        return None


def _try_manual_csv() -> pd.DataFrame | None:
    """Lee CSV manual con histórico FSI Venezuela."""
    if not _MANUAL_CSV.exists():
        return None
    try:
        df = pd.read_csv(_MANUAL_CSV)
        year_col  = "year" if "year" in df.columns else "año"
        score_col = "total" if "total" in df.columns else (
                    "score" if "score" in df.columns else df.columns[1])
        df = df[[year_col, score_col]].rename(
            columns={year_col: "año", score_col: "valor"}
        )
        df = df.dropna(subset=["valor"])
        df["año"] = df["año"].astype(int)
        df = df[(df["año"] >= START) & (df["año"] <= END)]
        print(f"  Manual CSV: {len(df)} años cargados")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  Manual CSV error: {exc}")
        return None


def fetch_fragile_states() -> pd.DataFrame:
    """
    Descarga Fragile States Index para Venezuela.
    Sin fallbacks inventados — NaN si no hay datos reales.
    """
    # Intentar OWID primero (serie histórica), luego Excels individuales, luego manual
    df_owid = _try_owid_fsi()
    if df_owid is not None and not df_owid.empty:
        df_manual = None
        df_latest = None
    else:
        df_manual = _try_manual_csv()
        # Intentar TODOS los URLs de Excel para recopilar todos los años disponibles
        # (no romper al primer éxito — cada Excel tiene un año diferente)
        excel_frames = []
        for url in _FSI_URLS:
            df_yr = _try_download_fsi_excel(url)
            if df_yr is not None and not df_yr.empty:
                excel_frames.append(df_yr)
        df_latest = (
            pd.concat(excel_frames).drop_duplicates(subset=["año"])
            if excel_frames else None
        )

    if df_owid is None and df_manual is None and df_latest is None:
        print(
            "\n  ADVERTENCIA: Fragile States Index no disponible automaticamente.\n"
            "  Para datos completos: descargar histórico desde fragilestatesindex.org/data/\n"
            "  y guardar en data/raw/fsi_manual.csv con columnas: year | total\n"
            "  Variable fragile_states_index quedara NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    # Combinar fuentes: OWID (series) + manual + dato más reciente
    frames = [f for f in [df_owid, df_manual, df_latest] if f is not None and not f.empty]
    df_vals = pd.concat(frames).drop_duplicates(subset=["año"]).sort_values("año")

    rows = []
    for _, row in df_vals.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "fragile_states_index",
            "valor":     round(float(row["valor"]), 2),
            "pais":      "Venezuela",
            "fuente":    (
                "Fund for Peace — Fragile States Index. "
                "https://fragilestatesindex.org/data/"
            ),
        })

    df = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 65)
    print("  Fragile States Index — Venezuela")
    print("  Fuente: Fund for Peace (fragilestatesindex.org)")
    print("=" * 65)
    settings.paths.ensure_exists()

    df = fetch_fragile_states()

    if df.empty:
        print("\n  0 anos disponibles. fragile_states.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
