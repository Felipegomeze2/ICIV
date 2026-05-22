"""
DataCleaner — estandarización y limpieza estructural de DataFrames.

Responsabilidad única: garantizar tipos correctos, eliminar duplicados
y asegurar que el DataFrame tenga la forma esperada por el pipeline.
No imputa ni normaliza — eso lo hacen los transformers siguientes.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from .base import BaseTransformer

logger = logging.getLogger(__name__)


class DataCleaner(BaseTransformer):
    """
    Limpieza estructural de un DataFrame de series temporales.

    Operaciones aplicadas (en orden):
    1. Coerce `año` a int y elimina filas sin año
    2. Elimina filas duplicadas por año (conserva la primera)
    3. Filtra al rango de años especificado
    4. Ordena por año ascendente
    5. Resetea el índice

    Nota: este transformer es stateless (fit() no aprende nada),
    pero mantiene la interfaz fit/transform por consistencia con el pipeline.
    """

    def __init__(
        self,
        start_year: int = 2000,
        end_year: int = 2024,
        year_col: str = "año",
    ) -> None:
        super().__init__()
        self.start_year = start_year
        self.end_year = end_year
        self.year_col = year_col

    def fit(self, df: pd.DataFrame) -> "DataCleaner":
        # Stateless: nada que aprender
        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self._assert_fitted()
        result = df.copy()

        # 1. Coerce año a int, eliminar NaN
        result[self.year_col] = pd.to_numeric(result[self.year_col], errors="coerce")
        n_before = len(result)
        result = result.dropna(subset=[self.year_col])
        result[self.year_col] = result[self.year_col].astype(int)
        if len(result) < n_before:
            logger.warning("  Eliminadas %d filas con año inválido", n_before - len(result))

        # 2. Deduplicar por año
        dupes = result.duplicated(subset=[self.year_col], keep="first").sum()
        if dupes:
            logger.warning("  Eliminados %d años duplicados (conservando primero)", dupes)
            result = result.drop_duplicates(subset=[self.year_col], keep="first")

        # 3. Filtrar rango
        result = result[
            (result[self.year_col] >= self.start_year) &
            (result[self.year_col] <= self.end_year)
        ]

        # 4–5. Ordenar y resetear índice
        result = result.sort_values(self.year_col).reset_index(drop=True)

        logger.debug(
            "  DataCleaner: %d → %d filas, años %s–%s",
            n_before,
            len(result),
            result[self.year_col].min() if not result.empty else "?",
            result[self.year_col].max() if not result.empty else "?",
        )
        return result
