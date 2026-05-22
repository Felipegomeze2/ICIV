"""
Loader para Freedom House — Freedom in the World Index.

Lee data/raw/freedom_house.csv en formato largo (año|indicador|valor|pais|fuente).
Columna de salida: freedom_house_score (0-100, mayor = más libre)
"""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import SourceID
from .index_loader import _LongFormatLoader


class FreedomHouseLoader(_LongFormatLoader):
    """Loader para el Aggregate Score de Freedom House — Venezuela."""

    _indicator_name = "freedom_house_score"
    _output_column  = "freedom_house_score"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_freedom_house)

    def get_source_id(self) -> SourceID:
        return SourceID.FREEDOM_HOUSE
