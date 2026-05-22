"""
MinMaxNormalizer — normalización de variables a escala 0–100.

Responsabilidad única: llevar todas las variables del ICIV a una
escala común para que sean comparables y combinables.

Método: Min-Max Rescaling (OCDE Handbook, 2008)
  - Variable positiva: score = (x - min) / (max - min) × 100
  - Variable negativa: score = (max - x) / (max - min) × 100

Los parámetros min/max se aprenden en fit() sobre el período histórico
y se almacenan para aplicarlos a datos nuevos sin recalcular.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from iciv.data.catalog import CATALOG, get_negative_variables
from .base import BaseTransformer

logger = logging.getLogger(__name__)


class MinMaxNormalizer(BaseTransformer):
    """
    Normalización Min-Max a escala 0–100 con inversión automática
    para variables de dirección negativa.

    Args:
        columns:         lista de columnas a normalizar. Si None, normaliza
                         todas las columnas numéricas excepto 'año'.
        negative_vars:   columnas cuya dirección es negativa (se invierten).
                         Si None, se deriva automáticamente del CATALOG.
        clip:            si True, recorta valores fuera del rango [0, 100]
                         que pueden ocurrir cuando datos nuevos superan los
                         extremos históricos.

    Atributos aprendidos (disponibles tras fit()):
        min_:   dict {columna: valor_mínimo}
        max_:   dict {columna: valor_máximo}
        range_: dict {columna: max - min}
    """

    def __init__(
        self,
        columns: list[str] | None = None,
        negative_vars: list[str] | None = None,
        clip: bool = True,
    ) -> None:
        super().__init__()
        self.columns = columns
        self.negative_vars = negative_vars if negative_vars is not None else get_negative_variables()
        self.clip = clip

        # Parámetros aprendidos en fit()
        self.min_: dict[str, float] = {}
        self.max_: dict[str, float] = {}
        self.range_: dict[str, float] = {}

    def fit(self, df: pd.DataFrame) -> "MinMaxNormalizer":
        """Aprende min y max de cada columna numérica."""
        cols = self._resolve_columns(df)
        for col in cols:
            valid = df[col].dropna()
            if valid.empty:
                logger.warning("  Columna '%s' está completamente vacía — se omite", col)
                continue
            self.min_[col] = float(valid.min())
            self.max_[col] = float(valid.max())
            self.range_[col] = self.max_[col] - self.min_[col]
            if self.range_[col] == 0:
                logger.warning(
                    "  Columna '%s' tiene rango 0 (todos los valores iguales) — "
                    "producirá NaN al normalizar",
                    col,
                )
        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica normalización Min-Max. Requiere haber llamado fit()."""
        self._assert_fitted()
        result = df.copy()
        cols = self._resolve_columns(df)

        for col in cols:
            if col not in self.min_:
                logger.warning("  Columna '%s' no fue ajustada en fit() — se omite", col)
                continue

            rng = self.range_[col]
            if rng == 0:
                result[col] = np.nan
                continue

            is_negative = col in self.negative_vars

            if is_negative:
                # Mayor valor = peor clima → invertir
                result[col] = (self.max_[col] - result[col]) / rng * 100
            else:
                result[col] = (result[col] - self.min_[col]) / rng * 100

            if self.clip:
                result[col] = result[col].clip(0, 100)

        return result

    def get_params_table(self) -> pd.DataFrame:
        """Devuelve tabla de parámetros aprendidos, útil para el reporte."""
        self._assert_fitted()
        rows = []
        for col in self.min_:
            direction = "negativa" if col in self.negative_vars else "positiva"
            rows.append({
                "variable": col,
                "min_histórico": round(self.min_[col], 4),
                "max_histórico": round(self.max_[col], 4),
                "rango": round(self.range_[col], 4),
                "dirección": direction,
            })
        return pd.DataFrame(rows)

    def _resolve_columns(self, df: pd.DataFrame) -> list[str]:
        """Determina qué columnas normalizar."""
        if self.columns is not None:
            return [c for c in self.columns if c in df.columns]
        return [
            c for c in df.select_dtypes(include="number").columns
            if c != "año"
        ]
