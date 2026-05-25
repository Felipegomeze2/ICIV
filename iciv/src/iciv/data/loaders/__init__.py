"""Registro de loaders usados por el pipeline vigente."""

from .base import DataLoader
from .wdi_loader import WDILoader
from .wgi_loader import WGILoader
from .eia_loader import EIALoader
from .imf_loader import IMFLoader
from .index_loader import CPILoader, HDILoader
from .guardian_loader import GuardianLoader
from .fred_loader import FREDLoader
from .freedom_house_loader import FreedomHouseLoader
from .unhcr_loader import UNHCRLoader
from .viirs_loader import VIIRSLoader
from .unctad_loader import UNCTADLoader
from .pts_loader import PTSLoader
from .who_loader import WHOLoader
from .extended_loaders import WJPLoader, ILOStatLoader

# Loaders que alimentan el ICIV anual vigente o su outcome externo.
# Las fuentes apartadas pueden conservar scripts/CSV de auditoria, pero no entran
# al panel maestro para no publicitarlas como cobertura efectiva.
ALL_LOADERS: list[type[DataLoader]] = [
    WDILoader,
    WGILoader,
    EIALoader,
    IMFLoader,
    CPILoader,
    HDILoader,
    GuardianLoader,
    FREDLoader,
    FreedomHouseLoader,
    UNHCRLoader,
    VIIRSLoader,
    UNCTADLoader,
    PTSLoader,
    WHOLoader,
    WJPLoader,
    ILOStatLoader,
]

__all__ = [
    "DataLoader",
    "WDILoader",
    "WGILoader",
    "EIALoader",
    "IMFLoader",
    "CPILoader",
    "HDILoader",
    "GuardianLoader",
    "FREDLoader",
    "FreedomHouseLoader",
    "UNHCRLoader",
    "VIIRSLoader",
    "UNCTADLoader",
    "PTSLoader",
    "WHOLoader",
    "WJPLoader",
    "ILOStatLoader",
    "ALL_LOADERS",
]
