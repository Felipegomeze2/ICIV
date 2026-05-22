"""Loader para el Banco Mundial — World Development Indicators (WDI)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

_REQUIRED_COLS = [
    "año",
    "pib_crecimiento_real_pct",
    "pib_nominal_usd",
    "pib_per_capita_usd",
    "ied_neta_usd",
    "reservas_internacionales_usd",
    "exportaciones_pct_pib",
    "acceso_electricidad_pct",
]


class WDILoader(DataLoader):
    """
    Carga el archivo pivot del WDI desde data/raw/banco_mundial/.

    El archivo esperado es banco_mundial_wdi_pivot.csv, generado por
    01_ingesta.py con una columna por indicador y filas por año.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_wdi)

    def get_source_id(self) -> SourceID:
        return SourceID.WDI

    def load(self) -> DatasetResult:
        df_raw = self._read_csv()
        df = self._ensure_year_column(df_raw)
        df = self._filter_year_range(df)
        df = df.sort_values("año").reset_index(drop=True)

        missing = self._check_required_columns(df, _REQUIRED_COLS, "WDI")
        return DatasetResult(source=self.get_source_id(), df=df, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        df = result.df
        if df.empty:
            return False
        if "año" not in df.columns:
            return False
        # Mínimo: necesitamos PIB nominal para cualquier cálculo
        if "pib_nominal_usd" not in df.columns:
            return False
        return True
