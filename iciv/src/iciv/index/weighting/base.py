"""Contrato abstracto para estrategias de ponderación del ICIV."""

from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd


class WeightingStrategy(ABC):
    """
    Interfaz para estrategias de determinación de pesos.

    Permite intercambiar AHP, PCA u otros métodos sin modificar
    el Aggregator que los consume (Dependency Inversion).
    """

    @abstractmethod
    def compute_weights(self, df: pd.DataFrame) -> dict[str, float]:
        """
        Calcula pesos para cada columna del DataFrame.

        Args:
            df: DataFrame normalizado con las variables del ICIV.

        Returns:
            dict {nombre_columna: peso} donde los valores suman 1.0.
        """
        ...

    @abstractmethod
    def get_method_name(self) -> str:
        """Nombre legible del método (para reportes)."""
        ...
