"""
GapImputer — estrategias de imputación para gaps en series temporales.

Responsabilidad única: rellenar valores nulos con la estrategia
apropiada por columna. Registra qué valores fueron imputados.

Estrategias disponibles:
  - 'interpolate'  : interpolación lineal (default para series continuas)
  - 'forward_fill' : propagación hacia adelante (para índices categóricos)
  - 'backward_fill': propagación hacia atrás
  - 'none'         : no imputar (dejar NaN — para columnas con gaps irreducibles)
"""

from __future__ import annotations

import logging
from typing import Literal

import pandas as pd
import numpy as np

from .base import BaseTransformer

logger = logging.getLogger(__name__)

ImputeStrategy = Literal["interpolate", "forward_fill", "backward_fill", "none"]

# Estrategias por defecto basadas en los hallazgos del EDA
# REGLA: "none" para variables donde faltan años al INICIO o FIN de la serie
#         (sin dato real en ese extremo → no inventar mediante extrapolación).
#         "interpolate" solo llena gaps INTERNOS entre dos datos reales.
DEFAULT_STRATEGIES: dict[str, ImputeStrategy] = {
    "pib_crecimiento_real_pct":       "interpolate",
    "reservas_internacionales_usd":   "none",         # Venezuela no reporta al WB desde 2018
    "tipo_cambio_oficial_lcu_usd":    "none",         # lag WDI 2025-2026 → NaN honesto
    "cpi_score":                      "interpolate",
    "hdi":                            "interpolate",
    "cuenta_corriente_pct_pib":       "none",         # suspendió reporte al FMI
}


class GapImputer(BaseTransformer):
    """
    Imputa valores nulos en series temporales usando estrategias por columna.

    Args:
        column_strategies: dict {nombre_columna: estrategia}. Las columnas
            no especificadas usan `default_strategy`.
        default_strategy:  estrategia para columnas sin regla específica.
        limit:             máximo de períodos consecutivos a imputar.
            Evita imputar gaps muy largos que distorsionarían el análisis.

    Ejemplo:
        imputer = GapImputer(
            column_strategies={"cpi_score": "interpolate"},
            default_strategy="interpolate",
            limit=3,
        )
        df_clean = imputer.fit_transform(df)
        # Acceder al log de imputaciones:
        print(imputer.imputation_log_)
    """

    def __init__(
        self,
        column_strategies: dict[str, ImputeStrategy] | None = None,
        default_strategy: ImputeStrategy = "interpolate",
        limit: int | None = 4,
    ) -> None:
        super().__init__()
        self.column_strategies = {**DEFAULT_STRATEGIES, **(column_strategies or {})}
        self.default_strategy = default_strategy
        self.limit = limit
        self.imputation_log_: dict[str, int] = {}  # {columna: n_valores_imputados}

    def fit(self, df: pd.DataFrame) -> "GapImputer":
        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self._assert_fitted()
        result = df.copy()
        self.imputation_log_ = {}

        numeric_cols = result.select_dtypes(include="number").columns.tolist()
        if "año" in numeric_cols:
            numeric_cols.remove("año")

        for col in numeric_cols:
            n_null_before = result[col].isna().sum()
            if n_null_before == 0:
                continue

            strategy = self.column_strategies.get(col, self.default_strategy)

            if strategy == "interpolate":
                # limit_area="inside" garantiza que SOLO se rellenan NaN que tienen
                # datos reales en AMBOS extremos (gaps internos). Nunca extrapola
                # hacia el inicio ni el fin de la serie — eso crearía datos artificiales.
                result[col] = result[col].interpolate(
                    method="linear", limit=self.limit, limit_area="inside"
                )
            elif strategy == "forward_fill":
                result[col] = result[col].ffill(limit=self.limit)
            elif strategy == "backward_fill":
                result[col] = result[col].bfill(limit=self.limit)
            elif strategy == "none":
                pass  # dejar NaN deliberadamente

            n_imputed = n_null_before - result[col].isna().sum()
            if n_imputed > 0:
                self.imputation_log_[col] = int(n_imputed)
                logger.info(
                    "  Imputados %d valores en '%s' (estrategia: %s)",
                    n_imputed, col, strategy,
                )

        return result

    def get_imputation_summary(self) -> pd.DataFrame:
        """Resumen tabular de las imputaciones realizadas."""
        if not self.imputation_log_:
            return pd.DataFrame(columns=["columna", "valores_imputados", "estrategia"])
        rows = [
            {
                "columna": col,
                "valores_imputados": n,
                "estrategia": self.column_strategies.get(col, self.default_strategy),
            }
            for col, n in self.imputation_log_.items()
        ]
        return pd.DataFrame(rows).sort_values("valores_imputados", ascending=False)
