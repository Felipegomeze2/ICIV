"""
Contrato abstracto para todos los transformadores del pipeline.

Sigue la interfaz fit/transform de scikit-learn para que los
transformers sean interoperables con el ecosistema de Python ML.

Principio Single Responsibility: cada transformer hace UNA cosa.
Principio Open/Closed: el pipeline acepta cualquier transformer sin
    modificación — basta con crear una subclase de BaseTransformer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseTransformer(ABC):
    """
    Interfaz base para todos los transformers del ICIV.

    Ciclo de vida:
        1. fit(df)           → aprende parámetros del conjunto de entrenamiento
        2. transform(df)     → aplica la transformación usando los parámetros
        3. fit_transform(df) → atajo: fit + transform en un paso

    Los parámetros aprendidos en fit() se almacenan como atributos de instancia
    para poder aplicarlos luego a datos nuevos (ej. años futuros).

    Ejemplo de uso:
        normalizer = MinMaxNormalizer(columns=["pib_crecimiento_real_pct"])
        df_norm = normalizer.fit_transform(df_train)
        df_new_norm = normalizer.transform(df_new)   # usa min/max de entrenamiento
    """

    def __init__(self) -> None:
        self._fitted = False

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> "BaseTransformer":
        """
        Aprende parámetros necesarios para la transformación.

        Debe marcar self._fitted = True al finalizar.
        Retorna self para permitir encadenamiento: transformer.fit(df).transform(df2)
        """
        ...

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica la transformación. Requiere que fit() haya sido llamado.

        No debe modificar el DataFrame original: trabajar sobre una copia.
        """
        ...

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Atajo: fit seguido de transform sobre el mismo DataFrame."""
        return self.fit(df).transform(df)

    def _assert_fitted(self) -> None:
        """Lanza RuntimeError si se llama transform() antes de fit()."""
        if not self._fitted:
            raise RuntimeError(
                f"{self.__class__.__name__}.transform() fue llamado antes de fit(). "
                f"Llama fit() primero o usa fit_transform()."
            )

    def __repr__(self) -> str:
        status = "fitted" if self._fitted else "not fitted"
        return f"{self.__class__.__name__}({status})"
