"""
Pipeline — orquestador de transformaciones del ICIV.

Encadena transformers en secuencia. Sigue el patrón Composite:
el pipeline se comporta externamente igual que un transformer individual
(tiene fit/transform/fit_transform), lo que permite anidar pipelines.

Uso típico:
    from iciv.processing.pipeline import Pipeline
    from iciv.processing.transformers import DataCleaner, GapImputer, MinMaxNormalizer

    pipeline = Pipeline([
        ("clean",     DataCleaner()),
        ("impute",    GapImputer()),
        ("normalize", MinMaxNormalizer()),
    ])

    df_procesado = pipeline.fit_transform(df_raw)

    # Reutilizar en datos nuevos con los parámetros aprendidos:
    df_nuevo_norm = pipeline.transform(df_nuevo)
"""

from __future__ import annotations

import logging
import time
from typing import Sequence

import pandas as pd

from .transformers.base import BaseTransformer

logger = logging.getLogger(__name__)

Step = tuple[str, BaseTransformer]


class Pipeline(BaseTransformer):
    """
    Cadena ordenada de transformers.

    Args:
        steps: lista de tuplas (nombre, transformer). El nombre es un
               identificador legible usado en los logs.

    Invariante: los pasos se ejecutan en el orden en que se definen.
    """

    def __init__(self, steps: Sequence[Step]) -> None:
        super().__init__()
        self._validate_steps(steps)
        self.steps: list[Step] = list(steps)

    # ── API pública ───────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> "Pipeline":
        """
        Ajusta cada transformer en secuencia, pasando la salida del anterior
        como entrada del siguiente (necesario cuando fit depende de los datos
        ya transformados, ej. normalizar después de imputar).
        """
        current = df.copy()
        for name, transformer in self.steps:
            t0 = time.perf_counter()
            transformer.fit(current)
            current = transformer.transform(current)
            logger.debug("  [Pipeline] fit '%s' en %.3fs", name, time.perf_counter() - t0)
        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica todos los transformers en secuencia."""
        self._assert_fitted()
        current = df.copy()
        for name, transformer in self.steps:
            t0 = time.perf_counter()
            current = transformer.transform(current)
            logger.debug("  [Pipeline] transform '%s' en %.3fs", name, time.perf_counter() - t0)
        return current

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajusta y transforma en un solo paso."""
        current = df.copy()
        logger.info("Pipeline.fit_transform: %d pasos, %d filas entrada", len(self.steps), len(df))
        for name, transformer in self.steps:
            t0 = time.perf_counter()
            current = transformer.fit_transform(current)
            logger.info(
                "  ✓ Paso '%s': %d→%d filas en %.3fs",
                name, len(df), len(current), time.perf_counter() - t0,
            )
        self._fitted = True
        return current

    def add_step(self, name: str, transformer: BaseTransformer) -> "Pipeline":
        """Agrega un paso al final del pipeline. Resetea estado fitted."""
        self.steps.append((name, transformer))
        self._fitted = False
        return self

    def get_step(self, name: str) -> BaseTransformer:
        """Recupera un transformer por nombre."""
        for step_name, transformer in self.steps:
            if step_name == name:
                return transformer
        raise KeyError(f"Paso '{name}' no encontrado en el pipeline.")

    def __repr__(self) -> str:
        steps_str = " -> ".join(name for name, _ in self.steps)
        return f"Pipeline([{steps_str}])"

    # ── Validación interna ────────────────────────────────────────────────────

    @staticmethod
    def _validate_steps(steps: Sequence[Step]) -> None:
        if not steps:
            raise ValueError("El pipeline debe tener al menos un paso.")
        names = [name for name, _ in steps]
        if len(names) != len(set(names)):
            raise ValueError(f"Los nombres de los pasos deben ser únicos. Recibidos: {names}")
        for name, transformer in steps:
            if not isinstance(transformer, BaseTransformer):
                raise TypeError(
                    f"El paso '{name}' debe ser una instancia de BaseTransformer, "
                    f"recibido: {type(transformer).__name__}"
                )
