"""
Loader para UNCTAD LSCI — Liner Shipping Connectivity Index Venezuela.

Lee data/raw/unctad.csv generado por scripts/fetch_unctad.py.
"""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

_REQUIRED = ["lsci_conectividad_maritima"]


class UNCTADLoader(DataLoader):
    """Loader para el LSCI (Liner Shipping Connectivity Index) de UNCTAD."""

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_unctad)

    def get_source_id(self) -> SourceID:
        return SourceID.UNCTAD

    def load(self) -> DatasetResult:
        df = self._read_csv()
        df = self._ensure_year_column(df)
        df = self._filter_year_range(df)
        # El CSV incluye una columna `fuente` para auditoría; el contrato del
        # pipeline exige solo año + variables, así que se filtra aquí.
        keep = ["año"] + [c for c in _REQUIRED if c in df.columns]
        df = df[keep].sort_values("año").reset_index(drop=True)
        missing = self._check_required_columns(df, _REQUIRED, "UNCTAD")
        return DatasetResult(source=self.get_source_id(), df=df, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        if result.df.empty:
            return False
        return "lsci_conectividad_maritima" in result.df.columns
