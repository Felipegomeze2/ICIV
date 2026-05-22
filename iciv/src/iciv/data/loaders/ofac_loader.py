"""
Loader para datos OFAC — Sanciones US Treasury hacia Venezuela.

Lee data/raw/ofac.csv en formato largo (año|indicador|valor|pais|fuente).
Columna de salida: ofac_sanciones_count (número de entidades sancionadas)
"""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import SourceID
from .index_loader import _LongFormatLoader


class OFACLoader(_LongFormatLoader):
    """Loader para conteo histórico de sanciones OFAC hacia Venezuela."""

    _indicator_name = "ofac_sanciones_count"
    _output_column  = "ofac_sanciones_count"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_ofac)

    def get_source_id(self) -> SourceID:
        return SourceID.OFAC
