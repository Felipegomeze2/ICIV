"""Regression checks for scientific snapshot comparison and non-destructive output."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("reproduce_release", Path(__file__).parents[1] / "scripts/reproduce_release.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_comparison_rejects_missingness_and_changed_values(tmp_path):
    expected, actual = tmp_path / "expected.csv", tmp_path / "actual.csv"
    expected.write_text("year,score\n2025,26.01\n2026,\n")
    actual.write_text("year,score\n2025,26.01\n2026,0\n")
    with pytest.raises(ValueError, match="Missingness"):
        module.compare_csv(expected, actual)
    actual.write_text("year,score\n2025,42.33\n2026,\n")
    with pytest.raises(ValueError, match="Values"):
        module.compare_csv(expected, actual)


def test_existing_output_is_never_replaced(tmp_path):
    sentinel = tmp_path / "original.txt"
    sentinel.write_text("preserve")
    with pytest.raises(ValueError, match="new directory"):
        module.prepare(tmp_path / "release", tmp_path)
    assert sentinel.read_text() == "preserve"
