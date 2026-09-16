"""Monthly descriptive alerts with common-component calendar comparisons."""
from __future__ import annotations

import pandas as pd

from iciv.index.pulse_aggregator import PULSE_WEIGHTS

GROUPS = {
    "macro_global": {"nombre": "Condiciones globales", "variables": [
        "wti_precio_usd", "brent_precio_usd", "crudo_dubai_usd", "tasa_fed_funds_pct",
        "usd_index_broad", "vix_volatility", "ust_10y_yield_pct", "em_bond_spread_pct"]},
    "energia": {"nombre": "Petróleo y otros líquidos", "variables": ["petroleo_liquidos_totales_tbpd"]},
    "comercio": {"nombre": "Comercio petrolero con EEUU", "variables": [
        "importaciones_eeuu_crudo_ven_tbpd", "importaciones_eeuu_productos_ven_tbpd"]},
    "noticias": {"nombre": "Cobertura internacional", "variables": [
        "guardian_articulos_venezuela", "guardian_tono_titulares", "gdelt_cobertura_vol", "gdelt_tono_noticias"]},
}


def _level(score: float | None) -> str:
    if score is None or pd.isna(score):
        return "sin_dato"
    return "critico" if score < 30 else "precaucion" if score < 50 else "normal"


def _trend(delta_1m: float | None, delta_3m: float | None) -> tuple[str, str, str]:
    if delta_1m is None and delta_3m is None:
        return "sin_comparacion", "Sin comparación suficiente", "?"
    d1 = delta_1m if delta_1m is not None else 0
    d3 = delta_3m if delta_3m is not None else 0
    if d1 <= -8 or d3 <= -12:
        return "deterioro_acelerado", "Descenso acelerado", "vv"
    if d1 <= -3 or d3 <= -6:
        return "deterioro", "Descenso", "v"
    if d1 >= 8 or d3 >= 12:
        return "recuperacion_acelerada", "Aumento acelerado", "^^"
    if d1 >= 3 or d3 >= 6:
        return "recuperacion", "Aumento", "^"
    return "estable", "Estable", "-"


def _date_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["fecha"] = pd.to_datetime(dict(year=frame["año"], month=frame["mes"], day=1))
    return frame.sort_values("fecha").set_index("fecha", drop=False)


class PulseSATVEngine:
    def __init__(self, pulse_df: pd.DataFrame, components_df: pd.DataFrame) -> None:
        self.pulse = _date_frame(pulse_df)
        self.components = _date_frame(components_df)

    def compute_all(self) -> dict:
        groups = self._group_status()
        alerts = self._alerts(groups)
        return {"resumen": self._summary(groups, alerts), "dimensiones": groups,
                "alertas_activas": alerts, "variables_criticas": self._critical_variables(),
                "timeline_historico": self._timeline(),
                "metodologia": "Señales descriptivas relativas; umbrales heurísticos, sin probabilidades de riesgo. Cambios sobre componentes comunes y fechas calendario."}

    def _weighted_group_series(self, variables: list[str]) -> pd.Series:
        def score(row: pd.Series) -> float:
            pairs = [(float(row[v]), PULSE_WEIGHTS[v]) for v in variables if pd.notna(row.get(v))]
            total = sum(weight for _, weight in pairs)
            return sum(value * weight for value, weight in pairs) / total if total else float("nan")
        return self.components.apply(score, axis=1)

    def _common_delta(self, variables: list[str], lag: int) -> float | None:
        if self.components.empty:
            return None
        date = self.components.index[-1]
        previous_date = date - pd.DateOffset(months=lag)
        if previous_date not in self.components.index:
            return None
        now, previous = self.components.loc[date], self.components.loc[previous_date]
        common = [v for v in variables if pd.notna(now.get(v)) and pd.notna(previous.get(v))]
        weight = sum(PULSE_WEIGHTS[v] for v in common)
        fixed = sum(PULSE_WEIGHTS[v] for v in variables)
        if weight < .70 * fixed - 1e-10:
            return None
        return round(float(sum(PULSE_WEIGHTS[v] * (now[v] - previous[v]) for v in common) / weight), 1)

    def _group_status(self) -> dict:
        result = {}
        for key, meta in GROUPS.items():
            series = self._weighted_group_series(meta["variables"])
            score = round(float(series.iloc[-1]), 1) if not series.empty and pd.notna(series.iloc[-1]) else None
            d1, d3, d6 = (self._common_delta(meta["variables"], lag) for lag in (1, 3, 6))
            trend, label, arrow = _trend(d1, d3)
            latest = self.components.iloc[-1] if not self.components.empty else pd.Series(dtype=float)
            present = [v for v in meta["variables"] if pd.notna(latest.get(v))]
            weakest = min(present, key=lambda var: latest[var]) if present else ""
            result[key] = {"nombre": meta["nombre"], "score_actual": score, "nivel": _level(score),
                "delta_1m": d1, "delta_3m": d3, "delta_6m": d6,
                # Legacy display keys; values are monthly changes, never annual estimates.
                "delta_1y": d1, "delta_3y": d3, "delta_5y": d6,
                "tendencia": trend, "tendencia_label": label, "arrow": arrow,
                "variable_critica": weakest,
                "variable_critica_score": round(float(latest[weakest]), 1) if weakest else None,
                "sparkline": [round(float(v), 1) if pd.notna(v) else None for v in series.tail(12)],
                "n_vars_disponibles": len(present), "n_vars_total": len(meta["variables"])}
        return result

    def _eligible_change(self, row: pd.Series, lag: int) -> float | None:
        value = row.get(f"delta_comparable_{lag}m")
        common = row.get(f"cobertura_comun_{lag}m_pct", 0)
        if pd.isna(value) or pd.isna(common) or common < 70 or not row.get("elegible_modelo", False):
            return None
        return float(value)

    def _alerts(self, groups: dict) -> list[dict]:
        if self.pulse.empty:
            return []
        last = self.pulse.iloc[-1]
        alerts = []
        if not last.get("elegible_modelo", False):
            alerts.append({"tipo": "Mes provisional", "nivel": "precaucion", "dimension": "pulse", "icono": "i",
                "mensaje": f"Cobertura utilizable {float(last['cobertura_pct']):.0f}%. Se exige producción doméstica disponible y mes cerrado para elegibilidad."})
        effect = last.get("efecto_composicion_1m")
        if pd.notna(effect) and abs(float(effect)) >= 1:
            alerts.append({"tipo": "Cambio de composición", "nivel": "precaucion", "dimension": "pulse", "icono": "i",
                "mensaje": f"El cambio de componentes aporta {float(effect):+.1f} puntos a la variación mensual. Consulte el cambio comparable."})
        d3 = self._eligible_change(last, 3)
        if d3 is not None and d3 <= -6:
            alerts.append({"tipo": "Descenso comparable de tres meses", "nivel": "precaucion", "dimension": "pulse", "icono": "v",
                "mensaje": f"Los componentes comunes descendieron {abs(d3):.1f} puntos respecto al mismo mes calendario tres meses atrás."})
        for group in groups.values():
            if group["nivel"] == "critico":
                alerts.append({"tipo": f"Nivel relativo bajo: {group['nombre']}", "nivel": "critico", "dimension": group["nombre"], "icono": "!",
                    "mensaje": f"{group['nombre']}: {group['score_actual']:.1f} puntos. Umbral descriptivo, no probabilidad de riesgo."})
        return alerts

    def _critical_variables(self) -> list[dict]:
        if self.components.empty:
            return []
        latest = self.components.iloc[-1]
        prior_date = self.components.index[-1] - pd.DateOffset(months=1)
        previous = self.components.loc[prior_date] if prior_date in self.components.index else pd.Series(dtype=float)
        group_by_var = {var: meta["nombre"] for meta in GROUPS.values() for var in meta["variables"]}
        rows = []
        for var in PULSE_WEIGHTS:
            if pd.isna(latest.get(var)):
                continue
            prev = previous.get(var)
            delta = round(float(latest[var] - prev), 1) if pd.notna(prev) else None
            rows.append({"label": var.replace("_", " "), "score": round(float(latest[var]), 1),
                         "delta_1m": delta, "delta_1y": delta, "dimension": group_by_var[var]})
        return sorted(rows, key=lambda row: row["score"])[:8]

    def _timeline(self) -> list[dict]:
        return [{"año": int(row["año"]), "mes": int(row["mes"]), "dimension": "pulse",
                 "tipo": "Nivel relativo Pulse < 35", "nivel": "critico"}
                for _, row in self.pulse.iterrows()
                if pd.notna(row["pulse_score"]) and row["pulse_score"] < 35 and row.get("elegible_modelo", False)]

    def _summary(self, groups: dict, alerts: list[dict]) -> dict:
        if self.pulse.empty:
            return {}
        last = self.pulse.iloc[-1]
        delta = self._eligible_change(last, 1)
        trend, _, _ = _trend(delta, self._eligible_change(last, 3))
        levels = [group["nivel"] for group in groups.values()]
        return {"dims_criticas": levels.count("critico"), "dims_precaucion": levels.count("precaucion"),
                "dims_normales": levels.count("normal"), "dims_sin_dato": levels.count("sin_dato"),
                "alertas_criticas": sum(a["nivel"] == "critico" for a in alerts),
                "alertas_precaucion": sum(a["nivel"] == "precaucion" for a in alerts), "alertas_positivas": 0,
                "iciv_delta_1m": delta, "iciv_delta_1y": delta, "iciv_tendencia": trend,
                "fecha": f"{int(last['año'])}-{int(last['mes']):02d}"}
