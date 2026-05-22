"""Tests para el Pipeline y los transformers."""

import pytest
import pandas as pd
import numpy as np

from iciv.processing import Pipeline, DataCleaner, GapImputer, MinMaxNormalizer


def test_pipeline_fit_transform(sample_wdi_df):
    pipeline = Pipeline([
        ("clean", DataCleaner()),
        ("impute", GapImputer()),
    ])
    result = pipeline.fit_transform(sample_wdi_df)
    assert isinstance(result, pd.DataFrame)
    assert "año" in result.columns
    assert len(result) <= 27  # pipeline end_year=2026: máximo 27 años (2000-2026)


def test_pipeline_rejects_empty_steps():
    with pytest.raises(ValueError, match="al menos un paso"):
        Pipeline([])


def test_pipeline_rejects_duplicate_names():
    with pytest.raises(ValueError, match="únicos"):
        Pipeline([
            ("clean", DataCleaner()),
            ("clean", DataCleaner()),
        ])


def test_transform_before_fit_raises():
    cleaner = DataCleaner()
    with pytest.raises(RuntimeError, match="fit\\(\\)"):
        cleaner.transform(pd.DataFrame({"año": [2000]}))


def test_cleaner_removes_duplicates():
    df = pd.DataFrame({
        "año": [2000, 2000, 2001],
        "val": [1.0, 2.0, 3.0]
    })
    cleaner = DataCleaner()
    result = cleaner.fit_transform(df)
    assert result["año"].nunique() == len(result)
    assert len(result) == 2


def test_cleaner_filters_year_range():
    df = pd.DataFrame({
        "año": [1999, 2000, 2024, 2025],
        "val": [1.0, 2.0, 3.0, 4.0]
    })
    result = DataCleaner(start_year=2000, end_year=2024).fit_transform(df)
    assert result["año"].min() == 2000
    assert result["año"].max() == 2024


def test_imputer_fills_gaps():
    df = pd.DataFrame({
        "año": [2000, 2001, 2002, 2003],
        "val": [10.0, np.nan, np.nan, 40.0]
    })
    imputer = GapImputer(column_strategies={"val": "interpolate"})
    result = imputer.fit_transform(df)
    assert result["val"].isna().sum() == 0
    assert result.loc[result["año"] == 2001, "val"].values[0] == pytest.approx(20.0)


def test_imputer_respects_none_strategy():
    df = pd.DataFrame({
        "año": [2000, 2001, 2002],
        "val": [10.0, np.nan, 30.0]
    })
    imputer = GapImputer(column_strategies={"val": "none"})
    result = imputer.fit_transform(df)
    assert result["val"].isna().sum() == 1


def test_normalizer_output_range(sample_wdi_df):
    normalizer = MinMaxNormalizer(columns=["pib_crecimiento_real_pct"])
    result = normalizer.fit_transform(sample_wdi_df)
    col = result["pib_crecimiento_real_pct"].dropna()
    assert col.min() >= 0.0 - 1e-9
    assert col.max() <= 100.0 + 1e-9


def test_normalizer_inverts_negative_vars():
    df = pd.DataFrame({
        "año": [2000, 2001, 2002],
        "inflacion_deflactor_pib_pct": [10.0, 50.0, 100.0]
    })
    normalizer = MinMaxNormalizer(columns=["inflacion_deflactor_pib_pct"])
    result = normalizer.fit_transform(df)
    # Mayor inflación = peor → debe tener score más BAJO
    scores = result["inflacion_deflactor_pib_pct"].tolist()
    assert scores[0] > scores[2], "Inflación baja debe dar score más alto"


def test_pipeline_repr():
    p = Pipeline([("a", DataCleaner()), ("b", GapImputer())])
    assert "a" in repr(p)
    assert "b" in repr(p)
