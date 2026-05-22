"""
Loader para OpenSky / conectividad aérea — Venezuela.

Lee data/raw/opensky.csv generado por scripts/fetch_opensky.py.
"""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

_REQUIRED = ["vuelos_aerolineas_int_count"]


class OpenSkyLoader(DataLoader):
    """Loader para el conteo de aerolíneas internacionales con servicio a Venezuela."""

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_opensky)

    def get_source_id(self) -> SourceID:
        return SourceID.OPENSKY

    def load(self) -> DatasetResult:
        df = self._read_csv()
        df = self._ensure_year_column(df)
        df = self._filter_year_range(df)
        df = df.sort_values("año").reset_index(drop=True)
        missing = self._check_required_columns(df, _REQUIRED, "OPENSKY")
        return DatasetResult(source=self.get_source_id(), df=df, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        if result.df.empty:
            return False
        return "vuelos_aerolineas_int_count" in result.df.columns
