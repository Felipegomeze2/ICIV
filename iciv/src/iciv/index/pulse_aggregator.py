"""
PulseAggregator — ICIV Pulse Mensual.

Co-indicador de alta frecuencia que captura los movimientos mensuales del clima
de inversión usando solo las variables disponibles con granularidad ≥mensual.

NO reemplaza el ICIV Anual oficial — es un nowcasting indicator
(Stock & Watson, 2002; Aruoba, Diebold & Scotti, 2009).

Variables incluidas (15, todas de fuentes internacionales, ninguna de
origen venezolano):
  Macro externo (D1 — 35% peso renormalizado):
    - wti_precio_usd            (FRED, mensual)
    - brent_precio_usd          (FRED, mensual)
    - crudo_dubai_usd           (WB Pink Sheet, mensual — benchmark mediano-pesado)
    - tasa_fed_funds_pct        (FRED, mensual)
    - usd_index_broad           (FRED, mensual)
    - vix_volatility            (FRED, mensual)
    - ust_10y_yield_pct         (FRED, mensual)
    - em_bond_spread_pct        (FRED BAMLEMCBPIOAS, mensual — estrés financiero EM)
  Energía Venezuela (D2 — 25% peso renormalizado):
    - petroleo_liquidos_totales_tbpd (EIA International, mensual)
  Actividad comercial espejo (10%):
    - importaciones_espejo_usa_musd (IMF IMTS, reportado por EEUU, mensual)
    - exportaciones_espejo_usa_musd (IMF IMTS, reportado por EEUU, mensual)
  Percepción (D6 — 30%):
    - guardian_articulos_venezuela (Guardian, mensual)
    - guardian_tono_titulares      (Guardian, mensual)
    - gdelt_cobertura_vol          (GDELT DOC timeline, mensual)
    - gdelt_tono_noticias          (GDELT DOC timeline, mensual)

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
# Ampliado 2026-07: comercio espejo IMTS (actividad real), crudo Dubai
# (benchmark mediano-pesado, mas cercano al Merey que WTI/Brent) y spread
# EM (condicion financiera para emergentes). Todas fuentes internacionales;
# ninguna de origen venezolano.
PULSE_WEIGHTS: dict[str, float] = {
    # D1 Macro externo (35%) — drivers globales de precio y financiamiento
    "wti_precio_usd":                  0.065,
    "brent_precio_usd":                0.040,
    "crudo_dubai_usd":                 0.040,  # POSITIVO (WB Pink Sheet)
    "tasa_fed_funds_pct":              0.040,  # NEGATIVO (tasa alta → menos IED EM)
    "usd_index_broad":                 0.035,  # NEGATIVO (USD fuerte → presión EM)
    "vix_volatility":                  0.060,  # NEGATIVO (volatilidad alta → riesgo)
    "ust_10y_yield_pct":               0.030,  # NEGATIVO (yield alto → outflow EM)
    "em_bond_spread_pct":              0.040,  # NEGATIVO (spread alto → estrés EM)
    # D2 Energía VEN (25%) — driver doméstico clave
    "petroleo_liquidos_totales_tbpd":  0.250,
    # D4 Comercio espejo EEUU-VEN (10%) — aduana de EEUU vía FRED.
    # Sustituye a IMF IMTS desde 2026-08-11: mismo concepto (comercio real
    # observado por el socio) con 2 meses de rezago en vez de 4, volumen físico
    # en vez de valor declarado, y 395 meses de historia. Ver METODOLOGIA §3.3.
    "importaciones_eeuu_crudo_ven_tbpd":     0.050,  # POSITIVO (flujo exportador VEN)
    "importaciones_eeuu_productos_ven_tbpd": 0.050,  # POSITIVO (actividad refinadora)
    # D6 Percepción internacional (30%) — dos sistemas de cobertura
    "guardian_articulos_venezuela":    0.065,  # NEGATIVO (más cobertura → crisis)
    "guardian_tono_titulares":         0.100,  # POSITIVO (tono positivo es bueno)
    "gdelt_cobertura_vol":             0.055,  # NEGATIVO
    "gdelt_tono_noticias":             0.080,  # POSITIVO
}

# Variables con dirección negativa (mayor valor = peor clima)
PULSE_NEGATIVE = {
    "tasa_fed_funds_pct", "usd_index_broad", "vix_volatility",
    "ust_10y_yield_pct", "em_bond_spread_pct",
    "guardian_articulos_venezuela", "gdelt_cobertura_vol",
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
            "eia_monthly.csv":            "EIA International monthly",
            "fred_monthly.csv":           "FRED monthly aggregation",
            "guardian_monthly.csv":       "Guardian monthly + VADER",
            "gdelt_monthly.csv":          "GDELT DOC timeline monthly",
            "imts_monthly.csv":           "IMF IMTS mirror trade (EEUU-VEN)",
            "wb_commodities_monthly.csv": "WB Pink Sheet crude Dubai",
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
                    df["variable"] = "petroleo_liquidos_totales_tbpd"
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

        return wide

    # ── Normalización ─────────────────────────────────────────────────────────

    def normalize(self, df_wide: pd.DataFrame) -> pd.DataFrame:
        """Min-max expansivo hasta cada fecha, sin usar observaciones futuras.

        Una serie sin rango aún no tiene escala identificable: permanece NaN.
        Los faltantes originales nunca se convierten en puntajes. Esta propiedad
        no elimina revisiones de las fuentes: la evaluación es de último vintage.
        """
        result = df_wide.sort_values("fecha").copy()
        self.df_raw_wide = result.copy()
        for var in PULSE_WEIGHTS.keys():
            if var not in result.columns:
                continue
            series = pd.to_numeric(result[var], errors="coerce").replace([np.inf, -np.inf], np.nan)
            v_min = series.expanding(min_periods=2).min()
            v_max = series.expanding(min_periods=2).max()
            rng = v_max - v_min
            rng = rng.where(rng > 0)
            if var in PULSE_NEGATIVE:
                result[var] = (v_max - series) / rng * 100.0
            else:
                result[var] = (series - v_min) / rng * 100.0
            result[var] = result[var].clip(0, 100)
            if series.notna().any():
                self.min_max_params[var] = (float(series.min()), float(series.max()))
        self.df_normalized = result
        return result

    # ── Agregación ────────────────────────────────────────────────────────────

    def aggregate(self, df_norm: pd.DataFrame, as_of: str | pd.Timestamp | None = None) -> pd.DataFrame:
        """
        ICIV Pulse = Σ (peso_i × variable_norm_i) con redistribución de pesos
        cuando algunas variables están NaN ese mes.
        """
        rows: list[dict] = []
        now = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.now(tz="UTC").tz_localize(None)
        current_month = now.to_period("M").start_time
        fixed_weight = sum(PULSE_WEIGHTS.values())
        raw = getattr(self, "df_raw_wide", df_norm).set_index("fecha")
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
            raw_row = raw.loc[row["fecha"]] if row["fecha"] in raw.index else row
            available_weight = sum(w for var, w in PULSE_WEIGHTS.items() if pd.notna(raw_row.get(var)))
            domestic_present = pd.notna(row.get("petroleo_liquidos_totales_tbpd"))
            closed = pd.Timestamp(row["fecha"]) < current_month
            eligible = total_weight / fixed_weight >= 0.70 - 1e-10 and domestic_present and closed
            rows.append({
                "año":           int(row["año"]),
                "mes":           int(row["mes"]),
                "fecha":         row["fecha"],
                "pulse_score":   round(pulse_score, 2) if pulse_score is not None else None,
                "cobertura_pct": round(total_weight / fixed_weight * 100.0, 1),
                "disponibilidad_pct": round(available_weight / fixed_weight * 100.0, 1),
                "n_vars":        n_vars_disponibles,
                "n_vars_total": len(PULSE_WEIGHTS),
                "produccion_disponible": bool(domestic_present),
                "mes_cerrado": bool(closed),
                "elegible_modelo": bool(eligible),
                "estado": "utilizable" if eligible else "provisional",
            })
        df_pulse = pd.DataFrame(rows)
        if not df_pulse.empty:
            norm_by_date = df_norm.set_index("fecha")
            score_by_date = df_pulse.set_index("fecha")["pulse_score"]
            for lag in (1, 3):
                decompositions = []
                for _, row in df_pulse.iterrows():
                    date = pd.Timestamp(row["fecha"])
                    previous_date = date - pd.DateOffset(months=lag)
                    item = {f"delta_{lag}m": np.nan, f"delta_comparable_{lag}m": np.nan,
                            f"efecto_composicion_{lag}m": np.nan, f"cobertura_comun_{lag}m_pct": 0.0,
                            f"composicion_estable_{lag}m": False}
                    if previous_date in norm_by_date.index:
                        current, previous = norm_by_date.loc[date], norm_by_date.loc[previous_date]
                        current_vars = {v for v in PULSE_WEIGHTS if pd.notna(current.get(v))}
                        previous_vars = {v for v in PULSE_WEIGHTS if pd.notna(previous.get(v))}
                        common = current_vars & previous_vars
                        common_weight = sum(PULSE_WEIGHTS[v] for v in common)
                        item[f"cobertura_comun_{lag}m_pct"] = round(common_weight / fixed_weight * 100, 1)
                        item[f"composicion_estable_{lag}m"] = current_vars == previous_vars
                        if common_weight >= 0.3 and pd.notna(row["pulse_score"]) and pd.notna(score_by_date.loc[previous_date]):
                            observed = float(row["pulse_score"] - score_by_date.loc[previous_date])
                            comparable = sum(PULSE_WEIGHTS[v] * (current[v] - previous[v]) for v in common) / common_weight
                            item[f"delta_{lag}m"] = round(observed, 4)
                            item[f"delta_comparable_{lag}m"] = round(float(comparable), 4)
                            item[f"efecto_composicion_{lag}m"] = round(float(observed - comparable), 4)
                    decompositions.append(item)
                df_pulse = pd.concat([df_pulse, pd.DataFrame(decompositions)], axis=1)
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
