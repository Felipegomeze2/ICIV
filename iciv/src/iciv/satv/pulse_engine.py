"""Monthly SATV alerts driven only by the ICIV Pulse signals."""

from __future__ import annotations

import pandas as pd

from iciv.index.pulse_aggregator import PULSE_WEIGHTS

GROUPS: dict[str, dict] = {
    "macro_global": {
        "nombre": "Macro global",
        "variables": [
            "wti_precio_usd",
            "brent_precio_usd",
            "tasa_fed_funds_pct",
            "usd_index_broad",
            "vix_volatility",
            "ust_10y_yield_pct",
        ],
    },
    "energia": {
        "nombre": "Energia",
        "variables": ["petroleo_crudo_produccion_tbpd"],
    },
    "noticias": {
        "nombre": "Cobertura internacional",
        "variables": [
            "guardian_articulos_venezuela",
            "guardian_tono_titulares",
            "gdelt_cobertura_vol",
            "gdelt_tono_noticias",
        ],
    },
}


def _level(score: float | None) -> str:
    if score is None or pd.isna(score):
        return "sin_dato"
    if score < 30:
        return "critico"
    if score < 50:
        return "precaucion"
    return "normal"


def _trend(delta_1m: float | None, delta_3m: float | None) -> tuple[str, str, str]:
    d1 = delta_1m or 0.0
    d3 = delta_3m or 0.0
    if d1 <= -8 or d3 <= -12:
        return "deterioro_acelerado", "Deterioro acelerado", "vv"
    if d1 <= -3 or d3 <= -6:
        return "deterioro", "Deterioro", "v"
    if d1 >= 8 or d3 >= 12:
        return "recuperacion_acelerada", "Recuperacion acelerada", "^^"
    if d1 >= 3 or d3 >= 6:
        return "recuperacion", "Recuperacion", "^"
    return "estable", "Estable", "-"


class PulseSATVEngine:
    """Build SATV cards and alerts from monthly Pulse scores/components."""

    def __init__(self, pulse_df: pd.DataFrame, components_df: pd.DataFrame) -> None:
        self.pulse = pulse_df.copy().sort_values(["año", "mes"]).reset_index(drop=True)
        self.components = components_df.copy().sort_values(["año", "mes"]).reset_index(drop=True)

    def compute_all(self) -> dict:
        groups = self._group_status()
        alerts = self._alerts(groups)
        return {
            "resumen": self._summary(groups, alerts),
            "dimensiones": groups,
            "alertas_activas": alerts,
            "variables_criticas": self._critical_variables(),
            "timeline_historico": self._timeline(),
        }

    def _weighted_group_series(self, variables: list[str]) -> pd.Series:
        available = [v for v in variables if v in self.components.columns]
        if not available:
            return pd.Series(index=self.components.index, dtype=float)

        def score(row: pd.Series) -> float:
            pairs = [
                (var, float(row[var]), PULSE_WEIGHTS[var])
                for var in available
                if pd.notna(row.get(var))
            ]
            total = sum(weight for _, _, weight in pairs)
            return sum(value * weight / total for _, value, weight in pairs) if total else float("nan")

        return self.components.apply(score, axis=1)

    def _group_status(self) -> dict:
        result: dict[str, dict] = {}
        for key, meta in GROUPS.items():
            series = self._weighted_group_series(meta["variables"]).dropna()
            if series.empty:
                score = None
                delta_1m = delta_3m = delta_6m = None
                sparkline: list[float] = []
            else:
                score = round(float(series.iloc[-1]), 1)
                delta_1m = round(float(series.iloc[-1] - series.iloc[-2]), 1) if len(series) > 1 else None
                delta_3m = round(float(series.iloc[-1] - series.iloc[-4]), 1) if len(series) > 3 else None
                delta_6m = round(float(series.iloc[-1] - series.iloc[-7]), 1) if len(series) > 6 else None
                sparkline = [round(float(v), 1) for v in series.tail(12)]

            trend, trend_label, arrow = _trend(delta_1m, delta_3m)
            latest = self.components.iloc[-1] if not self.components.empty else pd.Series(dtype=float)
            present = [v for v in meta["variables"] if pd.notna(latest.get(v))]
            weakest = min(present, key=lambda var: latest[var]) if present else ""
            result[key] = {
                "nombre": meta["nombre"],
                "score_actual": score,
                "nivel": _level(score),
                "delta_1y": delta_1m or 0.0,
                "delta_3y": delta_3m or 0.0,
                "delta_5y": delta_6m or 0.0,
                "tendencia": trend,
                "tendencia_label": trend_label,
                "arrow": arrow,
                "variable_critica": weakest,
                "variable_critica_score": round(float(latest[weakest]), 1) if weakest else 0.0,
                "sparkline": sparkline,
                "n_vars_disponibles": len(present),
                "n_vars_total": len(meta["variables"]),
            }
        return result

    def _alerts(self, groups: dict) -> list[dict]:
        if self.pulse.empty:
            return []
        valid = self.pulse.dropna(subset=["pulse_score"])
        if valid.empty:
            return []

        last = valid.iloc[-1]
        recent = valid.tail(4)["pulse_score"]
        alerts: list[dict] = []
        if float(last["cobertura_pct"]) < 70:
            alerts.append({
                "tipo": "Cobertura mensual parcial",
                "nivel": "precaucion",
                "dimension": "pulse",
                "icono": "i",
                "mensaje": (
                    f"El Pulse de {int(last['año'])}-{int(last['mes']):02d} usa "
                    f"{float(last['cobertura_pct']):.0f}% del peso mensual disponible."
                ),
            })
        if float(last["pulse_score"]) < 35:
            alerts.append({
                "tipo": "Pulse en zona alta de riesgo",
                "nivel": "critico",
                "dimension": "pulse",
                "icono": "!",
                "mensaje": f"El monitor mensual cerro en {float(last['pulse_score']):.1f} puntos.",
            })
        if len(recent) == 4 and recent.is_monotonic_decreasing and recent.iloc[0] - recent.iloc[-1] >= 6:
            alerts.append({
                "tipo": "Deterioro de tres meses",
                "nivel": "precaucion",
                "dimension": "pulse",
                "icono": "v",
                "mensaje": f"El Pulse perdio {recent.iloc[0] - recent.iloc[-1]:.1f} puntos en tres meses.",
            })
        for group in groups.values():
            if group["nivel"] == "critico":
                alerts.append({
                    "tipo": f"Señal critica: {group['nombre']}",
                    "nivel": "critico",
                    "dimension": group["nombre"],
                    "icono": "!",
                    "mensaje": f"{group['nombre']} esta en {group['score_actual']:.1f} puntos.",
                })
        return alerts

    def _critical_variables(self) -> list[dict]:
        if self.components.empty:
            return []
        latest = self.components.iloc[-1]
        previous = self.components.iloc[-2] if len(self.components) > 1 else latest
        rows: list[dict] = []
        group_by_var = {var: meta["nombre"] for meta in GROUPS.values() for var in meta["variables"]}
        for var in PULSE_WEIGHTS:
            if var not in self.components.columns or pd.isna(latest.get(var)):
                continue
            prev = previous.get(var)
            delta = float(latest[var] - prev) if pd.notna(prev) else 0.0
            rows.append({
                "label": var.replace("_", " "),
                "score": round(float(latest[var]), 1),
                "delta_1y": round(delta, 1),
                "dimension": group_by_var.get(var, "pulse"),
            })
        return sorted(rows, key=lambda row: row["score"])[:8]

    def _timeline(self) -> list[dict]:
        valid = self.pulse.dropna(subset=["pulse_score"])
        rows: list[dict] = []
        for _, row in valid.iterrows():
            score = float(row["pulse_score"])
            if score < 35:
                rows.append({
                    "año": int(row["año"]),
                    "mes": int(row["mes"]),
                    "dimension": "pulse",
                    "tipo": "Pulse < 35",
                    "nivel": "critico",
                })
        return rows

    def _summary(self, groups: dict, alerts: list[dict]) -> dict:
        valid = self.pulse.dropna(subset=["pulse_score"])
        if valid.empty:
            return {}
        last = valid.iloc[-1]
        prev = valid.iloc[-2] if len(valid) > 1 else last
        delta = round(float(last["pulse_score"] - prev["pulse_score"]), 1)
        levels = [group["nivel"] for group in groups.values()]
        return {
            "dims_criticas": levels.count("critico"),
            "dims_precaucion": levels.count("precaucion"),
            "dims_normales": levels.count("normal"),
            "alertas_criticas": sum(a["nivel"] == "critico" for a in alerts),
            "alertas_precaucion": sum(a["nivel"] == "precaucion" for a in alerts),
            "alertas_positivas": sum(a["nivel"] == "normal" for a in alerts),
            "iciv_delta_1y": delta,
            "iciv_tendencia": "deterioro" if delta < -3 else "recuperacion" if delta > 3 else "estable",
            "fecha": f"{int(last['año'])}-{int(last['mes']):02d}",
        }
