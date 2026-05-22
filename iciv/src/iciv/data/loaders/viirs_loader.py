"""
Loader para NASA VIIRS / NOAA DMSP-OLS — Luminosidad nocturna Venezuela.

Lee data/raw/viirs.csv en formato largo (año|indicador|valor|pais|fuente).
Columna de salida: luminosidad_nocturna_idx (índice normalizado 0-100)
"""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import SourceID
from .index_loader import _LongFormatLoader


class VIIRSLoader(_LongFormatLoader):
    """Loader para índice de luminosidad nocturna VIIRS/DMSP — Venezuela."""

    _indicator_name = "luminosidad_nocturna_idx"
    _output_column  = "luminosidad_nocturna_idx"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_viirs)

    def get_source_id(self) -> SourceID:
        return SourceID.VIIRS
