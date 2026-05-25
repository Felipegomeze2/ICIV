"""Catalogo central de variables publicadas por el ICIV vigente.

El score anual se define en `iciv.index.dimensions`. Este catalogo aporta los
metadatos de esas variables, del outcome externo IED y de las senales mensuales
usadas por Pulse. Las fuentes apartadas no se registran aqui para no confundir
dataset disponible con variables efectivamente defendidas.
"""

from __future__ import annotations

from .models.indicators import Direction, DimensionID, SourceID, VariableMetadata


def _v(
    column: str,
    description: str,
    source: SourceID,
    unit: str,
    direction: Direction,
    dimension: DimensionID,
    weight: float,
    since: int,
    notes: str = "",
) -> VariableMetadata:
    return VariableMetadata(
        column_name=column,
        description=description,
        source=source,
        unit=unit,
        direction=direction,
        dimension=dimension,
        dim_weight=weight,
        available_from=since,
        notes=notes,
    )


CATALOG: dict[str, VariableMetadata] = {
    # D1 - macro
    "inflacion_deflactor_pib_pct": _v(
        "inflacion_deflactor_pib_pct", "Inflacion, deflactor del PIB",
        SourceID.IMF, "% log10", Direction.NEGATIVE, DimensionID.MACRO, 0.28, 2000,
        "Transformada a log10 antes de normalizar para no inflar anos recientes por el maximo de hiperinflacion.",
    ),
    "pib_crecimiento_real_pct": _v(
        "pib_crecimiento_real_pct", "Crecimiento real del PIB",
        SourceID.WDI, "%", Direction.POSITIVE, DimensionID.MACRO, 0.22, 2002,
    ),
    "reservas_internacionales_usd": _v(
        "reservas_internacionales_usd", "Reservas internacionales",
        SourceID.WDI, "USD", Direction.POSITIVE, DimensionID.MACRO, 0.18, 2000,
        "Faltantes recientes se muestran como faltantes; no se hace forward-fill.",
    ),
    "tipo_cambio_oficial_lcu_usd": _v(
        "tipo_cambio_oficial_lcu_usd", "Tipo de cambio oficial homogeneizado",
        SourceID.WDI, "log10 BsF/USD equivalente", Direction.NEGATIVE, DimensionID.MACRO, 0.12, 2000,
    ),
    "wti_precio_usd": _v(
        "wti_precio_usd", "Precio WTI del petroleo",
        SourceID.FRED, "USD/barril", Direction.POSITIVE, DimensionID.MACRO, 0.12, 2000,
    ),
    "tasa_fed_funds_pct": _v(
        "tasa_fed_funds_pct", "Tasa efectiva de fondos federales de EE. UU.",
        SourceID.FRED, "%", Direction.NEGATIVE, DimensionID.MACRO, 0.08, 2000,
    ),

    # D2 - energia
    "petroleo_crudo_produccion_tbpd": _v(
        "petroleo_crudo_produccion_tbpd", "Produccion de petroleo crudo",
        SourceID.EIA, "mil barriles/dia", Direction.POSITIVE, DimensionID.ENERGY, 0.45, 2000,
    ),
    "gas_natural_produccion_bcf": _v(
        "gas_natural_produccion_bcf", "Produccion de gas natural",
        SourceID.EIA, "BCF", Direction.POSITIVE, DimensionID.ENERGY, 0.25, 2000,
    ),
    "electricidad_generacion_bkwh": _v(
        "electricidad_generacion_bkwh", "Generacion electrica",
        SourceID.EIA, "bkWh", Direction.POSITIVE, DimensionID.ENERGY, 0.15, 2000,
    ),
    "luminosidad_nocturna_idx": _v(
        "luminosidad_nocturna_idx", "Luminosidad nocturna satelital",
        SourceID.VIIRS, "indice 0-100", Direction.POSITIVE, DimensionID.ENERGY, 0.15, 2000,
        "Proxy independiente de actividad real basado en Li et al./Figshare.",
    ),

    # D3 - institucional
    "cpi_score": _v(
        "cpi_score", "Indice de percepcion de corrupcion",
        SourceID.CPI, "0-100", Direction.POSITIVE, DimensionID.INSTITUTIONAL, 0.24, 2000,
    ),
    "wgi_promedio_sc": _v(
        "wgi_promedio_sc", "Promedio WGI de gobernanza",
        SourceID.WGI, "percentil 0-100", Direction.POSITIVE, DimensionID.INSTITUTIONAL, 0.24, 2000,
    ),
    "freedom_house_score": _v(
        "freedom_house_score", "Freedom House aggregate score",
        SourceID.FREEDOM_HOUSE, "0-100", Direction.POSITIVE, DimensionID.INSTITUTIONAL, 0.18, 2000,
    ),
    "wjp_rule_of_law": _v(
        "wjp_rule_of_law", "World Justice Project Rule of Law",
        SourceID.WJP, "0-1", Direction.POSITIVE, DimensionID.INSTITUTIONAL, 0.18, 2007,
    ),
    "pts_terror_politico": _v(
        "pts_terror_politico", "Political Terror Scale",
        SourceID.PTS, "1-5", Direction.NEGATIVE, DimensionID.INSTITUTIONAL, 0.16, 2000,
    ),

    # D4 - comercial
    "exportaciones_pct_pib": _v(
        "exportaciones_pct_pib", "Exportaciones de bienes y servicios",
        SourceID.WDI, "% PIB", Direction.POSITIVE, DimensionID.COMMERCIAL, 0.34, 2000,
    ),
    "desempleo_pct": _v(
        "desempleo_pct", "Tasa de desempleo",
        SourceID.IMF, "%", Direction.NEGATIVE, DimensionID.COMMERCIAL, 0.24, 2000,
    ),
    "migrantes_vzla_millones": _v(
        "migrantes_vzla_millones", "Migrantes y refugiados venezolanos",
        SourceID.UNHCR, "millones", Direction.NEGATIVE, DimensionID.COMMERCIAL, 0.24, 2000,
    ),
    "lsci_conectividad_maritima": _v(
        "lsci_conectividad_maritima", "Liner Shipping Connectivity Index",
        SourceID.UNCTAD, "0-100", Direction.POSITIVE, DimensionID.COMMERCIAL, 0.18, 2006,
    ),

    # D5 - humano
    "hdi": _v(
        "hdi", "Indice de Desarrollo Humano",
        SourceID.HDI, "0-1", Direction.POSITIVE, DimensionID.HUMAN, 0.28, 2000,
    ),
    "esperanza_vida_anos": _v(
        "esperanza_vida_anos", "Esperanza de vida al nacer",
        SourceID.WHO, "anos", Direction.POSITIVE, DimensionID.HUMAN, 0.18, 2000,
    ),
    "mortalidad_infantil_x1000": _v(
        "mortalidad_infantil_x1000", "Mortalidad infantil",
        SourceID.WHO, "muertes por 1.000 nacidos vivos", Direction.NEGATIVE, DimensionID.HUMAN, 0.18, 2000,
    ),
    "acceso_electricidad_pct": _v(
        "acceso_electricidad_pct", "Acceso a electricidad",
        SourceID.WDI, "% poblacion", Direction.POSITIVE, DimensionID.HUMAN, 0.18, 2000,
    ),
    "ilo_empleo_informal_pct": _v(
        "ilo_empleo_informal_pct", "Empleo informal",
        SourceID.ILOSTAT, "% empleo", Direction.NEGATIVE, DimensionID.HUMAN, 0.18, 2000,
    ),

    # D6 - percepcion
    "guardian_tono_titulares": _v(
        "guardian_tono_titulares", "Tono de titulares internacionales",
        SourceID.GUARDIAN, "VADER compound", Direction.POSITIVE, DimensionID.PERCEPTION, 0.65, 2000,
    ),
    "guardian_articulos_venezuela": _v(
        "guardian_articulos_venezuela", "Volumen de cobertura internacional",
        SourceID.GUARDIAN, "articulos", Direction.NEGATIVE, DimensionID.PERCEPTION, 0.35, 2000,
    ),

    # Outcome externo, fuera del score.
    "ied_neta_usd": _v(
        "ied_neta_usd", "Inversion extranjera directa neta",
        SourceID.WDI, "USD", Direction.POSITIVE, DimensionID.COMMERCIAL, 0.0, 2000,
        "Outcome externo usado para validacion ICIV -> IED; no entra al score.",
    ),

    # Pulse-only, no score anual.
    "brent_precio_usd": _v(
        "brent_precio_usd", "Precio Brent del petroleo",
        SourceID.FRED, "USD/barril", Direction.POSITIVE, DimensionID.MACRO, 0.0, 2010,
    ),
    "usd_index_broad": _v(
        "usd_index_broad", "Indice amplio del dolar",
        SourceID.FRED, "indice", Direction.NEGATIVE, DimensionID.MACRO, 0.0, 2010,
    ),
    "vix_volatility": _v(
        "vix_volatility", "VIX volatilidad financiera",
        SourceID.FRED, "indice", Direction.NEGATIVE, DimensionID.MACRO, 0.0, 2010,
    ),
    "ust_10y_yield_pct": _v(
        "ust_10y_yield_pct", "Treasury 10Y yield",
        SourceID.FRED, "%", Direction.NEGATIVE, DimensionID.MACRO, 0.0, 2010,
    ),
    "gdelt_cobertura_vol": _v(
        "gdelt_cobertura_vol", "Volumen de cobertura GDELT",
        SourceID.GDELT, "indice", Direction.NEGATIVE, DimensionID.PERCEPTION, 0.0, 2015,
    ),
    "gdelt_tono_noticias": _v(
        "gdelt_tono_noticias", "Tono de cobertura GDELT",
        SourceID.GDELT, "tono", Direction.POSITIVE, DimensionID.PERCEPTION, 0.0, 2015,
    ),
}


def get_variables_by_dimension(dim: DimensionID) -> list[str]:
    """Devuelve variables catalogadas por dimension."""
    return [name for name, meta in CATALOG.items() if meta.dimension == dim]


def get_negative_variables() -> list[str]:
    """Variables donde mayor valor implica peor clima de inversion."""
    return [name for name, meta in CATALOG.items() if meta.direction == Direction.NEGATIVE]


def get_catalog_summary() -> list[dict]:
    """Resumen tabular para reportes y dataset publico."""
    return [
        {
            "variable": name,
            "descripcion": meta.description,
            "fuente": meta.source.value,
            "dimension": meta.dimension.value,
            "peso_dim": meta.dim_weight,
            "direccion": meta.direction.value,
            "desde": meta.available_from,
            "notas": meta.notes,
        }
        for name, meta in CATALOG.items()
    ]
