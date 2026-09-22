"""Regression for Actions run 38: monthly period starts are not release dates."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("pulse_gate", Path(__file__).resolve().parents[1] / "scripts/check_pulse_inputs.py")
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)

@pytest.mark.parametrize("year,month,today,expected", [
    (2026,8,"2026-09-21",0),  # actual failure: 21 days after August closes
    (2026,7,"2026-09-21",1),  # 52 days: still blocks stale observations
    (2026,8,"2026-10-20",0),  # exact 50-day boundary
    (2026,8,"2026-10-21",1),
    (2026,9,"2026-09-21",0),  # current partial month
    (2026,10,"2026-09-21",1), # future data must not pass
    (2024,2,"2024-04-19",0),  # leap February, 50 days
    (2024,2,"2024-04-20",1),
])
def test_month_end_freshness(tmp_path, monkeypatch, year, month, today, expected):
    pd.DataFrame({"año":[year],"mes":[month],"valor":[1.0]}).to_csv(tmp_path / "source.csv",index=False)
    monkeypatch.setattr(gate,"settings",SimpleNamespace(paths=SimpleNamespace(data_raw=tmp_path)))
    monkeypatch.setattr(gate,"RULES",(gate.SourceRule("source.csv","Test",50),))
    assert gate.check_inputs(pd.Timestamp(today)) == expected

def test_missing_required_source_still_blocks(tmp_path,monkeypatch):
    monkeypatch.setattr(gate,"settings",SimpleNamespace(paths=SimpleNamespace(data_raw=tmp_path)))
    monkeypatch.setattr(gate,"RULES",(gate.SourceRule("absent.csv","Test",50),))
    assert gate.check_inputs(pd.Timestamp("2026-09-21")) == 1
