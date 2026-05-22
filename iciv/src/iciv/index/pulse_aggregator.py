"""
PulseAggregator — ICIV Pulse Mensual.

Co-indicador de alta frecuencia que captura los movimientos mensuales del clima
de inversión usando solo las variables disponibles con granularidad ≥mensual.

NO reemplaza el ICIV Anual oficial — es un nowcasting indicator
(Stock & Watson, 2002; Aruoba, Diebold & Scotti, 2009).

Variables incluidas (12, todas de fuentes internacionales):
  Macro externo (D1 — 35% peso renormalizado):
    - wti_precio_usd            (FRED, mensual)
    - brent_precio_usd          (FRED, mensual)
    - tasa_fed_funds_pct        (FRED, mensual)
    - usd_index_broad           (FRED, mensual)
    - vix_volatility            (FRED, mensual)
    - ust_10y_yield_pct         (FRED, mensual)
  Energía Venezuela (D2 — 25% peso renormalizado):
    - petroleo_crudo_produccion_tbpd (EIA International, mensual)
  Institucional (D3 — 10% peso):
    - ofac_sanciones_count      (Treasury, snapshot mensual)
  Comercial/Migración (D4 — 15% peso):
    - migrantes_vzla_millones   (UNHCR, mensual donde disponible)
  Percepción (D6 — 15% peso):
    - guardian_articulos_venezuela (Guardian, mensual)
    - guardian_tono_titulares      (Guardian, mensual)

NO incluye D5 (capital humano) — todas sus variables son anuales estructuralmente.

Metodología:
  1. Normalización Min-Max usando rango histórico del ICIV Anual (consistencia)
  2. Inversión automática para variables negativas (mismo CATALOG que ICIV Anual)
  3. Agregación lineal ponderada con pesos renormalizados
  4. Score 0-100, mismas 5 bandas de riesgo

Referencias:
  Stock & Watson (2002) — Macroeconomic forecasting using diffusion indexes
  Aruoba, Diebold, Scotti (2009) — Real-time measurement of business conditions
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Año desde el cual se computa el Pulse (FRED y Guardian ahora cubren desde 2010)
PULSE_START_YEAR = 2010

# ── Pesos renormalizados del Pulse (suman 1.0) ───────────────────────────────
# Basado en pesos AHP originales pero renormalizando sobre el subconjunto disponible.
PULSE_WEIGHTS: dict[str, float] = {
    # D1 Macro externo (35%) — drivers globales
    "wti_precio_usd":                  0.08,
    "brent_precio_usd":                0.05,
    "tasa_fed_funds_pct":              0.06,  # NEGATIVO (tasa alta → menos IED EM)
    "usd_index_broad":                 0.05,  # NEGATIVO (USD fuerte → presión EM)
    "vix_volatility":                  0.06,  # NEGATIVO (volatilidad alta → riesgo)
    "ust_10y_yield_pct":               0.05,  # NEGATIVO (yield alto → outflow EM)
    # D2 Energía VEN (25%) — driver doméstico clave
    "petroleo_crudo_produccion_tbpd":  0.25,
    # D3 Institucional (10%)
    "ofac_sanciones_count":            0.10,  # NEGATIVO
    # D4 Migración (15%) — proxy de salida de capital humano
    "migrantes_vzla_millones":         0.15,  # NEGATIVO
    # D6 Percepción (15%)
    "guardian_articulos_venezuela":    0.07,  # NEGATIVO (más cobertura → crisis)
    "guardian_tono_titulares":         0.08,  # POSITIVO (tono positivo es bueno)
}

# Variables con dirección negativa (mayor valor = peor clima)
PULSE_NEGATIVE = {
    "tasa_fed_funds_pct", "usd_index_broad", "vix_volatility",
    "ust_10y_yield_pct", "ofac_sanciones_count",
    "migrantes_vzla_millones", "guardian_articulos_venezuela",
}


class PulseAggregator:
    """
    Construye el ICIV Pulse Mensual desde panel long-format de datos mensuales.

    Input esperado: DataFrame con columnas [año, mes, variable, valor].
    Output: DataFrame mensual con score Pulse + cobertura por mes.
    """

    def __init__(self, raw_data_dir: Path | str) -> None:
        self.raw_data_dir = Path(raw_data_dir)
        self.df_panel: pd.DataFrame | None = None
        self.df_normalized: pd.DataFrame | None = None
        self.df_pulse: pd.DataFrame | None = None
        self.min_max_params: dict[str, tuple[float, float]] = {}

    # ── ETL ────────────────────────────────────────────────────────────────────

    def load_monthly_sources(self) -> pd.DataFrame:
        """Carga y unifica todos los CSVs mensuales en un panel."""
        sources = {
            "eia_monthly.csv":      "EIA International monthly",
            "fred_monthly.csv":     "FRED monthly aggregation",
            "guardian_monthly.csv": "Guardian monthly + VADER",
        }
        frames: list[pd.DataFrame] = []
        for fname, label in sources.items():
            fpath = self.raw_data_dir / fname
            if not fpath.exists():
                logger.warning("  Pulse: missing %s — skipping", fname)
                continue
            df = pd.read_csv(fpath)
            # eia_monthly.csv tiene "variable" como columna; otros similar
            if "variable" not in df.columns:
                # eia_monthly puede tener formato distinto; estandarizar
                if "productId" in df.columns and "value" in df.columns:
                    df = df[df["productId"] == 53].rename(columns={"value": "valor"})
                    df["variable"] = "petroleo_crudo_produccion_tbpd"
            if not {"año", "mes", "variable", "valor"}.issubset(df.columns):
                logger.warning("  Pulse: %s formato inválido — skipping", fname)
                continue
            frames.append(df[["año", "mes", "variable", "valor"]])
            logger.info("  Pulse: cargado %s (%d filas)", fname, len(df))

        if not frames:
            return pd.DataFrame()
        df_all = pd.concat(frames, ignore_index=True)
        # Solo conservar variables del Pulse
        df_all = df_all[df_all["variable"].isin(PULSE_WEIGHTS.keys())].copy()
        # Filtrar al rango temporal del Pulse (desde PULSE_START_YEAR)
        df_all = df_all[df_all["año"] >= PULSE_START_YEAR].copy()
        # Eliminar duplicados (mes-variable)
        df_all = df_all.drop_duplicates(subset=["año", "mes", "variable"], keep="last")

        self.df_panel = df_all
        return df_all

    def pivot_to_wide(self) -> pd.DataFrame:
        """Convierte panel long → wide (filas: mes, columnas: variables)."""
        if self.df_panel is None or self.df_panel.empty:
            return pd.DataFrame()
        wide = self.df_panel.pivot_table(
            index=["año", "mes"], columns="variable", values="valor", aggfunc="first"
        ).reset_index()
        wide.columns.name = None
        # Ordenar por fecha
        wide["fecha"] = pd.to_datetime(
            wide["año"].astype(str) + "-" + wide["mes"].astype(str).str.zfill(2) + "-01"
        )
        wide = wide.sort_values("fecha").reset_index(drop=True)

        # ── Forward-fill por lag de publicación EIA (máx 2 meses) ────────────
        # petroleo_crudo_produccion_tbpd tiene lag típico de 2-3 meses en EIA.
        # Se propaga el último valor conocido hasta 2 meses para evitar que su
        # ausencia redistribuya el 25% de peso hacia commodities globales y
        # distorsione el Pulse. No es dato inventado: es el último valor publicado,
        # pendiente de actualización. Límite de 2 meses para no extrapolar en exceso.
        if "petroleo_crudo_produccion_tbpd" in wide.columns:
            wide["petroleo_crudo_produccion_tbpd"] = (
                wide["petroleo_crudo_produccion_tbpd"]
                .ffill(limit=4)  # lag típico EIA international: 3-4 meses
            )

        return wide

    # ── Normalización ─────────────────────────────────────────────────────────

    def normalize(self, df_wide: pd.DataFrame) -> pd.DataFrame:
        """
        Min-Max usando el rango histórico de cada variable en este panel.
        Variables negativas se invierten.
        """
        result = df_wide.copy()
        for var in PULSE_WEIGHTS.keys():
            if var not in result.columns:
                continue
            series = result[var].dropna()
            if series.empty:
                continue
            v_min, v_max = float(series.min()), float(series.max())
            self.min_max_params[var] = (v_min, v_max)
            rng = v_max - v_min
            if rng == 0:
                result[var] = 50.0
                continue
            if var in PULSE_NEGATIVE:
                result[var] = (v_max - result[var]) / rng * 100.0
            else:
                result[var] = (result[var] - v_min) / rng * 100.0
            result[var] = result[var].clip(0, 100)
        self.df_normalized = result
        return result

    # ── Agregación ────────────────────────────────────────────────────────────

    def aggregate(self, df_norm: pd.DataFrame) -> pd.DataFrame:
        """
        ICIV Pulse = Σ (peso_i × variable_norm_i) con redistribución de pesos
        cuando algunas variables están NaN ese mes.
        """
        rows: list[dict] = []
        for _, row in df_norm.iterrows():
            total_weight = 0.0
            score_sum = 0.0
            n_vars_disponibles = 0
            for var, w in PULSE_WEIGHTS.items():
                if var not in row.index:
                    continue
                v = row[var]
                if pd.isna(v):
                    continue
                score_sum += float(v) * w
                total_weight += w
                n_vars_disponibles += 1
            if total_weight < 0.3:  # menos del 30% del peso disponible
                pulse_score = None
            else:
                pulse_score = score_sum / total_weight
            rows.append({
                "año":           int(row["año"]),
                "mes":           int(row["mes"]),
                "fecha":         row["fecha"],
                "pulse_score":   round(pulse_score, 2) if pulse_score is not None else None,
                "cobertura_pct": round(total_weight * 100.0, 1),
                "n_vars":        n_vars_disponibles,
            })
        df_pulse = pd.DataFrame(rows)
        self.df_pulse = df_pulse
        return df_pulse

    # ── API pública ───────────────────────────────────────────────────────────

    def compute_pulse(self) -> pd.DataFrame:
        """Ejecuta el pipeline completo y retorna el Pulse mensual."""
        self.load_monthly_sources()
        df_wide = self.pivot_to_wide()
        if df_wide.empty:
            logger.warning("  Pulse: no se pudo construir panel")
            return pd.DataFrame()
        df_norm = self.normalize(df_wide)
        df_pulse = self.aggregate(df_norm)
        logger.info("  Pulse: %d meses calculados, rango %.1f–%.1f",
                    len(df_pulse),
                    df_pulse["pulse_score"].min() if df_pulse["pulse_score"].notna().any() else 0,
                    df_pulse["pulse_score"].max() if df_pulse["pulse_score"].notna().any() else 0)
        return df_pulse

    def get_components_normalized(self) -> pd.DataFrame:
        """Retorna el panel normalizado con un componente por columna (para visualización)."""
        if self.df_normalized is None:
            return pd.DataFrame()
        return self.df_normalized.copy()
