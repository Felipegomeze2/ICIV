"""
Definición de las 6 dimensiones del ICIV y sus variables.

Este módulo es la fuente de verdad sobre la arquitectura del índice:
qué variables componen cada dimensión y qué peso tiene cada una.

Versión ampliada (mayo 2026): 40 variables en 6 dimensiones.
  D1 Macro:         6 vars  (sum=1.00)
  D2 Energía:       4 vars  (sum=1.00)
  D3 Institucional: 13 vars (sum=1.00)  ← ampliado con V-Dem, WJP, RSF, BTI, etc.
  D4 Comercial:     7 vars  (sum=1.00)  ← ampliado con LSCI, vuelos, remesas
  D5 Capital Humano: 8 vars (sum=1.00)  ← ampliado con salud, GHI, FAO, ILO
  D6 Percepción:    3 vars  (sum=1.00)  ← sin cambios

Nota sobre variables con cobertura parcial (NaN para muchos años):
  El aggregator re-normaliza pesos automáticamente cuando una variable
  tiene NaN en un año dado → los años sin dato no distorsionan el índice.

Pesos iciv_weight: D1=0.25, D2=0.20, D3=0.20, D4=0.15, D5=0.10, D6=0.10
  (validado con AHP, CR=0.0081 < 0.10)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from iciv.data.models import DimensionID


@dataclass(frozen=True)
class VariableWeight:
    """Peso de una variable dentro de su dimensión."""
    column: str
    weight: float   # debe sumar 1.0 con las demás variables de la dimensión


@dataclass(frozen=True)
class Dimension:
    """
    Configuración completa de una dimensión del ICIV.

    Attributes:
        id:          identificador único (DimensionID)
        name:        nombre legible para reportes
        iciv_weight: peso de esta dimensión en el índice final (debe sumar 1.0)
        variables:   variables que la componen con sus pesos internos
        description: justificación metodológica
    """
    id: DimensionID
    name: str
    iciv_weight: float
    variables: list[VariableWeight]
    description: str = ""

    def __post_init__(self) -> None:
        total = sum(v.weight for v in self.variables)
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Dimensión '{self.name}': los pesos de variables deben sumar 1.0, "
                f"pero suman {total:.3f}"
            )

    @property
    def column_names(self) -> list[str]:
        return [v.column for v in self.variables]

    @property
    def weights_dict(self) -> dict[str, float]:
        return {v.column: v.weight for v in self.variables}


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LAS 6 DIMENSIONES — VERSIÓN AMPLIADA (40 variables)
# Los iciv_weight deben sumar 1.0: 0.25+0.20+0.20+0.15+0.10+0.10 = 1.00
# ─────────────────────────────────────────────────────────────────────────────

DIMENSIONS: dict[DimensionID, Dimension] = {

    DimensionID.MACRO: Dimension(
        id=DimensionID.MACRO,
        name="Estabilidad Macroeconómica",
        iciv_weight=0.25,
        description=(
            "Salud del entorno económico general: inflación, crecimiento, reservas, "
            "tipo de cambio. Ampliada con precio WTI (driver externo del ciclo fiscal "
            "venezolano) y tasa Fed Funds (costo de oportunidad de capital global)."
        ),
        variables=[
            VariableWeight("inflacion_deflactor_pib_pct",  0.28),
            VariableWeight("pib_crecimiento_real_pct",     0.22),
            VariableWeight("reservas_internacionales_usd", 0.18),
            VariableWeight("tipo_cambio_oficial_lcu_usd",  0.12),
            VariableWeight("wti_precio_usd",               0.12),
            VariableWeight("tasa_fed_funds_pct",           0.08),
        ],
    ),

    DimensionID.ENERGY: Dimension(
        id=DimensionID.ENERGY,
        name="Sector Energético y Petróleo",
        iciv_weight=0.20,
        description=(
            "Venezuela es petro-dependiente. Esta dimensión captura el estado "
            "de la industria petrolera como motor de ingresos fiscales y divisas. "
            "Ampliada con luminosidad nocturna satelital (VIIRS/DMSP) como proxy "
            "independiente del colapso del sistema eléctrico y la actividad real."
        ),
        variables=[
            VariableWeight("petroleo_crudo_produccion_tbpd", 0.45),
            VariableWeight("gas_natural_produccion_bcf",      0.25),
            VariableWeight("electricidad_generacion_bkwh",    0.15),
            VariableWeight("luminosidad_nocturna_idx",         0.15),
        ],
    ),

    DimensionID.INSTITUTIONAL: Dimension(
        id=DimensionID.INSTITUTIONAL,
        name="Entorno Institucional y Legal",
        iciv_weight=0.20,
        description=(
            "Seguridad jurídica, corrupción, gobernanza, Estado de derecho y "
            "riesgo político. Ampliada con V-Dem (democracia liberal), WJP (rule "
            "of law), Fragile States Index, RSF (prensa), BTI (gobernanza), Basel "
            "AML (cumplimiento financiero) y UCDP (conflicto armado)."
        ),
        variables=[
            # Fuentes gold-standard de corrupción y gobernanza
            VariableWeight("cpi_score",            0.14),
            VariableWeight("wgi_promedio_sc",       0.14),
            # Libertad económica y democracia
            VariableWeight("ief_overall_score",     0.11),
            VariableWeight("freedom_house_score",   0.10),
            VariableWeight("vdem_libdem_index",     0.10),
            # Estado de derecho
            VariableWeight("wjp_rule_of_law",       0.09),
            # Fragilidad y estabilidad del Estado
            VariableWeight("fragile_states_index",  0.08),
            # Terror político y represión
            VariableWeight("pts_terror_politico",   0.07),
            # Sanciones internacionales
            VariableWeight("ofac_sanciones_count",  0.05),
            # Libertad de prensa
            VariableWeight("rsf_press_freedom",     0.04),
            # Gobernanza transformacional
            VariableWeight("bti_governance_index",  0.04),
            # Riesgo financiero / lavado de activos
            VariableWeight("basel_aml_index",       0.03),
            # Conflicto armado (bajo peso: Venezuela no tiene conflicto formal)
            VariableWeight("ucdp_conflicto_idx",    0.01),
        ],
    ),

    DimensionID.COMMERCIAL: Dimension(
        id=DimensionID.COMMERCIAL,
        name="Apertura Comercial y Financiera",
        iciv_weight=0.15,
        description=(
            "Capacidad operativa en Venezuela: flujos de IED, comercio exterior, "
            "mercado laboral y conectividad logística. Ampliada con conectividad "
            "marítima (LSCI), remesas recibidas y vuelos internacionales."
        ),
        variables=[
            VariableWeight("ied_neta_usd",               0.28),
            VariableWeight("exportaciones_pct_pib",      0.22),
            VariableWeight("desempleo_pct",              0.16),
            VariableWeight("migrantes_vzla_millones",    0.14),
            VariableWeight("lsci_conectividad_maritima", 0.10),
            VariableWeight("remesas_recibidas_usd",      0.06),
            VariableWeight("vuelos_aerolineas_int_count",0.04),
        ],
    ),

    DimensionID.HUMAN: Dimension(
        id=DimensionID.HUMAN,
        name="Capital Humano e Infraestructura Social",
        iciv_weight=0.10,
        description=(
            "Disponibilidad de fuerza laboral calificada, salud pública y "
            "condiciones de vida. Ampliada con esperanza de vida, mortalidad "
            "infantil, seguridad alimentaria (GHI, FAO) y empleo informal (ILO)."
        ),
        variables=[
            VariableWeight("hdi",                             0.24),
            VariableWeight("esperanza_vida_anos",             0.16),
            VariableWeight("mortalidad_infantil_x1000",       0.14),
            VariableWeight("tasa_alfabetizacion_adulta_pct",  0.14),
            VariableWeight("acceso_electricidad_pct",         0.14),
            VariableWeight("ghi_score",                       0.08),
            VariableWeight("fao_calorias_per_capita",         0.06),
            VariableWeight("ilo_empleo_informal_pct",         0.04),
        ],
    ),

    DimensionID.PERCEPTION: Dimension(
        id=DimensionID.PERCEPTION,
        name="Percepción Internacional",
        iciv_weight=0.10,
        description=(
            "Imagen de Venezuela en medios globales y búsquedas de inversión. "
            "Ampliada con Google Trends como proxy nowcasting de interés global "
            "en Venezuela como destino económico (Choi & Varian, 2012)."
        ),
        variables=[
            VariableWeight("guardian_tono_titulares",      0.45),
            VariableWeight("guardian_articulos_venezuela", 0.25),
            VariableWeight("google_trends_vzla",           0.30),
        ],
    ),
}


def validate_dimension_weights() -> bool:
    """Verifica que los pesos de dimensiones sumen exactamente 1.0."""
    total = sum(d.iciv_weight for d in DIMENSIONS.values())
    if not (0.99 <= total <= 1.01):
        raise ValueError(f"Los pesos de las dimensiones deben sumar 1.0, suman {total:.3f}")
    return True


# Validar al importar el módulo
validate_dimension_weights()
