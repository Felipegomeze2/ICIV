"""
Basel AML Index — Venezuela.

Fuente: Basel Institute on Governance
        https://baselgovernance.org/basel-aml-index

Variable: Riesgo de lavado de activos y financiamiento al terrorismo (0-10).
  Escala: mayor valor = mayor riesgo AML/CFT.
  Componentes: riesgo financiero, cohecho/corrupción, transparencia,
  estándares legales y políticos, supervisión.

Cobertura: 2012–2024 (anual). Venezuela consistentemente en el rango de
  "Alto Riesgo" (7.5–8.5/10) por deficiencias en el marco AML/CFT.
  FATF incluyó a Venezuela en lista gris 2021-2023.

Acceso: Basel Institute publica el índice como Excel descargable.
  URL de descarga del Excel histórico.
  Sin API — requiere descarga directa o CSV manual.

Salida: data/raw/basel_aml.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_basel_aml.py
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
OUTPUT = settings.paths.raw_basel_aml

# URLs directas al Excel histórico del Basel AML Index
# El Instituto Basel publica ediciones anuales desde 2012 — la URL cambia cada año
_BASEL_URLS = [
    # 2024 — varias variantes de URL que han sido usadas
    "https://baselgovernance.org/sites/default/files/2024-08/Basel_AML_Index_2024_Public_Edition_Scores.xlsx",
    "https://baselgovernance.org/sites/default/files/2024-08/Basel_AML_Index_2024_Public_Edition.xlsx",
    "https://baselgovernance.org/sites/default/files/2024-07/Basel_AML_Index_2024_Public_Edition_Scores.xlsx",
    # 2023
    "https://baselgovernance.org/sites/default/files/2023-08/Basel_AML_Index_2023_Public_Edition.xlsx",
    "https://baselgovernance.org/sites/default/files/2023-08/Basel_AML_Index_2023_Public_Edition_Scores.xlsx",
    # 2022
    "https://baselgovernance.org/sites/default/files/2022-08/Basel_AML_Index_2022_Public_Edition.xlsx",
    "https://baselgovernance.org/sites/default/files/2022-09/Basel_AML_Index_2022_Public_Edition.xlsx",
    # 2021
    "https://baselgovernance.org/sites/default/files/2021-09/Basel%20AML%20Index%202021%20Public%20Edition.xlsx",
]
_MANUAL_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "basel_aml_manual.csv"
_VEN_NAMES  = {"Venezuela", "Venezuela, RB", "Venezuela (Bolivarian Republic of)"}


def _try_basel_excel(url: str) -> pd.DataFrame | None:
    """Intenta descargar el Excel del Basel AML Index y extraer Venezuela."""
    try:
        print(f"  Probando Basel AML URL: {url.split('/')[-1]}")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, timeout=90, headers=headers)
        resp.raise_for_status()

        xls = pd.ExcelFile(BytesIO(resp.content))
        # Buscar la hoja con los scores
        sheet_name = None
        for sh in xls.sheet_names:
            sl = sh.lower()
            if "score" in sl or "result" in sl or "data" in sl or "index" in sl:
                sheet_name = sh
                break
        if sheet_name is None:
            sheet_name = xls.sheet_names[0]

        df = pd.read_excel(BytesIO(resp.content), sheet_name=sheet_name, header=0)

        # Buscar columna de país
        country_col = None
        for col in df.columns:
            cl = str(col).lower()
            if "country" in cl or "pais" in cl or "nation" in cl:
                country_col = col
                break
        if country_col is None:
            country_col = df.columns[0]

        # Filtrar Venezuela
        ven_mask = df[country_col].astype(str).str.contains("Venezuela", case=False, na=False)
        if not ven_mask.any():
            print(f"  Basel AML: Venezuela no encontrada en hoja '{sheet_name}'")
            return None

        ven_row = df[ven_mask].iloc[0]

        # El Excel puede tener formato ancho (columna por año) o largo (row per year)
        # Detectar columnas de año
        year_cols = {}
        for col in df.columns[1:]:
            try:
                yr = int(col)
                if 2010 <= yr <= 2030:
                    year_cols[yr] = col
            except (ValueError, TypeError):
                pass

        if year_cols:
            # Formato ancho: columnas = años
            rows = []
            for yr, col in sorted(year_cols.items()):
                if START <= yr <= END:
                    val = ven_row[col]
                    if pd.notna(val):
                        try:
                            rows.append({"año": yr, "valor": float(val)})
                        except (ValueError, TypeError):
                            pass
            if rows:
                print(f"  Basel AML Excel (ancho): {len(rows)} años para Venezuela")
                return pd.DataFrame(rows)

        # Intentar formato largo: buscar columnas 'year' y 'score'
        year_c = None
        score_c = None
        for col in df.columns:
            cl = str(col).lower()
            if "year" in cl and year_c is None:
                year_c = col
            if ("score" in cl or "value" in cl or "risk" in cl) and score_c is None:
                score_c = col

        if year_c and score_c:
            df_ven = df[ven_mask][[year_c, score_c]].copy()
            df_ven = df_ven.rename(columns={year_c: "año", score_c: "valor"})
            df_ven["año"] = pd.to_numeric(df_ven["año"], errors="coerce").astype("Int64")
            df_ven["valor"] = pd.to_numeric(df_ven["valor"], errors="coerce")
            df_ven = df_ven.dropna().copy()
            df_ven = df_ven[(df_ven["año"] >= START) & (df_ven["año"] <= END)]
            if not df_ven.empty:
                print(f"  Basel AML Excel (largo): {len(df_ven)} años para Venezuela")
                return df_ven

        print(f"  Basel AML Excel: estructura no reconocida en '{sheet_name}'")
        return None

    except Exception as exc:
        print(f"  Basel AML {url.split('/')[-1]} falló: {exc}")
        return None


def _try_manual_csv() -> pd.DataFrame | None:
    if not _MANUAL_CSV.exists():
        return None
    try:
        df = pd.read_csv(_MANUAL_CSV)
        year_col  = "year" if "year" in df.columns else "año"
        score_col = ("score" if "score" in df.columns
                     else "value" if "value" in df.columns
                     else "valor" if "valor" in df.columns
                     else df.columns[1])
        df = df[[year_col, score_col]].rename(
            columns={year_col: "año", score_col: "valor"}
        ).dropna(subset=["valor"])
        df["año"] = df["año"].astype(int)
        df = df[(df["año"] >= START) & (df["año"] <= END)]
        print(f"  Manual CSV Basel AML: {len(df)} años")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  Manual CSV error: {exc}")
        return None


def fetch_basel_aml() -> pd.DataFrame:
    """
    Descarga el Basel AML Index para Venezuela.
    Sin datos inventados.
    """
    print("  Consultando Basel AML Index para Venezuela...")

    df_vals = None
    for url in _BASEL_URLS:
        df_vals = _try_basel_excel(url)
        if df_vals is not None and not df_vals.empty:
            break

    if df_vals is None or df_vals.empty:
        df_vals = _try_manual_csv()

    if df_vals is None or df_vals.empty:
        print(
            "\n  ADVERTENCIA: Basel AML Index no disponible automaticamente.\n"
            "  Descargar desde: https://baselgovernance.org/basel-aml-index\n"
            "    -> Rankings -> Download Excel\n"
            "  Guardar en data/raw/basel_aml_manual.csv con columnas: year | score\n"
            "  (El score es 0-10, mayor = mas riesgo AML)\n"
            "  Variable basel_aml_index quedara NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    print(f"  Basel AML: {len(df_vals)} años para Venezuela (cobertura 2012+)")

    rows = []
    for _, row in df_vals.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "basel_aml_index",
            "valor":     round(float(row["valor"]), 2),
            "pais":      "Venezuela",
            "fuente":    (
                "Basel Institute on Governance — Basel AML Index "
                "(Anti-Money Laundering, 0-10 scale, higher = more risk). "
                "https://baselgovernance.org/basel-aml-index"
            ),
        })

    df = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 65)
    print("  Basel AML Index — Venezuela")
    print("  Fuente: Basel Institute on Governance")
    print("  Cobertura: 2012-2024")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_basel_aml()
    if df.empty:
        print("\n  0 años. basel_aml.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} años)")
        print(df[["año", "valor"]].to_string(index=False))
