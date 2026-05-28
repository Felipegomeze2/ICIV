"""Configuracion central del proyecto ICIV."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Paths:
    """Rutas absolutas de carpetas y fuentes vigentes."""

    root: Path = _PROJECT_ROOT

    data_raw: Path = _PROJECT_ROOT / "data" / "raw"
    data_processed: Path = _PROJECT_ROOT / "data" / "processed"
    data_releases: Path = _PROJECT_ROOT / "data" / "releases"

    raw_wdi: Path = _PROJECT_ROOT / "data" / "raw" / "wdi.csv"
    raw_wgi: Path = _PROJECT_ROOT / "data" / "raw" / "wgi.csv"
    raw_eia: Path = _PROJECT_ROOT / "data" / "raw" / "eia.csv"
    raw_imf: Path = _PROJECT_ROOT / "data" / "raw" / "imf.csv"
    raw_cpi: Path = _PROJECT_ROOT / "data" / "raw" / "cpi.csv"
    raw_hdi: Path = _PROJECT_ROOT / "data" / "raw" / "hdi.csv"
    raw_guardian: Path = _PROJECT_ROOT / "data" / "raw" / "guardian.csv"
    raw_fred: Path = _PROJECT_ROOT / "data" / "raw" / "fred.csv"
    raw_freedom_house: Path = _PROJECT_ROOT / "data" / "raw" / "freedom_house.csv"
    raw_unhcr: Path = _PROJECT_ROOT / "data" / "raw" / "unhcr.csv"
    raw_viirs: Path = _PROJECT_ROOT / "data" / "raw" / "viirs.csv"
    raw_unctad: Path = _PROJECT_ROOT / "data" / "raw" / "unctad.csv"
    raw_viirs_states: Path = _PROJECT_ROOT / "data" / "raw" / "viirs_states.csv"
    raw_pts: Path = _PROJECT_ROOT / "data" / "raw" / "pts.csv"
    raw_who: Path = _PROJECT_ROOT / "data" / "raw" / "who.csv"
    raw_wjp: Path = _PROJECT_ROOT / "data" / "raw" / "wjp.csv"
    raw_ilostat: Path = _PROJECT_ROOT / "data" / "raw" / "ilostat.csv"

    raw_eia_monthly: Path = _PROJECT_ROOT / "data" / "raw" / "eia_monthly.csv"
    raw_fred_monthly: Path = _PROJECT_ROOT / "data" / "raw" / "fred_monthly.csv"
    raw_guardian_monthly: Path = _PROJECT_ROOT / "data" / "raw" / "guardian_monthly.csv"
    raw_gdelt_monthly: Path = _PROJECT_ROOT / "data" / "raw" / "gdelt_monthly.csv"
    raw_international_news: Path = _PROJECT_ROOT / "data" / "raw" / "international_news.csv"

    config: Path = _PROJECT_ROOT / "config"
    scripts: Path = _PROJECT_ROOT / "scripts"

    def ensure_exists(self) -> None:
        for folder in (self.data_raw, self.data_processed, self.data_releases):
            folder.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class SeriesConfig:
    start_year: int = 2000
    end_year: int = 2026
    base_year: int = 2010
    country_code_wb: str = "VEN"
    country_code_imf: str = "VEN"
    country_name: str = "Venezuela"


@dataclass(frozen=True)
class NormalizationConfig:
    method: str = "minmax"
    output_min: float = 0.0
    output_max: float = 100.0
    clip_outliers: bool = True


@dataclass(frozen=True)
class AggregationConfig:
    method: str = "linear"
    use_fixed_weights: bool = True


@dataclass(frozen=True)
class Settings:
    paths: Paths = field(default_factory=Paths)
    series: SeriesConfig = field(default_factory=SeriesConfig)
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    aggregation: AggregationConfig = field(default_factory=AggregationConfig)


settings = Settings()
