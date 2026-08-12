"""
ICIVAggregator — calcula el puntaje final del índice y sus sub-scores.

Responsabilidad única: tomar el DataFrame normalizado (0–100) y producir:
  1. Puntaje por dimensión (D1–D5)
  2. Puntaje ICIV compuesto
  3. Categoría de riesgo ('Alto Riesgo', 'Riesgo Moderado', etc.)

Soporta dos métodos de agregación:
  - 'linear':    ICIV = Σ(w_i × D_i)  — suma ponderada lineal
  - 'geometric': ICIV = Π(D_i ^ w_i)  — media geométrica ponderada
    (penaliza más las dimensiones extremadamente bajas)
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np
import pandas as pd

from iciv.index.dimensions import DIMENSIONS, Dimension
from iciv.data.models import DimensionID
from iciv.index.weighting.base import WeightingStrategy
from iciv.index.weighting.fixed_weights import FixedWeights

logger = logging.getLogger(__name__)

AggregationMethod = Literal["linear", "geometric"]

# Cobertura mínima de una DIMENSIÓN para publicar su score (fracción 0–1).
#
# Motivo (2026-08-11): el agregador publicaba el score de una dimensión con
# cualquier variable disponible, sin piso. En 2025 eso daba
# D5_capital_humano = 0.0 apoyado en UNA sola variable —
# ilo_empleo_informal_pct, el 18% del peso de la dimensión— y la barra del
# dashboard lo dibujaba con la misma autoridad que una dimensión con 100% de
# cobertura. Lo mismo con D4_comercial en 2026 (23.7%, solo LSCI).
#
# 0.50 = la mitad del peso AHP de la dimensión, el mismo criterio que ya usaba
# SectorRadar._base_score. Por debajo del umbral la dimensión queda NaN y sus
# pesos se redistribuyen, igual que cualquier otra dimensión sin dato.
#
# EFECTO SECUNDARIO CONOCIDO: descartar una dimensión baja SUBE el índice del
# año, porque la redistribución de pesos elimina justamente el peor dato. Por
# eso el score de un año con poca cobertura se marca 'Provisional' y el
# dashboard suprime el delta interanual (ver main.py, tarjeta 'Índice anual').
# La cobertura por dimensión se expone en las columnas cobertura_D*.
MIN_DIMENSION_COVERAGE = 0.50

# Tabla de categorías de riesgo.
#
# ESCALA RELATIVA, NO COMPARABLE ENTRE PAÍSES (corregido 2026-08-11)
# ------------------------------------------------------------------
# Cada variable se normaliza Min-Max sobre el rango histórico DE VENEZUELA
# 2000-2026. Por tanto 100 = el mejor registro de Venezuela en el periodo y
# 0 = el peor, no un óptimo internacional.
#
# Las etiquetas anteriores decían cosas como "clima comparable a mercados
# emergentes estables", que es una afirmación entre países que esta escala no
# puede sostener: nunca se normalizó contra otros países. Se reescribieron para
# que digan lo que el número realmente significa. Para poder comparar con otros
# países haría falta normalizar sobre un panel multi-país (pendiente).
#
# Ver docs/METODOLOGIA.md §1.
RISK_CATEGORIES = [
    (0,  30,  "🔴 Alto Riesgo",
     "Entre los peores registros de la propia serie venezolana. No se recomienda inversión directa."),
    (31, 50,  "🟠 Riesgo Moderado-Alto",
     "Por debajo de la media histórica de Venezuela. Solo sectores con alta tolerancia al riesgo."),
    (51, 65,  "🟡 Riesgo Moderado",
     "En torno a la media histórica de Venezuela. Viable con due diligence reforzado."),
    (66, 80,  "🟢 Bajo Riesgo",
     "Por encima de la media histórica de Venezuela. Favorable en términos de su propia serie."),
    (81, 100, "🟢🟢 Muy Bajo Riesgo",
     "Cerca del mejor registro histórico de Venezuela. No implica equivalencia con otros países."),
]


def _get_risk_category(score: float) -> str:
    # Usar < hi excepto en el último rango para cubrir el espacio continuo 0-100
    for i, (lo, hi, label, _) in enumerate(RISK_CATEGORIES):
        if i < len(RISK_CATEGORIES) - 1:
            if lo <= score < hi + 1:
                return label
        else:
            if lo <= score <= hi:
                return label
    return "Sin categoria"


class ICIVAggregator:
    """
    Calcula el ICIV y sus puntajes por dimensión.

    Args:
        method:   método de agregación ('linear' o 'geometric')
        strategy: estrategia de ponderación. Si None, usa FixedWeights.
        min_dimension_coverage: fracción MÍNIMA del peso de una dimensión que
                  debe estar cubierta por variables con dato real para publicar
                  su score. Por debajo del umbral la dimensión queda NaN.

    Ejemplo:
        aggregator = ICIVAggregator(method="linear")
        results = aggregator.compute(df_normalized)
        print(results[["año", "iciv_score", "iciv_categoria"]])
    """

    def __init__(
        self,
        method: AggregationMethod = "linear",
        strategy: WeightingStrategy | None = None,
        min_dimension_coverage: float = MIN_DIMENSION_COVERAGE,
    ) -> None:
        self.method = method
        self.strategy = strategy or FixedWeights()
        self.min_dimension_coverage = float(min_dimension_coverage)

    def compute(self, df_normalized: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula los puntajes completos del ICIV.

        Args:
            df_normalized: DataFrame con variables normalizadas 0–100,
                           más columna 'año'.

        Returns:
            DataFrame con columnas:
              - año
              - d1_macro, d2_energia, d3_institucional, d4_comercial, d5_capital_humano
              - iciv_score
              - iciv_categoria
        """
        result = pd.DataFrame({"año": df_normalized["año"]})

        # 1. Calcular puntaje y cobertura por dimensión.
        #    La cobertura es la fracción del peso de la dimensión cubierta por
        #    variables con dato real ese año; se publica para que el dashboard
        #    pueda distinguir "0 = el peor registro" de "0 con 18% de cobertura".
        for dim_id, dim in DIMENSIONS.items():
            scores, cov = self._score_dimension(df_normalized, dim)
            result[dim_id.value] = scores
            result[f"cobertura_{dim_id.value}"] = (cov * 100).round(1)

        # 2. Determinar pesos de dimensiones
        # Si la estrategia tiene resultados AHP (dimension_result_), usarlos.
        # De lo contrario, usar los pesos hardcodeados de DIMENSIONS.
        dim_cols = [d.value for d in DIMENSIONS]
        dim_result = getattr(self.strategy, "dimension_result_", None)
        if dim_result is not None and dim_result.get("weights"):
            dim_weights = {k: v for k, v in dim_result["weights"].items() if k in dim_cols}
            # Normalizar por si faltan dimensiones
            total_w = sum(dim_weights.values())
            if total_w > 0:
                dim_weights = {k: v / total_w for k, v in dim_weights.items()}
        else:
            dim_weights = {d.value: DIMENSIONS[d].iciv_weight for d in DIMENSIONS}

        result["iciv_score"] = result.apply(
            lambda row: self._aggregate_dimensions(row, dim_cols, dim_weights),
            axis=1,
        )
        result["iciv_score"] = result["iciv_score"].round(2)

        # 3. Categoría de riesgo
        result["iciv_categoria"] = result["iciv_score"].apply(
            lambda s: _get_risk_category(s) if pd.notna(s) else "Sin datos"
        )

        # 4. Índice de cobertura temporal (metodología de cobertura)
        # = fracción del peso ICIV total cubierta por variables con dato real ese año.
        # Útil para comunicar confianza en el score: 2000-2005 < 2015-2026.
        # Peso ICIV de una variable = dim.iciv_weight × v.weight_dentro_dimensión.
        var_iciv_weights: list[tuple[str, float]] = []
        for dim_id, dim in DIMENSIONS.items():
            for v in dim.variables:
                if v.column in df_normalized.columns and df_normalized[v.column].notna().any():
                    var_iciv_weights.append((v.column, dim.iciv_weight * v.weight))

        total_iciv_w = sum(w for _, w in var_iciv_weights) or 1.0

        def _coverage_row(row: pd.Series) -> float:
            covered = sum(w for col, w in var_iciv_weights if pd.notna(row.get(col)))
            return round(covered / total_iciv_w * 100, 1)

        try:
            result["cobertura_pct"] = df_normalized.apply(_coverage_row, axis=1)
        except Exception:
            result["cobertura_pct"] = np.nan

        logger.info(
            "ICIVAggregator (%s): %d años calculados, rango %.1f–%.1f",
            self.method,
            result["iciv_score"].notna().sum(),
            result["iciv_score"].min(),
            result["iciv_score"].max(),
        )
        return result

    # ── Métodos privados ──────────────────────────────────────────────────────

    def _score_dimension(
        self, df: pd.DataFrame, dim: Dimension
    ) -> tuple[pd.Series, pd.Series]:
        """Calcula el puntaje de una dimensión como suma ponderada de sus variables.

        Devuelve (scores, cobertura) donde cobertura es la fracción 0–1 del peso
        de la dimensión cubierta por variables con dato real ese año. Si la
        cobertura cae por debajo de self.min_dimension_coverage el score se
        publica como NaN: un promedio sobre una fracción mínima del peso no es
        representativo de la dimensión (ver MIN_DIMENSION_COVERAGE).

        Metodología de cobertura temporal:
          Para cada año individualmente, solo se usan las variables que tienen dato
          real (o interpolado entre observaciones reales) ese año específico.
          Si una variable tiene NaN ese año (fuera de su rango de cobertura),
          su peso se redistribuye entre las demás variables disponibles ESE año.
          Esto garantiza que nunca se inventa un valor para rellenar cobertura parcial.

        Consecuencia esperada: los scores de años con poca cobertura (p. ej. 2000–2005)
        reflejan solo las variables con datos históricos disponibles — no se infla
        ni deflacta artificialmente el score de años tempranos.
        """
        # Candidatas: variables con al menos 1 valor real en toda la serie
        candidate_vars = [
            v for v in dim.variables
            if v.column in df.columns and df[v.column].notna().any()
        ]

        if not candidate_vars:
            logger.warning("Dimensión '%s': ninguna variable con datos disponibles", dim.name)
            nan_series = pd.Series(np.nan, index=df.index)
            return nan_series, pd.Series(0.0, index=df.index)

        # Denominador de cobertura: peso total de las variables que la dimensión
        # PODRÍA cubrir (las que tienen al menos un dato en toda la serie).
        candidate_weight = sum(v.weight for v in candidate_vars) or 1.0

        def _row(row: pd.Series) -> tuple[float, float]:
            """(score, cobertura) de la dimensión para una fila (año) específica."""
            present = [
                (v, float(row[v.column]))
                for v in candidate_vars
                if pd.notna(row.get(v.column))
            ]
            if not present:
                return np.nan, 0.0
            total_w = sum(v.weight for v, _ in present)
            coverage = total_w / candidate_weight
            if total_w == 0.0:
                return np.nan, coverage
            if coverage < self.min_dimension_coverage:
                # Cobertura insuficiente: no se publica score, pero SÍ la
                # cobertura, para que el consumidor sepa por qué falta.
                return np.nan, coverage
            return round(sum(val * v.weight / total_w for v, val in present), 2), coverage

        pairs = df.apply(_row, axis=1)
        scores = pairs.map(lambda t: t[0])
        coverage = pairs.map(lambda t: t[1])
        return scores, coverage

    def _aggregate_dimensions(
        self,
        row: pd.Series,
        dim_cols: list[str],
        dim_weights: dict[str, float],
    ) -> float:
        """Agrega los puntajes de dimensión en el ICIV final."""
        valid_dims = [(col, dim_weights[col]) for col in dim_cols if pd.notna(row.get(col))]

        if not valid_dims:
            return np.nan

        # Re-normalizar pesos si alguna dimensión tiene NaN
        total_w = sum(w for _, w in valid_dims)
        norm_dims = [(col, w / total_w) for col, w in valid_dims]

        if self.method == "linear":
            return sum(row[col] * w for col, w in norm_dims)

        if self.method == "geometric":
            # Evitar log(0): recortar valores en [0.1, 100]
            vals = [max(row[col], 0.1) for col, _ in norm_dims]
            weights = [w for _, w in norm_dims]
            return float(np.prod([v ** w for v, w in zip(vals, weights)]))

        raise ValueError(f"Método de agregación no reconocido: {self.method}")
