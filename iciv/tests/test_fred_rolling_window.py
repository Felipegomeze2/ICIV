"""Regression: the ICE BofA rolling window on FRED must not block the whole FRED file.

Between 2026-10-09 and 2026-10-28 the window dropped 2023-09 from BAMLEMCBPIOAS,
safe_save rejected fred_monthly.csv for "losing" that month, and FEDFUNDS stayed
stale until the Pulse gate failed (Actions run 45).
"""
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

from iciv.utils.safe_save import NoDataError, save_dataframe

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("fred_monthly", ROOT / "scripts/fetch_fred_monthly.py")
fred = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fred)


def _rows(variable, months, value=1.0):
    return pd.DataFrame({"año": [2023] * len(months), "mes": months, "variable": variable,
                         "valor": value, "fuente": "FRED"})


def test_rolling_window_months_are_kept_and_save_passes(tmp_path):
    old = pd.concat([_rows("em_bond_spread_pct", [9, 10, 11]), _rows("wti_precio_usd", [9, 10, 11])])
    path = tmp_path / "fred_monthly.csv"
    old.to_csv(path, index=False)
    new = pd.concat([_rows("em_bond_spread_pct", [10, 11, 12], 2.0), _rows("wti_precio_usd", [9, 10, 11, 12], 2.0)])

    merged = fred._retain_rolling_window(new, previous=path)

    em = merged[merged.variable == "em_bond_spread_pct"].set_index("mes")["valor"]
    assert em.to_dict() == {10: 2.0, 11: 2.0, 12: 2.0, 9: 1.0}  # new values win; only the lost month is kept
    assert save_dataframe(merged, path)


def test_other_series_still_rejected_when_they_lose_a_month(tmp_path):
    path = tmp_path / "fred_monthly.csv"
    _rows("wti_precio_usd", [9, 10, 11]).to_csv(path, index=False)
    new = _rows("wti_precio_usd", [10, 11, 12], 2.0)

    merged = fred._retain_rolling_window(new, previous=path)

    with pytest.raises(NoDataError):
        save_dataframe(merged, path)
