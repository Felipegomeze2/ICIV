"""Loader para The Guardian — artículos anuales y tono de titulares sobre Venezuela."""

from __future__ import annotations

import pandas as pd

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

_REQUIRED_COLS = [
    "año",
    "guardian_articulos_venezuela",
    "guardian_tono_titulares",
]


class GuardianLoader(DataLoader):
    """
    Carga data/raw/guardian.csv generado por scripts/fetch_guardian.py.

    Columnas esperadas:
      - guardian_articulos_venezuela : conteo anual de artículos
      - guardian_tono_titulares      : promedio VADER compound de titulares (-1..+1)

    Cobertura: 2000–2024 (The Guardian cubre desde 1999).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_guardian)

    def get_source_id(self) -> SourceID:
        return SourceID.GUARDIAN

    def load(self) -> DatasetResult:
        df_raw = self._read_csv()
        df = self._ensure_year_column(df_raw)
        df = self._filter_year_range(df)
        df = df.sort_values("año").reset_index(drop=True)

        missing = self._check_required_columns(df, _REQUIRED_COLS, "Guardian")
        return DatasetResult(source=self.get_source_id(), df=df, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        df = result.df
        if df.empty:
            return False
        return (
            "guardian_articulos_venezuela" in df.columns
            and df["guardian_articulos_venezuela"].notna().any()
        )
