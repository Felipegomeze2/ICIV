"""Loader para EIA — U.S. Energy Information Administration."""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

_REQUIRED_COLS = [
    "año",
    "petroleo_crudo_produccion_tbpd",
    "gas_natural_produccion_bcf",
    "electricidad_generacion_bkwh",
]


class EIALoader(DataLoader):
    """
    Carga el archivo pivot de energía de la EIA.

    La EIA tiene cobertura completa 2000–2024 y es la fuente más
    confiable del dataset. No se esperan gaps.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_eia)

    def get_source_id(self) -> SourceID:
        return SourceID.EIA

    def load(self) -> DatasetResult:
        df_raw = self._read_csv()
        df = self._ensure_year_column(df_raw)
        df = self._filter_year_range(df)
        df = df.sort_values("año").reset_index(drop=True)

        missing = self._check_required_columns(df, _REQUIRED_COLS, "EIA")
        return DatasetResult(source=self.get_source_id(), df=df, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        df = result.df
        if df.empty:
            return False
        # EIA debería tener al menos 20 años (serie prácticamente completa)
        if len(result.available_years) < 20:
            return False
        if "petroleo_crudo_produccion_tbpd" not in df.columns:
            return False
        return True
