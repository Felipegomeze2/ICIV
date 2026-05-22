"""Tests para ICIVAggregator y la arquitectura del índice."""

import pytest
import pandas as pd
import numpy as np

from iciv.index import ICIVAggregator, DIMENSIONS, validate_dimension_weights
from iciv.index.weighting import FixedWeights
from iciv.data.models import DimensionID


def test_dimension_weights_sum_to_one():
    """Los pesos de las 5 dimensiones deben sumar exactamente 1.0."""
    validate_dimension_weights()  # lanza ValueError si falla
    total = sum(d.iciv_weight for d in DIMENSIONS.values())
    assert abs(total - 1.0) < 0.01


def test_each_dimension_variable_weights_sum_to_one():
    """Los pesos de variables dentro de cada dimensión deben sumar 1.0."""
    for dim_id, dim in DIMENSIONS.items():
        total = sum(v.weight for v in dim.variables)
        assert abs(total - 1.0) < 0.01, \
            f"Dimensión {dim.name}: pesos suman {total:.3f}, esperado 1.0"


def test_aggregator_linear(sample_normalized_df):
    agg = ICIVAggregator(method="linear")
    result = agg.compute(sample_normalized_df)

    assert "iciv_score" in result.columns
    assert "iciv_categoria" in result.columns
    assert "año" in result.columns

    scores = result["iciv_score"].dropna()
    assert (scores >= 0).all()
    assert (scores <= 100).all()


def test_aggregator_geometric(sample_normalized_df):
    agg = ICIVAggregator(method="geometric")
    result = agg.compute(sample_normalized_df)
    scores = result["iciv_score"].dropna()
    assert (scores >= 0).all()
    assert (scores <= 100).all()


def test_aggregator_dimension_columns(sample_normalized_df):
    agg = ICIVAggregator()
    result = agg.compute(sample_normalized_df)
    for dim_id in DIMENSIONS:
        assert dim_id.value in result.columns, \
            f"Falta columna de dimensión: {dim_id.value}"


def test_risk_category_assigned(sample_normalized_df):
    result = ICIVAggregator().compute(sample_normalized_df)
    valid_categories = {
        "🔴 Alto Riesgo", "🟠 Riesgo Moderado-Alto",
        "🟡 Riesgo Moderado", "🟢 Bajo Riesgo", "🟢🟢 Muy Bajo Riesgo",
        "Sin datos",
        "Sin categoria",
    }
    for cat in result["iciv_categoria"].dropna():
        assert cat in valid_categories, f"Categoría inesperada: {cat}"


def test_fixed_weights_compute(sample_normalized_df):
    strategy = FixedWeights()
    weights = strategy.compute_weights(sample_normalized_df)
    assert isinstance(weights, dict)
    assert len(weights) > 0
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.01, f"Pesos suman {total:.3f}"


def test_aggregator_invalid_method():
    with pytest.raises(ValueError, match="no reconocido"):
        agg = ICIVAggregator(method="invalid")  # type: ignore
        row = pd.Series({"D1_macro": 50.0})
        agg._aggregate_dimensions(row, ["D1_macro"], {"D1_macro": 1.0})
