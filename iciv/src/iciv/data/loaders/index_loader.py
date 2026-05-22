"""
Loaders para los tres índices compuestos de gobernanza y capital humano:
  - CPI  (Transparency International)
  - IEF  (Heritage Foundation)
  - HDI  (PNUD)

Los tres archivos usan formato largo con columnas:
    año | indicador | valor | pais | fuente

Este módulo los carga y devuelve en formato ancho (una columna por índice)
para que sean compatibles con el pipeline de transformación.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader


class _LongFormatLoader(DataLoader):
    """
    Loader genérico para archivos en formato largo (indicador/valor).
    Subclases solo necesitan declarar el archivo, el SourceID y el
    nombre del indicador a extraer.
    """

    _indicator_name: str  # valor esperado en la columna 'indicador'
    _output_column: str   # nombre de columna en el DataFrame de salida

    def load(self) -> DatasetResult:
        df_raw = self._read_csv()
        df = self._ensure_year_column(df_raw)

        if "indicador" not in df.columns or "valor" not in df.columns:
            raise KeyError(
                f"El archivo {self._data_path.name} debe tener columnas "
                f"'indicador' y 'valor'."
            )

        # Filtrar solo el indicador de interés y pivotar a formato ancho
        mask = df["indicador"] == self._indicator_name
        df_filtered = df[mask][["año", "valor"]].copy()
        df_filtered = df_filtered.rename(columns={"valor": self._output_column})
        df_filtered = self._filter_year_range(df_filtered)
        df_filtered = df_filtered.sort_values("año").reset_index(drop=True)

        missing: list[str] = []
        if df_filtered.empty:
            missing.append(self._output_column)

        return DatasetResult(
            source=self.get_source_id(), df=df_filtered, missing_cols=missing
        )

    def validate(self, result: DatasetResult) -> bool:
        return not result.df.empty and self._output_column in result.df.columns


class CPILoader(_LongFormatLoader):
    """Índice de Percepción de Corrupción — Transparency International."""

    _indicator_name = "cpi_score"
    _output_column = "cpi_score"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_cpi)

    def get_source_id(self) -> SourceID:
        return SourceID.CPI


class IEFLoader(_LongFormatLoader):
    """Índice de Libertad Económica — Heritage Foundation."""

    _indicator_name = "ief_overall_score"
    _output_column = "ief_overall_score"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_ief)

    def get_source_id(self) -> SourceID:
        return SourceID.IEF


class HDILoader(_LongFormatLoader):
    """Índice de Desarrollo Humano — PNUD."""

    _indicator_name = "hdi"
    _output_column = "hdi"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_hdi)

    def get_source_id(self) -> SourceID:
        return SourceID.HDI
