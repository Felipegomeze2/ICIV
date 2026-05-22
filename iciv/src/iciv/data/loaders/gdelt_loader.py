"""Loader para GDELT — tono y volumen de cobertura internacional sobre Venezuela."""

from __future__ import annotations

import pandas as pd

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

_REQUIRED_COLS = ["año", "gdelt_tono_noticias", "gdelt_cobertura_vol"]


class GDELTLoader(DataLoader):
    """
    Carga data/raw/gdelt.csv generado por scripts/fetch_gdelt.py.

    Cobertura esperada: 2015–2024 (GDELT DOC 2.0 API).
    Años anteriores quedan como NaN y son manejados por el GapImputer.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_gdelt)

    def get_source_id(self) -> SourceID:
        return SourceID.GDELT

    def load(self) -> DatasetResult:
        df_raw = self._read_csv()
        df = self._ensure_year_column(df_raw)
        df = self._filter_year_range(df)
        df = df.sort_values("año").reset_index(drop=True)

        missing = self._check_required_columns(df, _REQUIRED_COLS, "GDELT")
        return DatasetResult(source=self.get_source_id(), df=df, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        df = result.df
        if df.empty:
            return False
        # Aceptamos si al menos una de las dos columnas tiene algún dato
        has_tone = "gdelt_tono_noticias" in df.columns and df["gdelt_tono_noticias"].notna().any()
        has_vol  = "gdelt_cobertura_vol" in df.columns  and df["gdelt_cobertura_vol"].notna().any()
        return has_tone or has_vol
