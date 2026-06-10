"""
Validación externa NO circular del ICIV (leave-one-out).

Problema que resuelve:
  La validación original correlacionaba ICIV vs IED, pero también existía la
  tentación de validar contra migración UNHCR o luminosidad VIIRS — ambas
  variables que están DENTRO del score (D4 y D2). Correlacionar el índice con
  un componente propio es circular.

Diseño leave-one-out:
  Para cada variable externa de validación se recalcula el ICIV completo
  EXCLUYENDO esa variable (el aggregator redistribuye su peso automáticamente
  al encontrar NaN). La correlación se mide entre:

    ICIV_sin_X  vs  serie cruda de X

  Hipótesis económicas (falsables):
    1. ICIV_sin_migrantes  vs migrantes UNHCR (stock, millones) → NEGATIVA
       (peor clima de inversión → más emigración)
    2. ICIV_sin_luminosidad vs luminosidad nocturna VIIRS/DMSP → POSITIVA
       (mejor clima → más actividad económica observable desde satélite)
    3. ICIV (completo)      vs IED neta (outcome externo, ya fuera del score)
       → POSITIVA (referencia exploratoria, no es leave-one-out porque la IED
       nunca formó parte del score)

Outputs:
  - data/processed/external_validation.csv        (series alineadas por año)
  - data/processed/external_validation_summary.csv (correlaciones + n + p-value)
  - stdout: resumen legible

Uso:
  cd iciv
  python scripts/external_validation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Permitir ejecución directa desde iciv/
_ICIV_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ICIV_DIR / "src"))

from iciv.index.aggregator import ICIVAggregator  # noqa: E402

PROCESSED = _ICIV_DIR / "data" / "processed"
RAW = _ICIV_DIR / "data" / "raw"


def _load_raw_series(csv_path: Path, indicador: str) -> pd.Series:
    """Carga una serie cruda año→valor desde un CSV largo (año,indicador,valor,...)."""
    df = pd.read_csv(csv_path)
    df = df[df["indicador"] == indicador]
    return df.set_index("año")["valor"].astype(float)


def _iciv_without(df_norm: pd.DataFrame, exclude_col: str) -> pd.Series:
    """Recalcula el ICIV excluyendo una variable (leave-one-out).

    El ICIVAggregator redistribuye el peso de la variable excluida entre las
    demás variables de su dimensión, de modo que el score resultante no
    contiene información directa de la variable de validación.
    """
    df_loo = df_norm.copy()
    df_loo[exclude_col] = np.nan
    scores = ICIVAggregator(method="linear").compute(df_loo)
    return scores.set_index("año")["iciv_score"]


def _correlate(a: pd.Series, b: pd.Series) -> dict:
    """Pearson y Spearman sobre la intersección de años con datos en ambas series."""
    joined = pd.concat([a, b], axis=1, keys=["x", "y"]).dropna()
    n = len(joined)
    if n < 5:
        return {"n": n, "pearson_r": np.nan, "pearson_p": np.nan,
                "spearman_rho": np.nan, "spearman_p": np.nan}
    pr, pp = stats.pearsonr(joined["x"], joined["y"])
    sr, sp = stats.spearmanr(joined["x"], joined["y"])
    return {"n": n, "pearson_r": round(pr, 4), "pearson_p": round(pp, 5),
            "spearman_rho": round(sr, 4), "spearman_p": round(sp, 5),
            "years": f"{joined.index.min()}-{joined.index.max()}"}


def main() -> None:
    df_norm = pd.read_csv(PROCESSED / "iciv_normalizado.csv")
    iciv_full = ICIVAggregator(method="linear").compute(df_norm).set_index("año")["iciv_score"]

    # Series crudas de validación (valores reales, NO normalizados)
    migrantes = _load_raw_series(RAW / "unhcr.csv", "migrantes_vzla_millones")
    luminosidad = _load_raw_series(RAW / "viirs.csv", "luminosidad_nocturna_idx")

    # IED: outcome externo ya excluido del score (referencia exploratoria)
    ied = None
    wdi = pd.read_csv(RAW / "wdi.csv")  # formato ancho: año × indicadores
    if "ied_neta_usd" in wdi.columns:
        ied = wdi.set_index("año")["ied_neta_usd"].astype(float)

    # Leave-one-out scores
    iciv_sin_migr = _iciv_without(df_norm, "migrantes_vzla_millones")
    iciv_sin_lumi = _iciv_without(df_norm, "luminosidad_nocturna_idx")

    tests = [
        {
            "test": "ICIV_loo_vs_migracion_UNHCR",
            "descripcion": "ICIV sin migrantes vs stock migrantes UNHCR (millones)",
            "hipotesis": "negativa",
            "metodo": "leave-one-out",
            **_correlate(iciv_sin_migr, migrantes),
        },
        {
            # Periodo completo 2000-2024: NO interpretable como validación.
            # La serie armonizada NTL combina sensores DMSP (hasta 2013) y VIIRS
            # (desde 2014) con un escalón de calibración en la transición, y el
            # tramo 2000-2013 refleja la expansión eléctrica del boom petrolero.
            # Se reporta por transparencia con veredicto "no interpretable".
            "test": "ICIV_loo_vs_luminosidad_2000_2024",
            "descripcion": "ICIV sin luminosidad vs luminosidad nocturna (periodo completo, confundido por transición de sensor DMSP a VIIRS)",
            "hipotesis": "no interpretable",
            "metodo": "leave-one-out (descartado: artefacto de sensor)",
            **_correlate(iciv_sin_lumi, luminosidad),
        },
        {
            # Test válido: solo era VIIRS (sensor homogéneo, 2014-2024), que
            # cubre además el periodo de colapso económico documentado.
            "test": "ICIV_loo_vs_luminosidad_era_VIIRS",
            "descripcion": "ICIV sin luminosidad vs luminosidad nocturna, solo era VIIRS 2014-2024 (sensor homogéneo)",
            "hipotesis": "positiva",
            "metodo": "leave-one-out",
            **_correlate(iciv_sin_lumi.loc[2014:], luminosidad.loc[2014:]),
        },
    ]
    if ied is not None:
        tests.append({
            "test": "ICIV_vs_IED_neta",
            "descripcion": "ICIV completo vs IED neta USD (outcome externo al score)",
            "hipotesis": "positiva",
            "metodo": "outcome externo (exploratorio)",
            **_correlate(iciv_full, ied),
        })

    summary = pd.DataFrame(tests)

    # Veredicto por test: hipótesis confirmada si el signo coincide y p<0.05
    def _verdict(row) -> str:
        r = row["pearson_r"]
        if row["hipotesis"] == "no interpretable":
            return "no interpretable (artefacto de sensor documentado)"
        if pd.isna(r):
            return "datos insuficientes"
        sign_ok = (r < 0) if row["hipotesis"] == "negativa" else (r > 0)
        sig = row["pearson_p"] < 0.05
        if sign_ok and sig:
            return "confirmada (p<0.05)"
        if sign_ok:
            return "signo correcto, no significativa"
        return "NO confirmada"

    summary["veredicto"] = summary.apply(_verdict, axis=1)

    # Dataset alineado para gráficos/auditoría
    aligned = pd.DataFrame({
        "iciv_score": iciv_full,
        "iciv_sin_migrantes": iciv_sin_migr,
        "iciv_sin_luminosidad": iciv_sin_lumi,
        "migrantes_vzla_millones": migrantes,
        "luminosidad_nocturna_idx": luminosidad,
    })
    if ied is not None:
        aligned["ied_neta_usd"] = ied
    aligned.index.name = "año"

    PROCESSED.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(PROCESSED / "external_validation.csv")
    summary.to_csv(PROCESSED / "external_validation_summary.csv", index=False)

    print("\n=== VALIDACIÓN EXTERNA NO CIRCULAR (leave-one-out) ===\n")
    for _, row in summary.iterrows():
        print(f"  {row['test']}")
        print(f"    {row['descripcion']}")
        print(f"    método: {row['metodo']} | años: {row.get('years', 'n/a')} | n={row['n']}")
        print(f"    Pearson r={row['pearson_r']} (p={row['pearson_p']}) | "
              f"Spearman rho={row['spearman_rho']} (p={row['spearman_p']})")
        print(f"    hipótesis ({row['hipotesis']}): {row['veredicto']}\n")
    print(f"  Outputs: {PROCESSED / 'external_validation.csv'}")
    print(f"           {PROCESSED / 'external_validation_summary.csv'}")


if __name__ == "__main__":
    main()
