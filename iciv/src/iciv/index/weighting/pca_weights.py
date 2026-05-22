"""
Estrategia de pesos por PCA — derivados estadísticamente.

Alternativa objetiva a los pesos fijos del AHP. El peso de cada variable
se determina por su contribución a la varianza explicada del primer
componente principal, sin juicio subjetivo de expertos.

Referencia: OCDE Handbook on Constructing Composite Indicators (2008), Cap. 6.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA  # type: ignore
from sklearn.preprocessing import StandardScaler  # type: ignore

from .base import WeightingStrategy

logger = logging.getLogger(__name__)


class PCAWeights(WeightingStrategy):
    """
    Calcula pesos usando el primer componente principal (PC1).

    El peso de cada variable es el cuadrado de su carga en PC1,
    normalizado para que todos los pesos sumen 1.0.

    Args:
        exclude_cols: columnas a excluir del PCA (ej. 'año').
        min_variance_explained: umbral mínimo de varianza que PC1 debe
            explicar. Si no se alcanza, emite un warning.

    Atributos tras compute_weights():
        variance_explained_: fracción de varianza explicada por PC1
        loadings_:           cargas de cada variable en PC1
    """

    def __init__(
        self,
        exclude_cols: list[str] | None = None,
        min_variance_explained: float = 0.40,
    ) -> None:
        self.exclude_cols = exclude_cols or ["año"]
        self.min_variance_explained = min_variance_explained
        self.variance_explained_: float = 0.0
        self.loadings_: dict[str, float] = {}

    def compute_weights(self, df: pd.DataFrame) -> dict[str, float]:
        cols = [
            c for c in df.select_dtypes(include="number").columns
            if c not in self.exclude_cols
        ]
        df_num = df[cols].dropna(axis=0, how="any")

        if len(df_num) < 5:
            logger.warning(
                "PCAWeights: muy pocos registros completos (%d). "
                "Considera usar FixedWeights en su lugar.", len(df_num)
            )

        scaler = StandardScaler()
        X = scaler.fit_transform(df_num)

        pca = PCA(n_components=1)
        pca.fit(X)

        self.variance_explained_ = float(pca.explained_variance_ratio_[0])
        loadings = pca.components_[0]

        if self.variance_explained_ < self.min_variance_explained:
            logger.warning(
                "PC1 explica solo %.1f%% de la varianza (umbral: %.1f%%). "
                "Los pesos PCA pueden no ser representativos.",
                self.variance_explained_ * 100,
                self.min_variance_explained * 100,
            )

        # Pesos = cuadrado de las cargas, normalizados a 1.0
        weights_raw = loadings ** 2
        total = weights_raw.sum()
        weights_norm = weights_raw / total if total > 0 else weights_raw

        self.loadings_ = dict(zip(cols, loadings.tolist()))
        weights = dict(zip(cols, weights_norm.tolist()))

        logger.info(
            "PCAWeights: PC1 explica %.1f%% de varianza con %d variables",
            self.variance_explained_ * 100, len(cols),
        )
        return weights

    def get_method_name(self) -> str:
        return f"PCA (PC1, varianza explicada: {self.variance_explained_*100:.1f}%)"
