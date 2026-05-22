"""
Validacion del modelo ICIV — Paso 7 de la metodologia.

Produce data/processed/iciv_validacion.html con 4 analisis:
  1. Sensibilidad de pesos AHP  (+/-5%, +/-10%, +/-20%)
  2. Correlacion ICIV vs IED    (Pearson + Spearman + scatter)
  3. Lineal vs Geometrico       (comparacion de metodos de agregacion)
  4. AHP vs PCA                 (comparacion de estrategias de ponderacion)

Uso:
    python scripts/validate_model.py
    python scripts/validate_model.py --no-open
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

# -- path setup ----------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT       = _SCRIPT_DIR.parent
sys.path.insert(0, str(_ROOT / "src"))

from iciv.config import Settings
from iciv.index.aggregator import ICIVAggregator
from iciv.index.dimensions import DIMENSIONS
from iciv.index.weighting.ahp_weights import AHPWeights
from iciv.index.weighting.fixed_weights import FixedWeights
from iciv.index.weighting.pca_weights import PCAWeights

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

settings = Settings()

DIM_COLS   = [d.value for d in DIMENSIONS]
DIM_NAMES  = {d.value: DIMENSIONS[d].name for d in DIMENSIONS}
DIM_COLORS = ["#3498db", "#e67e22", "#9b59b6", "#1abc9c", "#e74c3c", "#f39c12"]


# =============================================================================
# DATA LOADING
# =============================================================================

def _load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    norm_path = settings.paths.data_processed / "iciv_normalizado.csv"
    ahp_path  = settings.paths.data_processed / "iciv_scores_ahp.csv"

    if not norm_path.exists():
        raise FileNotFoundError(
            f"No encontrado: {norm_path}\n"
            "Ejecuta primero: python main.py --no-fetch"
        )
    if not ahp_path.exists():
        raise FileNotFoundError(
            f"No encontrado: {ahp_path}\n"
            "Ejecuta primero: python main.py --no-fetch"
        )

    df_norm = pd.read_csv(norm_path)
    df_ahp  = pd.read_csv(ahp_path)

    # Ensure año is int in both
    df_norm["año"] = df_norm["año"].astype(int)
    df_ahp["año"]  = df_ahp["año"].astype(int)

    return df_norm, df_ahp


# =============================================================================
# ANALISIS 1 — SENSIBILIDAD DE PESOS AHP
# =============================================================================

def _perturb_weights(
    base_weights: dict[str, float],
    target_dim: str,
    delta: float,
) -> dict[str, float]:
    """Perturba el peso de target_dim por delta y redistribuye el resto."""
    others = [k for k in base_weights if k != target_dim]
    new_w  = max(0.01, base_weights[target_dim] + delta)
    excess = (new_w - base_weights[target_dim])  # cuanto se robo a los demas

    new_weights = dict(base_weights)
    new_weights[target_dim] = new_w

    # Redistribuir proporcionalmente en los demas
    total_others = sum(base_weights[k] for k in others)
    for k in others:
        fraction = base_weights[k] / total_others if total_others > 0 else 1 / len(others)
        new_weights[k] = max(0.01, base_weights[k] - excess * fraction)

    # Renormalizar a 1.0
    total = sum(new_weights.values())
    return {k: v / total for k, v in new_weights.items()}


def _compute_iciv_with_weights(
    df_norm: pd.DataFrame,
    dim_weights: dict[str, float],
    method: str = "linear",
) -> pd.Series:
    """Calcula ICIV dado unos pesos de dimension y un metodo de agregacion."""

    class _CustomStrategy:
        """Wrapper para inyectar pesos de dimension arbitrarios."""
        def compute_weights(self, df):
            return dim_weights

        def get_method_name(self):
            return "custom"

        @property
        def dimension_result_(self):
            return {"weights": dim_weights}

    agg = ICIVAggregator(method=method, strategy=_CustomStrategy())
    result = agg.compute(df_norm)
    return result.set_index("año")["iciv_score"]


def run_sensitivity(
    df_norm: pd.DataFrame,
    base_ahp_weights: dict[str, float],
) -> dict:
    """
    Analisis de sensibilidad: perturbacion de +/-5%, +/-10%, +/-20%
    en cada peso de dimension por separado.

    Retorna:
        {
          "years":       [int, ...],
          "baseline":    [float, ...],
          "envelope_min": [float, ...],  # ICIV minimo en cualquier escenario
          "envelope_max": [float, ...],  # ICIV maximo en cualquier escenario
          "scenarios":   [{"label": str, "dim": str, "delta_pct": int,
                           "scores": [float, ...], "mean_delta": float}, ...],
          "stability":   {"mean_range": float, "max_range": float,
                          "sensitivity_index": float},
          "dim_impact":  {dim: float, ...},  # variacion media al perturbar esa dim
        }
    """
    logger.info("  [1/4] Sensibilidad de pesos AHP...")

    baseline_series = _compute_iciv_with_weights(df_norm, base_ahp_weights)
    years    = baseline_series.index.tolist()
    baseline = baseline_series.tolist()

    deltas_pct = [-20, -10, -5, 5, 10, 20]
    scenarios  = []

    for dim in DIM_COLS:
        for d_pct in deltas_pct:
            delta_abs  = base_ahp_weights.get(dim, 0) * (d_pct / 100)
            new_w      = _perturb_weights(base_ahp_weights, dim, delta_abs)
            scores_s   = _compute_iciv_with_weights(df_norm, new_w)
            scores_s   = scores_s.reindex(years)
            scores_lst = [round(float(v), 2) if not pd.isna(v) else None
                          for v in scores_s]
            mean_delta = float(np.nanmean([
                (s - b) for s, b in zip(scores_s, baseline)
                if s is not None
            ]))
            scenarios.append({
                "label":      f"{DIM_NAMES.get(dim, dim)} {'+' if d_pct>0 else ''}{d_pct}%",
                "dim":        dim,
                "delta_pct":  d_pct,
                "scores":     scores_lst,
                "mean_delta": round(mean_delta, 3),
            })

    # Envelope (min/max en todos los escenarios por anio)
    all_matrices = [sc["scores"] for sc in scenarios]
    envelope_min = []
    envelope_max = []
    for i in range(len(years)):
        vals = [m[i] for m in all_matrices if m[i] is not None]
        vals.append(baseline[i])
        envelope_min.append(round(min(vals), 2))
        envelope_max.append(round(max(vals), 2))

    ranges = [hi - lo for hi, lo in zip(envelope_max, envelope_min)]
    mean_range  = round(float(np.mean(ranges)), 2)
    max_range   = round(float(np.max(ranges)), 2)
    si = round(mean_range / float(np.mean([b for b in baseline if b is not None])), 4)

    # Impacto por dimension
    dim_impact = {}
    for dim in DIM_COLS:
        dim_scenarios = [sc for sc in scenarios if sc["dim"] == dim]
        impacts = [abs(sc["mean_delta"]) for sc in dim_scenarios]
        dim_impact[DIM_NAMES.get(dim, dim)] = round(float(np.mean(impacts)), 3)

    logger.info("      SI (Sensitivity Index) = %.4f  |  Rango medio = %.2f pts", si, mean_range)

    return {
        "years":         years,
        "baseline":      [round(b, 2) for b in baseline],
        "envelope_min":  envelope_min,
        "envelope_max":  envelope_max,
        "scenarios":     scenarios,
        "stability":     {
            "mean_range":         mean_range,
            "max_range":          max_range,
            "sensitivity_index":  si,
        },
        "dim_impact": dim_impact,
    }


# =============================================================================
# ANALISIS 2 — CORRELACION ICIV vs IED
# =============================================================================

def run_ied_correlation(
    df_norm: pd.DataFrame,
    df_ahp: pd.DataFrame,
) -> dict:
    """
    Calcula la correlacion entre el ICIV (AHP) y la IED normalizada.
    Usa Pearson, Spearman y genera datos para scatter + serie dual.
    """
    logger.info("  [2/4] Correlacion ICIV vs IED...")

    ied_col = "ied_neta_usd"
    if ied_col not in df_norm.columns:
        logger.warning("      IED no disponible en datos normalizados. Usando NaN.")
        return {"available": False}

    merged = df_ahp[["año", "iciv_score"]].merge(
        df_norm[["año", ied_col]], on="año", how="inner"
    ).dropna()

    if len(merged) < 5:
        logger.warning("      Muy pocos puntos para correlacion (%d). Omitiendo.", len(merged))
        return {"available": False, "n": len(merged)}

    iciv_vals = merged["iciv_score"].tolist()
    ied_vals  = merged[ied_col].tolist()
    years_cor = merged["año"].tolist()

    pearson_r, pearson_p   = scipy_stats.pearsonr(iciv_vals, ied_vals)
    spearman_r, spearman_p = scipy_stats.spearmanr(iciv_vals, ied_vals)

    # Linea de regresion para el scatter
    slope, intercept, *_ = scipy_stats.linregress(iciv_vals, ied_vals)
    x_line = [min(iciv_vals), max(iciv_vals)]
    y_line = [round(slope * x + intercept, 2) for x in x_line]

    logger.info(
        "      Pearson r=%.3f (p=%.4f)  |  Spearman rho=%.3f (p=%.4f)  |  n=%d",
        pearson_r, pearson_p, spearman_r, spearman_p, len(merged)
    )

    return {
        "available":   True,
        "n":           len(merged),
        "years":       years_cor,
        "iciv":        [round(v, 2) for v in iciv_vals],
        "ied":         [round(v, 2) for v in ied_vals],
        "pearson_r":   round(pearson_r, 4),
        "pearson_p":   round(pearson_p, 4),
        "spearman_r":  round(spearman_r, 4),
        "spearman_p":  round(spearman_p, 4),
        "reg_x":       [round(x, 2) for x in x_line],
        "reg_y":       y_line,
        "slope":       round(slope, 4),
        "intercept":   round(intercept, 4),
    }


# =============================================================================
# ANALISIS 3 — LINEAL vs GEOMETRICO
# =============================================================================

def run_method_comparison(
    df_norm: pd.DataFrame,
    base_ahp_weights: dict[str, float],
) -> dict:
    """
    Compara agregacion lineal vs geometrica usando los mismos pesos AHP.
    """
    logger.info("  [3/4] Lineal vs Geometrico...")

    lin_series  = _compute_iciv_with_weights(df_norm, base_ahp_weights, method="linear")
    geom_series = _compute_iciv_with_weights(df_norm, base_ahp_weights, method="geometric")

    years = sorted(set(lin_series.index) & set(geom_series.index))
    lin_vals  = [round(float(lin_series.loc[y]),  2) if not pd.isna(lin_series.loc[y])  else None for y in years]
    geom_vals = [round(float(geom_series.loc[y]), 2) if not pd.isna(geom_series.loc[y]) else None for y in years]
    deltas    = [round(g - l, 2) if (g is not None and l is not None) else None
                 for g, l in zip(geom_vals, lin_vals)]

    valid_lin  = [v for v in lin_vals  if v is not None]
    valid_geom = [v for v in geom_vals if v is not None]
    valid_d    = [v for v in deltas    if v is not None]

    mad = round(float(np.mean(np.abs(valid_d))), 3) if valid_d else 0.0
    corr_lg, _ = scipy_stats.pearsonr(valid_lin, valid_geom) if len(valid_lin) > 2 else (1.0, 1.0)

    logger.info(
        "      MAD lineal-geometrico = %.3f pts  |  correlacion = %.4f",
        mad, corr_lg
    )

    return {
        "years":      years,
        "linear":     lin_vals,
        "geometric":  geom_vals,
        "deltas":     deltas,
        "stats": {
            "mad":          mad,
            "corr":         round(corr_lg, 4),
            "mean_linear":  round(float(np.mean(valid_lin)),  2),
            "mean_geom":    round(float(np.mean(valid_geom)), 2),
            "max_abs_delta": round(float(np.max(np.abs(valid_d))), 2) if valid_d else 0.0,
        },
    }


# =============================================================================
# ANALISIS 4 — AHP vs PCA
# =============================================================================

def run_ahp_vs_pca(
    df_norm: pd.DataFrame,
    df_ahp_scores: pd.DataFrame,
    base_ahp_weights: dict[str, float],
) -> dict:
    """
    Compara pesos AHP vs pesos PCA a nivel de dimension.
    PCA se aplica sobre los puntajes de dimension del ICIV.
    """
    logger.info("  [4/4] AHP vs PCA...")

    # Columnas de dimension disponibles
    avail_dims = [c for c in DIM_COLS if c in df_ahp_scores.columns]

    # Filtrar dims que tienen al menos 5 valores no nulos
    avail_dims = [d for d in avail_dims
                  if df_ahp_scores[d].notna().sum() >= 5]

    if len(avail_dims) < 2:
        logger.warning("      Menos de 2 dimensiones con datos suficientes para PCA.")
        return {"available": False}

    dim_scores = df_ahp_scores[["año"] + avail_dims].copy()
    # Imputar NaN con la media de cada dimension (OCDE Handbook, Cap. 7)
    for d in avail_dims:
        dim_scores[d] = dim_scores[d].fillna(dim_scores[d].mean())

    # Filtrar años con todo NaN (año sin ningún dato)
    dim_scores = dim_scores.dropna(subset=avail_dims)

    if len(dim_scores) < 5:
        logger.warning("      Muy pocos datos completos para PCA (%d filas).", len(dim_scores))
        return {"available": False}

    pca = PCAWeights(exclude_cols=["año"])
    pca_var_weights = pca.compute_weights(dim_scores)  # pesos en espacio de dimensiones
    var_expl = pca.variance_explained_

    # Tomar solo columnas de dimension
    pca_dim_weights = {k: v for k, v in pca_var_weights.items() if k in avail_dims}
    total_pca = sum(pca_dim_weights.values())
    pca_dim_weights = {k: v / total_pca for k, v in pca_dim_weights.items()}

    # Calcular ICIV con pesos PCA
    pca_series = _compute_iciv_with_weights(df_norm, pca_dim_weights, method="linear")
    ahp_series = _compute_iciv_with_weights(df_norm, base_ahp_weights, method="linear")

    years = sorted(set(pca_series.index) & set(ahp_series.index))
    ahp_vals = [round(float(ahp_series.loc[y]), 2) if not pd.isna(ahp_series.loc[y]) else None for y in years]
    pca_vals = [round(float(pca_series.loc[y]), 2) if not pd.isna(pca_series.loc[y]) else None for y in years]

    valid_ahp = [v for v in ahp_vals if v is not None]
    valid_pca = [v for v in pca_vals if v is not None]
    deltas    = [round(p - a, 2) if (p and a) else None for p, a in zip(pca_vals, ahp_vals)]
    valid_d   = [v for v in deltas if v is not None]

    mad = round(float(np.mean(np.abs(valid_d))), 3) if valid_d else 0.0
    corr_ap, _ = scipy_stats.pearsonr(valid_ahp, valid_pca) if len(valid_ahp) > 2 else (1.0, 1.0)

    # Tabla de pesos
    weight_table = []
    for dim in avail_dims:
        weight_table.append({
            "dim":       DIM_NAMES.get(dim, dim),
            "ahp_w":     round(base_ahp_weights.get(dim, 0), 4),
            "pca_w":     round(pca_dim_weights.get(dim, 0), 4),
            "diff":      round(pca_dim_weights.get(dim, 0) - base_ahp_weights.get(dim, 0), 4),
        })

    logger.info(
        "      PC1 varianza = %.1f%%  |  MAD AHP-PCA = %.3f pts  |  correlacion = %.4f",
        var_expl * 100, mad, corr_ap
    )

    return {
        "available":       True,
        "variance_pc1":    round(var_expl * 100, 1),
        "years":           years,
        "ahp":             ahp_vals,
        "pca":             pca_vals,
        "deltas":          deltas,
        "weight_table":    weight_table,
        "stats": {
            "mad":          mad,
            "corr":         round(corr_ap, 4),
            "mean_ahp":     round(float(np.mean(valid_ahp)), 2),
            "mean_pca":     round(float(np.mean(valid_pca)), 2),
            "max_abs_delta": round(float(np.max(np.abs(valid_d))), 2) if valid_d else 0.0,
        },
    }


# =============================================================================
# REPORTE HTML
# =============================================================================

def _pval_label(p: float) -> str:
    if p < 0.001: return "p < 0.001 ***"
    if p < 0.01:  return "p < 0.01 **"
    if p < 0.05:  return "p < 0.05 *"
    return f"p = {p:.3f} (n.s.)"


def _corr_label(r: float) -> str:
    a = abs(r)
    if a >= 0.7: return "Fuerte"
    if a >= 0.4: return "Moderada"
    if a >= 0.2: return "Debil"
    return "Muy debil"


def _build_html(
    sens:    dict,
    corr:    dict,
    methods: dict,
    weights: dict,
    generated_at: str,
) -> str:

    # -- Serializar datos para JS -----------------------------------------
    # Sensibilidad
    s_years    = json.dumps(sens["years"])
    s_baseline = json.dumps(sens["baseline"])
    s_env_min  = json.dumps(sens["envelope_min"])
    s_env_max  = json.dumps(sens["envelope_max"])
    s_si       = sens["stability"]["sensitivity_index"]
    s_mr       = sens["stability"]["mean_range"]
    s_maxr     = sens["stability"]["max_range"]

    # Impacto por dimension (bar chart)
    dim_impact_labels = json.dumps(list(sens["dim_impact"].keys()))
    dim_impact_vals   = json.dumps(list(sens["dim_impact"].values()))

    # Correlacion
    corr_available = corr.get("available", False)
    if corr_available:
        c_years    = json.dumps(corr["years"])
        c_iciv     = json.dumps(corr["iciv"])
        c_ied      = json.dumps(corr["ied"])
        c_reg_x    = json.dumps(corr["reg_x"])
        c_reg_y    = json.dumps(corr["reg_y"])
        c_pr       = corr["pearson_r"]
        c_pp       = _pval_label(corr["pearson_p"])
        c_sr       = corr["spearman_r"]
        c_sp       = _pval_label(corr["spearman_p"])
        c_n        = corr["n"]
        c_pr_label = _corr_label(c_pr)
        c_sr_label = _corr_label(c_sr)
    else:
        c_years = c_iciv = c_ied = c_reg_x = c_reg_y = "[]"
        c_pr = c_sr = 0.0
        c_pp = c_sp = "n/a"
        c_n  = 0
        c_pr_label = c_sr_label = "Sin datos"

    # Lineal vs Geometrico
    m_years  = json.dumps(methods["years"])
    m_lin    = json.dumps(methods["linear"])
    m_geom   = json.dumps(methods["geometric"])
    m_deltas = json.dumps(methods["deltas"])
    m_mad    = methods["stats"]["mad"]
    m_corr   = methods["stats"]["corr"]
    m_ml     = methods["stats"]["mean_linear"]
    m_mg     = methods["stats"]["mean_geom"]

    # AHP vs PCA
    w_available = weights.get("available", False)
    if w_available:
        w_years  = json.dumps(weights["years"])
        w_ahp    = json.dumps(weights["ahp"])
        w_pca    = json.dumps(weights["pca"])
        w_deltas = json.dumps(weights["deltas"])
        w_mad    = weights["stats"]["mad"]
        w_corr   = weights["stats"]["corr"]
        w_var    = weights["variance_pc1"]
        # Tabla de pesos
        wt_rows  = ""
        for row in weights["weight_table"]:
            diff_sign = "+" if row["diff"] >= 0 else ""
            diff_col  = "#00d4aa" if abs(row["diff"]) < 0.02 else ("#e67e22" if abs(row["diff"]) < 0.05 else "#e05c5c")
            wt_rows += (
                f'<tr>'
                f'<td>{row["dim"]}</td>'
                f'<td>{row["ahp_w"]:.4f} ({row["ahp_w"]*100:.1f}%)</td>'
                f'<td>{row["pca_w"]:.4f} ({row["pca_w"]*100:.1f}%)</td>'
                f'<td style="color:{diff_col};font-weight:600">{diff_sign}{row["diff"]:.4f}</td>'
                f'</tr>\n'
            )
        w_lbl_arr = json.dumps([r["dim"] for r in weights["weight_table"]])
        w_ahp_arr = json.dumps([r["ahp_w"] for r in weights["weight_table"]])
        w_pca_arr = json.dumps([r["pca_w"] for r in weights["weight_table"]])
    else:
        w_years = w_ahp = w_pca = w_deltas = "[]"
        w_mad = w_corr = w_var = 0.0
        wt_rows = '<tr><td colspan="4" style="color:var(--muted)">PCA no disponible</td></tr>'
        w_lbl_arr = w_ahp_arr = w_pca_arr = "[]"

    # Robusto o no?
    robust_msg = (
        "ROBUSTO: el ICIV es estable ante cambios de pesos (SI < 0.08)"
        if s_si < 0.08 else
        "MODERADO: el ICIV muestra cierta sensibilidad a los pesos (SI >= 0.08)"
        if s_si < 0.15 else
        "SENSIBLE: el ICIV varia significativamente segun los pesos (SI >= 0.15)"
    )
    robust_cls = "alert-good" if s_si < 0.08 else ("alert-warn" if s_si < 0.15 else "alert-bad")
    si_label   = "Robusto" if s_si < 0.08 else ("Moderado" if s_si < 0.15 else "Sensible")
    si_val_cls = "c-accent" if s_si < 0.08 else ("c-orange" if s_si < 0.15 else "c-red")

    # -- Pre-build conditional HTML blocks to avoid nested f-string issues -------

    # Section 2: Correlacion IED
    if not corr_available:
        corr_block = (
            '<div class="alert alert-warn">'
            '<div class="alert-title">Datos insuficientes</div>'
            '<div class="alert-body">IED no disponible o menos de 5 puntos. '
            'Verifica los datos de WDI (ied_neta_usd).</div></div>'
        )
    else:
        c_pr_cls = "c-accent" if abs(c_pr) >= 0.4 else "c-orange"
        c_sr_cls = "c-accent" if abs(c_sr) >= 0.4 else "c-orange"
        corr_block = (
            f'<div class="stats-row">'
            f'<div class="stat"><div class="stat-label">Pearson r</div>'
            f'<div class="stat-val {c_pr_cls}">{c_pr:.4f}</div>'
            f'<div class="stat-sub">{c_pr_label} · {c_pp}</div></div>'
            f'<div class="stat"><div class="stat-label">Spearman rho</div>'
            f'<div class="stat-val {c_sr_cls}">{c_sr:.4f}</div>'
            f'<div class="stat-sub">{c_sr_label} · {c_sp}</div></div>'
            f'<div class="stat"><div class="stat-label">Observaciones (n)</div>'
            f'<div class="stat-val c-accent">{c_n}</div>'
            f'<div class="stat-sub">anos con ambas variables</div></div>'
            f'</div>'
            f'<div class="grid-2">'
            f'<div class="card"><div class="ct">Scatter: ICIV vs IED normalizada</div>'
            f'<div class="cs">Cada punto = un ano · Linea roja = regresion lineal</div>'
            f'<div style="height:300px;position:relative"><canvas id="cCorrScatter"></canvas></div></div>'
            f'<div class="card"><div class="ct">Serie temporal comparada</div>'
            f'<div class="cs">ICIV (eje izq.) vs IED normalizada (eje der.)</div>'
            f'<div style="height:300px;position:relative"><canvas id="cCorrTime"></canvas></div></div>'
            f'</div>'
        )

    # Section 4: AHP vs PCA
    if not w_available:
        weights_block = (
            '<div class="alert alert-warn">'
            '<div class="alert-title">PCA no disponible</div>'
            '<div class="alert-body">Insuficientes datos completos para el PCA.</div></div>'
        )
    else:
        w_mad_cls = "c-accent" if w_mad < 3 else "c-orange"
        weights_block = (
            f'<div class="stats-row">'
            f'<div class="stat"><div class="stat-label">PC1 varianza explicada</div>'
            f'<div class="stat-val c-accent">{w_var}%</div>'
            f'<div class="stat-sub">Del total de varianza dimensional</div></div>'
            f'<div class="stat"><div class="stat-label">MAD (AHP vs PCA)</div>'
            f'<div class="stat-val {w_mad_cls}">{w_mad} pts</div>'
            f'<div class="stat-sub">Diferencia promedio en ICIV</div></div>'
            f'<div class="stat"><div class="stat-label">Correlacion AHP-PCA</div>'
            f'<div class="stat-val c-accent">{w_corr:.4f}</div>'
            f'<div class="stat-sub">Pearson entre series</div></div>'
            f'</div>'
            f'<div class="grid-2">'
            f'<div class="card"><div class="ct">Tabla de pesos: AHP vs PCA</div>'
            f'<div class="cs">PC1 varianza explicada = {w_var}%</div>'
            f'<table class="vtable"><thead><tr><th>Dimension</th><th>Peso AHP</th>'
            f'<th>Peso PCA</th><th>Diferencia</th></tr></thead>'
            f'<tbody>{wt_rows}</tbody></table></div>'
            f'<div class="card"><div class="ct">Pesos por dimension: AHP vs PCA</div>'
            f'<div class="cs">Comparativa visual de ponderaciones</div>'
            f'<div style="height:260px;position:relative"><canvas id="cWeightsBar"></canvas></div></div>'
            f'<div class="card wide"><div class="ct">ICIV resultante: AHP vs PCA</div>'
            f'<div class="cs">Mismo metodo de agregacion (lineal) — distinta ponderacion</div>'
            f'<div style="height:300px;position:relative"><canvas id="cWeightsLine"></canvas></div></div>'
            f'</div>'
        )

    m_mad_cls = "c-accent" if m_mad < 3 else "c-orange"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ICIV — Validacion del Modelo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{{
  --bg:#0d1117;--card:#1c2128;--border:#30363d;
  --text:#e6edf3;--muted:#8b949e;--accent:#00d4aa;
  --red:#e05c5c;--orange:#e67e22;--yellow:#f1c40f;--green:#2ecc71;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}

/* nav */
.nav{{position:sticky;top:0;z-index:100;background:#161b22;border-bottom:1px solid var(--border);
      display:flex;align-items:center;gap:0;padding:0 32px;height:48px}}
.nav a{{color:var(--muted);text-decoration:none;font-size:.8rem;font-weight:500;
        padding:0 16px;height:48px;display:flex;align-items:center;border-bottom:2px solid transparent;
        transition:color .2s,border-color .2s}}
.nav a:hover{{color:var(--text);border-bottom-color:var(--accent)}}
.nav-brand{{color:var(--accent);font-weight:700;font-size:.9rem;margin-right:24px}}

/* header */
.header{{padding:36px 40px 28px;background:linear-gradient(135deg,#161b22 0%,#1c2128 100%);
         border-bottom:1px solid var(--border)}}
.header h1{{font-size:1.7rem;font-weight:700}}
.header h1 span{{color:var(--accent)}}
.header .sub{{color:var(--muted);font-size:.85rem;margin-top:6px}}

/* section */
.section{{padding:32px 40px;border-bottom:1px solid var(--border)}}
.section-header{{margin-bottom:20px}}
.section-title{{font-size:.7rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:1px}}
.section-h2{{font-size:1.15rem;font-weight:700;margin-top:4px}}
.section-sub{{font-size:.78rem;color:var(--muted);margin-top:2px}}

/* grid */
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}}

/* cards */
.card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px}}
.card.wide{{grid-column:span 2}}
.ct{{font-size:.78rem;font-weight:600;color:var(--text);margin-bottom:2px}}
.cs{{font-size:.7rem;color:var(--muted);margin-bottom:16px}}

/* stats */
.stats-row{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
.stat{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 18px;flex:1;min-width:120px}}
.stat-label{{font-size:.66rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px}}
.stat-val{{font-size:1.5rem;font-weight:700}}
.stat-sub{{font-size:.7rem;color:var(--muted);margin-top:3px}}
.c-accent{{color:var(--accent)}}
.c-green{{color:var(--green)}}
.c-orange{{color:var(--orange)}}
.c-red{{color:var(--red)}}

/* alerts */
.alert{{border-radius:8px;padding:14px 18px;margin-bottom:18px;border:1px solid}}
.alert-good{{background:#00d4aa15;border-color:#00d4aa40;color:#00d4aa}}
.alert-warn{{background:#e67e2215;border-color:#e67e2240;color:#e67e22}}
.alert-bad{{background:#e05c5c15;border-color:#e05c5c40;color:#e05c5c}}
.alert-title{{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px}}
.alert-body{{font-size:.84rem;color:var(--text);line-height:1.5}}

/* tables */
.vtable{{width:100%;border-collapse:collapse;font-size:.82rem}}
.vtable th{{text-align:left;padding:8px 12px;font-size:.66rem;color:var(--muted);
            text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border)}}
.vtable td{{padding:8px 12px;border-bottom:1px solid #21262d;vertical-align:middle}}
.vtable tr:last-child td{{border-bottom:none}}
.vtable tbody tr:hover{{background:rgba(255,255,255,.02)}}

/* badge */
.badge{{display:inline-block;padding:2px 9px;border-radius:10px;font-size:.7rem;font-weight:600}}

/* footer */
.footer{{text-align:center;padding:24px;font-size:.72rem;color:var(--muted);border-top:1px solid var(--border)}}

@media(max-width:900px){{
  .grid-2,.grid-3{{grid-template-columns:1fr}}
  .card.wide{{grid-column:span 1}}
  .section{{padding:22px 18px}}
  .header{{padding:22px 18px}}
}}
</style>
</head>
<body>

<!-- NAV -->
<nav class="nav">
  <span class="nav-brand">ICIV · Validacion</span>
  <a href="#sensibilidad">Sensibilidad</a>
  <a href="#correlacion">Correlacion IED</a>
  <a href="#metodos">Lineal vs Geometrico</a>
  <a href="#ponderacion">AHP vs PCA</a>
</nav>

<!-- HEADER -->
<div class="header">
  <h1>ICIV — <span>Validacion del Modelo</span></h1>
  <p class="sub">Paso 7 de la metodologia · OCDE Handbook on Constructing Composite Indicators (2008) · {generated_at}</p>
</div>

<!-- ===== 1. SENSIBILIDAD ===== -->
<section class="section" id="sensibilidad">
  <div class="section-header">
    <div class="section-title">Analisis 1 de 4</div>
    <div class="section-h2">Analisis de Sensibilidad de Pesos AHP</div>
    <div class="section-sub">Perturbacion de +/-5%, +/-10%, +/-20% en cada peso de dimension · Redistribucion proporcional</div>
  </div>

  <div class="alert {robust_cls}">
    <div class="alert-title">Conclusion de robustez</div>
    <div class="alert-body">{robust_msg} — Indice de Sensibilidad (SI) = {s_si:.4f}</div>
  </div>

  <div class="stats-row">
    <div class="stat">
      <div class="stat-label">Indice de Sensibilidad (SI)</div>
      <div class="stat-val {si_val_cls}">{s_si:.4f}</div>
      <div class="stat-sub">SI = Rango medio / ICIV medio</div>
    </div>
    <div class="stat">
      <div class="stat-label">Rango medio de variacion</div>
      <div class="stat-val c-accent">{s_mr} pts</div>
      <div class="stat-sub">Promedio de (ICIV_max - ICIV_min) por ano</div>
    </div>
    <div class="stat">
      <div class="stat-label">Rango maximo observado</div>
      <div class="stat-val c-orange">{s_maxr} pts</div>
      <div class="stat-sub">En el ano mas sensible</div>
    </div>
    <div class="stat">
      <div class="stat-label">Escenarios evaluados</div>
      <div class="stat-val c-accent">{len(DIM_COLS) * 6}</div>
      <div class="stat-sub">6 dimensiones × 6 perturbaciones</div>
    </div>
  </div>

  <div class="grid-2">
    <div class="card wide">
      <div class="ct">Corredor de sensibilidad del ICIV</div>
      <div class="cs">Area sombreada = rango posible ante perturbaciones de pesos · Linea central = AHP base</div>
      <div style="height:340px;position:relative">
        <canvas id="cSensEnvelope"></canvas>
      </div>
    </div>
    <div class="card">
      <div class="ct">Impacto por dimension</div>
      <div class="cs">Variacion media absoluta del ICIV al perturbar cada dimension</div>
      <div style="height:280px;position:relative">
        <canvas id="cSensImpact"></canvas>
      </div>
    </div>
    <div class="card">
      <div class="ct">Interpretacion del Indice de Sensibilidad</div>
      <div class="cs">Referencia: Saisana & Tarantola (2002), OCDE Handbook (2008)</div>
      <table class="vtable" style="margin-top:8px">
        <thead><tr><th>SI</th><th>Clasificacion</th><th>Interpretacion</th></tr></thead>
        <tbody>
          <tr><td>0.00 – 0.08</td><td><span class="badge" style="background:#00d4aa22;color:#00d4aa">Robusto</span></td><td>Pesos tienen efecto marginal</td></tr>
          <tr><td>0.08 – 0.15</td><td><span class="badge" style="background:#e67e2222;color:#e67e22">Moderado</span></td><td>Cierta dependencia de los pesos</td></tr>
          <tr><td>&gt; 0.15</td><td><span class="badge" style="background:#e05c5c22;color:#e05c5c">Sensible</span></td><td>Resultado dependiente de pesos</td></tr>
        </tbody>
      </table>
      <div style="margin-top:16px;padding:12px;background:#0d1117;border-radius:8px;border:1px solid var(--border)">
        <div style="font-size:.7rem;color:var(--muted);margin-bottom:4px">ICIV obtenido en este analisis</div>
        <div style="font-size:1.1rem;font-weight:700;color:var(--accent)">SI = {s_si:.4f}
          <span style="font-size:.78rem;color:var(--muted);font-weight:400;margin-left:8px">
            {si_label}
          </span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ===== 2. CORRELACION IED ===== -->
<section class="section" id="correlacion">
  <div class="section-header">
    <div class="section-title">Analisis 2 de 4</div>
    <div class="section-h2">Correlacion ICIV vs Inversion Extranjera Directa (IED)</div>
    <div class="section-sub">Validacion: si el ICIV captura el clima de inversion real, deberia correlacionar con los flujos de IED</div>
  </div>

  {corr_block}
</section>

<!-- ===== 3. LINEAL vs GEOMETRICO ===== -->
<section class="section" id="metodos">
  <div class="section-header">
    <div class="section-title">Analisis 3 de 4</div>
    <div class="section-h2">Comparacion: Agregacion Lineal vs Geometrica</div>
    <div class="section-sub">Mismos pesos AHP — diferente funcion de agregacion · Ref: OCDE Handbook (2008), Cap. 6</div>
  </div>

  <div class="alert alert-warn">
    <div class="alert-title">Interpretacion</div>
    <div class="alert-body">
      La agregacion geometrica penaliza dimensiones extremadamente bajas (no permite compensacion plena).
      Para Venezuela, valores muy bajos en D1 (macro) o D3 (institucional) reducen mas el ICIV geometrico.
      Una diferencia media peqena (MAD &lt; 3 pts) indica que ambos metodos son intercambiables.
    </div>
  </div>

  <div class="stats-row">
    <div class="stat">
      <div class="stat-label">MAD (Desv. Absoluta Media)</div>
      <div class="stat-val {m_mad_cls}">{m_mad} pts</div>
      <div class="stat-sub">Diferencia promedio entre metodos</div>
    </div>
    <div class="stat">
      <div class="stat-label">Correlacion L-G</div>
      <div class="stat-val c-accent">{m_corr:.4f}</div>
      <div class="stat-sub">Pearson entre series</div>
    </div>
    <div class="stat">
      <div class="stat-label">Media Lineal</div>
      <div class="stat-val c-accent">{m_ml}</div>
      <div class="stat-sub">Promedio historico</div>
    </div>
    <div class="stat">
      <div class="stat-label">Media Geometrica</div>
      <div class="stat-val c-orange">{m_mg}</div>
      <div class="stat-sub">Promedio historico</div>
    </div>
  </div>

  <div class="grid-2">
    <div class="card wide">
      <div class="ct">ICIV Lineal vs Geometrico</div>
      <div class="cs">Area sombreada = diferencia entre metodos</div>
      <div style="height:320px;position:relative"><canvas id="cMethodsLine"></canvas></div>
    </div>
    <div class="card wide">
      <div class="ct">Delta (Geometrico - Lineal)</div>
      <div class="cs">Diferencia puntual por ano · Negativo = geometrico penaliza mas</div>
      <div style="height:220px;position:relative"><canvas id="cMethodsDelta"></canvas></div>
    </div>
  </div>
</section>

<!-- ===== 4. AHP vs PCA ===== -->
<section class="section" id="ponderacion">
  <div class="section-header">
    <div class="section-title">Analisis 4 de 4</div>
    <div class="section-h2">Comparacion de Estrategias de Ponderacion: AHP vs PCA</div>
    <div class="section-sub">AHP = juicio experto (Saaty 1980) · PCA = varianza estadistica (OCDE 2008, Cap. 6)</div>
  </div>

  {weights_block}
</section>

<footer class="footer">
  ICIV · Validacion del Modelo · Tesis de Posgrado — Especializacion en Big Data e Inteligencia de Negocios<br>
  Referencias: Saaty (1980) · OCDE Handbook on Constructing Composite Indicators (2008) · Saisana & Tarantola (2002)
</footer>

<script>
Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.font.family = "'Inter', sans-serif";

// ── Data ────────────────────────────────────────────────────────────────────
const sYears    = {s_years};
const sBase     = {s_baseline};
const sEnvMin   = {s_env_min};
const sEnvMax   = {s_env_max};
const sImpLbls  = {dim_impact_labels};
const sImpVals  = {dim_impact_vals};

const cYears    = {c_years};
const cIciv     = {c_iciv};
const cIed      = {c_ied};
const cRegX     = {c_reg_x};
const cRegY     = {c_reg_y};

const mYears    = {m_years};
const mLin      = {m_lin};
const mGeom     = {m_geom};
const mDeltas   = {m_deltas};

const wYears    = {w_years};
const wAhp      = {w_ahp};
const wPca      = {w_pca};
const wDeltas   = {w_deltas};
const wLbls     = {w_lbl_arr};
const wAhpArr   = {w_ahp_arr};
const wPcaArr   = {w_pca_arr};

// ── 1a. Sensibilidad — Corredor ──────────────────────────────────────────────
new Chart(document.getElementById('cSensEnvelope'), {{
  data: {{
    labels: sYears,
    datasets: [
      {{
        type: 'line',
        label: 'ICIV max (escenario)',
        data: sEnvMax,
        borderColor: '#e67e22',
        borderWidth: 1,
        borderDash: [3,3],
        pointRadius: 0,
        fill: false,
      }},
      {{
        type: 'line',
        label: 'ICIV AHP (base)',
        data: sBase,
        borderColor: '#00d4aa',
        borderWidth: 2.5,
        pointRadius: 4,
        pointBackgroundColor: '#00d4aa',
        fill: false,
        tension: 0.3,
      }},
      {{
        type: 'line',
        label: 'ICIV min (escenario)',
        data: sEnvMin,
        borderColor: '#e05c5c',
        borderWidth: 1,
        borderDash: [3,3],
        pointRadius: 0,
        backgroundColor: 'rgba(230,126,34,0.08)',
        fill: 1,
      }},
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{ legend: {{ position: 'top' }} }},
    scales: {{
      y: {{ min: 0, max: 100, grid: {{ color: '#21262d' }}, ticks: {{ stepSize: 10 }} }},
      x: {{ grid: {{ color: '#21262d' }} }}
    }}
  }}
}});

// ── 1b. Sensibilidad — Impacto por dimension ─────────────────────────────────
new Chart(document.getElementById('cSensImpact'), {{
  type: 'bar',
  data: {{
    labels: sImpLbls,
    datasets: [{{
      label: 'Impacto medio (pts)',
      data: sImpVals,
      backgroundColor: ['#3498db99','#e67e2299','#9b59b699','#1abc9c99','#e74c3c99','#f39c1299'],
      borderColor:     ['#3498db',  '#e67e22',  '#9b59b6',  '#1abc9c',  '#e74c3c',  '#f39c12'],
      borderWidth: 1,
      borderRadius: 4,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: '#21262d' }}, title: {{ display: true, text: 'Variacion media absoluta (pts)' }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}
    }}
  }}
}});

// ── 2a. Correlacion — Scatter ─────────────────────────────────────────────────
if (document.getElementById('cCorrScatter')) {{
  new Chart(document.getElementById('cCorrScatter'), {{
    type: 'scatter',
    data: {{
      datasets: [
        {{
          label: 'Ano (ICIV, IED)',
          data: cIciv.map((v, i) => ({{ x: v, y: cIed[i] }})),
          backgroundColor: '#00d4aa99',
          borderColor: '#00d4aa',
          pointRadius: 6,
        }},
        {{
          type: 'line',
          label: 'Regresion',
          data: cRegX.map((v, i) => ({{ x: v, y: cRegY[i] }})),
          borderColor: '#e05c5c',
          borderWidth: 1.5,
          borderDash: [4,3],
          pointRadius: 0,
          fill: false,
        }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: 'top' }}, tooltip: {{
        callbacks: {{
          label: (ctx) => {{
            const i = ctx.dataIndex;
            return `${{cYears[i]}}: ICIV=${{cIciv[i]}}, IED=${{cIed[i]}}`;
          }}
        }}
      }} }},
      scales: {{
        x: {{ title: {{ display: true, text: 'ICIV (AHP)' }}, grid: {{ color: '#21262d' }} }},
        y: {{ title: {{ display: true, text: 'IED normalizada (0-100)' }}, grid: {{ color: '#21262d' }} }}
      }}
    }}
  }});

  // ── 2b. Correlacion — Serie temporal ────────────────────────────────────────
  new Chart(document.getElementById('cCorrTime'), {{
    type: 'line',
    data: {{
      labels: cYears,
      datasets: [
        {{
          label: 'ICIV (AHP)',
          data: cIciv,
          borderColor: '#00d4aa',
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.3,
          yAxisID: 'y',
        }},
        {{
          label: 'IED normalizada',
          data: cIed,
          borderColor: '#e67e22',
          borderWidth: 2,
          borderDash: [4,3],
          pointRadius: 3,
          tension: 0.3,
          yAxisID: 'y2',
        }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{ legend: {{ position: 'top' }} }},
      scales: {{
        y:  {{ min: 0, max: 100, grid: {{ color: '#21262d' }}, title: {{ display: true, text: 'ICIV' }} }},
        y2: {{ min: 0, max: 100, position: 'right', grid: {{ display: false }}, title: {{ display: true, text: 'IED (norm)' }} }},
        x:  {{ grid: {{ color: '#21262d' }} }}
      }}
    }}
  }});
}}

// ── 3a. Metodos — Lineas ─────────────────────────────────────────────────────
new Chart(document.getElementById('cMethodsLine'), {{
  type: 'line',
  data: {{
    labels: mYears,
    datasets: [
      {{
        label: 'Lineal',
        data: mLin,
        borderColor: '#00d4aa',
        borderWidth: 2,
        pointRadius: 3,
        tension: 0.3,
        fill: false,
      }},
      {{
        label: 'Geometrico',
        data: mGeom,
        borderColor: '#e67e22',
        borderWidth: 2,
        borderDash: [5,3],
        pointRadius: 3,
        tension: 0.3,
        fill: false,
      }},
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{ legend: {{ position: 'top' }} }},
    scales: {{
      y: {{ min: 0, max: 100, grid: {{ color: '#21262d' }} }},
      x: {{ grid: {{ color: '#21262d' }} }}
    }}
  }}
}});

// ── 3b. Metodos — Delta ───────────────────────────────────────────────────────
new Chart(document.getElementById('cMethodsDelta'), {{
  type: 'bar',
  data: {{
    labels: mYears,
    datasets: [{{
      label: 'Delta (Geom - Lin)',
      data: mDeltas,
      backgroundColor: mDeltas.map(v => v >= 0 ? 'rgba(0,212,170,0.5)' : 'rgba(224,92,92,0.5)'),
      borderColor:     mDeltas.map(v => v >= 0 ? '#00d4aa' : '#e05c5c'),
      borderWidth: 1,
      borderRadius: 3,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      y: {{ grid: {{ color: '#21262d' }}, title: {{ display: true, text: 'pts' }} }},
      x: {{ grid: {{ color: '#21262d' }} }}
    }}
  }}
}});

// ── 4a. Ponderacion — Barras comparativas ────────────────────────────────────
if (document.getElementById('cWeightsBar')) {{
  new Chart(document.getElementById('cWeightsBar'), {{
    type: 'bar',
    data: {{
      labels: wLbls,
      datasets: [
        {{
          label: 'Peso AHP',
          data: wAhpArr,
          backgroundColor: '#00d4aa66',
          borderColor: '#00d4aa',
          borderWidth: 1,
          borderRadius: 3,
        }},
        {{
          label: 'Peso PCA',
          data: wPcaArr,
          backgroundColor: '#e67e2266',
          borderColor: '#e67e22',
          borderWidth: 1,
          borderRadius: 3,
        }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: 'top' }} }},
      scales: {{
        y: {{ min: 0, grid: {{ color: '#21262d' }}, ticks: {{ format: {{ style: 'percent' }} }} }},
        x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 9 }} }} }}
      }}
    }}
  }});

  // ── 4b. Ponderacion — Series ICIV ────────────────────────────────────────────
  new Chart(document.getElementById('cWeightsLine'), {{
    type: 'line',
    data: {{
      labels: wYears,
      datasets: [
        {{
          label: 'ICIV (AHP)',
          data: wAhp,
          borderColor: '#00d4aa',
          borderWidth: 2.5,
          pointRadius: 3,
          tension: 0.3,
          fill: false,
        }},
        {{
          label: 'ICIV (PCA)',
          data: wPca,
          borderColor: '#e67e22',
          borderWidth: 2,
          borderDash: [5,3],
          pointRadius: 3,
          tension: 0.3,
          fill: false,
        }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{ legend: {{ position: 'top' }} }},
      scales: {{
        y: {{ min: 0, max: 100, grid: {{ color: '#21262d' }} }},
        x: {{ grid: {{ color: '#21262d' }} }}
      }}
    }}
  }});
}}
</script>
</body>
</html>"""


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

def run_validation(open_browser: bool = True) -> Path:
    logger.info("\n" + "-" * 60)
    logger.info("  Validacion del modelo ICIV")
    logger.info("-" * 60)

    # -- Cargar datos ----------------------------------------------------------
    df_norm, df_ahp = _load_data()

    # -- Obtener pesos AHP base ------------------------------------------------
    ahp = AHPWeights()
    ahp.compute_weights(df_norm)
    base_weights = {k: v for k, v in ahp.dimension_result_["weights"].items()
                    if k in DIM_COLS}
    total_w = sum(base_weights.values())
    base_weights = {k: v / total_w for k, v in base_weights.items()}

    # -- Ejecutar los 4 analisis -----------------------------------------------
    sens    = run_sensitivity(df_norm, base_weights)
    corr    = run_ied_correlation(df_norm, df_ahp)
    methods = run_method_comparison(df_norm, base_weights)
    weights = run_ahp_vs_pca(df_norm, df_ahp, base_weights)

    # -- Generar HTML ----------------------------------------------------------
    generated_at = datetime.now().strftime("%d de %B de %Y · %H:%M")
    html = _build_html(sens, corr, methods, weights, generated_at)

    out_path = settings.paths.data_processed / "iciv_validacion.html"
    out_path.write_text(html, encoding="utf-8")
    logger.info("\n  OK Reporte guardado -> %s", out_path)

    # -- Resumen en consola ----------------------------------------------------
    logger.info("\n" + "=" * 60)
    logger.info("  RESUMEN DE VALIDACION")
    logger.info("=" * 60)
    logger.info("  Sensibilidad  SI = %.4f  (%s)",
                sens["stability"]["sensitivity_index"],
                "Robusto" if sens["stability"]["sensitivity_index"] < 0.08 else
                "Moderado" if sens["stability"]["sensitivity_index"] < 0.15 else "Sensible")
    if corr.get("available"):
        logger.info("  Correlacion   Pearson r = %.4f  Spearman rho = %.4f  (n=%d)",
                    corr["pearson_r"], corr["spearman_r"], corr["n"])
    logger.info("  Lineal-Geom   MAD = %.3f pts  |  corr = %.4f",
                methods["stats"]["mad"], methods["stats"]["corr"])
    if weights.get("available"):
        logger.info("  AHP-PCA       MAD = %.3f pts  |  PC1 var = %.1f%%",
                    weights["stats"]["mad"], weights["variance_pc1"])
    logger.info("=" * 60)

    if open_browser:
        webbrowser.open(out_path.as_uri())

    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validacion del modelo ICIV")
    parser.add_argument("--no-open", action="store_true", help="No abrir el navegador")
    args = parser.parse_args()
    run_validation(open_browser=not args.no_open)
