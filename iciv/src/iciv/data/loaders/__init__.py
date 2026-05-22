"""
Registro de todos los loaders disponibles.

Uso:
    from iciv.data.loaders import ALL_LOADERS, WDILoader

    for loader_cls in ALL_LOADERS:
        result = loader_cls().load_validated()
"""

from .wdi_loader import WDILoader
from .wgi_loader import WGILoader
from .eia_loader import EIALoader
from .imf_loader import IMFLoader
from .index_loader import CPILoader, IEFLoader, HDILoader
from .guardian_loader import GuardianLoader
from .fred_loader import FREDLoader
from .freedom_house_loader import FreedomHouseLoader
from .unhcr_loader import UNHCRLoader
from .ofac_loader import OFACLoader
from .gtrends_loader import GTrendsLoader
from .viirs_loader import VIIRSLoader
from .unctad_loader import UNCTADLoader
from .opensky_loader import OpenSkyLoader
from .pts_loader import PTSLoader
from .who_loader import WHOLoader
from .extended_loaders import (
    VDemLoader,
    FragileStatesLoader,
    WJPLoader,
    RSFLoader,
    BTILoader,
    GHILoader,
    ACLEDLoader,
    ILOStatLoader,
    UCDPLoader,
    FAOLoader,
    BaselAMLLoader,
)
from .base import DataLoader

# Lista completa de loaders — útil para iterar en el pipeline de ingesta
ALL_LOADERS: list[type[DataLoader]] = [
    WDILoader,
    WGILoader,
    EIALoader,
    IMFLoader,
    CPILoader,
    IEFLoader,
    HDILoader,
    GuardianLoader,
    FREDLoader,
    FreedomHouseLoader,
    UNHCRLoader,
    OFACLoader,
    GTrendsLoader,
    VIIRSLoader,
    UNCTADLoader,
    OpenSkyLoader,
    PTSLoader,
    WHOLoader,
    # Fuentes ampliadas (mayo 2026)
    VDemLoader,
    FragileStatesLoader,
    WJPLoader,
    RSFLoader,
    BTILoader,
    GHILoader,
    ACLEDLoader,
    ILOStatLoader,
    UCDPLoader,
    FAOLoader,
    BaselAMLLoader,
]

__all__ = [
    "DataLoader",
    "WDILoader",
    "WGILoader",
    "EIALoader",
    "IMFLoader",
    "CPILoader",
    "IEFLoader",
    "HDILoader",
    "GuardianLoader",
    "FREDLoader",
    "FreedomHouseLoader",
    "UNHCRLoader",
    "OFACLoader",
    "GTrendsLoader",
    "VIIRSLoader",
    "UNCTADLoader",
    "OpenSkyLoader",
    "PTSLoader",
    "WHOLoader",
    "VDemLoader",
    "FragileStatesLoader",
    "WJPLoader",
    "RSFLoader",
    "BTILoader",
    "GHILoader",
    "ACLEDLoader",
    "ILOStatLoader",
    "UCDPLoader",
    "FAOLoader",
    "BaselAMLLoader",
    "ALL_LOADERS",
]
