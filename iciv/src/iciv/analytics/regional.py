"""
ICIV Regional — Comparación Venezuela vs. Colombia, Perú, Ecuador, Bolivia.

Calcula un ICIV "universal" usando 11 variables disponibles vía API pública
(WDI + WGI) para los 5 países andinos. Permite comparar la trayectoria del
clima de inversión venezolano en contexto regional.

Variables del ICIV Regional (11):
  D1 Macro       (30%): gdp_growth, inflation, reserves_months
  D2 Energía     (15%): electricity_kwh_pc
  D3 Institucional(25%): wgi_composite
  D4 Comercial   (20%): fdi_pct_gdp, exports_pct_gdp, unemployment_pct
  D5 Capital Hum (10%): life_expectancy, school_enrollment_sec_pct, electricity_access_pct

Nota metodológica:
  La normalización MinMax se aplica GLOBALMENTE sobre todos los países y años,
  de modo que el mismo rango sirve de referencia común. Venezuela no determina
  los extremos para las otras naciones; el mínimo/máximo global los fija.
  El ICIV Regional NO es comparable numéricamente al ICIV completo (27 vars),
  pero sí es internamente consistente para comparación relativa entre países.

Ref.: OCDE (2008) Handbook on Constructing Composite Indicators, §4 (Normalisation).
      Nardo, M. et al. (2005). "Tools for Composite Indicators Building", EUR 21682.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────

COUNTRIES = ["VEN", "COL", "PER", "ECU", "BOL"]
LABELS    = {
    "VEN": "Venezuela",
    "COL": "Colombia",
    "PER": "Perú",
    "ECU": "Ecuador",
    "BOL": "Bolivia",
}
COLORS = {
    "VEN": "#e74c3c",
    "COL": "#2ecc71",
    "PER": "#3498db",
    "ECU": "#f1c40f",
    "BOL": "#e67e22",
}

# ── Dimensiones del ICIV Regional ─────────────────────────────────────────────

DIMENSIONS_REGIONAL = {
    "D1_macro": {
        "label":  "D1 Macro",
        "weight": 0.30,
        "vars": {
            "gdp_growth_pct":        {"weight": 0.38, "direction": "positive"},
            "inflation_cpi_pct":     {"weight": 0.37, "direction": "negative"},
            "reserves_months_imports":{"weight": 0.25, "direction": "positive"},
        },
    },
    "D2_energia": {
        "label":  "D2 Energía",
        "weight": 0.15,
        "vars": {
            "electricity_kwh_pc": {"weight": 1.00, "direction": "positive"},
        },
    },
    "D3_institucional": {
        "label":  "D3 Institucional",
        "weight": 0.25,
        "vars": {
            "wgi_composite": {"weight": 1.00, "direction": "positive"},
        },
    },
    "D4_comercial": {
        "label":  "D4 Comercial",
        "weight": 0.20,
        "vars": {
            "fdi_pct_gdp":      {"weight": 0.40, "direction": "positive"},
            "exports_pct_gdp":  {"weight": 0.35, "direction": "positive"},
            "unemployment_pct": {"weight": 0.25, "direction": "negative"},
        },
    },
    "D5_capital_humano": {
        "label":  "D5 Capital Humano",
        "weight": 0.10,
        "vars": {
            "life_expectancy":            {"weight": 0.40, "direction": "positive"},
            "school_enrollment_sec_pct":  {"weight": 0.30, "direction": "positive"},
            "electricity_access_pct":     {"weight": 0.30, "direction": "positive"},
        },
    },
}

ALL_VARS = [
    v for dim in DIMENSIONS_REGIONAL.values() for v in dim["vars"]
]


class RegionalComparison:
    """
    Computa el ICIV Regional para Venezuela y 4 países latinoamericanos.

    Args:
        data_path: Path a la carpeta data/raw/regional/ con los CSVs.
    """

    def __init__(self, data_path: Path) -> None:
        self._path = data_path

    # ─────────────────────────────────────────────────────────────────────────
    # API pública
    # ─────────────────────────────────────────────────────────────────────────

    def compute_all(self) -> dict:
        """Retorna dict completo para el dashboard."""
        master = self._load_data()
        if master.empty:
            return {"error": "Datos regionales no disponibles. Ejecute scripts/fetch_regional.py"}

        master_norm = self._normalize(master)
        scores      = self._compute_scores(master_norm)

        if scores.empty:
            return {"error": "No se pudo calcular el ICIV regional."}

        return self._build_output(scores)

    # ─────────────────────────────────────────────────────────────────────────
    # Carga y preprocesamiento
    # ─────────────────────────────────────────────────────────────────────────

    def _load_data(self) -> pd.DataFrame:
        """Carga WDI + WGI regional y combina en un DataFrame master."""
        wdi_path = self._path / "wdi_regional.csv"
        wgi_path = self._path / "wgi_regional.csv"

        if not wdi_path.exists():
            logger.warning("  WARN wdi_regional.csv no encontrado en %s", self._path)
            return pd.DataFrame()

        df_wdi = pd.read_csv(wdi_path, encoding="utf-8-sig")
        df_wdi["año"] = df_wdi["año"].astype(int)
        df_wdi["pais_iso3"] = df_wdi["pais_iso3"].str.upper()

        if wgi_path.exists():
            df_wgi = pd.read_csv(wgi_path, encoding="utf-8-sig")
            df_wgi["año"] = df_wgi["año"].astype(int)
            df_wgi["pais_iso3"] = df_wgi["pais_iso3"].str.upper()
            df = df_wdi.merge(df_wgi, on=["pais_iso3", "año"], how="outer")
        else:
            df = df_wdi

        # Filtrar solo los países deseados y años 2000-2024
        df = df[df["pais_iso3"].isin(COUNTRIES)]
        df = df[(df["año"] >= 2000) & (df["año"] <= 2024)]

        return df.sort_values(["pais_iso3", "año"]).reset_index(drop=True)

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza Min-Max globalmente (todos los países juntos como referencia).
        Variables negativas se invierten: score = 100 - normalized.
        """
        df_norm = df[["pais_iso3", "año"]].copy()
        for var in ALL_VARS:
            if var not in df.columns:
                df_norm[var] = np.nan
                continue

            series = df[var]
            v_min  = series.min()
            v_max  = series.max()

            if v_max == v_min or pd.isna(v_min):
                df_norm[var] = 50.0
                continue

            direction = self._get_direction(var)
            normalized = (series - v_min) / (v_max - v_min) * 100.0
            if direction == "negative":
                normalized = 100.0 - normalized

            df_norm[var] = normalized.round(2)

        return df_norm

    def _compute_scores(self, df_norm: pd.DataFrame) -> pd.DataFrame:
        """Calcula scores por dimensión e ICIV total para cada país/año."""
        rows = []
        for _, row in df_norm.iterrows():
            pais = row["pais_iso3"]
            año  = int(row["año"])
            dim_scores: dict[str, float | None] = {}

            for dim_id, dim_cfg in DIMENSIONS_REGIONAL.items():
                w_vars   = dim_cfg["vars"]
                vals, ws = [], []
                for var, vcfg in w_vars.items():
                    val = row.get(var)
                    if val is not None and not pd.isna(val):
                        vals.append(float(val))
                        ws.append(vcfg["weight"])

                if not vals:
                    dim_scores[dim_id] = None
                    continue

                # Renormalizar pesos si faltan variables
                total_w = sum(ws)
                dim_score = sum(v * w / total_w for v, w in zip(vals, ws))
                dim_scores[dim_id] = round(dim_score, 2)

            # ICIV Regional = promedio ponderado de dimensiones disponibles
            dim_weights = [DIMENSIONS_REGIONAL[d]["weight"] for d in dim_scores if dim_scores[d] is not None]
            dim_vals    = [dim_scores[d] for d in dim_scores if dim_scores[d] is not None]
            if not dim_vals:
                continue
            total_dw = sum(dim_weights)
            iciv = sum(v * w / total_dw for v, w in zip(dim_vals, dim_weights))

            rows.append({
                "pais_iso3": pais,
                "año":       año,
                "iciv_regional": round(iciv, 2),
                **{k: v for k, v in dim_scores.items()},
            })

        return pd.DataFrame(rows)

    # ─────────────────────────────────────────────────────────────────────────
    # Construcción del output
    # ─────────────────────────────────────────────────────────────────────────

    def _build_output(self, scores: pd.DataFrame) -> dict:
        """Construye el dict final para el dashboard."""
        años_all  = sorted(scores["año"].unique().tolist())

        # Series temporales por país
        series: dict[str, list] = {}
        for pais in COUNTRIES:
            df_p = scores[scores["pais_iso3"] == pais].sort_values("año")
            # Crear serie completa, None donde falta data
            vals: list[float | None] = []
            for yr in años_all:
                row = df_p[df_p["año"] == yr]
                vals.append(round(float(row["iciv_regional"].values[0]), 2) if len(row) else None)
            series[pais] = vals

        # Año más reciente con datos para todos los países
        año_actual = max(
            yr for yr in años_all
            if all(scores[(scores["pais_iso3"] == p) & (scores["año"] == yr)]["iciv_regional"].notna().any()
                   for p in COUNTRIES)
        ) if años_all else años_all[-1]

        # Scores actuales y ranking
        actual: dict[str, dict] = {}
        scores_latest = []
        for pais in COUNTRIES:
            row = scores[(scores["pais_iso3"] == pais) & (scores["año"] == año_actual)]
            if row.empty:
                continue
            sc = float(row["iciv_regional"].values[0])
            scores_latest.append((pais, sc))

        scores_latest.sort(key=lambda x: x[1], reverse=True)
        for rank, (pais, sc) in enumerate(scores_latest, 1):
            # Tendencia 5 años
            row5y = scores[(scores["pais_iso3"] == pais) & (scores["año"] == año_actual - 5)]
            sc_5y = float(row5y["iciv_regional"].values[0]) if not row5y.empty else sc
            delta5 = round(sc - sc_5y, 1)

            # Scores por dimensión (año actual)
            row_full = scores[(scores["pais_iso3"] == pais) & (scores["año"] == año_actual)]
            dims: dict[str, float | None] = {}
            for dim_id in DIMENSIONS_REGIONAL:
                val = row_full[dim_id].values[0] if dim_id in row_full.columns else None
                dims[dim_id] = round(float(val), 1) if val is not None and not pd.isna(val) else None

            actual[pais] = {
                "score":     round(sc, 1),
                "rank":      rank,
                "delta5y":   delta5,
                "dims":      dims,
            }

        # Radar: scores de dimensión por país (año actual)
        dim_labels = [DIMENSIONS_REGIONAL[d]["label"] for d in DIMENSIONS_REGIONAL]
        radar: dict[str, list] = {}
        for pais in COUNTRIES:
            row = scores[(scores["pais_iso3"] == pais) & (scores["año"] == año_actual)]
            vals_radar: list[float | None] = []
            for dim_id in DIMENSIONS_REGIONAL:
                if row.empty or dim_id not in row.columns:
                    vals_radar.append(None)
                else:
                    v = row[dim_id].values[0]
                    vals_radar.append(round(float(v), 1) if not pd.isna(v) else None)
            radar[pais] = vals_radar

        # Brecha VEN vs promedio regional por año
        brecha: list[float | None] = []
        for i, yr in enumerate(años_all):
            ven_val = series["VEN"][i]
            otros = [series[p][i] for p in COUNTRIES if p != "VEN" and series[p][i] is not None]
            if ven_val is not None and otros:
                brecha.append(round(ven_val - (sum(otros) / len(otros)), 1))
            else:
                brecha.append(None)

        año_peor_brecha = None
        brechas_reales = [(yr, b) for yr, b in zip(años_all, brecha) if b is not None]
        if brechas_reales:
            año_peor_brecha = min(brechas_reales, key=lambda x: x[1])[0]

        return {
            "paises":          COUNTRIES,
            "etiquetas":       {p: LABELS[p] for p in COUNTRIES},
            "colores":         {p: COLORS[p] for p in COUNTRIES},
            "años":            años_all,
            "año_actual":      año_actual,
            "series":          series,
            "actual":          actual,
            "radar":           {"dimensiones": dim_labels, **radar},
            "brecha_ven_region": brecha,
            "año_peor_brecha": año_peor_brecha,
            "n_variables":     len(ALL_VARS),
            "n_dimensiones":   len(DIMENSIONS_REGIONAL),
            "metodologia": (
                f"ICIV Regional: {len(ALL_VARS)} variables universales (WDI + WGI), "
                f"{len(DIMENSIONS_REGIONAL)} dimensiones. "
                "Normalización MinMax global (todos los países como referencia). "
                "Nota: no es directamente comparable al ICIV completo (27 vars). "
                "Ref.: OCDE Handbook on Composite Indicators (2008), §4."
            ),
            "nota_variables": (
                f"Usa {len(ALL_VARS)} variables comunes (WDI + WGI API) "
                "vs 27 variables del ICIV Venezuela completo. "
                "No incluye: producción petróleo/gas, sanciones OFAC, Google Trends, "
                "datos Guardian, Freedom House ni VIIRS (Venezuela-específicos)."
            ),
        }

    @staticmethod
    def _get_direction(var: str) -> str:
        negative_vars = {
            "inflation_cpi_pct",
            "unemployment_pct",
        }
        return "negative" if var in negative_vars else "positive"
