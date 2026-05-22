"""
Loader para indicadores de salud de la OMS (WHO GHO).

Lee data/raw/who.csv en formato largo (año|indicador|valor|pais|fuente).
Columnas de salida:
  - esperanza_vida_anos       : esperanza de vida al nacer, ambos sexos (años)
  - mortalidad_infantil_x1000 : tasa mortalidad infantil 0-11m (muertes x 1.000 NV)
"""

from __future__ import annotations

import pandas as pd

from iciv.config import Settings
from iciv.data.models import DatasetResult, SourceID
from .base import DataLoader

_INDICATORS = ["esperanza_vida_anos", "mortalidad_infantil_x1000"]


class WHOLoader(DataLoader):
    """
    Carga data/raw/who.csv generado por scripts/fetch_who.py.

    El archivo contiene dos indicadores en formato largo.
    El loader los pivota a formato ancho (una columna por indicador).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_who)

    def get_source_id(self) -> SourceID:
        return SourceID.WHO

    def load(self) -> DatasetResult:
        df_raw = self._read_csv()

        if df_raw.empty or "indicador" not in df_raw.columns:
            return DatasetResult(
                source=self.get_source_id(),
                df=pd.DataFrame(columns=["año"] + _INDICATORS),
                missing_cols=_INDICATORS,
            )

        df = self._ensure_year_column(df_raw)
        df = self._filter_year_range(df)

        # Pivotar formato largo → ancho
        df_wide = (
            df[df["indicador"].isin(_INDICATORS)]
            .pivot_table(index="año", columns="indicador", values="valor", aggfunc="first")
            .reset_index()
        )
        df_wide.columns.name = None

        # Asegurar que todas las columnas esperadas existen
        for col in _INDICATORS:
            if col not in df_wide.columns:
                df_wide[col] = None

        df_wide = df_wide.sort_values("año").reset_index(drop=True)
        missing = [col for col in _INDICATORS if df_wide[col].isna().all()]

        return DatasetResult(source=self.get_source_id(), df=df_wide, missing_cols=missing)

    def validate(self, result: DatasetResult) -> bool:
        if result.df.empty:
            return False
        return any(
            col in result.df.columns and result.df[col].notna().any()
            for col in _INDICATORS
        )
