"""
Definición de las 6 dimensiones del ICIV y sus variables.

Este módulo es la fuente de verdad sobre la arquitectura del índice:
qué variables componen cada dimensión y qué peso tiene cada una.

Version core (mayo 2026): 26 variables en 6 dimensiones.
  D1 Macro:         6 vars  (sum=1.00)
  D2 Energía:       4 vars  (sum=1.00)
  D3 Institucional: 5 vars  (sum=1.00)
  D4 Comercial:     4 vars  (sum=1.00)
  D5 Capital Humano:5 vars  (sum=1.00)
  D6 Percepción:    2 vars  (sum=1.00)

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
# CONFIGURACION DE LAS 6 DIMENSIONES - VERSION CORE (26 variables)
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
            "Seguridad juridica, corrupcion, gobernanza, Estado de derecho y "
            "riesgo politico. El core conserva indicadores internacionales con "
            "cobertura suficiente y funciones no redundantes."
        ),
        variables=[
            # Fuentes gold-standard de corrupción y gobernanza
            VariableWeight("cpi_score",             0.24),
            VariableWeight("wgi_promedio_sc",       0.24),
            # Libertades y estado de derecho
            VariableWeight("freedom_house_score",   0.18),
            VariableWeight("wjp_rule_of_law",       0.18),
            # Represion politica con cobertura historica util
            VariableWeight("pts_terror_politico",   0.16),
        ],
    ),

    DimensionID.COMMERCIAL: Dimension(
        id=DimensionID.COMMERCIAL,
        name="Apertura Comercial y Financiera",
        iciv_weight=0.15,
        description=(
            "Capacidad operativa en Venezuela: comercio exterior, mercado laboral, "
            "migracion y conectividad logistica. La IED se reserva como outcome "
            "externo para validar el indice, no como componente del score."
        ),
        variables=[
            VariableWeight("exportaciones_pct_pib",      0.34),
            VariableWeight("desempleo_pct",              0.24),
            VariableWeight("migrantes_vzla_millones",    0.24),
            VariableWeight("lsci_conectividad_maritima", 0.18),
        ],
    ),

    DimensionID.HUMAN: Dimension(
        id=DimensionID.HUMAN,
        name="Capital Humano e Infraestructura Social",
        iciv_weight=0.10,
        description=(
            "Disponibilidad de fuerza laboral, salud publica, infraestructura "
            "social y vulnerabilidad laboral con series internacionales de "
            "cobertura suficiente."
        ),
        variables=[
            VariableWeight("hdi",                             0.28),
            VariableWeight("esperanza_vida_anos",             0.18),
            VariableWeight("mortalidad_infantil_x1000",       0.18),
            VariableWeight("acceso_electricidad_pct",         0.18),
            VariableWeight("ilo_empleo_informal_pct",         0.18),
        ],
    ),

    DimensionID.PERCEPTION: Dimension(
        id=DimensionID.PERCEPTION,
        name="Percepción Internacional",
        iciv_weight=0.10,
        description=(
            "Imagen de Venezuela en cobertura internacional. El core anual "
            "usa Guardian por su serie reproducible; otras senales de noticias "
            "se reservan para el Pulse y el laboratorio."
        ),
        variables=[
            VariableWeight("guardian_tono_titulares",      0.65),
            VariableWeight("guardian_articulos_venezuela", 0.35),
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
