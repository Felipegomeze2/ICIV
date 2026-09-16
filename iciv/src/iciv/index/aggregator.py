"""Annual ICIV aggregation over a fixed, versioned indicator universe.

Missing observations are never filled. Available weights are redistributed only
for scoring; coverage retains the full denominator of the selected strategy.
The score is relative to Venezuela's historical normalization, not a calibrated
investment-risk probability or an investment recommendation.
"""
from __future__ import annotations

import logging
from typing import Literal
import numpy as np
import pandas as pd
from iciv.index.dimensions import DIMENSIONS, Dimension
from iciv.index.weighting.base import WeightingStrategy
from iciv.index.weighting.ahp_weights import AHPWeights

logger = logging.getLogger(__name__)
AggregationMethod = Literal["linear", "geometric"]
MIN_DIMENSION_COVERAGE = 0.50

# Descriptive design cutoffs, not calibrated country-risk thresholds.
RISK_CATEGORIES = [
    (0, 30, "Muy desfavorable", "Tramo inferior de la escala histórica venezolana."),
    (31, 50, "Desfavorable", "Tramo bajo de la escala histórica venezolana."),
    (51, 65, "Intermedio", "Tramo intermedio de la escala histórica venezolana."),
    (66, 80, "Favorable", "Tramo alto de la escala histórica venezolana."),
    (81, 100, "Muy favorable", "Tramo superior de la escala histórica venezolana."),
]


def _get_risk_category(score: float) -> str:
    for i, (lo, hi, label, _) in enumerate(RISK_CATEGORIES):
        if lo <= score < hi + 1 and (i < len(RISK_CATEGORIES) - 1 or score <= hi):
            return label
    return "Sin categoria"


class ICIVAggregator:
    """Compute dimension and composite scores using AHP by default.

    Strategies return final variable weights over the full indicator universe;
    both intra and inter dimension weights are derived from those weights.
    """
    def __init__(self, method: AggregationMethod = "linear",
                 strategy: WeightingStrategy | None = None,
                 min_dimension_coverage: float = MIN_DIMENSION_COVERAGE) -> None:
        self.method = method
        self.strategy = strategy if strategy is not None else AHPWeights()
        self.min_dimension_coverage = float(min_dimension_coverage)
        if not 0 <= self.min_dimension_coverage <= 1:
            raise ValueError("min_dimension_coverage debe estar entre 0 y 1")
        self.variable_weights_: dict[str, float] = {}
        self.dimension_weights_: dict[str, float] = {}

    def compute(self, df_normalized: pd.DataFrame) -> pd.DataFrame:
        """Return scores and weighted coverage (0–100).

        Observed coverage counts all available indicator values. Effective
        coverage counts only variables in dimensions passing the coverage floor.
        ``cobertura_pct`` aliases effective coverage for reliability filtering.
        These fields measure availability, not observation/finality status.
        """
        universe = {v.column for d in DIMENSIONS.values() for v in d.variables}
        weights = self.strategy.compute_weights(df_normalized)
        unknown = set(weights) - universe
        if unknown:
            raise ValueError(f"Pesos de variables fuera del catálogo: {sorted(unknown)}")
        if any(not np.isfinite(w) or w < 0 for w in weights.values()):
            raise ValueError("Los pesos deben ser finitos y no negativos")
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("Los pesos deben sumar un valor positivo")
        self.variable_weights_ = {c: weights.get(c, 0.0) / total for c in sorted(universe)}
        self.dimension_weights_ = {
            dim_id.value: sum(self.variable_weights_[v.column] for v in dim.variables)
            for dim_id, dim in DIMENSIONS.items()
        }
        result = pd.DataFrame({"año": df_normalized["año"]})
        observed = pd.Series(0.0, index=result.index)
        effective = pd.Series(0.0, index=result.index)
        published_weight = pd.Series(0.0, index=result.index)
        published_count = pd.Series(0, index=result.index, dtype=int)
        for dim_id, dim in DIMENSIONS.items():
            scores, coverage = self._score_dimension(df_normalized, dim)
            result[dim_id.value] = scores
            result[f"cobertura_{dim_id.value}"] = (coverage * 100).round(1)
            dim_w = self.dimension_weights_[dim_id.value]
            available_mass = coverage * dim_w
            observed += available_mass
            effective += available_mass.where(scores.notna(), 0.0)
            published_weight += scores.notna().astype(float) * dim_w
            published_count += (scores.notna() & (dim_w > 0)).astype(int)
        dim_cols = list(self.dimension_weights_)
        result["iciv_score"] = result.apply(
            lambda row: self._aggregate_dimensions(row, dim_cols, self.dimension_weights_), axis=1
        ).round(2)
        result["iciv_categoria"] = result["iciv_score"].map(
            lambda s: _get_risk_category(s) if pd.notna(s) else "Sin datos"
        )
        result["cobertura_observada_pct"] = (100 * observed).round(1)
        result["cobertura_efectiva_pct"] = (100 * effective).round(1)
        result["cobertura_pct"] = result["cobertura_efectiva_pct"]
        result["peso_dimensiones_publicadas_pct"] = (100 * published_weight).round(1)
        result["dimensiones_publicadas"] = published_count
        logger.info("ICIVAggregator (%s): %d años con puntaje", self.method, result.iciv_score.notna().sum())
        return result

    def _score_dimension(self, df: pd.DataFrame, dim: Dimension) -> tuple[pd.Series, pd.Series]:
        """Reweight available observations, retaining the fixed denominator."""
        weights = {v.column: self.variable_weights_.get(v.column, 0.0) for v in dim.variables}
        denominator = sum(weights.values())
        if denominator <= 0:
            return pd.Series(np.nan, index=df.index), pd.Series(0.0, index=df.index)
        values = df.reindex(columns=list(weights)).apply(pd.to_numeric, errors="raise")
        values = values.replace([np.inf, -np.inf], np.nan)
        available = values.notna().mul(pd.Series(weights)).sum(axis=1)
        coverage = available / denominator
        numerator = values.mul(pd.Series(weights)).sum(axis=1, min_count=1)
        scores = numerator.div(available.where(available > 0))
        scores = scores.where(coverage + 1e-12 >= self.min_dimension_coverage)
        return scores.round(2), coverage

    def _aggregate_dimensions(self, row: pd.Series, dim_cols: list[str],
                              dim_weights: dict[str, float]) -> float:
        valid = [(c, dim_weights.get(c, 0.0)) for c in dim_cols
                 if pd.notna(row.get(c)) and dim_weights.get(c, 0.0) > 0]
        if not valid:
            return np.nan
        total = sum(w for _, w in valid)
        if self.method == "linear":
            return sum(row[c] * w / total for c, w in valid)
        if self.method == "geometric":
            # Genuine zeros remain zero in a true geometric mean.
            if any(row[c] <= 0 for c, _ in valid):
                return 0.0
            return float(np.exp(sum(np.log(row[c]) * w / total for c, w in valid)))
        raise ValueError(f"Método de agregación no reconocido: {self.method}")
