"""
RSF — Reporters Without Borders Press Freedom Index — Venezuela.

Fuente: Reporters Without Borders (RSF)
        https://rsf.org/en/index

Variable: RSF Press Freedom Score (0-100, mayor = más libre).

NOTA DE METODOLOGÍA — CAMBIO DE ESCALA EN 2022:
  Pre-2022 (OWID press-freedom-rsf.csv): datos en "violations score" donde
    MAYOR valor = MÁS violaciones = MENOS libertad de prensa.
    (Ejemplo: Norway 2021 = 6.72; Venezuela 2021 = 47.60)
    Para compatibilidad con direction=POSITIVE en el pipeline, el script
    INVIERTE estos valores: new_value = 100 - old_value
    (Venezuela 2021 invertido: 100 - 47.60 = 52.40)

  Post-2022 (nueva metodología RSF): datos en "press freedom score" donde
    MAYOR valor = MÁS libertad de prensa (compatible con direction=POSITIVE).
    (Ejemplo: Venezuela 2022 = 37.78; Venezuela 2025 = 29.21)

  Los valores verificados 2022-2025 están en _VERIFIED_NEW_DATA y SIEMPRE
  se añaden/reemplazan sobre el dato OWID para esos años.

Cobertura: 2013-2025 (OWID para 2013-2021, verificado para 2022-2025)

Cita: Reporters Without Borders. (2025). World Press Freedom Index 2025.
      https://rsf.org/en/index
      Statista/RSF. Venezuela press freedom index 2015-2025.
      https://www.statista.com/statistics/955803/press-freedom-index-venezuela/

Salida: data/raw/rsf.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_rsf.py
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
OUTPUT = settings.paths.raw_rsf

# OWID grapher CSV endpoint — datos históricos RSF (probar múltiples slugs)
_OWID_RSF_URLS = [
    "https://ourworldindata.org/grapher/rsf-press-freedom-index.csv",
    "https://ourworldindata.org/grapher/press-freedom-index.csv",
    "https://ourworldindata.org/grapher/press-freedom-rsf.csv",
    "https://ourworldindata.org/grapher/freedom-of-press-index-rsf.csv",
    "https://ourworldindata.org/grapher/press-freedom-score.csv",
]
# RSF publica JSON/CSV desde su API (acceso público, sin auth)
_RSF_API_URL = "https://rsf.org/api/news?zone=1&category=1&slug=index&lang=EN"
# RSF datos directos por año vía endpoint de datos
_RSF_DATA_URLS = [
    "https://rsf.org/sites/default/files/rsf_index_2024.csv",
    "https://rsf.org/sites/default/files/rsf_index_2023.csv",
]
_MANUAL_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "rsf_manual.csv"
_VEN_NAMES  = {"Venezuela", "Venezuela, RB", "ven", "VEN"}

# ─────────────────────────────────────────────────────────────────────────────
# DATOS HISTÓRICOS — Pre-2022 (metodología antigua, invertidos a escala nueva)
# Fuente: OWID press-freedom-rsf.csv — "violations score" (mayor=menos libre)
# Inversión: 100 - violations_score → escala comparable con nueva metodología
#   Original OWID: Norway 2021=6.72 (más libre), Venezuela 2021=47.60 (menos libre)
#   Invertido:     Norway=93.28, Venezuela=52.40
# ─────────────────────────────────────────────────────────────────────────────
_VERIFIED_OLD_DATA: dict[int, tuple[float, str]] = {
    2013: (65.56, "RSF/OWID press-freedom-rsf.csv pre-2022 — violations_score=34.44 invertido (100-34.44=65.56). Reporters Without Borders World Press Freedom Index."),
    2014: (64.63, "RSF/OWID press-freedom-rsf.csv pre-2022 — violations_score=35.37 invertido (100-35.37=64.63). Reporters Without Borders World Press Freedom Index."),
    2015: (59.39, "RSF/OWID press-freedom-rsf.csv pre-2022 — violations_score=40.61 invertido (100-40.61=59.39). Reporters Without Borders World Press Freedom Index."),
    2016: (55.23, "RSF/OWID press-freedom-rsf.csv pre-2022 — violations_score=44.77 invertido (100-44.77=55.23). Reporters Without Borders World Press Freedom Index."),
    2017: (57.06, "RSF/OWID press-freedom-rsf.csv pre-2022 — violations_score=42.94 invertido (100-42.94=57.06). Reporters Without Borders World Press Freedom Index."),
    2018: (53.97, "RSF/OWID press-freedom-rsf.csv pre-2022 — violations_score=46.03 invertido (100-46.03=53.97). Reporters Without Borders World Press Freedom Index."),
    2019: (50.90, "RSF/OWID press-freedom-rsf.csv pre-2022 — violations_score=49.10 invertido (100-49.10=50.90). Reporters Without Borders World Press Freedom Index."),
    2020: (54.34, "RSF/OWID press-freedom-rsf.csv pre-2022 — violations_score=45.66 invertido (100-45.66=54.34). Reporters Without Borders World Press Freedom Index."),
    2021: (52.40, "RSF/OWID press-freedom-rsf.csv pre-2022 — violations_score=47.60 invertido (100-47.60=52.40). Reporters Without Borders World Press Freedom Index."),
}

# ─────────────────────────────────────────────────────────────────────────────
# DATOS VERIFICADOS — Nueva metodología RSF 2022+ (0-100, mayor = más libre)
# Fuente: Statista / RSF World Press Freedom Index (nueva escala post-2022)
#   https://www.statista.com/statistics/955803/press-freedom-index-venezuela/
# ESTOS VALORES REEMPLAZAN/COMPLEMENTAN el dato OWID para años >= 2022.
# ─────────────────────────────────────────────────────────────────────────────
_VERIFIED_NEW_DATA: dict[int, tuple[float, str]] = {
    2022: (37.78, "RSF World Press Freedom Index 2022 (nueva metodologia 0-100, mayor=mas libre). https://www.statista.com/statistics/955803/press-freedom-index-venezuela/"),
    2023: (36.99, "RSF World Press Freedom Index 2023 (nueva metodologia 0-100, mayor=mas libre). https://www.statista.com/statistics/955803/press-freedom-index-venezuela/"),
    2024: (33.06, "RSF World Press Freedom Index 2024 (nueva metodologia 0-100, mayor=mas libre). https://www.statista.com/statistics/955803/press-freedom-index-venezuela/"),
    2025: (29.21, "RSF World Press Freedom Index 2025 (nueva metodologia 0-100, mayor=mas libre). https://www.statista.com/statistics/955803/press-freedom-index-venezuela/"),
}


def _try_owid_rsf(url: str) -> pd.DataFrame | None:
    """Intenta obtener RSF desde OWID grapher CSV."""
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
            if "score" in cl or "press" in cl or "freedom" in cl or "rsf" in cl:
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

        # Normalizar: si los valores son rankings (1-180) convertir a score 0-100
        max_val = ven["valor"].max()
        if max_val > 100:
            # Es un ranking: invertir (180=peor → 0; 1=mejor → 100)
            ven["valor"] = round((180 - ven["valor"]) / 179 * 100, 2)
            print("  RSF: valores convertidos de ranking a score 0-100")
        else:
            # Datos OWID pre-2022: "violations score" (mayor = peor).
            # Invertir a escala compatible con nueva metodología RSF (mayor = más libre).
            ven["valor"] = round(100.0 - ven["valor"], 2)
            print("  RSF OWID (pre-2022): violations score invertido 100-x (compatible con nueva escala)")

        ven = ven[(ven["año"] >= START) & (ven["año"] <= END)]
        print(f"  OWID RSF ({url.split('/')[-1]}): {len(ven)} anos para Venezuela")
        return ven if not ven.empty else None
    except Exception as exc:
        print(f"  OWID RSF fallo ({url.split('/')[-1]}): {exc}")
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
        print(f"  Manual CSV RSF: {len(df)} anos")
        return df if not df.empty else None
    except Exception as exc:
        print(f"  Manual CSV error: {exc}")
        return None


def fetch_rsf() -> pd.DataFrame:
    """Descarga RSF Press Freedom Index Venezuela.

    Estrategia:
    1. Usar _VERIFIED_OLD_DATA (2013-2021, inversión de escala OWID verificada)
    2. Intentar OWID para enriquecer/actualizar datos pre-2022
    3. Sobreescribir con _VERIFIED_NEW_DATA (2022-2025, nueva metodología)
    4. rsf_manual.csv como fallback adicional
    """
    rows_by_year: dict[int, dict] = {}

    # --- Paso 1: Datos históricos verificados (pre-2022) ---
    for yr, (score, fuente) in _VERIFIED_OLD_DATA.items():
        if START <= yr <= END:
            rows_by_year[yr] = {
                "año": yr, "indicador": "rsf_press_freedom",
                "valor": score, "pais": "Venezuela", "fuente": fuente,
            }

    # --- Paso 2: Intentar OWID para enriquecer (si URL funciona) ---
    for url in _OWID_RSF_URLS:
        df_owid = _try_owid_rsf(url)
        if df_owid is not None and not df_owid.empty:
            for _, row in df_owid.iterrows():
                yr = int(row["año"])
                if yr < 2022 and START <= yr <= END:  # Solo usar para años pre-2022
                    rows_by_year[yr] = {
                        "año": yr, "indicador": "rsf_press_freedom",
                        "valor": round(float(row["valor"]), 2),
                        "pais": "Venezuela",
                        "fuente": (
                            "RSF/OWID press-freedom-rsf.csv (pre-2022, "
                            "violations_score invertido 100-x). "
                            "https://ourworldindata.org/grapher/press-freedom-rsf.csv"
                        ),
                    }
            break

    # --- Paso 3: Datos verificados nueva metodología 2022+ (siempre aplican) ---
    for yr, (score, fuente) in _VERIFIED_NEW_DATA.items():
        if START <= yr <= END:
            rows_by_year[yr] = {
                "año": yr, "indicador": "rsf_press_freedom",
                "valor": score, "pais": "Venezuela", "fuente": fuente,
            }

    # --- Paso 4: rsf_manual.csv como fallback adicional ---
    df_manual = _try_manual_csv()
    if df_manual is not None:
        for _, row in df_manual.iterrows():
            yr = int(row["año"])
            if yr not in rows_by_year and START <= yr <= END:
                rows_by_year[yr] = {
                    "año": yr, "indicador": "rsf_press_freedom",
                    "valor": round(float(row["valor"]), 2),
                    "pais": "Venezuela",
                    "fuente": "rsf_manual.csv (datos manuales verificados)",
                }

    if not rows_by_year:
        print(
            "\n  ADVERTENCIA: RSF Press Freedom no disponible.\n"
            "  Guardar en data/raw/rsf_manual.csv con columnas: year | score\n"
            "  Variable rsf_press_freedom quedara NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    df_result = pd.DataFrame(list(rows_by_year.values()))
    n_verified = sum(1 for yr in rows_by_year if yr in _VERIFIED_NEW_DATA)
    n_old = sum(1 for yr in rows_by_year if yr in _VERIFIED_OLD_DATA)
    print(f"  RSF total: {len(df_result)} años ({n_old} histórico pre-2022 + {n_verified} nueva metodología 2022+)")
    return df_result.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 65)
    print("  RSF Press Freedom Index — Venezuela")
    print("  Fuente: Reporters Without Borders (rsf.org)")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_rsf()
    if df.empty:
        print("\n  0 anos. rsf.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
