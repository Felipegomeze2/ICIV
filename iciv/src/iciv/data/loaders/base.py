"""
Contrato abstracto para todos los cargadores de datos del ICIV.

Principio Open/Closed: para agregar una nueva fuente de datos basta con
crear una subclase de DataLoader — no se toca ningún código existente.

Principio de Sustitución de Liskov: cualquier DataLoader concreto puede
reemplazar a otro en el pipeline sin que el código que lo usa se rompa.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import logging

import pandas as pd

from iciv.data.models import DatasetResult, SourceID

logger = logging.getLogger(__name__)


class DataLoader(ABC):
    """
    Clase base abstracta para todos los loaders de datos del ICIV.

    Cada fuente de datos (WDI, WGI, EIA, IMF, CPI, IEF, HDI) tiene su
    propio loader concreto que hereda de esta clase. El contrato garantiza:

    1. `load()`         → devuelve siempre un DatasetResult
    2. `validate()`     → verifica integridad mínima del DataFrame cargado
    3. `get_source_id()`→ identifica la fuente
    4. `load_validated()` → método plantilla que orquesta load + validate

    El DataFrame dentro de DatasetResult siempre tiene:
    - Una columna `año` de tipo int (o el año como índice)
    - Una fila por año (sin duplicados)
    - Solo columnas relevantes para el ICIV (sin metadatos de fuente)
    """

    def __init__(self, data_path: Path) -> None:
        """
        Args:
            data_path: ruta al archivo CSV (o carpeta) de esta fuente.
        """
        self._data_path = data_path

    # ── Métodos abstractos — obligatorios en cada subclase ───────────────────

    @abstractmethod
    def load(self) -> DatasetResult:
        """
        Carga el CSV de la fuente y retorna un DatasetResult.

        Debe:
        - Leer el archivo desde self._data_path
        - Retornar columnas con los nombres estándar definidos en el catálogo
        - Incluir columna `año` como int
        - No imputar ni normalizar (eso lo hacen los Transformers)
        """
        ...

    @abstractmethod
    def validate(self, result: DatasetResult) -> bool:
        """
        Valida que el DatasetResult cumple los requisitos mínimos.

        Retorna True si es válido. Debe registrar warnings específicos
        (no lanzar excepciones) para que el pipeline pueda continuar
        con las demás fuentes aunque una falle validación.
        """
        ...

    @abstractmethod
    def get_source_id(self) -> SourceID:
        """Retorna el identificador de esta fuente."""
        ...

    # ── Método plantilla — NO sobreescribir en subclases ────────────────────

    def load_validated(self) -> DatasetResult:
        """
        Carga y valida los datos. Lanza ValueError si la validación falla.

        Uso recomendado en el pipeline principal.
        """
        logger.info("Cargando fuente: %s desde %s", self.get_source_id().value, self._data_path)
        result = self.load()
        if not self.validate(result):
            raise ValueError(
                f"Validación fallida para {self.get_source_id().value}. "
                f"Revisa los logs para detalles."
            )
        logger.info(
            "  ✓ %s cargado: %s filas, %s columnas, cobertura %s%%",
            self.get_source_id().value,
            result.shape[0],
            result.shape[1],
            result.coverage_pct,
        )
        return result

    # ── Helpers protegidos — disponibles para todas las subclases ────────────

    def _read_csv(self, path: Path | None = None) -> pd.DataFrame:
        """Lee un CSV con manejo de errores descriptivos."""
        target = path or self._data_path
        if not target.exists():
            raise FileNotFoundError(
                f"Archivo no encontrado: {target}\n"
                f"Ejecuta scripts/fetch_*.py para descargar los datos raw."
            )
        return pd.read_csv(target, encoding="utf-8-sig")

    @staticmethod
    def _ensure_year_column(df: pd.DataFrame) -> pd.DataFrame:
        """Garantiza que la columna 'año' exista y sea int."""
        if "año" not in df.columns:
            raise KeyError("El DataFrame no tiene columna 'año'.")
        df = df.copy()
        df["año"] = df["año"].astype(int)
        return df

    @staticmethod
    def _filter_year_range(
        df: pd.DataFrame, start: int = 2000, end: int = 2026
    ) -> pd.DataFrame:
        """Filtra filas fuera del período de análisis."""
        return df[(df["año"] >= start) & (df["año"] <= end)].copy()

    @staticmethod
    def _check_required_columns(
        df: pd.DataFrame, required: list[str], source_name: str
    ) -> list[str]:
        """
        Verifica columnas requeridas. Retorna lista de columnas faltantes
        y registra un warning por cada una.
        """
        missing = [col for col in required if col not in df.columns]
        for col in missing:
            logger.warning("  ⚠ Columna '%s' no encontrada en %s", col, source_name)
        return missing
