"""
Loader para Google Trends — Interés de búsqueda relativo sobre Venezuela.

Lee data/raw/gtrends.csv en formato largo (año|indicador|valor|pais|fuente).
Columna de salida: google_trends_vzla (score relativo 0-100)
"""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import SourceID
from .index_loader import _LongFormatLoader


class GTrendsLoader(_LongFormatLoader):
    """Loader para interés de búsqueda Google Trends sobre Venezuela."""

    _indicator_name = "google_trends_vzla"
    _output_column  = "google_trends_vzla"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_gtrends)

    def get_source_id(self) -> SourceID:
        return SourceID.GTRENDS
