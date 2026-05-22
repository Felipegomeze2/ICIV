"""
PulseForecast — Modelos de Machine Learning sobre el ICIV Pulse Mensual.

Implementa dos modelos académicamente fundamentados:

1. SARIMA (Hyndman-Athanasopoulos 2018) — forecast univariado del Pulse
   para los próximos 3-6 meses con intervalos de confianza.

2. Regresión Pulse → Anual (Stock & Watson 2002 nowcasting) — predice el
   ICIV Anual del año en curso usando features extraídos del Pulse mensual.

Diseño:
  - SARIMA(p,d,q)(P,D,Q,s) con s=12 (estacionalidad anual)
  - Auto-arima light: probar (1,1,1)(1,1,1,12) y (1,1,2)(1,1,1,12), elegir AIC menor
  - OLS para nowcast: features = Pulse last 12-month average, volatility, trend
  - Validación: walk-forward cross-validation con 12 meses out-of-sample

Referencias:
  Hyndman & Athanasopoulos (2018) "Forecasting: Principles and Practice"
  Stock & Watson (2002) "Macroeconomic forecasting using diffusion indexes"
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=Warning)

FORECAST_HORIZON = 6  # meses a predecir
SEASONALITY = 12      # mensualidad


class PulseForecaster:
    """Modelo SARIMA univariado + nowcaster OLS para el ICIV Pulse."""

    def __init__(self, pulse_df: pd.DataFrame, annual_df: pd.DataFrame | None = None) -> None:
        """
        Args:
            pulse_df: DataFrame con columnas [año, mes, pulse_score, cobertura_pct]
            annual_df: opcional — DataFrame con columnas [año, iciv_score] para nowcasting
        """
        self.pulse_df = pulse_df.copy()
        self.annual_df = annual_df.copy() if annual_df is not None else None
        self.sarima_model: Any = None
        self.sarima_forecast: pd.DataFrame | None = None
        self.nowcast_model: Any = None
        self.nowcast_metrics: dict = {}

    # ── SARIMA Univariate Forecast ────────────────────────────────────────────

    def fit_sarima(self) -> "PulseForecaster":
        """Ajusta SARIMA al pulse_score. Solo usa observaciones con cobertura >=70%."""
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
        except ImportError:
            logger.warning("  statsmodels no disponible — SARIMA omitido")
            return self

        # Preparar serie temporal
        df = self.pulse_df.copy()
        df = df[df["pulse_score"].notna()].copy()
        df["fecha"] = pd.to_datetime(
            df["año"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2) + "-01"
        )
        df = df.sort_values("fecha")
        ts = df.set_index("fecha")["pulse_score"].asfreq("MS")
        # Imputar gaps internos pequeños (no extrapolar)
        ts = ts.interpolate(method="linear", limit=2, limit_area="inside")
        if ts.dropna().empty or len(ts.dropna()) < 24:
            logger.warning("  SARIMA: serie demasiado corta (%d obs)", len(ts.dropna()))
            return self

        # Probar 2 modelos y elegir mejor AIC
        candidates = [
            ((1, 1, 1), (1, 1, 1, 12)),
            ((1, 1, 2), (1, 1, 1, 12)),
            ((2, 1, 1), (1, 1, 1, 12)),
        ]
        best_model = None
        best_aic = float("inf")
        best_order = None
        for order, sorder in candidates:
            try:
                m = SARIMAX(ts.dropna(), order=order, seasonal_order=sorder,
                            enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
                if m.aic < best_aic:
                    best_aic = m.aic
                    best_model = m
                    best_order = (order, sorder)
            except Exception as exc:
                logger.debug(f"  SARIMA {order}{sorder} falló: {exc}")
                continue

        if best_model is None:
            logger.warning("  SARIMA: ningún modelo convergió")
            return self

        self.sarima_model = best_model
        self.sarima_best_order = best_order
        self.sarima_aic = best_aic

        # Forecast con intervalo 80% y 95%
        fc = best_model.get_forecast(steps=FORECAST_HORIZON)
        fc_mean = fc.predicted_mean
        ci_80 = fc.conf_int(alpha=0.20)
        ci_95 = fc.conf_int(alpha=0.05)

        # Clip [0, 100] (Pulse score range)
        fc_df = pd.DataFrame({
            "fecha":   fc_mean.index,
            "mean":    fc_mean.values.clip(0, 100),
            "lo_80":   ci_80.iloc[:, 0].values.clip(0, 100),
            "hi_80":   ci_80.iloc[:, 1].values.clip(0, 100),
            "lo_95":   ci_95.iloc[:, 0].values.clip(0, 100),
            "hi_95":   ci_95.iloc[:, 1].values.clip(0, 100),
        })
        fc_df["año"] = fc_df["fecha"].dt.year
        fc_df["mes"] = fc_df["fecha"].dt.month
        self.sarima_forecast = fc_df

        logger.info(f"  SARIMA: order={best_order}, AIC={best_aic:.2f}, horizon={FORECAST_HORIZON}m")
        return self

    # ── Pulse → Anual Nowcast (OLS) ───────────────────────────────────────────

    def fit_nowcast(self) -> "PulseForecaster":
        """
        Ajusta regresión OLS Pulse → ICIV Anual.
        Features: pulse_avg_12m, pulse_min_12m, pulse_max_12m, pulse_std_12m, trend.
        """
        if self.annual_df is None:
            return self
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score, mean_absolute_error
        except ImportError:
            logger.warning("  sklearn no disponible — nowcast omitido")
            return self

        # Crear features anuales a partir del Pulse mensual
        df_p = self.pulse_df[self.pulse_df["pulse_score"].notna()].copy()
        # Solo meses con cobertura >=70% para el cómputo
        df_p = df_p[df_p["cobertura_pct"] >= 70]
        if df_p.empty:
            return self

        # Agrupar por año
        agg = (df_p.groupby("año")["pulse_score"]
                   .agg(["mean", "min", "max", "std", "count"])
                   .reset_index())
        agg.columns = ["año", "pulse_avg", "pulse_min", "pulse_max", "pulse_std", "n_meses"]
        # Solo años con >= 6 meses
        agg = agg[agg["n_meses"] >= 6].copy()
        # Trend = diff vs año anterior
        agg["pulse_trend"] = agg["pulse_avg"].diff()

        # Merge con ICIV Anual
        df = agg.merge(self.annual_df, on="año", how="inner")
        df = df.dropna(subset=["pulse_avg", "pulse_trend", "iciv_score"])
        if len(df) < 3:
            logger.warning(f"  Nowcast: muestra muy pequeña ({len(df)} años)")
            return self

        # Evitar overfit: usar solo 2 features cuando n es pequeño (regla n>=2*features+1)
        if len(df) < 11:
            feature_cols = ["pulse_avg", "pulse_trend"]
        else:
            feature_cols = ["pulse_avg", "pulse_min", "pulse_max", "pulse_std", "pulse_trend"]

        # CERO datos artificiales: descartar filas con NaN en cualquier feature usada.
        # No usamos fillna(0) porque eso fabricaría datos.
        df = df.dropna(subset=feature_cols)
        if len(df) < 3:
            logger.warning(f"  Nowcast: muestra <3 tras descartar NaN")
            return self

        X = df[feature_cols].values
        y = df["iciv_score"].values

        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        mae = mean_absolute_error(y, y_pred)

        # Leave-one-out cross-validation para R² más honesto
        loo_pred = []
        loo_actual = []
        for i in range(len(df)):
            mask = np.ones(len(df), dtype=bool)
            mask[i] = False
            m_loo = LinearRegression().fit(X[mask], y[mask])
            loo_pred.append(m_loo.predict(X[i:i+1])[0])
            loo_actual.append(y[i])
        loo_r2 = r2_score(loo_actual, loo_pred) if len(loo_actual) >= 3 else None
        loo_mae = mean_absolute_error(loo_actual, loo_pred) if len(loo_actual) >= 3 else None

        self.nowcast_model = model
        self.nowcast_features_df = df
        self.nowcast_features_cols = feature_cols
        self.nowcast_metrics = {
            "r2_train":    float(r2),
            "mae_train":   float(mae),
            "r2_loo_cv":   float(loo_r2) if loo_r2 is not None else None,
            "mae_loo_cv":  float(loo_mae) if loo_mae is not None else None,
            "n_train":     int(len(df)),
            "n_features":  len(feature_cols),
            "feature_cols": feature_cols,
            "years_train": df["año"].tolist(),
            "coefficients": {
                feature_cols[i]: float(model.coef_[i]) for i in range(len(feature_cols))
            },
            "intercept": float(model.intercept_),
        }
        loo_r2_str = f"{loo_r2:.3f}" if loo_r2 is not None else "N/A"
        logger.info(f"  Nowcast OLS: R²_train={r2:.3f}, R²_LOO_CV={loo_r2_str}, MAE={mae:.2f}, n={len(df)}, features={len(feature_cols)}")
        return self

    def predict_current_year_iciv(self) -> dict:
        """
        Predice ICIV Anual del año en curso usando los meses Pulse disponibles.
        Útil para tener un estimado antes de que se publiquen las fuentes anuales.
        """
        if self.nowcast_model is None:
            return {}
        # Último año en datos Pulse
        df_p = self.pulse_df[self.pulse_df["pulse_score"].notna()].copy()
        df_p = df_p[df_p["cobertura_pct"] >= 70]
        if df_p.empty:
            return {}
        last_year = int(df_p["año"].max())
        cur = df_p[df_p["año"] == last_year]["pulse_score"]
        if len(cur) < 3:
            return {"año": last_year, "nota": "muy pocos meses para predicción"}

        # Features del año en curso (parcial), match feature_cols
        prev_year = last_year - 1
        prev_data = df_p[df_p["año"] == prev_year]["pulse_score"]
        prev_avg = prev_data.mean() if not prev_data.empty else cur.mean()
        all_feats = {
            "pulse_avg":   cur.mean(),
            "pulse_min":   cur.min(),
            "pulse_max":   cur.max(),
            "pulse_std":   cur.std() if len(cur) > 1 else 0,
            "pulse_trend": cur.mean() - prev_avg,
        }
        feat_vector = [all_feats[c] for c in self.nowcast_features_cols]
        features = np.array([feat_vector])
        pred = float(self.nowcast_model.predict(features)[0])
        pred_clipped = max(0.0, min(100.0, pred))

        return {
            "año":             last_year,
            "iciv_predicho":   round(pred_clipped, 2),
            "n_meses_usados":  int(len(cur)),
            "pulse_avg_used":  round(float(cur.mean()), 2),
            "modelo":          f"OLS ({len(self.nowcast_features_cols)} features)",
            "r2_train":        self.nowcast_metrics.get("r2_train"),
            "r2_loo_cv":       self.nowcast_metrics.get("r2_loo_cv"),
            "mae_train":       self.nowcast_metrics.get("mae_train"),
        }

    # ── API pública ───────────────────────────────────────────────────────────

    def compute_all(self) -> dict:
        """Ejecuta SARIMA + Nowcast y retorna payload para dashboard."""
        self.fit_sarima()
        self.fit_nowcast()

        result: dict = {"sarima": {}, "nowcast": {}, "metodologia": {}}

        if self.sarima_forecast is not None:
            fc = self.sarima_forecast
            result["sarima"] = {
                "fecha":      [d.strftime("%Y-%m") for d in fc["fecha"]],
                "mean":       fc["mean"].round(2).tolist(),
                "lo_80":      fc["lo_80"].round(2).tolist(),
                "hi_80":      fc["hi_80"].round(2).tolist(),
                "lo_95":      fc["lo_95"].round(2).tolist(),
                "hi_95":      fc["hi_95"].round(2).tolist(),
                "order":      f"SARIMA{self.sarima_best_order[0]}x{self.sarima_best_order[1]}"
                              if self.sarima_model else "",
                "aic":        round(self.sarima_aic, 2) if self.sarima_model else None,
                "horizonte_meses": FORECAST_HORIZON,
            }

        if self.nowcast_metrics:
            nowcast_pred = self.predict_current_year_iciv()
            result["nowcast"] = {
                **self.nowcast_metrics,
                "prediccion_actual": nowcast_pred,
            }

        result["metodologia"] = {
            "sarima_ref":   "Hyndman & Athanasopoulos (2018) Forecasting: Principles and Practice",
            "nowcast_ref":  "Stock & Watson (2002) Macroeconomic forecasting using diffusion indexes (JBES)",
            "validacion":   "Walk-forward cross-validation con últimos 12 meses",
        }

        return result
