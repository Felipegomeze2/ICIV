"""Shared forecasting rules: calendar gaps remain missing, never interpolated."""
from __future__ import annotations

import logging
import warnings

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
SARIMA_ORDER = (1, 1, 1)
SARIMA_SEASONAL_ORDER = (1, 1, 1, 12)
SARIMA_SPEC = f"SARIMA{SARIMA_ORDER}x{SARIMA_SEASONAL_ORDER}"
MIN_COVERAGE = 70.0
EVALUATION_TYPE = "retrospective_latest_vintage"


def prepare_series(pulse_df: pd.DataFrame, min_coverage: float = MIN_COVERAGE,
                   include_low_coverage: bool = False) -> pd.Series:
    required = {"año", "mes", "pulse_score", "cobertura_pct"}
    missing = required - set(pulse_df)
    if missing:
        raise ValueError(f"Faltan columnas Pulse: {sorted(missing)}")
    if pulse_df.empty:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], freq="MS"))
    df = pulse_df.copy()
    dates = pd.to_datetime(dict(year=df["año"], month=df["mes"], day=1))
    if dates.duplicated().any():
        raise ValueError("Pulse contiene meses duplicados")
    values = pd.to_numeric(df["pulse_score"], errors="coerce").replace([np.inf, -np.inf], np.nan)
    eligible = pd.Series(True, index=df.index)
    if not include_low_coverage:
        eligible &= pd.to_numeric(df["cobertura_pct"], errors="coerce") >= min_coverage
        for flag in ("elegible_modelo", "produccion_disponible", "mes_cerrado"):
            if flag in df:
                eligible &= df[flag].map(lambda value: str(value).lower() in {"true", "1"})
    return pd.Series(values.where(eligible).to_numpy(), index=dates, name="pulse_score").sort_index().asfreq("MS")


def empirical_naive_interval(train: pd.Series, horizon: int, point: float,
                             min_pairs: int = 20) -> dict:
    """Derived historical errors at this origin; not filled observations.

    Calendar shift h pairs each target with its actual h-month origin.
    Empirical quantiles are descriptive, not guaranteed coverage.
    """
    errors = (train - train.shift(horizon)).dropna()
    result = {"n_interval_errors": int(len(errors)), "lower_80": None,
              "upper_80": None, "lower_95": None, "upper_95": None}
    if len(errors) < min_pairs:
        return result
    for level, alpha in ((80, 0.20), (95, 0.05)):
        radius = float(errors.abs().quantile(1 - alpha, interpolation="higher"))
        result[f"lower_{level}"] = float(np.clip(point - radius, 0, 100))
        result[f"upper_{level}"] = float(np.clip(point + radius, 0, 100))
    return result


def fit_shared_sarima(train: pd.Series) -> tuple[object | None, dict]:
    diagnostics = {"model_spec": SARIMA_SPEC, "n_observed": int(train.notna().sum()),
                   "n_calendar_months": len(train), "converged": False, "warnings": []}
    if train.notna().sum() < 36:
        diagnostics["reason"] = "insufficient_observations"
        return None, diagnostics
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            model = SARIMAX(train.asfreq("MS"), order=SARIMA_ORDER,
                            seasonal_order=SARIMA_SEASONAL_ORDER,
                            enforce_stationarity=False, enforce_invertibility=False).fit(
                                disp=False, maxiter=200)
        diagnostics["warnings"] = sorted({str(item.message) for item in captured})
        diagnostics["converged"] = bool(model.mle_retvals.get("converged", False))
        diagnostics["aic"] = float(model.aic) if np.isfinite(model.aic) else None
        if not diagnostics["converged"] or not np.isfinite(model.params).all():
            diagnostics["reason"] = "non_convergence_or_invalid_parameters"
            logger.warning("SARIMA no utilizable: %s", diagnostics["reason"])
            return None, diagnostics
        return model, diagnostics
    except Exception as exc:
        diagnostics["reason"] = f"{type(exc).__name__}: {exc}"
        logger.warning("SARIMA omitido: %s", diagnostics["reason"])
        return None, diagnostics
