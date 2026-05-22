"""
Loader para datos UNHCR/R4V — Migración venezolana.

Lee data/raw/unhcr.csv en formato largo (año|indicador|valor|pais|fuente).
Columna de salida: migrantes_vzla_millones (millones de personas)
"""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import SourceID
from .index_loader import _LongFormatLoader


class UNHCRLoader(_LongFormatLoader):
    """Loader para datos de migración venezolana UNHCR/R4V."""

    _indicator_name = "migrantes_vzla_millones"
    _output_column  = "migrantes_vzla_millones"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_unhcr)

    def get_source_id(self) -> SourceID:
        return SourceID.UNHCR
