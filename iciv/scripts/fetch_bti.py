"""
BTI — Bertelsmann Transformation Index — Venezuela.

Fuente: Bertelsmann Stiftung
        https://bti-project.org/en/index/ranking

Variable: BTI Governance Index (1-10, mayor = mejor gobernanza).
  Mide la calidad de gobernanza política: capacidad de dirección, eficiencia
  de recursos, consenso, cooperación internacional.

Cobertura: 2006-2024 (bienal — solo años pares)
  Venezuela: de 4.5 (2006) a 1.8 (2024) — declive sostenido.

Acceso: BTI publica datos en Excel descargable sin registro.
  URL directa disponible para la edición 2024.

Salida: data/raw/bti.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_bti.py
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
OUTPUT = settings.paths.raw_bti

# URL directa al Excel BTI 2026 (todos los países, histórico)
_BTI_EXCEL_2026 = "https://bti-project.org/fileadmin/api/content/en/downloads/data/BTI_2006-2026_Scores.xlsx"
# Fallback: BTI 2024
_BTI_EXCEL_2024 = "https://bti-project.org/fileadmin/api/content/en/downloads/data/BTI_2006-2024_Scores.xlsx"
# Fallback URL alternativa BTI 2022
_BTI_EXCEL_ALT  = "https://bti-project.org/fileadmin/api/content/en/downloads/data/BTI_2006-2022_Scores.xlsx"
_MANUAL_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "bti_manual.csv"
_VEN_NAMES  = {"Venezuela", "Venezuela, RB"}


def _extract_governance_score(df_sheet: pd.DataFrame) -> float | None:
    """
    Extrae el Governance Index de Venezuela de una hoja BTI.
    La hoja tiene: country col, region col, luego indicadores en columnas.
    Busca la columna que contiene "Governance" (no Democracy Status).
    """
    country_col = df_sheet.columns[0]
    ven_mask = df_sheet[country_col].astype(str).str.contains("Venezuela", case=False, na=False)
    if not ven_mask.any():
        return None
    ven_row = df_sheet[ven_mask].iloc[0]

    # Buscar columna de Governance Index — por orden de especificidad
    gov_col = None
    # Patrón BTI: "  G | Governance Index" (con espacios al principio)
    # Buscar primero coincidencias exactas, luego parciales
    gov_priorities = [
        "g | governance index",     # columna principal BTI
        "governance index",          # sin prefijo
        " g | governance",           # variante con espacio
        "gii | governance performance",  # sub-índice alternativo
    ]
    for pat in gov_priorities:
        for col in df_sheet.columns:
            # Verificar que sea un match limpio (no "ranking governance")
            col_l = str(col).lower()
            if pat in col_l and "ranking" not in col_l and "trend" not in col_l and ".1" not in str(col):
                gov_col = col
                break
        if gov_col:
            break

    if gov_col is None:
        return None

    try:
        val = float(ven_row[gov_col])
        return val if pd.notna(val) else None
    except (ValueError, TypeError):
        return None


def _try_bti_excel(url: str) -> pd.DataFrame | None:
    """
    Descarga el Excel BTI histórico.
    Estructura real: cada hoja = un año (BTI 2024, BTI 2022, ...)
    Cada hoja tiene: países en filas, indicadores BTI en columnas.
    """
    try:
        print(f"  Descargando BTI desde {url.split('/')[-1]}...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, timeout=90, headers=headers)
        resp.raise_for_status()

        xls     = pd.ExcelFile(BytesIO(resp.content))
        rows    = []

        for sh in xls.sheet_names:
            # Inferir año del nombre de hoja: "BTI 2024" → 2024
            yr = None
            for token in str(sh).split():
                try:
                    candidate = int(token)
                    if 2000 <= candidate <= 2030:
                        yr = candidate
                        break
                except ValueError:
                    pass

            if yr is None or not (START <= yr <= END):
                continue

            try:
                df_sh = pd.read_excel(BytesIO(resp.content), sheet_name=sh, header=0)
            except Exception:
                continue

            val = _extract_governance_score(df_sh)

            if val is not None:
                print(f"  BTI {yr}: Venezuela Governance = {val:.2f}")
                rows.append({"año": yr, "valor": val})

        if not rows:
            print(f"  BTI: ninguna hoja produjo datos para Venezuela")
            print(f"  BTI: hojas disponibles: {xls.sheet_names[:8]}")
            return None

        print(f"  BTI Excel: {len(rows)} anos para Venezuela (bienal)")
        return pd.DataFrame(rows)

    except Exception as exc:
        print(f"  BTI Excel fallo: {exc}")
        return None


def _try_manual_csv() -> pd.DataFrame | None:
    if not _MANUAL_CSV.exists():
        return None
    try:
        df = pd.read_csv(_MANUAL_CSV)
        year_col  = "year" if "year" in df.columns else "año"
        score_col = "governance" if "governance" in df.columns else (
                    "score" if "score" in df.columns else df.columns[1])
        df = df[[year_col, score_col]].rename(
            columns={year_col: "año", score_col: "valor"}
        ).dropna(subset=["valor"])
        df["año"] = df["año"].astype(int)
        df = df[(df["año"] >= START) & (df["año"] <= END)]
        print(f"  Manual CSV BTI: {len(df)} anos")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  Manual CSV error: {exc}")
        return None


def fetch_bti() -> pd.DataFrame:
    """Descarga BTI Governance Index Venezuela. Sin datos inventados."""
    df_vals = None
    for attempt in [
        lambda: _try_bti_excel(_BTI_EXCEL_2026),
        lambda: _try_bti_excel(_BTI_EXCEL_2024),
        lambda: _try_bti_excel(_BTI_EXCEL_ALT),
        _try_manual_csv,
    ]:
        candidate = attempt()
        if candidate is not None and not candidate.empty:
            df_vals = candidate
            break

    if df_vals is None or df_vals.empty:
        print(
            "\n  ADVERTENCIA: BTI no disponible automaticamente.\n"
            "  Descargar desde bti-project.org/en/index/ranking (Downloads)\n"
            "  Guardar en data/raw/bti_manual.csv con columnas: year | governance\n"
            "  Variable bti_governance_index quedara NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    rows = []
    for _, row in df_vals.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "bti_governance_index",
            "valor":     round(float(row["valor"]), 2),
            "pais":      "Venezuela",
            "fuente":    (
                "Bertelsmann Stiftung — BTI Governance Index. "
                "https://bti-project.org/en/index/ranking"
            ),
        })

    return pd.DataFrame(rows).sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 65)
    print("  BTI Governance Index — Venezuela (bienal 2006-2024)")
    print("  Fuente: Bertelsmann Transformation Index")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_bti()
    if df.empty:
        print("\n  0 anos. bti.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
