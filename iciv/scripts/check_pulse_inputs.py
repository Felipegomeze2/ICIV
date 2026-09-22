"""Quality gate for monthly Pulse inputs before publishing the dashboard."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from iciv.config import settings


@dataclass(frozen=True)
class SourceRule:
    filename: str
    label: str
    max_lag_days: int  # Days since the end of the reported month, not its first day.
    required: bool = True


RULES = (
    SourceRule("fred_monthly.csv", "FRED macro monthly", 50),
    SourceRule("guardian_monthly.csv", "Guardian monthly", 75),
    # EIA International commonly publishes Venezuela monthly values with lag.
    SourceRule("eia_monthly.csv", "EIA petroleum monthly", 160),
    SourceRule("gdelt_monthly.csv", "GDELT news monthly", 75, required=False),
    # IMF IMTS (mirror trade) publica con rezago de varios meses (~6 observado jul-2026).
    SourceRule("imts_monthly.csv", "IMF IMTS mirror trade monthly", 220, required=False),
    # WB Pink Sheet publica a inicios de mes el mes anterior.
    SourceRule("wb_commodities_monthly.csv", "WB Pink Sheet monthly", 90, required=False),
)


def _latest_month(path: Path) -> pd.Timestamp | None:
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    if df.empty or not {"año", "mes"}.issubset(df.columns):
        return None
    if "valor" in df:
        df = df[pd.to_numeric(df["valor"], errors="coerce").notna()]
    years = pd.to_numeric(df["año"], errors="coerce")
    months = pd.to_numeric(df["mes"], errors="coerce")
    fechas = pd.to_datetime(
        years.astype("Int64").astype(str) + "-" + months.astype("Int64").astype(str) + "-01",
        errors="coerce",
    )
    if not fechas.notna().any():
        return None
    if "variable" in df:
        from iciv.index.pulse_aggregator import PULSE_WEIGHTS
        active = df["variable"].isin(PULSE_WEIGHTS)
        if active.any():
            return fechas[active].groupby(df.loc[active, "variable"]).max().min()
    return fechas.max()


def check_inputs(now: pd.Timestamp | None = None) -> int:
    now = now or pd.Timestamp.today().normalize()
    failures: list[str] = []
    warnings: list[str] = []

    for rule in RULES:
        path = settings.paths.data_raw / rule.filename
        if not path.exists():
            msg = f"{rule.label}: falta {rule.filename}"
            (failures if rule.required else warnings).append(msg)
            continue

        latest = _latest_month(path)
        if latest is None:
            msg = f"{rule.label}: CSV vacio o sin columnas año/mes validas"
            (failures if rule.required else warnings).append(msg)
            continue

        if latest > now.to_period("M").start_time:
            msg = f"{rule.label}: mes futuro {latest:%Y-%m}; no es una observacion vigente"
            (failures if rule.required else warnings).append(msg)
            continue
        # CSVs encode a month as day 1. That is a period identifier, not the
        # publication date. A current (partial) month has zero closed-month lag.
        month_end = latest + pd.offsets.MonthEnd(0)
        lag_days = max(0, int((now.normalize() - month_end).days))
        msg = f"{rule.label}: ultimo mes {latest:%Y-%m}, rezago desde cierre {lag_days} dias"
        if lag_days > rule.max_lag_days:
            stale = f"{msg}; maximo permitido {rule.max_lag_days}"
            (failures if rule.required else warnings).append(stale)
        else:
            print(f"OK {msg}")

    for msg in warnings:
        print(f"WARN {msg}")
    for msg in failures:
        print(f"ERROR {msg}")

    if failures:
        print("Pulse input gate failed: no se publica una actualizacion semanal sin fuentes core vigentes.")
        return 1
    print("Pulse input gate passed.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate freshness of monthly Pulse sources.")
    parser.add_argument("--today", help="Override current date as YYYY-MM-DD for tests/reproducibility.")
    args = parser.parse_args()
    now = pd.Timestamp(args.today) if args.today else None
    raise SystemExit(check_inputs(now))


if __name__ == "__main__":
    main()
