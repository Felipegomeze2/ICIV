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

    def _read_csv(self, path=None):
        df = super()._read_csv(path)
        if "fuente" in df.columns:
            # El archivo histórico conserva asignaciones antiguas a ambos años;
            # una edición doble solo aporta al año final, sin modificar el raw.
            end_year = df["fuente"].str.extract(r"edicion\s+\d{4}-(\d{4})", expand=False)
            keep = end_year.isna() | (df["año"].astype(str) == end_year)
            df = df.loc[keep].copy()
        return df


class ILOStatLoader(_LongFormatLoader):
    """Empleo vulnerable, estimación modelada OIT distribuida por WDI."""

    _indicator_name = "empleo_vulnerable_oit_pct"
    _output_column = "empleo_vulnerable_oit_pct"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_ilostat)

    def get_source_id(self) -> SourceID:
        return SourceID.WDI
