"""
SATV — Sistema de Alertas Tempranas Venezuela.

Lee los DataFrames ya producidos por el pipeline (df_norm, df_scores) y
computa tres capas de inteligencia sin tocar ningún componente existente:

  Capa 1 — Semáforo por dimensión   (estado actual vs umbrales fijos)
  Capa 2 — Tendencia                (Δ1y · Δ3y · Δ5y por dimensión)
  Capa 3 — Alertas compuestas       (reglas nombradas multi-señal)

Extra  — Backtesting histórico      (cuándo se habría activado cada alerta)
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

# ── Mapeo dimensión → variables (espejo de DIMENSIONS en dimensions.py) ─────
DIM_VARIABLES: dict[str, list[str]] = {
    "D1_macro": [
        "inflacion_deflactor_pib_pct",
        "pib_crecimiento_real_pct",
        "reservas_internacionales_usd",
        "tipo_cambio_oficial_lcu_usd",
        "wti_precio_usd",
        "tasa_fed_funds_pct",
    ],
    "D2_energia": [
        "petroleo_crudo_produccion_tbpd",
        "gas_natural_produccion_bcf",
        "electricidad_generacion_bkwh",
        "luminosidad_nocturna_idx",
    ],
    "D3_institucional": [
        "cpi_score",
        "wgi_promedio_sc",
        "ief_overall_score",
        "freedom_house_score",
        "ofac_sanciones_count",
    ],
    "D4_comercial": [
        "ied_neta_usd",
        "exportaciones_pct_pib",
        "desempleo_pct",
        "migrantes_vzla_millones",
    ],
    "D5_capital_humano": [
        "hdi",
        "tasa_alfabetizacion_adulta_pct",
        "acceso_electricidad_pct",
    ],
    "D6_percepcion": [
        "guardian_tono_titulares",
        "guardian_articulos_venezuela",
        "google_trends_vzla",
    ],
}

DIM_NOMBRES: dict[str, str] = {
    "D1_macro":          "Estabilidad Macroeconómica",
    "D2_energia":        "Sector Energético",
    "D3_institucional":  "Entorno Institucional",
    "D4_comercial":      "Apertura Comercial",
    "D5_capital_humano": "Capital Humano",
    "D6_percepcion":     "Percepción Internacional",
}

AlertLevel  = Literal["critico", "precaucion", "normal", "sin_dato"]
TrendLabel  = Literal["deterioro_acelerado", "deterioro", "estable", "recuperacion", "recuperacion_acelerada"]

# ── Umbrales ──────────────────────────────────────────────────────────────────
_UMBRAL_CRITICO    = 25   # score < 25 → crítico
_UMBRAL_PRECAUCION = 50   # score < 50 → precaución
_DELTA_DETERIORO_FUERTE  = -10.0  # Δ1y
_DELTA_DETERIORO         =  -3.0
_DELTA_RECUPERACION      =   3.0
_DELTA_RECUPERACION_FUERTE = 10.0
_DELTA_3Y_DETERIORO      = -8.0
_DELTA_3Y_RECUPERACION   =  8.0


def _nivel(score: float | None) -> AlertLevel:
    """Convierte un score numérico a nivel de alerta.
    Retorna 'sin_dato' cuando el score es None o NaN — nunca 'normal'."""
    if score is None or (isinstance(score, float) and score != score):  # NaN check
        return "sin_dato"
    if score < _UMBRAL_CRITICO:
        return "critico"
    if score < _UMBRAL_PRECAUCION:
        return "precaucion"
    return "normal"


def _tendencia(delta_1y: float, delta_3y: float) -> TrendLabel:
    if delta_1y < _DELTA_DETERIORO_FUERTE or delta_3y < _DELTA_3Y_DETERIORO * 2:
        return "deterioro_acelerado"
    if delta_1y < _DELTA_DETERIORO or delta_3y < _DELTA_3Y_DETERIORO:
        return "deterioro"
    if delta_1y > _DELTA_RECUPERACION_FUERTE or delta_3y > _DELTA_3Y_RECUPERACION * 2:
        return "recuperacion_acelerada"
    if delta_1y > _DELTA_RECUPERACION or delta_3y > _DELTA_3Y_RECUPERACION:
        return "recuperacion"
    return "estable"


_ARROW: dict[TrendLabel, str] = {
    "deterioro_acelerado":    "↓↓",
    "deterioro":              "↓",
    "estable":                "→",
    "recuperacion":           "↑",
    "recuperacion_acelerada": "↑↑",
}

_TENDENCIA_LABEL: dict[TrendLabel, str] = {
    "deterioro_acelerado":    "Deterioro acelerado",
    "deterioro":              "Deterioro",
    "estable":                "Estable",
    "recuperacion":           "Recuperación",
    "recuperacion_acelerada": "Recuperación acelerada",
}


# ── Engine ────────────────────────────────────────────────────────────────────

class SATVEngine:
    """
    Computa el Sistema de Alertas Tempranas Venezuela.

    Args:
        df_norm:   DataFrame normalizado 0-100.  Columna 'año' + variables.
        df_scores: DataFrame con D1_macro … D6_percepcion + iciv_score por año.
    """

    def __init__(self, df_norm: pd.DataFrame, df_scores: pd.DataFrame) -> None:
        self._norm   = df_norm.copy().sort_values("año").reset_index(drop=True)
        self._scores = (
            df_scores.dropna(subset=["iciv_score"])
            .copy()
            .sort_values("año")
            .reset_index(drop=True)
        )

    # ── API pública ───────────────────────────────────────────────────────────

    def compute_all(self) -> dict:
        dim_status        = self._dim_status()
        alertas           = self._alertas_activas(dim_status)
        timeline          = self._timeline_historico()
        variables_criticas = self._variables_criticas()
        resumen           = self._resumen(dim_status, alertas)
        return {
            "resumen":            resumen,
            "dimensiones":        dim_status,
            "alertas_activas":    alertas,
            "timeline_historico": timeline,
            "variables_criticas": variables_criticas,
        }

    # ── Capa 1 + 2 ────────────────────────────────────────────────────────────

    def _dim_status(self) -> dict:
        last = self._scores.iloc[-1]
        result: dict = {}

        for dim_id, vars_list in DIM_VARIABLES.items():
            if dim_id not in self._scores.columns:
                continue

            series = self._scores[dim_id].dropna()
            if series.empty:
                continue

            # Manejo correcto de NaN: pd.isna(nan) == True
            raw_score = last.get(dim_id)
            score_actual: float | None = None if pd.isna(raw_score) else float(raw_score)

            def delta(n: int) -> float | None:
                """Cambio n-anual del score de la dimensión. None si no hay datos suficientes."""
                # Usar solo valores no-NaN de la serie para calcular deltas
                series_valid = series.dropna()
                if len(series_valid) < n + 1:
                    return None
                return round(float(series_valid.iloc[-1]) - float(series_valid.iloc[-(n + 1)]), 1)

            d1y = delta(1)
            d3y = delta(3)
            d5y = delta(5)
            # Tendencia solo si hay deltas disponibles
            tend = _tendencia(d1y or 0.0, d3y or 0.0)

            # Sparkline — últimos 10 años con datos (excluir NaN)
            spark = [
                round(float(v), 1) if not pd.isna(v) else None
                for v in series.tail(10).tolist()
            ]

            # Variable más crítica: buscar en el último año con datos reales de la norm
            # (no forzosamente el último año del calendario — puede ser que 2026 no tenga datos)
            last_norm_with_data = None
            for idx in range(len(self._norm) - 1, -1, -1):
                row_candidate = self._norm.iloc[idx]
                has_any = any(
                    pd.notna(row_candidate.get(v)) for v in vars_list if v in self._norm.columns
                )
                if has_any:
                    last_norm_with_data = row_candidate
                    break

            if last_norm_with_data is not None:
                disponibles_con_dato = [
                    v for v in vars_list
                    if v in self._norm.columns and pd.notna(last_norm_with_data.get(v))
                ]
            else:
                disponibles_con_dato = []

            if disponibles_con_dato:
                var_scores = {
                    v: float(last_norm_with_data.get(v))
                    for v in disponibles_con_dato
                }
                var_critica       = min(var_scores, key=var_scores.get)
                var_critica_score = round(var_scores[var_critica], 1)
            else:
                var_critica, var_critica_score = "", 0.0

            # Cuántas variables tienen datos en el año actual
            last_norm_any = self._norm.iloc[-1]
            n_vars_disponibles = sum(
                1 for v in vars_list
                if v in self._norm.columns and pd.notna(last_norm_any.get(v))
            )
            n_vars_total = len(vars_list)

            result[dim_id] = {
                "nombre":                 DIM_NOMBRES[dim_id],
                "score_actual":           round(score_actual, 1) if score_actual is not None else None,
                "nivel":                  _nivel(score_actual),
                "delta_1y":               d1y if d1y is not None else 0.0,
                "delta_3y":               d3y if d3y is not None else 0.0,
                "delta_5y":               d5y if d5y is not None else 0.0,
                "tendencia":              tend,
                "tendencia_label":        _TENDENCIA_LABEL[tend],
                "arrow":                  _ARROW[tend],
                "variable_critica":       var_critica,
                "variable_critica_score": var_critica_score,
                "sparkline":              spark,
                "n_vars_disponibles":     n_vars_disponibles,
                "n_vars_total":           n_vars_total,
            }

        return result

    # ── Capa 3 ────────────────────────────────────────────────────────────────

    def _alertas_activas(self, dim_status: dict) -> list[dict]:
        alertas: list[dict] = []
        last    = self._scores.iloc[-1]
        prev    = self._scores.iloc[-2] if len(self._scores) >= 2 else last
        last_norm = self._norm.iloc[-1]

        raw_iciv = last.get("iciv_score")
        iciv_actual = float(raw_iciv) if raw_iciv is not None and not pd.isna(raw_iciv) else 50.0

        # ── Colapso Energético ────────────────────────────────────────────────
        d2 = dim_status.get("D2_energia", {})
        d2_score = d2.get("score_actual")  # puede ser None si no hay datos
        if d2_score is not None and d2_score < 20:
            alertas.append({
                "tipo":      "Colapso Energético",
                "nivel":     "critico",
                "dimension": "D2_energia",
                "icono":     "⚡",
                "mensaje": (
                    f"D2 Energía en {d2_score} pts — el sector petrolero opera al "
                    f"{d2_score:.0f}% de su mejor nivel histórico. "
                    "La capacidad de generación de divisas está severamente comprometida."
                ),
            })

        # ── Aislamiento Internacional ──────────────────────────────────────
        fh_raw  = last_norm.get("freedom_house_score")
        ofac_raw = last_norm.get("ofac_sanciones_count")
        fh  = float(fh_raw) if fh_raw is not None and not pd.isna(fh_raw) else 100.0
        # OFAC es variable NEGATIVA: score bajo = muchas sanciones
        ofac_score = float(ofac_raw) if ofac_raw is not None and not pd.isna(ofac_raw) else 100.0
        if fh < 15 and ofac_score < 10:
            alertas.append({
                "tipo":      "Aislamiento Internacional",
                "nivel":     "critico",
                "dimension": "D3_institucional",
                "icono":     "🌐",
                "mensaje": (
                    "Freedom House en mínimo histórico y máximo nivel de sanciones OFAC activas. "
                    "El aislamiento financiero limita severamente el acceso a banca corresponsal, "
                    "mercados de capitales y contrapartes extranjeras."
                ),
            })

        # ── Contagio Sistémico ─────────────────────────────────────────────
        no_normales = [d for d, s in dim_status.items() if s.get("nivel") != "normal"]
        if len(no_normales) >= 4:
            alertas.append({
                "tipo":      "Contagio Sistémico",
                "nivel":     "critico" if len(no_normales) >= 5 else "precaucion",
                "dimension": "iciv",
                "icono":     "🔗",
                "mensaje": (
                    f"{len(no_normales)} de 6 dimensiones por debajo del umbral normal (≥50 pts). "
                    "El deterioro multidimensional simultáneo indica una crisis estructural, "
                    "no sectorial. No es mitigable con estrategias de un solo sector."
                ),
            })

        # ── Deterioro Acelerado (por dimensión) ───────────────────────────
        for dim_id, s in dim_status.items():
            if s.get("delta_1y", 0) < -15:
                alertas.append({
                    "tipo":      "Deterioro Acelerado",
                    "nivel":     "precaucion",
                    "dimension": dim_id,
                    "icono":     "📉",
                    "mensaje": (
                        f"{DIM_NOMBRES.get(dim_id, dim_id)} cayó "
                        f"{abs(s['delta_1y']):.1f} pts en el último año "
                        "(umbral: 15 pts). Requiere monitoreo trimestral inmediato."
                    ),
                })

        # ── Pre-Colapso ICIV ──────────────────────────────────────────────
        iciv_series = self._scores["iciv_score"].dropna()
        if iciv_actual < 35 and len(iciv_series) >= 3:
            last3 = iciv_series.tail(3).tolist()
            if last3[-1] < last3[-2] < last3[-3]:
                alertas.append({
                    "tipo":      "Pre-Colapso ICIV",
                    "nivel":     "critico",
                    "dimension": "iciv",
                    "icono":     "🚨",
                    "mensaje": (
                        f"ICIV en {iciv_actual:.1f} pts y en tendencia descendente 3 años consecutivos. "
                        "Patrón idéntico al registrado en 2014–2016 y 2018–2020. "
                        "Se recomienda suspender evaluaciones de entrada hasta estabilización."
                    ),
                })

        # ── Señal de Recuperación ─────────────────────────────────────────
        if len(iciv_series) >= 3:
            last3 = iciv_series.tail(3).tolist()
            if (last3[-1] > last3[-2] > last3[-3]
                    and (last3[-1] - last3[-3]) > 5):
                alertas.append({
                    "tipo":      "Señal de Recuperación",
                    "nivel":     "normal",
                    "dimension": "iciv",
                    "icono":     "📈",
                    "mensaje": (
                        f"ICIV subió {last3[-1]-last3[-3]:.1f} pts en 2 años consecutivos. "
                        "Primera señal de estabilización sostenida. Iniciar due diligence "
                        "sectorial en energía y comercio exterior."
                    ),
                })

        return alertas

    # ── Backtesting histórico ─────────────────────────────────────────────────

    def _timeline_historico(self) -> list[dict]:
        """Detecta cuándo cada alerta se habría activado en la serie histórica."""
        eventos: list[dict] = []

        for i in range(1, len(self._scores)):
            row  = self._scores.iloc[i]
            prev = self._scores.iloc[i - 1]
            año  = int(row["año"])

            iciv_now  = float(row.get("iciv_score",  50) or 50)
            iciv_prev = float(prev.get("iciv_score", 50) or 50)

            # ICIV cruza zona crítica
            if iciv_now < 35 and iciv_prev >= 35:
                eventos.append({"año": año, "evento": "ICIV entra zona crítica (<35)",
                                "nivel": "critico", "dimension": "iciv"})
            elif iciv_now >= 35 and iciv_prev < 35:
                eventos.append({"año": año, "evento": "ICIV sale zona crítica",
                                "nivel": "normal", "dimension": "iciv"})

            for dim_id in DIM_VARIABLES:
                if dim_id not in row.index:
                    continue
                s_now  = float(row.get(dim_id,  50) or 50)
                s_prev = float(prev.get(dim_id, 50) or 50)
                nombre = DIM_NOMBRES[dim_id]

                if s_now < _UMBRAL_CRITICO and s_prev >= _UMBRAL_CRITICO:
                    eventos.append({"año": año, "evento": f"{nombre} — entra zona crítica",
                                    "nivel": "critico", "dimension": dim_id})
                elif s_now < _UMBRAL_PRECAUCION and s_prev >= _UMBRAL_PRECAUCION:
                    eventos.append({"año": año, "evento": f"{nombre} — entra precaución",
                                    "nivel": "precaucion", "dimension": dim_id})
                elif s_now >= _UMBRAL_PRECAUCION and s_prev < _UMBRAL_PRECAUCION:
                    eventos.append({"año": año, "evento": f"{nombre} — recupera zona normal",
                                    "nivel": "normal", "dimension": dim_id})

        return sorted(eventos, key=lambda x: x["año"])

    # ── Variables más críticas ────────────────────────────────────────────────

    def _variables_criticas(self) -> list[dict]:
        """Top 5 variables con peor score en el año más reciente."""
        from iciv.data.catalog import CATALOG

        last_norm = self._norm.iloc[-1]
        prev_norm = self._norm.iloc[-2] if len(self._norm) >= 2 else last_norm

        import math
        entradas = []
        for col in self._norm.columns:
            if col == "año":
                continue
            raw_score = last_norm.get(col, None)
            raw_prev  = prev_norm.get(col, None)

            # Si el score del último año es NaN → sin dato real, excluir del ranking
            # (NaN ≠ "peor" — significa que Venezuela no reportó esta variable)
            try:
                score_f = float(raw_score)
            except (TypeError, ValueError):
                continue
            if math.isnan(score_f):
                continue

            try:
                prev_f = float(raw_prev)
                if math.isnan(prev_f):
                    prev_f = score_f
            except (TypeError, ValueError):
                prev_f = score_f

            meta  = CATALOG.get(col)
            entradas.append({
                "variable":  col,
                "label":     meta.description if meta else col,
                "score":     round(score_f, 1),
                "delta_1y":  round(score_f - prev_f, 1),
                "dimension": meta.dimension.value if meta else "",
            })

        entradas.sort(key=lambda x: x["score"])
        return entradas[:5]

    # ── Resumen ejecutivo ─────────────────────────────────────────────────────

    def _resumen(self, dim_status: dict, alertas: list[dict]) -> dict:
        criticas   = sum(1 for s in dim_status.values() if s["nivel"] == "critico")
        precaucion = sum(1 for s in dim_status.values() if s["nivel"] == "precaucion")
        normales   = sum(1 for s in dim_status.values() if s["nivel"] == "normal")

        iciv_series = self._scores["iciv_score"].dropna()
        iciv_actual = float(iciv_series.iloc[-1])
        iciv_prev   = float(iciv_series.iloc[-2]) if len(iciv_series) >= 2 else iciv_actual
        delta_1y    = round(iciv_actual - iciv_prev, 1)

        if delta_1y < -3:
            tend = "deterioro"
        elif delta_1y > 3:
            tend = "recuperacion"
        else:
            tend = "estable"

        return {
            "dims_criticas":       criticas,
            "dims_precaucion":     precaucion,
            "dims_normales":       normales,
            "iciv_tendencia":      tend,
            "iciv_delta_1y":       delta_1y,
            "alertas_criticas":    sum(1 for a in alertas if a["nivel"] == "critico"),
            "alertas_precaucion":  sum(1 for a in alertas if a["nivel"] == "precaucion"),
            "alertas_positivas":   sum(1 for a in alertas if a["nivel"] == "normal"),
        }
