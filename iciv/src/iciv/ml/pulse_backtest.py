"""Backtesting rolling-origin para el forecast del ICIV Pulse.

El objetivo es evaluar modelos sobre meses ya observados sin mirar el futuro.
No fabrica datos: por defecto usa solo meses con `cobertura_pct >= 70`.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=Warning)
try:
    from statsmodels.tools.sm_exceptions import ConvergenceWarning
    warnings.filterwarnings("ignore", category=ConvergenceWarning)
except Exception:
    pass


@dataclass(frozen=True)
class BacktestConfig:
    horizons: tuple[int, ...] = (1, 3, 6)
    min_train_months: int = 60
    step_months: int = 3
    sarima_origin_step_months: int = 12
    min_coverage_pct: float = 70.0
    include_low_coverage: bool = False


def _prepare_series(pulse_df: pd.DataFrame, config: BacktestConfig) -> pd.Series:
    required = {"año", "mes", "pulse_score", "cobertura_pct"}
    missing = required - set(pulse_df.columns)
    if missing:
        raise ValueError(f"Pulse backtest requiere columnas faltantes: {sorted(missing)}")

    df = pulse_df.dropna(subset=["pulse_score"]).copy()
    if not config.include_low_coverage:
        df = df[df["cobertura_pct"] >= config.min_coverage_pct].copy()
    if df.empty:
        return pd.Series(dtype=float)

    df["fecha"] = pd.to_datetime(
        df["año"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2) + "-01",
        errors="coerce",
    )
    df = df.dropna(subset=["fecha"]).sort_values("fecha")
    return df.set_index("fecha")["pulse_score"].astype(float).asfreq("MS")


def _fit_sarima(train: pd.Series):
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except ImportError:
        return None, None, None

    candidates = [
        ((1, 1, 1), (1, 1, 1, 12)),
    ]
    best_model = None
    best_order = None
    best_aic = np.inf
    clean = train.dropna()
    if len(clean) < 36:
        return None, None, None
    for order, seasonal_order in candidates:
        try:
            model = SARIMAX(
                clean,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False, maxiter=40)
            if model.aic < best_aic:
                best_model = model
                best_order = f"SARIMA{order}x{seasonal_order}"
                best_aic = float(model.aic)
        except Exception:
            continue
    return best_model, best_order, best_aic if np.isfinite(best_aic) else None


def _ets_forecast(train: pd.Series, steps: int) -> float | None:
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
    except ImportError:
        return None
    clean = train.dropna()
    if len(clean) < 24:
        return None
    try:
        seasonal = "add" if len(clean) >= 36 else None
        model = ExponentialSmoothing(
            clean,
            trend="add",
            seasonal=seasonal,
            seasonal_periods=12 if seasonal else None,
            initialization_method="estimated",
        ).fit(optimized=True)
        return float(model.forecast(steps).iloc[-1])
    except Exception:
        return None


def _seasonal_naive(train: pd.Series, target_date: pd.Timestamp) -> float | None:
    lookup = target_date - pd.DateOffset(years=1)
    if lookup in train.index and pd.notna(train.loc[lookup]):
        return float(train.loc[lookup])
    clean = train.dropna()
    return float(clean.iloc[-1]) if not clean.empty else None


def run_pulse_backtest(
    pulse_df: pd.DataFrame,
    output_dir: Path | str | None = None,
    config: BacktestConfig | None = None,
) -> dict:
    """Ejecuta backtesting y opcionalmente guarda CSVs."""
    config = config or BacktestConfig()
    ts = _prepare_series(pulse_df, config)
    max_h = max(config.horizons)
    if len(ts.dropna()) < config.min_train_months + max_h:
        result = {
            "rows": pd.DataFrame(),
            "summary": pd.DataFrame(),
            "payload": {
                "available": False,
                "reason": "Muestra insuficiente para backtesting rolling-origin",
            },
        }
        return result

    pulse_cov = pulse_df.copy()
    pulse_cov["fecha"] = pd.to_datetime(
        pulse_cov["año"].astype(str) + "-" + pulse_cov["mes"].astype(str).str.zfill(2) + "-01",
        errors="coerce",
    )
    coverage_by_date = pulse_cov.dropna(subset=["fecha"]).set_index("fecha")["cobertura_pct"]

    rows: list[dict] = []
    last_origin = len(ts) - max_h - 1
    for origin_idx in range(config.min_train_months - 1, last_origin + 1, config.step_months):
        train = ts.iloc[: origin_idx + 1]
        origin_date = train.index[-1]
        run_sarima = (
            config.sarima_origin_step_months > 0
            and ((origin_idx - (config.min_train_months - 1)) % config.sarima_origin_step_months == 0)
        )
        sarima_model, sarima_order, sarima_aic = _fit_sarima(train) if run_sarima else (None, None, None)
        sarima_fc = None
        sarima_ci80 = None
        sarima_ci95 = None
        if sarima_model is not None:
            try:
                sarima_fc_obj = sarima_model.get_forecast(steps=max_h)
                sarima_fc = sarima_fc_obj.predicted_mean
                sarima_ci80 = sarima_fc_obj.conf_int(alpha=0.20)
                sarima_ci95 = sarima_fc_obj.conf_int(alpha=0.05)
            except Exception:
                sarima_fc = None

        for h in config.horizons:
            target_idx = origin_idx + h
            if target_idx >= len(ts):
                continue
            target_date = ts.index[target_idx]
            y_true = ts.iloc[target_idx]
            if pd.isna(y_true):
                continue

            predictions: list[dict] = [
                {"model": "naive", "y_pred": float(train.dropna().iloc[-1])},
                {"model": "seasonal_naive", "y_pred": _seasonal_naive(train, target_date)},
                {"model": "ets", "y_pred": _ets_forecast(train, h)},
            ]
            if sarima_fc is not None:
                pred = float(sarima_fc.iloc[h - 1])
                row = {
                    "model": "sarima",
                    "y_pred": pred,
                    "lower_80": float(sarima_ci80.iloc[h - 1, 0]) if sarima_ci80 is not None else None,
                    "upper_80": float(sarima_ci80.iloc[h - 1, 1]) if sarima_ci80 is not None else None,
                    "lower_95": float(sarima_ci95.iloc[h - 1, 0]) if sarima_ci95 is not None else None,
                    "upper_95": float(sarima_ci95.iloc[h - 1, 1]) if sarima_ci95 is not None else None,
                    "model_spec": sarima_order,
                    "aic": sarima_aic,
                }
                predictions.append(row)

            for pred_row in predictions:
                y_pred = pred_row.get("y_pred")
                if y_pred is None or pd.isna(y_pred):
                    continue
                y_pred = max(0.0, min(100.0, float(y_pred)))
                y_true_f = float(y_true)
                lower_80 = pred_row.get("lower_80")
                upper_80 = pred_row.get("upper_80")
                lower_95 = pred_row.get("lower_95")
                upper_95 = pred_row.get("upper_95")
                rows.append({
                    "origin_date": origin_date.strftime("%Y-%m-%d"),
                    "target_date": target_date.strftime("%Y-%m-%d"),
                    "horizon": h,
                    "model": pred_row["model"],
                    "model_spec": pred_row.get("model_spec"),
                    "aic": pred_row.get("aic"),
                    "y_true": round(y_true_f, 4),
                    "y_pred": round(y_pred, 4),
                    "lower_80": round(max(0.0, min(100.0, lower_80)), 4) if lower_80 is not None else None,
                    "upper_80": round(max(0.0, min(100.0, upper_80)), 4) if upper_80 is not None else None,
                    "lower_95": round(max(0.0, min(100.0, lower_95)), 4) if lower_95 is not None else None,
                    "upper_95": round(max(0.0, min(100.0, upper_95)), 4) if upper_95 is not None else None,
                    "coverage_pct_target": (
                        round(float(coverage_by_date.loc[target_date]), 1)
                        if target_date in coverage_by_date.index else None
                    ),
                    "absolute_error": round(abs(y_true_f - y_pred), 4),
                    "squared_error": round((y_true_f - y_pred) ** 2, 4),
                    "bias_error": round(y_pred - y_true_f, 4),
                    "inside_80": (
                        bool(lower_80 <= y_true_f <= upper_80)
                        if lower_80 is not None and upper_80 is not None else None
                    ),
                    "inside_95": (
                        bool(lower_95 <= y_true_f <= upper_95)
                        if lower_95 is not None and upper_95 is not None else None
                    ),
                })

    detail = pd.DataFrame(rows)
    if detail.empty:
        summary = pd.DataFrame()
        payload = {"available": False, "reason": "No se generaron predicciones validables"}
    else:
        summary = (
            detail.groupby(["model", "horizon"], as_index=False)
            .agg(
                n=("absolute_error", "count"),
                mae=("absolute_error", "mean"),
                rmse=("squared_error", lambda x: float(np.sqrt(np.mean(x)))),
                bias=("bias_error", "mean"),
                inside_80=("inside_80", lambda x: float(pd.Series(x).dropna().mean()) if pd.Series(x).dropna().size else np.nan),
                inside_95=("inside_95", lambda x: float(pd.Series(x).dropna().mean()) if pd.Series(x).dropna().size else np.nan),
            )
        )
        for col in ["mae", "rmse", "bias", "inside_80", "inside_95"]:
            summary[col] = summary[col].round(4)
        best_rows = (
            summary.sort_values(["horizon", "mae"])
            .groupby("horizon", as_index=False)
            .first()[["horizon", "model", "mae", "rmse"]]
        )
        sarima_rows = summary[summary["model"] == "sarima"]
        payload = {
            "available": True,
            "config": {
                "horizons": list(config.horizons),
                "min_train_months": config.min_train_months,
                "step_months": config.step_months,
                "sarima_origin_step_months": config.sarima_origin_step_months,
                "min_coverage_pct": config.min_coverage_pct,
                "include_low_coverage": config.include_low_coverage,
            },
            "n_predictions": int(len(detail)),
            "n_origins": int(detail["origin_date"].nunique()),
            "best_by_horizon": best_rows.to_dict(orient="records"),
            "sarima": sarima_rows.to_dict(orient="records"),
        }

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        detail.to_csv(out / "pulse_forecast_backtest.csv", index=False, encoding="utf-8-sig")
        summary.to_csv(out / "pulse_forecast_backtest_summary.csv", index=False, encoding="utf-8-sig")

    return {"rows": detail, "summary": summary, "payload": payload}
