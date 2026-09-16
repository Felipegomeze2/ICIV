"""Semantic regressions: missing data, applied weights and temporal validation."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from iciv.index.aggregator import ICIVAggregator
from iciv.index.dimensions import DIMENSIONS
from iciv.index.weighting import AHPWeights, FixedWeights

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.external_validation import _correlate, _iciv_without
from scripts.validate_model import run_ahp_vs_pca, _compute_iciv_with_weights


def complete_panel(n=1):
    return pd.DataFrame({"año": range(2000, 2000 + n), **{
        v.column: [float(15 + 12 * i + j) for j in range(n)]
        for i, dim in enumerate(DIMENSIONS.values()) for v in dim.variables
    }})


def test_whole_missing_source_stays_in_coverage_denominator():
    df = complete_panel()
    agg = ICIVAggregator()
    full = agg.compute(df)
    expected_mass = agg.variable_weights_["cpi_score"]
    absent = agg.compute(df.drop(columns="cpi_score"))
    empty = agg.compute(df.assign(cpi_score=np.nan))
    assert full.cobertura_pct.iloc[0] == 100
    assert absent.cobertura_observada_pct.iloc[0] == round(100 * (1 - expected_mass), 1)
    pd.testing.assert_frame_equal(absent, empty)


def test_discarded_dimension_is_excluded_from_effective_coverage():
    df = complete_panel()
    dim = next(iter(DIMENSIONS.values()))
    df[[v.column for v in dim.variables[1:]]] = np.nan
    result = ICIVAggregator().compute(df).iloc[0]
    assert pd.isna(result[dim.id.value])
    assert result.cobertura_observada_pct > result.cobertura_efectiva_pct
    assert result.cobertura_pct == result.cobertura_efectiva_pct
    assert result.dimensiones_publicadas == 5


def test_equal_dimension_overrides_are_actually_applied():
    df = complete_panel()
    weights = {v.column: v.weight / len(DIMENSIONS)
               for dim in DIMENSIONS.values() for v in dim.variables}
    agg = ICIVAggregator(strategy=FixedWeights(override=weights))
    row = agg.compute(df).iloc[0]
    assert row.iciv_score == pytest.approx(np.mean([row[d.value] for d in DIMENSIONS]), abs=.005)
    assert set(round(w, 6) for w in agg.dimension_weights_.values()) == {round(1 / 6, 6)}
    assert row.iciv_score != ICIVAggregator().compute(df).iciv_score.iloc[0]


def test_variable_override_changes_within_dimension_score():
    df = complete_panel()
    target = next(iter(DIMENSIONS.values())).variables[0].column
    df[target] = 99.0
    baseline = ICIVAggregator(strategy=FixedWeights()).compute(df).iciv_score.iloc[0]
    changed = ICIVAggregator(strategy=FixedWeights(override={target: .95})).compute(df).iciv_score.iloc[0]
    assert changed > baseline + 20


def test_custom_ahp_internal_matrix_is_consumed():
    df = complete_panel()
    dim = list(DIMENSIONS.values())[1]
    df[dim.variables[0].column] = 0.0
    df[dim.variables[1].column] = 100.0
    strategy = AHPWeights(variable_matrices={dim.id.value: (
        np.array([[1., 1 / 9], [9., 1.]]), [v.column for v in dim.variables])})
    result = ICIVAggregator(strategy=strategy).compute(df)
    assert result[dim.id.value].iloc[0] == 90.0


def test_default_is_explicit_public_ahp():
    df = complete_panel()
    pd.testing.assert_frame_equal(ICIVAggregator().compute(df), ICIVAggregator(strategy=AHPWeights()).compute(df))
    ahp = AHPWeights()
    ahp.compute_weights(df)
    actual = _compute_iciv_with_weights(df, ahp.dimension_result_["weights"])
    assert actual.iloc[0] == ICIVAggregator().compute(df).iciv_score.iloc[0]


def test_zero_is_not_filled_in_geometric_mean():
    agg = ICIVAggregator(method="geometric")
    assert agg._aggregate_dimensions(pd.Series({"a": 0., "b": 90.}), ["a", "b"], {"a": .5, "b": .5}) == 0


def test_leave_one_out_preserves_public_coverage_floor():
    df = complete_panel()
    df["luminosidad_nocturna_idx"] = np.nan
    expected = ICIVAggregator(strategy=AHPWeights()).compute(df).set_index("año").iciv_score
    pd.testing.assert_series_equal(_iciv_without(complete_panel(), "luminosidad_nocturna_idx"), expected)


def test_annual_differences_do_not_bridge_missing_years():
    index = [2000, 2001, 2003, 2004, 2005, 2006]
    a = pd.Series([2, 5, 9, 11, 17, 18.], index=index)
    b = pd.Series([4, 7, 8, 13, 15, 19.], index=index)
    assert _correlate(a, b, "primeras_diferencias")["n"] == 4
    assert _correlate(a, b)["hac_status"] == "no estimado: años no consecutivos"


def test_hac_reports_exact_sample_and_finite_uncertainty():
    a = pd.Series(np.arange(12.), index=range(2000, 2012))
    b = a * .3 + np.sin(a)
    result = _correlate(a, b)
    assert result["n"] == 12
    assert np.isfinite(result["hac_p"])
    assert result["hac_ci95_low"] <= result["hac_slope"] <= result["hac_ci95_high"]


def test_pca_uses_complete_cases_without_imputing():
    df = complete_panel(10)
    for v in list(DIMENSIONS.values())[4].variables:
        df.loc[:2, v.column] = np.nan
    original = df.copy(deep=True)
    scores = ICIVAggregator().compute(df)
    ahp = AHPWeights()
    ahp.compute_weights(df)
    result = run_ahp_vs_pca(df, scores, ahp.dimension_result_["weights"])
    assert result["available"]
    assert result["n_complete"] == 7
    assert result["fit_years"] == list(range(2003, 2010))
    assert result["years"] == result["fit_years"]
    pd.testing.assert_frame_equal(df, original)


def test_pca_declines_insufficient_complete_cases():
    df = complete_panel(6)
    ahp = AHPWeights()
    ahp.compute_weights(df)
    result = run_ahp_vs_pca(df, ICIVAggregator().compute(df), ahp.dimension_result_["weights"])
    assert not result["available"]
    assert result["n_complete"] == 6
