"""Genera backtesting rolling-origin del forecast ICIV Pulse."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from iciv.config import settings
from iciv.ml.pulse_backtest import BacktestConfig, run_pulse_backtest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-low-coverage", action="store_true")
    parser.add_argument("--min-train-months", type=int, default=60)
    parser.add_argument("--step-months", type=int, default=3)
    parser.add_argument("--sarima-origin-step-months", type=int, default=12)
    args = parser.parse_args()

    pulse_path = settings.paths.data_processed / "iciv_pulse_monthly.csv"
    if not pulse_path.exists():
        raise FileNotFoundError(
            f"No existe {pulse_path}. Ejecuta primero: python main.py --no-fetch --no-open"
        )
    pulse_df = pd.read_csv(pulse_path)
    config = BacktestConfig(
        min_train_months=args.min_train_months,
        step_months=args.step_months,
        sarima_origin_step_months=args.sarima_origin_step_months,
        include_low_coverage=args.include_low_coverage,
    )
    result = run_pulse_backtest(pulse_df, settings.paths.data_processed, config)
    payload = result["payload"]
    if not payload.get("available"):
        print(f"Backtest no disponible: {payload.get('reason')}")
        return 1

    print("Backtest Pulse generado")
    print(f"  Predicciones: {payload['n_predictions']}")
    print(f"  Origenes: {payload['n_origins']}")
    print(f"  Detalle: {settings.paths.data_processed / 'pulse_forecast_backtest.csv'}")
    print(f"  Resumen: {settings.paths.data_processed / 'pulse_forecast_backtest_summary.csv'}")
    for row in payload["best_by_horizon"]:
        print(
            f"  h={row['horizon']} mejor={row['model']} "
            f"MAE={row['mae']:.2f} RMSE={row['rmse']:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
