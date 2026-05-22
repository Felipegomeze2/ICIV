"""
Configuración central del proyecto ICIV.

Todas las rutas y parámetros globales viven aquí.
Nunca uses rutas hardcodeadas fuera de este archivo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# Raíz del proyecto: iciv/src/iciv/config/settings.py → 3 niveles arriba = iciv/
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Paths:
    """Rutas absolutas de las carpetas del proyecto."""

    root: Path = _PROJECT_ROOT

    # Datos
    data_raw: Path = _PROJECT_ROOT / "data" / "raw"
    data_processed: Path = _PROJECT_ROOT / "data" / "processed"

    # Archivos raw — un CSV por fuente, nombre simple
    raw_wdi:      Path = _PROJECT_ROOT / "data" / "raw" / "wdi.csv"
    raw_wgi:      Path = _PROJECT_ROOT / "data" / "raw" / "wgi.csv"
    raw_eia:      Path = _PROJECT_ROOT / "data" / "raw" / "eia.csv"
    raw_imf:      Path = _PROJECT_ROOT / "data" / "raw" / "imf.csv"
    raw_cpi:      Path = _PROJECT_ROOT / "data" / "raw" / "cpi.csv"
    raw_ief:      Path = _PROJECT_ROOT / "data" / "raw" / "ief.csv"
    raw_hdi:      Path = _PROJECT_ROOT / "data" / "raw" / "hdi.csv"
    raw_gdelt:         Path = _PROJECT_ROOT / "data" / "raw" / "gdelt.csv"
    raw_guardian:      Path = _PROJECT_ROOT / "data" / "raw" / "guardian.csv"
    raw_fred:          Path = _PROJECT_ROOT / "data" / "raw" / "fred.csv"
    raw_freedom_house: Path = _PROJECT_ROOT / "data" / "raw" / "freedom_house.csv"
    raw_unhcr:         Path = _PROJECT_ROOT / "data" / "raw" / "unhcr.csv"
    raw_ofac:          Path = _PROJECT_ROOT / "data" / "raw" / "ofac.csv"
    raw_gtrends:       Path = _PROJECT_ROOT / "data" / "raw" / "gtrends.csv"
    raw_viirs:         Path = _PROJECT_ROOT / "data" / "raw" / "viirs.csv"
    raw_unctad:        Path = _PROJECT_ROOT / "data" / "raw" / "unctad.csv"
    raw_opensky:       Path = _PROJECT_ROOT / "data" / "raw" / "opensky.csv"
    raw_viirs_states:  Path = _PROJECT_ROOT / "data" / "raw" / "viirs_states.csv"
    raw_ofac_network:  Path = _PROJECT_ROOT / "data" / "raw" / "ofac_network.json"
    raw_pts:           Path = _PROJECT_ROOT / "data" / "raw" / "pts.csv"
    raw_who:           Path = _PROJECT_ROOT / "data" / "raw" / "who.csv"

    # Fuentes ampliadas (sesión mayo 2026)
    raw_vdem:          Path = _PROJECT_ROOT / "data" / "raw" / "vdem.csv"
    raw_fragile:       Path = _PROJECT_ROOT / "data" / "raw" / "fragile_states.csv"
    raw_wjp:           Path = _PROJECT_ROOT / "data" / "raw" / "wjp.csv"
    raw_rsf:           Path = _PROJECT_ROOT / "data" / "raw" / "rsf.csv"
    raw_bti:           Path = _PROJECT_ROOT / "data" / "raw" / "bti.csv"
    raw_ghi:           Path = _PROJECT_ROOT / "data" / "raw" / "ghi.csv"
    raw_acled:         Path = _PROJECT_ROOT / "data" / "raw" / "acled.csv"
    raw_ilostat:       Path = _PROJECT_ROOT / "data" / "raw" / "ilostat.csv"
    raw_ucdp:          Path = _PROJECT_ROOT / "data" / "raw" / "ucdp.csv"
    raw_fao:           Path = _PROJECT_ROOT / "data" / "raw" / "fao.csv"
    raw_basel_aml:     Path = _PROJECT_ROOT / "data" / "raw" / "basel_aml.csv"
    raw_eia_monthly:   Path = _PROJECT_ROOT / "data" / "raw" / "eia_monthly.csv"
    raw_owid_extras:   Path = _PROJECT_ROOT / "data" / "raw" / "owid_extras.csv"

    # Pulse Mensual — fuentes high-frequency
    raw_fred_monthly:     Path = _PROJECT_ROOT / "data" / "raw" / "fred_monthly.csv"
    raw_guardian_monthly: Path = _PROJECT_ROOT / "data" / "raw" / "guardian_monthly.csv"

    # Config y scripts
    config: Path = _PROJECT_ROOT / "config"
    scripts: Path = _PROJECT_ROOT / "scripts"

    def ensure_exists(self) -> None:
        """Crea las carpetas de salida si no existen."""
        for folder in (self.data_raw, self.data_processed):
            folder.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class SeriesConfig:
    """Parámetros temporales y geográficos de la serie histórica."""

    start_year: int = 2000
    end_year: int = 2026
    base_year: int = 2010
    country_code_wb: str = "VEN"
    country_code_imf: str = "VEN"
    country_name: str = "Venezuela"


@dataclass(frozen=True)
class NormalizationConfig:
    """Parámetros de normalización de variables."""

    method: str = "minmax"       # "minmax" | "zscore"
    output_min: float = 0.0
    output_max: float = 100.0
    clip_outliers: bool = True


@dataclass(frozen=True)
class AggregationConfig:
    """Parámetros de agregación del índice."""

    method: str = "linear"           # "linear" | "geometric"
    use_fixed_weights: bool = True    # False = usar PCA


@dataclass(frozen=True)
class Settings:
    """
    Punto de entrada único a toda la configuración del proyecto.

    Uso:
        from iciv.config import Settings
        cfg = Settings()
        df = pd.read_csv(cfg.paths.raw_wdi)
    """

    paths: Paths = field(default_factory=Paths)
    series: SeriesConfig = field(default_factory=SeriesConfig)
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    aggregation: AggregationConfig = field(default_factory=AggregationConfig)


# Instancia global (singleton) — importar esto en el resto del código
settings = Settings()
