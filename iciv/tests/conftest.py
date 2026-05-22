"""
Fixtures compartidas para todos los tests del ICIV.

pytest carga este archivo automáticamente antes de cualquier test.
"""

import pytest
import pandas as pd
import numpy as np

from iciv.config import Settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def raw_data_available(settings) -> bool:
    """Indica si los archivos CSV de raw están presentes (skip si no)."""
    return settings.paths.raw_wdi.exists()


@pytest.fixture
def sample_wdi_df() -> pd.DataFrame:
    """DataFrame mínimo con estructura WDI para tests unitarios (2000-2026 = 27 años)."""
    n = 27  # 2000-2026
    return pd.DataFrame({
        "año": list(range(2000, 2027)),
        "pib_nominal_usd": np.random.uniform(40e9, 400e9, n),
        "pib_crecimiento_real_pct": np.random.uniform(-30, 18, n),
        "pib_per_capita_usd": np.random.uniform(1500, 14000, n),
        "ied_neta_usd": np.random.uniform(-2e9, 6e9, n),
        "reservas_internacionales_usd": [
            *np.random.uniform(10e9, 43e9, 18), *[np.nan] * 9  # post-2018 sin datos WB
        ],
        "exportaciones_pct_pib": np.random.uniform(13, 48, n),
    })


@pytest.fixture
def sample_normalized_df() -> pd.DataFrame:
    """DataFrame normalizado 0–100 con todas las variables del catálogo (2000-2026 = 27 años)."""
    np.random.seed(42)
    n = 27  # 2000-2026
    years = list(range(2000, 2027))
    return pd.DataFrame({
        "año": years,
        "inflacion_deflactor_pib_pct": np.random.uniform(0, 100, n),
        "pib_crecimiento_real_pct": np.random.uniform(0, 100, n),
        "reservas_internacionales_usd": [*np.random.uniform(0, 100, 18), *[np.nan]*9],
        "tipo_cambio_oficial_lcu_usd": np.random.uniform(0, 100, n),
        "petroleo_crudo_produccion_tbpd": np.random.uniform(0, 100, n),
        "gas_natural_produccion_bcf": np.random.uniform(0, 100, n),
        "electricidad_generacion_bkwh": np.random.uniform(0, 100, n),
        "cpi_score": [*[np.nan]*10, *np.random.uniform(0, 30, 13), np.nan, np.nan, 10.0, np.nan],
        "wgi_promedio_sc": np.random.uniform(15, 55, n),
        "ief_overall_score": np.random.uniform(24, 48, n),
        "ied_neta_usd": np.random.uniform(0, 100, n),
        "exportaciones_pct_pib": np.random.uniform(0, 100, n),
        "desempleo_pct": np.random.uniform(0, 100, n),
        "hdi": [*[np.nan]*5, *np.random.uniform(60, 80, 15), *[np.nan]*7],
        "tasa_alfabetizacion_adulta_pct": np.random.uniform(85, 100, n),
        "acceso_electricidad_pct": np.random.uniform(80, 100, n),
    })
