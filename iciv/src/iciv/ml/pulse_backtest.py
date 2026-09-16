"""Matched-origin retrospective evaluation on the latest available vintage.

The common-sample summary excludes origin/horizon pairs where any requested
model fails; all attempts and failures remain visible. No data are filled.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from iciv.ml.pulse_models import (
    EVALUATION_TYPE, SARIMA_SPEC, empirical_naive_interval,
    fit_shared_sarima, prepare_series,
)


@dataclass(frozen=True)
class BacktestConfig:
    horizons: tuple[int, ...] = (1, 3, 6)
    min_train_months: int = 60
    step_months: int = 6
    min_coverage_pct: float = 70.0
    include_low_coverage: bool = False
    models: tuple[str, ...] = ("naive", "seasonal_naive", "sarima")


def _prepare_series(pulse_df: pd.DataFrame, config: BacktestConfig) -> pd.Series:
    return prepare_series(pulse_df, config.min_coverage_pct, config.include_low_coverage)


def _seasonal_naive(train: pd.Series, target_date: pd.Timestamp) -> float | None:
    value = train.get(target_date - pd.DateOffset(years=1), np.nan)
    return float(value) if pd.notna(value) else None  # Missing seasonal reference is not substituted.


def _summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame()
    result = detail.groupby(["model", "horizon"], as_index=False).agg(
        n=("absolute_error", "count"), mae=("absolute_error", "mean"),
        rmse=("squared_error", lambda x: float(np.sqrt(x.mean()))),
        bias=("bias_error", "mean"),
        n_intervals=("inside_95", lambda x: int(x.notna().sum())),
        inside_80=("inside_80", lambda x: float(x.dropna().astype(float).mean()) if x.notna().any() else np.nan),
        inside_95=("inside_95", lambda x: float(x.dropna().astype(float).mean()) if x.notna().any() else np.nan),
    )
    return result.round(4)


def _records(df: pd.DataFrame) -> list[dict]:
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


def run_pulse_backtest(pulse_df: pd.DataFrame, output_dir: Path | str | None = None,
                       config: BacktestConfig | None = None) -> dict:
    config = config or BacktestConfig()
    if config.step_months < 1 or not config.horizons or min(config.horizons) < 1:
        raise ValueError("Horizontes y paso deben ser enteros positivos")
    if not config.models or set(config.models) - {"naive", "seasonal_naive", "sarima"}:
        raise ValueError("Modelos admitidos: naive, seasonal_naive, sarima")
    ts = _prepare_series(pulse_df, config)
    rows, failures, diagnostics = [], [], []
    max_h = max(config.horizons)
    attempted_origins = 0
    for origin_idx in range(config.min_train_months - 1, len(ts) - max_h, config.step_months):
        train = ts.iloc[:origin_idx + 1]
        if train.notna().sum() < config.min_train_months or pd.isna(train.iloc[-1]):
            continue
        origin = train.index[-1]
        attempted_origins += 1
        sarima = None
        diagnostic = {}
        if "sarima" in config.models:
            sarima, diagnostic = fit_shared_sarima(train)
            diagnostics.append({"origin_date": origin.strftime("%Y-%m-%d"), **diagnostic})
        forecast = None
        if sarima is not None:
            try:
                forecast = sarima.get_forecast(steps=max_h)
            except Exception as exc:
                diagnostic["reason"] = f"forecast_error: {exc}"
        for horizon in config.horizons:
            target = ts.index[origin_idx + horizon]
            actual = ts.iloc[origin_idx + horizon]
            if pd.isna(actual):
                continue
            for name in config.models:
                intervals = {}
                prediction = None
                reason = "unavailable"
                if name == "naive":
                    prediction = float(train.iloc[-1])
                    intervals = empirical_naive_interval(train, horizon, prediction)
                elif name == "seasonal_naive":
                    prediction = _seasonal_naive(train, target)
                    reason = "missing_same_calendar_month_previous_year"
                elif forecast is not None:
                    prediction = float(forecast.predicted_mean.iloc[horizon - 1])
                    for level, alpha in ((80, .20), (95, .05)):
                        interval = forecast.conf_int(alpha=alpha).iloc[horizon - 1]
                        intervals[f"lower_{level}"] = float(np.clip(interval.iloc[0], 0, 100))
                        intervals[f"upper_{level}"] = float(np.clip(interval.iloc[1], 0, 100))
                else:
                    reason = diagnostic.get("reason", "sarima_unavailable")
                base = {"origin_date": origin.strftime("%Y-%m-%d"), "target_date": target.strftime("%Y-%m-%d"),
                        "horizon": horizon, "model": name}
                if prediction is None or not np.isfinite(prediction):
                    failures.append({**base, "reason": reason})
                    continue
                prediction = float(np.clip(prediction, 0, 100))
                error = prediction - float(actual)
                row = {**base, "model_spec": SARIMA_SPEC if name == "sarima" else name,
                       "aic": diagnostic.get("aic") if name == "sarima" else None,
                       "y_true": float(actual), "y_pred": prediction,
                       "absolute_error": abs(error), "squared_error": error ** 2, "bias_error": error,
                       "n_train_observed": int(train.notna().sum()), "n_train_calendar": len(train)}
                for level in (80, 95):
                    lo, hi = intervals.get(f"lower_{level}"), intervals.get(f"upper_{level}")
                    row[f"lower_{level}"], row[f"upper_{level}"] = lo, hi
                    row[f"inside_{level}"] = bool(lo <= actual <= hi) if lo is not None and hi is not None else None
                rows.append(row)
    detail = pd.DataFrame(rows)
    if not detail.empty:
        counts = detail.groupby(["origin_date", "horizon"])["model"].transform("nunique")
        detail["common_sample"] = counts.eq(len(set(config.models)))
        common = detail[detail["common_sample"]]
    else:
        common = detail
    summary = _summary(common)
    all_summary = _summary(detail)
    best = summary.sort_values(["horizon", "mae"]).groupby("horizon", as_index=False).first() if not summary.empty else pd.DataFrame()
    payload = {
        "available": not summary.empty, "evaluation_type": EVALUATION_TYPE,
        "reason": None if not summary.empty else "Sin pares comparables para todos los modelos solicitados",
        "limitations": "Sin vintages o fechas históricas de publicación. No es una simulación en tiempo real. Errores condicionados a meses elegibles; composición del índice variable.",
        "config": asdict(config), "sample_policy": "same_origin_and_target_for_every_model",
        "n_predictions": len(detail), "n_common_predictions": len(common),
        "n_origins_attempted": attempted_origins,
        "n_origins": int(common["origin_date"].nunique()) if not common.empty else 0,
        "n_failures": len(failures), "failures": failures, "diagnostics": diagnostics,
        "summary": _records(summary), "best_by_horizon": _records(best),
        "sarima": _records(summary[summary["model"] == "sarima"]) if not summary.empty else [],
        "public_model": "naive", "public_model_selection": "prespecified_conservative_baseline",
    }
    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        detail.to_csv(out / "pulse_forecast_backtest.csv", index=False, encoding="utf-8-sig")
        summary.to_csv(out / "pulse_forecast_backtest_summary.csv", index=False, encoding="utf-8-sig")
        all_summary.to_csv(out / "pulse_forecast_backtest_available_summary.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(failures, columns=["origin_date", "target_date", "horizon", "model", "reason"]).to_csv(
            out / "pulse_forecast_backtest_failures.csv", index=False, encoding="utf-8-sig")
    return {"rows": detail, "summary": summary, "available_summary": all_summary, "payload": payload}
