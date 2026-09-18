"""Deterministic methodological alternatives, not simulated observations."""
from __future__ import annotations
import numpy as np
import pandas as pd
from iciv.data.catalog import get_negative_variables
from iciv.index.aggregator import ICIVAggregator
from iciv.index.dimensions import DIMENSIONS
from iciv.index.weighting.ahp_weights import AHPWeights
from iciv.index.weighting.fixed_weights import FixedWeights

VARIABLES = [v.column for d in DIMENSIONS.values() for v in d.variables]

def alternative_normalization(transformed, method, fit_end=None):
    """Fit retrospective normalizers on real values. Preserve missingness."""
    result = transformed.reindex(columns=["año"] + VARIABLES).copy()
    negative = set(get_negative_variables())
    for col in VARIABLES:
        values = pd.to_numeric(result[col])
        train = values[result["año"] <= fit_end] if fit_end is not None else values
        train = train.dropna()
        if train.empty or train.nunique() < 2:
            result[col] = np.nan
            continue
        if method == "rank":
            # Average tied ranks on the observed historical sample; no fill.
            if fit_end is not None:
                raise ValueError("rank fit_end not supported")
            ranks = values.rank(method="average")
            score = (ranks - ranks.min()) / (ranks.max() - ranks.min()) * 100
        else:
            if method == "winsor05":
                lo, hi = train.quantile([.05, .95])
            elif method == "minmax":
                lo, hi = train.min(), train.max()
            else:
                raise ValueError(method)
            score = (values - lo) / (hi - lo) * 100 if hi > lo else values * np.nan
            score = score.clip(0, 100)
        result[col] = 100 - score if col in negative else score
    return result

def common_basket_changes(normalized):
    """Adjacent-year change with the same observed variables on both sides.

    Full-universe coverage denominator and dimensional floor remain unchanged.
    Residual is a net composition effect, not an economic causal attribution.
    """
    df = normalized.reindex(columns=["año"] + VARIABLES).sort_values("año").reset_index(drop=True)
    actual = ICIVAggregator().compute(df).set_index("año")
    rows = []
    for i in range(1, len(df)):
        pair = df.iloc[i-1:i+1].copy()
        y0, y1 = pair["año"].astype(int)
        if y1 != y0 + 1:
            continue
        common = pair[VARIABLES].notna().all()
        pair.loc[:, common.index[~common]] = np.nan
        comp = ICIVAggregator().compute(pair)
        published_delta = actual.loc[y1, "iciv_score"] - actual.loc[y0, "iciv_score"]
        common_delta = comp.iloc[1].iciv_score - comp.iloc[0].iciv_score
        rows.append({"año": y1, "año_previo": y0, "delta_publicado": published_delta,
                     "delta_canasta_comun": common_delta,
                     "efecto_composicion_neto": published_delta-common_delta,
                     "cobertura_comun_pct": comp.iloc[1].cobertura_pct,
                     "n_variables_comunes": int(common.sum()),
                     "cambio_signo": bool(np.isfinite(common_delta) and published_delta*common_delta < 0)})
    return pd.DataFrame(rows)

def evaluate_scenarios(normalized, transformed, verified=None):
    base_agg = ICIVAggregator()
    baseline = base_agg.compute(normalized).set_index("año")
    weights = base_agg.variable_weights_
    dimensions = base_agg.dimension_weights_
    scenarios = []

    def add(name, family, data=None, w=None, floor=.5, method="linear", note=""):
        agg = ICIVAggregator(strategy=FixedWeights(override=w if w is not None else weights),
                             min_dimension_coverage=floor, method=method)
        data = normalized if data is None else data
        out = agg.compute(data).set_index("año")
        scenarios.append((name, family, note, out))

    for dim_id, dim in DIMENSIONS.items():
        for change in (-.20, -.10, -.05, .05, .10, .20):
            target = dim_id.value
            new = dimensions.copy()
            new[target] = dimensions[target] * (1+change)
            for other in new:
                if other != target:
                    new[other] *= (1-new[target])/(1-dimensions[target])
            adjusted = {v.column: new[d.value]*v.weight for d, spec in DIMENSIONS.items() for v in spec.variables}
            add(f"peso_{target}_{change:+.0%}", "pesos", w=adjusted)
    add("dimensiones_iguales", "pesos", w={v.column: v.weight/6 for d in DIMENSIONS.values() for v in d.variables})
    add("geometrico", "agregacion", method="geometric")
    for method in ("winsor05", "rank"):
        add(method, "normalizacion", data=alternative_normalization(transformed, method),
            note="Escala alternativa; categorías no recalibradas. No es un intervalo de confianza.")
    add("minmax_sin_2026_en_ajuste", "normalizacion", data=alternative_normalization(transformed, "minmax", 2025))
    for floor in (.25, .75, 1.):
        add(f"piso_{floor:.0%}", "cobertura", floor=floor)
    for col in VARIABLES:
        w = weights.copy(); w[col] = 0
        add("excluir_" + col, "exclusion_variable", w=w,
            note="Cambio explícito del universo, no una avería de fuente; cobertura recalculada.")
    for dim_id, dim in DIMENSIONS.items():
        w = weights.copy()
        for v in dim.variables:
            w[v.column] = 0
        add("excluir_"+dim_id.value, "exclusion_dimension", w=w)
        data = normalized.copy()
        for v in dim.variables:
            data[v.column] = np.nan
        add("sin_datos_"+dim_id.value, "indisponibilidad", data=data,
            note="Universo fijo; cobertura penaliza la fuente ausente.")
    # Sensitivity to the explicit log transformation, not a new official model.
    raw_inflation = transformed.copy()
    raw_inflation["inflacion_ipc_imf_pct"] = 10 ** raw_inflation["inflacion_ipc_imf_pct"]
    add("inflacion_sin_log", "transformacion", data=alternative_normalization(raw_inflation, "minmax"))
    if verified is not None and not verified.empty:
        data = normalized.copy()
        estimated = verified[verified.estado_observacion.eq("WEO_estimacion_o_proyeccion_del_FMI")]
        for _, row in estimated.iterrows():
            if row.variable in data:
                data.loc[data["año"].eq(row["año"]), row.variable] = np.nan
        add("sin_estimaciones_WEO_verificadas", "estado_proveedor", data=data,
            note="Retira únicamente estimaciones FMI con estado acreditado. OIT sigue modelado; no implica conjunto enteramente observado.")

    summary, detail = [], []
    for name, family, note, out in scenarios:
        for year, r in out.iterrows():
            detail.append({"escenario": name, "familia": family, "año": year,
                           "iciv_score": r.iciv_score, "categoria": r.iciv_categoria,
                           "cobertura_pct": r.cobertura_pct,
                           "diferencia_base": r.iciv_score-baseline.loc[year, "iciv_score"]})
        # Report all comparable years and a fixed high-coverage baseline subset.
        for subset, mask in (("todos_comparables", baseline.iciv_score.notna()),
                             ("base_cobertura80", baseline.cobertura_pct.ge(80))):
            years = baseline.index[mask & out.iciv_score.notna()]
            a, b = baseline.loc[years], out.loc[years]
            diff = b.iciv_score-a.iciv_score
            rank = a.iciv_score.corr(b.iciv_score, method="spearman") if len(years)>2 and a.iciv_score.nunique()>1 and b.iciv_score.nunique()>1 else np.nan
            summary.append({"escenario": name, "familia": family, "muestra": subset, "n": len(years),
                            "n_sin_score": int(out.iciv_score.isna().sum()),
                            "mae_vs_base": diff.abs().mean(), "max_abs_vs_base": diff.abs().max(),
                            "sesgo_medio": diff.mean(), "spearman": rank,
                            "cambios_categoria": int(a.iciv_categoria.ne(b.iciv_categoria).sum()),
                            "nota": note})
    return pd.DataFrame(summary), pd.DataFrame(detail), common_basket_changes(normalized)
