"""
Loader para datos FRED (Federal Reserve Bank of St. Louis).

Lee data/raw/fred.csv en formato ancho (año + columnas de series).
Series esperadas: wti_precio_usd, tasa_fed_funds_pct
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

_REQUIRED = ["wti_precio_usd", "tasa_fed_funds_pct"]


class FREDLoader(DataLoader):
    """Loader para series FRED — WTI Oil Price y Fed Funds Rate."""

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_fred)

    def get_source_id(self) -> SourceID:
        return SourceID.FRED

    def load(self) -> DatasetResult:
        df = self._read_csv()
        df = self._ensure_year_column(df)
        df = self._filter_year_range(df)
        df = df.sort_values("año").reset_index(drop=True)
        missing = self._check_required_columns(df, _REQUIRED, "FRED")
        return DatasetResult(source=self.get_source_id(), df=df, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        if result.df.empty:
            return False
        present = [c for c in _REQUIRED if c in result.df.columns]
        return len(present) >= 1
