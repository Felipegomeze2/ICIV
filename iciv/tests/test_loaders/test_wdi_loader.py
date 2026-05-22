"""Tests para WDILoader."""

import pytest
import pandas as pd

from iciv.data.loaders import WDILoader
from iciv.data.models import SourceID


def test_source_id():
    loader = WDILoader()
    assert loader.get_source_id() == SourceID.WDI


def test_load_returns_dataset_result(raw_data_available):
    if not raw_data_available:
        pytest.skip("Archivos raw no disponibles — ejecutar 01_ingesta.py primero")
    result = WDILoader().load()
    assert result.source == SourceID.WDI
    assert not result.df.empty
    assert "año" in result.df.columns


def test_year_column_is_int(raw_data_available):
    if not raw_data_available:
        pytest.skip("Archivos raw no disponibles")
    result = WDILoader().load()
    assert result.df["año"].dtype in ("int32", "int64")


def test_years_in_expected_range(raw_data_available):
    if not raw_data_available:
        pytest.skip("Archivos raw no disponibles")
    result = WDILoader().load()
    assert result.df["año"].min() >= 2000
    assert result.df["año"].max() <= 2026  # pipeline end_year configurado en settings.yaml


def test_no_duplicate_years(raw_data_available):
    if not raw_data_available:
        pytest.skip("Archivos raw no disponibles")
    result = WDILoader().load()
    assert result.df["año"].nunique() == len(result.df)


def test_validate_passes(raw_data_available):
    if not raw_data_available:
        pytest.skip("Archivos raw no disponibles")
    loader = WDILoader()
    result = loader.load()
    assert loader.validate(result) is True


def test_coverage_reasonable(raw_data_available):
    if not raw_data_available:
        pytest.skip("Archivos raw no disponibles")
    result = WDILoader().load()
    assert result.coverage_pct >= 80.0  # WDI debería tener ≥80% cobertura


def test_file_not_found_raises():
    from pathlib import Path
    from iciv.data.loaders.base import DataLoader
    loader = WDILoader()
    loader._data_path = Path("/nonexistent/file.csv")
    with pytest.raises(FileNotFoundError, match="fetch_"):
        loader.load()
