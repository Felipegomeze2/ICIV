"""Loaders auxiliares vigentes en el core ICIV."""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import SourceID
from .index_loader import _LongFormatLoader


class WJPLoader(_LongFormatLoader):
    """World Justice Project Rule of Law Index."""

    _indicator_name = "wjp_rule_of_law"
    _output_column = "wjp_rule_of_law"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_wjp)

    def get_source_id(self) -> SourceID:
        return SourceID.WJP


class ILOStatLoader(_LongFormatLoader):
    """ILO ILOSTAT, informal employment as share of total employment."""

    _indicator_name = "ilo_empleo_informal_pct"
    _output_column = "ilo_empleo_informal_pct"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_ilostat)

    def get_source_id(self) -> SourceID:
        return SourceID.ILOSTAT
