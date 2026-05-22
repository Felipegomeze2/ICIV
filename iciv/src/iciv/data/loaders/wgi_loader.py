"""Loader para el Banco Mundial — World Governance Indicators (WGI)."""

from __future__ import annotations

import pandas as pd

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

# Columnas de percentil (escala 0–100) — usamos .SC, no .EST
_SC_COLS = [
    "GOV_WGI_CC.SC",   # Control de Corrupción
    "GOV_WGI_GE.SC",   # Efectividad del Gobierno
    "GOV_WGI_PV.SC",   # Estabilidad Política
    "GOV_WGI_RL.SC",   # Estado de Derecho
    "GOV_WGI_RQ.SC",   # Calidad Regulatoria
    "GOV_WGI_VA.SC",   # Voz y Rendición de Cuentas
]


class WGILoader(DataLoader):
    """
    Carga el archivo pivot del WGI y calcula el promedio de los 6 indicadores.

    Devuelve tanto las columnas individuales (para análisis) como
    `wgi_promedio_sc` (para el índice compuesto).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_wgi)

    def get_source_id(self) -> SourceID:
        return SourceID.WGI

    def load(self) -> DatasetResult:
        df_raw = self._read_csv()
        df = self._ensure_year_column(df_raw)
        df = self._filter_year_range(df)

        missing = self._check_required_columns(df, _SC_COLS, "WGI")

        # Calcular promedio de los 6 indicadores disponibles
        available_sc = [c for c in _SC_COLS if c in df.columns]
        if available_sc:
            df["wgi_promedio_sc"] = df[available_sc].mean(axis=1)

        df = df.sort_values("año").reset_index(drop=True)
        return DatasetResult(source=self.get_source_id(), df=df, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        df = result.df
        if df.empty:
            return False
        present_sc = [c for c in _SC_COLS if c in df.columns]
        if len(present_sc) < 3:
            return False
        return True
