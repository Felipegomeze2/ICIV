"""
Loaders para las fuentes de datos ampliadas del ICIV (mayo 2026).

Cada clase hereda de _LongFormatLoader (misma interfaz que CPI/IEF/HDI/PTS).
Los archivos fuente usan formato largo: año | indicador | valor | pais | fuente.

Fuentes incluidas:
  - VDemLoader          → data/raw/vdem.csv            → vdem_libdem_index
  - FragileStatesLoader → data/raw/fragile_states.csv  → fragile_states_index
  - WJPLoader           → data/raw/wjp.csv             → wjp_rule_of_law
  - RSFLoader           → data/raw/rsf.csv             → rsf_press_freedom
  - BTILoader           → data/raw/bti.csv             → bti_governance_index
  - GHILoader           → data/raw/ghi.csv             → ghi_score
  - ACLEDLoader         → data/raw/acled.csv           → acled_eventos_violencia
  - ILOStatLoader       → data/raw/ilostat.csv         → ilo_empleo_informal_pct
  - UCDPLoader          → data/raw/ucdp.csv            → ucdp_conflicto_idx
  - FAOLoader           → data/raw/fao.csv             → fao_calorias_per_capita
  - BaselAMLLoader      → data/raw/basel_aml.csv       → basel_aml_index
"""

from __future__ import annotations

from iciv.config import Settings
from iciv.data.models import SourceID
from .index_loader import _LongFormatLoader


class VDemLoader(_LongFormatLoader):
    """V-Dem Liberal Democracy Index — Varieties of Democracy Project."""

    _indicator_name = "vdem_libdem_index"
    _output_column  = "vdem_libdem_index"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_vdem)

    def get_source_id(self) -> SourceID:
        return SourceID.VDEM


class FragileStatesLoader(_LongFormatLoader):
    """Fragile States Index — Fund for Peace."""

    _indicator_name = "fragile_states_index"
    _output_column  = "fragile_states_index"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_fragile)

    def get_source_id(self) -> SourceID:
        return SourceID.FRAGILE


class WJPLoader(_LongFormatLoader):
    """World Justice Project Rule of Law Index."""

    _indicator_name = "wjp_rule_of_law"
    _output_column  = "wjp_rule_of_law"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_wjp)

    def get_source_id(self) -> SourceID:
        return SourceID.WJP


class RSFLoader(_LongFormatLoader):
    """Reporters Without Borders Press Freedom Index."""

    _indicator_name = "rsf_press_freedom"
    _output_column  = "rsf_press_freedom"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_rsf)

    def get_source_id(self) -> SourceID:
        return SourceID.RSF


class BTILoader(_LongFormatLoader):
    """Bertelsmann Transformation Index — Governance Index."""

    _indicator_name = "bti_governance_index"
    _output_column  = "bti_governance_index"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_bti)

    def get_source_id(self) -> SourceID:
        return SourceID.BTI


class GHILoader(_LongFormatLoader):
    """Global Hunger Index — Welthungerhilfe / Concern Worldwide."""

    _indicator_name = "ghi_score"
    _output_column  = "ghi_score"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_ghi)

    def get_source_id(self) -> SourceID:
        return SourceID.GHI


class ACLEDLoader(_LongFormatLoader):
    """ACLED Armed Conflict — violent events count (2018+)."""

    _indicator_name = "acled_eventos_violencia"
    _output_column  = "acled_eventos_violencia"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_acled)

    def get_source_id(self) -> SourceID:
        return SourceID.ACLED


class ILOStatLoader(_LongFormatLoader):
    """ILO ILOSTAT — Informal employment (% of total employment)."""

    _indicator_name = "ilo_empleo_informal_pct"
    _output_column  = "ilo_empleo_informal_pct"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_ilostat)

    def get_source_id(self) -> SourceID:
        return SourceID.ILOSTAT


class UCDPLoader(_LongFormatLoader):
    """UCDP — Uppsala Conflict Data Program conflict deaths per 100k."""

    _indicator_name = "ucdp_conflicto_idx"
    _output_column  = "ucdp_conflicto_idx"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_ucdp)

    def get_source_id(self) -> SourceID:
        return SourceID.UCDP


class FAOLoader(_LongFormatLoader):
    """FAO FAOSTAT — Food supply (kcal/capita/day)."""

    _indicator_name = "fao_calorias_per_capita"
    _output_column  = "fao_calorias_per_capita"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_fao)

    def get_source_id(self) -> SourceID:
        return SourceID.FAO


class BaselAMLLoader(_LongFormatLoader):
    """Basel Institute on Governance — AML Index (0-10, higher = more risk)."""

    _indicator_name = "basel_aml_index"
    _output_column  = "basel_aml_index"

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or Settings()
        super().__init__(cfg.paths.raw_basel_aml)

    def get_source_id(self) -> SourceID:
        return SourceID.BASEL_AML
