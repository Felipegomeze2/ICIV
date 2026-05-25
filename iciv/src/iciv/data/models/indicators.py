"""
Modelos de datos para las variables del ICIV.

Define los tipos que circulan por el pipeline usando dataclasses.
Esto garantiza que nadie pase un DataFrame sin contexto: siempre
se sabe qué fuente produjo los datos y qué columnas se esperan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import pandas as pd


class Direction(str, Enum):
    """Dirección del indicador respecto al clima de inversión."""
    POSITIVE = "positive"   # mayor valor → mejor clima
    NEGATIVE = "negative"   # mayor valor → peor clima (ej. inflación)


class DimensionID(str, Enum):
    """Las 6 dimensiones del ICIV según el documento maestro."""
    MACRO         = "D1_macro"
    ENERGY        = "D2_energia"
    INSTITUTIONAL = "D3_institucional"
    COMMERCIAL    = "D4_comercial"
    HUMAN         = "D5_capital_humano"
    PERCEPTION    = "D6_percepcion"


class SourceID(str, Enum):
    """Identificadores de fuentes vigentes."""
    WDI = "WDI"
    WGI = "WGI"
    EIA = "EIA"
    IMF = "IMF"
    CPI = "CPI"
    HDI = "HDI"
    GDELT = "GDELT"
    GUARDIAN = "GUARDIAN"
    FRED = "FRED"
    FREEDOM_HOUSE = "FREEDOM_HOUSE"
    UNHCR = "UNHCR"
    VIIRS = "VIIRS"
    UNCTAD = "UNCTAD"
    PTS = "PTS"
    WHO = "WHO"
    WJP = "WJP"
    ILOSTAT = "ILOSTAT"


@dataclass(frozen=True)
class VariableMetadata:
    """
    Metadatos completos de una variable del ICIV.

    Attributes:
        column_name:    nombre de la columna en el DataFrame procesado
        description:    descripción legible para reportes y gráficos
        source:         fuente de datos (SourceID)
        unit:           unidad de medida (ej. "%", "USD bn", "score 0-100")
        direction:      si un valor alto es bueno o malo para inversión
        dimension:      dimensión a la que pertenece en el ICIV
        dim_weight:     peso dentro de su dimensión (0–1, debe sumar 1 por dim.)
        available_from: primer año con datos confiables
        notes:          advertencias o decisiones metodológicas
    """

    column_name: str
    description: str
    source: SourceID
    unit: str
    direction: Direction
    dimension: DimensionID
    dim_weight: float
    available_from: int
    notes: str = ""


@dataclass
class DatasetResult:
    """
    Contenedor que encapsula un DataFrame junto con sus metadatos de origen.
    Es el tipo que retornan todos los DataLoaders.

    Attributes:
        source:         identificador de la fuente
        df:             datos cargados (índice = año, columnas = variables)
        available_years: lista de años con al menos un dato
        missing_cols:   columnas esperadas que no se encontraron
    """

    source: SourceID
    df: pd.DataFrame
    available_years: list[int] = field(default_factory=list)
    missing_cols: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if "año" in self.df.columns:
            self.available_years = sorted(self.df["año"].dropna().astype(int).tolist())
        elif self.df.index.name == "año":
            self.available_years = sorted(self.df.index.dropna().astype(int).tolist())

    @property
    def coverage_pct(self) -> float:
        """Porcentaje de cobertura respecto al período 2000–2026."""
        total_years = 27  # 2000–2026
        return round(len(self.available_years) / total_years * 100, 1)

    @property
    def shape(self) -> tuple[int, int]:
        return self.df.shape

    def __repr__(self) -> str:
        yr = (
            f"{min(self.available_years)}–{max(self.available_years)}"
            if self.available_years else "sin datos"
        )
        return (
            f"DatasetResult(source={self.source.value}, "
            f"shape={self.shape}, years={yr}, coverage={self.coverage_pct}%)"
        )
