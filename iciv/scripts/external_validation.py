"""Exploratory retrospective association checks for the public AHP index.

Reports levels and first annual differences, exact sample years, ordinary
correlations and HAC uncertainty for an OLS association slope. Leave-one-out
removes direct reuse of the contrasted component, but does not establish source
independence, causal validity, predictive performance or construct validity.
No observations are imputed. HAC estimates have substantial small-sample limits.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

_ICIV_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ICIV_DIR / "src"))
from iciv.index.aggregator import ICIVAggregator
from iciv.index.dimensions import DIMENSIONS
from iciv.index.weighting.ahp_weights import AHPWeights

PROCESSED = _ICIV_DIR / "data" / "processed"
RAW = _ICIV_DIR / "data" / "raw"


def _load_raw_series(csv_path: Path, indicador: str) -> pd.Series:
    df = pd.read_csv(csv_path)
    df = df.loc[df["indicador"] == indicador]
    if df["año"].duplicated().any():
        raise ValueError(f"Años duplicados para {indicador}: {csv_path}")
    return df.set_index("año")["valor"].astype(float).sort_index()


def _public_score(df_norm: pd.DataFrame) -> pd.Series:
    # Same weights and 50% dimension coverage floor as the public model.
    return ICIVAggregator(method="linear", strategy=AHPWeights()).compute(df_norm).set_index("año")["iciv_score"]


def _iciv_without_dimension(df_norm: pd.DataFrame, dim_id: str) -> pd.Series:
    df_loo = df_norm.copy()
    target = next(d for d_id, d in DIMENSIONS.items() if d_id.value == dim_id)
    for v in target.variables:
        df_loo[v.column] = np.nan
    return _public_score(df_loo)


def _iciv_without(df_norm: pd.DataFrame, exclude_col: str) -> pd.Series:
    df_loo = df_norm.copy()
    df_loo[exclude_col] = np.nan
    return _public_score(df_loo)


def _correlate(a: pd.Series, b: pd.Series, representation: str = "niveles") -> dict:
    """Annual complete pairs; differences never bridge missing years.

    Pearson/Spearman p-values assume independent pairs and are descriptive.
    Newey-West HAC is applied only to a consecutive annual estimation sample.
    HAC adjusts autocorrelation/heteroskedasticity, not spurious trends or causal
    confounding. Report first differences alongside levels for that reason.
    """
    joined = pd.concat([a, b], axis=1, keys=["x", "y"]).sort_index()
    joined = joined.replace([np.inf, -np.inf], np.nan)
    if joined.index.duplicated().any():
        raise ValueError("La validación requiere un registro por año")
    if representation == "primeras_diferencias":
        if not joined.empty:
            joined = joined.reindex(range(int(joined.index.min()), int(joined.index.max()) + 1)).diff()
    elif representation != "niveles":
        raise ValueError(f"Representación desconocida: {representation}")
    joined = joined.dropna()
    n = len(joined)
    result = {
        "representacion": representation, "n": n,
        "years": f"{joined.index.min()}-{joined.index.max()}" if n else "",
        "years_exact": json.dumps([int(y) for y in joined.index]),
        "pearson_r": np.nan, "pearson_p": np.nan,
        "spearman_rho": np.nan, "spearman_p": np.nan,
        "hac_slope": np.nan, "hac_ci95_low": np.nan, "hac_ci95_high": np.nan,
        "hac_p": np.nan, "hac_maxlags": np.nan,
        "hac_status": "muestra insuficiente o constante",
    }
    if n < 5 or joined.x.nunique() < 2 or joined.y.nunique() < 2:
        return result
    pr, pp = stats.pearsonr(joined.x, joined.y)
    sr, sp = stats.spearmanr(joined.x, joined.y)
    result.update(pearson_r=float(pr), pearson_p=float(pp), spearman_rho=float(sr), spearman_p=float(sp))
    if not np.all(np.diff(joined.index.to_numpy(dtype=int)) == 1):
        result["hac_status"] = "no estimado: años no consecutivos"
        return result
    lags = min(n - 2, max(1, int(np.floor(4 * (n / 100) ** (2 / 9)))))
    fit = sm.OLS(joined.y, sm.add_constant(joined.x)).fit(
        cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": True}, use_t=True
    )
    ci = fit.conf_int().loc["x"]
    result.update(hac_slope=float(fit.params["x"]), hac_ci95_low=float(ci.iloc[0]),
                  hac_ci95_high=float(ci.iloc[1]), hac_p=float(fit.pvalues["x"]),
                  hac_maxlags=lags, hac_status="estimado; aproximación de muestra pequeña")
    return result


def _verdict(row: pd.Series) -> str:
    if row["hipotesis"] == "no interpretable":
        return "descriptivo; transición de sensor impide interpretación homogénea"
    r = row["pearson_r"]
    if pd.isna(r):
        return "datos insuficientes o serie constante"
    sign_ok = r < 0 if row["hipotesis"] == "negativa" else r > 0
    if not sign_ok:
        return "asociación con signo contrario al esperado; exploratoria"
    if pd.notna(row.get("hac_p_holm")) and row["hac_p_holm"] < .05:
        return "asociación compatible con signo esperado (HAC + Holm); exploratoria"
    return "signo esperado; evidencia no concluyente con HAC + Holm"


def main() -> None:
    df_norm = pd.read_csv(PROCESSED / "iciv_normalizado.csv")
    iciv_full = _public_score(df_norm)
    migrantes = _load_raw_series(RAW / "unhcr.csv", "migrantes_vzla_millones")
    luminosidad = _load_raw_series(RAW / "viirs.csv", "luminosidad_nocturna_idx")
    wdi = pd.read_csv(RAW / "wdi.csv")
    ied = wdi.set_index("año")["ied_neta_usd"].astype(float) if "ied_neta_usd" in wdi else None
    iciv_sin_migr = _iciv_without(df_norm, "migrantes_vzla_millones")
    iciv_sin_lumi = _iciv_without(df_norm, "luminosidad_nocturna_idx")
    tests = []

    def add(test, description, hypothesis, method, a, b):
        for representation in ("niveles", "primeras_diferencias"):
            tests.append({"test": test, "descripcion": description, "hipotesis": hypothesis,
                          "metodo": method, "modelo": "AHP público; piso dimensional 50%",
                          "alcance": "asociación retrospectiva exploratoria; sin inferencia causal o predictiva",
                          **_correlate(a, b, representation)})

    add("ICIV_loo_vs_migracion_UNHCR", "ICIV sin migrantes vs stock UNHCR (millones)",
        "negativa", "leave-one-out", iciv_sin_migr, migrantes)
    add("ICIV_loo_vs_luminosidad_2000_2024", "ICIV sin luminosidad vs Li et al.; transición DMSP/VIIRS",
        "no interpretable", "descriptivo con ruptura de sensor", iciv_sin_lumi, luminosidad)
    add("ICIV_loo_vs_luminosidad_era_VIIRS", "ICIV sin luminosidad vs Li et al. desde 2014; origen VIIRS compartido con Black Marble",
        "positiva", "leave-one-out; proveedor distinto, sensor no independiente", iciv_sin_lumi.loc[2014:], luminosidad.loc[2014:])
    if ied is not None:
        add("ICIV_vs_IED_neta", "ICIV completo vs IED neta USD, excluida del índice",
            "positiva", "outcome externo exploratorio", iciv_full, ied)
    vdem_series = {}
    iciv_sin_d3 = None
    if (RAW / "vdem.csv").exists():
        iciv_sin_d3 = _iciv_without_dimension(df_norm, "D3_institucional")
        for indicator, hypothesis in [("vdem_libdem_index", "positiva"),
                                       ("vdem_rule_of_law", "positiva"),
                                       ("vdem_corrupcion_pol", "negativa")]:
            series = _load_raw_series(RAW / "vdem.csv", indicator)
            if series.empty:
                continue
            vdem_series[indicator] = series
            add(f"ICIV_completo_vs_{indicator}", f"ICIV vs {indicator}; solapamiento institucional",
                hypothesis, "convergencia exploratoria; solape declarado", iciv_full, series)
            add(f"ICIV_sinD3_vs_{indicator}", f"ICIV sin D3 vs {indicator}; tendencias y fuentes comunes siguen siendo posibles",
                hypothesis, "convergencia exploratoria sin D3", iciv_sin_d3, series)
    summary = pd.DataFrame(tests)
    summary["hac_p_holm"] = np.nan
    eligible = summary.hac_p.notna() & summary.hipotesis.ne("no interpretable")
    if eligible.any():
        summary.loc[eligible, "hac_p_holm"] = multipletests(summary.loc[eligible, "hac_p"], method="holm")[1]
    summary["veredicto"] = summary.apply(_verdict, axis=1)
    aligned = pd.DataFrame({"iciv_score": iciv_full, "iciv_sin_migrantes": iciv_sin_migr,
                            "iciv_sin_luminosidad": iciv_sin_lumi, "migrantes_vzla_millones": migrantes,
                            "luminosidad_nocturna_idx": luminosidad})
    if ied is not None:
        aligned["ied_neta_usd"] = ied
    if iciv_sin_d3 is not None:
        aligned["iciv_sin_D3_institucional"] = iciv_sin_d3
        for name, series in vdem_series.items():
            aligned[name] = series
    aligned.index.name = "año"
    PROCESSED.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(PROCESSED / "external_validation.csv")
    summary.to_csv(PROCESSED / "external_validation_summary.csv", index=False)
    print("\nVALIDACIÓN EXTERNA: ASOCIACIONES RETROSPECTIVAS EXPLORATORIAS\n")
    print(summary[["test", "representacion", "n", "pearson_r", "hac_p_holm", "veredicto"]].to_string(index=False))
    print("HAC no elimina tendencias espurias; muestras anuales pequeñas. Ver niveles y diferencias conjuntamente.")


if __name__ == "__main__":
    main()
