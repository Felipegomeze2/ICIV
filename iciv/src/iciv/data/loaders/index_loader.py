"""Loaders para indices estaticos vigentes: CPI y HDI."""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader


class _LongFormatLoader(DataLoader):
    """Loader generico para CSV largo: año, indicador, valor, pais, fuente."""

    _indicator_name: str
    _output_column: str

    def load(self) -> DatasetResult:
        df_raw = self._read_csv()
        df = self._ensure_year_column(df_raw)

        if "indicador" not in df.columns or "valor" not in df.columns:
            raise KeyError(
                f"El archivo {self._data_path.name} debe tener columnas "
                f"'indicador' y 'valor'."
            )

        mask = df["indicador"] == self._indicator_name
        df_filtered = df[mask][["año", "valor"]].copy()
        df_filtered = df_filtered.rename(columns={"valor": self._output_column})
        df_filtered = self._filter_year_range(df_filtered)
        df_filtered = df_filtered.sort_values("año").reset_index(drop=True)

        missing: list[str] = []
        if df_filtered.empty:
            missing.append(self._output_column)

        return DatasetResult(source=self.get_source_id(), df=df_filtered, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        return not result.df.empty and self._output_column in result.df.columns


class CPILoader(_LongFormatLoader):
    """CPI comparable desde 2012; el archivo histórico previo se conserva.

    Cambiar la escala 0–10 a 0–100 no resuelve la ruptura metodológica de
    Transparency International. No se empalman ambos regímenes en el índice.
    """

    _indicator_name = "cpi_score"
    _output_column = "cpi_score"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_cpi)

    def get_source_id(self) -> SourceID:
        return SourceID.CPI

    def load(self) -> DatasetResult:
        result = super().load()
        comparable = result.df.loc[result.df["año"] >= 2012].reset_index(drop=True)
        return DatasetResult(
            source=self.get_source_id(), df=comparable,
            missing_cols=[self._output_column] if comparable.empty else [],
        )


class HDILoader(_LongFormatLoader):
    """Human Development Index, UNDP."""

    _indicator_name = "hdi"
    _output_column = "hdi"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_hdi)

    def get_source_id(self) -> SourceID:
        return SourceID.HDI
