"""
ICIV — Análisis de Indicadores Líderes (Early Warning Power).

Para cada una de las 27 variables normalizadas del ICIV, calcula:
  1. Correlación de Pearson LEAD: var(t) vs iciv_score(t+k) para k=1,2,3.
  2. Causalidad de Granger: ¿var(t) Granger-causa iciv(t+1)?
  3. Early Warning Score (EWS): métrica compuesta 0–1 de poder predictivo.
  4. Señal actual: ¿está la variable enviando una señal de alerta o recuperación?

El EWS pondera la correlación máxima en rezago 1–3 con la significancia de Granger.
Una variable con EWS > 0.5 y señal "alerta" es un indicador líder de deterioro
inminente del clima de inversión.

Metodología:
  Pearson cross-lag: Hyndman & Athanasopoulos (2021), §5.1 — Forecasting: Principles
    and Practice (3rd ed.), Monash University.
  Granger causality: Granger, C.W.J. (1969). Econometrica, 37(3), 424–438.
  Early Warning Systems en macroeconomía: Kaminsky, G., Lizondo, S. & Reinhart, C.
    (1998). "Leading Indicators of Currency Crises". IMF Staff Papers, 45(1), 1–48.
"""

from __future__ import annotations

import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Etiquetas legibles para las variables del catálogo
_VAR_LABELS: dict[str, str] = {
    "inflacion_deflactor_pib_pct":      "Inflación — Deflactor PIB",
    "pib_crecimiento_real_pct":         "Crecimiento PIB Real",
    "reservas_internacionales_usd":     "Reservas Internacionales (USD)",
    "tipo_cambio_oficial_lcu_usd":      "Tipo de Cambio Oficial",
    "wti_precio_usd":                   "Precio WTI (USD/barril)",
    "tasa_fed_funds_pct":               "Tasa Fed Funds (%)",
    "petroleo_crudo_produccion_tbpd":   "Producción Petróleo (tbpd)",
    "gas_natural_produccion_bcf":       "Producción Gas Natural (bcf)",
    "electricidad_generacion_bkwh":     "Generación Eléctrica (bkWh)",
    "luminosidad_nocturna_idx":         "Luminosidad Nocturna (VIIRS)",
    "cpi_score":                        "Índice de Corrupción (CPI)",
    "wgi_promedio_sc":                  "WGI Gobernanza Promedio",
    "ief_overall_score":                "Libertad Económica (IEF)",
    "freedom_house_score":              "Freedom House Score",
    "ofac_sanciones_count":             "Sanciones OFAC (conteo)",
    "ied_neta_usd":                     "IED Neta (USD)",
    "exportaciones_pct_pib":            "Exportaciones (% PIB)",
    "desempleo_pct":                    "Desempleo (%)",
    "lsci_conectividad_maritima":       "Conectividad Marítima (LSCI)",
    "vuelos_aerolineas_int_count":      "Vuelos Aerolíneas Internacionales",
    "migrantes_vzla_millones":          "Migrantes Venezolanos (M)",
    "hdi":                              "Índice de Desarrollo Humano (IDH)",
    "tasa_alfabetizacion_adulta_pct":   "Tasa de Alfabetización (%)",
    "acceso_electricidad_pct":          "Acceso a Electricidad (%)",
    "google_trends_vzla":               "Google Trends — Venezuela",
    "guardian_tono_titulares":          "Tono Mediático (Guardian VADER)",
    "guardian_articulos_venezuela":     "Artículos Guardian — Venezuela",
}

# Dirección de cada variable respecto al ICIV
# "positive" → sube cuando ICIV mejora; "negative" → sube cuando ICIV empeora
_VAR_DIRECTIONS: dict[str, str] = {
    "inflacion_deflactor_pib_pct":      "negative",
    "pib_crecimiento_real_pct":         "positive",
    "reservas_internacionales_usd":     "positive",
    "tipo_cambio_oficial_lcu_usd":      "negative",
    "wti_precio_usd":                   "positive",
    "tasa_fed_funds_pct":               "negative",
    "petroleo_crudo_produccion_tbpd":   "positive",
    "gas_natural_produccion_bcf":       "positive",
    "electricidad_generacion_bkwh":     "positive",
    "luminosidad_nocturna_idx":         "positive",
    "cpi_score":                        "positive",
    "wgi_promedio_sc":                  "positive",
    "ief_overall_score":                "positive",
    "freedom_house_score":              "positive",
    "ofac_sanciones_count":             "negative",
    "ied_neta_usd":                     "positive",
    "exportaciones_pct_pib":            "positive",
    "desempleo_pct":                    "negative",
    "lsci_conectividad_maritima":       "positive",
    "vuelos_aerolineas_int_count":      "positive",
    "migrantes_vzla_millones":          "negative",
    "hdi":                              "positive",
    "tasa_alfabetizacion_adulta_pct":   "positive",
    "acceso_electricidad_pct":          "positive",
    "google_trends_vzla":               "positive",
    "guardian_tono_titulares":          "positive",
    "guardian_articulos_venezuela":     "positive",
}

_DIM_MAP: dict[str, str] = {
    "inflacion_deflactor_pib_pct":      "D1 Macro",
    "pib_crecimiento_real_pct":         "D1 Macro",
    "reservas_internacionales_usd":     "D1 Macro",
    "tipo_cambio_oficial_lcu_usd":      "D1 Macro",
    "wti_precio_usd":                   "D1 Macro",
    "tasa_fed_funds_pct":               "D1 Macro",
    "petroleo_crudo_produccion_tbpd":   "D2 Energía",
    "gas_natural_produccion_bcf":       "D2 Energía",
    "electricidad_generacion_bkwh":     "D2 Energía",
    "luminosidad_nocturna_idx":         "D2 Energía",
    "cpi_score":                        "D3 Institucional",
    "wgi_promedio_sc":                  "D3 Institucional",
    "ief_overall_score":                "D3 Institucional",
    "freedom_house_score":              "D3 Institucional",
    "ofac_sanciones_count":             "D3 Institucional",
    "ied_neta_usd":                     "D4 Comercial",
    "exportaciones_pct_pib":            "D4 Comercial",
    "desempleo_pct":                    "D4 Comercial",
    "lsci_conectividad_maritima":       "D4 Comercial",
    "vuelos_aerolineas_int_count":      "D4 Comercial",
    "migrantes_vzla_millones":          "D4 Comercial",
    "hdi":                              "D5 Capital Humano",
    "tasa_alfabetizacion_adulta_pct":   "D5 Capital Humano",
    "acceso_electricidad_pct":          "D5 Capital Humano",
    "google_trends_vzla":               "D6 Percepción",
    "guardian_tono_titulares":          "D6 Percepción",
    "guardian_articulos_venezuela":     "D6 Percepción",
}


class LeadingIndicatorsAnalyzer:
    """
    Analiza cuáles variables del ICIV tienen mayor poder de anticipación
    (leading power) sobre la evolución futura del índice.

    Args:
        df_norm:   DataFrame con variables normalizadas 0–100 (columna 'año').
        df_scores: DataFrame con 'año' e 'iciv_score' (serie AHP).
    """

    MAX_LAG = 3          # Horizonte de predicción máximo (años)
    GRANGER_MAXLAG = 2   # Máximo rezago para Granger (preserva g.d.l. con n=27)
    MIN_OBS = 8          # Mínimo de observaciones para calcular correlación

    def __init__(self, df_norm: pd.DataFrame, df_scores: pd.DataFrame) -> None:
        self._norm   = df_norm.copy()
        self._scores = df_scores[["año", "iciv_score"]].dropna().copy()
        self._scores["año"] = self._scores["año"].astype(int)
        self._norm["año"]   = self._norm["año"].astype(int)

        # Variables disponibles (excluir 'año')
        self._vars = [c for c in self._norm.columns if c != "año"
                      and self._norm[c].notna().sum() >= self.MIN_OBS]

    # ─────────────────────────────────────────────────────────────────────────
    # API pública
    # ─────────────────────────────────────────────────────────────────────────

    def compute_all(self) -> dict:
        """Retorna dict completo para el dashboard."""
        records = []
        for var in self._vars:
            rec = self._analyze_variable(var)
            if rec:
                records.append(rec)

        if not records:
            return {"error": "Datos insuficientes para análisis de indicadores líderes."}

        # Ordenar por EWS descendente
        records.sort(key=lambda r: r["ews"], reverse=True)
        top10 = records[:10]

        # Resumen de señales actuales
        signals = [r["signal"] for r in records]
        resumen = {
            "alertas":    signals.count("alerta"),
            "precaucion": signals.count("precaucion"),
            "neutro":     signals.count("neutro"),
            "positivo":   signals.count("positivo"),
        }

        # Barómetro agregado (promedio ponderado de señal × EWS)
        signal_scores = {"alerta": 0, "precaucion": 33, "neutro": 66, "positivo": 100}
        total_ews = sum(r["ews"] for r in records) or 1.0
        barometro = sum(
            signal_scores.get(r["signal"], 50) * r["ews"] for r in records
        ) / total_ews
        barometro = round(barometro, 1)

        if barometro < 25:
            barometro_label = "Deterioro Inminente"
        elif barometro < 45:
            barometro_label = "Señales de Deterioro"
        elif barometro < 60:
            barometro_label = "Mixto — Sin Tendencia Clara"
        elif barometro < 78:
            barometro_label = "Señales de Estabilización"
        else:
            barometro_label = "Señales de Recuperación"

        return {
            "top_lideres":       top10,
            "tabla_completa":    records,
            "resumen_senales":   resumen,
            "barometro_score":   barometro,
            "barometro_label":   barometro_label,
            "n_variables":       len(records),
            "periodo":           f"{int(self._scores['año'].min())}–{int(self._scores['año'].max())}",
            "metodologia": (
                "Pearson cross-lag (k=1–3 años): correlación var(t) vs ICIV(t+k). "
                "Granger causality (maxlag=2, statsmodels). "
                "EWS = max|r_k| × (1 si Granger sig. al 10%, 0.5 si no). "
                "Señal actual: comportamiento Δ3y de la variable vs su dirección esperada. "
                "Ref.: Kaminsky, Lizondo & Reinhart (1998), IMF Staff Papers 45(1)."
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Métodos privados
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_variable(self, var: str) -> dict | None:
        """Calcula métricas de indicador líder para una variable."""
        from scipy import stats as sp_stats

        # Construir panel: var(t) y iciv(t) por año
        df = self._norm[["año", var]].dropna()
        df = df.merge(self._scores, on="año", how="inner").sort_values("año")
        if len(df) < self.MIN_OBS:
            return None

        # ── 1. Pearson cross-lag k=1..MAX_LAG ────────────────────────────────
        lead_corrs: list[dict] = []
        for k in range(1, self.MAX_LAG + 1):
            x = df[var].values[:-k]           # var(t)
            y = df["iciv_score"].values[k:]    # iciv(t+k)
            if len(x) < 5:
                continue
            r, p = sp_stats.pearsonr(x, y)
            lead_corrs.append({"lag": k, "r": round(float(r), 4), "p": round(float(p), 4), "sig": p < 0.10})

        if not lead_corrs:
            return None

        # Mejor rezago (|r| máximo en k=1..MAX_LAG)
        best = max(lead_corrs, key=lambda d: abs(d["r"]))

        # ── 2. Granger: var(t) → iciv(t) ─────────────────────────────────────
        granger_p = 1.0
        granger_sig = False
        try:
            from statsmodels.tsa.stattools import grangercausalitytests, adfuller

            test_df = df[[var, "iciv_score"]].dropna()
            # Diferenciar si hay raíz unitaria
            adf_var  = adfuller(test_df[var].values, autolag="AIC")[1]
            adf_iciv = adfuller(test_df["iciv_score"].values, autolag="AIC")[1]
            if adf_var > 0.05 or adf_iciv > 0.05:
                test_df = test_df.diff().dropna()

            if len(test_df) >= 10:
                res = grangercausalitytests(test_df[[var, "iciv_score"]],
                                            maxlag=self.GRANGER_MAXLAG, verbose=False)
                # Tomar el lag 1 como referencia
                f_test = res[1][0]["ssr_ftest"]
                granger_p   = round(float(f_test[1]), 4)
                granger_sig = granger_p < 0.10
        except Exception:
            pass

        # ── 3. Early Warning Score ─────────────────────────────────────────────
        r_abs   = abs(best["r"])
        granger_bonus = 1.0 if granger_sig else 0.5
        ews = round(r_abs * granger_bonus, 4)

        # ── 4. Señal actual — comportamiento reciente de la variable ──────────
        recent = df[var].dropna()
        val_now = float(recent.iloc[-1])
        val_3y  = float(recent.iloc[-4]) if len(recent) >= 4 else float(recent.iloc[0])
        delta_3y = round(val_now - val_3y, 2)

        direction = _VAR_DIRECTIONS.get(var, "positive")
        # Una variable "positiva" cayendo = señal de alerta
        # Una variable "negativa" subiendo = señal de alerta
        if direction == "positive":
            if delta_3y < -8:   signal = "alerta"
            elif delta_3y < -3: signal = "precaucion"
            elif delta_3y > 5:  signal = "positivo"
            else:               signal = "neutro"
        else:   # negative direction: sube cuando empeora
            if delta_3y > 8:   signal = "alerta"
            elif delta_3y > 3: signal = "precaucion"
            elif delta_3y < -5: signal = "positivo"
            else:               signal = "neutro"

        signal_colors = {
            "alerta":     "#e05c5c",
            "precaucion": "#e67e22",
            "neutro":     "#8b949e",
            "positivo":   "#2ecc71",
        }

        # Últimos 10 años (sparkline)
        sparkline_raw = df[[var]].dropna().tail(10)[var].tolist()
        sparkline = [round(float(v), 1) for v in sparkline_raw]

        return {
            "variable":         var,
            "label":            _VAR_LABELS.get(var, var),
            "dimension":        _DIM_MAP.get(var, "—"),
            "best_lag":         best["lag"],
            "r_max":            best["r"],
            "r_abs":            abs(best["r"]),
            "p_best":           best["p"],
            "lag_sig":          best["sig"],
            "granger_p":        granger_p,
            "granger_sig":      granger_sig,
            "ews":              ews,
            "signal":           signal,
            "signal_color":     signal_colors[signal],
            "valor_actual_norm": round(val_now, 1),
            "delta_3y":         delta_3y,
            "serie_historica":  sparkline,
            "lead_corrs":       lead_corrs,
        }
