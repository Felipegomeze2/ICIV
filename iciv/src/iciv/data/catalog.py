"""Catalogo central de variables publicadas por el ICIV vigente.

El score anual se define en `iciv.index.dimensions`. Este catalogo aporta los
metadatos de esas variables, del outcome externo IED y de las senales mensuales
usadas por Pulse. Los campos con peso 0 son auxiliares o exclusivos de Pulse;
solo DIMENSIONS define que variables entran al indice anual.
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
    "inflacion_ipc_imf_pct": _v(
        "inflacion_ipc_imf_pct", "Inflacion de precios al consumidor (FMI)",
        SourceID.IMF, "% anual", Direction.NEGATIVE, DimensionID.MACRO, 0.40, 2000,
        "IMF WEO PCPIPCH: variacion porcentual anual del IPC, no deflactor del PIB. "
        "Incluye estimaciones y proyecciones del proveedor; el estado se declara por observacion. "
        "Se transforma a log10 antes de normalizar; los valores originales se conservan.",
    ),
    "pib_crecimiento_real_pct": _v(
        "pib_crecimiento_real_pct", "Crecimiento real del PIB",
        SourceID.WDI, "%", Direction.POSITIVE, DimensionID.MACRO, 0.3143, 2002,
    ),
    "reservas_internacionales_usd": _v(
        "reservas_internacionales_usd", "Reservas internacionales",
        SourceID.WDI, "USD", Direction.POSITIVE, DimensionID.MACRO, 0.0, 2000,
        "Faltantes recientes se muestran como faltantes; no se hace forward-fill.",
    ),
    "tipo_cambio_oficial_lcu_usd": _v(
        "tipo_cambio_oficial_lcu_usd", "Tipo de cambio oficial (unidad original WDI)",
        SourceID.WDI, "BsF/USD equivalente", Direction.NEGATIVE, DimensionID.MACRO, 0.0, 2000,
    ),
    "wti_precio_usd": _v(
        "wti_precio_usd", "Precio WTI del petroleo",
        SourceID.FRED, "USD/barril", Direction.POSITIVE, DimensionID.MACRO, 0.1714, 2000,
    ),
    "tasa_fed_funds_pct": _v(
        "tasa_fed_funds_pct", "Tasa efectiva de fondos federales de EE. UU.",
        SourceID.FRED, "%", Direction.NEGATIVE, DimensionID.MACRO, 0.1143, 2000,
    ),

    # D2 - energia
    "petroleo_crudo_produccion_tbpd": _v(
        "petroleo_crudo_produccion_tbpd", "Produccion de crudo y condensado de arrendamiento (EIA producto 57)",
        SourceID.EIA, "mil barriles/dia", Direction.POSITIVE, DimensionID.ENERGY, 0.75, 2000,
    ),
    "gas_natural_produccion_bcf": _v(
        "gas_natural_produccion_bcf", "Produccion de gas natural",
        SourceID.EIA, "BCF", Direction.POSITIVE, DimensionID.ENERGY, 0.0, 2000,
    ),
    "electricidad_generacion_bkwh": _v(
        "electricidad_generacion_bkwh", "Generacion electrica",
        SourceID.EIA, "bkWh", Direction.POSITIVE, DimensionID.ENERGY, 0.0, 2000,
    ),
    "luminosidad_nocturna_idx": _v(
        "luminosidad_nocturna_idx", "Luminosidad nocturna satelital",
        SourceID.VIIRS, "nW/cm2/sr", Direction.POSITIVE, DimensionID.ENERGY, 0.25, 2014,
        "NASA Black Marble VNP46A3, media nacional con mascara poligonal exacta. "
        "Sustituyo a la serie de Li et al. el 2026-08-11: mismo fenomeno con 2 meses "
        "de rezago en vez de 2 anios. Cubre 2014-2026; no se empalma con la anterior.",
    ),

    # D3 - institucional
    "cpi_score": _v(
        "cpi_score", "Indice de percepcion de corrupcion",
        SourceID.CPI, "0-100", Direction.POSITIVE, DimensionID.INSTITUTIONAL, 0.24, 2012,
        "CPI comparable solo desde 2012; registros anteriores conservados en raw y excluidos del indice.",
    ),
    "wgi_promedio_sc": _v(
        "wgi_promedio_sc", "Promedio WGI de gobernanza",
        SourceID.WGI, "percentil 0-100", Direction.POSITIVE, DimensionID.INSTITUTIONAL, 0.24, 2000,
    ),
    "freedom_house_score": _v(
        "freedom_house_score", "Freedom House aggregate score",
        SourceID.FREEDOM_HOUSE, "0-100", Direction.POSITIVE, DimensionID.INSTITUTIONAL, 0.18, 2012,
    ),
    "wjp_rule_of_law": _v(
        "wjp_rule_of_law", "World Justice Project Rule of Law",
        SourceID.WJP, "0-1", Direction.POSITIVE, DimensionID.INSTITUTIONAL, 0.18, 2013,
        "Ediciones dobles asignadas solo al año final (2012-2013 a 2013; 2017-2018 a 2018).",
    ),
    "pts_terror_politico": _v(
        "pts_terror_politico", "Political Terror Scale",
        SourceID.PTS, "1-5", Direction.NEGATIVE, DimensionID.INSTITUTIONAL, 0.16, 2000,
    ),

    # D4 - comercial
    "exportaciones_pct_pib": _v(
        "exportaciones_pct_pib", "Exportaciones de bienes y servicios",
        SourceID.WDI, "% PIB", Direction.POSITIVE, DimensionID.COMMERCIAL, 0.4474, 2000,
    ),
    "desempleo_pct": _v(
        "desempleo_pct", "Tasa de desempleo",
        SourceID.IMF, "%", Direction.NEGATIVE, DimensionID.COMMERCIAL, 0.0, 2000,
    ),
    # OJO: la API de UNHCR con coo=VEN devuelve refugiados + solicitantes de
    # asilo REGISTRADOS (~1.6M en 2025), no el total de la diáspora venezolana
    # (~7.9M según R4V/OIM, que incluye migrantes no registrados). La etiqueta
    # anterior, "Migrantes y refugiados venezolanos", sobredimensionaba lo que
    # la serie realmente mide. Ver scripts/fetch_unhcr.py, nota de cobertura.
    "migrantes_vzla_millones": _v(
        "migrantes_vzla_millones", "Refugiados y solicitantes de asilo venezolanos",
        SourceID.UNHCR, "millones", Direction.NEGATIVE, DimensionID.COMMERCIAL, 0.3158, 2000,
    ),
    "lsci_conectividad_maritima": _v(
        "lsci_conectividad_maritima", "Liner Shipping Connectivity Index",
        SourceID.UNCTAD, "indice (base promedio Q1 2023 = 100)", Direction.POSITIVE, DimensionID.COMMERCIAL, 0.2368, 2006,
        "No es una escala acotada 0-100. Promedio de trimestres publicados; años parciales se identifican.",
    ),

    # D5 - humano
    "hdi": _v(
        "hdi", "Indice de Desarrollo Humano",
        SourceID.HDI, "0-1", Direction.POSITIVE, DimensionID.HUMAN, 0.28, 2000,
    ),
    # Migradas de WHO GHO al World Bank el 2026-08-11 (SP.DYN.LE00.IN /
    # SP.DYN.IMRT.IN): la OMS se quedaba en 2021 y 2023, el WB llega a 2024.
    "esperanza_vida_anos": _v(
        "esperanza_vida_anos", "Esperanza de vida al nacer",
        SourceID.WDI, "anos", Direction.POSITIVE, DimensionID.HUMAN, 0.18, 2000,
    ),
    "mortalidad_infantil_x1000": _v(
        "mortalidad_infantil_x1000", "Mortalidad infantil",
        SourceID.WDI, "muertes por 1.000 nacidos vivos", Direction.NEGATIVE, DimensionID.HUMAN, 0.18, 2000,
    ),
    "acceso_electricidad_pct": _v(
        "acceso_electricidad_pct", "Acceso a electricidad",
        SourceID.WDI, "% poblacion", Direction.POSITIVE, DimensionID.HUMAN, 0.18, 2000,
    ),
    "empleo_vulnerable_oit_pct": _v(
        "empleo_vulnerable_oit_pct", "Empleo vulnerable (estimacion modelada OIT)",
        SourceID.WDI, "% empleo", Direction.NEGATIVE, DimensionID.HUMAN, 0.18, 2000,
        "OIT ILOEST distribuido por WDI SL.EMP.VULN.ZS: cuenta propia y familiares auxiliares. "
        "No equivale a empleo informal ni a una observacion directa; no sustituye otras series.",
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
    "petroleo_liquidos_totales_tbpd": _v(
        "petroleo_liquidos_totales_tbpd", "Produccion total de petroleo y otros liquidos",
        SourceID.EIA, "mil barriles/dia", Direction.POSITIVE, DimensionID.ENERGY, 0.0, 2010,
        "EIA producto 53 mensual; concepto distinto del crudo+condensado anual (producto 57).",
    ),
    "crudo_dubai_usd": _v(
        "crudo_dubai_usd", "Precio del crudo Dubai",
        SourceID.WDI, "USD/barril", Direction.POSITIVE, DimensionID.MACRO, 0.0, 2010,
        "World Bank Commodity Markets Pink Sheet, no API WDI. Benchmark externo, no precio Merey.",
    ),
    "em_bond_spread_pct": _v(
        "em_bond_spread_pct", "Diferencial corporativo de mercados emergentes",
        SourceID.FRED, "puntos porcentuales", Direction.NEGATIVE, DimensionID.MACRO, 0.0, 2023,
        "ICE BofA BAMLEMCBPIOAS, distribuido por FRED. Ventana historica limitada por licencia.",
    ),
    "importaciones_eeuu_crudo_ven_tbpd": _v(
        "importaciones_eeuu_crudo_ven_tbpd", "Importaciones de crudo venezolano en EE. UU.",
        SourceID.FRED, "mil barriles/dia", Direction.POSITIVE, DimensionID.COMMERCIAL, 0.0, 2010,
        "EIA IR14270 distribuido por FRED. Comercio espejo fisico; no representa comercio total venezolano.",
    ),
    "importaciones_eeuu_productos_ven_tbpd": _v(
        "importaciones_eeuu_productos_ven_tbpd", "Importaciones de productos petroleros venezolanos en EE. UU.",
        SourceID.FRED, "mil barriles/dia", Direction.POSITIVE, DimensionID.COMMERCIAL, 0.0, 2010,
        "EIA IR14260 distribuido por FRED. Volumen fisico; no equivale a valor comercial ni a actividad refinadora directa.",
    ),
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
