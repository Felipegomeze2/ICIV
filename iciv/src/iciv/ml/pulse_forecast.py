"""Forecast mensual explícito; ninguna predicción entra a las observaciones.

El baseline público prespecificado es persistencia (naive). SARIMA se conserva
como candidato diagnóstico, con las mismas reglas que el backtest. No se ofrece
nowcast anual OLS: el antiguo ajuste mezclaba años futuros en su validación.
"""
from __future__ import annotations

import pandas as pd

from iciv.ml.pulse_models import (
    EVALUATION_TYPE, SARIMA_SPEC, empirical_naive_interval,
    fit_shared_sarima, prepare_series,
)

FORECAST_HORIZON = 6
SEASONALITY = 12


class PulseForecaster:
    def __init__(self, pulse_df: pd.DataFrame, annual_df: pd.DataFrame | None = None) -> None:
        self.pulse_df = pulse_df.copy()
        self.annual_df = annual_df
        self.sarima_model = None
        self.sarima_diagnostics: dict = {}

    def _series(self) -> pd.Series:
        ts = prepare_series(self.pulse_df)
        return ts.loc[:ts.last_valid_index()] if ts.notna().any() else ts

    def fit_sarima(self) -> "PulseForecaster":
        self.sarima_model, self.sarima_diagnostics = fit_shared_sarima(self._series())
        return self

    def compute_forecast(self) -> dict:
        ts = self._series()
        methodology = {
            "model_selected": "naive",
            "selection_rule": "Baseline de persistencia prespecificado; no afirma superioridad predictiva.",
            "evaluation_type": EVALUATION_TYPE,
            "validacion": "Retrospectiva de último vintage; sin archivos históricos de publicación o revisiones.",
            "training_filter": "Cobertura utilizable >=70%, producción doméstica disponible y mes cerrado cuando existen estas banderas.",
            "interval_method": "Cuantiles empíricos de errores absolutos históricos por horizonte; mínimo 20 pares, sin garantía de cobertura nominal.",
            "normalization": "Min-max expansivo causal hasta cada fecha; no añade observaciones.",
            "caveat": "El puntaje puede cambiar de composición; las bandas incluyen esa inestabilidad histórica y no son probabilidades de riesgo económico.",
            "sarima_candidate": SARIMA_SPEC,
        }
        if ts.notna().sum() < 24:
            return {"forecast": {}, "metodologia": methodology, "available": False,
                    "reason": "Menos de 24 observaciones elegibles para el baseline"}
        point = float(ts.dropna().iloc[-1])
        dates = pd.date_range(ts.index[-1] + pd.offsets.MonthBegin(1), periods=FORECAST_HORIZON, freq="MS")
        intervals = [empirical_naive_interval(ts, h, point) for h in range(1, FORECAST_HORIZON + 1)]
        forecast = {
            "model": "naive", "model_label": "Persistencia (naive)",
            "fecha": [date.strftime("%Y-%m") for date in dates],
            "origin_date": ts.index[-1].strftime("%Y-%m"),
            "mean": [round(point, 2)] * FORECAST_HORIZON,
            "n_observed": int(ts.notna().sum()), "n_calendar_months": len(ts),
            "horizonte_meses": FORECAST_HORIZON,
            "interval_method": methodology["interval_method"],
            "n_interval_errors": [item["n_interval_errors"] for item in intervals],
        }
        for level in (80, 95):
            for label, key in (("lo", "lower"), ("hi", "upper")):
                forecast[f"{label}_{level}"] = [round(item[f"{key}_{level}"], 2)
                                                 if item[f"{key}_{level}"] is not None else None
                                                 for item in intervals]
        return {"forecast": forecast, "metodologia": methodology, "available": True}

    def compute_all(self) -> dict:
        return self.compute_forecast()
