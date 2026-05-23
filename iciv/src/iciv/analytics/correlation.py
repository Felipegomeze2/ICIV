"""
Análisis de Correlación y Causalidad ICIV → IED — Venezuela (2000–2026).

Metodología:
  1. Cross-correlación de Pearson (rezagos 0–4 años): mide la asociación
     lineal entre ICIV_{t-k} e IED_{t} para cada rezago k.
     Pregunta exploratoria: si el ICIV antecede estadísticamente los flujos de IED.

  2. Regresión OLS:
       IED_t = β₀ + β₁·ICIV_{t-1} + ε              (modelo con 1 rezago)
       IED_t = β₀ + β₁·ICIV_{t-1} + β₂·ICIV_{t-2} + ε  (2 rezagos)
     El coeficiente β₁ resume la asociación estimada entre ICIV rezagado e IED;
     por sí solo no prueba causalidad económica.

  3. Test de Causalidad de Granger (Granger, 1969):
     H₀: el ICIV no Granger-causa la IED.
     Se usan maxlags = 2 para preservar grados de libertad (n=27).
     Requiere pre-test de estacionariedad (ADF) y, si la serie es
     integrada de orden 1, diferenciación antes de aplicar el test.

  4. Test ADF de estacionariedad (Dickey & Fuller, 1979):
     Determina si las series son I(0) o I(1) para seleccionar la
     especificación correcta del test de Granger.

Referencias:
  Granger, C.W.J. (1969). Investigating causal relations by econometric
    models and cross-spectral methods. Econometrica, 37(3), 424–438.
  Dickey, D.A. & Fuller, W.A. (1979). Distribution of the estimators for
    autoregressive time series with a unit root. JASA, 74(366), 427–431.
  Greene, W.H. (2018). Econometric Analysis (8th ed.). Pearson.

Nota sobre Venezuela: la IED venezolana es estructuralmente negativa
desde 2015 (desinversión neta). El análisis usa los valores originales
sin transformar, pues la correlación lineal es válida para valores negativos.
El scatter muestra la relación directamente interpretable.
"""

from __future__ import annotations

import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class CorrelationAnalyzer:
    """
    Computa la relación estadística entre el ICIV y los flujos de IED a Venezuela.

    Args:
        df_raw:    DataFrame maestro con la variable 'ied_neta_usd' (valores crudos).
        df_scores: DataFrame con columnas 'año' e 'iciv_score' (serie AHP 0–100).
    """

    MAX_LAGS = 4

    def __init__(self, df_raw: pd.DataFrame, df_scores: pd.DataFrame) -> None:
        self._raw    = df_raw.copy()
        self._scores = df_scores[["año", "iciv_score"]].dropna().copy()

    # ─────────────────────────────────────────────────────────────────────────
    def compute_all(self) -> dict:
        """Retorna dict completo para el dashboard."""
        df = self._build_panel()
        if df is None or len(df) < 10:
            return {"error": "Datos insuficientes para análisis de correlación."}

        cross_corr = self._cross_correlation(df)
        ols_1lag   = self._ols(df, lags=1)
        ols_2lag   = self._ols(df, lags=2)
        adf_iciv   = self._adf(df["iciv"])
        adf_ied    = self._adf(df["ied"])
        granger    = self._granger(df)

        # Scatter data: ICIV_{t-1} vs IED_t
        scatter = self._scatter_data(df, lag=1)

        return {
            "panel": {
                "años":  [int(y) for y in df["año"].tolist()],
                "iciv":  [round(float(v), 2) for v in df["iciv"].tolist()],
                "ied":   [round(float(v) / 1e9, 3) for v in df["ied"].tolist()],  # en miles de millones
            },
            "cross_correlation": cross_corr,
            "ols_1lag":          ols_1lag,
            "ols_2lag":          ols_2lag,
            "adf": {
                "iciv": adf_iciv,
                "ied":  adf_ied,
            },
            "granger":  granger,
            "scatter":  scatter,
            "n_obs":    int(len(df)),
            "periodo":  f"{int(df['año'].min())}–{int(df['año'].max())}",
            "nota_ied": (
                "IED expresada en miles de millones USD. Valores negativos indican "
                "desinversión neta (fuga de capital). Período de desinversión sostenida: "
                "2015–2026, correlacionado con el colapso del ICIV post-2014."
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Métodos privados
    # ─────────────────────────────────────────────────────────────────────────

    def _build_panel(self) -> pd.DataFrame | None:
        """Combina ICIV e IED en un panel anual limpio."""
        if "ied_neta_usd" not in self._raw.columns or "año" not in self._raw.columns:
            return None
        ied = self._raw[["año", "ied_neta_usd"]].copy()
        ied["año"] = ied["año"].astype(int)
        df = self._scores.merge(ied, on="año", how="inner")
        df = df.rename(columns={"iciv_score": "iciv", "ied_neta_usd": "ied"})
        df = df.dropna(subset=["iciv", "ied"]).sort_values("año").reset_index(drop=True)
        return df if len(df) >= 8 else None

    def _cross_correlation(self, df: pd.DataFrame) -> list[dict]:
        """Pearson r entre ICIV_{t-lag} e IED_t para lags 0..MAX_LAGS."""
        from scipy import stats
        results = []
        for lag in range(self.MAX_LAGS + 1):
            iciv_lag = df["iciv"].shift(lag)
            ied      = df["ied"]
            mask = iciv_lag.notna() & ied.notna()
            x, y = iciv_lag[mask].values, ied[mask].values
            if len(x) < 5:
                continue
            r, p = stats.pearsonr(x, y)
            results.append({
                "lag":    lag,
                "r":      round(float(r), 4),
                "p":      round(float(p), 4),
                "n":      int(mask.sum()),
                "sig":    p < 0.05,
                "label":  f"Rezago {lag}a" if lag > 0 else "Contemporáneo",
            })
        return results

    def _ols(self, df: pd.DataFrame, lags: int = 1) -> dict:
        """OLS: IED_t ~ ICIV_{t-1} (+ ICIV_{t-2} si lags=2)."""
        try:
            import statsmodels.api as sm
        except ImportError:
            return {"error": "statsmodels no disponible"}

        data = df.copy()
        for k in range(1, lags + 1):
            data[f"iciv_lag{k}"] = data["iciv"].shift(k)
        data = data.dropna()
        if len(data) < 6:
            return {"error": "Muestra insuficiente"}

        x_cols = [f"iciv_lag{k}" for k in range(1, lags + 1)]
        X = sm.add_constant(data[x_cols])
        y = data["ied"] / 1e9  # convertir a miles de millones

        model  = sm.OLS(y, X).fit()
        params = {}
        for name, coef, se, tstat, pval in zip(
            model.params.index, model.params, model.bse, model.tvalues, model.pvalues
        ):
            params[name] = {
                "coef":  round(float(coef), 4),
                "se":    round(float(se), 4),
                "tstat": round(float(tstat), 3),
                "pval":  round(float(pval), 4),
                "sig":   float(pval) < 0.05,
            }

        return {
            "lags":    lags,
            "r2":      round(float(model.rsquared), 4),
            "r2_adj":  round(float(model.rsquared_adj), 4),
            "f_stat":  round(float(model.fvalue), 3),
            "f_pval":  round(float(model.f_pvalue), 4),
            "n":       int(model.nobs),
            "params":  params,
            "formula": f"IED_t = β₀ + " + " + ".join(f"β{k}·ICIV_{{t-{k}}}" for k in range(1, lags+1)) + " + ε",
        }

    def _adf(self, series: pd.Series) -> dict:
        """Augmented Dickey-Fuller test de estacionariedad."""
        try:
            from statsmodels.tsa.stattools import adfuller
        except ImportError:
            return {"error": "statsmodels no disponible"}

        clean = series.dropna()
        if len(clean) < 8:
            return {"stat": None}

        result = adfuller(clean, autolag="AIC")
        stat, pval = result[0], result[1]
        cv5 = result[4]["5%"]
        return {
            "stat":        round(float(stat), 4),
            "pval":        round(float(pval), 4),
            "cv_5pct":     round(float(cv5), 4),
            "stationary":  bool(pval < 0.05),
            "label":       "Estacionaria I(0)" if pval < 0.05 else "No estacionaria I(1) — diferenciación recomendada",
        }

    def _granger(self, df: pd.DataFrame) -> dict:
        """Test de Causalidad de Granger: ¿ICIV Granger-causa IED?"""
        try:
            from statsmodels.tsa.stattools import grangercausalitytests
        except ImportError:
            return {"error": "statsmodels no disponible"}

        data = df[["ied", "iciv"]].dropna()
        if len(data) < 12:
            return {"error": "Muestra insuficiente para Granger (mínimo 12 obs.)"}

        # Usar diferencias si alguna serie es no-estacionaria
        adf_ied  = self._adf(data["ied"])
        adf_iciv = self._adf(data["iciv"])
        use_diff = not (adf_ied.get("stationary", True) and adf_iciv.get("stationary", True))

        test_data = data.copy()
        if use_diff:
            test_data = test_data.diff().dropna()

        results_by_lag = {}
        for lag in [1, 2]:
            try:
                res = grangercausalitytests(test_data[["ied", "iciv"]], maxlag=lag, verbose=False)
                f_test = res[lag][0]["ssr_ftest"]
                results_by_lag[lag] = {
                    "f_stat": round(float(f_test[0]), 4),
                    "p_val":  round(float(f_test[1]), 4),
                    "df_den": int(f_test[3]),
                    "reject_h0": bool(f_test[1] < 0.05),
                }
            except Exception:
                results_by_lag[lag] = {"error": "No convergió"}

        best = results_by_lag.get(1, {})
        conclusion = (
            "El ICIV Granger-causa la IED (p < 0.05): variaciones en el ICIV "
            "preceden y predicen estadísticamente los flujos de inversión."
            if best.get("reject_h0")
            else
            "No se rechaza H₀ al 5%: no se confirma causalidad de Granger con los datos disponibles. "
            "La correlación observada puede deberse a factores comunes (precio del petróleo, "
            "sanciones) que afectan simultáneamente ambas variables."
        )

        return {
            "diferenciado": use_diff,
            "nota_diff":    "Series diferenciadas (I→ΔI) por no-estacionariedad ADF" if use_diff else "Series en niveles (estacionarias ADF)",
            "por_lag":      results_by_lag,
            "conclusion":   conclusion,
        }

    def _scatter_data(self, df: pd.DataFrame, lag: int = 1) -> list[dict]:
        """Datos para scatter ICIV_{t-lag} vs IED_t con línea de regresión."""
        data = df.copy()
        data["iciv_lagged"] = data["iciv"].shift(lag)
        data = data.dropna(subset=["iciv_lagged", "ied"])

        pts = []
        for _, row in data.iterrows():
            pts.append({
                "año":  int(row["año"]),
                "x":    round(float(row["iciv_lagged"]), 2),
                "y":    round(float(row["ied"]) / 1e9, 3),
            })

        # Línea de regresión
        xs = np.array([p["x"] for p in pts])
        ys = np.array([p["y"] for p in pts])
        if len(xs) >= 3:
            coeffs = np.polyfit(xs, ys, 1)
            x_min, x_max = float(xs.min()), float(xs.max())
            reg_line = [
                {"x": round(x_min, 1), "y": round(float(np.poly1d(coeffs)(x_min)), 3)},
                {"x": round(x_max, 1), "y": round(float(np.poly1d(coeffs)(x_max)), 3)},
            ]
        else:
            reg_line = []

        return {"puntos": pts, "regresion": reg_line, "lag": lag}
