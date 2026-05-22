"""Loader para el FMI — IMF DataMapper."""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

_REQUIRED_COLS = [
    "año",
    "desempleo_pct",
    "inflacion_deflactor_pib_pct",
]

# cuenta_corriente_pct_pib es opcional: solo llega hasta 2016
_OPTIONAL_COLS = ["cuenta_corriente_pct_pib"]


class IMFLoader(DataLoader):
    """
    Carga el archivo pivot del FMI.

    Nota metodológica:
    - `inflacion_deflactor_pib_pct` es la variable de inflación principal
      del ICIV, ya que el IPC del WDI tiene solo 32% de cobertura.
    - `cuenta_corriente_pct_pib` está disponible solo hasta 2016.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_imf)

    def get_source_id(self) -> SourceID:
        return SourceID.IMF

    def load(self) -> DatasetResult:
        df_raw = self._read_csv()
        df = self._ensure_year_column(df_raw)
        df = self._filter_year_range(df)
        df = df.sort_values("año").reset_index(drop=True)

        missing = self._check_required_columns(df, _REQUIRED_COLS, "IMF")
        return DatasetResult(source=self.get_source_id(), df=df, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        df = result.df
        if df.empty:
            return False
        if "inflacion_deflactor_pib_pct" not in df.columns:
            return False
        if "desempleo_pct" not in df.columns:
            return False
        return True
