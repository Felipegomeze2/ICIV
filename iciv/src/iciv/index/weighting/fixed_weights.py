"""
Estrategia de pesos fijos — definidos en DIMENSIONS o por el usuario.

Caso de uso principal: pesos derivados del proceso AHP con expertos,
o los pesos del documento maestro del ICIV como punto de partida.
"""

from __future__ import annotations

import pandas as pd
import math

from iciv.index.dimensions import DIMENSIONS
from iciv.data.models import DimensionID
from .base import WeightingStrategy


class FixedWeights(WeightingStrategy):
    """
    Usa los pesos definidos estáticamente en DIMENSIONS.

    Los pesos se calculan como:
        peso_final_variable = peso_dim_iciv × peso_variable_dentro_dim

    Ejemplo: inflacion en D1:
        0.30 (peso D1) × 0.35 (peso inflacion en D1) = 0.105 (peso final)

    Args:
        dimensions: configuración de dimensiones. Si None, usa DIMENSIONS global.
        override:   dict {columna: peso_final} para sobreescribir pesos específicos
                    sin modificar DIMENSIONS. Útil para análisis de sensibilidad.
    """

    def __init__(
        self,
        dimensions: dict | None = None,
        override: dict[str, float] | None = None,
    ) -> None:
        self._dimensions = dimensions or DIMENSIONS
        self._override = override or {}
        self._weights: dict[str, float] = {}

    def compute_weights(self, df: pd.DataFrame) -> dict[str, float]:
        weights: dict[str, float] = {}

        for dim in self._dimensions.values():
            for var in dim.variables:
                weights[var.column] = dim.iciv_weight * var.weight

        # Aplicar overrides
        unknown = set(self._override) - set(weights)
        if unknown:
            raise ValueError(f"Overrides fuera del catálogo de variables: {sorted(unknown)}")
        weights.update(self._override)
        if any(not math.isfinite(w) or w < 0 for w in weights.values()):
            raise ValueError("Los pesos deben ser finitos y no negativos")

        # El universo no depende de las columnas disponibles en el dataset.
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("Los pesos deben sumar un valor positivo")
        weights = {k: v / total for k, v in weights.items()}

        self._weights = weights
        return weights

    def get_method_name(self) -> str:
        return "Pesos fijos declarados (incluye overrides explícitos)"

    def get_weights_table(self) -> pd.DataFrame:
        """Tabla de pesos con dimensión y peso final — útil para la tesis."""
        weights = self.compute_weights(pd.DataFrame())
        rows = []
        for dim in self._dimensions.values():
            dim_weight = sum(weights[v.column] for v in dim.variables)
            for var in dim.variables:
                rows.append({
                    "dimensión": dim.name,
                    "peso_dim": dim_weight,
                    "variable": var.column,
                    "peso_en_dim": weights[var.column] / dim_weight if dim_weight else 0.0,
                    "peso_final": weights[var.column],
                })
        return pd.DataFrame(rows).sort_values("peso_final", ascending=False)
