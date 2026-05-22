"""
Loader para datos del Political Terror Scale (PTS).

Lee data/raw/pts.csv en formato largo (año|indicador|valor|pais|fuente).
Columna de salida: pts_terror_politico (escala 1-5, dirección negativa)
"""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import SourceID
from .index_loader import _LongFormatLoader


class PTSLoader(_LongFormatLoader):
    """Loader para el Political Terror Scale de Venezuela."""

    _indicator_name = "pts_terror_politico"
    _output_column  = "pts_terror_politico"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_pts)

    def get_source_id(self) -> SourceID:
        return SourceID.PTS
