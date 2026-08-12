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


# ── Piso de cobertura por dimensión ──────────────────────────────────────────
# Regresión de 2026-08-11: el agregador publicaba el score de una dimensión con
# cualquier variable disponible. En 2025 eso daba D5_capital_humano = 0.0 sobre
# UNA sola variable (18% del peso de la dimensión) y el dashboard lo dibujaba
# igual que una dimensión con cobertura completa.

def _one_variable_per_dimension_df() -> pd.DataFrame:
    """Serie de dos años que reproduce el patrón real de publicación tardía.

    2024: todas las variables publicaron (cobertura 100% en cada dimensión).
    2025: solo la primera variable de cada dimensión; las demás aún no salen.

    El año 2024 es imprescindible: el denominador de cobertura son las variables
    con AL MENOS un dato en toda la serie. Una variable ausente del dataset
    entero (fuente retirada) no debe deprimir la cobertura para siempre, así que
    queda fuera del denominador. Sin 2024, las variables que faltan en 2025 no
    serían candidatas y la cobertura daría 100% — que es lo correcto, pero no lo
    que este test quiere ejercitar.
    """
    rows = {"año": [2024, 2025]}
    for dim in DIMENSIONS.values():
        for i, v in enumerate(dim.variables):
            rows[v.column] = [40.0, 40.0] if i == 0 else [40.0, np.nan]
    return pd.DataFrame(rows)


def test_dimension_coverage_column_is_emitted(sample_normalized_df):
    """compute() publica la cobertura de cada dimensión junto a su score."""
    result = ICIVAggregator(method="linear").compute(sample_normalized_df)
    for dim_id in DIMENSIONS:
        col = f"cobertura_{dim_id.value}"
        assert col in result.columns, f"falta {col}"
        cov = result[col].dropna()
        assert (cov >= 0).all() and (cov <= 100).all()


def test_low_coverage_dimension_is_not_published():
    """Una dimensión bajo el umbral queda NaN, pero su cobertura sí se informa."""
    df = _one_variable_per_dimension_df()
    result = ICIVAggregator(method="linear", min_dimension_coverage=0.50).compute(df)
    y2025 = result[result["año"] == 2025].iloc[0]
    y2024 = result[result["año"] == 2024].iloc[0]

    bajo_umbral = 0
    for dim_id, dim in DIMENSIONS.items():
        peso_primera = dim.variables[0].weight
        col, cov_col = dim_id.value, f"cobertura_{dim_id.value}"

        # 2024 tiene cobertura completa: siempre se publica.
        assert pd.notna(y2024[col]), f"{col}: 2024 tiene 100% de cobertura"

        if peso_primera < 0.50:
            bajo_umbral += 1
            assert pd.isna(y2025[col]), (
                f"{col}: cobertura {peso_primera:.0%} < 50% pero se publicó score"
            )
            # la cobertura se informa aunque el score no se publique
            assert y2025[cov_col] > 0, f"{cov_col}: debería informarse igual"
            assert y2025[cov_col] < 50.0
        else:
            assert pd.notna(y2025[col]), f"{col}: cobertura suficiente, debe publicarse"

    assert bajo_umbral > 0, "el fixture no ejercita ninguna dimensión bajo el umbral"


def test_coverage_floor_zero_restores_previous_behaviour():
    """Con umbral 0 se publica todo, como antes del cambio."""
    df = _one_variable_per_dimension_df()
    result = ICIVAggregator(method="linear", min_dimension_coverage=0.0).compute(df)
    for dim_id in DIMENSIONS:
        assert result[dim_id.value].notna().all(), f"{dim_id.value} debería publicarse"


def test_full_coverage_is_unaffected_by_floor(sample_normalized_df):
    """El piso no altera los años cuyas dimensiones sí tienen cobertura suficiente."""
    sin_piso = ICIVAggregator(method="linear", min_dimension_coverage=0.0)
    con_piso = ICIVAggregator(method="linear", min_dimension_coverage=0.50)
    a = sin_piso.compute(sample_normalized_df)
    b = con_piso.compute(sample_normalized_df)
    for dim_id in DIMENSIONS:
        col, cov_col = dim_id.value, f"cobertura_{dim_id.value}"
        completos = b[cov_col] >= 50.0
        pd.testing.assert_series_equal(
            a.loc[completos, col], b.loc[completos, col], check_names=False
        )
