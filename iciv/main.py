"""
ICIV -- Orquestador Principal
=============================
Ejecuta el pipeline completo del Indicador de Clima de Inversión Venezuela:

  Fase 1 -- Descarga de datos (todas las fuentes)
  Fase 2 -- Limpieza y normalización
  Fase 3 -- Cálculo del ICIV (pesos fijos + AHP)
  Fase 4 -- Generación del dashboard HTML interactivo
  Fase 5 -- Apertura automática del dashboard en el navegador

Uso:
    python main.py            # Ejecuta todo (fetch + pipeline + dashboard)
    python main.py --no-fetch # Salta descarga (usa datos existentes en data/raw/)
    python main.py --no-open  # No abre el navegador al terminar
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
import webbrowser
from pathlib import Path
from datetime import datetime

# -- Asegurar que src/ está en el path -----------------------------------------
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT / "src"))

import json

import numpy as np
import pandas as pd


class _NumpyEncoder(json.JSONEncoder):
    """Serializa tipos numpy (bool_, int_, float_) a Python nativos."""
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

from iciv.config import Settings
from iciv.data.loaders import ALL_LOADERS
from iciv.data.catalog import CATALOG
from iciv.processing.pipeline import Pipeline
from iciv.processing.transformers.cleaner import DataCleaner
from iciv.processing.transformers.normalizer import MinMaxNormalizer
from iciv.index.aggregator import ICIVAggregator
from iciv.index.weighting import AHPWeights, FixedWeights
from iciv.index.dimensions import DIMENSIONS

# -- Logging -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# -- Colores del ICIV ----------------------------------------------------------
RISK_COLORS = {
    "Alto Riesgo":          "#e74c3c",
    "Riesgo Moderado-Alto": "#e67e22",
    "Riesgo Moderado":      "#f1c40f",
    "Bajo Riesgo":          "#2ecc71",
    "Muy Bajo Riesgo":      "#27ae60",
}
DIM_COLORS = ["#3498db", "#e67e22", "#9b59b6", "#1abc9c", "#e74c3c", "#f39c12"]


# =============================================================================
# FASE 1 -- DESCARGA DE DATOS
# =============================================================================

def fase_fetch(settings: Settings) -> None:
    logger.info("\n" + "-" * 60)
    logger.info("  FASE 1 -- Descarga de datos (2000-%s)", settings.series.end_year)
    logger.info("-" * 60)

    # Importar y ejecutar cada fetch function directamente
    fetch_scripts = [
        # ── Fuentes originales ────────────────────────────────────────────────
        ("WDI  -- Banco Mundial (macro/social)",  "scripts.fetch_wdi",           "fetch_wdi"),
        ("IMF  -- Fondo Monetario Internacional", "scripts.fetch_imf",           "fetch_imf"),
        ("WGI  -- Gobernanza (Banco Mundial)",    "scripts.fetch_wgi",           "fetch_wgi"),
        ("EIA  -- Energía (petróleo/gas/elec)",   "scripts.fetch_eia",           "fetch_eia"),
        ("EIA Monthly -- Petróleo nowcast VEN",   "scripts.fetch_eia_monthly",   "fetch_eia_monthly"),
        ("FRED Monthly -- WTI/Brent/Fed/VIX...",   "scripts.fetch_fred_monthly",  "fetch_fred_monthly"),
        ("Guardian Monthly -- VADER mensual",      "scripts.fetch_guardian_monthly", "fetch_guardian_monthly"),
        ("GDELT Monthly -- tono/cobertura global", "scripts.fetch_gdelt_monthly", "fetch_gdelt_monthly"),
        ("IMF IMTS -- comercio espejo EEUU-VEN",   "scripts.fetch_imts_monthly",  "fetch_imts_monthly"),
        ("WB Pink Sheet -- crudo Dubai mensual",   "scripts.fetch_wb_commodities_monthly", "fetch_wb_commodities_monthly"),
        ("Noticias internacionales -- RSS filtrado", "scripts.fetch_international_news", "fetch_international_news"),
        ("Guardian -- Percepción mediática",      "scripts.fetch_guardian",      "fetch_guardian"),
        ("FRED -- WTI + Fed Funds (St. Louis)",   "scripts.fetch_fred",          "fetch_fred"),
        ("Freedom House -- Libertades políticas", "scripts.fetch_freedom_house", "fetch_freedom_house"),
        ("UNHCR/R4V -- Migración venezolana",     "scripts.fetch_unhcr",         "build_unhcr"),
        ("VIIRS/DMSP   -- Luminosidad nocturna",  "scripts.fetch_viirs",         "build_viirs"),
        ("UNCTAD LSCI -- Conectividad marítima",  "scripts.fetch_unctad",        "fetch_unctad"),
        ("VIIRS NTL   -- Luminosidad por estado",  "scripts.fetch_viirs_states",  "build_viirs_states"),
        ("PTS -- Terror Político (Gibney et al.)", "scripts.fetch_pts",           "fetch_pts"),
        ("WHO GHO -- Salud (esperanza/mortalidad)","scripts.fetch_who",           "fetch_who"),
        # ── Fuentes ampliadas (mayo 2026) ─────────────────────────────────────
        ("WJP -- Rule of Law Index",              "scripts.fetch_wjp",           "fetch_wjp"),
        ("ILOSTAT -- Empleo informal (ILO)",      "scripts.fetch_ilostat",       "fetch_ilostat"),
    ]

    for label, module_path, func_name in fetch_scripts:
        logger.info("\n  [->] %s", label)
        try:
            import importlib
            mod = importlib.import_module(module_path)
            fetch_fn = getattr(mod, func_name)
            df = fetch_fn()
            # Guardar usando el path estándar del módulo
            output_map = {
                "fetch_wdi":           settings.paths.raw_wdi,
                "fetch_imf":           settings.paths.raw_imf,
                "fetch_wgi":           settings.paths.raw_wgi,
                "fetch_eia":           settings.paths.raw_eia,
                "fetch_eia_monthly":   settings.paths.raw_eia_monthly,
                "fetch_fred_monthly":  settings.paths.raw_fred_monthly,
                "fetch_guardian_monthly": settings.paths.raw_guardian_monthly,
                "fetch_gdelt_monthly": settings.paths.raw_gdelt_monthly,
                "fetch_imts_monthly":  settings.paths.data_raw / "imts_monthly.csv",
                "fetch_wb_commodities_monthly": settings.paths.data_raw / "wb_commodities_monthly.csv",
                "fetch_international_news": settings.paths.raw_international_news,
                "fetch_guardian":      settings.paths.raw_guardian,
                "fetch_fred":          settings.paths.raw_fred,
                "fetch_freedom_house": settings.paths.raw_freedom_house,
                "build_unhcr":         settings.paths.raw_unhcr,
                "build_viirs":         settings.paths.raw_viirs,
                "fetch_unctad":        settings.paths.raw_unctad,
                "build_viirs_states":  settings.paths.raw_viirs_states,
                "fetch_pts":           settings.paths.raw_pts,
                "fetch_who":           settings.paths.raw_who,
                # Fuentes ampliadas
                "fetch_wjp":           settings.paths.raw_wjp,
                "fetch_ilostat":       settings.paths.raw_ilostat,
            }
            out = output_map[func_name]
            if not df.empty:
                df.to_csv(out, index=False, encoding="utf-8-sig")
                logger.info("      OK %d años · %d columnas -> %s",
                            len(df), len(df.columns) - 1, out.name)
            else:
                logger.warning("      SKIP 0 filas (sin datos disponibles) -> %s", out.name)
        except Exception as exc:
            logger.warning("      FAIL Error: %s", exc)

    logger.info("\n  [i] CPI / HDI se usan desde archivos existentes en data/raw/")
    logger.info("      (requieren descarga manual -- ver docs/FUENTES_Y_VARIABLES.md)")


# =============================================================================
# FASE 2 -- PIPELINE: CARGA + LIMPIEZA + NORMALIZACIÓN
# =============================================================================

def fase_pipeline(settings: Settings) -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("\n" + "-" * 60)
    logger.info("  FASE 2 -- Limpieza y normalización")
    logger.info("-" * 60)

    # Carga
    years = list(range(settings.series.start_year, settings.series.end_year + 1))
    master = pd.DataFrame({"año": years})

    for loader_cls in ALL_LOADERS:
        loader = loader_cls(settings=settings)
        source_name = loader.get_source_id().value
        try:
            result = loader.load_validated()
            cols = [c for c in result.df.columns if c != "año"]
            master = master.merge(result.df[["año"] + cols], on="año", how="left")
            logger.info("  OK %-10s %d años · %d variables", source_name, len(result.df), len(cols))
        except FileNotFoundError:
            logger.warning("  FAIL %-10s archivo no encontrado -- se omite", source_name)
        except Exception as exc:
            logger.warning("  FAIL %-10s %s", source_name, exc)

    logger.info("\n  Maestro: %d años × %d variables", len(master), len(master.columns) - 1)

    # IMF and OWID auxiliary series remain available to their own loaders. The
    # core panel does not patch missing annual observations from alternate files:
    # missing publication is carried into coverage.
    master.drop(columns=["pib_crecimiento_imf_pct"], inplace=True, errors="ignore")

    # ── Reconversión monetaria + log10 para tipo_cambio_oficial_lcu_usd ─────────
    # El WDI mezcla 3 denominaciones históricas sin convertir:
    #   2000-2017 → BsF/USD  (serie nativa del API, ya en BsF)
    #   2018-2021 → BsS/USD  (1 BsS = 1 000 BsF, reconversión dic-2018)
    #   2022+     → Bs/USD   (1 Bs = 10^6 BsS = 10^9 BsF, reconversión oct-2021)
    # Convertimos todo a BsF/USD equivalente y aplicamos log10 para comprimir
    # el rango de 11 órdenes de magnitud antes de la normalización Min-Max.
    if "tipo_cambio_oficial_lcu_usd" in master.columns:
        _tc = master["tipo_cambio_oficial_lcu_usd"].copy()
        _mask_bss = (master["año"] >= 2018) & (master["año"] <= 2021)
        _mask_bs  = master["año"] >= 2022
        _tc[_mask_bss] = _tc[_mask_bss] * 1_000          # BsS → BsF
        _tc[_mask_bs]  = _tc[_mask_bs]  * 1_000_000_000  # Bs  → BsF
        master["tipo_cambio_oficial_lcu_usd"] = np.log10(_tc.clip(lower=1e-9))
        logger.info("  Tipo cambio -> log10(BsF/USD equiv.): rango [%.2f, %.2f]",
                    master["tipo_cambio_oficial_lcu_usd"].min(),
                    master["tipo_cambio_oficial_lcu_usd"].max())
        # 2025-2026 queda NaN por lag WDI — se muestra como "sin dato" en dashboard.
        # NO se hace ffill: inventar dato trailing viola la regla CERO datos artificiales.

    # ── log10 para inflacion_deflactor_pib_pct ────────────────────────────────
    # Venezuela tiene un rango de 4 ordenes de magnitud: 12% (2001) → 65,374% (2018).
    # Sin transformar, Min-Max hace que 49.4% (2024) score ~99.9 por estar "cerca"
    # del minimo absoluto relativo al maximo historico.
    # log10 comprime la escala: log10(12)=1.08, log10(65374)=4.82, log10(49.4)=1.69
    # → el score 2024 pasa de ~99.9 a ~84, mas consistente con la realidad economica.
    # clip lower=0.1 para cubrir posible deflacion (log10(0) = -inf).
    if "inflacion_deflactor_pib_pct" in master.columns:
        master["inflacion_deflactor_pib_pct"] = np.log10(
            master["inflacion_deflactor_pib_pct"].clip(lower=0.1)
        )
        logger.info("  Inflacion -> log10(%%): rango [%.2f, %.2f]",
                    master["inflacion_deflactor_pib_pct"].min(),
                    master["inflacion_deflactor_pib_pct"].max())

    if master.shape[1] == 1:
        logger.error("  Sin datos. Ejecuta primero la fase de descarga.")
        sys.exit(1)

    # Pipeline de transformación
    pipeline = Pipeline([
        ("clean",     DataCleaner(
            start_year=settings.series.start_year,
            end_year=settings.series.end_year,
        )),
        ("normalize", MinMaxNormalizer()),
    ])
    df_norm = pipeline.fit_transform(master)

    # Guardar normalizado
    catalog_cols = ["año"] + [c for c in CATALOG if c in df_norm.columns]
    df_norm_out = df_norm[catalog_cols]
    df_norm_out.to_csv(settings.paths.data_processed / "iciv_normalizado.csv",
                       index=False, encoding="utf-8-sig")


    return master, df_norm_out


def fase_dataset_publico(
    df_raw: pd.DataFrame,
    df_norm: pd.DataFrame,
    settings: Settings,
) -> tuple[Path, Path]:
    """Exporta el dataset publico del proyecto en formato ancho y largo."""
    from iciv.data.dataset_package import build_dataset_package
    from iciv.index.dimensions import DIMENSIONS

    out_dir = settings.paths.data_processed
    core_vars = {v.column for dim in DIMENSIONS.values() for v in dim.variables}
    pulse_vars = {
        "wti_precio_usd", "brent_precio_usd", "tasa_fed_funds_pct",
        "usd_index_broad", "vix_volatility", "ust_10y_yield_pct",
        "petroleo_crudo_produccion_tbpd", "guardian_articulos_venezuela",
        "guardian_tono_titulares", "gdelt_cobertura_vol", "gdelt_tono_noticias",
    }

    year_col_raw = df_raw.columns[0]
    year_col_norm = df_norm.columns[0] if not df_norm.empty else year_col_raw
    public_vars = [c for c in CATALOG if c in df_raw.columns]
    wide = df_raw[[year_col_raw] + public_vars].copy()
    wide = wide.rename(columns={year_col_raw: "year"})
    wide_path = out_dir / "iciv_dataset_wide.csv"
    wide.to_csv(wide_path, index=False, encoding="utf-8-sig")

    rows: list[dict] = []
    norm_lookup = df_norm.set_index(year_col_norm) if year_col_norm in df_norm.columns else pd.DataFrame()
    for _, r in wide.iterrows():
        year = int(r["year"])
        for var in public_vars:
            meta = CATALOG.get(var)
            if meta is None:
                continue
            raw_val = r[var]
            norm_val = None
            if not norm_lookup.empty and var in norm_lookup.columns and year in norm_lookup.index:
                nv = norm_lookup.loc[year, var]
                norm_val = None if pd.isna(nv) else float(nv)
            if var in core_vars:
                role = "core_anual"
            elif var == "ied_neta_usd":
                role = "outcome_externo"
            elif var in pulse_vars:
                role = "pulse_mensual"
            else:
                role = "auxiliar"
            rows.append({
                "year": year,
                "variable": var,
                "valor_crudo": None if pd.isna(raw_val) else raw_val,
                "valor_normalizado": norm_val,
                "fuente": meta.source.value,
                "dimension": meta.dimension.value,
                "direccion": meta.direction.value,
                "rol": role,
                "entra_iciv_anual": var in core_vars,
                "entra_pulse_mensual": var in pulse_vars,
                "entra_validacion_outcome": var == "ied_neta_usd",
                "descripcion": meta.description,
                "nota": meta.notes,
            })

    long_path = out_dir / "iciv_dataset_largo.csv"
    pd.DataFrame(rows).to_csv(long_path, index=False, encoding="utf-8-sig")
    package = build_dataset_package(df_raw, wide_path, long_path, settings, release_id="latest")
    logger.info(
        "  OK Dataset publico -> %s, %s, release %s",
        wide_path.name,
        long_path.name,
        package.release_dir.relative_to(settings.paths.root),
    )
    return wide_path, long_path


# =============================================================================
# FASE 3 -- CÁLCULO DEL ICIV (FIXED + AHP)
# =============================================================================

def fase_modelo(df_norm: pd.DataFrame, settings: Settings) -> tuple[pd.DataFrame, pd.DataFrame, AHPWeights]:
    logger.info("\n" + "-" * 60)
    logger.info("  FASE 3 -- Cálculo del ICIV")
    logger.info("-" * 60)

    # -- Pesos Fijos (línea base — pesos iguales 1/6 por dimensión) ---------------
    # Usar 1/6 por dimensión hace la comparación AHP vs Fijos más informativa:
    # AHP refleja juicio experto; Fijos = benchmark neutral sin preferencias.
    _n_dims = len(DIMENSIONS)
    _equal_overrides: dict[str, float] = {}
    for _d_id, _d in DIMENSIONS.items():
        for _vw in _d.variables:
            if _vw.column in df_norm.columns:
                _equal_overrides[_vw.column] = (1.0 / _n_dims) * _vw.weight
    agg_fixed = ICIVAggregator(method="linear", strategy=FixedWeights(override=_equal_overrides))
    df_fixed = agg_fixed.compute(df_norm)
    df_fixed.to_csv(settings.paths.data_processed / "iciv_scores.csv",
                    index=False, encoding="utf-8-sig")
    logger.info("  OK Pesos Iguales (1/6 por dimensión) -> data/processed/iciv_scores.csv")

    # -- AHP (Saaty) -----------------------------------------------------------
    # compute_weights() debe llamarse antes de pasarlo al aggregator
    # para que dimension_result_ esté disponible al momento de agregar.
    ahp = AHPWeights()
    ahp.compute_weights(df_norm)  # inicializa dimension_result_ y variable_results_
    agg_ahp = ICIVAggregator(method="linear", strategy=ahp)
    df_ahp = agg_ahp.compute(df_norm)
    df_ahp.to_csv(settings.paths.data_processed / "iciv_scores_ahp.csv",
                  index=False, encoding="utf-8-sig")

    cr = ahp.dimension_result_["consistency"]["CR"]  # type: ignore
    logger.info("  OK AHP (CR=%.4f) -> data/processed/iciv_scores_ahp.csv", cr)

    # Resumen en consola
    logger.info("\n  -- Resultados ICIV (AHP) ------------------------------")
    logger.info("  %-6s  %-6s  %s", "Año", "ICIV", "Categoría")
    logger.info("  " + "-" * 48)
    for _, row in df_ahp.dropna(subset=["iciv_score"]).iterrows():
        logger.info("  %-6d  %-6.1f  %s",
                    int(row["año"]), row["iciv_score"], row["iciv_categoria"])

    valid = df_ahp["iciv_score"].dropna()
    logger.info("  " + "-" * 48)
    logger.info("  Promedio: %.1f  |  Mín: %.1f (%d)  |  Máx: %.1f (%d)",
                valid.mean(),
                valid.min(), int(df_ahp.loc[valid.idxmin(), "año"]),
                valid.max(), int(df_ahp.loc[valid.idxmax(), "año"]))

    return df_fixed, df_ahp, ahp


# =============================================================================
# FASE 3a-bis -- ICIV PULSE MENSUAL (co-indicador high-frequency)
# =============================================================================

def fase_pulse(settings: Settings) -> pd.DataFrame:
    """
    Construye el ICIV Pulse Mensual desde fuentes high-frequency.

    NO reemplaza el ICIV Anual oficial — es un nowcasting indicator
    paralelo basado en variables disponibles a frecuencia mensual.
    """
    from iciv.index.pulse_aggregator import PulseAggregator
    logger.info("\n" + "-" * 60)
    logger.info("  FASE 3a-bis -- ICIV Pulse Mensual (nowcast)")
    logger.info("-" * 60)
    agg = PulseAggregator(settings.paths.data_raw)
    df_pulse = agg.compute_pulse()
    if df_pulse.empty:
        logger.warning("  Pulse vacío — verifica fred_monthly.csv, eia_monthly.csv, guardian_monthly.csv")
        return df_pulse
    # Guardar
    out = settings.paths.data_processed / "iciv_pulse_monthly.csv"
    df_pulse.to_csv(out, index=False, encoding="utf-8-sig")
    # Guardar también componentes normalizados para el dashboard
    df_components = agg.get_components_normalized()
    if not df_components.empty:
        out_comp = settings.paths.data_processed / "iciv_pulse_components.csv"
        df_components.to_csv(out_comp, index=False, encoding="utf-8-sig")
    n_meses = len(df_pulse)
    n_reliable = int((df_pulse["cobertura_pct"] >= 70).sum())
    score_min = df_pulse["pulse_score"].min()
    score_max = df_pulse["pulse_score"].max()
    score_last = df_pulse["pulse_score"].iloc[-1]
    logger.info(f"  Pulse: {n_meses} meses, {n_reliable} con cobertura >=70%")
    logger.info(f"  Rango score: {score_min:.1f} - {score_max:.1f}, último: {score_last:.1f}")
    return df_pulse


# =============================================================================
# FASE 3a-ter -- FORECAST MENSUAL PULSE
# =============================================================================

def fase_ml_forecast(pulse_df: pd.DataFrame, annual_df: pd.DataFrame) -> dict:
    """
    Ajusta el forecast publico del Pulse:
    SARIMA univariado a seis meses sobre la serie mensual observada.
    """
    if pulse_df is None or pulse_df.empty:
        return {}
    from iciv.ml.pulse_forecast import PulseForecaster
    logger.info("\n" + "-" * 60)
    logger.info("  FASE 3a-ter -- Forecast Pulse (SARIMA)")
    logger.info("-" * 60)
    annual_for_ml = annual_df[["año", "iciv_score"]].dropna()
    forecaster = PulseForecaster(pulse_df, annual_for_ml)
    result = forecaster.compute_forecast()
    try:
        from iciv.config import settings as project_settings
        from iciv.ml.pulse_backtest import run_pulse_backtest

        bt = run_pulse_backtest(pulse_df, project_settings.paths.data_processed)
        result["backtest"] = bt["payload"]
        if bt["payload"].get("available"):
            logger.info(
                "  Backtest Pulse: %s predicciones, %s origenes",
                bt["payload"].get("n_predictions"),
                bt["payload"].get("n_origins"),
            )
        else:
            logger.warning("  Backtest Pulse no disponible: %s", bt["payload"].get("reason"))
    except Exception as exc:
        logger.warning("  Backtest Pulse omitido: %s", exc)
        result["backtest"] = {"available": False, "reason": str(exc)}
    return result


# =============================================================================
# FASE 3b -- SATV (Sistema de Alertas Tempranas Venezuela)
# =============================================================================

def fase_satv(settings: Settings, pulse_df: pd.DataFrame) -> dict:
    """Computa alertas SATV mensuales desde Pulse y sus componentes reales."""
    from iciv.satv.pulse_engine import PulseSATVEngine
    logger.info("\n" + "-" * 60)
    logger.info("  FASE 3b -- SATV · Alertas mensuales Pulse")
    logger.info("-" * 60)
    comp_path = settings.paths.data_processed / "iciv_pulse_components.csv"
    if pulse_df.empty or not comp_path.exists():
        logger.warning("  SATV Pulse vacío — no hay componentes mensuales suficientes")
        return {}
    components = pd.read_csv(comp_path)
    satv = PulseSATVEngine(pulse_df, components).compute_all()
    r = satv["resumen"]
    logger.info("  Señales: %d críticas · %d precaución · %d normal",
                r["dims_criticas"], r["dims_precaucion"], r["dims_normales"])
    logger.info("  Alertas activas: %d críticas · %d precaución · %d positivas",
                r["alertas_criticas"], r["alertas_precaucion"], r["alertas_positivas"])
    return satv


# =============================================================================
# FASE 3c -- CORRELACIÓN ICIV → IED
# =============================================================================

def fase_correlacion(df_raw: pd.DataFrame, df_ahp: pd.DataFrame) -> dict:
    """Análisis de correlación y causalidad de Granger: ICIV → IED."""
    from iciv.analytics.correlation import CorrelationAnalyzer
    logger.info("\n" + "-" * 60)
    logger.info("  FASE 3c -- Correlación ICIV → IED (Pearson / OLS / Granger)")
    logger.info("-" * 60)
    analyzer = CorrelationAnalyzer(df_raw, df_ahp)
    result = analyzer.compute_all()
    if "error" not in result:
        cc = result.get("cross_correlation", [])
        best = max(cc, key=lambda x: abs(x["r"])) if cc else {}
        logger.info("  Correlación máxima: r=%.3f (rezago %s)", best.get("r", 0), best.get("lag", "?"))
        ols = result.get("ols_1lag", {})
        logger.info("  OLS (1 rezago): R²=%.3f · F-pval=%.4f", ols.get("r2", 0), ols.get("f_pval", 1))
        gr  = result.get("granger", {}).get("por_lag", {}).get(1, {})
        logger.info("  Granger (lag=1): p=%.4f · H₀ %s",
                    gr.get("p_val", 1), "RECHAZADA" if gr.get("reject_h0") else "no rechazada")
    return result


def _generate_corr_charts_b64(corr: dict) -> tuple[str, str]:
    """
    Genera scatter ICIV(t-1)→IED(t) y barchart cross-correlación con matplotlib.
    Retorna (scatter_b64, crosscorr_b64) — strings base64 para <img src="data:...">.
    Devuelve ('','') si faltan datos.
    """
    import base64, io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    scatter_b64 = ""
    crosscorr_b64 = ""

    DARK_BG  = "#0d1117"
    CARD_BG  = "#161b22"
    GRID_COL = "#21262d"
    TEXT_COL = "#8b949e"
    ACCENT   = "#00d4aa"
    RED_COL  = "#e05c5c"
    YELLOW   = "#f1c40f"

    plt.rcParams.update({
        "figure.facecolor": DARK_BG, "axes.facecolor": CARD_BG,
        "axes.edgecolor": GRID_COL,  "axes.labelcolor": TEXT_COL,
        "xtick.color": TEXT_COL,     "ytick.color": TEXT_COL,
        "grid.color": GRID_COL,      "text.color": TEXT_COL,
        "font.size": 9,
    })

    # ── Scatter ──────────────────────────────────────────────────────────────
    scatter = corr.get("scatter", {})
    pts = scatter.get("puntos", [])
    reg = scatter.get("regresion", [])
    if pts:
        xs = [p["x"] for p in pts]
        ys = [p["y"] for p in pts]
        anos = [str(p.get("año", "")) for p in pts]
        colors = [ACCENT if y >= 0 else RED_COL for y in ys]

        fig, ax = plt.subplots(figsize=(5.5, 3.6))
        fig.patch.set_facecolor(DARK_BG)
        ax.scatter(xs, ys, c=colors, s=45, zorder=3, alpha=0.85)
        for x, y, a in zip(xs, ys, anos):
            ax.annotate(a, (x, y), fontsize=6.5, color=TEXT_COL,
                        xytext=(3, 3), textcoords="offset points")
        if len(reg) == 2:
            ax.plot([reg[0]["x"], reg[1]["x"]], [reg[0]["y"], reg[1]["y"]],
                    color=YELLOW, linewidth=1.4, linestyle="--", zorder=2)
        ax.axhline(0, color=GRID_COL, linewidth=0.8)
        ax.set_xlabel("ICIV (t−1)", color=TEXT_COL, fontsize=9)
        ax.set_ylabel("IED (MMM USD)", color=TEXT_COL, fontsize=9)
        ax.set_title("Scatter: ICIV₍ₜ₋₁₎ → IED₍ₜ₎", color="#e6edf3", fontsize=9.5, pad=8)
        ax.grid(True, linewidth=0.5, alpha=0.6)
        ax.tick_params(labelsize=8)
        fig.tight_layout(pad=1.0)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                    facecolor=DARK_BG, edgecolor="none")
        plt.close(fig)
        scatter_b64 = base64.b64encode(buf.getvalue()).decode()

    # ── Cross-correlación ────────────────────────────────────────────────────
    cc = corr.get("cross_correlation", [])
    if cc:
        labels = [d["label"] for d in cc]
        rs     = [d["r"] for d in cc]
        sigs   = [d["sig"] for d in cc]
        bar_colors = []
        for r, s in zip(rs, sigs):
            if s:
                bar_colors.append(ACCENT if r >= 0 else RED_COL)
            else:
                bar_colors.append("#8b949e55")

        fig, ax = plt.subplots(figsize=(5.5, 3.6))
        fig.patch.set_facecolor(DARK_BG)
        bars = ax.bar(labels, rs, color=bar_colors, edgecolor=GRID_COL,
                      linewidth=0.8, width=0.6)
        ax.axhline(0, color=GRID_COL, linewidth=0.8)
        ax.axhline(0.05,  color=TEXT_COL, linewidth=0.5, linestyle=":")
        ax.axhline(-0.05, color=TEXT_COL, linewidth=0.5, linestyle=":")
        for bar, r, s in zip(bars, rs, sigs):
            ax.text(bar.get_x() + bar.get_width()/2, r + (0.02 if r >= 0 else -0.05),
                    f"{r:.3f}", ha="center", va="bottom" if r >= 0 else "top",
                    fontsize=7.5, color="#e6edf3" if s else TEXT_COL)
        ax.set_ylim(-1, 1)
        ax.set_ylabel("Pearson r", color=TEXT_COL, fontsize=9)
        ax.set_title("Cross-Correlación ICIV → IED por Rezago", color="#e6edf3", fontsize=9.5, pad=8)
        ax.grid(True, axis="y", linewidth=0.5, alpha=0.6)
        ax.tick_params(labelsize=8)
        legend_els = [
            mpatches.Patch(color=ACCENT, label="Sig. positiva (p<0.05)"),
            mpatches.Patch(color=RED_COL, label="Sig. negativa"),
            mpatches.Patch(color="#8b949e55", label="No significativa"),
        ]
        ax.legend(handles=legend_els, fontsize=7, loc="lower right",
                  facecolor=CARD_BG, edgecolor=GRID_COL, labelcolor=TEXT_COL)
        fig.tight_layout(pad=1.0)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                    facecolor=DARK_BG, edgecolor="none")
        plt.close(fig)
        crosscorr_b64 = base64.b64encode(buf.getvalue()).decode()

    return scatter_b64, crosscorr_b64


def _generate_loo_validation_html(df_norm) -> str:
    """
    Bloque A2 del dashboard: validación externa NO circular (leave-one-out).

    Recalcula el ICIV excluyendo la variable de validación (el aggregator
    redistribuye su peso) y lo correlaciona contra la serie cruda excluida:
      - ICIV sin migración   vs stock migrantes UNHCR (esperada negativa)
      - ICIV sin luminosidad vs luz nocturna VIIRS 2014-2024 (esperada positiva;
        restringido a la era VIIRS por el escalón de sensor DMSP→VIIRS en 2013/14)

    Retorna el bloque HTML completo, o "" si faltan datos.
    Misma lógica que scripts/external_validation.py (fuente canónica de los CSV).
    """
    import base64, io

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from scipy import stats

    from iciv.config.settings import settings
    from iciv.index.aggregator import ICIVAggregator

    DARK_BG  = "#0d1117"
    CARD_BG  = "#161b22"
    GRID_COL = "#21262d"
    TEXT_COL = "#8b949e"
    ACCENT   = "#00d4aa"
    YELLOW   = "#f1c40f"

    if df_norm is None or "año" not in getattr(df_norm, "columns", []):
        return ""

    def _loo_score(col: str) -> pd.Series:
        df_loo = df_norm.copy()
        df_loo[col] = np.nan
        return ICIVAggregator(method="linear").compute(df_loo).set_index("año")["iciv_score"]

    def _raw_series(fname: str, indicador: str) -> pd.Series:
        df = pd.read_csv(settings.paths.data_raw / fname)
        df = df[df["indicador"] == indicador]
        return df.set_index("año")["valor"].astype(float)

    def _scatter_b64_loo(x: pd.Series, y: pd.Series, xlabel: str, ylabel: str,
                         title: str) -> tuple[str, dict]:
        joined = pd.concat([x, y], axis=1, keys=["x", "y"]).dropna()
        if len(joined) < 5:
            return "", {}
        r, p = stats.pearsonr(joined["x"], joined["y"])
        rho, p2 = stats.spearmanr(joined["x"], joined["y"])
        st = {"r": r, "p": p, "rho": rho, "p2": p2, "n": len(joined),
              "y0": int(joined.index.min()), "y1": int(joined.index.max())}

        plt.rcParams.update({
            "figure.facecolor": DARK_BG, "axes.facecolor": CARD_BG,
            "axes.edgecolor": GRID_COL,  "axes.labelcolor": TEXT_COL,
            "xtick.color": TEXT_COL,     "ytick.color": TEXT_COL,
            "grid.color": GRID_COL,      "text.color": TEXT_COL,
            "font.size": 9,
        })
        fig, ax = plt.subplots(figsize=(5.5, 3.6))
        fig.patch.set_facecolor(DARK_BG)
        ax.scatter(joined["x"], joined["y"], c=ACCENT, s=45, zorder=3, alpha=0.85)
        for yr, row in joined.iterrows():
            ax.annotate(str(int(yr)), (row["x"], row["y"]), fontsize=6.5,
                        color=TEXT_COL, xytext=(3, 3), textcoords="offset points")
        slope, intercept = np.polyfit(joined["x"], joined["y"], 1)
        xs = np.array([joined["x"].min(), joined["x"].max()])
        ax.plot(xs, slope * xs + intercept, color=YELLOW, linewidth=1.4,
                linestyle="--", zorder=2)
        ax.set_xlabel(xlabel, color=TEXT_COL, fontsize=9)
        ax.set_ylabel(ylabel, color=TEXT_COL, fontsize=9)
        ax.set_title(title, color="#e6edf3", fontsize=9.5, pad=8)
        ax.grid(True, linewidth=0.5, alpha=0.6)
        ax.tick_params(labelsize=8)
        fig.tight_layout(pad=1.0)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                    facecolor=DARK_BG, edgecolor="none")
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode(), st

    try:
        migr = _raw_series("unhcr.csv", "migrantes_vzla_millones")
        lumi = _raw_series("viirs.csv", "luminosidad_nocturna_idx")
        loo_migr = _loo_score("migrantes_vzla_millones")
        loo_lumi = _loo_score("luminosidad_nocturna_idx").loc[2014:]

        b64_m, st_m = _scatter_b64_loo(
            loo_migr, migr,
            "ICIV recalculado sin migración", "Migrantes UNHCR (millones)",
            "ICIV (leave-one-out) vs Emigración UNHCR")
        b64_l, st_l = _scatter_b64_loo(
            loo_lumi, lumi.loc[2014:],
            "ICIV recalculado sin luminosidad", "Luminosidad nocturna (índice)",
            "ICIV (leave-one-out) vs Luz nocturna · era VIIRS")
        if not b64_m or not b64_l:
            return ""
    except Exception as exc:  # noqa: BLE001 — el dashboard no debe caerse por este bloque
        logger.warning("  Validación leave-one-out: %s", exc)
        return ""

    def _stat_card(st: dict, esperado: str, ok: bool) -> str:
        color = "#2ecc71" if ok else "#e67e22"
        veredicto = "Hipótesis confirmada ✓" if ok else "Revisar"
        p_txt = "&lt; 0.001" if st["p"] < 0.001 else f"= {st['p']:.3f}"
        return (
            f'<div style="display:flex;gap:14px;flex-wrap:wrap;font-size:.74rem;color:var(--muted);margin-top:8px">'
            f'<span><strong style="color:#e6edf3">Pearson r = {st["r"]:+.3f}</strong> (p {p_txt})</span>'
            f'<span>Spearman ρ = {st["rho"]:+.3f}</span>'
            f'<span>n = {st["n"]} ({st["y0"]}–{st["y1"]})</span>'
            f'<span>Esperada: {esperado}</span>'
            f'<span style="color:{color};font-weight:600">{veredicto}</span>'
            f'</div>'
        )

    card_m = _stat_card(st_m, "negativa", st_m["r"] < 0 and st_m["p"] < 0.05)
    card_l = _stat_card(st_l, "positiva", st_l["r"] > 0 and st_l["p"] < 0.05)

    return f'''
  <!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
  <!-- A2 · VALIDACIÓN EXTERNA NO CIRCULAR (leave-one-out) -->
  <div style="margin-top:32px;margin-bottom:14px;padding:10px 14px;background:var(--card);border-left:3px solid var(--accent);border-radius:6px">
    <strong style="color:var(--accent);font-size:.85rem">A2 · Validación externa no circular — leave-one-out</strong>
    <div style="font-size:.72rem;color:var(--muted);margin-top:2px">
      El ICIV se recalcula <em>excluyendo</em> la variable de validación (su peso se redistribuye) y se
      correlaciona contra la serie cruda excluida. El score validado no contiene información directa
      de la señal contra la que se contrasta.
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
    <div class="card">
      <div style="font-size:.8rem;font-weight:600;color:var(--accent);margin-bottom:4px">
        ICIV (sin migración) vs Emigración venezolana
      </div>
      <div style="font-size:.72rem;color:var(--muted);margin-bottom:12px">
        Stock de migrantes y refugiados UNHCR · hipótesis: peor clima → más emigración
      </div>
      <img src="data:image/png;base64,{b64_m}" style="width:100%;border-radius:6px" alt="Scatter ICIV leave-one-out vs migración UNHCR">
      {card_m}
    </div>
    <div class="card">
      <div style="font-size:.8rem;font-weight:600;color:var(--accent);margin-bottom:4px">
        ICIV (sin luminosidad) vs Luz nocturna satelital
      </div>
      <div style="font-size:.72rem;color:var(--muted);margin-bottom:12px">
        Era VIIRS 2014–2024 (sensor homogéneo) · hipótesis: mejor clima → más actividad luminosa
      </div>
      <img src="data:image/png;base64,{b64_l}" style="width:100%;border-radius:6px" alt="Scatter ICIV leave-one-out vs luminosidad VIIRS">
      {card_l}
    </div>
  </div>

  <div class="card" style="border-left:3px solid var(--accent)">
    <div style="font-size:.75rem;color:var(--muted);line-height:1.6">
      <strong style="color:var(--text)">Por qué no es circular.</strong>
      Migración (D4) y luminosidad (D2) forman parte del score, así que correlacionar el ICIV completo
      contra ellas sería validar el índice con sus propios componentes. En el diseño leave-one-out el
      ICIV se recalcula sin la variable y el peso se redistribuye dentro de su dimensión: la correlación
      resultante mide si <em>el resto del índice</em> sigue la señal externa.
      <br><strong>Luminosidad — periodo completo no interpretable:</strong> la serie armonizada
      (Li et al., 2020) combina sensores DMSP (hasta 2013) y VIIRS (desde 2014) con un escalón de
      calibración en la transición; además el tramo 2000–2013 refleja la expansión eléctrica del boom
      petrolero. El test se restringe a la era VIIRS, que cubre el periodo de colapso económico.
      <br><em>Fuentes: UNHCR Population Statistics; Li et al. (2020) Harmonized NTL; Henderson,
      Storeygard &amp; Weil (2012, AER). Reproducible: <code>python scripts/external_validation.py</code>.</em>
    </div>
  </div>
'''


def _build_corr_stats_html(corr: dict) -> tuple[str, str, str, str]:
    """
    Genera HTML estático para OLS, Granger, ADF y la fórmula.
    Retorna (formula_html, ols1_html, ols2_html, granger_adf_html).
    """
    def _sig_color(sig: bool) -> str:
        return "#2ecc71" if sig else "#8b949e"

    def _ols_rows(ols: dict) -> str:
        if not ols or ols.get("error"):
            return "<tr><td colspan='3' style='color:#8b949e;padding:6px'>No disponible</td></tr>"
        rows = []
        for name, p in (ols.get("params") or {}).items():
            sig = p.get("sig", False)
            star = " *" if sig else ""
            rows.append(
                f'<tr><td style="padding:3px 0;color:#e6edf3">{name}</td>'
                f'<td style="text-align:right;color:#00d4aa">{p["coef"]:.4f}</td>'
                f'<td style="text-align:right;color:{_sig_color(sig)}">{p["pval"]:.4f}{star}</td></tr>'
            )
        r2 = ols.get("r2", 0)
        r2a = ols.get("r2_adj", 0)
        fp = ols.get("f_pval", 1)
        n = ols.get("n", "")
        rows.append(
            f'<tr><td colspan="3" style="padding-top:6px;font-size:.68rem;color:#8b949e">'
            f'R²={r2:.3f} R²adj={r2a:.3f} F-p={fp:.4f} n={n}</td></tr>'
        )
        return "\n".join(rows)

    ols1 = corr.get("ols_1lag", {})
    ols2 = corr.get("ols_2lag", {})
    formula = (ols1.get("formula") or "IED_t = β₀ + β₁·ICIV_{t−1} + ε")
    formula_html = f'<code style="font-size:.75rem;color:#8b949e">{formula}</code>'

    ols1_html = _ols_rows(ols1)
    ols2_html = _ols_rows(ols2)

    # Granger + ADF
    gr = corr.get("granger", {})
    adf = corr.get("adf", {})
    parts = []

    # Granger cards
    for lag, res in (gr.get("por_lag") or {}).items():
        if res.get("error"):
            continue
        reject = res.get("reject_h0", False)
        col = "#00d4aa" if reject else "#8b949e"
        label = "H₀ rechazada (p&lt;0.05)" if reject else "H₀ no rechazada"
        parts.append(
            f'<div style="background:#0d1117;border-radius:8px;padding:10px 12px;border:1px solid {col}44">'
            f'<div style="font-size:.68rem;color:#8b949e">Lag {lag}</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{col}">{res["p_val"]:.4f}</div>'
            f'<div style="font-size:.68rem;color:{col}">{label}</div>'
            f'<div style="font-size:.65rem;color:#8b949e">F={res["f_stat"]:.3f}</div></div>'
        )
    granger_cards_html = "\n".join(parts) if parts else "<div style='color:#8b949e;font-size:.72rem'>No disponible</div>"

    conclusion = gr.get("conclusion", "")
    nota_diff = gr.get("nota_diff", "")
    conclusion_html = (
        f'<div style="font-size:.73rem;color:#8b949e;line-height:1.5;padding:8px 12px;'
        f'background:#0d1117;border-radius:6px;margin-bottom:8px">{conclusion}</div>'
        + (f'<div style="font-size:.68rem;color:#8b949e;margin-bottom:14px">{nota_diff}</div>' if nota_diff else "")
    )

    # ADF cards
    adf_parts = []
    for key, lbl in [("iciv", "ICIV"), ("ied", "IED")]:
        d = (adf or {}).get(key, {})
        if not d.get("stat"):
            continue
        col = "#00d4aa" if d.get("stationary") else "#e67e22"
        adf_parts.append(
            f'<div style="background:#0d1117;border-radius:8px;padding:10px 12px;border:1px solid {col}44">'
            f'<div style="font-size:.68rem;color:#8b949e">{lbl} ADF</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{col}">{d["stat"]:.4f}</div>'
            f'<div style="font-size:.68rem;color:{col}">{d.get("label","")}</div>'
            f'<div style="font-size:.65rem;color:#8b949e">p={d.get("pval",0):.4f} CV5%={d.get("cv_5pct",0):.3f}</div></div>'
        )
    adf_cards_html = "\n".join(adf_parts) if adf_parts else "<div style='color:#8b949e;font-size:.72rem'>No disponible</div>"

    granger_adf_html = (
        '<div style="font-size:.72rem;font-weight:600;color:#8b949e;margin-bottom:6px">'
        'Test de Granger: \u00bfICIV precede estad\u00edsticamente a la IED?</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">'
        f'{granger_cards_html}</div>'
        f'{conclusion_html}'
        '<div style="font-size:.72rem;font-weight:600;color:#8b949e;margin-bottom:6px">'
        'Test ADF \u2014 Estacionariedad de las series</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">{adf_cards_html}</div>'
    )

    return formula_html, ols1_html, ols2_html, granger_adf_html


def _load_map_data(settings: Settings) -> tuple[str, str]:
    """
    Carga el GeoJSON de estados venezolanos y los datos NTL por estado.
    Retorna (geojson_str, viirs_states_json_str).
    """
    import json as _json
    geojson_path = settings.paths.data_raw / "venezuela_states.geojson"
    viirs_path   = settings.paths.raw_viirs_states

    geojson_str = "{}"
    viirs_json  = "[]"

    if geojson_path.exists():
        geojson_str = geojson_path.read_text(encoding="utf-8")
    else:
        logger.warning("  WARN GeoJSON de estados no encontrado en %s", geojson_path)

    if viirs_path.exists():
        df_vs = pd.read_csv(viirs_path, encoding="utf-8-sig")
        # Normalizar el nombre de la columna de año (puede ser "año" o "ano")
        if "año" in df_vs.columns:
            df_vs = df_vs.rename(columns={"año": "ano"})
        # Normalizar ntl_idx por estado al rango 0-100 (max historico de cada estado = 100)
        # Los valores raw son DN 0-63; la normalizacion per-estado muestra la dinamica temporal.
        if "ntl_idx" in df_vs.columns and not df_vs.empty:
            state_max = df_vs.groupby("estado_cod")["ntl_idx"].transform("max")
            df_vs["ntl_idx"] = (df_vs["ntl_idx"] / state_max * 100).round(1)
        # Pivotear: {cod: {año: ntl_idx}}
        pivot: dict[str, dict[int, float]] = {}
        for _, row in df_vs.iterrows():
            cod = str(row["estado_cod"])
            yr  = int(row["ano"])
            val = round(float(row["ntl_idx"]), 1)
            pivot.setdefault(cod, {})[yr] = val
        viirs_json = _json.dumps(pivot, ensure_ascii=False)
    else:
        logger.warning("  WARN viirs_states.csv no encontrado — mapa sin datos NTL")

    return geojson_str, viirs_json


def fase_sector_radar(df_ahp: pd.DataFrame) -> dict:
    """Calcula el radar sectorial con las dimensiones ICIV disponibles."""
    try:
        from iciv.analytics.sector_radar import SectorRadar

        logger.info("\n" + "-" * 60)
        logger.info("  FASE 3e -- Radar Sectorial")
        logger.info("-" * 60)
        return SectorRadar(df_ahp).compute_all()
    except Exception as exc:
        logger.error("  ERROR SectorRadar: %s", exc, exc_info=True)
        return {"error": str(exc), "ranking": []}


def _score_to_label(score: float) -> str:
    if score < 35:
        return "Alto Riesgo"
    if score < 50:
        return "Riesgo Moderado-Alto"
    if score < 65:
        return "Riesgo Moderado"
    if score < 80:
        return "Bajo Riesgo"
    return "Muy Bajo Riesgo"


def _score_to_color(score: float) -> str:
    return RISK_COLORS[_score_to_label(score)]


# =============================================================================
# FASE 4 -- DASHBOARD HTML
# =============================================================================

def fase_dashboard(
    df_raw: pd.DataFrame,
    df_norm: pd.DataFrame,
    df_fixed: pd.DataFrame,
    df_ahp: pd.DataFrame,
    ahp: AHPWeights,
    settings: Settings,
    satv_data: dict | None = None,
    escenarios_data: dict | None = None,
    correlacion_data: dict | None = None,
    sanciones_data: dict | None = None,
    mc_data: dict | None = None,
    sector_data: dict | None = None,
    pulse_data: pd.DataFrame | None = None,
    ml_forecast: dict | None = None,
) -> Path:
    logger.info("\n" + "-" * 60)
    logger.info("  FASE 4 -- Generando dashboard HTML")
    logger.info("-" * 60)

    df_plot = df_ahp.dropna(subset=["iciv_score"]).copy()
    df_fixed_plot = df_fixed.dropna(subset=["iciv_score"]).copy()

    # current_score / current_year_val / current_label / current_color se
    # calculan más abajo tras determinar el año de referencia confiable (≥60% cobertura).
    # Aquí solo se necesita prev_score para el delta.
    prev_score = float(df_plot.iloc[-2]["iciv_score"]) if len(df_plot) >= 2 else float(df_plot.iloc[-1]["iciv_score"])

    dim_cols = [d.value for d in DIMENSIONS]
    dim_names = {d.value: DIMENSIONS[d].name for d in DIMENSIONS}
    available_dims = [c for c in dim_cols if c in df_plot.columns]

    _MONTH_NAMES_ES = [
        "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    _now = datetime.now()
    generated_at = f"{_now.day:02d} de {_MONTH_NAMES_ES[_now.month]} de {_now.year} · {_now:%H:%M}"
    n_years   = int(df_plot["iciv_score"].notna().sum())
    score_min = float(df_plot["iciv_score"].min())
    year_min  = int(df_plot.loc[df_plot["iciv_score"].idxmin(), "año"])
    score_max = float(df_plot["iciv_score"].max())
    year_max  = int(df_plot.loc[df_plot["iciv_score"].idxmax(), "año"])
    score_avg = float(df_plot["iciv_score"].mean())

    # -- Serialise data as JS variables ----------------------------------------
    years_js      = json.dumps([int(y) for y in df_plot["año"].tolist()])
    scores_ahp_js = json.dumps([round(float(s), 2) for s in df_plot["iciv_score"].tolist()])
    pt_colors_js  = json.dumps([_score_to_color(float(s)) for s in df_plot["iciv_score"].tolist()])

    # Cobertura temporal por año (para indicar confianza del dato en el gráfico)
    _COVERAGE_THRESHOLD = 60.0  # % mínimo para considerar el score confiable
    if "cobertura_pct" in df_plot.columns:
        coverage_js = json.dumps([
            round(float(v), 1) if pd.notna(v) else None
            for v in df_plot["cobertura_pct"].tolist()
        ])
    else:
        coverage_js = json.dumps([100.0] * len(df_plot))

    years_fix_js   = json.dumps([int(y) for y in df_fixed_plot["año"].tolist()])
    scores_fix_js  = json.dumps([round(float(s), 2) for s in df_fixed_plot["iciv_score"].tolist()])

    # ── Per-year data for Score Actual interactive year selector ─────────────
    _sya: dict = {}
    for _, _row in df_plot.iterrows():
        _yr = int(_row["año"])
        _sya_dims: dict = {}
        for _d in dim_cols:
            if _d in df_plot.columns:
                _v = _row[_d]
                _sya_dims[_d] = round(float(_v), 2) if pd.notna(_v) else None
        _sya_cov = float(_row["cobertura_pct"]) \
            if "cobertura_pct" in df_plot.columns and pd.notna(_row.get("cobertura_pct")) else 100.0
        # Score of previous year for delta calculation
        _prev_rows = df_plot[df_plot["año"] < _yr]
        _sya_prev = round(float(_prev_rows.iloc[-1]["iciv_score"]), 2) if not _prev_rows.empty else None
        _sya[_yr] = {
            "iciv":     round(float(_row["iciv_score"]), 2),
            "coverage": round(_sya_cov, 1),
            "prev":     _sya_prev,
            "dims":     _sya_dims,
        }
    score_by_year_json = json.dumps(_sya, ensure_ascii=False)

    # Default annual reference: the headline must always show the latest
    # available year, even when coverage is provisional. A separate reference
    # row keeps the latest high-coverage annual reading visible for comparison.
    if "cobertura_pct" in df_plot.columns:
        _reference_years = df_plot[df_plot["cobertura_pct"] >= 70.0]
    else:
        _reference_years = df_plot
    _reference_row = _reference_years.iloc[-1] if not _reference_years.empty else df_plot.iloc[-1]
    _current_row = df_plot.iloc[-1]
    annual_ref_year = int(_reference_row["año"])
    annual_ref_score = float(_reference_row["iciv_score"])
    annual_ref_coverage = float(_reference_row["cobertura_pct"]) \
        if "cobertura_pct" in df_plot.columns else 100.0

    # Year selector buttons (horizontal scrollable bar)
    _score_years = [int(y) for y in df_plot["año"].tolist()]
    year_tabs_html = '<div class="score-year-tabs" id="scoreYearTabs">\n'
    for _syr in _score_years:
        _syr_cls = " score-yr-active" if _syr == int(_current_row["año"]) else ""
        year_tabs_html += f'  <button class="score-yr-btn{_syr_cls}" onclick="selectScoreYear({_syr})">{_syr}</button>\n'
    year_tabs_html += "</div>"

    current_score    = float(_current_row["iciv_score"])
    current_year_val = int(_current_row["año"])
    current_label    = _score_to_label(current_score)
    current_color    = _score_to_color(current_score)

    current_coverage = float(_current_row["cobertura_pct"]) \
        if "cobertura_pct" in df_plot.columns else 100.0
    is_low_coverage  = current_coverage < _COVERAGE_THRESHOLD
    _prev_current_rows = df_plot[df_plot["año"] < current_year_val]
    prev_score = (
        float(_prev_current_rows.iloc[-1]["iciv_score"])
        if not _prev_current_rows.empty else current_score
    )

    # ── Tier de cobertura (para etiquetas académicas) ──────────────────────────
    # ≥85%       → Histórico  (verde)     — series completas, publicación oficial
    # 70–84.9%  → Útil       (cyan)      — mayoría de fuentes disponibles
    # 50–69.9%  → Parcial    (naranja)   — fuentes anuales con lag, año reciente
    # <50%       → Provisional (rojo)     — solo fuentes de alta frecuencia
    def _cov_tier(pct: float) -> tuple[str, str]:
        if pct >= 85.0:
            return ("Histórico",   "#00d4aa")
        elif pct >= 70.0:
            return ("Útil",        "#2ecc71")
        elif pct >= 50.0:
            return ("Parcial",     "#e6a817")
        else:
            return ("Provisional", "#e74c3c")

    _tier_label, _tier_color = _cov_tier(current_coverage)
    coverage_badge = f"{current_coverage:.0f}% · {_tier_label}"

    # Para el radar de dimensiones: usar el último año con algún dato en dimensiones
    # (puede ser que 2026 tenga NaN en todas las dims excepto D1/D6)
    last_row  = _current_row
    dim_vals  = [round(float(last_row.get(d, 0) or 0), 2) if not pd.isna(last_row.get(d)) else 0.0
                 for d in available_dims]
    dim_lbls  = [dim_names.get(d, d) for d in available_dims]
    dim_clrs  = DIM_COLORS[:len(available_dims)]
    has_provisional = False   # kept for template compatibility

    radar_vals_js = json.dumps(dim_vals)
    radar_lbls_js = json.dumps(dim_lbls)
    radar_clrs_js = json.dumps(dim_clrs)

    dim_series_js = {}
    for dc in available_dims:
        dim_series_js[dc] = [round(float(v), 2) if v is not None and str(v) != "nan" else None
                             for v in df_plot[dc].tolist()]

    dim_series_json = json.dumps(dim_series_js)

    # AHP weight table
    ahp_rows_html = ""
    cr_val = 0.0
    if ahp.dimension_result_:
        ahp_tbl = ahp.get_dimension_weights_table()
        cr_val  = ahp.dimension_result_["consistency"]["CR"]
        dim_label_map = {
            "D1_macro":          "Estabilidad Macroeconómica",
            "D2_energia":        "Sector Energético",
            "D3_institucional":  "Entorno Institucional",
            "D4_comercial":      "Apertura Comercial",
            "D5_capital_humano": "Capital Humano",
            "D6_percepcion":     "Percepción Internacional",
        }
        for _, r in ahp_tbl.iterrows():
            label = dim_label_map.get(r["elemento"], r["elemento"])
            w     = float(r["peso_ahp"])
            pct   = r["peso_pct"]
            bar   = int(w * 400)
            ahp_rows_html += (
                f'<tr><td>{label}</td>'
                f'<td>{w:.4f}</td>'
                f'<td>{pct}</td>'
                f'<td><div style="background:#00d4aa;height:10px;border-radius:4px;width:{bar}px;max-width:200px"></div></td></tr>\n'
            )

    # Historical table rows
    df_table = df_ahp[["año", "iciv_score", "iciv_categoria"]].copy()
    df_table = df_table.dropna(subset=["iciv_score"]).sort_values("año", ascending=False)
    df_table["año"]        = df_table["año"].astype(int)
    df_table["iciv_score"] = df_table["iciv_score"].round(1)

    hist_rows_html = ""
    for _, r in df_table.iterrows():
        c   = _score_to_color(float(r["iciv_score"]))
        cat = str(r["iciv_categoria"]).replace("🔴 ", "").replace("🟠 ", "").replace("🟡 ", "").replace("🟢🟢 ", "").replace("🟢 ", "").replace("🟢🟢", "").replace("🔴", "").replace("🟠", "").replace("🟡", "").replace("🟢", "")
        hist_rows_html += (
            f'<tr>'
            f'<td>{int(r["año"])}</td>'
            f'<td><span style="color:{c};font-weight:700">{r["iciv_score"]:.1f}</span></td>'
            f'<td><span class="pill" style="background:{c}22;color:{c};border:1px solid {c}55">{cat}</span></td>'
            f'</tr>\n'
        )

    # Dimension detail cards — variables + sources per dimension
    SOURCE_LABELS = {
        "WDI": "World Bank WDI", "WGI": "World Bank WGI", "EIA": "EIA International",
        "HDI": "PNUD / UNDP", "GUARDIAN": "The Guardian", "FRED": "FRED St. Louis Fed",
        "FREEDOM_HOUSE": "Freedom House",
    }
    from iciv.data.catalog import CATALOG
    dim_detail_cards_html = ""
    for dim_id, dim in DIMENSIONS.items():
        d_score = float(last_row.get(dim_id.value, 0) or 0)
        d_color = _score_to_color(d_score) if d_score > 0 else "#8b949e"
        d_pct   = f"{dim.iciv_weight*100:.0f}%"
        vars_rows = ""
        for vw in dim.variables:
            meta = CATALOG.get(vw.column)
            src  = SOURCE_LABELS.get(meta.source.value, meta.source.value) if meta else "—"
            dirn = "▲ positiva" if (meta and meta.direction.value == "positive") else "▼ negativa"
            dirn_color = "#00d4aa" if (meta and meta.direction.value == "positive") else "#e05c5c"
            col_label = (meta.description.split("—")[0].strip() if meta else vw.column)
            vars_rows += (
                f'<tr>'
                f'<td style="font-size:.75rem">{col_label}</td>'
                f'<td style="text-align:center;font-weight:600">{vw.weight:.0%}</td>'
                f'<td><span style="background:#21262d;padding:2px 7px;border-radius:10px;font-size:.68rem">{src}</span></td>'
                f'<td style="color:{dirn_color};font-size:.72rem">{dirn}</td>'
                f'</tr>\n'
            )
        dim_detail_cards_html += (
            f'<div class="dim-detail-card">'
            f'<div class="dim-detail-header">'
            f'<div>'
            f'<span class="dim-detail-id">{dim_id.value}</span>'
            f'<span class="dim-detail-name">{dim.name}</span>'
            f'</div>'
            f'<div style="text-align:right">'
            f'<div style="font-size:1.5rem;font-weight:700;color:{d_color}">{d_score:.1f}</div>'
            f'<div style="font-size:.68rem;color:var(--muted)">Peso ICIV: {d_pct}</div>'
            f'</div>'
            f'</div>'
            f'<table class="dim-var-table">'
            f'<thead><tr><th>Variable</th><th>Peso</th><th>Fuente</th><th>Dirección</th></tr></thead>'
            f'<tbody>{vars_rows}</tbody>'
            f'</table>'
            f'</div>\n'
        )

    # ── Dimension sub-tab descriptions (academic) ────────────────────────────
    DIM_DESCRIPTIONS = {
        "D1_macro": (
            "La <strong>Estabilidad Macroeconomica</strong> captura inflacion, crecimiento, "
            "reservas, tipo de cambio y condiciones financieras externas. Se transforma la "
            "inflacion a log10 para que la hiperinflacion historica no vuelva artificialmente "
            "optimistas los anos recientes. Peso en el ICIV: <strong>25 %</strong>."
        ),
        "D2_energia": (
            "El <strong>Sector Energetico y Petrolero</strong> mide capacidad de produccion de "
            "crudo, gas, electricidad y actividad observada por luminosidad nocturna. La capa "
            "satelital aporta una senal independiente de estadisticas locales. Peso en el ICIV: "
            "<strong>20 %</strong>."
        ),
        "D3_institucional": (
            "El <strong>Entorno Institucional y Legal</strong> resume corrupcion, gobernanza, "
            "libertades, regla de derecho y represion politica con fuentes internacionales "
            "comparables: Transparency International, WGI, Freedom House, WJP y Political Terror "
            "Scale. Peso en el ICIV: <strong>20 %</strong>."
        ),
        "D4_comercial": (
            "La <strong>Apertura Comercial y Operativa</strong> evalua exportaciones, desempleo, "
            "migracion acumulada y conectividad maritima. La IED queda fuera del score y se usa "
            "como outcome externo para validacion. Peso en el ICIV: <strong>15 %</strong>."
        ),
        "D5_capital_humano": (
            "El <strong>Capital Humano e Infraestructura Social</strong> mide condiciones de vida "
            "y capacidad laboral mediante IDH, esperanza de vida, mortalidad infantil, acceso a "
            "electricidad y empleo informal. Peso en el ICIV: <strong>10 %</strong>."
        ),
        "D6_percepcion": (
            "La <strong>Percepcion Internacional</strong> captura tono y volumen de cobertura "
            "externa sobre Venezuela con The Guardian y VADER. GDELT se reserva para Pulse y "
            "monitoreo de noticias, no para el score anual core. Peso en el ICIV: <strong>10 %</strong>."
        ),
    }

    # Instead, for each variable use the LAST YEAR where it has a real non-NaN value.
    def _last_valid_norm(col: str) -> tuple[float | None, int | None]:
        """Return (normalized_value, year) for the most recent non-NaN cell in col."""
        if col not in df_norm.columns:
            return None, None
        valid = df_norm[df_norm[col].notna()]
        if valid.empty:
            return None, None
        last = valid.iloc[-1]
        val = last[col]
        yr_col = df_norm.columns[0]
        yr = int(last[yr_col]) if yr_col in last.index else None
        try:
            return round(float(val), 1), yr
        except (ValueError, TypeError):
            return None, yr

    dim_tab_data: dict = {}
    for _dim_id, _dim in DIMENSIONS.items():
        _key = _dim_id.value
        _hist: list = []
        if _key in df_plot.columns:
            _hist = [
                round(float(v), 2) if v is not None and str(v) != "nan" else None
                for v in df_plot[_key].tolist()
            ]
        _var_data: list = []
        for _vw in _dim.variables:
            _meta = CATALOG.get(_vw.column)
            # Use last real value for each variable (not forced 2026 which is mostly NaN)
            _val, _val_yr = _last_valid_norm(_vw.column)
            # Build label suffix showing which year the value is from
            _yr_suffix = f" [{_val_yr}]" if _val_yr is not None and _val is not None else ""
            _var_data.append({
                "col": _vw.column,
                "label": (_meta.description if _meta else _vw.column),
                "label_yr": _yr_suffix,
                "weight": _vw.weight,
                "source": SOURCE_LABELS.get(_meta.source.value, _meta.source.value) if _meta else "—",
                "direction": (_meta.direction.value if _meta else "positive"),
                "val": _val,
                "val_yr": _val_yr,
            })
        _scores = [v for v in _hist if v is not None]
        dim_tab_data[_key] = {
            "name": _dim.name,
            "weight": _dim.iciv_weight,
            "description": DIM_DESCRIPTIONS.get(_key, ""),
            "hist": _hist,
            "vars": _var_data,
            "current": round(float(last_row.get(_key, 0) or 0), 1),
            "avg": round(sum(_scores) / len(_scores), 1) if _scores else 0.0,
            "min_val": round(min(_scores), 1) if _scores else 0.0,
            "max_val": round(max(_scores), 1) if _scores else 0.0,
        }
    dim_tab_data_json = json.dumps(dim_tab_data, ensure_ascii=False)

    # ── Sub-tab buttons + view placeholders ───────────────────────────────────
    _dim_short_labels = {
        "D1_macro":          "D1 Macro",
        "D2_energia":        "D2 Energía",
        "D3_institucional":  "D3 Institucional",
        "D4_comercial":      "D4 Comercial",
        "D5_capital_humano": "D5 Capital Humano",
        "D6_percepcion":     "D6 Percepción",
    }
    dim_subtab_buttons_html = '    <button class="dim-stab dim-stab-active" data-dim="todas">Todas</button>\n'
    for _dim_id in DIMENSIONS:
        _lbl = _dim_short_labels.get(_dim_id.value, _dim_id.value)
        dim_subtab_buttons_html += (
            f'    <button class="dim-stab" data-dim="{_dim_id.value}">{_lbl}</button>\n'
        )

    dim_view_divs_html = ""
    for _dim_id in DIMENSIONS:
        dim_view_divs_html += f'  <div class="dim-view" id="dimview-{_dim_id.value}"></div>\n'

    # Delta respecto al año anterior del mismo conjunto
    delta_sign = "+" if current_score >= prev_score else ""
    delta_val  = current_score - prev_score
    delta_cls  = "stat-up" if delta_val >= 0 else "stat-down"

    # gauge angle: 0=left(-135deg) 100=right(+135deg) — arc of 270deg
    # Needle angle: arc is 180° (semicircle), NOT 270°.
    # score=0 → -90° (left), score=50 → 0° (up), score=100 → +90° (right)
    gauge_angle = -90 + (current_score / 100) * 180

    # Gauge active-band highlight — which band contains the current score
    # Total arc length = π*90 ≈ 282.74. Band offsets (cumulative arc lengths):
    _ARC_TOTAL = 282.74
    _BAND_BREAKS = [(0, 30, 0.0), (30, 50, 84.8), (50, 65, 141.3), (65, 80, 183.7), (80, 100, 226.1)]
    _BAND_LENS   = [84.8, 56.5, 42.4, 42.4, 56.5]
    _active_band_idx = 0
    for _i, (lo, hi, _) in enumerate(_BAND_BREAKS):
        if lo <= current_score <= hi or (current_score > lo and current_score <= hi):
            _active_band_idx = _i
    active_dash_len    = _BAND_LENS[_active_band_idx]
    active_dash_offset = _BAND_BREAKS[_active_band_idx][2]
    # Arc from score=0 to current score (visual fill)
    score_arc = (current_score / 100) * _ARC_TOTAL

    # ── SATV — serializar a JSON para el dashboard ────────────────────────────
    _satv = satv_data or {}
    satv_json = json.dumps(_satv, ensure_ascii=False)

    # ── Escenarios — serializar a JSON ────────────────────────────────────────
    _esc = escenarios_data or {}
    escenarios_json = json.dumps(_esc, ensure_ascii=False)

    # ── Datos del Simulador — pesos AHP y scores actuales por dimensión ───────
    _sim_dim_cols = [d_id.value for d_id in DIMENSIONS]
    _sim_complete = df_plot.dropna(subset=[c for c in _sim_dim_cols if c in df_plot.columns])
    _sim_base_row = _sim_complete.iloc[-1] if not _sim_complete.empty else df_plot.iloc[-1]
    sim_base_year = int(_sim_base_row["año"])
    _sim_dims: list[dict] = []
    for _d_id, _d in DIMENSIONS.items():
        _key = _d_id.value
        _hist_vals = [round(float(v), 2) if v is not None and str(v) != "nan" else None
                      for v in df_plot[_key].tolist()] if _key in df_plot.columns else []
        _cur_raw = _sim_base_row.get(_key)
        _cur = round(float(_cur_raw), 1) if _cur_raw is not None and not pd.isna(_cur_raw) else 0.0
        _sim_dims.append({
            "id":      _key,
            "label":   _d.name,
            "weight":  _d.iciv_weight,
            "current": _cur,
            "hist":    _hist_vals,
            "max_hist": max((v for v in _hist_vals if v is not None), default=100.0),
        })
    sim_dims_json = json.dumps(_sim_dims, ensure_ascii=False)
    sim_years_js  = years_js   # same years already computed
    sim_scores_js = scores_ahp_js  # same AHP scores already computed

    # ── Correlación ICIV → IED — gráficas y tablas estáticas ────────────────
    _corr = correlacion_data or {}
    correlacion_json = json.dumps(_corr, ensure_ascii=False, cls=_NumpyEncoder)
    _scatter_b64, _crosscorr_b64 = _generate_corr_charts_b64(_corr)
    _corr_formula_html, _corr_ols1_html, _corr_ols2_html, _corr_granger_adf_html = _build_corr_stats_html(_corr)

    sanciones_json = "{}"
    _sanciones_table_html = ""

    # ── Validación externa no circular (leave-one-out) — bloque A2 ───────────
    _loo_validation_html = _generate_loo_validation_html(df_norm)

    # ── Validación externa: correlaciones ICIV vs índices internacionales ─────
    # Calcula Pearson/Spearman entre el ICIV y cada índice externo presente como
    # variable normalizada. Solo años con ambos datos disponibles (n>=10).
    _ve_rows_html = ""
    try:
        from scipy.stats import pearsonr, spearmanr
        # Mapa: nombre legible → columna en df_norm + dirección esperada
        # "+" significa que el índice ya está en escala "más es mejor" (debería correlacionar positivo)
        # "-" significa que el índice es "más es peor" → ya invertido en normalizado, correlación positiva
        _ext_indices = {
            "HDI - Desarrollo Humano (PNUD)":             ("hdi", "+"),
            "WGI - Gobernanza promedio (Banco Mundial)":  ("wgi_promedio_sc", "+"),
            "CPI - Percepcion Corrupcion (TI)":           ("cpi_score", "+"),
            "Freedom House - Libertades":                 ("freedom_house_score", "+"),
            "WJP - Rule of Law":                          ("wjp_rule_of_law", "+"),
            "PTS - Political Terror Scale":               ("pts_terror_politico", "+"),
        }
        _iciv_series = df_ahp["iciv_score"]
        _df_match = df_ahp.merge(df_norm, on="año", suffixes=("_x", "")) \
                    if df_norm is not None and "año" in df_norm.columns else df_ahp.copy()
        for _label, (_col, _dir) in _ext_indices.items():
            if _col not in _df_match.columns:
                continue
            _pair = _df_match[["iciv_score", _col]].dropna()
            if len(_pair) < 10:
                continue
            try:
                _r, _p = pearsonr(_pair["iciv_score"], _pair[_col])
                _rho, _p2 = spearmanr(_pair["iciv_score"], _pair[_col])
            except Exception:
                continue
            # Interpretación
            _r_abs = abs(_r)
            if _r_abs >= 0.7:
                _interp = '<span style="color:#2ecc71">Validado ✓ (correlación fuerte)</span>'
            elif _r_abs >= 0.4:
                _interp = '<span style="color:#f1c40f">Validado parcialmente (moderada)</span>'
            else:
                _interp = '<span style="color:#e67e22">Débil — revisar</span>'
            _ve_rows_html += (
                f'<tr><td>{_label}</td>'
                f'<td>{_r:.3f}</td>'
                f'<td>{_rho:.3f}</td>'
                f'<td>{len(_pair)}</td>'
                f'<td>{_interp}</td></tr>'
            )
        if not _ve_rows_html:
            _ve_rows_html = '<tr><td colspan="5" style="color:var(--muted);font-style:italic">No hay datos suficientes para correlacionar</td></tr>'
    except Exception as _ve_exc:
        logger.warning("  Validación externa: %s", _ve_exc)
        _ve_rows_html = f'<tr><td colspan="5" style="color:var(--muted)">Error: {_ve_exc}</td></tr>'
    _validacion_externa_rows = _ve_rows_html

    # ── Validación externa: eventos políticos venezolanos vs Δ ICIV ───────────
    # Cada evento tiene una dirección esperada (↓ crisis, ↑ recuperación).
    # Se computa el delta real ICIV(año) - ICIV(año-1) y se valida si la
    # dirección coincide con la esperada.
    _eventos_pol = [
        (2002, "Golpe de Estado + Paro Petrolero", "↓"),
        (2007, "Cierre RCTV · nacionalización masiva", "↓"),
        (2014, "Protestas masivas · primeras sanciones EE.UU.", "↓"),
        (2017, "ANC constituyente · endurecimiento financiero externo", "↓"),
        (2019, "Dual gobierno Maduro-Guaidó · hiperinflación", "↓"),
        (2021, "Recuperación gradual oil · dolarización informal", "↑"),
        (2024, "Elecciones presidenciales · escalada represión", "↓"),
    ]
    _ev_rows_html = ""
    _df_scores_by_year = df_ahp.set_index("año")["iciv_score"].to_dict()
    _n_validados = 0
    _n_total = 0
    for _yr, _evento, _dir_esp in _eventos_pol:
        _cur = _df_scores_by_year.get(_yr)
        _prev = _df_scores_by_year.get(_yr - 1)
        if _cur is None or _prev is None or pd.isna(_cur) or pd.isna(_prev):
            _delta_str = "—"
            _validacion_cell = '<span style="color:var(--muted)">Sin datos</span>'
        else:
            _delta = _cur - _prev
            _delta_str = f"{'+' if _delta >= 0 else ''}{_delta:.1f}"
            _dir_observada = "↑" if _delta >= 0 else "↓"
            _es_validado = (_dir_observada == _dir_esp)
            _n_total += 1
            if _es_validado:
                _n_validados += 1
                _validacion_cell = f'<span style="color:#2ecc71">✓ Validado ({_dir_observada} observado, {_dir_esp} esperado)</span>'
            else:
                _validacion_cell = f'<span style="color:#e67e22">✗ Divergencia ({_dir_observada} obs, {_dir_esp} esp)</span>'
            # Color del delta
            _delta_color = "#e05c5c" if _delta < 0 else "#2ecc71"
            _delta_str = f'<span style="color:{_delta_color};font-weight:600">{_delta_str}</span>'
        _ev_rows_html += (
            f'<tr><td>{_yr}</td><td>{_evento}</td>'
            f'<td>{_delta_str}</td><td>{_validacion_cell}</td></tr>'
        )
    _eventos_validados_html = _ev_rows_html
    _eventos_resumen = (f"<strong style='color:#2ecc71'>{_n_validados}/{_n_total}</strong> eventos validados"
                        if _n_total > 0 else "Sin datos suficientes")

    # ── Simulacion probabilistica retirada — JSON ────────────────────────────────────────────────────
    _mc = mc_data or {}
    mc_json = json.dumps(_mc, cls=_NumpyEncoder, ensure_ascii=False)

    # ── Sector Radar — JSON + HTML server-side ───────────────────────────────
    # ── ICIV Pulse Mensual — preparar JSON para dashboard ────────────────────
    _pulse_payload: dict = {"meses": [], "scores": [], "cobertura": [], "n_vars": []}
    _pulse_summary: dict = {"n_meses": 0, "score_actual": None, "categoria": "",
                            "color": "#8b949e", "fecha_actual": ""}
    if pulse_data is not None and not pulse_data.empty:
        _p = pulse_data.copy()
        _p["mes_str"] = _p["año"].astype(str) + "-" + _p["mes"].astype(str).str.zfill(2)
        _pulse_payload = {
            "meses":      _p["mes_str"].tolist(),
            "scores":     [round(float(s), 2) if pd.notna(s) else None
                          for s in _p["pulse_score"].tolist()],
            "cobertura":  [round(float(c), 1) for c in _p["cobertura_pct"].tolist()],
            "n_vars":     [int(n) for n in _p["n_vars"].tolist()],
        }
        # Resumen dual: último mes disponible + último mes con cobertura alta.
        _p_reliable = _p[_p["cobertura_pct"] >= 70]
        _p_latest = _p.iloc[-1]
        _p_ref = _p_reliable.iloc[-1] if not _p_reliable.empty else _p_latest
        _ps = float(_p_latest["pulse_score"]) if pd.notna(_p_latest["pulse_score"]) else None
        _prs = float(_p_ref["pulse_score"]) if pd.notna(_p_ref["pulse_score"]) else None
        _latest_reliable = bool(float(_p_latest["cobertura_pct"]) >= 70)
        _pulse_summary = {
            "n_meses":      len(_p),
            "score_actual": round(_ps, 2) if _ps is not None else None,
            "categoria":    (_score_to_label(_ps) if _latest_reliable else "Provisional") if _ps is not None else "Sin datos",
            "color":        (_score_to_color(_ps) if _latest_reliable else "#e6a817") if _ps is not None else "#8b949e",
            "fecha_actual": _p_latest["mes_str"],
            "cobertura":    round(float(_p_latest["cobertura_pct"]), 1),
            "es_confiable": _latest_reliable,
            "score_confiable": round(_prs, 2) if _prs is not None else None,
            "categoria_confiable": _score_to_label(_prs) if _prs is not None else "Sin datos",
            "color_confiable": _score_to_color(_prs) if _prs is not None else "#8b949e",
            "fecha_confiable": _p_ref["mes_str"],
            "cobertura_confiable": round(float(_p_ref["cobertura_pct"]), 1),
        }
    pulse_json = json.dumps({"data": _pulse_payload, "summary": _pulse_summary},
                            cls=_NumpyEncoder, ensure_ascii=False)

    # Pulse components (15 series mensuales normalizadas)
    _pulse_comp_payload: dict = {"meses": [], "componentes": {}}
    _pulse_comp_path = settings.paths.data_processed / "iciv_pulse_components.csv"
    if _pulse_comp_path.exists():
        try:
            _pc = pd.read_csv(_pulse_comp_path)
            _pc["mes_str"] = _pc["año"].astype(str) + "-" + _pc["mes"].astype(str).str.zfill(2)
            _pulse_comp_payload["meses"] = _pc["mes_str"].tolist()
            from iciv.index.pulse_aggregator import PULSE_WEIGHTS as _PW
            for var in _PW.keys():
                if var in _pc.columns:
                    _pulse_comp_payload["componentes"][var] = [
                        round(float(v), 2) if pd.notna(v) else None
                        for v in _pc[var].tolist()
                    ]
        except Exception as _pe:
            logger.warning(f"  Pulse components load failed: {_pe}")
    pulse_components_json = json.dumps(_pulse_comp_payload, ensure_ascii=False)

    # Comercio espejo multi-socio (IMTS EEUU + Comtrade 5 socios) — capa contextual
    _mirror_payload: dict = {"meses": [], "imts_imp": [], "imts_exp": [], "ct_imp": [], "ct_exp": []}
    try:
        def _mirror_series(path: Path, var: str) -> dict:
            _df = pd.read_csv(path)
            _df = _df[_df["variable"] == var]
            return {
                f"{int(r['año'])}-{int(r['mes']):02d}": round(float(r["valor"]), 1)
                for _, r in _df.iterrows()
            }
        _mirror_sources = {}
        _imts_path = settings.paths.data_raw / "imts_monthly.csv"
        _ct_path   = settings.paths.data_raw / "comtrade_monthly.csv"
        if _imts_path.exists():
            _mirror_sources["imts_imp"] = _mirror_series(_imts_path, "importaciones_espejo_usa_musd")
            _mirror_sources["imts_exp"] = _mirror_series(_imts_path, "exportaciones_espejo_usa_musd")
        if _ct_path.exists():
            _mirror_sources["ct_imp"] = _mirror_series(_ct_path, "importaciones_espejo_socios_musd")
            _mirror_sources["ct_exp"] = _mirror_series(_ct_path, "exportaciones_espejo_socios_musd")
        if _mirror_sources:
            _mm = sorted(set().union(*[set(s) for s in _mirror_sources.values()]))
            _mirror_payload["meses"] = _mm
            for _k in ("imts_imp", "imts_exp", "ct_imp", "ct_exp"):
                _s = _mirror_sources.get(_k, {})
                _mirror_payload[_k] = [_s.get(m) for m in _mm]
    except Exception as _me:
        logger.warning(f"  Mirror trade payload failed: {_me}")
    mirror_trade_json = json.dumps(_mirror_payload, ensure_ascii=False)

    # Black Marble — luminosidad nocturna mensual (VNP46A3): media + log-media + Li et al.
    _bm_payload: dict = {"meses": [], "mensual": [], "robusta": [], "anual_meses": [], "anual_li": []}
    try:
        _bm_path = settings.paths.data_raw / "blackmarble_monthly.csv"
        if _bm_path.exists():
            _bm = pd.read_csv(_bm_path)
            def _bm_series(_var):
                _s = _bm[_bm["variable"] == _var].sort_values(["año", "mes"])
                return {f"{int(r['año'])}-{int(r['mes']):02d}": round(float(r["valor"]), 4)
                        for _, r in _s.iterrows()}
            _mean_s = _bm_series("luminosidad_nocturna_mensual_nwcm2sr")
            _rob_s  = _bm_series("luminosidad_nocturna_logmedia")
            _meses = sorted(set(_mean_s) | set(_rob_s))
            _bm_payload["meses"] = _meses
            _bm_payload["mensual"] = [_mean_s.get(m) for m in _meses]
            _bm_payload["robusta"] = [_rob_s.get(m) for m in _meses] if _rob_s else []
            # Serie anual Li et al. (VIIRS armonizado) reescalada al eje de la media
            _li = pd.read_csv(settings.paths.raw_viirs)
            _mean_vals = [v for v in _mean_s.values()]
            if _mean_vals:
                _y0 = int(min(m[:4] for m in _meses)); _y1 = int(max(m[:4] for m in _meses))
                _li = _li[(_li["año"] >= _y0) & (_li["año"] <= _y1)]
                _mm = sum(_mean_vals) / len(_mean_vals)
                if not _li.empty and _li["valor"].mean() > 0:
                    _scale = _mm / float(_li["valor"].mean())
                    for _, _r in _li.iterrows():
                        _bm_payload["anual_meses"].append(f"{int(_r['año'])}-06")
                        _bm_payload["anual_li"].append(round(float(_r["valor"]) * _scale, 4))
    except Exception as _be:
        logger.warning(f"  Black Marble payload failed: {_be}")
    blackmarble_json = json.dumps(_bm_payload, ensure_ascii=False)

    # Mapa coroplético subnacional Black Marble (radiancia por estado y año)
    _bmmap: dict = {"viewbox": [1000, 700], "estados": [], "years": [], "radiance": {}, "vmax": 1.0}
    try:
        _st_path = settings.paths.data_raw / "blackmarble_states_monthly.csv"
        _geojson_bm = settings.paths.data_raw / "venezuela_states.geojson"
        if _st_path.exists() and _geojson_bm.exists():
            _gj = json.loads(_geojson_bm.read_text(encoding="utf-8"))
            _feats = _gj.get("features", [])
            # bbox para proyección equirectangular
            _lons, _lats = [], []
            for _f in _feats:
                _g = _f.get("geometry") or {}
                _polys = ([_g["coordinates"]] if _g.get("type") == "Polygon"
                          else _g.get("coordinates", []) if _g.get("type") == "MultiPolygon" else [])
                for _poly in _polys:
                    for _ring in _poly:
                        for _pt in _ring:
                            _lons.append(_pt[0]); _lats.append(_pt[1])
            _lo0, _lo1, _la0, _la1 = min(_lons), max(_lons), min(_lats), max(_lats)
            _W = 1000.0
            _H = round(_W * (_la1 - _la0) / (_lo1 - _lo0))
            _bmmap["viewbox"] = [int(_W), int(_H)]

            def _proj(pt):
                x = (pt[0] - _lo0) / (_lo1 - _lo0) * _W
                y = (_la1 - pt[1]) / (_la1 - _la0) * _H
                return f"{x:.1f},{y:.1f}"

            for _f in _feats:
                _g = _f.get("geometry") or {}
                _polys = ([_g["coordinates"]] if _g.get("type") == "Polygon"
                          else _g.get("coordinates", []) if _g.get("type") == "MultiPolygon" else [])
                _d = []
                for _poly in _polys:
                    for _ring in _poly:
                        if len(_ring) < 3:
                            continue
                        _d.append("M" + "L".join(_proj(p) for p in _ring[::2]) + "Z")
                _bmmap["estados"].append({
                    "cod": _f["properties"].get("cod", ""),
                    "nombre": _f["properties"].get("nombre", ""),
                    "d": "".join(_d),
                })

            _st = pd.read_csv(_st_path)
            _st_annual = _st.groupby(["año", "cod"])["radiancia_media"].mean().reset_index()
            _years = sorted(_st_annual["año"].unique())
            _bmmap["years"] = [int(y) for y in _years]
            for _y in _years:
                _sub = _st_annual[_st_annual["año"] == _y]
                _bmmap["radiance"][str(int(_y))] = {
                    r["cod"]: round(float(r["radiancia_media"]), 3) for _, r in _sub.iterrows()
                }
            _allvals = _st_annual["radiancia_media"].values
            _bmmap["vmax"] = round(float(np.percentile(_allvals, 95)), 3) if len(_allvals) else 1.0
    except Exception as _mpe:
        logger.warning(f"  Black Marble map payload failed: {_mpe}")
    blackmarble_map_json = json.dumps(_bmmap, ensure_ascii=False)

    # ── ML Forecast (SARIMA + Nowcast) ────────────────────────────────────────
    _ml_payload = ml_forecast or {}
    ml_forecast_json = json.dumps(_ml_payload, cls=_NumpyEncoder, ensure_ascii=False)

    # Noticias internacionales: snapshot RSS filtrado server-side.
    _intl_news: list[dict] = []
    try:
        _news_path = settings.paths.raw_international_news
        if _news_path.exists() and _news_path.stat().st_size > 40:
            _news_df = pd.read_csv(_news_path).fillna("")
            _news_df = _news_df.head(24)
            _intl_news = _news_df.to_dict("records")
    except Exception as _ne:
        logger.warning(f"  International news load failed: {_ne}")
    intl_news_json = json.dumps(_intl_news, cls=_NumpyEncoder, ensure_ascii=False)

    _sector = sector_data or {}
    sector_json = json.dumps(_sector, cls=_NumpyEncoder, ensure_ascii=False)
    _sector_year = _sector.get("año_actual", int(last_row["año"]))

    # ── Venezuela Hoy: panel de indicadores clave (high-frequency + anuales) ──
    _MONTHS_ES = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    _ven_hoy: dict = {}
    try:
        # === ICIV Anual ===
        _dfa_nn = df_ahp.dropna(subset=["iciv_score"])
        if not _dfa_nn.empty:
            _dfa_reliable = (
                _dfa_nn[_dfa_nn["cobertura_pct"] >= 70]
                if "cobertura_pct" in _dfa_nn.columns else _dfa_nn
            )
            _vi = _dfa_nn.iloc[-1]
            _vr = _dfa_reliable.iloc[-1] if not _dfa_reliable.empty else _vi
            _vp = _dfa_nn.iloc[-2] if len(_dfa_nn) >= 2 else _vi
            _vi_cov = round(float(_vi.get("cobertura_pct", 100)), 1) \
                if "cobertura_pct" in _dfa_nn.columns else None
            _vi_reliable = bool((_vi_cov or 100) >= 70)
            _ven_hoy["iciv"] = {
                "score": round(float(_vi["iciv_score"]), 2),
                "year": int(_vi["año"]),
                "label": (
                    _score_to_label(float(_vi["iciv_score"]))
                    if _vi_reliable else f"Provisional · {_score_to_label(float(_vi['iciv_score']))}"
                ),
                "color": _score_to_color(float(_vi["iciv_score"])),
                "delta": round(float(_vi["iciv_score"]) - float(_vp["iciv_score"]), 2)
                         if len(_dfa_nn) >= 2 else None,
                "coverage": _vi_cov,
                "is_reliable": _vi_reliable,
                "reliable_score": round(float(_vr["iciv_score"]), 2),
                "reliable_year": int(_vr["año"]),
                "reliable_label": _score_to_label(float(_vr["iciv_score"])),
                "reliable_coverage": round(float(_vr.get("cobertura_pct", 100)), 1)
                                     if "cobertura_pct" in _dfa_nn.columns else None,
            }
        # === ICIV Pulse ===
        if pulse_data is not None and not pulse_data.empty:
            _pp = pulse_data.dropna(subset=["pulse_score"])
            if not _pp.empty:
                _pp_reliable = _pp[_pp["cobertura_pct"] >= 70] if "cobertura_pct" in _pp.columns else _pp
                _pl = _pp.iloc[-1]
                _pr = _pp_reliable.iloc[-1] if not _pp_reliable.empty else _pl
                _prev_base = _pp_reliable if len(_pp_reliable) >= 2 else _pp
                _ven_hoy["pulse"] = {
                    "score": round(float(_pl["pulse_score"]), 2),
                    "year": int(_pl["año"]),
                    "month": int(_pl["mes"]),
                    "label_mes": _MONTHS_ES[int(_pl["mes"])],
                    "coverage": round(float(_pl.get("cobertura_pct", 0)), 1)
                                if "cobertura_pct" in pulse_data.columns else None,
                    "delta": round(float(_pl["pulse_score"]) - float(_prev_base.iloc[-2]["pulse_score"]), 2)
                             if len(_prev_base) >= 2 else None,
                    "is_reliable": bool(float(_pl.get("cobertura_pct", 100)) >= 70)
                                   if "cobertura_pct" in pulse_data.columns else True,
                    "reliable_score": round(float(_pr["pulse_score"]), 2),
                    "reliable_year": int(_pr["año"]),
                    "reliable_month": int(_pr["mes"]),
                    "reliable_label_mes": _MONTHS_ES[int(_pr["mes"])],
                    "reliable_coverage": round(float(_pr.get("cobertura_pct", 0)), 1)
                                         if "cobertura_pct" in pulse_data.columns else None,
                }
        # === FRED Monthly (WTI, Brent, VIX, UST10Y, USD Index, Fed Funds) ===
        _fred_path = _ROOT / "data" / "raw" / "fred_monthly.csv"
        if _fred_path.exists():
            _fdf = pd.read_csv(_fred_path, encoding="utf-8-sig")
            _fdf.columns = ["año","mes","variable","valor","fuente"]
            _fdf["valor"] = pd.to_numeric(_fdf["valor"], errors="coerce")
            _fdf = _fdf.dropna(subset=["valor"])
            for _fvar, _fkey in [
                ("wti_precio_usd",    "wti"),
                ("brent_precio_usd",  "brent"),
                ("vix_volatility",    "vix"),
                ("ust_10y_yield_pct", "ust10y"),
                ("usd_index_broad",   "usd_index"),
                ("tasa_fed_funds_pct","fed_funds"),
            ]:
                _fs = _fdf[_fdf["variable"] == _fvar].sort_values(["año","mes"])
                if _fs.empty:
                    continue
                _fl = _fs.iloc[-1]
                _fp = _fs.iloc[-13] if len(_fs) >= 13 else None
                _ven_hoy[_fkey] = {
                    "valor": round(float(_fl["valor"]), 2),
                    "año": int(_fl["año"]),
                    "mes": int(_fl["mes"]),
                    "label_mes": _MONTHS_ES[int(_fl["mes"])],
                    "delta_12m": round(float(_fl["valor"]) - float(_fp["valor"]), 2)
                                 if _fp is not None else None,
                }
        # === EIA Monthly (producción petróleo Venezuela) ===
        _eia_path = _ROOT / "data" / "raw" / "eia_monthly.csv"
        if _eia_path.exists():
            _edf = pd.read_csv(_eia_path, encoding="utf-8-sig")
            _edf.columns = ["año","mes","productId","productName","variable","valor","unidad","fuente"]
            _edf["valor"] = pd.to_numeric(_edf["valor"], errors="coerce")
            _ev = _edf[_edf["variable"] == "petroleo_crudo_produccion_tbpd"].sort_values(["año","mes"])
            if not _ev.empty:
                _el = _ev.iloc[-1]
                _ep = _ev.iloc[-13] if len(_ev) >= 13 else None
                _ven_hoy["petroleo_ven"] = {
                    "valor": round(float(_el["valor"]), 0),
                    "año": int(_el["año"]),
                    "mes": int(_el["mes"]),
                    "label_mes": _MONTHS_ES[int(_el["mes"])],
                    "delta_12m": round(float(_el["valor"]) - float(_ep["valor"]), 0)
                                 if _ep is not None else None,
                }
        # === Inflación real (desde CSV IMF, sin log10) ===
        _imf_path = _ROOT / "data" / "raw" / "imf.csv"
        if _imf_path.exists():
            _imf = pd.read_csv(_imf_path)
            _imf.columns = [c.strip() for c in _imf.columns]
            _icol = [c for c in _imf.columns if "a" in c.lower() and "o" in c.lower()][0]
            _imf = _imf.rename(columns={_icol: "año"})
            if "inflacion_deflactor_pib_pct" in _imf.columns:
                _inf = _imf[_imf["inflacion_deflactor_pib_pct"].notna()].sort_values("año")
                if not _inf.empty:
                    _il = _inf.iloc[-1]
                    _ip = _inf.iloc[-2] if len(_inf) >= 2 else None
                    _ven_hoy["inflacion"] = {
                        "valor": round(float(_il["inflacion_deflactor_pib_pct"]), 1),
                        "año": int(_il["año"]),
                        "delta": round(float(_il["inflacion_deflactor_pib_pct"])
                                       - float(_ip["inflacion_deflactor_pib_pct"]), 1)
                                 if _ip is not None else None,
                    }
            if "pib_crecimiento_imf_pct" in _imf.columns:
                _pg = _imf[_imf["pib_crecimiento_imf_pct"].notna()].sort_values("año")
                if not _pg.empty:
                    _pl2 = _pg.iloc[-1]
                    _pp2 = _pg.iloc[-2] if len(_pg) >= 2 else None
                    _ven_hoy["pib_crec"] = {
                        "valor": round(float(_pl2["pib_crecimiento_imf_pct"]), 1),
                        "año": int(_pl2["año"]),
                        "delta": round(float(_pl2["pib_crecimiento_imf_pct"])
                                       - float(_pp2["pib_crecimiento_imf_pct"]), 1)
                                 if _pp2 is not None else None,
                    }
        # === Variables anuales desde df_raw ===
        for _vc, _vk in [
            ("freedom_house_score",    "fh"),
            ("cpi_score",              "cpi"),
            ("wgi_promedio_sc",        "wgi"),
            ("migrantes_vzla_millones","migrantes"),
            ("hdi",                    "hdi"),
            ("pib_crecimiento_real_pct","pib_crec"),  # fill si IMF no disponible
        ]:
            if _vk in _ven_hoy:
                continue  # ya calculado arriba
            if _vc not in df_raw.columns:
                continue
            _vs = df_raw[[_vc,"año"]].dropna(subset=[_vc]).sort_values("año")
            if _vs.empty:
                continue
            _vl = _vs.iloc[-1]
            _vp = _vs.iloc[-2] if len(_vs) >= 2 else None
            _ven_hoy[_vk] = {
                "valor": round(float(_vl[_vc]), 2),
                "año": int(_vl["año"]),
                "delta": round(float(_vl[_vc]) - float(_vp[_vc]), 2)
                         if _vp is not None else None,
            }
    except Exception as _vhe:
        logger.warning("  Venezuela Hoy data error: %s", _vhe)

    ven_hoy_json = json.dumps(_ven_hoy, cls=_NumpyEncoder, ensure_ascii=False)
    _sector_iciv  = _sector.get("iciv_actual", round(float(last_row["iciv_score"]), 1))

    # Generar HTML del sector directamente en Python (server-side rendering)
    _sector_ranking = _sector.get("ranking", [])
    _sector_resumen = _sector.get("resumen_categorias", {})
    _sector_labels  = _sector.get("sector_labels", {})
    _sector_met     = _sector.get("metodologia", "")

    # KPI strip — 5 tarjetas de categoría
    _KPI_CATS = [
        ("PRIORITARIA", "Prioritaria", "#00d4aa"),
        ("ENTRADA",     "Entrada",     "#2ecc71"),
        ("PILOTO",      "Piloto",      "#f1c40f"),
        ("ESPERAR",     "Esperar",     "#e67e22"),
        ("NO ENTRAR",   "No entrar",   "#e05c5c"),
    ]
    _kpi_html = "".join(
        f'<div style="background:var(--card);border:1px solid {hex_}44;border-radius:10px;'
        f'padding:14px;text-align:center">'
        f'<div style="font-size:.7rem;color:var(--muted);margin-bottom:4px">{label}</div>'
        f'<div style="font-size:1.8rem;font-weight:700;color:{hex_};line-height:1">'
        f'{_sector_resumen.get(short, 0)}</div>'
        f'<div style="font-size:.65rem;color:var(--muted);margin-top:2px">sector(es)</div>'
        f'</div>'
        for short, label, hex_ in _KPI_CATS
    )

    # Tabla de ranking — filas
    _SECTOR_COLORS = [
        "#00d4aa","#3498db","#2ecc71","#e67e22","#e74c3c",
        "#9b59b6","#f1c40f","#1abc9c","#e91e63","#ff5722",
    ]
    _table_rows_html = ""
    for r in _sector_ranking:
        score = r.get("score")
        score_label = f"{score:.1f}" if score is not None else "N/D"
        bar_width = f"{score:.1f}%" if score is not None else "0"
        bar = (f'<div style="width:{bar_width};max-width:100%;height:6px;'
               f'background:{r["hex"]};border-radius:3px;margin-top:3px"></div>')
        _table_rows_html += (
            f'<tr style="border-bottom:1px solid var(--border);cursor:pointer" '
            f'data-sid="{r["sector_id"]}" onclick="sectorShowHist(this.dataset.sid)">'
            f'<td style="padding:10px 14px;color:var(--muted);font-size:.72rem">{r["rank"]}</td>'
            f'<td style="padding:10px 14px;color:var(--text);font-weight:600">{r["label"]}</td>'
            f'<td style="padding:10px 14px;text-align:center">'
            f'<div style="font-size:1.05rem;font-weight:700;color:{r["hex"]}">{score_label}</div>'
            f'{bar}</td>'
            f'<td style="padding:10px 14px">'
            f'<span style="background:{r["hex"]}22;color:{r["hex"]};border:1px solid {r["hex"]}55;'
            f'border-radius:4px;padding:2px 8px;font-size:.68rem;font-weight:600;white-space:nowrap">'
            f'{r["recomendacion_short"]}</span></td>'
            f'<td style="padding:10px 14px;color:var(--muted);font-size:.72rem;white-space:nowrap">'
            f'{r["riesgo_principal"]}</td>'
            f'<td style="padding:10px 14px;color:var(--muted);font-size:.70rem;max-width:280px;'
            f'line-height:1.4">{r["racional"]}</td>'
            f'</tr>'
        )

    # Toggle buttons
    _toggle_btns_html = ""
    for i, (sid, slabel) in enumerate(_sector_labels.items()):
        c = _SECTOR_COLORS[i % len(_SECTOR_COLORS)]
        active = i < 4
        bg  = f"{c}33" if active else "transparent"
        col = c if active else "#8b949e"
        brd = c if active else "#444"
        _toggle_btns_html += (
            f'<button data-sid="{sid}" data-idx="{i}" '
            f'onclick="sectorShowHist(this.dataset.sid)" '
            f'style="background:{bg};color:{col};border:1px solid {brd};'
            f'border-radius:4px;padding:3px 10px;font-size:.68rem;cursor:pointer;transition:all .2s">'
            f'{slabel}</button>'
        )

    # ── Mapa — cargar GeoJSON + NTL por estado ────────────────────────────────
    _geojson_str, _viirs_states_json = _load_map_data(settings)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ICIV — Indicador de Clima de Inversión Venezuela</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<style>
:root{{
  --bg:#0d1117;--card:#1c2128;--border:#30363d;
  --text:#e6edf3;--muted:#8b949e;--accent:#00d4aa;
  --red:#e05c5c;--orange:#e67e22;--yellow:#f1c40f;--green:#2ecc71;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}

/* nav — sistema de 2 niveles */
.nav-wrap{{position:sticky;top:0;z-index:100;background:#161b22;
           border-bottom:1px solid var(--border);box-shadow:0 2px 8px rgba(0,0,0,.25)}}

/* Top nav: 5 pestañas principales */
.nav-top{{display:flex;align-items:center;gap:4px;padding:0 32px;height:54px;
         border-bottom:1px solid #21262d}}
.nav-brand{{color:var(--accent);font-weight:700;font-size:1rem;margin-right:28px;
            letter-spacing:.4px;cursor:pointer;text-decoration:none;
            transition:opacity .15s}}
.nav-brand:hover{{opacity:.75}}
.nav-top a{{color:var(--muted);text-decoration:none;font-size:.78rem;font-weight:600;
            padding:8px 18px;border-radius:8px;transition:all .18s;
            text-transform:uppercase;letter-spacing:.6px;border:1px solid transparent}}
.nav-top a:hover{{color:var(--text);background:rgba(255,255,255,.04);
                  border-color:var(--border)}}
.nav-top a.nav-top-active{{color:#0d1117;background:var(--accent);
                           border-color:var(--accent);font-weight:700}}

/* Sub-nav: contiene las pestañas internas de cada bloque principal */
.nav-sub{{display:none;align-items:center;gap:0;padding:0 32px;height:42px;
         background:#0d1117;overflow-x:auto}}
.nav-sub.nav-sub-active{{display:flex}}
.nav-sub a{{color:var(--muted);text-decoration:none;font-size:.74rem;font-weight:500;
           padding:0 14px;height:42px;display:flex;align-items:center;
           border-bottom:3px solid transparent;
           transition:color .18s,border-color .22s,background .18s;
           white-space:nowrap;border-radius:0;position:relative}}
.nav-sub a:hover{{color:var(--text);background:rgba(255,255,255,.04)}}
.nav-sub a.active{{color:var(--accent);border-bottom-color:var(--accent);font-weight:600;
                   background:rgba(0,212,170,.05)}}

/* header */
.header{{padding:40px 40px 32px;background:linear-gradient(135deg,#161b22 0%,#1c2128 100%);
         border-bottom:1px solid var(--border)}}
.header h1{{font-size:1.9rem;font-weight:700;letter-spacing:-.5px;line-height:1.2}}
.header h1 span{{color:var(--accent)}}
.header .sub{{color:var(--muted);font-size:.88rem;margin-top:6px}}
.badges{{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}}
.badge{{background:rgba(255,255,255,.06);border:1px solid var(--border);
        padding:4px 12px;border-radius:20px;font-size:.74rem;color:var(--muted)}}

/* section */
.section{{padding:32px 40px;border-bottom:1px solid var(--border);scroll-margin-top:100px}}

/* Links de bibliografía — color visible, con subrayado */
#bibliografia a{{color:var(--accent);text-decoration:underline;text-underline-offset:3px;
                 text-decoration-color:rgba(0,212,170,.4);transition:color .15s,text-decoration-color .15s}}
#bibliografia a:hover{{color:#00f5c2;text-decoration-color:var(--accent)}}
.section-header{{display:flex;align-items:baseline;gap:12px;margin-bottom:24px;
                 flex-wrap:wrap}}
.section-title{{font-size:.72rem;font-weight:700;color:var(--text);text-transform:uppercase;
                letter-spacing:.8px;opacity:.85}}
.section-sub{{font-size:.76rem;color:var(--muted);line-height:1.5}}

/* portada pillar cards */
.portada-pillar{{padding:28px 30px;border-right:1px solid var(--border)}}
.portada-pillar:last-child{{border-right:none}}
.portada-pillar-bar{{height:3px;border-radius:2px;margin-bottom:14px;width:32px}}
.portada-pillar-title{{font-size:.88rem;font-weight:600;color:var(--text);margin-bottom:8px}}
.portada-pillar-body{{font-size:.77rem;color:var(--muted);line-height:1.65}}
.portada-stat{{padding:22px 28px;text-align:center;border-right:1px solid var(--border)}}
.portada-stat:last-child{{border-right:none}}
.portada-stat-num{{font-size:2.2rem;font-weight:800;line-height:1;margin-bottom:5px}}
.portada-stat-lbl{{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}}
.portada-cta{{display:inline-flex;align-items:center;gap:8px;background:var(--accent);
              color:#0d1117;border:none;border-radius:8px;padding:11px 24px;
              font-size:.85rem;font-weight:700;cursor:pointer;font-family:'Inter',sans-serif;
              transition:opacity .15s;text-decoration:none}}
.portada-cta:hover{{opacity:.85}}
.portada-cta-sec{{display:inline-flex;align-items:center;gap:8px;background:transparent;
                  color:var(--text);border:1px solid var(--border);border-radius:8px;
                  padding:10px 22px;font-size:.85rem;cursor:pointer;
                  font-family:'Inter',sans-serif;transition:border-color .15s,color .15s;
                  text-decoration:none}}
.portada-cta-sec:hover{{border-color:var(--accent);color:var(--accent)}}

/* stats row */
.stats-row{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px}}
.stat{{background:var(--card);border:1px solid var(--border);border-radius:10px;
       padding:16px 20px;flex:1;min-width:130px}}
.stat-label{{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px}}
.stat-val{{font-size:1.7rem;font-weight:700;line-height:1}}
.stat-up{{color:var(--green)}}
.stat-down{{color:var(--red)}}
.stat-neu{{color:var(--accent)}}
.stat-sub{{font-size:.72rem;color:var(--muted);margin-top:4px}}

/* chart cards */
.charts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.charts-grid.single{{grid-template-columns:1fr}}
.chart-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px}}
.chart-card.wide{{grid-column:span 2}}
.ct{{font-size:.78rem;font-weight:600;color:var(--text);margin-bottom:2px}}
.cs{{font-size:.7rem;color:var(--muted);margin-bottom:16px}}
.chart-wrap{{position:relative}}

/* gauge */
.gauge-wrap{{display:flex;flex-direction:column;align-items:center;padding:24px 0 8px}}
.gauge-svg{{width:220px;height:130px}}
.gauge-value{{font-size:2.8rem;font-weight:700;line-height:1;text-align:center;margin-top:8px}}
.gauge-label{{font-size:.78rem;color:var(--muted);text-align:center;margin-top:4px}}
.gauge-cat{{font-size:.85rem;font-weight:600;text-align:center;margin-top:6px}}

/* Score Actual — year selector */
.score-year-tabs{{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:16px;
                  border-bottom:1px solid var(--border);padding-bottom:12px}}
.score-yr-btn{{background:transparent;border:1px solid var(--border);color:var(--muted);
               border-radius:6px;padding:3px 9px;font-size:.72rem;cursor:pointer;
               transition:all .15s;white-space:nowrap}}
.score-yr-btn:hover{{border-color:var(--accent);color:var(--accent)}}
.score-yr-btn.score-yr-active{{background:var(--accent);border-color:var(--accent);
                                color:#0d1117;font-weight:600}}

/* risk bands sidebar */
.risk-bands{{display:flex;flex-direction:column;gap:4px;margin-top:8px}}
.rb{{display:flex;align-items:center;gap:10px;padding:6px 10px;border-radius:6px;
     font-size:.74rem;border:1px solid transparent}}
.rb-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.rb.active{{border-color:currentColor;background:rgba(255,255,255,.04)}}

/* AHP table */
.ahp-table{{width:100%;border-collapse:collapse;font-size:.82rem}}
.ahp-table th{{text-align:left;padding:8px 12px;font-size:.68rem;color:var(--muted);
               text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border)}}
.ahp-table td{{padding:8px 12px;border-bottom:1px solid #21262d;vertical-align:middle}}
.ahp-table tr:last-child td{{border-bottom:none}}
.cr-badge{{display:inline-block;background:#00d4aa22;color:var(--accent);border:1px solid #00d4aa44;
           padding:2px 10px;border-radius:12px;font-size:.72rem;font-weight:600;margin-left:8px}}

/* history table */
.gap-table{{width:100%;border-collapse:collapse;font-size:.82rem}}
.gap-table th{{text-align:left;padding:8px 12px;font-size:.68rem;color:var(--muted);
               text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border)}}
.gap-table td{{padding:7px 12px;border-bottom:1px solid #21262d}}
.gap-table tr:last-child td{{border-bottom:none}}
.gap-table tbody tr:hover{{background:rgba(255,255,255,.03)}}
.pill{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:.72rem;font-weight:600}}

/* recommendation alert */
.alert{{border-radius:10px;padding:16px 20px;margin-bottom:20px;border:1px solid}}
.alert-warn{{background:#e67e2215;border-color:#e67e2240;color:#e67e22}}
.alert-info{{background:#00d4aa15;border-color:#00d4aa40;color:#00d4aa}}
.alert-bad{{background:#e05c5c15;border-color:#e05c5c40;color:#e05c5c}}
.alert-title{{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px}}
.alert-body{{font-size:.88rem;color:var(--text);line-height:1.55}}

/* satv */
.satv-kpi{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center}}
.satv-kpi-val{{font-size:2rem;font-weight:700;line-height:1}}
.satv-kpi-lbl{{font-size:.72rem;color:var(--muted);margin-top:6px;text-transform:uppercase;letter-spacing:.6px}}
.satv-alert{{display:flex;align-items:flex-start;gap:14px;background:var(--card);border:1px solid var(--border);
             border-radius:10px;padding:14px 18px}}
.satv-alert.critico{{border-left:4px solid var(--red)}}
.satv-alert.precaucion{{border-left:4px solid var(--orange)}}
.satv-alert.normal{{border-left:4px solid var(--green)}}
.satv-alert-icon{{font-size:1.4rem;line-height:1;padding-top:2px}}
.satv-alert-tipo{{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.7px;margin-bottom:4px}}
.satv-alert-msg{{font-size:.85rem;color:var(--text);line-height:1.55}}
.satv-dim-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px}}
.satv-dim-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}}
.satv-dim-name{{font-size:.82rem;font-weight:600}}
.satv-badge{{font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px;text-transform:uppercase}}
.satv-badge.critico{{background:#e05c5c22;color:#e05c5c;border:1px solid #e05c5c55}}
.satv-badge.precaucion{{background:#e67e2222;color:#e67e22;border:1px solid #e67e2255}}
.satv-badge.normal{{background:#2ecc7122;color:#2ecc71;border:1px solid #2ecc7155}}
.satv-badge.sin_dato{{background:#8b949e22;color:#8b949e;border:1px solid #8b949e55}}
.satv-dim-score{{font-size:1.6rem;font-weight:700;line-height:1}}
.satv-dim-deltas{{display:flex;gap:10px;margin-top:8px;font-size:.72rem;color:var(--muted)}}
.satv-dim-var{{font-size:.72rem;margin-top:8px;padding-top:8px;border-top:1px solid var(--border);color:var(--muted)}}
.satv-var-table{{width:100%;border-collapse:collapse;font-size:.82rem}}
.satv-var-table th{{text-align:left;padding:6px 8px;font-size:.68rem;color:var(--muted);
                   text-transform:uppercase;letter-spacing:.6px;border-bottom:1px solid var(--border)}}
.satv-var-table td{{padding:7px 8px;border-bottom:1px solid #21262d;vertical-align:middle}}
.satv-bar-mini{{height:6px;border-radius:3px;background:var(--accent);min-width:2px;transition:width .3s}}

/* news */
.news-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}}
.news-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden;
            display:flex;flex-direction:column;transition:border-color .2s}}
.news-card:hover{{border-color:var(--accent)}}
.news-thumb{{width:100%;height:160px;object-fit:cover;background:#21262d;display:block}}
.news-thumb-ph{{width:100%;height:80px;background:linear-gradient(135deg,#161d2b,#1d2430);display:flex;
                align-items:center;justify-content:center;font-size:1.5rem;opacity:.7}}
.news-thumb-ph::after{{content:'📰'}}
.news-srclinks{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}
.news-srclink{{font-size:.7rem;color:var(--muted);text-decoration:none;border-bottom:1px dotted var(--border);
               padding-bottom:1px;transition:color .2s}}
.news-srclink:hover{{color:var(--accent);border-bottom-color:var(--accent)}}
.news-srclink::after{{content:' ↗';font-size:.62rem;opacity:.7}}
.news-body{{padding:14px 16px;flex:1;display:flex;flex-direction:column;gap:6px}}
.news-section{{font-size:.65rem;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.8px}}
.news-title{{font-size:.9rem;font-weight:600;color:var(--text);line-height:1.4}}
.news-title a{{color:inherit;text-decoration:none}}
.news-title a:hover{{color:var(--accent)}}
.news-trail{{font-size:.78rem;color:var(--muted);line-height:1.5;flex:1}}
.news-date{{font-size:.68rem;color:var(--muted);margin-top:4px}}
.news-skeleton{{background:linear-gradient(90deg,#21262d 25%,#2d333b 50%,#21262d 75%);
                background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:4px}}
@keyframes shimmer{{0%{{background-position:200% 0}}100%{{background-position:-200% 0}}}}
.news-status{{padding:32px;text-align:center;color:var(--muted);font-size:.88rem}}
.news-filter{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}}
.news-chip{{background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:16px;
            padding:4px 14px;font-size:.74rem;color:var(--muted);cursor:pointer;transition:all .2s}}
.news-chip.active,.news-chip:hover{{background:rgba(0,212,170,.12);border-color:var(--accent);color:var(--accent)}}

/* ── tab switching ── */
.tab-section{{display:none}}
.tab-section.tab-active{{display:block}}

/* ── dimension detail cards ── */
.dim-detail-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.dim-detail-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 20px}}
.dim-detail-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;gap:12px}}
.dim-detail-id{{display:inline-block;background:rgba(0,212,170,.12);color:var(--accent);
                border:1px solid rgba(0,212,170,.3);border-radius:6px;
                font-size:.68rem;font-weight:700;padding:2px 8px;margin-right:8px}}
.dim-detail-name{{font-size:.85rem;font-weight:600;color:var(--text)}}
.dim-var-table{{width:100%;border-collapse:collapse;font-size:.78rem}}
.dim-var-table th{{text-align:left;padding:6px 8px;font-size:.65rem;color:var(--muted);
                   text-transform:uppercase;letter-spacing:.4px;border-bottom:1px solid var(--border)}}
.dim-var-table td{{padding:6px 8px;border-bottom:1px solid #21262d;vertical-align:middle}}
.dim-var-table tr:last-child td{{border-bottom:none}}
.dim-var-table tbody tr:hover{{background:rgba(255,255,255,.02)}}

/* ── dimension sub-tabs ── */
.dim-subtabs{{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:24px;padding:4px;
             background:#161b22;border:1px solid var(--border);border-radius:10px}}
.dim-stab{{background:transparent;border:1px solid transparent;color:var(--muted);
           font-family:'Inter',sans-serif;font-size:.78rem;font-weight:500;
           padding:7px 16px;border-radius:7px;cursor:pointer;transition:all .2s;white-space:nowrap}}
.dim-stab:hover{{color:var(--text);background:rgba(255,255,255,.05)}}
.dim-stab.dim-stab-active{{background:var(--card);color:var(--text);border-color:var(--border)}}
.dim-view{{display:none}}
.dim-view.dim-view-active{{display:block}}

@media(max-width:900px){{
  .dim-detail-grid{{grid-template-columns:1fr}}
  .dim-subtabs{{gap:4px}}
  .dim-stab{{font-size:.72rem;padding:6px 10px}}
}}

/* footer */
.footer{{text-align:center;padding:28px;font-size:.72rem;color:var(--muted);
         border-top:1px solid var(--border)}}

@media(max-width:900px){{
  .charts-grid{{grid-template-columns:1fr}}
  .chart-card.wide{{grid-column:span 1}}
  .section{{padding:24px 20px}}
  .header{{padding:24px 20px}}
  .nav{{padding:0 16px}}
}}
</style>
</head>
<body>

<!-- NAV de 2 niveles — estructura narrativa -->
<div class="nav-wrap">
  <div class="nav-top">
    <a class="nav-brand" href="#" onclick="event.preventDefault();showSection('portada')" title="Ir a portada">ICIV</a>
    <a href="#" data-block="inicio">Inicio</a>
    <a href="#" data-block="historia">Historia</a>
    <a href="#" data-block="diagnostico">Diagnóstico</a>
    <a href="#" data-block="proyeccion">Proyección</a>
    <a href="#" data-block="noticias">Noticias</a>
    <a href="#" data-block="metodologia">Metodología</a>
  </div>

  <div class="nav-sub nav-sub-active" data-block="portada">
    <!-- portada no necesita sub-nav: es una sección única -->
  </div>

  <div class="nav-sub" data-block="inicio">
    <a href="#inicio" class="active">Clima Actual</a>
    <a href="#ven-hoy">Venezuela Hoy</a>
    <a href="#score">ICIV Anual</a>
  </div>

  <div class="nav-sub" data-block="historia">
    <a href="#historia">Evolución 25 años</a>
    <a href="#pulse">Pulse Mensual</a>
    <a href="#pulse-componentes">Componentes Pulse</a>
    <a href="#pulse-metodologia">Metodología Pulse</a>
    <a href="#mapa">Actividad por Estado</a>
  </div>

  <div class="nav-sub" data-block="diagnostico">
    <a href="#dimensiones">Dimensiones</a>
    <a href="#alertas">Alertas SATV</a>
    <a href="#sectorial">Radar Sectorial</a>
  </div>

  <div class="nav-sub" data-block="proyeccion">
    <a href="#forecast-ml">Predicción Pulse</a>
    <a href="#forecast-metodologia">Metodología</a>
    <a href="#proyecciones">Laboratorio</a>
  </div>

  <div class="nav-sub" data-block="noticias">
    <!-- Noticias queda como pestaña principal sin submenú. -->
  </div>

  <div class="nav-sub" data-block="metodologia">
    <a href="#correlacion">Validación / Coherencia</a>
    <a href="#bibliografia">Bibliografía</a>
  </div>
</div>

<!-- ===== PORTADA — Introducción al proyecto ===== -->
<section class="tab-section tab-active" id="portada" style="border-bottom:1px solid var(--border)">

  <!-- Hero block -->
  <div style="padding:48px 40px 40px;background:linear-gradient(135deg,rgba(0,212,170,.04) 0%,rgba(52,152,219,.03) 50%,transparent 100%);border-bottom:1px solid var(--border)">
    <div style="margin-bottom:18px">
      <div style="font-size:1rem;font-weight:700;color:var(--text);margin-bottom:4px">Felipe Gómez Espinal</div>
      <div style="font-size:.68rem;color:var(--muted);letter-spacing:.3px">Tesis de Especialización · Big Data e Inteligencia de Negocios · Universidad EIA &nbsp;·&nbsp; {generated_at}</div>
    </div>
    <div style="display:flex;align-items:baseline;gap:18px;flex-wrap:wrap;margin-bottom:10px">
      <span style="font-size:3.2rem;font-weight:800;line-height:1;color:var(--accent);letter-spacing:-1px">ICIV</span>
      <span style="font-size:1.3rem;font-weight:300;color:var(--text);line-height:1.2;letter-spacing:-.2px">Indicador de Clima de Inversión Venezuela</span>
    </div>
    <p style="font-size:.88rem;color:var(--muted);max-width:700px;line-height:1.7;margin:0 0 26px">
      Un indicador reproducible del clima de inversión para Venezuela construido
      con datos satelitales e internacionales auditables, sin fuentes originadas en Venezuela.
      El ICIV anual describe la trayectoria estructural 2000–{settings.series.end_year}; el Pulse
      mensual monitorea señales de alta frecuencia desde 2010.
    </p>

    <!-- Scores actuales -->
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:30px">
      <div style="background:var(--card);border:1px solid var(--border);border-left:3px solid {current_color};
                  border-radius:8px;padding:12px 20px">
        <div style="font-size:.6rem;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-bottom:4px">ICIV Anual {current_year_val}</div>
        <div style="display:flex;align-items:baseline;gap:8px">
          <span style="font-size:1.5rem;font-weight:700;color:{current_color}">{current_score:.1f}</span>
          <span style="font-size:.75rem;color:{current_color}">{current_label}</span>
        </div>
        <div style="font-size:.68rem;color:var(--muted);margin-top:6px">
          {coverage_badge}{f" · último confiable: {annual_ref_year} · {annual_ref_score:.1f} · {annual_ref_coverage:.0f}% cob." if current_year_val != annual_ref_year else ""}
        </div>
      </div>
      <div id="portadaPCard" style="background:var(--card);border:1px solid var(--border);border-left:3px solid #8b949e;
                  border-radius:8px;padding:12px 20px">
        <div style="font-size:.6rem;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-bottom:4px">Pulse Mensual</div>
        <div style="display:flex;align-items:baseline;gap:8px">
          <span id="portadaPS" style="font-size:1.5rem;font-weight:700;color:#8b949e">—</span>
          <span id="portadaPF" style="font-size:.75rem;color:var(--muted)">—</span>
        </div>
        <div id="portadaPR" style="font-size:.68rem;color:var(--muted);margin-top:6px">—</div>
      </div>
    </div>

    <!-- CTAs -->
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      <a href="#" class="portada-cta-sec" onclick="event.preventDefault();showSection('inicio')">Ver clima actual</a>
      <a href="#" class="portada-cta-sec" onclick="event.preventDefault();showSection('historia')">25 años de historia</a>
      <a href="#" class="portada-cta-sec" onclick="event.preventDefault();showSection('dimensiones')">Ver diagnóstico</a>
    </div>
  </div>

  <!-- 3 Pilares diferenciadores -->
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;border-bottom:1px solid var(--border)">
    <div class="portada-pillar">
      <div class="portada-pillar-bar" style="background:var(--accent)"></div>
      <div class="portada-pillar-title">Datos satelitales VIIRS</div>
      <div class="portada-pillar-body">
        Luminosidad nocturna (Li et al.) como proxy de actividad económica.
        25 años de imágenes reales sin interpolación. Verificable con datos Figshare públicos.
      </div>
    </div>
    <div class="portada-pillar">
      <div class="portada-pillar-bar" style="background:#3498db"></div>
      <div class="portada-pillar-title">Frecuencia mensual — ICIV Pulse</div>
      <div class="portada-pillar-body">
        Señales mensuales desde enero 2010. El Pulse combina variables reales de
        FRED, EIA, Guardian y GDELT para leer el tramo entre publicaciones anuales.
      </div>
    </div>
    <div class="portada-pillar">
      <div class="portada-pillar-bar" style="background:#e74c3c"></div>
      <div class="portada-pillar-title">Cero datos venezolanos</div>
      <div class="portada-pillar-body">
        Ninguna variable del gobierno venezolano (BCV, INE, PDVSA).
        Todo construido con IMF · World Bank · EIA · UNHCR · The Guardian · Li et al.
        Reproducible y auditable.
      </div>
    </div>
  </div>

  <!-- Stats -->
  <div style="display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--border)">
    <div class="portada-stat">
      <div class="portada-stat-num" style="color:var(--accent)">25</div>
      <div class="portada-stat-lbl">años · 2000–{settings.series.end_year}</div>
    </div>
    <div class="portada-stat">
      <div class="portada-stat-num" style="color:#3498db">197</div>
      <div class="portada-stat-lbl">meses Pulse mensual</div>
    </div>
    <div class="portada-stat">
      <div class="portada-stat-num" style="color:var(--text)">26</div>
      <div class="portada-stat-lbl">variables · 6 dimensiones</div>
    </div>
    <div class="portada-stat">
      <div class="portada-stat-num" style="color:var(--text)">15+</div>
      <div class="portada-stat-lbl">fuentes internacionales</div>
    </div>
  </div>

  <!-- 6 Dimensiones + Metodología -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0;padding:32px 40px">
    <div style="border-right:1px solid var(--border);padding-right:36px">
      <div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin-bottom:16px">Las 6 dimensiones del ICIV</div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:#3498db;flex-shrink:0"></div><span style="font-size:.8rem;color:var(--text)">D1 Macroeconomía externa</span><span style="font-size:.7rem;color:var(--muted);margin-left:auto">35%</span></div>
        <div style="display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:#e67e22;flex-shrink:0"></div><span style="font-size:.8rem;color:var(--text)">D2 Energía Venezuela</span><span style="font-size:.7rem;color:var(--muted);margin-left:auto">25%</span></div>
        <div style="display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:#9b59b6;flex-shrink:0"></div><span style="font-size:.8rem;color:var(--text)">D3 Institucional</span><span style="font-size:.7rem;color:var(--muted);margin-left:auto">10%</span></div>
        <div style="display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:#1abc9c;flex-shrink:0"></div><span style="font-size:.8rem;color:var(--text)">D4 Comercial / Migración</span><span style="font-size:.7rem;color:var(--muted);margin-left:auto">15%</span></div>
        <div style="display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:#e74c3c;flex-shrink:0"></div><span style="font-size:.8rem;color:var(--text)">D5 Capital humano</span><span style="font-size:.7rem;color:var(--muted);margin-left:auto">10%</span></div>
        <div style="display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:#f39c12;flex-shrink:0"></div><span style="font-size:.8rem;color:var(--text)">D6 Percepción mediática</span><span style="font-size:.7rem;color:var(--muted);margin-left:auto">5%</span></div>
      </div>
    </div>
    <div style="padding-left:36px">
      <div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin-bottom:16px">Metodología y temporalidad</div>
      <div style="display:flex;flex-direction:column;gap:12px;font-size:.8rem;color:var(--muted)">
        <div><span style="color:var(--text);font-weight:600">ICIV Anual (oficial):</span> Datos 2000–{settings.series.end_year} · Pesos AHP (CR=0.008) · Normalización Min-Max · Score 0–100</div>
        <div><span style="color:var(--text);font-weight:600">ICIV Pulse (mensual):</span> 2010–{settings.series.end_year} · 15 variables mensuales · Pesos renormalizados según cobertura real · Stock &amp; Watson (2002)</div>
        <div><span style="color:var(--text);font-weight:600">Forecast:</span> SARIMA(1,1,2)(1,1,1,12) · 6 meses horizon · IC 80%/95%</div>
        <div><span style="color:var(--text);font-weight:600">VIIRS NTL:</span> Li et al. (2020) Figshare · bbox Venezuela + 25 estados · Extracción raster real</div>
        <div style="margin-top:4px;padding-top:12px;border-top:1px solid var(--border);font-size:.72rem">
          <span style="color:var(--accent);font-weight:600">CR = 0.008 &lt; 0.10</span> — consistencia AHP validada ·
          <span style="color:var(--accent);font-weight:600">SI = 0.041</span> — robustez a cambios de pesos
        </div>
      </div>
    </div>
  </div>

</section>

<!-- ===== SECTION 0: INICIO — HERO (Pulse como protagonista) ===== -->
<section class="section tab-section" id="inicio">
  <div class="section-header">
    <span class="section-title">Monitor de Clima · Actual</span>
    <span class="section-sub">ICIV Pulse mensual como protagonista · ICIV Anual como referencia estructural · Datos FRED / EIA / UNHCR / IMF</span>
  </div>

  <!-- Hero: Pulse (protagonista) + ICIV Anual (contexto) -->
  <div id="inicioHero" style="display:grid;grid-template-columns:1.4fr 1fr;gap:20px;margin-bottom:24px">

    <!-- Pulse: el número principal -->
    <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:28px 32px;position:relative;overflow:hidden">
      <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#3498db,#00d4aa)"></div>
      <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:6px">ICIV Pulse — Mensual</div>
      <div style="display:flex;align-items:flex-end;gap:16px;margin-bottom:8px">
        <div id="inicioPS" style="font-size:4rem;font-weight:700;line-height:1;color:#3498db">—</div>
        <div style="padding-bottom:6px">
          <div id="inicioPL" style="font-size:.9rem;font-weight:600;color:var(--text)">—</div>
          <div id="inicioPF" style="font-size:.72rem;color:var(--muted);margin-top:2px">—</div>
        </div>
      </div>
      <div style="display:flex;gap:20px;font-size:.75rem;color:var(--muted)">
        <span>vs. mes anterior: <strong id="inicioPD" style="color:var(--text)">—</strong></span>
        <span>cobertura directa: <strong id="inicioPC" style="color:var(--accent)">—</strong></span>
      </div>
      <div id="inicioPR" style="font-size:.72rem;color:var(--muted);margin-top:10px">—</div>
      <!-- Sparkline 12 meses (oculta, usada internamente) -->
      <canvas id="cInicioSparkline" style="display:none"></canvas>
      <div style="font-size:.65rem;color:#555;margin-top:16px">15 variables internacionales · FRED macro · EIA petróleo · IMF IMTS comercio espejo · WB Pink Sheet · Guardian y GDELT noticias · cobertura visible por mes</div>
    </div>

    <!-- ICIV Anual: contexto estructural -->
    <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:28px 32px;position:relative;overflow:hidden;display:flex;flex-direction:column">
      <div style="position:absolute;top:0;left:0;right:0;height:3px;background:var(--accent)"></div>
      <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:6px">ICIV Anual — Referencia</div>
      <div id="inicioAS" style="font-size:3.2rem;font-weight:700;line-height:1;color:var(--accent);margin-bottom:6px">—</div>
      <div id="inicioAL" style="font-size:.88rem;font-weight:600;color:var(--text)">—</div>
      <div id="inicioAD" style="font-size:.72rem;color:var(--muted);margin-top:4px">—</div>
      <div id="inicioAY" style="font-size:.68rem;color:#555;margin-top:4px">—</div>
      <div id="inicioAR" style="font-size:.68rem;color:var(--muted);margin-top:6px;line-height:1.4">—</div>
      <div style="flex:1"></div>
      <!-- Mini gauge — misma estructura que el gauge principal: bandas tenues,
           banda activa resaltada y aguja del color de la categoría -->
      <svg id="inicioGauge" viewBox="0 0 220 130" style="width:100%;max-width:220px;margin:16px auto 0">
        <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#21262d" stroke-width="20" stroke-linecap="butt"/>
        <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#e05c5c" stroke-width="20" stroke-linecap="butt"
              stroke-dasharray="84.8 282.74" stroke-dashoffset="0" opacity="0.18"/>
        <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#e67e22" stroke-width="20" stroke-linecap="butt"
              stroke-dasharray="56.5 282.74" stroke-dashoffset="-84.8" opacity="0.18"/>
        <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#f1c40f" stroke-width="20" stroke-linecap="butt"
              stroke-dasharray="42.4 282.74" stroke-dashoffset="-141.3" opacity="0.18"/>
        <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#2ecc71" stroke-width="20" stroke-linecap="butt"
              stroke-dasharray="42.4 282.74" stroke-dashoffset="-183.7" opacity="0.18"/>
        <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#00d4aa" stroke-width="20" stroke-linecap="butt"
              stroke-dasharray="56.5 282.74" stroke-dashoffset="-226.1" opacity="0.18"/>
        <path id="inicioActiveBand" d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="{current_color}" stroke-width="22" stroke-linecap="butt"
              stroke-dasharray="{active_dash_len:.1f} 282.74" stroke-dashoffset="-{active_dash_offset:.1f}" opacity="1"/>
        <line id="inicioNeedle" x1="110" y1="112" x2="110" y2="38"
              stroke="{current_color}" stroke-width="3.5" stroke-linecap="round"
              transform="rotate({gauge_angle},110,110)"/>
        <circle id="inicioNeedleBase" cx="110" cy="110" r="7" fill="{current_color}" opacity="0.95"/>
        <circle cx="110" cy="110" r="3.5" fill="#0d1117"/>
      </svg>
    </div>
  </div>

  <!-- Indicadores clave: 6 cards -->
  <div id="inicioGrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:20px">
    <!-- filled by JS from VH data -->
  </div>

  <!-- Serie completa Pulse mensual 2010–2026: el corazón del ICIV -->
  <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:22px 24px;margin-bottom:20px">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
      <div>
        <div style="font-size:.8rem;font-weight:600;color:var(--text)">ICIV Pulse — Evolución mensual 2010–2026</div>
        <div style="font-size:.7rem;color:var(--muted);margin-top:3px">197 meses · Línea verde = Pulse mensual · Línea amarilla = ICIV Anual referencia · Puntos huecos = cobertura &lt;70%</div>
      </div>
      <a href="#" onclick="event.preventDefault();showSection('pulse')" style="font-size:.7rem;color:var(--accent);text-decoration:none;white-space:nowrap;margin-left:16px">Ver análisis completo →</a>
    </div>
    <div style="height:260px">
      <canvas id="cInicioFullPulse"></canvas>
    </div>
  </div>

  <!-- Nota de actualización -->
  <div style="background:rgba(0,212,170,.04);border:1px solid rgba(0,212,170,.12);border-radius:8px;padding:12px 18px;font-size:.72rem;color:#6b7280;line-height:1.65">
    <strong style="color:var(--muted)">Actualización:</strong>
    Pulse mensual — datos FRED/EIA hasta el último mes disponible (lag EIA: 3–4 meses).
    ICIV Anual — actualización anual (WGI sep · HDI sep · WDI dic · CPI ene).
    Ninguna variable proviene de fuentes del gobierno venezolano.
  </div>
</section>

<!-- ===== SECTION 1: SCORE ACTUAL (ICIV Anual detalle) ===== -->
<section class="section tab-section" id="score">
  <div class="section-header">
    <span class="section-title">Score Actual</span>
    <span class="section-sub" id="scoreHeaderSub">Venezuela · {current_year_val}</span>
  </div>

  <!-- Year selector -->
  {year_tabs_html}

  <!-- Coverage badge — always visible, color-coded by coverage level -->
  <div id="scoreCoverageWarn" style="display:flex;background:#1c2128;border:1px solid {'#e6a817' if is_low_coverage else '#00d4aa'};border-radius:8px;padding:10px 16px;margin-bottom:16px;align-items:center;gap:12px">
    <span id="scoreCovWarnIcon" style="font-size:1.1rem">{'&#9888;' if is_low_coverage else '&#10003;'}</span>
    <div style="flex:1">
      <strong id="scoreCovWarnPct" style="color:{'#e6a817' if is_low_coverage else '#00d4aa'}">Cobertura de datos: {current_coverage:.0f}%</strong><br>
      <span style="color:#8b949e;font-size:.8rem" id="scoreCovWarnTxt">El score {current_year_val} se calcula con {current_coverage:.0f}% del peso total del modelo. {'Para años recientes, las fuentes con lag publican sus datos meses después.' if is_low_coverage else 'Cobertura suficiente para considerar el score estadísticamente representativo.'}</span>
    </div>
  </div>

  <div class="stats-row">
    <div class="stat">
      <div class="stat-label" id="scoreMainLbl">ICIV {current_year_val}</div>
      <div class="stat-val" id="scoreMainVal" style="color:{current_color}">{current_score:.1f}</div>
      <div class="stat-sub" id="scoreMainSub">{current_label} · {coverage_badge}</div>
    </div>
    <div class="stat">
      <div class="stat-label" id="scoreDeltaLbl">Variación vs año anterior</div>
      <div class="stat-val {delta_cls}" id="scoreDeltaVal">{delta_sign}{delta_val:.1f}</div>
      <div class="stat-sub" id="scoreDeltaSub">puntos respecto a {current_year_val - 1}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Mínimo histórico</div>
      <div class="stat-val stat-down">{score_min:.1f}</div>
      <div class="stat-sub">{year_min}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Máximo histórico</div>
      <div class="stat-val stat-up">{score_max:.1f}</div>
      <div class="stat-sub">{year_max}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Promedio histórico</div>
      <div class="stat-val stat-neu">{score_avg:.1f}</div>
      <div class="stat-sub">{n_years} años calculados</div>
    </div>
  </div>

  <!-- Recommendation -->
  <div class="alert {'alert-bad' if current_score <= 30 else 'alert-warn' if current_score <= 50 else 'alert-info'}" id="scoreAlertDiv">
    <div class="alert-title" id="scoreAlertTitle">Recomendación de inversión {current_year_val}</div>
    <div class="alert-body" id="scoreAlertBody">{_get_recommendation(current_score)}</div>
  </div>

  <div class="charts-grid">
    <div class="chart-card">
      <div class="ct" id="gaugeTitle">Indicador ICIV {current_year_val}</div>
      <div class="cs">Escala 0–100 · Metodología AHP Saaty (1980)</div>
      <div class="gauge-wrap">
        <svg class="gauge-svg" viewBox="0 0 220 130">
          <!-- arc background (dark track) -->
          <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#21262d" stroke-width="20" stroke-linecap="butt"/>
          <!-- Inactive bands — dim opacity so active band stands out clearly -->
          <!-- Total arc length = π*90 ≈ 282.74. Bands: 0-30=84.8 | 31-50=56.5 | 51-65=42.4 | 66-80=42.4 | 81-100=56.5 -->
          <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#e05c5c" stroke-width="20" stroke-linecap="butt"
                stroke-dasharray="84.8 282.74" stroke-dashoffset="0" opacity="0.18"/>
          <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#e67e22" stroke-width="20" stroke-linecap="butt"
                stroke-dasharray="56.5 282.74" stroke-dashoffset="-84.8" opacity="0.18"/>
          <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#f1c40f" stroke-width="20" stroke-linecap="butt"
                stroke-dasharray="42.4 282.74" stroke-dashoffset="-141.3" opacity="0.18"/>
          <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#2ecc71" stroke-width="20" stroke-linecap="butt"
                stroke-dasharray="42.4 282.74" stroke-dashoffset="-183.7" opacity="0.18"/>
          <path d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="#00d4aa" stroke-width="20" stroke-linecap="butt"
                stroke-dasharray="56.5 282.74" stroke-dashoffset="-226.1" opacity="0.18"/>
          <!-- Active band highlight (dynamic) — full opacity, slightly thicker -->
          <path id="gaugeActiveBand" d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="{current_color}" stroke-width="22" stroke-linecap="butt"
                stroke-dasharray="{active_dash_len:.1f} 282.74" stroke-dashoffset="-{active_dash_offset:.1f}" opacity="1"/>
          <!-- Fill arc removed: caused visual overlap when score crossed band boundaries.
               The needle + active band already communicate position clearly. -->
          <path id="gaugeFillArc" d="M20,110 A90,90,0,0,1,200,110" fill="none" stroke="transparent" stroke-width="0"/>
          <!-- needle (dynamic) -->
          <line id="gaugeNeedle" x1="110" y1="112" x2="110" y2="38"
                stroke="{current_color}" stroke-width="3.5" stroke-linecap="round"
                transform="rotate({gauge_angle},110,110)"/>
          <circle id="gaugeNeedleBase" cx="110" cy="110" r="7" fill="{current_color}" opacity="0.95"/>
          <circle cx="110" cy="110" r="3.5" fill="#0d1117"/>
        </svg>
        <div style="text-align:center;margin-top:4px">
          <span id="gaugeScoreNum" style="font-size:2.6rem;font-weight:700;color:{current_color};line-height:1">{current_score:.1f}</span>
          <span style="font-size:.8rem;color:var(--muted);display:block;margin-top:2px">/ 100 pts</span>
        </div>
        <div id="gaugeCatLbl" class="gauge-cat" style="color:{current_color}">{current_label}</div>
      </div>
    </div>

    <div class="chart-card">
      <div class="ct">Categorías de riesgo</div>
      <div class="cs">Escala de bandas de riesgo del ICIV</div>
      <div class="risk-bands" id="riskBands">
        <div class="rb {'active' if current_score <= 30 else ''}" id="rb0" style="color:#e05c5c">
          <div class="rb-dot" style="background:#e05c5c"></div>
          <div><strong>0–30 · Alto Riesgo</strong><br><span style="color:var(--muted)">No se recomienda inversión directa</span></div>
        </div>
        <div class="rb {'active' if 30 < current_score <= 50 else ''}" id="rb1" style="color:#e67e22">
          <div class="rb-dot" style="background:#e67e22"></div>
          <div><strong>31–50 · Riesgo Moderado-Alto</strong><br><span style="color:var(--muted)">Solo sectores con alta tolerancia al riesgo</span></div>
        </div>
        <div class="rb {'active' if 50 < current_score <= 65 else ''}" id="rb2" style="color:#f1c40f">
          <div class="rb-dot" style="background:#f1c40f"></div>
          <div><strong>51–65 · Riesgo Moderado</strong><br><span style="color:var(--muted)">Viable con due diligence reforzado</span></div>
        </div>
        <div class="rb {'active' if 65 < current_score <= 80 else ''}" id="rb3" style="color:#2ecc71">
          <div class="rb-dot" style="background:#2ecc71"></div>
          <div><strong>66–80 · Bajo Riesgo</strong><br><span style="color:var(--muted)">Condiciones favorables con análisis sectorial</span></div>
        </div>
        <div class="rb {'active' if current_score > 80 else ''}" id="rb4" style="color:#00d4aa">
          <div class="rb-dot" style="background:#00d4aa"></div>
          <div><strong>81–100 · Muy Bajo Riesgo</strong><br><span style="color:var(--muted)">Comparable a mercados emergentes estables</span></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ===== SECTION 2: EVOLUCIÓN HISTÓRICA ===== -->
<section class="section tab-section" id="historia">
  <div class="section-header">
    <span class="section-title">Evolución Histórica</span>
    <span class="section-sub">2000–{settings.series.end_year} · AHP vs Pesos Fijos</span>
  </div>

  <!-- Sub-tabs: Gráfico / Tabla -->
  <div style="display:flex;gap:0;margin-bottom:20px;border-bottom:1px solid var(--border)">
    <button class="hist-tab hist-tab-active" data-view="grafico"
      style="background:none;border:none;color:var(--text);font-size:.82rem;font-weight:600;
             padding:8px 20px;cursor:pointer;border-bottom:2px solid var(--accent)">
      Gráfico
    </button>
    <button class="hist-tab" data-view="tabla"
      style="background:none;border:none;color:var(--muted);font-size:.82rem;font-weight:500;
             padding:8px 20px;cursor:pointer;border-bottom:2px solid transparent">
      Tabla de datos
    </button>
  </div>

  <!-- Vista: Gráfico -->
  <div id="histView-grafico">
    <div class="alert alert-info" style="margin-bottom:20px">
      <div class="alert-title">Cómo leer esta sección</div>
      <div class="alert-body">
        La <strong>línea continua</strong> refleja el ICIV calculado con pesos AHP (juicio de expertos via Saaty 1980);
        la <strong>línea punteada</strong> usa pesos fijos iguales (1/6 por dimensión), que sirve como benchmark neutro.
        La <strong>diferencia entre ambas curvas</strong> cuantifica el impacto del juicio experto frente a una distribución
        sin preferencias. Las bandas de color indican el nivel de riesgo de inversión.<br><br>
        <strong>Hitos clave:</strong> El colapso post-2013 coincide con la caída del precio del petróleo y el inicio
        de las colapso macroinstitucional. El mínimo histórico ({score_min:.1f} pts) se alcanza en {year_min}, durante la hiperinflación
        y el aislamiento internacional máximo. La recuperación parcial post-2021 refleja el aperturismo económico
        del régimen y la dolarización de facto, no una normalización institucional.
      </div>
    </div>
    <div class="charts-grid single">
      <div class="chart-card wide">
        <div class="ct">Serie histórica del ICIV — Venezuela</div>
        <div class="cs">Línea principal: pesos AHP · Línea punteada: pesos fijos · Bandas: categorías de riesgo</div>
        <div class="chart-wrap" style="height:380px">
          <canvas id="cHistoria"></canvas>
        </div>
      </div>
    </div>
  </div>

  <!-- Vista: Tabla -->
  <div id="histView-tabla" style="display:none">
    <p style="font-size:.8rem;color:var(--muted);margin-bottom:16px">
      Serie completa del ICIV con pesos AHP (Saaty 1980) · {n_years} años · rango {score_min:.1f}–{score_max:.1f} pts
    </p>
    <div style="overflow-x:auto">
      <table class="gap-table">
        <thead><tr><th>Año</th><th>ICIV (AHP)</th><th>Categoría</th></tr></thead>
        <tbody>
          {hist_rows_html}
        </tbody>
      </table>
    </div>
  </div>
</section>

<!-- ===== SECTION 3: DIMENSIONES ===== -->
<section class="section tab-section" id="dimensiones">
  <div class="section-header">
    <span class="section-title">Dimensiones</span>
    <span class="section-sub">Puntaje por dimensión 2000–{settings.series.end_year}</span>
  </div>

  <!-- Sub-tab navigation -->
  <div class="dim-subtabs">
{dim_subtab_buttons_html}
  </div>

  <!-- View: Todas las dimensiones -->
  <div class="dim-view dim-view-active" id="dimview-todas">
    <div class="alert alert-info" style="margin-bottom:20px">
      <div class="alert-title">Cómo leer esta sección</div>
      <div class="alert-body">
        El ICIV descompone el clima de inversión en <strong>6 dimensiones</strong> independientes,
        cada una con su propio peso en el índice final (AHP Saaty 1980).
        El gráfico de evolución muestra cómo cada dimensión ha variado desde 2000 — las caídas
        sincronizadas post-2016 reflejan el colapso sistémico del modelo rentista venezolano.
        El radar y la barra horizontal muestran el perfil dimensional del <strong>año más reciente</strong>.
        Usa las pestañas D1–D6 para explorar cada dimensión en detalle con sus variables, fuentes y evolución histórica.
      </div>
    </div>
    <div class="charts-grid">
      <div class="chart-card wide">
        <div class="ct">Evolución de las 6 dimensiones</div>
        <div class="cs">Score 0–100 por dimensión a través del tiempo</div>
        <div class="chart-wrap" style="height:340px">
          <canvas id="cDimensiones"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <div class="ct">Perfil dimensional {current_year_val}</div>
        <div class="cs">Radar de puntajes por dimensión — año más reciente</div>
        <div class="chart-wrap" style="height:320px">
          <canvas id="cRadar"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <div class="ct">Comparativa de dimensiones {current_year_val}</div>
        <div class="cs">Barra horizontal — puntajes del último año</div>
        <div class="chart-wrap" style="height:320px">
          <canvas id="cDimBar"></canvas>
        </div>
      </div>
    </div>

    <!-- Dimension detail cards -->
    <div class="section-header" style="margin-top:32px">
      <span class="section-title">Detalle por dimensión</span>
      <span class="section-sub">Variables, fuentes de datos y dirección por dimensión — año {current_year_val}</span>
    </div>
    <div class="dim-detail-grid">
      {dim_detail_cards_html}
    </div>
  </div>

  <!-- Per-dimension detail views (populated by JS on first click) -->
{dim_view_divs_html}
</section>

<!-- ===== SECTION 4: METODOLOGÍA AHP ===== -->
<!-- AHP section fusionada dentro de #correlacion como bloque E (ver arriba) -->

<!-- ===== SECTION 6: SATV ===== -->
<section class="section tab-section" id="alertas">
  <div class="section-header">
    <span class="section-title">SATV — Alertas del Pulse</span>
    <span class="section-sub">Señales mensuales · Cobertura · Umbrales · Tendencias recientes</span>
  </div>

  <div class="alert alert-info" style="margin-bottom:20px">
    <div class="alert-title">Cómo leer esta sección</div>
    <div class="alert-body">
      El SATV se pega al Pulse para no mezclar alertas de frecuencia anual y mensual.
      Resume tres grupos de señales observadas: macro global, energía y noticias internacionales;
      marca cobertura parcial, Pulse bajo y deterioros de tres meses. La alerta es un monitor
      operacional, no una predicción ni una validación retrospectiva del ICIV anual.
    </div>
  </div>

  <!-- Panel resumen -->
  <div id="satvResumen" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px"></div>

  <!-- Alertas activas -->
  <div class="section-header" style="margin-top:0;margin-bottom:12px">
    <span class="section-title" style="font-size:1rem">Alertas activas</span>
  </div>
  <div id="satvAlertas" style="display:flex;flex-direction:column;gap:10px;margin-bottom:28px"></div>

  <!-- Semáforo de señales -->
  <div class="section-header" style="margin-top:0;margin-bottom:12px">
    <span class="section-title" style="font-size:1rem">Estado por grupo de señales</span>
  </div>
  <div id="satvDims" style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:28px"></div>

  <!-- Variables críticas + Timeline -->
  <div class="charts-grid" style="margin-bottom:0">
    <div class="chart-card">
      <div class="ct">Señales con score más bajo</div>
      <div class="cs">Último mes disponible · ordenadas de peor a mejor</div>
      <div id="satvVarTable" style="margin-top:12px"></div>
    </div>
    <div class="chart-card">
      <div class="ct">Timeline Pulse de alertas</div>
      <div class="cs">Meses con Pulse en zona crítica desde 2010</div>
      <div class="chart-wrap" style="height:280px">
        <canvas id="cSatvTimeline"></canvas>
      </div>
    </div>
  </div>
</section>

<!-- ===== SECTION 7: MAPA COROPLÉTICO ===== -->
<section class="section tab-section" id="mapa">
  <div class="section-header">
    <span class="section-title">Luminosidad Nocturna por Estado</span>
    <span class="section-sub">NTL Index (0–100) · Fuente: VIIRS DNB / DMSP-OLS · Stokes &amp; Ghosh (2021)</span>
  </div>
  <p style="font-size:.8rem;color:var(--muted);margin-bottom:16px">
    La luminosidad nocturna satelital (Nighttime Lights, NTL) es un proxy
    establecido de actividad económica subnacional (Henderson et al., 2012).
    El índice 100 corresponde al máximo histórico de cada estado.
    Seleccione el año con el control deslizante para observar la evolución geográfica.
  </p>
  <div style="display:flex;align-items:center;gap:16px;margin-bottom:12px;flex-wrap:wrap">
    <label style="font-size:.82rem;color:var(--muted)">Año:</label>
    <input type="range" id="mapaYear" min="{settings.series.start_year}" max="{settings.series.end_year}"
           value="{settings.series.end_year}" step="1"
           style="flex:1;min-width:200px;max-width:400px;accent-color:var(--accent)">
    <span id="mapaYearLabel" style="font-size:1.1rem;font-weight:700;color:var(--accent);min-width:48px">
      {settings.series.end_year}
    </span>
    <button id="mapaPlayBtn" style="background:var(--card);border:1px solid var(--border);
      color:var(--text);padding:6px 14px;border-radius:6px;cursor:pointer;font-size:.8rem">
      ▶ Animar
    </button>
    <span id="mapaNoDataNote" style="display:none;font-size:.72rem;color:#e67e22;font-style:italic"></span>
  </div>
  <div style="display:flex;gap:16px;flex-wrap:wrap">
    <div id="mapaContainer" style="flex:2;min-width:300px;height:480px;
      background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden">
    </div>
    <div style="flex:1;min-width:200px">
      <div style="background:var(--card);border:1px solid var(--border);
        border-radius:10px;padding:16px;margin-bottom:12px">
        <div style="font-size:.78rem;font-weight:600;margin-bottom:12px">Escala NTL</div>
        <div id="mapaLegend" style="display:flex;flex-direction:column;gap:6px"></div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);
        border-radius:10px;padding:16px">
        <div style="font-size:.78rem;font-weight:600;margin-bottom:10px">Top estados (año seleccionado)</div>
        <div id="mapaRanking" style="font-size:.78rem;color:var(--muted)"></div>
      </div>
    </div>
  </div>
  <p style="font-size:.72rem;color:var(--muted);margin-top:12px">
    Límites estatales: GADM Venezuela Level-1 (https://gadm.org).
    NTL por estado: Li et al. (2020/2024) Figshare DOI:10.6084/m9.figshare.9828827.v10 —
    datos reales extraídos de raster GeoTIFF por bbox estatal (rasterio). Cobertura 2000–2024.
    Para 2025–2026 sin dato satelital se muestra el último año disponible (indicado en tooltip).
    Mapa visualizado con Leaflet.js (BSD-2). Proyección: WGS84.
  </p>

  <!-- Mapa coroplético mensual NASA Black Marble (2014-2026) -->
  <div class="section-header" style="margin-top:36px">
    <span class="section-title">Mapa mensual NASA Black Marble (2014–2026)</span>
    <span class="section-sub">Radiancia nocturna por estado del producto satelital VNP46A3 · promedio anual · animación del apagón económico y su recuperación parcial</span>
  </div>
  <div class="chart-card" style="margin-top:14px">
    <div class="ct">Actividad nocturna por estado — <span id="bmMapYear">—</span></div>
    <div class="cs">Radiancia media anual por estado (NASA Black Marble VNP46A3, nW/cm²/sr). Mueve el año o pulsa «Animar» para ver cómo cambia la actividad nocturna en el territorio. Escala fija entre años: un mismo color = misma radiancia en cualquier año. Complementa el mapa anual Li et al. de arriba con datos mensuales más recientes (hasta 2026) y de un producto distinto.</div>
    <div style="display:flex;align-items:center;gap:14px;margin:14px 0 6px">
      <input type="range" id="bmMapSlider" min="0" max="0" value="0" step="1" style="flex:1;accent-color:#e6a817">
      <button id="bmMapPlay" style="background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:6px 14px;cursor:pointer;font-size:.8rem">▶ Animar</button>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start">
      <div style="flex:1 1 460px;min-width:300px">
        <svg id="bmMapSvg" viewBox="0 0 1000 700" style="width:100%;height:auto;background:#0d1117;border-radius:8px"></svg>
        <div style="display:flex;align-items:center;gap:8px;margin-top:8px;font-size:.7rem;color:var(--muted)">
          <span>menos luz</span>
          <span id="bmMapGradient" style="flex:1;height:12px;border-radius:6px;display:block"></span>
          <span>más luz</span>
        </div>
      </div>
      <div style="flex:1 1 240px;min-width:220px">
        <div style="font-size:.72rem;color:var(--muted);margin-bottom:6px">Top estados por radiancia (<span id="bmRankYear">—</span>)</div>
        <div id="bmMapRanking" style="font-size:.75rem;line-height:1.5"></div>
      </div>
    </div>
    <div id="bmMapTip" style="font-size:.72rem;color:var(--muted);margin-top:10px;min-height:1.2em"></div>
  </div>
</section>

<!-- ===== SECTION 8: LABORATORIO ===== -->
<section class="section tab-section" id="proyecciones">
  <div class="section-header">
    <span class="section-title">Laboratorio ICIV</span>
    <span class="section-sub">Simulador interactivo para explorar sensibilidad del índice anual</span>
  </div>

  <!-- El laboratorio conserva solo el simulador defendible en la vista principal. -->
  <div style="display:flex;gap:0;margin-bottom:20px;border-bottom:1px solid var(--border);flex-wrap:wrap">
    <button class="esc-tab esc-tab-active" data-esc="simulador"
      style="background:none;border:none;color:var(--muted);font-size:.82rem;font-weight:500;
             padding:8px 20px;cursor:pointer;border-bottom:2px solid var(--accent)">
      Simulador Interactivo
    </button>
  </div>

  <!-- Vista: Simulador Interactivo -->
  <div class="esc-view" id="escView-simulador">
    <div class="alert alert-info" style="margin-bottom:16px">
      <div class="alert-title">Simulador de Escenarios ICIV</div>
      <div class="alert-body">
        Ajusta el puntaje de cada dimensión con los controles deslizantes para ver el impacto en el ICIV.
        Los pesos de cada dimensión corresponden al modelo AHP calibrado (CR={cr_val:.4f}).
        El ICIV resultante es la suma ponderada: ICIV = Σ(score_dimensión × peso_AHP).
        Esto permite evaluar, por ejemplo, qué pasaría con el índice si la institucionalidad mejora
        o si la producción energética cae aún más.
      </div>
    </div>
    <div style="display:flex;gap:20px;flex-wrap:wrap">
      <!-- Sliders panel -->
      <div style="flex:1;min-width:280px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <span style="font-size:.82rem;font-weight:600">Dimensiones (score 0–100)</span>
          <button id="simReset" style="background:var(--card);border:1px solid var(--border);
            color:var(--muted);padding:4px 12px;border-radius:6px;cursor:pointer;font-size:.75rem">
            Restablecer {sim_base_year}
          </button>
        </div>
        <div id="simSliders"></div>

        <!-- Presets rápidos -->
        <div style="margin-top:16px">
          <div style="font-size:.75rem;color:var(--muted);margin-bottom:8px;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Presets históricos</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <button class="sim-preset" data-preset="peak"
              style="background:var(--card);border:1px solid var(--border);color:var(--muted);
                     padding:5px 12px;border-radius:6px;cursor:pointer;font-size:.75rem">
              Pico 2007
            </button>
            <button class="sim-preset" data-preset="min"
              style="background:var(--card);border:1px solid var(--border);color:var(--muted);
                     padding:5px 12px;border-radius:6px;cursor:pointer;font-size:.75rem">
              Mínimo 2020
            </button>
          </div>
        </div>
      </div>

      <!-- Result panel -->
      <div style="flex:1;min-width:240px">
        <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;
          padding:20px;text-align:center;margin-bottom:16px">
          <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px">
            ICIV Simulado
          </div>
          <div id="simScore" style="font-size:3.5rem;font-weight:700;line-height:1;color:var(--accent)">—</div>
          <div id="simCategory" style="font-size:.9rem;font-weight:600;margin-top:8px;color:var(--muted)">—</div>
          <div id="simAnalog" style="font-size:.75rem;color:var(--muted);margin-top:8px">—</div>
        </div>
        <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px">
          <div style="font-size:.75rem;font-weight:600;margin-bottom:10px">Contribución por dimensión</div>
          <div id="simContribBars"></div>
        </div>
      </div>
    </div>
    <!-- Mini chart -->
    <div class="chart-card" style="margin-top:20px">
      <div class="ct">Posición del escenario simulado en la serie histórica</div>
      <div class="cs">Línea horizontal = ICIV simulado · Serie histórica 2000–2026</div>
      <div class="chart-wrap" style="height:260px"><canvas id="cSimChart"></canvas></div>
    </div>
  </div>

</section>

<!-- ===== SECTION 9: CORRELACIÓN ICIV → IED ===== -->
<section class="section tab-section" id="correlacion">
  <div class="section-header">
    <span class="section-title">Validación del Indicador</span>
    <span class="section-sub">A) Outcome externo ICIV→IED · A2) Leave-one-out UNHCR/VIIRS · B) Benchmarks internacionales · C) Eventos políticos · D) Validaciones internas · E) Metodología AHP</span>
  </div>

  <!-- Sub-encabezado bloque A -->
  <div style="margin-bottom:14px;padding:10px 14px;background:var(--card);border-left:3px solid var(--accent);border-radius:6px">
    <strong style="color:var(--accent);font-size:.85rem">A · Outcome externo — ICIV → IED</strong>
    <div style="font-size:.72rem;color:var(--muted);margin-top:2px">
      Análisis exploratorio de la relación entre el ICIV y la IED observada. Pearson · OLS · Causalidad de Granger 2000–2026.
      <em>IED se reserva fuera del score core para funcionar como outcome económico externo.</em>
    </div>
  </div>
  <!-- Nota metodológica IED -->
  <div style="margin-bottom:16px;padding:10px 14px;background:#2d2007;border-left:3px solid #f1c40f;border-radius:6px;font-size:.72rem;color:#f8d775;line-height:1.6">
    <strong>Nota metodológica — alcance de la IED:</strong>
    <code>ied_neta_usd</code> no entra al score core. Se conserva como resultado económico
    externo de interés para preguntar si un mejor clima antecede flujos de inversión más favorables.
    El tamaño muestral anual, los rezagos de publicación y la dinámica de desinversión en Venezuela
    obligan a leer este bloque como evidencia exploratoria, no como prueba causal suficiente.
  </div>

  <!-- Fila superior: scatter + cross-correlation — imágenes estáticas matplotlib -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">

    <!-- Scatter ICIV(t-1) vs IED(t) -->
    <div class="card">
      <div style="font-size:.8rem;font-weight:600;color:var(--accent);margin-bottom:4px">
        Scatter: ICIV<sub>t−1</sub> → IED<sub>t</sub>
      </div>
      <div style="font-size:.72rem;color:var(--muted);margin-bottom:12px">
        Cada punto es un año (2001–2026). La línea de regresión OLS muestra la relación predictiva.
      </div>
      {'<img src="data:image/png;base64,' + _scatter_b64 + '" style="width:100%;border-radius:6px" alt="Scatter ICIV-IED">' if _scatter_b64 else '<div style="color:#8b949e;text-align:center;padding:32px;font-size:.8rem">Datos insuficientes para el gráfico.</div>'}
    </div>

    <!-- Cross-correlación -->
    <div class="card">
      <div style="font-size:.8rem;font-weight:600;color:var(--accent);margin-bottom:4px">
        Cross-Correlación Pearson por Rezago
      </div>
      <div style="font-size:.72rem;color:var(--muted);margin-bottom:12px">
        Pearson r entre ICIV<sub>t−k</sub> e IED<sub>t</sub>. Rezago óptimo: máxima |r| significativo (p &lt; 0.05).
      </div>
      {'<img src="data:image/png;base64,' + _crosscorr_b64 + '" style="width:100%;border-radius:6px" alt="Cross-correlación">' if _crosscorr_b64 else '<div style="color:#8b949e;text-align:center;padding:32px;font-size:.8rem">Datos insuficientes para el gráfico.</div>'}
    </div>
  </div>

  <!-- Fila inferior: OLS stats + Granger + ADF — renderizado server-side -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">

    <!-- Tabla OLS -->
    <div class="card">
      <div style="font-size:.8rem;font-weight:600;color:var(--accent);margin-bottom:12px">
        Regresión OLS — Coeficientes
      </div>
      <div style="font-family:monospace;font-size:.75rem;color:var(--muted);
           background:#0d1117;padding:8px 12px;border-radius:6px;margin-bottom:12px">
        {_corr_formula_html}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div>
          <div style="font-size:.68rem;color:var(--muted);margin-bottom:6px">Modelo 1 rezago</div>
          <table style="width:100%;font-size:.72rem;border-collapse:collapse">
            <thead><tr style="color:var(--muted)">
              <th style="text-align:left;padding:3px 0">Parámetro</th>
              <th style="text-align:right">&beta;</th><th style="text-align:right">p-valor</th>
            </tr></thead>
            <tbody>{_corr_ols1_html}</tbody>
          </table>
        </div>
        <div>
          <div style="font-size:.68rem;color:var(--muted);margin-bottom:6px">Modelo 2 rezagos</div>
          <table style="width:100%;font-size:.72rem;border-collapse:collapse">
            <thead><tr style="color:var(--muted)">
              <th style="text-align:left;padding:3px 0">Parámetro</th>
              <th style="text-align:right">&beta;</th><th style="text-align:right">p-valor</th>
            </tr></thead>
            <tbody>{_corr_ols2_html}</tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Granger + ADF -->
    <div class="card">
      <div style="font-size:.8rem;font-weight:600;color:var(--accent);margin-bottom:12px">
        Causalidad de Granger &amp; Estacionariedad ADF
      </div>
      {_corr_granger_adf_html}
    </div>
  </div>

  <!-- Nota metodológica -->
  <div class="card" style="border-left:3px solid var(--accent)">
    <div style="font-size:.75rem;color:var(--muted);line-height:1.6">
      <strong style="color:var(--text)">Nota metodológica.</strong>
      El análisis de correlación y causalidad entre el ICIV y los flujos de Inversión Extranjera
      Directa (IED) sigue la metodología estándar de series de tiempo económicas (Granger, 1969;
      Greene, 2018). La cross-correlación de Pearson para rezagos 0–4 años permite identificar
      el horizonte temporal en que el ICIV anticipa cambios en la IED. La regresión OLS con rezagos
      formales estima el efecto cuantitativo: un punto adicional en el ICIV<sub>t−1</sub> se
      se asocia con β₁ miles de millones USD de IED al año siguiente. El test de Granger
      (H₀: el ICIV no Granger-causa la IED) se aplica sobre primeras diferencias cuando el test ADF
      indica no-estacionariedad (I(1)), preservando la validez asintótica de los estimadores.
      <br><strong>Nota sobre Venezuela:</strong> la IED venezolana es estructuralmente negativa
      desde 2015 (desinversión neta). Los valores negativos son válidos para el análisis de
      correlación lineal (Pearson) y no requieren transformación.
      <br><em>Fuentes: World Bank WDI (IED); ICIV AHP (este estudio). Período: 2000–2026 (n={int(n_years)} obs.).</em>
    </div>
  </div>

{_loo_validation_html}

  <!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
  <!-- B · VALIDACIÓN EXTERNA vs índices internacionales -->
  <div style="margin-top:32px;margin-bottom:14px;padding:10px 14px;background:var(--card);border-left:3px solid #2ecc71;border-radius:6px">
    <strong style="color:#2ecc71;font-size:.85rem">B · Benchmarks — Correlación con índices internacionales</strong>
    <div style="font-size:.72rem;color:var(--muted);margin-top:2px">
      Comparación con índices establecidos. Algunos benchmarks también aportan variables al modelo, por lo que esta tabla evalúa convergencia y no independencia estricta.
    </div>
  </div>

  <div class="chart-card">
    <div class="ct">Correlación ICIV vs 10 índices internacionales</div>
    <div class="cs">Pearson r y Spearman ρ — solo años con ambos datos disponibles (n ≥ 10)</div>
    <div style="margin-top:14px;overflow-x:auto">
      <table class="ahp-table" style="width:100%">
        <thead><tr><th>Índice externo</th><th>Pearson r</th><th>Spearman ρ</th><th>n años</th><th>Interpretación</th></tr></thead>
        <tbody>
          {_validacion_externa_rows}
        </tbody>
      </table>
    </div>
    <div style="font-size:.7rem;color:var(--muted);margin-top:10px;line-height:1.5">
      Esperaríamos <strong>correlaciones positivas y fuertes (r &gt; 0.7)</strong> con índices establecidos
      de gobernanza, libertades y desarrollo humano, ya que el ICIV está construido sobre dimensiones similares.
    </div>
  </div>

  <!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
  <!-- C · VALIDACIÓN HISTÓRICA — eventos políticos venezolanos -->
  <div style="margin-top:32px;margin-bottom:14px;padding:10px 14px;background:var(--card);border-left:3px solid #f1c40f;border-radius:6px">
    <strong style="color:#f1c40f;font-size:.85rem">C · Validación histórica — Eventos políticos venezolanos</strong>
    <div style="font-size:.72rem;color:var(--muted);margin-top:2px">
      ¿El ICIV reacciona en la dirección esperada ante eventos políticos conocidos? {_eventos_resumen}
    </div>
  </div>

  <div class="chart-card">
    <div class="ct">Δ ICIV vs eventos clave 2002–2024</div>
    <div class="cs">Variación observada respecto al año anterior · ✓ = dirección coincide con expectativa cualitativa</div>
    <div style="margin-top:10px;overflow-x:auto">
      <table class="ahp-table" style="width:100%">
        <thead><tr><th>Año</th><th>Evento</th><th>Δ ICIV (observado)</th><th>Validación</th></tr></thead>
        <tbody>
          {_eventos_validados_html}
        </tbody>
      </table>
    </div>
    <div style="font-size:.7rem;color:var(--muted);margin-top:10px;line-height:1.5">
      Δ ICIV calculado como ICIV(año) − ICIV(año-1). La columna de validación marca <span style="color:#2ecc71">✓</span>
      cuando la dirección del cambio observado coincide con la dirección esperada según la narrativa histórica.
    </div>
  </div>

  <!-- D · Validaciones internas (resumen) -->
  <div class="card" style="margin-top:20px;border-left:3px solid var(--accent)">
    <div style="font-size:.78rem;line-height:1.7">
      <strong style="color:var(--text)">D · Validaciones internas adicionales (calculadas en pipeline):</strong>
      <ul style="margin:8px 0;padding-left:20px;color:var(--muted)">
        <li><strong>Sensibilidad:</strong> SI = 0.042 → modelo <strong>robusto</strong> a ±10% en pesos AHP</li>
        <li><strong>Consistencia AHP:</strong> CR = 0.0081 &lt;&lt; 0.10 (umbral Saaty 1980)</li>
        <li><strong>AHP vs PCA:</strong> MAD = 2.04 pts, correlación ρ = 0.99 → robustez metodológica</li>
        <li><strong>Lineal vs Geométrica:</strong> MAD = 3.05 pts, ρ = 0.99 → modelo no muy sensible al método de agregación</li>
      </ul>
      Ver pestaña <strong>Bibliografía</strong> para detalles metodológicos completos.
    </div>
  </div>

  <!-- E · Metodología AHP -->
  <div style="margin-top:24px;padding:10px 14px;background:var(--card);border-left:3px solid var(--accent);border-radius:6px">
    <strong style="color:var(--accent);font-size:.85rem">E · Metodología AHP — Proceso Analítico Jerárquico</strong>
    <div style="font-size:.72rem;color:var(--muted);margin-top:2px">
      Pesos de dimensiones derivados por comparaciones por pares · Saaty (1980) · CR = {cr_val:.4f} &lt; 0.10 validado
    </div>
  </div>
  <div class="alert alert-info" style="margin:14px 0">
    <div class="alert-title">Proceso Analítico Jerárquico (AHP)</div>
    <div class="alert-body">
      El ICIV usa el <strong>AHP de Saaty (1980)</strong> para derivar los pesos de cada dimensión a partir de
      comparaciones por pares de importancia relativa. El método garantiza consistencia lógica mediante la
      <strong>Razón de Consistencia (CR)</strong>: se acepta un juicio como válido si CR &lt; 0.10.
      Un CR = 0 indica consistencia perfecta; el ICIV presenta CR = {cr_val:.4f}, validado.<br><br>
      La <strong>comparativa AHP vs Pesos Fijos</strong> permite evaluar si el juicio experto altera
      materialmente las conclusiones del índice. Una diferencia pequeña entre ambas curvas indica que
      el ranking de Venezuela es robusto y no depende de la asignación específica de pesos,
      lo que refuerza la credibilidad del indicador como herramienta de análisis.
    </div>
  </div>
  <div class="charts-grid">
    <div class="chart-card">
      <div class="ct">Pesos AHP de dimensiones
        <span class="cr-badge">CR = {cr_val:.4f} &lt; 0.10 ✓</span>
      </div>
      <div class="cs">Razón de Consistencia validada (Saaty exige CR &lt; 0.10)</div>
      <table class="ahp-table">
        <thead><tr><th>Dimensión</th><th>Peso</th><th>%</th><th>Barra</th></tr></thead>
        <tbody>
          {ahp_rows_html}
        </tbody>
      </table>
    </div>
    <div class="chart-card">
      <div class="ct">AHP vs Pesos Fijos — Comparativa</div>
      <div class="cs">Evolución del ICIV con dos estrategias de ponderación</div>
      <div class="chart-wrap" style="height:300px">
        <canvas id="cAHPvsFixed"></canvas>
      </div>
    </div>
  </div>
</section>

<!-- ===== SECTION 10 REMOVED: Riesgo regulatorio (decisión usuario: poco valor para el foco)
     Riesgo regulatorio se mantiene como variable D3 institucional pero sin sección dedicada. -->


<!-- ===== SECTION 11: RADAR SECTORIAL ===== -->
<section class="section tab-section" id="sectorial">
  <div class="section-header">
    <span class="section-title">Investment Entry Radar Sectorial</span>
    <span class="section-sub">¿En qué sectores tiene sentido entrar primero? · Score 0–100 por sensibilidad a las dimensiones ICIV · Ajustadores: colapso macroinstitucional · CAPEX · Demanda defensiva</span>
  </div>

  <!-- KPI strip (server-side rendered) -->
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:20px">{_kpi_html}</div>

  <!-- Ranking + gráfico -->
  <div style="display:grid;grid-template-columns:1fr 380px;gap:16px;align-items:start">
    <!-- Tabla ranking (server-side rendered) -->
    <div class="chart-card" style="padding:0;overflow:hidden">
      <div style="padding:14px 18px;border-bottom:1px solid var(--border)">
        <div class="ct">Ranking Sectorial — {_sector_year}</div>
        <div class="cs">Ordenado por Score de Entrada · Click en fila para ver evolución histórica</div>
      </div>
      <div style="overflow-x:auto">
        <table id="sectorTable" style="width:100%;border-collapse:collapse;font-size:.78rem">
          <thead>
            <tr style="background:var(--border-subtle,#21262d);color:var(--muted);text-align:left">
              <th style="padding:8px 14px;font-weight:600">#</th>
              <th style="padding:8px 14px;font-weight:600">Sector</th>
              <th style="padding:8px 14px;font-weight:600;text-align:center">Score</th>
              <th style="padding:8px 14px;font-weight:600">Recomendación</th>
              <th style="padding:8px 14px;font-weight:600">Riesgo Principal</th>
              <th style="padding:8px 14px;font-weight:600;max-width:280px">Racional</th>
            </tr>
          </thead>
          <tbody>{_table_rows_html}</tbody>
        </table>
      </div>
    </div>

    <!-- Barchart sectorial -->
    <div class="chart-card">
      <div class="ct">Score por Sector</div>
      <div class="cs">Bandas de recomendación · ICIV actual: {_sector_iciv:.1f}/100</div>
      <div class="chart-wrap" style="height:380px"><canvas id="cSectorBar"></canvas></div>
    </div>
  </div>

  <!-- Evolución histórica -->
  <div class="chart-card" style="margin-top:16px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <div>
        <div class="ct">Evolución Histórica por Sector (2000–{_sector_year})</div>
        <div class="cs">Score sectorial ajustado · Seleccionar sectores con los botones</div>
      </div>
      <!-- Toggle buttons (server-side rendered) -->
      <div id="sectorToggleBtns" style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end">{_toggle_btns_html}</div>
    </div>
    <div class="chart-wrap" style="height:320px"><canvas id="cSectorHist"></canvas></div>
  </div>

  <!-- Metodología (server-side rendered) -->
  <details style="margin-top:14px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px">
    <summary style="cursor:pointer;color:var(--accent);font-size:.8rem;font-weight:600">Metodología del Radar Sectorial</summary>
    <div style="margin-top:10px;font-size:.75rem;color:var(--muted);line-height:1.7">{_sector_met}</div>
  </details>
</section>

<!-- ═══════════════════════════════════════════════════════════════════════════
     BLOQUE B — ICIV PULSE MENSUAL (CO-INDICADOR HIGH-FREQUENCY)
     ═══════════════════════════════════════════════════════════════════════════ -->

<!-- ===== SECTION: PULSE MENSUAL ===== -->
<section class="section tab-section" id="pulse">
  <div class="section-header">
    <span class="section-title">ICIV Pulse Mensual</span>
    <span class="section-sub">Co-indicador high-frequency · 15 variables internacionales mensuales · Stock-Watson (2002)</span>
  </div>

  <div class="alert alert-info" style="margin-bottom:20px">
    <div class="alert-title">¿Qué es el ICIV Pulse?</div>
    <div class="alert-body">
      El <strong>ICIV Pulse</strong> es un <strong>co-indicador mensual</strong> construido con 11 señales
      internacionales de frecuencia mensual. <strong>NO reemplaza el ICIV Anual oficial</strong>:
      lo complementa con señales en tiempo casi real para inversores que necesitan
      actualización entre publicaciones anuales (WGI, HDI, CPI). Cubre desde enero 2010.
      Metodología: agregación lineal con pesos AHP renormalizados (Stock &amp; Watson 2002).
    </div>
  </div>

  <!-- Stats Pulse -->
  <div class="stats-row">
    <div class="stat">
      <div class="stat-label">Último mes disponible</div>
      <div class="stat-val" id="pulseScoreActual">—</div>
      <div class="stat-sub" id="pulseFechaActual">—</div>
    </div>
    <div class="stat">
      <div class="stat-label">Último mes confiable</div>
      <div class="stat-val" id="pulseCategoria" style="font-size:1rem">—</div>
      <div class="stat-sub" id="pulseCobertura">—</div>
    </div>
    <div class="stat">
      <div class="stat-label">Meses calculados</div>
      <div class="stat-val stat-neu" id="pulseNMeses">—</div>
      <div class="stat-sub">desde 2010-01</div>
    </div>
    <div class="stat">
      <div class="stat-label">vs ICIV Anual {current_year_val}</div>
      <div class="stat-val stat-neu" id="pulseVsAnual">—</div>
      <div class="stat-sub">diferencia en puntos</div>
    </div>
  </div>

  <!-- Gráfica serie temporal mensual -->
  <div class="chart-card">
    <div class="ct">ICIV Pulse — Serie histórica mensual (2010–2026) · 197 meses</div>
    <div class="cs">Línea verde = Pulse mensual (cob ≥70%) · Puntos huecos = provisional (cob &lt;70%) · Línea amarilla = ICIV Anual referencia</div>
    <div class="chart-wrap" style="height:380px">
      <canvas id="cPulseMonthly"></canvas>
    </div>
  </div>

  <!-- Comparación Pulse vs Anual -->
  <div class="chart-card" style="margin-top:18px">
    <div class="ct">Pulse Anualizado vs ICIV Oficial</div>
    <div class="cs">Promedio anual del Pulse comparado contra el score anual oficial. Convergencia esperada ρ &gt; 0.8</div>
    <div class="chart-wrap" style="height:280px">
      <canvas id="cPulseVsAnnual"></canvas>
    </div>
  </div>

  <!-- Disclaimer académico -->
  <div class="card" style="margin-top:18px;border-left:3px solid var(--accent)">
    <div style="font-size:.75rem;color:var(--muted);line-height:1.7">
      <strong style="color:var(--text)">Metodología del Pulse:</strong>
      Variables incluidas: WTI, Brent, Fed Funds, USD index, VIX, UST 10Y, producción petrolera Venezuela
      (EIA International monthly), volumen y tono Guardian, volumen y tono GDELT.
      No incluye D5 (Capital Humano) porque sus variables son intrínsecamente anuales.
      Normalización Min-Max sobre rango histórico mensual disponible. Pesos renormalizados
      sobre el peso Pulse disponible. Cuando EIA o GDELT aún no publica una observación,
      la cobertura baja en vez de fabricar continuidad. Score &lt; 70 % cobertura debe
      considerarse provisional.
    </div>
  </div>
</section>

<!-- ===== SECTION: PULSE COMPONENTES ===== -->
<section class="section tab-section" id="pulse-componentes">
  <div class="section-header">
    <span class="section-title">Componentes Pulse — Series mensuales</span>
    <span class="section-sub">Las 15 variables mensuales normalizadas (0–100) que alimentan el ICIV Pulse cuando cada fuente está disponible</span>
  </div>

  <div class="chart-card">
    <div class="ct">Series mensuales normalizadas (Min-Max 0–100)</div>
    <div class="cs">Mayor valor = mejor clima (variables negativas ya invertidas). Haz clic en la leyenda para mostrar/ocultar.</div>
    <div class="chart-wrap" style="height:520px">
      <canvas id="cPulseComponents"></canvas>
    </div>
  </div>

  <div class="card" style="margin-top:18px">
    <div class="ct">Pesos renormalizados del Pulse (suman 100 %)</div>
    <div id="pulseWeightsTable" style="margin-top:10px"></div>
  </div>

  <!-- Comercio espejo multi-socio (capa contextual, no entra al score) -->
  <div class="section-header" style="margin-top:32px">
    <span class="section-title">Comercio espejo multi-socio</span>
    <span class="section-sub">Lo que las aduanas de los socios reportan comerciar con Venezuela · IMF IMTS (EEUU) y UN Comtrade (España, Brasil, India, Türkiye, China) · capa contextual — no entra al score</span>
  </div>

  <div class="chart-card">
    <div class="ct">Importaciones venezolanas según los socios (millones USD/mes)</div>
    <div class="cs">Exportaciones de cada bloque de socios hacia Venezuela = proxy de demanda interna. Los últimos ~3 meses de Comtrade son parciales: no todos los socios han reportado aún.</div>
    <div class="chart-wrap" style="height:300px"><canvas id="cMirrorImports"></canvas></div>
  </div>

  <div class="chart-card" style="margin-top:18px">
    <div class="ct">Exportaciones venezolanas según los socios (millones USD/mes)</div>
    <div class="cs">Compras de los socios a Venezuela (mayormente crudo). La serie EEUU muestra el cese de 2019 (sanciones) y la reanudación desde 2023 (licencias OFAC). Últimos meses de Comtrade parciales.</div>
    <div class="chart-wrap" style="height:300px"><canvas id="cMirrorExports"></canvas></div>
  </div>

  <div class="card" style="margin-top:18px;border-left:3px solid var(--accent)">
    <div style="font-size:.75rem;color:var(--muted);line-height:1.7">
      <strong style="color:var(--text)">Mirror statistics:</strong>
      Venezuela dejó de publicar comercio exterior confiable, pero sus socios sí reportan el suyo.
      Estas series provienen exclusivamente de las aduanas de los socios (vía IMF IMTS y UN Comtrade),
      por lo que son observaciones reales de actividad económica no manipulables desde Venezuela.
      Es práctica estándar (mirror statistics) cuando un país deja de reportar. Esta capa es contextual:
      el Pulse solo usa el flujo EEUU (IMF IMTS); la serie Comtrade multi-socio sirve de validación
      cruzada y contexto, y no entra al score.
    </div>
  </div>

  <!-- Black Marble — luminosidad nocturna mensual (capa satelital contextual) -->
  <div class="section-header" style="margin-top:32px">
    <span class="section-title">Luminosidad nocturna mensual (satélite)</span>
    <span class="section-sub">NASA Black Marble VNP46A3 · radiancia promedio de Venezuela, mensual 2014–2026 · capa satelital contextual — no entra al score</span>
  </div>

  <div class="chart-card">
    <div class="ct">Radiancia nocturna mensual de Venezuela (nW/cm²/sr)</div>
    <div class="cs">Línea azul = Black Marble mensual (VNP46A3, promedio país). Línea amarilla punteada = serie anual Li et al. (VIIRS armonizado, ya usada en el score anual) reescalada al mismo eje para comparar tendencia. Ambas coinciden en el colapso 2014–2020; divergen desde 2022 (Black Marble muestra recuperación parcial).</div>
    <div class="chart-wrap" style="height:320px"><canvas id="cBlackMarble"></canvas></div>
  </div>

  <div class="card" style="margin-top:18px;border-left:3px solid var(--accent)">
    <div style="font-size:.75rem;color:var(--muted);line-height:1.7">
      <strong style="color:var(--text)">Validación cruzada:</strong>
      agregando la serie mensual por año y correlacionándola contra la serie anual Li et al.
      (11 años completos 2014–2024) da Pearson r=+0.65 (p=0.03): consistencia positiva significativa.
      Las diferencias esperables vienen de que son productos distintos (VNP46A3 radiancia cruda vs
      serie armonizada tipo DMSP) y del tratamiento del flaring petrolero del Orinoco. Esta capa es
      contextual y de mayor frecuencia; su eventual entrada al Pulse exige antes analizar variantes de
      agregación (media logarítmica, mediana, píxeles urbanos) que atenúen el flaring, y re-backtest.
    </div>
  </div>

</section>

<!-- ===== SUB-SECCIÓN: PULSE METODOLOGÍA ===== -->
<section class="section tab-section" id="pulse-metodologia">
  <div class="section-header">
    <span class="section-title">Pulse Mensual — Metodología</span>
    <span class="section-sub">Diseño del co-indicador high-frequency · AHP renormalizado · Decisiones técnicas</span>
  </div>

  <div class="alert alert-info" style="margin-bottom:20px">
    <div class="alert-title">¿Por qué un co-indicador mensual?</div>
    <div class="alert-body">
      Las fuentes anuales del ICIV (WGI, HDI, CPI, WDI) tienen un <strong>lag de publicación de 12–18 meses</strong>.
      El ICIV Pulse cubre esta brecha usando variables internacionales con frecuencia mensual,
      disponibilidad auditable y cobertura visible por mes. <strong>No reemplaza el ICIV Anual</strong>: lo complementa con señales
      en tiempo casi real entre publicaciones anuales. Marco teórico: Aruoba, Diebold &amp; Scotti
      (2009) <em>ADS Business Conditions Index</em>; Stock &amp; Watson (2002) nowcasting.
    </div>
  </div>

  <!-- Variables incluidas -->
  <div class="card" style="margin-bottom:16px">
    <div class="ct">Variables incluidas en el Pulse (15)</div>
    <div class="cs">Solo series mensuales observadas de fuentes internacionales (ninguna de origen venezolano); los pesos se renormalizan cuando una fuente aún no publicó dato</div>
    <table class="ahp-table" style="margin-top:10px">
      <thead><tr><th>Variable</th><th>Fuente</th><th>Frecuencia</th><th>Dirección</th><th>Peso AHP renorm.</th></tr></thead>
      <tbody>
        <tr><td>WTI precio (USD/bbl)</td><td>FRED</td><td>Diaria → Mensual</td><td>Positivo</td><td>6.5%</td></tr>
        <tr><td>Brent precio (USD/bbl)</td><td>FRED</td><td>Diaria → Mensual</td><td>Positivo</td><td>4%</td></tr>
        <tr><td>Crudo Dubai (USD/bbl)</td><td>World Bank Pink Sheet</td><td>Mensual</td><td>Positivo</td><td>4%</td></tr>
        <tr><td>Fed Funds Rate (%)</td><td>FRED</td><td>Diaria → Mensual</td><td>Negativo</td><td>4%</td></tr>
        <tr><td>USD Index</td><td>FRED</td><td>Diaria → Mensual</td><td>Negativo</td><td>3.5%</td></tr>
        <tr><td>VIX volatilidad</td><td>FRED</td><td>Diaria → Mensual</td><td>Negativo</td><td>6%</td></tr>
        <tr><td>US Treasury 10Y (%)</td><td>FRED</td><td>Diaria → Mensual</td><td>Negativo</td><td>3%</td></tr>
        <tr><td>Spread bonos EM (%)</td><td>FRED / ICE BofA</td><td>Diaria → Mensual</td><td>Negativo</td><td>4%</td></tr>
        <tr><td>Producción petróleo VEN (tbpd)</td><td>EIA International</td><td>Mensual</td><td>Positivo</td><td>25%</td></tr>
        <tr><td>Importaciones espejo desde EEUU (M USD)</td><td>IMF IMTS (reporta EEUU)</td><td>Mensual</td><td>Positivo</td><td>5%</td></tr>
        <tr><td>Exportaciones espejo a EEUU (M USD)</td><td>IMF IMTS (reporta EEUU)</td><td>Mensual</td><td>Positivo</td><td>5%</td></tr>
        <tr><td>Artículos Guardian (VEN)</td><td>Guardian API</td><td>Mensual</td><td>Negativo</td><td>6.5%</td></tr>
        <tr><td>Tono titulares Guardian</td><td>Guardian + VADER</td><td>Mensual</td><td>Positivo</td><td>10%</td></tr>
        <tr><td>Cobertura GDELT</td><td>GDELT DOC API</td><td>Mensual</td><td>Negativo</td><td>5.5%</td></tr>
        <tr><td>Tono GDELT</td><td>GDELT DOC API</td><td>Mensual</td><td>Positivo</td><td>8%</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Decisiones técnicas -->
  <div class="charts-grid">
    <div class="card">
      <div class="ct">Algoritmo de construcción</div>
      <div style="font-size:.75rem;color:var(--muted);line-height:1.9;margin-top:10px">
        <ol style="padding-left:18px;margin:0">
          <li>Para cada mes t: recopilar todas las variables con dato real disponible</li>
          <li>Normalizar cada variable con Min-Max sobre el rango histórico 2020-presente</li>
          <li>Invertir variables con dirección negativa: score_inv = 100 − score_norm</li>
          <li>Calcular peso disponible = suma de pesos AHP de variables con dato ese mes</li>
          <li>Si peso disponible &lt; 30% → Pulse(t) = NaN (dato insuficiente, no fabricar)</li>
          <li>Renormalizar pesos sobre variables disponibles (suman 1.0)</li>
          <li>Pulse(t) = suma ponderada de scores normalizados</li>
        </ol>
      </div>
    </div>
    <div class="card">
      <div class="ct">Interpretación y limitaciones</div>
      <div style="font-size:.75rem;color:var(--muted);line-height:1.8;margin-top:10px">
        <strong style="color:var(--text)">Escala:</strong> 0–100 (igual que el ICIV Anual).
        <strong style="color:var(--text)">Referencia:</strong> Pulse promedio 2020-2026 ≈ 57.
        No es directamente comparable al ICIV Anual (diferentes variables y cobertura).<br><br>
        <strong style="color:var(--text)">Limitaciones:</strong>
        <ul style="padding-left:16px;margin:6px 0">
          <li>Fuentes originadas en Venezuela excluidas por política del proyecto</li>
          <li>Cobertura variable mes a mes según disponibilidad de APIs</li>
          <li>GDELT puede rate-limit; si falta, la cobertura baja y no se fabrica una serie sustituta</li>
          <li>WTI/Brent son factores exógenos, no directamente sobre Venezuela</li>
        </ul>
        <strong style="color:var(--text)">Referencias:</strong><br>
        Aruoba, Diebold &amp; Scotti (2009) · Stock &amp; Watson (2002) ·
        Hyndman &amp; Athanasopoulos (2018)
      </div>
    </div>
  </div>
</section>

<!-- ═══════════════════════════════════════════════════════════════════════════
     BLOQUE C — MACHINE LEARNING (FORECAST + NOWCAST)
     ═══════════════════════════════════════════════════════════════════════════ -->

<!-- ===== SECTION: FORECAST ML ===== -->
<section class="section tab-section" id="forecast-ml">
  <div class="section-header">
    <span class="section-title">Predicción Pulse</span>
    <span class="section-sub">Forecast mensual univariado sobre la serie Pulse observada</span>
  </div>

  <div class="alert alert-info" style="margin-bottom:20px">
    <div class="alert-title">Modelos implementados</div>
    <div class="alert-body">
      Se expone una sola predicción: <strong>SARIMA(p,d,q)(P,D,Q,12)</strong> sobre el Pulse mensual
      observado para los próximos 6 meses, con intervalos de confianza 80 % y 95 % y
      auto-selección de orden por AIC. El simulador queda separado en el laboratorio porque
      explora sensibilidad del ICIV anual y no pretende pronosticar un escenario político.
    </div>
  </div>

  <!-- Stats forecast -->
  <div class="stats-row">
    <div class="stat">
      <div class="stat-label">SARIMA orden</div>
      <div class="stat-val stat-neu" id="mlSarimaOrder" style="font-size:.95rem">—</div>
      <div class="stat-sub" id="mlSarimaAic">AIC: —</div>
    </div>
    <div class="stat">
      <div class="stat-label">Horizonte</div>
      <div class="stat-val stat-neu" style="font-size:1.2rem">6 meses</div>
      <div class="stat-sub">una trayectoria media</div>
    </div>
    <div class="stat">
      <div class="stat-label">Bandas</div>
      <div class="stat-val stat-neu" style="font-size:1.2rem">80% / 95%</div>
      <div class="stat-sub">incertidumbre del forecast</div>
    </div>
    <div class="stat">
      <div class="stat-label">Backtesting</div>
      <div class="stat-val stat-neu" id="mlBacktestBest" style="font-size:1rem">—</div>
      <div class="stat-sub" id="mlBacktestSub">rolling-origin</div>
    </div>
  </div>

  <!-- Gráfico forecast SARIMA -->
  <div class="chart-card" style="margin-top:18px">
    <div class="ct">Forecast SARIMA — Últimos 30 meses + 6 meses de predicción</div>
    <div class="cs">Línea sólida = Pulse histórico (alta cobertura) · Línea punteada amarilla = forecast SARIMA · Bandas = IC 80% y 95%</div>
    <div class="chart-wrap" style="height:380px">
      <canvas id="cMlForecast"></canvas>
    </div>
  </div>

  <!-- Metodología compacta inline -->
  <div class="card" style="margin-top:18px;border-left:3px solid var(--accent)">
    <div style="font-size:.75rem;color:var(--muted);line-height:1.7">
      <strong style="color:var(--text)">Resumen metodológico:</strong>
      SARIMA auto-selección por AIC entre especificaciones candidatas sobre observaciones
      Pulse con cobertura suficiente. Ver metodología para supuestos y límites.
    </div>
  </div>

  <div class="card" style="margin-top:18px;border-left:3px solid #f1c40f">
    <div class="ct">Backtesting rolling-origin</div>
    <div id="mlBacktestSummary" style="font-size:.75rem;color:var(--muted);line-height:1.7;margin-top:8px">
      Ejecuta <code>python scripts/backtest_pulse_forecast.py</code> para generar la evidencia fuera de muestra.
    </div>
    <div id="mlBacktestTable" style="margin-top:12px"></div>
  </div>
</section>

<!-- ===== SUB-SECCIÓN: NOWCAST ANUAL ===== -->
<section class="section tab-section" id="forecast-metodologia">
  <div class="section-header">
    <span class="section-title">Forecast ML — Metodología</span>
    <span class="section-sub">SARIMA · OLS Nowcast · Validación · Referencias académicas</span>
  </div>

  <div class="charts-grid">

    <!-- SARIMA -->
    <div class="card">
      <div class="ct">Modelo A — SARIMA Univariado</div>
      <div style="font-size:.75rem;color:var(--muted);line-height:1.8;margin-top:10px">
        <strong style="color:var(--text)">Especificación:</strong>
        SARIMA(p,d,q)(P,D,Q)<sub>s=12</sub> — captura tendencia, estacionalidad anual y autocorrelación del Pulse.<br><br>
        <strong style="color:var(--text)">Selección de orden:</strong>
        Se prueban 3 configuraciones candidatas y se elige la de menor AIC (Akaike Information Criterion):
        <ul style="padding-left:16px;margin:6px 0">
          <li>(1,1,1)(1,1,1,12)</li>
          <li>(1,1,2)(1,1,1,12) — <em>generalmente el mejor</em></li>
          <li>(2,1,1)(1,1,1,12)</li>
        </ul>
        <strong style="color:var(--text)">Forecast:</strong> 6 meses con intervalos de confianza 80 % y 95 %.<br>
        Los valores forecast se recortan al rango [0, 100] (dominio del Pulse).<br><br>
        <strong style="color:var(--text)">Referencia:</strong>
        Hyndman &amp; Athanasopoulos (2018) <em>Forecasting: Principles and Practice</em>, 3ª ed., cap. 8-9.
      </div>
    </div>

    <!-- OLS Nowcast -->
    <div class="card">
      <div class="ct">Modelo B — OLS Nowcast Pulse → ICIV Anual</div>
      <div style="font-size:.75rem;color:var(--muted);line-height:1.8;margin-top:10px">
        <strong style="color:var(--text)">Especificación:</strong>
        Regresión OLS con features derivados del Pulse mensual del año en curso:<br>
        <ul style="padding-left:16px;margin:6px 0">
          <li>pulse_avg: promedio de meses disponibles</li>
          <li>pulse_trend: cambio vs año anterior</li>
          <li>pulse_min, pulse_max, pulse_std (si n ≥ 11 años)</li>
        </ul>
        <strong style="color:var(--text)">Anti-overfit:</strong>
        Si n &lt; 11 años de entrenamiento → solo 2 features (evita sobreajuste).
        Si n ≥ 11 → 5 features (mayor poder explicativo).<br><br>
        <strong style="color:var(--text)">Validación:</strong>
        Leave-One-Out Cross-Validation (LOO-CV) — más honesto que R² in-sample cuando n es pequeño.
        CERO datos artificiales: se usa <code>dropna()</code>, no <code>fillna(0)</code>.<br><br>
        <strong style="color:var(--text)">Referencia:</strong>
        Stock &amp; Watson (2002) <em>JBES</em> 20(2): 147–162.
      </div>
    </div>

  </div>

  <!-- Pipeline de datos -->
  <div class="card" style="margin-top:16px">
    <div class="ct">Pipeline de datos para los modelos ML</div>
    <div style="font-size:.75rem;color:var(--muted);line-height:1.9;margin-top:10px">
      <ol style="padding-left:18px;margin:0">
        <li>PulseAggregator genera DataFrame mensual [año, mes, pulse_score, cobertura_pct]</li>
        <li>PulseForecaster filtra observaciones con cobertura ≥ 70% para el SARIMA</li>
        <li>Serie temporal indexada por fecha (freq=MS), gaps internos imputados linealmente (limit=2)</li>
        <li>Si serie &lt; 24 observaciones → SARIMA omitido (muestra insuficiente)</li>
        <li>Para Nowcast: features calculados sobre años con ≥ 6 meses de Pulse disponibles</li>
        <li>Merge con ICIV Anual para entrenamiento (solo años con ambos datos reales)</li>
        <li>Predicción del año en curso con los meses Pulse ya disponibles</li>
      </ol>
    </div>
  </div>
</section>

<!-- ===== SECTION 12: NOTICIAS ===== -->
<section class="section tab-section" id="noticias">
  <div class="section-header">
    <span class="section-title">Noticias Venezuela</span>
    <span class="section-sub">Guardian en vivo + snapshot RSS internacional filtrado</span>
  </div>

  <div class="card" style="margin-bottom:16px">
    <div class="ct">Fuentes complementarias</div>
    <div style="font-size:.75rem;color:var(--muted);line-height:1.8;margin-top:8px">
      Esta pestana combina The Guardian por API abierta con un snapshot de Google News RSS filtrado
      por una lista cerrada de medios internacionales. Se excluyen fuentes locales venezolanas y la
      seccion no modifica el ICIV ni el Pulse: solo sirve como evidencia cualitativa de contexto.
    </div>
    <div class="news-srclinks">
      <a class="news-srclink" href="https://api.gdeltproject.org/api/v2/doc/doc?query=Venezuela%20investment&mode=artlist&format=html" target="_blank" rel="noopener">GDELT</a>
      <a class="news-srclink" href="https://www.reuters.com/site-search/?query=Venezuela%20investment" target="_blank" rel="noopener">Reuters</a>
      <a class="news-srclink" href="https://apnews.com/search?q=Venezuela%20economy" target="_blank" rel="noopener">AP</a>
      <a class="news-srclink" href="https://www.bbc.com/search?q=Venezuela%20economy" target="_blank" rel="noopener">BBC</a>
      <a class="news-srclink" href="https://www.ft.com/search?q=Venezuela%20economy" target="_blank" rel="noopener">Financial Times</a>
      <a class="news-srclink" href="https://www.bloomberg.com/search?query=Venezuela%20economy" target="_blank" rel="noopener">Bloomberg</a>
      <a class="news-srclink" href="https://news.google.com/search?q=Venezuela%20investment%20economy&hl=en-US&gl=US&ceid=US%3Aen" target="_blank" rel="noopener">Google News</a>
    </div>
  </div>

  <div class="card" style="margin-bottom:16px">
    <div class="ct">Prensa internacional agregada</div>
    <div class="cs">RSS filtrado · sin fuentes venezolanas · no entra al score</div>
    <div class="news-grid" id="intlNewsGrid" style="margin-top:12px">
      <div class="news-status">Cargando snapshot internacional...</div>
    </div>
  </div>

  <div style="display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:14px">
    <div>
      <div class="ct">The Guardian — en vivo</div>
      <div class="cs">Cobertura Venezuela vía API abierta · filtra por categoría</div>
    </div>
    <div class="news-filter" id="newsFilter" style="margin-bottom:0">
      <span class="news-chip active" data-tag="all">Todas</span>
      <span class="news-chip" data-tag="economy">Economia</span>
      <span class="news-chip" data-tag="politics">Politica</span>
      <span class="news-chip" data-tag="world">Internacional</span>
      <span class="news-chip" data-tag="business">Negocios</span>
    </div>
  </div>

  <div class="news-grid" id="newsGrid">
    <div class="news-status" id="newsStatus">
      <div class="news-skeleton" style="height:14px;width:220px;margin:0 auto 8px"></div>
      <div>Cargando noticias desde The Guardian...</div>
    </div>
  </div>

  <div style="text-align:center;margin-top:20px">
    <button id="newsLoadMore" style="display:none;background:rgba(0,212,170,.1);border:1px solid var(--accent);
      color:var(--accent);padding:8px 24px;border-radius:20px;cursor:pointer;font-size:.82rem;font-family:inherit">
      Cargar mas
    </button>
  </div>
</section>

<!-- ===== SECTION: BIBLIOGRAFÍA ===== -->
<section class="section tab-section" id="bibliografia">
  <div class="section-header">
    <span class="section-title">Bibliografía y Referencias</span>
    <span class="section-sub">Marco teórico · Fuentes de datos · Metodología</span>
  </div>

  <div class="charts-grid" style="grid-template-columns:1fr 1fr">
    <div class="chart-card">
      <div class="ct">Marco metodológico</div>
      <div class="cs">Índices compuestos · AHP · Normalización · Validación</div>
      <ol style="font-size:.78rem;line-height:1.8;color:var(--muted);margin-top:12px;padding-left:20px">
        <li><strong>Saaty, T. L. (1980).</strong> <em>The Analytic Hierarchy Process: Planning, Priority Setting, Resource Allocation</em>. McGraw-Hill. — Base metodológica del cálculo de pesos AHP, CR.</li>
        <li><strong>OECD &amp; JRC. (2008).</strong> <em>Handbook on Constructing Composite Indicators: Methodology and User Guide</em>. París: OECD Publishing. — Estándar para construcción de índices compuestos.</li>
        <li><strong>Nardo, M., Saisana, M., Saltelli, A., et al. (2005).</strong> Tools for composite indicators building. EUR 21682 EN. JRC.</li>
        <li><strong>Bekaert, G., &amp; Harvey, C. R. (2003).</strong> Emerging markets finance. <em>Journal of Empirical Finance</em>, 10(1-2), 3-55.</li>
        <li><strong>Stock, J. H., &amp; Watson, M. W. (2002).</strong> Macroeconomic forecasting using diffusion indexes. <em>JBES</em>, 20(2), 147-162. — Base teórica para nowcasting.</li>
        <li><strong>Jerven, M. (2013).</strong> <em>Poor Numbers: How We Are Misled by African Development Statistics</em>. Cornell University Press. — Limitaciones de datos en países en crisis.</li>
        <li><strong>Granger, C. W. J. (1969).</strong> Investigating causal relations by econometric models and cross-spectral methods. <em>Econometrica</em>, 37(3), 424-438.</li>
      </ol>
    </div>

    <div class="chart-card">
      <div class="ct">Fuentes de datos (internacionales)</div>
      <div class="cs">27 fuentes académicamente reconocidas · cero fuentes gubernamentales venezolanas</div>
      <ol style="font-size:.78rem;line-height:1.8;color:var(--muted);margin-top:12px;padding-left:20px">
        <li><strong>World Bank Group.</strong> World Development Indicators (WDI). <a href="https://databank.worldbank.org/source/world-development-indicators" target="_blank">databank.worldbank.org</a></li>
        <li><strong>Kaufmann, D., Kraay, A., &amp; Mastruzzi, M. (2010).</strong> The Worldwide Governance Indicators. <em>World Bank Policy Research</em> 5430.</li>
        <li><strong>IMF. (2026).</strong> World Economic Outlook Database, April 2026.</li>
        <li><strong>U.S. EIA.</strong> International Energy Statistics (monthly + annual). <a href="https://www.eia.gov/international/data/" target="_blank">eia.gov</a></li>
        <li><strong>Federal Reserve Bank of St. Louis.</strong> FRED Economic Data. <a href="https://fred.stlouisfed.org" target="_blank">fred.stlouisfed.org</a></li>
        <li><strong>UNDP. (2024).</strong> Human Development Report 2024. <a href="https://hdr.undp.org" target="_blank">hdr.undp.org</a></li>
        <li><strong>WHO.</strong> Global Health Observatory data repository. <a href="https://www.who.int/data/gho" target="_blank">who.int/data/gho</a></li>
        <li><strong>UNHCR.</strong> Refugee Data Finder. <a href="https://www.unhcr.org/refugee-statistics" target="_blank">unhcr.org/refugee-statistics</a></li>
        <li><strong>Transparency International. (2025).</strong> Corruption Perceptions Index 2024. <a href="https://www.transparency.org/en/cpi" target="_blank">transparency.org/cpi</a></li>
        <li><strong>Freedom House. (2026).</strong> Freedom in the World 2026.</li>
        <li><strong>World Justice Project. (2025).</strong> WJP Rule of Law Index 2025.</li>
        <li><strong>Gibney, M., Cornett, L., Wood, R., et al.</strong> Political Terror Scale 1976-2024 (ed. 2025). <a href="https://www.politicalterrorscale.org" target="_blank">politicalterrorscale.org</a></li>
        <li><strong>Li, X., Zhou, Y., et al. (2020).</strong> A harmonized global nighttime light dataset 1992-2024. <em>Scientific Data</em>, 7(1). Figshare DOI: 10.6084/m9.figshare.9828827</li>
        <li><strong>Our World in Data.</strong> Redistribución licencia abierta (HDI, GHI, FAO).</li>
        <li><strong>UNDP.</strong> Human Development Report — HDI series (via Our World in Data).</li>
        <li><strong>ILO ILOSTAT.</strong> Labour Statistics Database (via WB proxy).</li>
        <li><strong>The Guardian Open Platform.</strong> Articles API + VADER sentiment (Hutto &amp; Gilbert, 2014).</li>
        <li><strong>Hutto, C. J., &amp; Gilbert, E. (2014).</strong> VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. <em>ICWSM</em>.</li>
        <li><strong>Saisana, M., Saltelli, A., &amp; Tarantola, S. (2005).</strong> Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators. <em>JRSS A</em>, 168(2).</li>
      </ol>
    </div>
  </div>

  <!-- Software y herramientas -->
  <div class="card" style="margin-top:18px">
    <div class="ct">Software y herramientas (open source)</div>
    <div style="font-size:.74rem;color:var(--muted);line-height:1.8;margin-top:10px">
      <strong>Lenguaje:</strong> Python 3.10+ &nbsp;·&nbsp;
      <strong>Análisis:</strong> pandas, numpy, scipy, statsmodels &nbsp;·&nbsp;
      <strong>NLP:</strong> vaderSentiment (Hutto &amp; Gilbert, 2014) &nbsp;·&nbsp;
      <strong>Raster:</strong> rasterio (VIIRS nighttime lights) &nbsp;·&nbsp;
      <strong>Visualización:</strong> Chart.js, D3.js, matplotlib &nbsp;·&nbsp;
      <strong>HTTP:</strong> requests, BeautifulSoup4
    </div>
  </div>

  <!-- Cita sugerida -->
  <div class="alert alert-info" style="margin-top:18px">
    <div class="alert-title">Cita sugerida del proyecto</div>
    <div class="alert-body">
      Gómez, F. (2026). <em>ICIV — Indicador de Clima de Inversión Venezuela: Diseño metodológico,
      pipeline ETL automatizado y dashboard interactivo</em>. Tesis de Especialización en Big Data
      e Inteligencia de Negocios, Universidad EIA. Disponible en:
      <code>github.com/Felipegomeze2/ICIV</code>
    </div>
  </div>
</section>



<!-- ===== SECTION: VENEZUELA HOY ===== -->
<section class="section tab-section" id="ven-hoy">
  <div class="section-header">
    <span class="section-title">Venezuela Hoy</span>
    <span class="section-sub">Panel de indicadores clave · Alta frecuencia + anuales · Fuentes internacionales verificadas</span>
  </div>

  <!-- KPI Hero: ICIV + Pulse -->
  <div id="vhHero" style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px">
    <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:22px;text-align:center">
      <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin-bottom:8px">ICIV Score Anual</div>
      <div id="vhIcivScore" style="font-size:2.8rem;font-weight:700;line-height:1;color:var(--accent)">—</div>
      <div id="vhIcivLabel" style="font-size:.75rem;color:var(--muted);margin-top:6px">—</div>
      <div id="vhIcivDelta" style="font-size:.72rem;margin-top:4px;color:var(--muted)">—</div>
      <div id="vhIcivYear" style="font-size:.65rem;color:#555;margin-top:8px">—</div>
    </div>
    <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:22px;text-align:center">
      <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin-bottom:8px">ICIV Pulse Mensual</div>
      <div id="vhPulseScore" style="font-size:2.8rem;font-weight:700;line-height:1;color:#3498db">—</div>
      <div id="vhPulseLabel" style="font-size:.75rem;color:var(--muted);margin-top:6px">—</div>
      <div id="vhPulseDelta" style="font-size:.72rem;margin-top:4px;color:var(--muted)">—</div>
      <div id="vhPulseYear" style="font-size:.65rem;color:#555;margin-top:8px">—</div>
    </div>
  </div>

  <!-- Grid de indicadores -->
  <div id="vhGrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px;margin-bottom:24px">
    <!-- filled by JS -->
  </div>

  <!-- Nota de fuentes -->
  <div style="background:rgba(0,212,170,.04);border:1px solid rgba(0,212,170,.15);border-radius:8px;padding:14px 18px;font-size:.73rem;color:var(--muted);line-height:1.7">
    <strong style="color:var(--text)">Fuentes:</strong>
    Precios WTI/Brent · Fed Funds · VIX · USD Index · UST 10Y: <em>FRED, Federal Reserve Bank of St. Louis</em> &nbsp;·&nbsp;
    Producción petróleo Venezuela: <em>EIA International Energy Statistics (mensual)</em> &nbsp;·&nbsp;
    PIB / Inflación: <em>IMF World Economic Outlook Abril 2026</em> &nbsp;·&nbsp;
    Freedom House: <em>Freedom in the World 2026</em> &nbsp;·&nbsp;
    CPI: <em>Transparency International 2025</em> &nbsp;·&nbsp;
    WGI: <em>World Bank Governance Indicators 2024</em> &nbsp;·&nbsp;
    Migrantes: <em>UNHCR Refugee Data Finder 2025</em> &nbsp;·&nbsp;
    HDI: <em>UNDP Human Development Report 2024</em>
  </div>
</section>

<!-- FOOTER -->
<footer class="footer">
  <a href="#" onclick="event.preventDefault();showSection('portada')"
     style="color:var(--accent);text-decoration:none;font-weight:600">ICIV</a>
  &nbsp;·&nbsp; Indicador de Clima de Inversión Venezuela
  &nbsp;·&nbsp; Tesis de Especialización — Big Data e Inteligencia de Negocios · Universidad EIA &nbsp;·&nbsp; {generated_at}<br>
  <span style="font-size:.65rem">
    &nbsp;·&nbsp; AHP Saaty (1980) · OCDE Handbook (2008) · Stock &amp; Watson (2002)
  </span>
</footer>

<script>
// ── Shared defaults ──────────────────────────────────────────────────────────
Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.font.family = "'Inter', sans-serif";

const ACCENT = '#00d4aa';
const CARD   = '#1c2128';

// ── Data ────────────────────────────────────────────────────────────────────
const years     = {years_js};
const scoresAHP = {scores_ahp_js};
const ptColors  = {pt_colors_js};
const yearsFix  = {years_fix_js};
const scoresFix = {scores_fix_js};
const coverage  = {coverage_js};   // cobertura % por año (null si no disponible)
const COV_THRESHOLD = {_COVERAGE_THRESHOLD};  // % mínimo para score confiable
const dimSeries = {dim_series_json};
const radarVals = {radar_vals_js};
const radarLbls = {radar_lbls_js};
const radarClrs = {radar_clrs_js};
const dimLbls   = {radar_lbls_js};
const DIM_COLORS = {json.dumps(DIM_COLORS)};

// ── Chart 1: Historia ────────────────────────────────────────────────────────
new Chart(document.getElementById('cHistoria'), {{
  type: 'line',
  data: {{
    labels: years,
    datasets: [
      {{
        label: 'ICIV (Pesos Fijos)',
        data: (() => {{
          const map = {{}};
          yearsFix.forEach((y,i) => map[y] = scoresFix[i]);
          return years.map(y => map[y] ?? null);
        }})(),
        borderColor: '#444c56',
        borderWidth: 1.5,
        borderDash: [5,4],
        pointRadius: 0,
        tension: 0.3,
        fill: false,
      }},
      {{
        label: 'ICIV (AHP)',
        data: scoresAHP,
        borderColor: ACCENT,
        borderWidth: 2.5,
        // Puntos con baja cobertura (<60%) se muestran en naranja pálido con borde punteado
        pointBackgroundColor: years.map((y,i) => (coverage[i] !== null && coverage[i] < COV_THRESHOLD) ? '#e6981770' : ptColors[i]),
        pointBorderColor: years.map((y,i) => (coverage[i] !== null && coverage[i] < COV_THRESHOLD) ? '#e69817' : '#0d1117'),
        pointBorderWidth: years.map((y,i) => (coverage[i] !== null && coverage[i] < COV_THRESHOLD) ? 2 : 1),
        pointRadius: years.map((y,i) => (coverage[i] !== null && coverage[i] < COV_THRESHOLD) ? 4 : 5),
        pointStyle: years.map((y,i) => (coverage[i] !== null && coverage[i] < COV_THRESHOLD) ? 'rectRot' : 'circle'),
        pointHoverRadius: 7,
        tension: 0.3,
        fill: false,
      }},
      // Dataset auxiliar para la leyenda de baja cobertura
      {{
        label: 'Cobertura < 60% (provisional)',
        data: years.map((y,i) => (coverage[i] !== null && coverage[i] < COV_THRESHOLD) ? scoresAHP[i] : null),
        borderColor: 'transparent',
        backgroundColor: '#e69817',
        pointStyle: 'rectRot',
        pointRadius: 5,
        pointBorderColor: '#e69817',
        pointBorderWidth: 2,
        showLine: false,
      }}
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ position: 'top' }},
      annotation: {{
        annotations: {{
          band1: {{ type:'box', yMin:0,  yMax:30,  backgroundColor:'rgba(224,92,92,0.08)',  borderWidth:0, label:{{display:true,content:'Alto Riesgo',position:'start',color:'#e05c5c',font:{{size:9}}}}}},
          band2: {{ type:'box', yMin:30, yMax:50,  backgroundColor:'rgba(230,126,34,0.06)', borderWidth:0, label:{{display:true,content:'Moderado-Alto',position:'start',color:'#e67e22',font:{{size:9}}}}}},
          band3: {{ type:'box', yMin:50, yMax:65,  backgroundColor:'rgba(241,196,15,0.06)', borderWidth:0, label:{{display:true,content:'Moderado',position:'start',color:'#f1c40f',font:{{size:9}}}}}},
          band4: {{ type:'box', yMin:65, yMax:80,  backgroundColor:'rgba(46,204,113,0.06)', borderWidth:0, label:{{display:true,content:'Bajo Riesgo',position:'start',color:'#2ecc71',font:{{size:9}}}}}},
          band5: {{ type:'box', yMin:80, yMax:100, backgroundColor:'rgba(0,212,170,0.06)',  borderWidth:0, label:{{display:true,content:'Muy Bajo',position:'start',color:'#00d4aa',font:{{size:9}}}}}},
        }}
      }}
    }},
    scales: {{
      y: {{ min:0, max:100, grid:{{color:'#21262d'}}, ticks:{{stepSize:10}} }},
      x: {{ grid:{{color:'#21262d'}} }}
    }}
  }}
}});

// ── Chart 2: Dimensiones ─────────────────────────────────────────────────────
const dimKeys = Object.keys(dimSeries);
new Chart(document.getElementById('cDimensiones'), {{
  type: 'line',
  data: {{
    labels: years,
    datasets: dimKeys.map((k, i) => ({{
      label: dimLbls[i] || k,
      data: dimSeries[k],
      borderColor: DIM_COLORS[i % DIM_COLORS.length],
      borderWidth: 2,
      pointRadius: 2,
      tension: 0.3,
      fill: false,
    }}))
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode:'index', intersect:false }},
    plugins: {{ legend:{{ position:'top', labels:{{boxWidth:12, font:{{size:10}}}} }} }},
    scales: {{
      y: {{ min:0, max:100, grid:{{color:'#21262d'}} }},
      x: {{ grid:{{color:'#21262d'}} }}
    }}
  }}
}});

// ── Chart 3: Radar ───────────────────────────────────────────────────────────
new Chart(document.getElementById('cRadar'), {{
  type: 'radar',
  data: {{
    labels: radarLbls,
    datasets: [{{
      label: '{current_year_val}',
      data: radarVals,
      borderColor: '{current_color}',
      backgroundColor: '{current_color}33',
      pointBackgroundColor: radarClrs,
      borderWidth: 2,
      pointRadius: 5,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend:{{ display:false }} }},
    scales: {{
      r: {{
        min:0, max:100,
        grid:{{color:'#30363d'}},
        angleLines:{{color:'#30363d'}},
        ticks:{{backdropColor:'transparent', stepSize:25, font:{{size:9}}}},
        pointLabels:{{font:{{size:10}},color:'#8b949e'}}
      }}
    }}
  }}
}});

// ── Chart 4: DimBar ──────────────────────────────────────────────────────────
new Chart(document.getElementById('cDimBar'), {{
  type: 'bar',
  data: {{
    labels: dimLbls,
    datasets: [{{
      label: 'Score {current_year_val}',
      data: radarVals,
      backgroundColor: radarClrs.map(c => c + '99'),
      borderColor: radarClrs,
      borderWidth: 1,
      borderRadius: 4,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend:{{ display:false }} }},
    scales: {{
      x: {{ min:0, max:100, grid:{{color:'#21262d'}} }},
      y: {{ grid:{{display:false}}, ticks:{{font:{{size:10}}}} }}
    }}
  }}
}});

// ── Chart 5: AHP vs Fixed ────────────────────────────────────────────────────
new Chart(document.getElementById('cAHPvsFixed'), {{
  type: 'line',
  data: {{
    labels: years,
    datasets: [
      {{
        label: 'Pesos Fijos',
        data: (() => {{
          const map = {{}};
          yearsFix.forEach((y,i) => map[y] = scoresFix[i]);
          return years.map(y => map[y] ?? null);
        }})(),
        borderColor: '#6e7681',
        borderWidth: 1.5,
        borderDash: [4,3],
        pointRadius: 0,
        tension: 0.3,
        fill: false,
      }},
      {{
        label: 'AHP (Saaty)',
        data: scoresAHP,
        borderColor: ACCENT,
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: ACCENT,
        tension: 0.3,
        fill: false,
      }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode:'index', intersect:false }},
    plugins: {{ legend:{{ position:'top' }} }},
    scales: {{
      y: {{ min:0, max:100, grid:{{color:'#21262d'}} }},
      x: {{ grid:{{color:'#21262d'}} }}
    }}
  }}
}});

// ── Tab switching de 2 niveles (SPA) ─────────────────────────────────────────
// Estructura: pestañas top (.nav-top a) activan bloques de sub-navs (.nav-sub),
// y las sub-pestañas (.nav-sub a) cambian la sección visible (.tab-section).

const topLinks    = document.querySelectorAll('.nav-top a[data-block]');
const subNavs     = document.querySelectorAll('.nav-sub[data-block]');
const subLinks    = document.querySelectorAll('.nav-sub a[href^="#"]');
const tabSections = document.querySelectorAll('.tab-section');

const _tabInits = {{}};   // id → fn — populated lazily by section IIFEs

// Mapeo section_id → bloque narrativo
const SECTION_TO_BLOCK = {{
  // Portada
  'portada':'portada',
  // Inicio (Monitor de clima actual)
  'inicio':'inicio', 'score':'inicio', 'ven-hoy':'inicio',
  // Historia — anual + mensual + geográfico
  'historia':'historia', 'pulse':'historia',
  'pulse-componentes':'historia', 'pulse-metodologia':'historia',
  'mapa':'historia',
  // Diagnóstico — qué está fallando y dónde invertir
  'dimensiones':'diagnostico', 'alertas':'diagnostico', 'sectorial':'diagnostico',
  // Proyección
  'proyecciones':'proyeccion',
  'forecast-ml':'proyeccion', 'forecast-metodologia':'proyeccion',
  // Noticias
  'noticias':'noticias',
  // Metodología
  'correlacion':'metodologia', 'bibliografia':'metodologia',
}};

// Sección por defecto al activar cada bloque
const DEFAULT_SECTION = {{
  'portada':    'portada',
  'inicio':     'inicio',
  'historia':   'historia',
  'diagnostico':'dimensiones',
  'proyeccion': 'proyecciones',
  'noticias':   'noticias',
  'metodologia':'correlacion',
}};

function activateBlock(block) {{
  topLinks.forEach(a => a.classList.toggle('nav-top-active', a.dataset.block === block));
  subNavs.forEach(s => s.classList.toggle('nav-sub-active', s.dataset.block === block));
}}

function showSection(targetId) {{
  // Determinar bloque
  const block = SECTION_TO_BLOCK[targetId] || 'anual';
  activateBlock(block);

  // Mostrar sección
  tabSections.forEach(s => s.classList.remove('tab-active'));
  const section = document.getElementById(targetId);
  if (section) {{
    section.classList.add('tab-active');
    window.dispatchEvent(new Event('resize'));
  }}

  // Marcar sub-link activo
  subLinks.forEach(a => a.classList.remove('active'));
  const link = document.querySelector(`.nav-sub a[href="#${{targetId}}"]`);
  if (link) link.classList.add('active');

  if (_tabInits[targetId]) {{
    var _fn = _tabInits[targetId];
    _tabInits[targetId] = null;   // run-once: evita re-crear Chart.js sobre el mismo canvas
    setTimeout(_fn, 60);
  }}
}}

// Click en pestaña top → activa bloque + muestra sección default
topLinks.forEach(link => {{
  link.addEventListener('click', e => {{
    e.preventDefault();
    const block = link.dataset.block;
    const targetId = DEFAULT_SECTION[block];
    showSection(targetId);
    history.pushState(null, '', '#' + targetId);
  }});
}});

// Click en sub-pestaña → muestra esa sección
subLinks.forEach(link => {{
  link.addEventListener('click', e => {{
    e.preventDefault();
    const targetId = link.getAttribute('href').slice(1);
    showSection(targetId);
    history.pushState(null, '', '#' + targetId);
  }});
}});

// Handle browser back/forward
window.addEventListener('popstate', () => {{
  const id = location.hash.slice(1) || 'portada';
  showSection(id);
}});

// Init from URL hash if present
(function() {{
  const initId = location.hash.slice(1) || 'portada';
  showSection(initId);
}})();

// Compatibilidad: algunos handlers viejos usan '.nav a[href="..."]'
// Los redirigimos para que sigan funcionando con la nueva estructura
const navLinks = document.querySelectorAll('.nav-sub a[href^="#"]');
function showTab(id) {{ showSection(id); }}

// ── Dimension sub-tabs ───────────────────────────────────────────────────────
const DIM_TAB_DATA = {dim_tab_data_json};

function scoreToColor(s) {{
  if (s <= 30) return '#e05c5c';
  if (s <= 50) return '#e67e22';
  if (s <= 65) return '#f1c40f';
  if (s <= 80) return '#2ecc71';
  return '#00d4aa';
}}

const dimInitialized = {{}};

function initDimTab(dimId) {{
  const d = DIM_TAB_DATA[dimId];
  if (!d) return;
  const el = document.getElementById('dimview-' + dimId);
  if (!el) return;
  const color = scoreToColor(d.current);

  const varRows = d.vars.map(v => {{
    const dc = v.direction === 'positive' ? '#00d4aa' : '#e05c5c';
    const da = v.direction === 'positive' ? '&#9650; positiva' : '&#9660; negativa';
    const noData = v.val === null || v.val === undefined;
    const isWorst = !noData && v.val === 0;
    const vc = noData ? '#666' : (isWorst ? '#e05c5c' : (v.val >= 50 ? '#00d4aa' : (v.val >= 30 ? '#e67e22' : '#e05c5c')));
    const yrBadge = (!noData && v.val_yr) ? `<span style="margin-left:5px;color:#666;font-size:.62rem">${{v.val_yr}}</span>` : '';
    const badge = isWorst
      ? `<span style="margin-left:6px;background:#e05c5c22;color:#e05c5c;border:1px solid #e05c5c44;padding:1px 6px;border-radius:8px;font-size:.62rem">Peor registro histórico</span>`
      : (noData
        ? `<span style="margin-left:6px;background:#55555522;color:#888;border:1px solid #55555544;padding:1px 6px;border-radius:8px;font-size:.62rem">sin dato</span>`
        : '');
    const scoreDisplay = noData ? '—' : v.val;
    return `<tr>
      <td style="font-size:.78rem;padding:6px 8px">${{v.label}}${{badge}}</td>
      <td style="text-align:center;font-weight:600;padding:6px 8px">${{Math.round(v.weight*100)}}%</td>
      <td style="padding:6px 8px"><span style="background:#21262d;padding:2px 7px;border-radius:10px;font-size:.68rem">${{v.source}}</span></td>
      <td style="color:${{dc}};font-size:.72rem;padding:6px 8px">${{da}}</td>
      <td style="text-align:right;font-weight:700;color:${{vc}};padding:6px 8px">${{scoreDisplay}}${{yrBadge}}</td>
    </tr>`;
  }}).join('');

  const chartHeight = Math.max(180, d.vars.length * 40);

  el.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
      <div class="chart-card">
        <div class="ct">${{d.name}}</div>
        <div class="cs">Peso en el ICIV: ${{Math.round(d.weight*100)}}%</div>
        <div class="stats-row" style="margin-bottom:16px">
          <div class="stat">
            <div class="stat-label">Score actual</div>
            <div class="stat-val" style="color:${{color}}">${{d.current}}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Promedio</div>
            <div class="stat-val stat-neu">${{d.avg}}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Mínimo</div>
            <div class="stat-val stat-down">${{d.min_val}}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Máximo</div>
            <div class="stat-val stat-up">${{d.max_val}}</div>
          </div>
        </div>
        <div style="font-size:.84rem;color:var(--text);line-height:1.65;padding-top:12px;border-top:1px solid var(--border)">${{d.description}}</div>
      </div>
      <div class="chart-card">
        <div class="ct">Score por variable — último dato real disponible</div>
        <div class="cs">Valor normalizado (0–100) · verde = dirección positiva · [año] = último dato real</div>
        <div class="chart-wrap" style="height:${{chartHeight}}px">
          <canvas id="cDimVars-${{dimId}}"></canvas>
        </div>
      </div>
    </div>
    <div class="chart-card" style="margin-bottom:20px">
      <div class="ct">Evolución histórica — ${{d.name}}</div>
      <div class="cs">Score de dimensión 0–100 · serie completa 2000–presente</div>
      <div class="chart-wrap" style="height:260px">
        <canvas id="cDimHist-${{dimId}}"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <div class="ct">Variables de la dimensión</div>
      <div class="cs">Desglose metodológico — peso, fuente, dirección y score actual</div>
      <table class="dim-var-table" style="margin-top:8px">
        <thead><tr>
          <th>Variable</th><th style="text-align:center">Peso</th>
          <th>Fuente</th><th>Dirección</th><th style="text-align:right">Score</th>
        </tr></thead>
        <tbody>${{varRows}}</tbody>
      </table>
    </div>`;

  // Historical line chart
  new Chart(document.getElementById('cDimHist-' + dimId), {{
    type: 'line',
    data: {{
      labels: years,
      datasets: [{{
        label: d.name,
        data: d.hist,
        borderColor: color,
        backgroundColor: color + '22',
        borderWidth: 2.5,
        pointRadius: 3,
        pointBackgroundColor: color,
        tension: 0.3,
        fill: true,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        y: {{ min: 0, max: 100, grid: {{ color: '#21262d' }} }},
        x: {{ grid: {{ color: '#21262d' }} }}
      }}
    }}
  }});

  // Variable bar chart
  // v.val === null  → sin dato (variable con NaN real, ej. reservas sin reportar)
  // v.val === 0     → dato real, peor registro historico de Venezuela
  const varBg  = d.vars.map(v => v.val === null ? '#55555533' : (v.direction === 'positive' ? '#00d4aa66' : '#e05c5c66'));
  const varBdr = d.vars.map(v => v.val === null ? '#888888'   : (v.direction === 'positive' ? '#00d4aa'   : '#e05c5c'));
  new Chart(document.getElementById('cDimVars-' + dimId), {{
    type: 'bar',
    data: {{
      labels: d.vars.map(v => v.val === null ? v.label + ' (sin dato)' : v.label + (v.label_yr || '')),
      datasets: [{{
        label: 'Score (0-100)',
        data: d.vars.map(v => v.val === null ? 0 : v.val),
        backgroundColor: varBg,
        borderColor: varBdr,
        borderWidth: 1,
        borderRadius: 4,
        minBarLength: 2,
      }}]
    }},
    options: {{
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: ctx => {{
          const v = d.vars[ctx.dataIndex];
          if (v.val === null) return 'Sin dato — Venezuela no publica esta variable';
          if (v.val === 0)    return 'Score: 0 — Peor registro historico';
          return `Score: ${{v.val}}`;
        }} }} }}
      }},
      scales: {{
        x: {{ min: 0, max: 100, grid: {{ color: '#21262d' }} }},
        y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}
      }}
    }}
  }});
}}

function showDimTab(dimId) {{
  document.querySelectorAll('.dim-stab').forEach(b => b.classList.remove('dim-stab-active'));
  document.querySelectorAll('.dim-view').forEach(v => v.classList.remove('dim-view-active'));
  const btn  = document.querySelector(`.dim-stab[data-dim="${{dimId}}"]`);
  const view = document.getElementById('dimview-' + dimId);
  if (btn)  btn.classList.add('dim-stab-active');
  if (view) view.classList.add('dim-view-active');
  if (dimId !== 'todas' && !dimInitialized[dimId]) {{
    dimInitialized[dimId] = true;
    initDimTab(dimId);
  }}
  window.dispatchEvent(new Event('resize'));
}}

document.querySelectorAll('.dim-stab').forEach(btn => {{
  btn.addEventListener('click', () => showDimTab(btn.dataset.dim));
}});

// ── SATV ──────────────────────────────────────────────────────────────────────
(function() {{
  const SATV = {satv_json};
  if (!SATV || !SATV.resumen) return;

  const r   = SATV.resumen;
  const NIV_COLOR = {{ critico:'#e05c5c', precaucion:'#e67e22', normal:'#2ecc71' }};
  const NIV_EMOJI = {{ critico:'', precaucion:'', normal:'' }};
  const TEND_LABEL = {{
    deterioro_acelerado:'Deterioro acelerado', deterioro:'Deterioro',
    estable:'Estable', recuperacion:'Recuperación', recuperacion_acelerada:'Recuperación acelerada'
  }};

  // ── Resumen KPIs ────────────────────────────────────────────────────────────
  const tendColor = r.iciv_tendencia === 'deterioro' ? '#e05c5c'
                  : r.iciv_tendencia === 'recuperacion' ? '#2ecc71' : '#8b949e';
  const tendLabel = r.iciv_tendencia === 'deterioro' ? '↓ Deterioro'
                  : r.iciv_tendencia === 'recuperacion' ? '↑ Recuperación' : '→ Estable';
  const kpiData = [
    {{ val: r.dims_criticas,   lbl: 'Señales críticas',        color: '#e05c5c' }},
    {{ val: r.dims_precaucion, lbl: 'En precaución',           color: '#e67e22' }},
    {{ val: r.dims_normales,   lbl: 'En zona normal',          color: '#2ecc71' }},
    {{ val: `${{r.iciv_delta_1y > 0 ? '+' : ''}}${{r.iciv_delta_1y}}`, lbl: tendLabel, color: tendColor }},
  ];
  document.getElementById('satvResumen').innerHTML = kpiData.map(k => `
    <div class="satv-kpi">
      <div class="satv-kpi-val" style="color:${{k.color}}">${{k.val}}</div>
      <div class="satv-kpi-lbl">${{k.lbl}}</div>
    </div>`).join('');

  // ── Alertas activas ─────────────────────────────────────────────────────────
  const alertasEl = document.getElementById('satvAlertas');
  if (SATV.alertas_activas.length === 0) {{
    alertasEl.innerHTML = '<div class="satv-alert normal"><div class="satv-alert-msg">Sin alertas activas en el período actual.</div></div>';
  }} else {{
    alertasEl.innerHTML = SATV.alertas_activas.map(a => `
      <div class="satv-alert ${{a.nivel}}">
        <div class="satv-alert-icon">${{a.icono}}</div>
        <div>
          <div class="satv-alert-tipo" style="color:${{NIV_COLOR[a.nivel] || '#8b949e'}}">${{a.tipo}}</div>
          <div class="satv-alert-msg">${{a.mensaje}}</div>
        </div>
      </div>`).join('');
  }}

  // ── Dimensiones ─────────────────────────────────────────────────────────────
  const dimsEl = document.getElementById('satvDims');
  const dimEntries = Object.entries(SATV.dimensiones);
  dimsEl.innerHTML = dimEntries.map(([id, d]) => {{
    const noData  = d.score_actual === null || d.score_actual === undefined;
    const nivel   = noData ? 'sin_dato' : d.nivel;
    const c       = NIV_COLOR[nivel] || '#8b949e';
    const score_display = noData ? '—' : d.score_actual.toFixed !== undefined ? d.score_actual.toFixed(1) : d.score_actual;
    const badge_labels  = {{'critico':'CRÍTICO','precaucion':'PRECAUCIÓN','normal':'NORMAL','sin_dato':'SIN DATO'}};
    const sign = d.delta_1y >= 0 ? '+' : '';
    const nVars = d.n_vars_disponibles !== undefined ? `${{d.n_vars_disponibles}}/${{d.n_vars_total}} vars` : '';
    return `
      <div class="satv-dim-card">
        <div class="satv-dim-header">
          <span class="satv-dim-name">${{d.nombre}}</span>
          <span class="satv-badge ${{nivel}}">${{badge_labels[nivel] || nivel.toUpperCase()}}</span>
        </div>
        <div class="satv-dim-score" style="color:${{c}}">${{score_display}}</div>
        ${{noData ? `<div style="font-size:.72rem;color:#8b949e;margin-top:4px">Sin datos para ${{typeof CURRENT_YEAR !== 'undefined' ? CURRENT_YEAR : ''}}</div>` : ''}}
        <div class="satv-dim-deltas">
          ${{!noData ? `<span>Δ1m: <strong style="color:${{d.delta_1y<0?'#e05c5c':'#2ecc71'}}">${{sign}}${{d.delta_1y}}</strong></span>
          <span>Δ3m: <strong>${{d.delta_3y >= 0 ? '+' : ''}}${{d.delta_3y}}</strong></span>
          <span>Δ6m: <strong>${{d.delta_5y >= 0 ? '+' : ''}}${{d.delta_5y}}</strong></span>
          <span style="margin-left:auto">${{d.arrow}} ${{TEND_LABEL[d.tendencia] || d.tendencia}}</span>` : `<span style="color:#8b949e">Ver última tendencia disponible →</span>`}}
        </div>
        <div class="satv-dim-var">
          ${{noData
            ? `<span style="color:#8b949e">Sin indicadores disponibles en ${{typeof CURRENT_YEAR !== 'undefined' ? CURRENT_YEAR : 'año actual'}}</span>`
            : `Var. crítica: <strong>${{d.variable_critica.replace(/_/g,' ')}}</strong> (${{d.variable_critica_score}} pts)
               ${{nVars ? `<span style="color:#8b949e;font-size:.68rem;margin-left:6px">· ${{nVars}}</span>` : ''}}`
          }}
        </div>
      </div>`;
  }}).join('');

  // ── Variables críticas ───────────────────────────────────────────────────────
  document.getElementById('satvVarTable').innerHTML = `
    <table class="satv-var-table">
      <thead><tr><th>Señal</th><th>Score</th><th>Δ1m</th><th>Grupo</th></tr></thead>
      <tbody>
        ${{SATV.variables_criticas.map(v => {{
          const barW = Math.max(2, v.score);
          const barC = v.score < 25 ? '#e05c5c' : v.score < 50 ? '#e67e22' : '#00d4aa';
          const dSign = v.delta_1y >= 0 ? '+' : '';
          const dCol  = v.delta_1y < 0 ? '#e05c5c' : '#2ecc71';
          return `<tr>
            <td style="font-size:.76rem">${{v.label}}</td>
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <div class="satv-bar-mini" style="width:${{barW}}%;background:${{barC}}"></div>
                <span style="font-weight:700;color:${{barC}}">${{v.score}}</span>
              </div>
            </td>
            <td style="color:${{dCol}};font-weight:600">${{dSign}}${{v.delta_1y}}</td>
            <td style="font-size:.72rem;color:var(--muted)">${{v.dimension.replace('_',' ')}}</td>
          </tr>`;
        }}).join('')}}
      </tbody>
    </table>`;

  // ── Timeline histórico (Chart.js scatter) ────────────────────────────────────
  const timelineEvents = SATV.timeline_historico || [];
  // Agrupar por monitor para el eje Y.
  const dimOrder = ['pulse'];
  const dimLabel = {{
    pulse:'Pulse mensual'
  }};

  const datasets = dimOrder.map(dim => {{
    const pts = timelineEvents
      .filter(e => e.dimension === dim)
      .map(e => ({{ x: e.año + ((e.mes || 1) - 1) / 12, y: dimOrder.indexOf(dim), nivel: e.nivel, evento: e.tipo, mes: e.mes }}));
    return {{
      label: dimLabel[dim] || dim,
      data: pts,
      pointBackgroundColor: pts.map(p => NIV_COLOR[p.nivel] || '#8b949e'),
      pointBorderColor:     pts.map(p => NIV_COLOR[p.nivel] || '#8b949e'),
      pointRadius: 8,
      pointHoverRadius: 10,
      showLine: false,
    }};
  }}).filter(ds => ds.data.length > 0);

  new Chart(document.getElementById('cSatvTimeline'), {{
    type: 'scatter',
    data: {{ datasets }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{
          label: ctx => `${{ctx.raw.evento}} (${{Math.floor(ctx.raw.x)}}-${{String(ctx.raw.mes || 1).padStart(2,'0')}})`,
          title: () => '',
        }}}}
      }},
      scales: {{
        x: {{
          min: 2010, max: {settings.series.end_year} + 1,
          grid: {{ color: '#21262d' }},
          ticks: {{ stepSize: 2, font: {{ size: 9 }} }}
        }},
        y: {{
          min: -0.5, max: dimOrder.length - 0.5,
          grid: {{ color: '#21262d' }},
          ticks: {{
            callback: val => dimLabel[dimOrder[val]] || '',
            font: {{ size: 9 }}
          }}
        }}
      }}
    }}
  }});
}})();

// ── Guardian News ─────────────────────────────────────────────────────────────
(function() {{
  const INTL_NEWS = {intl_news_json};
  const GUARDIAN_KEY = '9d4cf6fc-8864-4693-adda-987c76fc7476';
  const PAGE_SIZE    = 12;
  let   allArticles  = [];
  let   filtered     = [];
  let   shown        = 0;
  let   activeTag    = 'all';

  function fromDate() {{
    const d = new Date();
    d.setDate(d.getDate() - 90);
    return d.toISOString().split('T')[0];
  }}

  function sectionTag(sectionId) {{
    const map = {{ economy:'business', politics:'politics', world:'world', business:'business' }};
    return Object.values(map).includes(sectionId) ? sectionId : 'other';
  }}

  function fmtDate(iso) {{
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('es-VE', {{ year:'numeric', month:'short', day:'numeric' }});
  }}

  function renderIntlNews() {{
    const grid = document.getElementById('intlNewsGrid');
    if (!grid) return;
    if (!INTL_NEWS || INTL_NEWS.length === 0) {{
      grid.innerHTML = '<div class="news-status">No hay snapshot internacional disponible. El pipeline no fabrica noticias si el RSS no entrega fuentes validas.</div>';
      return;
    }}
    grid.innerHTML = INTL_NEWS.slice(0, 12).map(a => `
      <div class="news-card">
        <div class="news-body">
          <div class="news-section">${{a.source || 'Fuente internacional'}}</div>
          <div class="news-title"><a href="${{a.url}}" target="_blank" rel="noopener">${{a.title}}</a></div>
          <div class="news-trail">${{a.query || 'Venezuela economy'}}</div>
          <div class="news-date">${{fmtDate(a.published_at)}}</div>
        </div>
      </div>`).join('');
  }}

  function renderCard(a) {{
    const thumb = a.fields?.thumbnail
      ? `<img class="news-thumb" src="${{a.fields.thumbnail}}" alt="" loading="lazy" onerror="this.style.display='none';this.nextSibling.style.display='flex'">`
        + `<div class="news-thumb-ph" style="display:none"></div>`
      : `<div class="news-thumb-ph"></div>`;
    const trail = a.fields?.trailText
      ? `<div class="news-trail">${{a.fields.trailText.replace(/<[^>]+>/g,'')}}</div>` : '';
    return `
      <div class="news-card" data-section="${{a.sectionId || ''}}">
        ${{thumb}}
        <div class="news-body">
          <div class="news-section">${{a.sectionName || 'Venezuela'}}</div>
          <div class="news-title"><a href="${{a.webUrl}}" target="_blank" rel="noopener">${{a.webTitle}}</a></div>
          ${{trail}}
          <div class="news-date">${{fmtDate(a.webPublicationDate)}}</div>
        </div>
      </div>`;
  }}

  function applyFilter() {{
    filtered = activeTag === 'all'
      ? allArticles
      : allArticles.filter(a => sectionTag(a.sectionId || '') === activeTag || (a.sectionId || '').includes(activeTag));
    shown = 0;
    showMore(true);
  }}

  function showMore(reset) {{
    const grid   = document.getElementById('newsGrid');
    const btnMore = document.getElementById('newsLoadMore');
    const batch  = filtered.slice(shown, shown + PAGE_SIZE);
    if (reset) grid.innerHTML = '';
    if (filtered.length === 0) {{
      grid.innerHTML = '<div class="news-status">No se encontraron artículos para esta categoría.</div>';
      btnMore.style.display = 'none';
      return;
    }}
    batch.forEach(a => grid.insertAdjacentHTML('beforeend', renderCard(a)));
    shown += batch.length;
    btnMore.style.display = shown < filtered.length ? 'inline-block' : 'none';
  }}

  async function loadNews() {{
    renderIntlNews();
    const grid = document.getElementById('newsGrid');
    const url  = `https://content.guardianapis.com/search`
               + `?section=world&tag=world/venezuela`
               + `&q=Venezuela`
               + `&api-key=${{GUARDIAN_KEY}}`
               + `&order-by=newest&page-size=50`
               + `&show-fields=trailText,thumbnail`
               + `&from-date=${{fromDate()}}`;
    try {{
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${{resp.status}}`);
      const data = await resp.json();
      allArticles = data.response?.results || [];
      if (allArticles.length === 0) {{
        grid.innerHTML = '<div class="news-status">No se encontraron noticias recientes sobre Venezuela.</div>';
        return;
      }}
      applyFilter();
    }} catch(err) {{
      grid.innerHTML = `<div class="news-status">No se pudo cargar noticias: ${{err.message}}<br>
        <a href="https://www.theguardian.com/world/venezuela" target="_blank" rel="noopener"
           style="color:var(--accent)">Ver en The Guardian →</a></div>`;
    }}
  }}

  // Filter chips
  document.getElementById('newsFilter').addEventListener('click', e => {{
    const chip = e.target.closest('.news-chip');
    if (!chip) return;
    document.querySelectorAll('#newsFilter .news-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeTag = chip.dataset.tag;
    applyFilter();
  }});

  // Load more
  document.getElementById('newsLoadMore').addEventListener('click', () => showMore(false));

  // Load news when the noticias tab is first activated (compatible con nuevo nav 2 niveles)
  let newsLoaded = false;
  if (typeof _tabInits !== 'undefined') {{
    _tabInits['noticias'] = function() {{
      if (!newsLoaded) {{ newsLoaded = true; loadNews(); }}
    }};
  }}
  // Fallback: también escucha clicks en cualquier link que lleve a #noticias
  document.querySelectorAll('[href="#noticias"]').forEach(function(el) {{
    el.addEventListener('click', function() {{
      if (!newsLoaded) {{ newsLoaded = true; setTimeout(loadNews, 100); }}
    }});
  }});
  if (window.location.hash === '#noticias') {{ newsLoaded = true; setTimeout(loadNews, 200); }}
}})();

// ── MAPA COROPLÉTICO — Luminosidad Nocturna por Estado ─────────────────────
(function() {{
  const GEOJSON    = {_geojson_str};
  const NTL_DATA   = {_viirs_states_json};
  const START_YEAR = {settings.series.start_year};
  const END_YEAR   = {settings.series.end_year};

  if (!GEOJSON || !GEOJSON.features || !GEOJSON.features.length) return;

  let map = null, geojsonLayer = null, currentYear = END_YEAR, animTimer = null;

  function ntlColor(val) {{
    // Escala oscuro (colapso) → amarillo brillante (activo)
    if (val === null || val === undefined) return '#2a2a2a';
    if (val < 10)  return '#1a1a2e';
    if (val < 20)  return '#16213e';
    if (val < 30)  return '#0f3460';
    if (val < 40)  return '#1b4f72';
    if (val < 50)  return '#1a5276';
    if (val < 60)  return '#2471a3';
    if (val < 70)  return '#c8a400';
    if (val < 80)  return '#d4ac0d';
    if (val < 90)  return '#f1c40f';
    return '#f9e400';
  }}

  // Devuelve el valor NTL para un estado y un año.
  // Si el año exacto no tiene dato (ej. 2025-2026 sin datos satelitales),
  // usa el último año disponible hacia atras (el usuario pidió esto explícitamente).
  function getVal(cod, yr) {{
    const stateData = NTL_DATA[cod];
    if (!stateData) return {{ val: null, dataYear: null }};
    // Intenta año exacto
    let val = stateData[yr] ?? stateData[String(yr)] ?? null;
    if (val !== null) return {{ val: val, dataYear: yr }};
    // Fallback: último año con dato <= yr
    const years = Object.keys(stateData).map(Number).sort((a,b) => b - a);
    const lastYr = years.find(y => y <= yr);
    if (lastYr !== undefined) {{
      val = stateData[lastYr] ?? stateData[String(lastYr)] ?? null;
      return {{ val: val, dataYear: lastYr }};
    }}
    return {{ val: null, dataYear: null }};
  }}

  function styleFeature(feature) {{
    const cod = feature.properties.cod;
    const {{ val }} = getVal(cod, currentYear);
    return {{
      fillColor: ntlColor(val),
      fillOpacity: 0.82,
      color: '#444',
      weight: 0.8,
    }};
  }}

  function onEachFeature(feature, layer) {{
    layer.on({{
      mouseover: function(e) {{
        const cod  = feature.properties.cod;
        const nombre = feature.properties.nombre;
        const {{ val, dataYear }} = getVal(cod, currentYear);
        const valStr = val !== null ? val.toFixed(1) + '/100' : 'sin dato';
        const yearNote = (dataYear !== null && dataYear !== currentYear)
          ? ` <span style="color:#e67e22;font-size:.8em">(dato: ${{dataYear}})</span>` : '';
        layer.setStyle({{ weight: 2, color: '#00d4aa', fillOpacity: 0.95 }});
        layer.bindTooltip(
          `<b>${{nombre}}</b><br>NTL Index: <b>${{valStr}}</b><br>Año: ${{currentYear}}${{yearNote}}`,
          {{ direction: 'top', sticky: true, className: 'leaflet-ven-tooltip' }}
        ).openTooltip();
      }},
      mouseout: function() {{
        geojsonLayer.resetStyle(layer);
        layer.closeTooltip();
      }}
    }});
  }}

  function updateRanking(yr) {{
    const stateVals = GEOJSON.features
      .filter(f => f.properties.cod !== 'DF')
      .map(f => {{ const {{ val }} = getVal(f.properties.cod, yr); return {{ cod: f.properties.cod, nombre: f.properties.nombre, val }}; }})
      .filter(s => s.val !== null)
      .sort((a,b) => b.val - a.val);
    const top5 = stateVals.slice(0,5);
    const bot3 = stateVals.slice(-3);
    const el = document.getElementById('mapaRanking');
    if (!el) return;
    let html = '<div style="margin-bottom:8px;font-size:.7rem;color:var(--accent);font-weight:600">MAYOR ACTIVIDAD</div>';
    top5.forEach((s,i) => {{
      const bar = Math.round(s.val);
      html += `<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
        <span style="width:16px;text-align:right;color:var(--muted);font-size:.7rem">${{i+1}}</span>
        <div style="flex:1;background:#333;border-radius:3px;height:10px;overflow:hidden">
          <div style="width:${{bar}}%;height:100%;background:${{ntlColor(s.val)}}"></div>
        </div>
        <span style="font-size:.7rem;width:80px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${{s.nombre.replace('DistritoCapital','D.Capital').replace('NuevaEsparta','Nva.Esparta')}}</span>
        <span style="font-size:.7rem;color:var(--muted);width:30px;text-align:right">${{s.val.toFixed(0)}}</span>
      </div>`;
    }});
    html += '<div style="margin-top:10px;margin-bottom:6px;font-size:.7rem;color:#e05c5c;font-weight:600">MENOR ACTIVIDAD</div>';
    bot3.forEach(s => {{
      const bar = Math.round(s.val);
      html += `<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
        <div style="flex:1;background:#333;border-radius:3px;height:10px;overflow:hidden">
          <div style="width:${{bar}}%;height:100%;background:${{ntlColor(s.val)}}"></div>
        </div>
        <span style="font-size:.7rem;width:80px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${{s.nombre}}</span>
        <span style="font-size:.7rem;color:var(--muted);width:30px;text-align:right">${{s.val.toFixed(0)}}</span>
      </div>`;
    }});
    el.innerHTML = html;
  }}

  function buildLegend() {{
    const el = document.getElementById('mapaLegend');
    if (!el) return;
    const steps = [[0,'< 10','Apagado'],[ 30,'30–50','Bajo'],[50,'50–70','Moderado'],[70,'70–90','Alto'],[90,'> 90','Máximo']];
    el.innerHTML = steps.map(([v,label,desc]) =>
      `<div style="display:flex;align-items:center;gap:8px">
        <div style="width:18px;height:18px;background:${{ntlColor(v+1)}};border-radius:3px;border:1px solid #555"></div>
        <span style="font-size:.72rem;color:var(--muted)">${{label}} — ${{desc}}</span>
      </div>`
    ).join('');
  }}

  function initMap() {{
    const container = document.getElementById('mapaContainer');
    if (!container || map) return;

    map = L.map('mapaContainer', {{
      center: [7.5, -66.0],
      zoom: 5,
      zoomControl: true,
      attributionControl: true,
    }});

    // Tile oscuro (compatible con el tema dark del dashboard)
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_nolabels/{{z}}/{{x}}/{{y}}{{r}}.png', {{
      attribution: '© CartoDB | © OpenStreetMap contributors',
      subdomains: 'abcd',
      maxZoom: 10,
    }}).addTo(map);

    geojsonLayer = L.geoJSON(GEOJSON, {{
      style: styleFeature,
      onEachFeature: onEachFeature,
    }}).addTo(map);

    map.fitBounds(geojsonLayer.getBounds().pad(0.05));
    buildLegend();
    updateRanking(currentYear);
  }}

  function updateMap(yr) {{
    currentYear = yr;
    // Detectar si el año seleccionado tiene datos o se usa el ultimo disponible
    const firstState = GEOJSON.features.find(f => f.properties.cod !== 'DF');
    const {{ dataYear }} = firstState ? getVal(firstState.properties.cod, yr) : {{ dataYear: yr }};
    const noDataNote = document.getElementById('mapaNoDataNote');
    if (noDataNote) {{
      if (dataYear !== null && dataYear !== yr) {{
        noDataNote.textContent = `(mostrando datos de ${{dataYear}} — sin satelital para ${{yr}})`;
        noDataNote.style.display = 'inline';
      }} else {{
        noDataNote.style.display = 'none';
      }}
    }}
    document.getElementById('mapaYearLabel').textContent = yr;
    if (geojsonLayer) geojsonLayer.setStyle(styleFeature);
    updateRanking(yr);
  }}

  // Slider
  const slider = document.getElementById('mapaYear');
  if (slider) {{
    slider.addEventListener('input', () => updateMap(parseInt(slider.value)));
  }}

  // Animate button
  const playBtn = document.getElementById('mapaPlayBtn');
  if (playBtn) {{
    playBtn.addEventListener('click', () => {{
      if (animTimer) {{
        clearInterval(animTimer);
        animTimer = null;
        playBtn.textContent = '▶ Animar';
        return;
      }}
      playBtn.textContent = '⏹ Detener';
      let yr = START_YEAR;
      slider.value = yr;
      updateMap(yr);
      animTimer = setInterval(() => {{
        yr++;
        if (yr > END_YEAR) {{ yr = START_YEAR; }}
        slider.value = yr;
        updateMap(yr);
      }}, 700);
    }});
  }}

  // Initialize map when tab is clicked (compatible con nuevo nav 2 niveles)
  function initMapTab() {{
    setTimeout(initMap, 100);
    setTimeout(function() {{ if (window.__buildBMMap) window.__buildBMMap(); }}, 120);
  }}
  if (typeof _tabInits !== 'undefined') {{
    _tabInits['mapa'] = initMapTab;
  }}
  // Fallback: escucha clicks en cualquier link que lleve a #mapa
  document.querySelectorAll('[href="#mapa"]').forEach(function(el) {{
    el.addEventListener('click', initMapTab);
  }});
  if (window.location.hash === '#mapa') setTimeout(initMapTab, 200);
}})();

// ── HISTORIA — sub-tabs Gráfico / Tabla ─────────────────────────────────────
(function() {{
  const tabs = document.querySelectorAll('.hist-tab');
  tabs.forEach(btn => {{
    btn.addEventListener('click', () => {{
      const view = btn.dataset.view;
      tabs.forEach(b => {{
        b.style.color = 'var(--muted)';
        b.style.fontWeight = '500';
        b.style.borderBottomColor = 'transparent';
      }});
      btn.style.color = 'var(--text)';
      btn.style.fontWeight = '600';
      btn.style.borderBottomColor = view === 'grafico' ? 'var(--accent)' : 'var(--accent)';
      document.getElementById('histView-grafico').style.display = view === 'grafico' ? '' : 'none';
      document.getElementById('histView-tabla').style.display  = view === 'tabla'   ? '' : 'none';
    }});
  }});
}})();

// ── SCORE ACTUAL — year selector ────────────────────────────────────────────
(function() {{
  const SBY = {score_by_year_json};  // {{year: {{iciv, coverage, prev, dims}}}}

  // Gauge constants
  const ARC_TOTAL = 282.74;
  const BAND_BREAKS = [
    [0,  30,   0.0,  84.8,  '#e05c5c'],
    [30, 50,  84.8,  56.5,  '#e67e22'],
    [50, 65, 141.3,  42.4,  '#f1c40f'],
    [65, 80, 183.7,  42.4,  '#2ecc71'],
    [80, 100,226.1,  56.5,  '#00d4aa'],
  ];

  function scoreColor(s) {{
    if (s <= 30) return '#e05c5c';
    if (s <= 50) return '#e67e22';
    if (s <= 65) return '#f1c40f';
    if (s <= 80) return '#2ecc71';
    return '#00d4aa';
  }}

  function scoreLabel(s) {{
    if (s <= 30) return 'Alto Riesgo';
    if (s <= 50) return 'Riesgo Moderado-Alto';
    if (s <= 65) return 'Riesgo Moderado';
    if (s <= 80) return 'Bajo Riesgo';
    return 'Muy Bajo Riesgo';
  }}

  function scoreRecommendation(s) {{
    if (s <= 30) return 'El clima de inversión en Venezuela presenta condiciones de <strong>Alto Riesgo</strong>. No se recomienda inversión directa en este período. Las condiciones macroeconómicas, institucionales y energéticas representan barreras estructurales significativas.';
    if (s <= 50) return 'Las condiciones reflejan un entorno de <strong>Riesgo Moderado-Alto</strong>. Solo sectores con alta tolerancia al riesgo y cobertura específica (commodity extraction, remesas, telecomunicaciones) pueden considerar operaciones bajo análisis de riesgo político exhaustivo.';
    if (s <= 65) return 'El ICIV indica un entorno de <strong>Riesgo Moderado</strong>. Viable con due diligence reforzado, estructura contractual de mitigación de riesgo y estrategia de salida definida. Preferible a través de joint-ventures con socios locales.';
    if (s <= 80) return 'El indicador señala condiciones de <strong>Bajo Riesgo</strong>. Ambiente favorable para inversión con análisis sectorial estándar. Se recomienda diversificación entre múltiples sectores para capturar el ciclo de recuperación.';
    return 'El ICIV presenta condiciones de <strong>Muy Bajo Riesgo</strong>, comparable a mercados emergentes estables de la región. Inversión recomendada con análisis sectorial convencional.';
  }}

  function alertClass(s) {{
    if (s <= 30) return 'alert alert-bad';
    if (s <= 50) return 'alert alert-warn';
    return 'alert alert-info';
  }}

  window.selectScoreYear = function(yr) {{
    const data = SBY[yr];
    if (!data) return;
    const s = data.iciv;
    const col = scoreColor(s);
    const lbl = scoreLabel(s);
    const cov = data.coverage;

    // Update header subtitle
    const hdr = document.getElementById('scoreHeaderSub');
    if (hdr) hdr.textContent = 'Venezuela · ' + yr;

    // Update year buttons
    document.querySelectorAll('.score-yr-btn').forEach(btn => {{
      btn.classList.toggle('score-yr-active', parseInt(btn.textContent) === yr);
    }});

    // Coverage tier function (mirrors Python _cov_tier)
    function covTier(pct) {{
      if (pct >= 85) return ['Histórico',   '#00d4aa'];
      if (pct >= 70) return ['Útil',        '#2ecc71'];
      if (pct >= 50) return ['Parcial',     '#e6a817'];
      return                ['Provisional', '#e74c3c'];
    }}
    const [tierLbl, tierCol] = covTier(cov);

    // Coverage badge — always visible, color-coded by tier
    const warn = document.getElementById('scoreCoverageWarn');
    const warnPct = document.getElementById('scoreCovWarnPct');
    const warnTxt = document.getElementById('scoreCovWarnTxt');
    const warnIcon = document.getElementById('scoreCovWarnIcon');
    if (warn) {{
      const low = cov < 60;
      warn.style.display = 'flex';
      warn.style.borderColor = tierCol;
      if (warnIcon) warnIcon.innerHTML = low ? '&#9888;' : '&#10003;';
      if (warnPct) {{
        warnPct.textContent = 'Cobertura de datos: ' + cov.toFixed(0) + '% · ' + tierLbl;
        warnPct.style.color = tierCol;
      }}
      if (warnTxt) {{
        const tierDesc = {{
          'Histórico':   'Series completas. Cobertura suficiente para análisis estadístico robusto.',
          'Útil':        'Mayoría de fuentes disponibles. Score representativo con pequeñas brechas de lag.',
          'Parcial':     'Fuentes anuales con lag de publicación. Resultado indicativo — confirmar cuando se publiquen WGI/HDI/WDI.',
          'Provisional': 'Solo fuentes de alta frecuencia disponibles. Score preliminar — uso exploratorio únicamente.'
        }};
        warnTxt.textContent = 'El score ' + yr + ' usa ' + cov.toFixed(0) + '% del peso del modelo. ' + (tierDesc[tierLbl] || '');
      }}
    }}

    // Stats cards
    const mainLbl = document.getElementById('scoreMainLbl');
    const mainVal = document.getElementById('scoreMainVal');
    const mainSub = document.getElementById('scoreMainSub');
    if (mainLbl) mainLbl.textContent = 'ICIV ' + yr;
    if (mainVal) {{ mainVal.textContent = s.toFixed(1); mainVal.style.color = col; }}
    if (mainSub) mainSub.textContent = lbl + ' · ' + cov.toFixed(0) + '% · ' + tierLbl;

    // Delta vs prev year
    const deltaVal = document.getElementById('scoreDeltaVal');
    const deltaSub = document.getElementById('scoreDeltaSub');
    if (data.prev !== null && data.prev !== undefined) {{
      const delta = s - data.prev;
      if (deltaVal) {{
        deltaVal.textContent = (delta >= 0 ? '+' : '') + delta.toFixed(1);
        deltaVal.className = 'stat-val ' + (delta >= 0 ? 'stat-up' : 'stat-down');
      }}
      if (deltaSub) deltaSub.textContent = 'puntos respecto a ' + (yr - 1);
    }} else {{
      if (deltaVal) {{ deltaVal.textContent = '—'; deltaVal.className = 'stat-val stat-neu'; }}
      if (deltaSub) deltaSub.textContent = 'primer año disponible';
    }}

    // Recommendation
    const alertDiv = document.getElementById('scoreAlertDiv');
    const alertTitle = document.getElementById('scoreAlertTitle');
    const alertBody  = document.getElementById('scoreAlertBody');
    if (alertDiv) alertDiv.className = alertClass(s);
    if (alertTitle) alertTitle.textContent = 'Recomendación de inversión ' + yr;
    if (alertBody) alertBody.innerHTML = scoreRecommendation(s);

    // Gauge
    const bandIdx = BAND_BREAKS.findIndex(([lo, hi]) => s <= hi) ?? 4;
    const band = BAND_BREAKS[Math.max(0, bandIdx)];
    const activeDashLen    = band[3];
    const activeDashOffset = band[2];
    const scoreArc = (s / 100) * ARC_TOTAL;
    const needleAngle = -90 + (s / 100) * 180;  // 180° arc (semicircle), not 270°

    const gaugeBand = document.getElementById('gaugeActiveBand');
    const gaugeFill = document.getElementById('gaugeFillArc');
    const gaugeNdl  = document.getElementById('gaugeNeedle');
    const gaugeBase = document.getElementById('gaugeNeedleBase');
    const gaugeNum  = document.getElementById('gaugeScoreNum');
    const gaugeCat  = document.getElementById('gaugeCatLbl');
    const gaugeTitle= document.getElementById('gaugeTitle');

    if (gaugeBand) {{
      gaugeBand.setAttribute('stroke', col);
      gaugeBand.setAttribute('stroke-dasharray', activeDashLen + ' 282.74');
      gaugeBand.setAttribute('stroke-dashoffset', '-' + activeDashOffset);
    }}
    // gaugeFill kept transparent (removed visual overlap issue)
    if (gaugeNdl) {{
      gaugeNdl.setAttribute('stroke', col);
      gaugeNdl.setAttribute('transform', 'rotate(' + needleAngle.toFixed(1) + ',110,110)');
    }}
    if (gaugeBase) gaugeBase.setAttribute('fill', col);
    if (gaugeNum) {{ gaugeNum.textContent = s.toFixed(1); gaugeNum.style.color = col; }}
    if (gaugeCat) {{ gaugeCat.textContent = lbl; gaugeCat.style.color = col; }}
    if (gaugeTitle) gaugeTitle.textContent = 'Indicador ICIV ' + yr;

    // Risk bands
    const rbIds = ['rb0','rb1','rb2','rb3','rb4'];
    const rbThresholds = [30, 50, 65, 80, 100];
    rbIds.forEach((id, i) => {{
      const el = document.getElementById(id);
      if (el) el.classList.toggle('active',
        (i === 0 && s <= 30) ||
        (i === 1 && s > 30 && s <= 50) ||
        (i === 2 && s > 50 && s <= 65) ||
        (i === 3 && s > 65 && s <= 80) ||
        (i === 4 && s > 80)
      );
    }});
  }};
}})();

// ── ESCENARIOS 2027–2030 ────────────────────────────────────────────────────
(function() {{
  const ESC = {escenarios_json} || {{}};

  const LABELS = {{ optimista: 'Optimista', base: 'Base', pesimista: 'Pesimista' }};
  const COLORS_MAP = {{ optimista:'#2ecc71', base:'#3498db', pesimista:'#e74c3c' }};
  const SC_NAMES   = ['base','optimista','pesimista'];
  const CANVAS_IDS = {{ base:'cEscBase', optimista:'cEscOpt', pesimista:'cEscPess' }};
  const KPI_IDS    = {{ base:'escKpiBase', optimista:'escKpiOpt', pesimista:'escKpiPess' }};
  const SUP_IDS    = {{ base:'escSupBase', optimista:'escSupOpt', pesimista:'escSupPess' }};

  const hist = ESC.historico;
  const chartInsts = {{}};

  // ── Esc tab switching ──────────────────────────────────────────────────────
  const escTabs  = document.querySelectorAll('.esc-tab');
  const escViews = document.querySelectorAll('.esc-view');
  escTabs.forEach(btn => {{
    btn.addEventListener('click', () => {{
      const name = btn.dataset.esc;
      escTabs.forEach(b => {{
        b.style.color = 'var(--muted)';
        b.style.fontWeight = '500';
        b.style.borderBottomColor = 'transparent';
      }});
      btn.style.color = 'var(--text)';
      btn.style.fontWeight = '600';
      btn.style.borderBottomColor = COLORS_MAP[name] || 'var(--accent)';
      escViews.forEach(v => v.style.display = 'none');
      const view = document.getElementById('escView-' + name);
      if (view) view.style.display = '';
      if (SC_NAMES.includes(name) && !chartInsts[name]) buildScChart(name);
      if (name === 'simulador' && !chartInsts['simulador']) initSimulator();
      if (name === 'montecarlo' && !chartInsts['montecarlo']) {{ buildMCChart(); buildProbCards(); buildParamsCard(); chartInsts['montecarlo'] = true; }}
    }});
  }});

  // ── Build per-scenario chart ───────────────────────────────────────────────
  function buildScChart(sc) {{
    const ctx = document.getElementById(CANVAS_IDS[sc]);
    if (!ctx) return;
    const existing = Chart.getChart ? Chart.getChart(ctx) : null;
    if (existing) existing.destroy();
    const d   = ESC.escenarios[sc];
    const col = COLORS_MAP[sc];
    const projYears = d.años;

    const datasets = [
      {{
        label: 'Histórico ICIV (2000–2026)',
        data: hist.años.map((y,i) => ({{ x:y, y:hist.valores[i] }})),
        borderColor: '#00d4aa', backgroundColor: 'transparent',
        borderWidth: 2.5, pointRadius: 2.5, tension: 0.3, order: 10,
      }},
      // CI band top
      {{
        label: '_ci_hi',
        data: projYears.map((y,i) => ({{ x:y, y:d.ci_hi[i] }})),
        borderColor: 'transparent', backgroundColor: col + '28',
        fill: '+1', pointRadius: 0, tension: 0.3, order: 5,
      }},
      // CI band bottom
      {{
        label: '_ci_lo',
        data: projYears.map((y,i) => ({{ x:y, y:d.ci_lo[i] }})),
        borderColor: 'transparent', backgroundColor: col + '28',
        fill: false, pointRadius: 0, tension: 0.3, order: 5,
      }},
      // Scenario line
      {{
        label: LABELS[sc],
        data: projYears.map((y,i) => ({{ x:y, y:d.valores[i] }})),
        borderColor: col, backgroundColor: 'transparent',
        borderWidth: 2.5, borderDash: sc==='base'?[]:[5,3],
        pointRadius: 5, pointHoverRadius: 7, tension: 0.3, order: 1,
      }},
    ];

    chartInsts[sc] = new Chart(ctx, {{
      type: 'line',
      data: {{ datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false, parsing: false,
        plugins: {{
          legend: {{ labels: {{ color:'#8b949e', filter: item => !item.text.startsWith('_'), boxWidth:22, font:{{size:11}} }} }},
          tooltip: {{ callbacks: {{ label: c => c.dataset.label.startsWith('_') ? null : `${{c.dataset.label}}: ${{c.parsed.y?.toFixed(1)}}` }} }},
          annotation: {{
            annotations: {{
              vline: {{ type:'line', xMin:2026.5, xMax:2026.5, borderColor:'#555', borderWidth:1, borderDash:[4,4],
                label: {{ content:'Proyección →', display:true, color:'#8b949e', font:{{size:10}}, position:'start' }} }},
              risk30: {{ type:'box', xMin:2000, xMax:2031, yMin:0, yMax:30, backgroundColor:'rgba(224,92,92,.05)', borderWidth:0 }},
              risk50: {{ type:'box', xMin:2000, xMax:2031, yMin:30, yMax:50, backgroundColor:'rgba(230,126,34,.04)', borderWidth:0 }},
            }}
          }}
        }},
        scales: {{
          x: {{ type:'linear', min:2000, max:2031, ticks:{{color:'#8b949e',stepSize:2,callback:v=>v}}, grid:{{color:'#21262d'}} }},
          y: {{ min:0, max:100, ticks:{{color:'#8b949e',stepSize:10}}, grid:{{color:'#21262d'}},
                title:{{display:true,text:'ICIV (0–100)',color:'#8b949e',font:{{size:11}}}} }}
        }}
      }}
    }});

    // KPI cards
    const kpiEl = document.getElementById(KPI_IDS[sc]);
    if (kpiEl) {{
      kpiEl.innerHTML = d.años.map((yr,i) => `
        <div style="background:var(--card);border:1px solid var(--border);border-top:3px solid ${{col}};
          border-radius:10px;padding:14px;text-align:center">
          <div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">${{yr}}</div>
          <div style="font-size:1.8rem;font-weight:700;color:${{col}}">${{d.valores[i].toFixed(1)}}</div>
          <div style="font-size:.68rem;color:var(--muted);margin-top:4px">IC: ${{d.ci_lo[i].toFixed(1)}}–${{d.ci_hi[i].toFixed(1)}}</div>
        </div>`).join('');
    }}

    // Supuestos
    const supEl = document.getElementById(SUP_IDS[sc]);
    if (supEl && d.supuestos) {{
      supEl.innerHTML = `<div style="font-size:.78rem;font-weight:600;margin-bottom:10px;color:${{col}}">${{LABELS[sc]}} — Supuestos documentados</div>
        <ul style="font-size:.76rem;color:var(--muted);padding-left:18px;line-height:1.8">${{d.supuestos.map(s=>`<li>${{s}}</li>`).join('')}}</ul>`;
    }}
  }}

  // ── SIMULADOR ────────────────────────────────────────────────────────────────
  const SIM_DIMS  = {sim_dims_json};
  const SIM_YEARS = {sim_years_js};
  const SIM_HIST  = {sim_scores_js};

  let simChart = null;
  let simValues = {{}};  // dim_id → current slider value

  function scoreToCategory(s) {{
    if (s <= 30)  return {{ label:'Alto Riesgo',          color:'#e05c5c' }};
    if (s <= 50)  return {{ label:'Riesgo Moderado-Alto', color:'#e67e22' }};
    if (s <= 65)  return {{ label:'Riesgo Moderado',      color:'#f1c40f' }};
    if (s <= 80)  return {{ label:'Bajo Riesgo',           color:'#2ecc71' }};
    return              {{ label:'Muy Bajo Riesgo',        color:'#00d4aa' }};
  }}

  function computeICIV() {{
    return SIM_DIMS.reduce((acc,d) => acc + (simValues[d.id] || 0) * d.weight, 0);
  }}

  function findAnalog(score) {{
    let best = null, bestDiff = 999;
    SIM_YEARS.forEach((yr,i) => {{
      const diff = Math.abs(SIM_HIST[i] - score);
      if (diff < bestDiff) {{ bestDiff = diff; best = yr; }}
    }});
    return best;
  }}

  function updateSimDisplay() {{
    const iciv  = computeICIV();
    const cat   = scoreToCategory(iciv);
    const analog = findAnalog(iciv);

    const scoreEl = document.getElementById('simScore');
    const catEl   = document.getElementById('simCategory');
    const anaEl   = document.getElementById('simAnalog');
    if (scoreEl) {{ scoreEl.textContent = iciv.toFixed(1); scoreEl.style.color = cat.color; }}
    if (catEl)   {{ catEl.textContent = cat.label; catEl.style.color = cat.color; }}
    if (anaEl)   anaEl.textContent = `Históricamente similar a Venezuela en ${{analog}}`;

    // Contribution bars
    const cbEl = document.getElementById('simContribBars');
    if (cbEl) {{
      cbEl.innerHTML = SIM_DIMS.map(d => {{
        const contrib = (simValues[d.id] || 0) * d.weight;
        const pct     = Math.round((contrib / Math.max(iciv, 0.1)) * 100);
        const shortLabel = d.label.replace('Estabilidad Macroeconómica','Macro')
          .replace('Sector Energético y Petróleo','Energía')
          .replace('Entorno Institucional y Legal','Institucional')
          .replace('Apertura Comercial y Financiera','Comercial')
          .replace('Capital Humano e Infraestructura','Cap. Humano')
          .replace('Percepción Internacional','Percepción');
        return `<div style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;font-size:.7rem;color:var(--muted);margin-bottom:3px">
            <span>${{shortLabel}} (×${{(d.weight*100).toFixed(0)}}%)</span>
            <span>${{contrib.toFixed(1)}} pts</span>
          </div>
          <div style="background:#333;border-radius:3px;height:8px">
            <div style="width:${{pct}}%;height:100%;background:var(--accent);border-radius:3px;transition:width .2s"></div>
          </div>
        </div>`;
      }}).join('');
    }}

    // Update mini chart reference line
    if (simChart) {{
      simChart.data.datasets[1].data = SIM_YEARS.map(y => ({{ x:y, y:iciv }}));
      simChart.update('none');
    }}
  }}

  function buildSliders() {{
    const el = document.getElementById('simSliders');
    if (!el) return;
    el.innerHTML = SIM_DIMS.map(d => `
      <div style="margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
          <span style="font-size:.76rem;color:var(--text)">${{d.label.replace('Estabilidad Macroeconómica','Macro')
            .replace('Sector Energético y Petróleo','Energía')
            .replace('Entorno Institucional y Legal','Institucional')
            .replace('Apertura Comercial y Financiera','Comercial')
            .replace('Capital Humano e Infraestructura','Capital Humano')
            .replace('Percepción Internacional','Percepción')}}</span>
          <span style="font-size:.76rem;color:var(--accent);font-weight:600;min-width:36px;text-align:right"
            id="simVal-${{d.id}}">${{d.current.toFixed(1)}}</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-size:.65rem;color:var(--muted);width:20px">0</span>
          <input type="range" id="simSlider-${{d.id}}" min="0" max="100" step="0.5"
            value="${{d.current}}"
            style="flex:1;accent-color:var(--accent)"
            data-dim="${{d.id}}">
          <span style="font-size:.65rem;color:var(--muted);width:24px">100</span>
        </div>
        <div style="font-size:.65rem;color:var(--muted);margin-top:2px">Peso AHP: ${{(d.weight*100).toFixed(0)}}% · Máx histórico: ${{d.max_hist.toFixed(1)}}</div>
      </div>`).join('');

    // Initialize values + wire events
    SIM_DIMS.forEach(d => {{
      simValues[d.id] = d.current;
      const slider = document.getElementById('simSlider-' + d.id);
      const valEl  = document.getElementById('simVal-'    + d.id);
      if (slider) slider.addEventListener('input', () => {{
        simValues[d.id] = parseFloat(slider.value);
        if (valEl) valEl.textContent = parseFloat(slider.value).toFixed(1);
        updateSimDisplay();
      }});
    }});
  }}

  function buildSimChart() {{
    const ctx = document.getElementById('cSimChart');
    if (!ctx || simChart) return;
    const curICIV = computeICIV();
    simChart = new Chart(ctx, {{
      type: 'line',
      data: {{
        datasets: [
          {{
            label: 'Histórico ICIV',
            data: SIM_YEARS.map((y,i) => ({{ x:y, y:SIM_HIST[i] }})),
            borderColor: '#00d4aa', backgroundColor: 'transparent',
            borderWidth: 2, pointRadius: 2.5, tension: 0.3,
          }},
          {{
            label: 'ICIV Simulado',
            data: SIM_YEARS.map(y => ({{ x:y, y:curICIV }})),
            borderColor: '#f1c40f', borderDash: [6,3],
            backgroundColor: 'rgba(241,196,15,.08)',
            borderWidth: 2, pointRadius: 0, fill: true, tension: 0,
          }},
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false, parsing: false,
        plugins: {{
          legend: {{ labels: {{ color:'#8b949e', boxWidth:20, font:{{size:11}} }} }},
          tooltip: {{ callbacks: {{ label: c => `${{c.dataset.label}}: ${{c.parsed.y?.toFixed(1)}}` }} }},
        }},
        scales: {{
          x: {{ type:'linear', min:2000, max:2026.5, ticks:{{color:'#8b949e',stepSize:2,callback:v=>v}}, grid:{{color:'#21262d'}} }},
          y: {{ min:0, max:100, ticks:{{color:'#8b949e',stepSize:10}}, grid:{{color:'#21262d'}} }}
        }}
      }}
    }});
  }}

  function setPreset(preset) {{
    // preset: 'peak' (2007), 'min' (2020), 'opt2030', 'pess2030'
    SIM_DIMS.forEach(d => {{
      let val;
      if (preset === 'peak') {{
        // Usar max histórico de cada dimensión
        val = d.max_hist;
      }} else if (preset === 'min') {{
        // Usar el año con ICIV más bajo — buscar valores de ese año
        const minIdx = SIM_HIST.indexOf(Math.min(...SIM_HIST));
        val = d.hist[minIdx] !== null ? d.hist[minIdx] : d.current;
      }} else if (preset === 'opt2030') {{
        // Base 2026 + ajuste optimista
        const optDeltas = {{ 0:2.5, 1:5.5, 2:8.0, 3:10.5 }}; // year idx→delta
        const baseLast = SIM_HIST[SIM_HIST.length-1];
        const optVal   = ESC.escenarios.optimista.valores[3]; // 2030
        const ratio    = optVal / Math.max(baseLast, 1);
        val = Math.min(100, d.current * ratio);
      }} else if (preset === 'pess2030') {{
        const baseLast = SIM_HIST[SIM_HIST.length-1];
        const pessVal  = ESC.escenarios.pesimista.valores[3];
        const ratio    = pessVal / Math.max(baseLast, 1);
        val = Math.max(0, d.current * ratio);
      }} else {{
        val = d.current;
      }}
      simValues[d.id] = parseFloat(val.toFixed(1));
      const slider = document.getElementById('simSlider-' + d.id);
      const valEl  = document.getElementById('simVal-'    + d.id);
      if (slider) slider.value = simValues[d.id];
      if (valEl)  valEl.textContent = simValues[d.id].toFixed(1);
    }});
    updateSimDisplay();
  }}

  function initSimulator() {{
    buildSliders();
    buildSimChart();
    updateSimDisplay();
    chartInsts['simulador'] = true;

    // Reset button
    document.getElementById('simReset')?.addEventListener('click', () => setPreset('current'));

    // Preset buttons
    document.querySelectorAll('.sim-preset').forEach(btn => {{
      btn.addEventListener('click', () => setPreset(btn.dataset.preset));
    }});
  }}

  // ── Simulacion probabilistica retirada — en el mismo scope para llamada directa sin bridge ─────────
  var MC = {mc_json};
  var buildMCChart = function() {{}};
  var buildProbCards = function() {{}};
  var buildParamsCard = function() {{}};
  if (MC && MC.percentiles) {{
    var allYears  = {years_js};
    var allScores = {scores_ahp_js};
    var mcYears   = MC.años;
    var pct       = MC.percentiles;

    buildMCChart = function() {{
      var ctx = document.getElementById('cMonteCarlo');
      if (!ctx) return;
      var existing = (typeof Chart !== 'undefined' && Chart.getChart) ? Chart.getChart(ctx) : null;
      if (existing) existing.destroy();
      new Chart(ctx, {{
        type: 'line',
        data: {{
          datasets: [
            {{ label:'P5', data:mcYears.map((y,i)=>({{x:y,y:pct.p5[i]}})),
               borderColor:'transparent', backgroundColor:'rgba(52,152,219,0.10)', fill:'+6', pointRadius:0, tension:0.4 }},
            {{ label:'P10', data:mcYears.map((y,i)=>({{x:y,y:pct.p10[i]}})),
               borderColor:'transparent', backgroundColor:'rgba(52,152,219,0.13)', fill:'+4', pointRadius:0, tension:0.4 }},
            {{ label:'P25', data:mcYears.map((y,i)=>({{x:y,y:pct.p25[i]}})),
               borderColor:'transparent', backgroundColor:'rgba(52,152,219,0.20)', fill:'+2', pointRadius:0, tension:0.4 }},
            {{ label:'Mediana (P50)', data:mcYears.map((y,i)=>({{x:y,y:pct.p50[i]}})),
               borderColor:'#3498db', borderWidth:2.5, backgroundColor:'transparent',
               pointRadius:4, pointBackgroundColor:'#3498db', tension:0.4 }},
            {{ label:'_p75', data:mcYears.map((y,i)=>({{x:y,y:pct.p75[i]}})),
               borderColor:'transparent', backgroundColor:'transparent', fill:false, pointRadius:0, tension:0.4 }},
            {{ label:'_p90', data:mcYears.map((y,i)=>({{x:y,y:pct.p90[i]}})),
               borderColor:'transparent', backgroundColor:'transparent', fill:false, pointRadius:0, tension:0.4 }},
            {{ label:'_p95', data:mcYears.map((y,i)=>({{x:y,y:pct.p95[i]}})),
               borderColor:'transparent', backgroundColor:'transparent', fill:false, pointRadius:0, tension:0.4 }},
            {{ label:'Histórico ICIV', data:allYears.map((y,i)=>({{x:y,y:allScores[i]}})),
               borderColor:'#00d4aa', borderWidth:2.5, backgroundColor:'transparent', pointRadius:2, tension:0.3 }},
          ]
        }},
        options: {{
          responsive:true, maintainAspectRatio:false,
          interaction:{{mode:'index', intersect:false}},
          plugins:{{
            legend:{{display:true, labels:{{filter:(item)=>!item.text.startsWith('_')&&!['P5','P10','P25'].includes(item.text)}}}},
            annotation:{{
              annotations:{{
                lineRec:{{type:'line', yMin:45, yMax:45, borderColor:'#2ecc7155', borderWidth:1, borderDash:[4,3],
                          label:{{content:'Recuperación parcial (45)',display:true,position:'end',color:'#2ecc71',font:{{size:9}}}}}},
                lineRisk:{{type:'line', yMin:25, yMax:25, borderColor:'#e05c5c55', borderWidth:1, borderDash:[4,3],
                           label:{{content:'Alto riesgo (25)',display:true,position:'end',color:'#e05c5c',font:{{size:9}}}}}},
              }}
            }}
          }},
          scales:{{
            x:{{type:'linear', min:2000, max:2031, grid:{{color:'#21262d'}}, ticks:{{stepSize:5}}}},
            y:{{min:0, max:100, grid:{{color:'#21262d'}},
               title:{{display:true, text:'ICIV (0–100)', color:'#8b949e', font:{{size:9}}}}}}
          }}
        }}
      }});
    }};

    buildProbCards = function() {{
      var el = document.getElementById('mcProbCards');
      if (!el) return;
      var cards = [
        {{label:'Probabilidad de Recuperación', sub:'ICIV 2030 > 45 pts', val:(MC.prob_recuperacion*100).toFixed(1)+'%', color:'#2ecc71'}},
        {{label:'Probabilidad Estable', sub:'25 ≤ ICIV 2030 ≤ 45 pts', val:(MC.prob_estable*100).toFixed(1)+'%', color:'#e67e22'}},
        {{label:'Probabilidad Alto Riesgo', sub:'ICIV 2030 < 25 pts', val:(MC.prob_colapso*100).toFixed(1)+'%', color:'#e05c5c'}},
      ];
      el.innerHTML = cards.map(c=>`
        <div style="background:var(--card);border:1px solid ${{c.color}}44;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:.72rem;color:var(--muted);margin-bottom:4px">${{c.label}}</div>
          <div style="font-size:2rem;font-weight:700;color:${{c.color}};line-height:1">${{c.val}}</div>
          <div style="font-size:.68rem;color:var(--muted);margin-top:4px">${{c.sub}}</div>
        </div>`).join('');
    }};

    buildParamsCard = function() {{
      var el = document.getElementById('mcParamsCard');
      if (!el || !MC.parametros) return;
      var etiquetas = {{
        wti_precio_usd:'WTI Precio USD',
        petroleo_crudo_produccion_tbpd:'Producción Petróleo (tbpd)',
        wgi_promedio_sc:'WGI Gobernanza',
      }};
      var rows = Object.entries(MC.parametros).map(([k,p])=>
        `<span style="color:var(--text);font-weight:600">${{etiquetas[k]||k}}:</span> `+
        `µ_anual=${{p.mu_anual?.toFixed(2)}}, σ=${{p.sigma_anual?.toFixed(2)}}, peso_AHP=${{p.peso_ahp?.toFixed(4)}}`
      ).join(' &nbsp;·&nbsp; ');
      el.innerHTML = `<strong style="color:var(--text)">${{MC.n_simulations?.toLocaleString()}} simulaciones.</strong> `+
        `Variables estocásticas: ${{rows}}. ${{MC.metodologia||''}}`;
    }};
  }}

  // The public laboratory starts with the interactive simulator.
  initSimulator();

  // Init on hash
  if (window.location.hash === '#proyecciones') {{
    initSimulator();
  }}
}})();

// ── Correlación y Sanciones — renderizadas server-side (matplotlib / HTML) ──

// ── [INDICADORES LÍDERES y COMPARACIÓN REGIONAL eliminados] ─────────────────

// ── RADAR SECTORIAL — gráficos creados al cargar, resize al activar tab ─────
(function() {{
  var SR = {sector_json};
  if (!SR || !SR.ranking || !SR.ranking.length) return;

  var series = SR.series_historicas;
  var SECTOR_COLORS = [
    '#00d4aa','#3498db','#2ecc71','#e67e22','#e74c3c',
    '#9b59b6','#f1c40f','#1abc9c','#e91e63','#ff5722',
  ];
  var sectorIds    = Object.keys(SR.sector_labels || {{}});
  var yearsArr     = (series && series.a\u00f1os) ? series.a\u00f1os : [];
  var activeSectors = new Set(
    SR.ranking.slice(0,4).map(function(r) {{ return r.sector_id; }})
  );

  // ── Global: click en filas HTML o toggle buttons ───────────────────────
  window.sectorShowHist = function(sid) {{
    if (activeSectors.has(sid)) {{ activeSectors.delete(sid); }}
    else {{ activeSectors.add(sid); }}
    // Actualizar estilos de botones
    document.querySelectorAll('#sectorToggleBtns button').forEach(function(btn) {{
      var i = parseInt(btn.dataset.idx);
      var c = SECTOR_COLORS[i % SECTOR_COLORS.length];
      if (activeSectors.has(btn.dataset.sid)) {{
        btn.style.background = c+'33'; btn.style.color = c; btn.style.borderColor = c;
      }} else {{
        btn.style.background = 'transparent'; btn.style.color = '#8b949e'; btn.style.borderColor = '#444';
      }}
    }});
    // Actualizar datasets del chart histórico sin rebuilding
    if (histChart) {{
      histChart.data.datasets.forEach(function(ds, i) {{
        var dsid = sectorIds[i];
        ds.hidden = !activeSectors.has(dsid);
        ds.borderWidth = activeSectors.has(dsid) ? 2 : 0;
      }});
      histChart.update('none');
    }}
  }};

  // ── Bar chart — creado en page load ───────────────────────────────────────
  var barChart = null;
  var ctxBar = document.getElementById('cSectorBar');
  if (ctxBar) {{
    barChart = new Chart(ctxBar, {{
      type: 'bar',
      data: {{
        labels: SR.ranking.map(function(r) {{ return r.label_corto; }}),
        datasets: [{{
          label: 'Score Sectorial',
          data: SR.ranking.map(function(r) {{ return r.score; }}),
          backgroundColor: SR.ranking.map(function(r) {{ return r.hex+'99'; }}),
          borderColor: SR.ranking.map(function(r) {{ return r.hex; }}),
          borderWidth: 1.5, borderRadius: 4,
        }}]
      }},
      options: {{
        indexAxis: 'y',
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{display:false}} }},
        scales: {{
          x: {{min:0, max:100, grid:{{color:'#21262d'}}, ticks:{{color:'#8b949e'}}}},
          y: {{grid:{{display:false}}, ticks:{{color:'#c9d1d9', font:{{size:11}}}}}},
        }}
      }}
    }});
  }}

  // ── Histórico — creado en page load ───────────────────────────────────────
  var histChart = null;
  var ctxH = document.getElementById('cSectorHist');
  if (ctxH) {{
    histChart = new Chart(ctxH, {{
      type: 'line',
      data: {{
        datasets: sectorIds.map(function(sid, i) {{
          var isActive = activeSectors.has(sid);
          return {{
            label: SR.sector_labels[sid] || sid,
            data: yearsArr.map(function(y, j) {{
              return {{x: y, y: (series.sectores[sid] || [])[j]}};
            }}),
            borderColor: SECTOR_COLORS[i % SECTOR_COLORS.length],
            backgroundColor: 'transparent',
            borderWidth: isActive ? 2 : 0,
            pointRadius: 0, tension: 0.3, hidden: !isActive,
          }};
        }})
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{mode:'index', intersect:false}},
        plugins: {{ legend: {{display:false}} }},
        scales: {{
          x: {{type:'linear', grid:{{color:'#21262d'}}, ticks:{{stepSize:5, color:'#8b949e'}}}},
          y: {{min:0, max:100, grid:{{color:'#21262d'}},
               title:{{display:true, text:'Score sectorial', color:'#8b949e', font:{{size:9}}}}}},
        }}
      }}
    }});
  }}

  // ── Tab activation: solo resize (charts ya existen) ───────────────────────
  if (typeof _tabInits !== 'undefined') {{
    _tabInits['sectorial'] = function() {{
      if (barChart) barChart.resize();
      if (histChart) histChart.resize();
    }};
  }}
}})();
// ── [INDICADORES LÍDERES y COMPARACIÓN REGIONAL eliminados] ─────────────────

// ── ICIV PULSE MENSUAL ──────────────────────────────────────────────────────
(function() {{
  var PULSE = {pulse_json};
  var PCOMP = {pulse_components_json};
  var MIRROR = {mirror_trade_json};
  var BLACKMARBLE = {blackmarble_json};
  var BMMAP = {blackmarble_map_json};
  if (!PULSE || !PULSE.data || !PULSE.data.scores || !PULSE.data.scores.length) return;

  var D = PULSE.data;
  var S = PULSE.summary;

  // Pesos AHP renormalizados Pulse (para tabla) — sincronizado con
  // iciv.index.pulse_aggregator.PULSE_WEIGHTS
  var PULSE_WEIGHTS = {{
    "wti_precio_usd": 0.065, "brent_precio_usd": 0.04,
    "crudo_dubai_usd": 0.04,
    "tasa_fed_funds_pct": 0.04, "usd_index_broad": 0.035,
    "vix_volatility": 0.06, "ust_10y_yield_pct": 0.03,
    "em_bond_spread_pct": 0.04,
    "petroleo_crudo_produccion_tbpd": 0.25,
    "importaciones_espejo_usa_musd": 0.05,
    "exportaciones_espejo_usa_musd": 0.05,
    "guardian_articulos_venezuela": 0.065,
    "guardian_tono_titulares": 0.10,
    "gdelt_cobertura_vol": 0.055,
    "gdelt_tono_noticias": 0.08,
  }};
  var PULSE_LABELS = {{
    "wti_precio_usd": "WTI Oil Price",
    "brent_precio_usd": "Brent Oil Price",
    "crudo_dubai_usd": "Crudo Dubai (Pink Sheet)",
    "tasa_fed_funds_pct": "Fed Funds Rate",
    "usd_index_broad": "USD Index (Broad)",
    "vix_volatility": "VIX Volatility",
    "ust_10y_yield_pct": "UST 10Y Yield",
    "em_bond_spread_pct": "Spread Bonos EM (ICE BofA)",
    "petroleo_crudo_produccion_tbpd": "Producción Petróleo VEN",
    "importaciones_espejo_usa_musd": "Import. espejo desde EEUU",
    "exportaciones_espejo_usa_musd": "Export. espejo a EEUU",
    "guardian_articulos_venezuela": "Vol. Artículos Guardian",
    "guardian_tono_titulares": "Tono VADER Guardian",
    "gdelt_cobertura_vol": "Cobertura GDELT",
    "gdelt_tono_noticias": "Tono GDELT",
  }};

  // Llenar stats
  if (S) {{
    var elScore = document.getElementById('pulseScoreActual');
    var elCat   = document.getElementById('pulseCategoria');
    var elFecha = document.getElementById('pulseFechaActual');
    var elCov   = document.getElementById('pulseCobertura');
    var elN     = document.getElementById('pulseNMeses');
    var elVA    = document.getElementById('pulseVsAnual');
    if (elScore) {{ elScore.textContent = S.score_actual != null ? S.score_actual.toFixed(1) : '—'; elScore.style.color = S.color; }}
    if (elCat)   {{ elCat.textContent = S.score_confiable != null ? S.score_confiable.toFixed(1) + ' · ' + S.categoria_confiable : '—'; elCat.style.color = S.color_confiable || '#8b949e'; }}
    if (elFecha) elFecha.textContent = S.fecha_actual + ' · cobertura directa ' + S.cobertura + '%' + (S.es_confiable ? '' : ' · provisional');
    if (elCov)   elCov.textContent = S.fecha_confiable + ' · cobertura ' + S.cobertura_confiable + '%';
    if (elN)     elN.textContent = S.n_meses;

    // Diferencia vs ICIV Anual del año actual
    if (elVA) {{
      var iciv_actual = {current_score};
      var refScore = S.score_confiable != null ? S.score_confiable : S.score_actual;
      if (refScore != null) {{
        var diff = refScore - iciv_actual;
        elVA.textContent = (diff >= 0 ? '+' : '') + diff.toFixed(1);
        elVA.className = 'stat-val ' + (diff >= 0 ? 'stat-up' : 'stat-down');
      }}
    }}
  }}

  // Tabla de pesos
  var wtBox = document.getElementById('pulseWeightsTable');
  if (wtBox) {{
    var rows = Object.keys(PULSE_WEIGHTS).map(function(k) {{
      return '<tr><td>' + (PULSE_LABELS[k] || k) + '</td>' +
             '<td style="text-align:right;color:var(--accent);font-weight:600">' +
             (PULSE_WEIGHTS[k] * 100).toFixed(0) + '%</td></tr>';
    }}).join('');
    wtBox.innerHTML = '<table class="ahp-table" style="width:100%;max-width:500px">' +
      '<thead><tr><th>Componente</th><th style="text-align:right">Peso renormalizado</th></tr></thead>' +
      '<tbody>' + rows + '</tbody></table>';
  }}

  // Construir gráfico Pulse mensual
  function buildPulseChart() {{
    var ctx = document.getElementById('cPulseMonthly');
    if (!ctx) return;
    if (typeof Chart !== 'undefined' && Chart.getChart && Chart.getChart(ctx)) return;

    var data_low_cov = D.scores.map(function(s, i) {{
      return D.cobertura[i] < 70 ? s : null;
    }});

    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: D.meses,
        datasets: [
          {{
            label: 'Pulse mensual (cob ≥70%)',
            data: D.scores.map(function(s, i) {{ return D.cobertura[i] >= 70 ? s : null; }}),
            borderColor: '#00d4aa', backgroundColor: 'rgba(0,212,170,.1)',
            borderWidth: 2.5, pointRadius: 2, tension: 0.25, fill: false,
          }},
          {{
            label: 'Pulse mensual (cob <70%, provisional)',
            data: data_low_cov,
            borderColor: '#8b949e', backgroundColor: 'transparent',
            borderWidth: 1.5, borderDash: [4, 3], pointRadius: 2,
          }},
          {{
            label: 'ICIV Anual {current_year_val} (referencia)',
            data: D.meses.map(function() {{ return {current_score}; }}),
            borderColor: '#f1c40f', backgroundColor: 'transparent',
            borderWidth: 1.5, borderDash: [8, 4], pointRadius: 0, fill: false,
          }},
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'top', labels: {{ color: '#8b949e', font: {{size: 10}} }} }},
          tooltip: {{ callbacks: {{
            afterLabel: function(c) {{
              if (c.datasetIndex < 2) return 'Cobertura: ' + D.cobertura[c.dataIndex] + '%';
            }}
          }} }},
        }},
        scales: {{
          x: {{ ticks: {{ color:'#8b949e', maxTicksLimit:14 }}, grid: {{color:'#21262d'}} }},
          y: {{ min:0, max:100, ticks: {{color:'#8b949e', stepSize:20}}, grid: {{color:'#21262d'}} }},
        }}
      }}
    }});
  }}

  // Construir gráfico Pulse Anual vs Oficial
  function buildPulseVsAnnual() {{
    var ctx = document.getElementById('cPulseVsAnnual');
    if (!ctx) return;
    if (typeof Chart !== 'undefined' && Chart.getChart && Chart.getChart(ctx)) return;

    // Pulse anualizado: promedio por año
    var byYear = {{}};
    D.meses.forEach(function(m, i) {{
      var y = m.split('-')[0];
      if (!byYear[y]) byYear[y] = [];
      if (D.scores[i] != null && D.cobertura[i] >= 70) byYear[y].push(D.scores[i]);
    }});
    var years_pulse = Object.keys(byYear).sort();
    var pulse_avg = years_pulse.map(function(y) {{
      var vs = byYear[y];
      return vs.length ? vs.reduce(function(a,b) {{return a+b;}}, 0) / vs.length : null;
    }});

    // ICIV oficial — pull from window globals if available
    var iciv_years = {years_js};
    var iciv_scores = {scores_ahp_js};
    var oficial_aligned = years_pulse.map(function(y) {{
      var idx = iciv_years.indexOf(parseInt(y));
      return idx >= 0 ? iciv_scores[idx] : null;
    }});

    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: years_pulse,
        datasets: [
          {{
            label: 'Pulse anualizado (promedio mensual)',
            data: pulse_avg,
            borderColor: '#00d4aa', backgroundColor: 'rgba(0,212,170,.1)',
            borderWidth: 2.5, pointRadius: 4, tension: 0.25,
          }},
          {{
            label: 'ICIV Anual oficial',
            data: oficial_aligned,
            borderColor: '#f1c40f', backgroundColor: 'rgba(241,196,15,.1)',
            borderWidth: 2.5, pointRadius: 4, tension: 0.25,
          }},
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'top', labels: {{color:'#8b949e'}} }} }},
        scales: {{
          x: {{ ticks: {{color:'#8b949e'}}, grid: {{color:'#21262d'}} }},
          y: {{ min:0, max:100, ticks: {{color:'#8b949e'}}, grid: {{color:'#21262d'}} }},
        }}
      }}
    }});
  }}

  // Componentes — multi-line chart
  function buildPulseComponents() {{
    var ctx = document.getElementById('cPulseComponents');
    if (!ctx) return;
    if (typeof Chart !== 'undefined' && Chart.getChart && Chart.getChart(ctx)) return;
    if (!PCOMP.meses || !PCOMP.meses.length) return;

    var COLORS = ['#00d4aa','#f1c40f','#e67e22','#3498db','#9b59b6','#2ecc71',
                  '#e74c3c','#1abc9c','#e91e63','#ff5722','#34495e'];
    var datasets = [];
    var i = 0;
    Object.keys(PULSE_WEIGHTS).forEach(function(k) {{
      var series = PCOMP.componentes[k];
      if (!series) return;
      datasets.push({{
        label: PULSE_LABELS[k] || k,
        data: series,
        borderColor: COLORS[i % COLORS.length],
        backgroundColor: 'transparent',
        borderWidth: 1.8, pointRadius: 1, tension: 0.2, hidden: i >= 5,
      }});
      i++;
    }});

    new Chart(ctx, {{
      type: 'line',
      data: {{ labels: PCOMP.meses, datasets: datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'right', labels: {{color:'#8b949e', font:{{size:10}}, boxWidth:14}} }} }},
        scales: {{
          x: {{ ticks: {{color:'#8b949e', maxTicksLimit:14}}, grid: {{color:'#21262d'}} }},
          y: {{ min:0, max:100, ticks: {{color:'#8b949e'}}, grid: {{color:'#21262d'}} }},
        }}
      }}
    }});
  }}

  // Comercio espejo multi-socio — dos charts (importaciones / exportaciones)
  function buildMirrorTrade() {{
    if (!MIRROR || !MIRROR.meses || !MIRROR.meses.length) return;
    var configs = [
      {{ id: 'cMirrorImports', usa: MIRROR.imts_imp, socios: MIRROR.ct_imp }},
      {{ id: 'cMirrorExports', usa: MIRROR.imts_exp, socios: MIRROR.ct_exp }},
    ];
    configs.forEach(function(cfg) {{
      var ctx = document.getElementById(cfg.id);
      if (!ctx) return;
      if (typeof Chart !== 'undefined' && Chart.getChart && Chart.getChart(ctx)) return;
      new Chart(ctx, {{
        type: 'line',
        data: {{
          labels: MIRROR.meses,
          datasets: [
            {{
              label: 'EEUU (IMF IMTS)',
              data: cfg.usa,
              borderColor: '#3498db', backgroundColor: 'transparent',
              borderWidth: 1.8, pointRadius: 0, tension: 0.2, spanGaps: false,
            }},
            {{
              label: '5 socios: ESP+BRA+IND+TUR+CHN (Comtrade)',
              data: cfg.socios,
              borderColor: '#00d4aa', backgroundColor: 'transparent',
              borderWidth: 1.8, pointRadius: 0, tension: 0.2, spanGaps: false,
            }},
          ]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          interaction: {{ mode: 'index', intersect: false }},
          plugins: {{ legend: {{ position: 'top', labels: {{color:'#8b949e'}} }} }},
          scales: {{
            x: {{ ticks: {{color:'#8b949e', maxTicksLimit:14}}, grid: {{color:'#21262d'}} }},
            y: {{ beginAtZero: true, ticks: {{color:'#8b949e'}}, grid: {{color:'#21262d'}},
                 title: {{display:true, text:'millones USD/mes', color:'#8b949e', font:{{size:10}}}} }},
          }}
        }}
      }});
    }});
  }}

  // Black Marble — luminosidad nocturna mensual + overlay anual Li et al.
  function buildBlackMarble() {{
    if (!BLACKMARBLE || !BLACKMARBLE.meses || !BLACKMARBLE.meses.length) return;
    var ctx = document.getElementById('cBlackMarble');
    if (!ctx) return;
    if (typeof Chart !== 'undefined' && Chart.getChart && Chart.getChart(ctx)) return;
    // El overlay anual se alinea por etiqueta de mes (YYYY-06) sobre el eje mensual
    var anualMap = {{}};
    (BLACKMARBLE.anual_meses || []).forEach(function(m, i) {{ anualMap[m] = BLACKMARBLE.anual_li[i]; }});
    var anualData = BLACKMARBLE.meses.map(function(m) {{ return (m in anualMap) ? anualMap[m] : null; }});
    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: BLACKMARBLE.meses,
        datasets: [
          {{
            label: 'Media mensual (VNP46A3)',
            data: BLACKMARBLE.mensual,
            borderColor: '#3498db', backgroundColor: 'transparent',
            borderWidth: 1.8, pointRadius: 0, tension: 0.25,
          }},
          {{
            label: 'Log-media mensual (atenúa flaring petrolero)',
            data: BLACKMARBLE.robusta && BLACKMARBLE.robusta.length ? BLACKMARBLE.robusta : null,
            borderColor: '#00d4aa', backgroundColor: 'transparent',
            borderWidth: 1.8, pointRadius: 0, tension: 0.25, hidden: false,
          }},
          {{
            label: 'Li et al. anual (VIIRS armonizado, reescalado)',
            data: anualData,
            borderColor: '#f1c40f', backgroundColor: 'transparent',
            borderWidth: 1.6, borderDash: [6,4], pointRadius: 3, spanGaps: true,
          }},
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{ legend: {{ position: 'top', labels: {{color:'#8b949e'}} }} }},
        scales: {{
          x: {{ ticks: {{color:'#8b949e', maxTicksLimit:14}}, grid: {{color:'#21262d'}} }},
          y: {{ ticks: {{color:'#8b949e'}}, grid: {{color:'#21262d'}},
               title: {{display:true, text:'nW/cm²/sr', color:'#8b949e', font:{{size:10}}}} }},
        }}
      }}
    }});
  }}

  // Mapa coroplético subnacional Black Marble — SVG + slider de año + animación
  function _bmColor(v, vmax) {{
    // escala secuencial tipo "luces nocturnas": negro-azulado → ámbar → blanco
    var t = Math.max(0, Math.min(1, Math.sqrt((v || 0) / (vmax || 1))));
    var stops = [[13,17,23],[40,30,60],[140,60,40],[230,150,30],[255,240,190]];
    var seg = t * (stops.length - 1);
    var i = Math.floor(seg), f = seg - i;
    if (i >= stops.length - 1) return 'rgb(' + stops[stops.length-1].join(',') + ')';
    var a = stops[i], b = stops[i+1];
    return 'rgb(' + a.map(function(c,k){{return Math.round(c+(b[k]-c)*f)}}).join(',') + ')';
  }}
  var _bmMapBuilt = false;
  function buildBlackMarbleMap() {{
    if (_bmMapBuilt || !BMMAP || !BMMAP.estados || !BMMAP.estados.length || !BMMAP.years.length) return;
    var svg = document.getElementById('bmMapSvg');
    if (!svg) return;
    _bmMapBuilt = true;
    svg.setAttribute('viewBox', '0 0 ' + BMMAP.viewbox[0] + ' ' + BMMAP.viewbox[1]);
    var NS = 'http://www.w3.org/2000/svg';
    var paths = {{}};
    BMMAP.estados.forEach(function(e) {{
      var p = document.createElementNS(NS, 'path');
      p.setAttribute('d', e.d);
      p.setAttribute('stroke', '#0d1117');
      p.setAttribute('stroke-width', '0.8');
      p.style.cursor = 'pointer';
      p.addEventListener('mousemove', function() {{
        var y = BMMAP.years[+document.getElementById('bmMapSlider').value];
        var v = (BMMAP.radiance[y] || {{}})[e.cod];
        document.getElementById('bmMapTip').textContent =
          e.nombre + ' · ' + (v != null ? v.toFixed(3) + ' nW/cm²/sr' : 'sin dato') + ' (' + y + ')';
      }});
      svg.appendChild(p);
      paths[e.cod] = p;
    }});
    // gradiente de leyenda
    var grad = document.getElementById('bmMapGradient');
    if (grad) {{
      var css = [];
      for (var s = 0; s <= 10; s++) css.push(_bmColor(BMMAP.vmax * (s/10)*(s/10), BMMAP.vmax));
      grad.style.background = 'linear-gradient(90deg,' + css.join(',') + ')';
    }}

    function render(idx) {{
      var y = BMMAP.years[idx];
      var rad = BMMAP.radiance[y] || {{}};
      BMMAP.estados.forEach(function(e) {{
        paths[e.cod].setAttribute('fill', _bmColor(rad[e.cod], BMMAP.vmax));
      }});
      document.getElementById('bmMapYear').textContent = y;
      document.getElementById('bmRankYear').textContent = y;
      var ranked = BMMAP.estados.map(function(e){{return {{n:e.nombre, v:rad[e.cod]}}}})
                    .filter(function(x){{return x.v!=null}}).sort(function(a,b){{return b.v-a.v}}).slice(0,8);
      document.getElementById('bmMapRanking').innerHTML = ranked.map(function(x){{
        var w = Math.max(3, Math.min(100, Math.sqrt(x.v/BMMAP.vmax)*100));
        return '<div style="display:flex;align-items:center;gap:6px;margin:2px 0">' +
          '<span style="width:96px;color:#c9d1d9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+x.n+'</span>' +
          '<span style="flex:1;background:#161b22;border-radius:3px"><span style="display:block;height:9px;border-radius:3px;width:'+w+'%;background:'+_bmColor(x.v,BMMAP.vmax)+'"></span></span>' +
          '<span style="width:38px;text-align:right;color:#8b949e">'+x.v.toFixed(2)+'</span></div>';
      }}).join('');
    }}

    var slider = document.getElementById('bmMapSlider');
    slider.max = BMMAP.years.length - 1;
    slider.value = BMMAP.years.length - 1;
    slider.addEventListener('input', function() {{ render(+slider.value); }});
    render(BMMAP.years.length - 1);

    var playBtn = document.getElementById('bmMapPlay');
    var timer = null;
    playBtn.addEventListener('click', function() {{
      if (timer) {{ clearInterval(timer); timer = null; playBtn.textContent = '▶ Animar'; return; }}
      playBtn.textContent = '⏸ Pausar';
      var i = 0;
      timer = setInterval(function() {{
        slider.value = i; render(i); i++;
        if (i >= BMMAP.years.length) {{ clearInterval(timer); timer = null; playBtn.textContent = '▶ Animar'; }}
      }}, 700);
    }});
  }}

  // El mapa Black Marble vive en la pestaña "Actividad por Estado" (#mapa);
  // se expone para que ese tab lo construya al activarse.
  window.__buildBMMap = buildBlackMarbleMap;

  // Render on tab activation (lazy)
  if (typeof _tabInits !== 'undefined') {{
    _tabInits['pulse'] = function() {{
      buildPulseChart();
      buildPulseVsAnnual();
    }};
    _tabInits['pulse-componentes'] = function() {{
      buildPulseComponents();
      buildMirrorTrade();
      buildBlackMarble();
    }};
  }}

  // Also try to build immediately if already on this tab
  if (window.location.hash === '#pulse') {{
    buildPulseChart();
    buildPulseVsAnnual();
  }}
  if (window.location.hash === '#pulse-componentes') {{
    buildPulseComponents();
    buildMirrorTrade();
    buildBlackMarble();
    buildBlackMarbleMap();
  }}
}})();

// ── ML FORECAST (SARIMA + Nowcast) ──────────────────────────────────────────
(function() {{
  var ML = {ml_forecast_json};
  var PULSE = {pulse_json};
  if (!ML || (!ML.sarima && !ML.nowcast)) return;

  // SARIMA stats
  if (ML.sarima && ML.sarima.order) {{
    var elO = document.getElementById('mlSarimaOrder');
    var elA = document.getElementById('mlSarimaAic');
    if (elO) elO.textContent = ML.sarima.order;
    if (elA) elA.textContent = 'AIC: ' + (ML.sarima.aic != null ? ML.sarima.aic.toFixed(2) : '—');
  }}

  if (ML.backtest && ML.backtest.available) {{
    var bt = ML.backtest;
    var best1 = (bt.best_by_horizon || []).find(function(r) {{ return r.horizon === 1; }}) || (bt.best_by_horizon || [])[0];
    var elBt = document.getElementById('mlBacktestBest');
    var elBtSub = document.getElementById('mlBacktestSub');
    if (elBt && best1) elBt.textContent = best1.model + ' · MAE ' + Number(best1.mae).toFixed(2);
    if (elBtSub) elBtSub.textContent = bt.n_origins + ' orígenes · ' + bt.n_predictions + ' predicciones';
    var elBtSummary = document.getElementById('mlBacktestSummary');
    if (elBtSummary) {{
      elBtSummary.innerHTML = 'Evaluación fuera de muestra con rolling-origin, usando meses con cobertura ≥ '
        + bt.config.min_coverage_pct + '%. Si SARIMA no es el mejor en MAE, el dashboard lo conserva como baseline técnico y muestra el ganador.';
    }}
    var elBtTable = document.getElementById('mlBacktestTable');
    if (elBtTable) {{
      var rows = (bt.best_by_horizon || []).map(function(r) {{
        return '<tr><td>' + r.horizon + 'm</td><td>' + r.model + '</td><td style="text-align:right">' +
          Number(r.mae).toFixed(2) + '</td><td style="text-align:right">' + Number(r.rmse).toFixed(2) + '</td></tr>';
      }}).join('');
      elBtTable.innerHTML = '<table class="ahp-table" style="width:100%;max-width:620px">' +
        '<thead><tr><th>Horizonte</th><th>Mejor modelo</th><th style="text-align:right">MAE</th><th style="text-align:right">RMSE</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table>';
    }}
  }} else if (ML.backtest) {{
    var elBtNote = document.getElementById('mlBacktestSummary');
    if (elBtNote) elBtNote.textContent = 'Backtesting no disponible: ' + (ML.backtest.reason || 'muestra insuficiente');
  }}

  // Nowcast stats
  if (ML.nowcast && ML.nowcast.r2_train != null) {{
    var elR2 = document.getElementById('mlR2Train');
    var elR2cv = document.getElementById('mlR2LooCv');
    var elMae = document.getElementById('mlMae');
    if (elR2) elR2.textContent = ML.nowcast.r2_train.toFixed(3);
    if (elR2cv) {{
      var v = ML.nowcast.r2_loo_cv;
      elR2cv.textContent = v != null ? v.toFixed(3) : '—';
      elR2cv.className = 'stat-val ' + (v != null && v >= 0.5 ? 'stat-up' : (v != null && v >= 0 ? 'stat-neu' : 'stat-down'));
    }}
    if (elMae) elMae.textContent = ML.nowcast.mae_train != null ? ML.nowcast.mae_train.toFixed(2) : '—';
  }}

  // Nowcast prediction
  if (ML.nowcast && ML.nowcast.prediccion_actual) {{
    var P = ML.nowcast.prediccion_actual;
    var elYr = document.getElementById('mlNowcastYear');
    var elVal = document.getElementById('mlNowcastValue');
    var elNote = document.getElementById('mlNowcastNote');
    if (elYr) elYr.textContent = P.año || '—';
    if (P.iciv_predicho != null) {{
      if (elVal) elVal.textContent = P.iciv_predicho.toFixed(2);
      if (elNote) elNote.textContent = '(usando ' + P.n_meses_usados + ' meses Pulse · ' + P.modelo + ')';
    }} else {{
      // Cuando hay pocos meses disponibles (< 3 con cobertura ≥70%)
      if (elVal) {{ elVal.textContent = 'Sin predicción'; elVal.style.fontSize = '.9rem'; elVal.style.color = '#8b949e'; }}
      if (elNote) elNote.textContent = P.nota || 'Datos insuficientes para nowcast este año';
    }}
  }}

  // Coeficientes table
  if (ML.nowcast && ML.nowcast.coefficients) {{
    var coefBox = document.getElementById('mlCoeffsTable');
    if (coefBox) {{
      var rows = Object.keys(ML.nowcast.coefficients).map(function(k) {{
        var v = ML.nowcast.coefficients[k];
        var color = v >= 0 ? '#2ecc71' : '#e74c3c';
        return '<tr><td>' + k + '</td><td style="text-align:right;color:' + color + ';font-weight:600">' + v.toFixed(4) + '</td></tr>';
      }}).join('');
      rows += '<tr><td><strong>Intercept</strong></td><td style="text-align:right">' +
              (ML.nowcast.intercept || 0).toFixed(2) + '</td></tr>';
      coefBox.innerHTML = '<table class="ahp-table" style="width:100%;max-width:500px">' +
        '<thead><tr><th>Feature</th><th style="text-align:right">Coeficiente</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table>';
    }}
  }}

  // Forecast chart
  function buildForecastChart() {{
    var ctx = document.getElementById('cMlForecast');
    if (!ctx) return;
    if (typeof Chart !== 'undefined' && Chart.getChart && Chart.getChart(ctx)) return;
    if (!ML.sarima || !ML.sarima.fecha || !ML.sarima.fecha.length) return;

    // Datos históricos del Pulse — SOLO últimos 30 meses para que el forecast sea visible
    var N_HIST = 30;  // ventana visible: ~2.5 años histórico + 6 meses forecast = 36 puntos
    var all_hist_dates  = PULSE.data.meses;
    var all_hist_scores = PULSE.data.scores;
    var all_hist_cov    = PULSE.data.cobertura;
    // Recortar al ventana
    var start_i = Math.max(0, all_hist_dates.length - N_HIST);
    var hist_dates  = all_hist_dates.slice(start_i);
    var hist_scores = all_hist_scores.slice(start_i);
    var hist_cov    = all_hist_cov.slice(start_i);
    var hist_clean  = hist_scores.map(function(s, i) {{
      return hist_cov[i] >= 70 ? s : null;
    }});

    // Forecast dates + bandas
    var fc_dates = ML.sarima.fecha;
    var fc_mean = ML.sarima.mean;

    // Combinar: histórico (ventana) + forecast
    var all_dates = hist_dates.concat(fc_dates);

    // Construir series: histórico con nulls en zona forecast
    var hist_series = hist_clean.concat(fc_dates.map(function() {{ return null; }}));
    // Forecast con nulls en zona histórica
    var fc_series = hist_dates.map(function() {{ return null; }}).concat(fc_mean);
    // Bandas con nulls en zona histórica
    var lo80 = hist_dates.map(function() {{ return null; }}).concat(ML.sarima.lo_80);
    var hi80 = hist_dates.map(function() {{ return null; }}).concat(ML.sarima.hi_80);
    var lo95 = hist_dates.map(function() {{ return null; }}).concat(ML.sarima.lo_95);
    var hi95 = hist_dates.map(function() {{ return null; }}).concat(ML.sarima.hi_95);

    // Mostrar meses de baja cobertura como serie discontinua (dashed, alpha bajo)
    var hist_low_cov = hist_scores.map(function(s, i) {{
      return hist_cov[i] < 70 ? s : null;
    }});
    // Asegurar que la transición baja-alta cobertura esté conectada visualmente
    for (var j = 1; j < hist_scores.length; j++) {{
      if (hist_low_cov[j] != null && hist_clean[j-1] != null) {{
        hist_low_cov[j-1] = hist_clean[j-1];
      }}
    }}

    // Pinning point: ÚLTIMO valor no-nulo del histórico
    var last_pin_idx = -1, last_pin_val = null;
    for (var k = hist_scores.length - 1; k >= 0; k--) {{
      if (hist_scores[k] != null) {{ last_pin_idx = k; last_pin_val = hist_scores[k]; break; }}
    }}
    if (last_pin_idx >= 0) {{
      fc_series[last_pin_idx] = last_pin_val;
      lo80[last_pin_idx] = last_pin_val;
      hi80[last_pin_idx] = last_pin_val;
      lo95[last_pin_idx] = last_pin_val;
      hi95[last_pin_idx] = last_pin_val;
    }}

    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: all_dates,
        datasets: [
          {{
            label: 'Banda 95% confianza',
            data: hi95,
            borderColor: 'rgba(0,212,170,0)',
            backgroundColor: 'rgba(0,212,170,.08)',
            fill: '+1', pointRadius: 0, borderWidth: 0, tension: 0.2,
          }},
          {{
            label: '__lo95',
            data: lo95,
            borderColor: 'rgba(0,212,170,0)',
            backgroundColor: 'rgba(0,212,170,.08)',
            fill: false, pointRadius: 0, borderWidth: 0, tension: 0.2,
          }},
          {{
            label: 'Banda 80% confianza',
            data: hi80,
            borderColor: 'rgba(0,212,170,0)',
            backgroundColor: 'rgba(0,212,170,.18)',
            fill: '+1', pointRadius: 0, borderWidth: 0, tension: 0.2,
          }},
          {{
            label: '__lo80',
            data: lo80,
            borderColor: 'rgba(0,212,170,0)',
            backgroundColor: 'rgba(0,212,170,.18)',
            fill: false, pointRadius: 0, borderWidth: 0, tension: 0.2,
          }},
          {{
            label: 'Pulse histórico',
            data: hist_series,
            borderColor: '#00d4aa', backgroundColor: 'transparent',
            borderWidth: 2.5, pointRadius: 1.5, tension: 0.25, fill: false,
          }},
          {{
            label: 'Pulse (baja cobertura)',
            data: hist_low_cov.concat(fc_dates.map(function() {{ return null; }})),
            borderColor: 'rgba(0,212,170,0.4)', backgroundColor: 'transparent',
            borderWidth: 1.5, pointRadius: 2, tension: 0.25, fill: false,
            borderDash: [4, 3],
          }},
          {{
            label: 'Forecast SARIMA (mean)',
            data: fc_series,
            borderColor: '#f1c40f', backgroundColor: 'transparent',
            borderWidth: 2.5, borderDash: [6, 3], pointRadius: 3, tension: 0.25, fill: false,
          }},
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{
            position: 'top',
            labels: {{
              color: '#8b949e', font: {{size: 10}},
              filter: function(item) {{ return !item.text.startsWith('__'); }}
            }}
          }},
        }},
        scales: {{
          x: {{ ticks: {{color:'#8b949e', maxTicksLimit:16}}, grid: {{color:'#21262d'}} }},
          y: {{ min:0, max:100, ticks: {{color:'#8b949e', stepSize:20}}, grid: {{color:'#21262d'}} }},
        }}
      }}
    }});
  }}

  if (typeof _tabInits !== 'undefined') {{
    _tabInits['forecast-ml'] = buildForecastChart;
  }}
  if (window.location.hash === '#forecast-ml') {{
    buildForecastChart();
  }}
}})();

(function() {{
  var ML = {ml_forecast_json};
  if (!ML || !ML.nowcast) return;
  function fillNowcastTab() {{
    // Stats cards
    var nc = ML.nowcast;
    var p  = nc.prediccion_actual || {{}};
    var el;
    el = document.getElementById('nc2NowcastValue');
    if (el) {{
      if (p.iciv_predicho != null) {{ el.textContent = p.iciv_predicho.toFixed(2); }}
      else {{ el.textContent = 'Sin predicción'; el.style.fontSize = '.85rem'; el.style.color = '#8b949e'; }}
    }}
    el = document.getElementById('nc2NowcastYear');
    if (el) el.textContent = p.año ? 'Estimado ' + p.año : '—';
    el = document.getElementById('nc2NMeses');
    if (el) el.textContent = p.n_meses_usados != null ? p.n_meses_usados : (p.nota || '—');
    el = document.getElementById('nc2R2Loo');
    if (el) {{
      var v = nc.r2_loo_cv;
      el.textContent = v != null ? v.toFixed(3) : '—';
      el.className = 'stat-val ' + (v != null && v >= 0.5 ? 'stat-up' : (v != null && v >= 0 ? 'stat-neu' : 'stat-down'));
    }}
    el = document.getElementById('nc2Mae');
    if (el) el.textContent = nc.mae_train != null ? nc.mae_train.toFixed(2) : '—';
    // Coeficientes
    var coefBox = document.getElementById('nc2CoeffsTable');
    if (coefBox && nc.coefficients) {{
      var rows = Object.keys(nc.coefficients).map(function(k) {{
        var v = nc.coefficients[k];
        var color = v >= 0 ? '#2ecc71' : '#e74c3c';
        return '<tr><td>' + k + '</td><td style="text-align:right;color:' + color + ';font-weight:600">' + v.toFixed(4) + '</td></tr>';
      }}).join('');
      rows += '<tr><td><strong>Intercept</strong></td><td style="text-align:right">' +
              (nc.intercept || 0).toFixed(2) + '</td></tr>';
      coefBox.innerHTML = '<table class="ahp-table" style="width:100%;max-width:500px">' +
        '<thead><tr><th>Feature</th><th style="text-align:right">Coeficiente</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table>';
    }}
  }}
  if (typeof _tabInits !== 'undefined') {{
    _tabInits['forecast-metodologia'] = function() {{}};  // sección estática
    _tabInits['pulse-metodologia']    = function() {{}};  // sección estática
  }}
}})();

// ── Venezuela Hoy panel ──────────────────────────────────────────────────────
(function() {{
  var VH = {ven_hoy_json};
  if (!VH) return;

  function _delta(d, decimals, suffix) {{
    if (d == null) return '';
    var s = d >= 0 ? '▲ +' : '▼ ';
    var v = Math.abs(d).toFixed(decimals);
    return '<span style="color:' + (d >= 0 ? '#2ecc71' : '#e05c5c') + ';font-size:.68rem">'
           + s + v + (suffix || '') + ' vs año ant.</span>';
  }}
  function _deltaM(d, decimals, suffix) {{
    if (d == null) return '';
    var s = d >= 0 ? '▲ +' : '▼ ';
    var v = Math.abs(d).toFixed(decimals);
    return '<span style="color:' + (d >= 0 ? '#2ecc71' : '#e05c5c') + ';font-size:.68rem">'
           + s + v + (suffix || '') + ' vs 12m</span>';
  }}

  // === Hero cards ===
  if (VH.iciv) {{
    var ic = VH.iciv;
    var el = document.getElementById('vhIcivScore');
    if (el) el.textContent = ic.score.toFixed(2);
    el = document.getElementById('vhIcivLabel');
    if (el) {{ el.textContent = ic.label; el.style.color = ic.color; }}
    el = document.getElementById('vhIcivDelta');
    if (el) el.innerHTML = _delta(ic.delta, 1, ' pts');
    el = document.getElementById('vhIcivYear');
    if (el) {{
      el.textContent = 'ICIV ' + ic.year + (ic.coverage != null ? ' · ' + ic.coverage + '% cob.' : '')
        + (ic.is_reliable ? '' : ' · confiable: ' + ic.reliable_year + ' (' + ic.reliable_score.toFixed(1) + ')');
    }}
    // color del score
    var sc = document.getElementById('vhIcivScore');
    if (sc) sc.style.color = ic.color;
  }}
  if (VH.pulse) {{
    var pc = VH.pulse;
    var pelScore = document.getElementById('vhPulseScore');
    if (pelScore) pelScore.textContent = pc.score.toFixed(2);
    var pelLabel = document.getElementById('vhPulseLabel');
    if (pelLabel) pelLabel.textContent = pc.score >= 50 ? 'Ambiente favorable' : pc.score >= 35 ? 'Ambiente adverso' : 'Deterioro marcado';
    var pelDelta = document.getElementById('vhPulseDelta');
    if (pelDelta) pelDelta.innerHTML = _delta(pc.delta, 1, ' pts');
    var pelYear = document.getElementById('vhPulseYear');
    if (pelYear) pelYear.textContent = 'Pulse ' + pc.label_mes + ' ' + pc.year
                                       + (pc.coverage != null ? ' · ' + pc.coverage + '% cob.' : '');
  }}

  // === Indicadores grid ===
  var CARDS = [
    {{ key:'wti',        label:'WTI Oil',          fmt:function(v){{return '$'+v.toFixed(1)}}, unit:'USD/bbl',  icon:'', monthly:true }},
    {{ key:'brent',      label:'Brent Oil',         fmt:function(v){{return '$'+v.toFixed(1)}}, unit:'USD/bbl',  icon:'', monthly:true }},
    {{ key:'petroleo_ven',label:'Petróleo VEN',     fmt:function(v){{return v.toFixed(0)}},     unit:'TBPD',    icon:'', monthly:true }},
    {{ key:'pib_crec',   label:'PIB Crecimiento',  fmt:function(v){{return v.toFixed(1)+'%'}},  unit:'IMF 2026', icon:'', monthly:false }},
    {{ key:'inflacion',  label:'Inflación',         fmt:function(v){{return v.toFixed(0)+'%'}}, unit:'IMF 2026', icon:'', monthly:false }},
    {{ key:'fh',         label:'Freedom House',    fmt:function(v){{return v.toFixed(0)+'/100'}},unit:'FH 2026', icon:'', monthly:false }},
    {{ key:'cpi',        label:'CPI Corrupción',   fmt:function(v){{return v.toFixed(0)+'/100'}},unit:'TI 2025', icon:'', monthly:false }},
    {{ key:'wgi',        label:'WGI Gobernanza',   fmt:function(v){{return v.toFixed(2)}},      unit:'z-score',  icon:'', monthly:false }},
    {{ key:'migrantes',  label:'Migrantes',        fmt:function(v){{return v.toFixed(2)+'M'}}, unit:'UNHCR 2025',icon:'', monthly:false }},
    {{ key:'hdi',        label:'IDH / HDI',        fmt:function(v){{return v.toFixed(3)}},      unit:'UNDP 2024',icon:'', monthly:false }},
    {{ key:'vix',        label:'VIX Volatilidad',  fmt:function(v){{return v.toFixed(1)}},      unit:'puntos',   icon:'', monthly:true }},
    {{ key:'ust10y',     label:'UST 10Y Yield',    fmt:function(v){{return v.toFixed(2)+'%'}},  unit:'FRED',     icon:'', monthly:true }},
  ];

  var grid = document.getElementById('vhGrid');
  if (!grid) return;
  var html = '';
  CARDS.forEach(function(card) {{
    var d = VH[card.key];
    if (!d) return;
    var valStr = card.fmt(d.valor);
    var dateStr = d.mes ? (d.label_mes + ' ' + d.año) : d.año.toString();
    var dStr = card.monthly
      ? _deltaM(d.delta_12m, 1, (card.unit.indexOf('USD')>=0||card.unit.indexOf('bbl')>=0?'$':
                                  card.unit.indexOf('TBPD')>=0?' TBPD':' pts'))
      : _delta(d.delta, 1, (card.unit.indexOf('%')>=0?'%':' pts'));
    html += '<div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 14px">'
          + '<div style="font-size:.65rem;color:var(--muted);margin-bottom:6px;display:flex;justify-content:space-between;align-items:center">'
          + '<span>' + (card.icon ? card.icon + ' ' : '') + card.label + '</span>'
          + '<span style="font-size:.6rem;color:#555">' + card.unit + '</span>'
          + '</div>'
          + '<div style="font-size:1.6rem;font-weight:700;color:var(--text);line-height:1.1;margin-bottom:4px">' + valStr + '</div>'
          + '<div style="font-size:.63rem;color:#555;margin-bottom:4px">' + dateStr + '</div>'
          + (dStr ? '<div>' + dStr + '</div>' : '')
          + '</div>';
  }});
  grid.innerHTML = html;

  if (typeof _tabInits !== 'undefined') {{
    _tabInits['ven-hoy'] = function() {{}};  // already rendered
  }}
  if (window.location.hash === '#ven-hoy') showSection('ven-hoy');
}})();

// ─────────────────────────────────────────────────────────────────────────────
// INICIO — Hero (Pulse como protagonista) + sparkline + 6 indicadores clave
// ─────────────────────────────────────────────────────────────────────────────
(function() {{
  var VH = {ven_hoy_json};
  var PULSE_JS = {pulse_json};

  // ── Helpers ──
  function _col(score) {{
    if (score == null) return '#8b949e';
    if (score > 65) return '#27ae60';
    if (score > 50) return '#2ecc71';
    if (score > 35) return '#f1c40f';
    if (score > 20) return '#e67e22';
    return '#e74c3c';
  }}
  function _lbl(score) {{
    if (score == null) return '—';
    if (score > 65) return 'Muy Bajo Riesgo';
    if (score > 50) return 'Bajo Riesgo';
    if (score > 35) return 'Riesgo Moderado';
    if (score > 20) return 'Riesgo Moderado-Alto';
    return 'Alto Riesgo';
  }}
  function _deltaStr(d, dec, suf) {{
    if (d == null) return '';
    var s = d >= 0 ? '+' : '';
    return '<span style="color:' + (d >= 0 ? '#2ecc71' : '#e05c5c') + '">' + s + d.toFixed(dec) + (suf||'') + '</span>';
  }}

  // ── Pulse hero (INICIO + PORTADA badge) ──
  if (VH.pulse) {{
    var p = VH.pulse;
    var el;
    var pColor = p.is_reliable ? _col(p.score) : '#e6a817';
    var pLabel = p.is_reliable ? _lbl(p.score) : 'Provisional';
    el = document.getElementById('inicioPS');
    if (el) {{ el.textContent = p.score.toFixed(1); el.style.color = pColor; }}
    el = document.getElementById('inicioPL');
    if (el) {{ el.textContent = pLabel; el.style.color = pColor; }}
    el = document.getElementById('inicioPF');
    if (el) el.textContent = (p.label_mes || '') + ' ' + (p.year || '') + (p.is_reliable ? '' : ' · provisional');
    el = document.getElementById('inicioPD');
    if (el) el.innerHTML = _deltaStr(p.delta, 1, ' pts');
    el = document.getElementById('inicioPC');
    if (el) el.textContent = p.coverage != null ? p.coverage + '%' : '—';
    el = document.getElementById('inicioPR');
    if (el) el.textContent = p.is_reliable ? 'Lectura con cobertura alta.' : 'Último mes confiable: ' + p.reliable_label_mes + ' ' + p.reliable_year + ' · ' + p.reliable_score.toFixed(1) + ' · cobertura ' + p.reliable_coverage + '%';
    // También llena portada (score + color borde dinámico)
    el = document.getElementById('portadaPS');
    if (el) {{ el.textContent = p.score.toFixed(1); el.style.color = pColor; }}
    el = document.getElementById('portadaPF');
    if (el) el.textContent = pLabel + ' · ' + (p.label_mes || '') + ' ' + (p.year || '') + ' · ' + p.coverage + '% cob.';
    el = document.getElementById('portadaPR');
    if (el) el.textContent = p.is_reliable ? 'Lectura con cobertura alta.' : 'Último mes confiable: ' + p.reliable_label_mes + ' ' + p.reliable_year + ' · ' + p.reliable_score.toFixed(1) + ' · ' + p.reliable_coverage + '% cob.';
    el = document.getElementById('portadaPCard');
    if (el) el.style.borderLeftColor = pColor;
  }}

  // ── ICIV Anual hero ──
  if (VH.iciv) {{
    var ic = VH.iciv;
    var el2;
    el2 = document.getElementById('inicioAS');
    if (el2) {{ el2.textContent = ic.score.toFixed(1); el2.style.color = ic.color || _col(ic.score); }}
    el2 = document.getElementById('inicioAL');
    if (el2) {{ el2.textContent = ic.label; el2.style.color = ic.color || _col(ic.score); }}
    el2 = document.getElementById('inicioAD');
    if (el2) el2.innerHTML = _deltaStr(ic.delta, 1, ' pts');
    el2 = document.getElementById('inicioAY');
    if (el2) el2.textContent = 'ICIV ' + ic.year + (ic.coverage != null ? ' · ' + ic.coverage + '% cob.' : '');
    el2 = document.getElementById('inicioAR');
    if (el2) {{
      el2.textContent = ic.is_reliable
        ? 'Lectura anual con cobertura alta.'
        : 'Último anual confiable: ' + ic.reliable_year + ' · ' + ic.reliable_score.toFixed(1) + ' · ' + ic.reliable_coverage + '% cob.';
    }}
    // Mini gauge: misma lógica que el gauge principal (banda activa + aguja).
    // Bandas: [lo, hi, dashOffset, dashLen] sobre arco total 282.74 (π·90).
    var _IC_BANDS = [
      [0,  30,   0.0,  84.8],
      [30, 50,  84.8,  56.5],
      [50, 65, 141.3,  42.4],
      [65, 80, 183.7,  42.4],
      [80, 100,226.1,  56.5],
    ];
    var icCol = ic.color || _col(ic.score);
    var icAngle = -90 + (ic.score / 100) * 180;
    var icBand = _IC_BANDS[0];
    for (var bi = 0; bi < _IC_BANDS.length; bi++) {{
      if (ic.score > _IC_BANDS[bi][0] && ic.score <= _IC_BANDS[bi][1]) icBand = _IC_BANDS[bi];
    }}
    var inBand = document.getElementById('inicioActiveBand');
    if (inBand) {{
      inBand.setAttribute('stroke', icCol);
      inBand.setAttribute('stroke-dasharray', icBand[3] + ' 282.74');
      inBand.setAttribute('stroke-dashoffset', '-' + icBand[2]);
    }}
    var needle = document.getElementById('inicioNeedle');
    if (needle) {{
      needle.setAttribute('stroke', icCol);
      needle.setAttribute('transform', 'rotate(' + icAngle.toFixed(1) + ',110,110)');
    }}
    var inBase = document.getElementById('inicioNeedleBase');
    if (inBase) inBase.setAttribute('fill', icCol);
  }}

  // ── Sparkline Pulse: últimos 12 meses ──
  // Canvas es display:none (sustituido por cInicioFullPulse).
  // Guard: solo renderizar si visible Y datos correctos (PULSE_JS.data es objeto, no array).
  var sparkCanvas = document.getElementById('cInicioSparkline');
  if (sparkCanvas && sparkCanvas.style.display !== 'none'
      && PULSE_JS && PULSE_JS.data && PULSE_JS.data.meses) {{
    var _pd2   = PULSE_JS.data;
    var _n2    = _pd2.meses.length;
    var _st2   = Math.max(0, _n2 - 12);
    var _MES   = ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
    var slabels = _pd2.meses.slice(_st2).map(function(m) {{
      var p = m.split('-');
      return _MES[parseInt(p[1])] + ' ' + p[0].slice(2);
    }});
    var svals   = _pd2.scores.slice(_st2);
    var scolors = svals.map(function(v) {{ return _col(v); }});
    new Chart(sparkCanvas, {{
      type: 'line',
      data: {{
        labels: slabels,
        datasets: [{{
          data: svals,
          borderColor: '#3498db', backgroundColor: 'rgba(52,152,219,.08)',
          borderWidth: 2, pointRadius: 3,
          pointBackgroundColor: scolors, pointBorderColor: 'transparent',
          tension: 0.35, fill: true, spanGaps: true,
        }}]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false, animation: false,
        plugins: {{ legend: {{ display: false }}, tooltip: {{
          callbacks: {{ label: function(c) {{ return 'Pulse: ' + (c.raw != null ? c.raw.toFixed(1) : '—'); }} }}
        }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 9 }}, maxRotation: 0 }} }},
          y: {{ min: 20, max: 90, grid: {{ color: 'rgba(255,255,255,.04)' }},
               ticks: {{ font: {{ size: 9 }}, stepSize: 20 }} }}
        }}
      }}
    }});
  }}

  // ── 6 indicadores clave en grid INICIO ──
  var ICARDS = [
    {{ key:'wti',         label:'WTI Oil',        fmt:function(v){{return '$'+v.toFixed(1)}}, unit:'USD/bbl' }},
    {{ key:'brent',       label:'Brent Oil',       fmt:function(v){{return '$'+v.toFixed(1)}}, unit:'USD/bbl' }},
    {{ key:'petroleo_ven',label:'Petróleo VEN',    fmt:function(v){{return v.toFixed(0)+' TBPD'}}, unit:'EIA mensual' }},
    {{ key:'inflacion',   label:'Inflación VEN',   fmt:function(v){{return v.toFixed(0)+'%'}}, unit:'IMF 2026' }},
    {{ key:'migrantes',   label:'Diáspora',        fmt:function(v){{return v.toFixed(2)+'M'}}, unit:'UNHCR' }},
    {{ key:'vix',         label:'VIX Volatilidad', fmt:function(v){{return v.toFixed(1)}}, unit:'riesgo global' }},
  ];
  var igrid = document.getElementById('inicioGrid');
  if (igrid) {{
    var ihtml = '';
    ICARDS.forEach(function(c) {{
      var d = VH[c.key];
      if (!d) return;
      var valStr = c.fmt(d.valor);
      var dateStr = d.mes ? (['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][d.mes] + ' ' + d.año) : d.año;
      ihtml += '<div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 16px">'
             + '<div style="font-size:.63rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">' + c.label + ' <span style="color:#555;font-size:.58rem">' + c.unit + '</span></div>'
             + '<div style="font-size:1.7rem;font-weight:700;color:var(--text);line-height:1">' + valStr + '</div>'
             + '<div style="font-size:.63rem;color:#555;margin-top:5px">' + dateStr + '</div>'
             + '</div>';
    }});
    igrid.innerHTML = ihtml;
  }}

  // ── Gráfico completo Pulse 2010–2026 — se inicia al mostrar #inicio ──
  if (typeof _tabInits !== 'undefined') {{
    _tabInits['inicio'] = function() {{
      var ctx2 = document.getElementById('cInicioFullPulse');
      // PULSE_JS.data es un objeto {{ meses:[...], scores:[...], cobertura:[...] }}
      // NO es un array de objetos — usar las claves directamente
      if (!ctx2 || !PULSE_JS || !PULSE_JS.data || !PULSE_JS.data.meses) return;
      var pd     = PULSE_JS.data;           // {{ meses, scores, cobertura, n_vars }}
      var meses  = pd.meses;                // ["2010-01", "2010-02", ...]
      var scores = pd.scores;               // [float|null, ...]
      var cov    = pd.cobertura;            // [float, ...]
      var MONTHS_ES = ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
      // Etiquetas: año en enero, mes abreviado en múltiplos de 3, vacío el resto
      var labels = meses.map(function(m) {{
        var parts = m.split('-');
        var yr = parts[0], mo = parseInt(parts[1]);
        if (mo === 1) return yr;
        if (mo % 3 === 0) return MONTHS_ES[mo] + "'" + yr.slice(2);
        return '';
      }});
      var hi_cov = scores.map(function(s,i) {{ return (cov[i] != null && cov[i] >= 70) ? s : null; }});
      var lo_cov = scores.map(function(s,i) {{ return (cov[i] != null && cov[i] < 70)  ? s : null; }});
      var icivRef     = {scores_ahp_js}[{scores_ahp_js}.length - 1];
      var icivRefLine = scores.map(function() {{ return icivRef; }});
      new Chart(ctx2, {{
        type: 'line',
        data: {{
          labels: labels,
          datasets: [
            {{
              label: 'Pulse mensual (cob ≥70%)',
              data: hi_cov,
              borderColor: '#00d4aa', backgroundColor: 'rgba(0,212,170,.06)',
              borderWidth: 2, pointRadius: 0, tension: 0.3, fill: true, spanGaps: false,
            }},
            {{
              label: 'Pulse mensual (cob <70%, provisional)',
              data: lo_cov,
              borderColor: 'rgba(0,212,170,0.4)', backgroundColor: 'transparent',
              borderWidth: 1.5, pointRadius: 3, pointStyle: 'circle',
              pointBackgroundColor: 'transparent', pointBorderColor: 'rgba(0,212,170,0.5)',
              tension: 0.3, fill: false, borderDash: [4,3], spanGaps: false,
            }},
            {{
              label: 'ICIV Anual {current_year_val} (referencia)',
              data: icivRefLine,
              borderColor: '#f1c40f', backgroundColor: 'transparent',
              borderWidth: 1.5, pointRadius: 0, borderDash: [6,4], fill: false,
            }},
          ]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false, animation: {{duration: 400}},
          plugins: {{
            legend: {{ position: 'top', labels: {{ color:'#8b949e', font:{{size:10}}, boxWidth:18 }} }},
            tooltip: {{
              callbacks: {{
                label: function(ctx) {{
                  if (ctx.dataset.label.startsWith('Pulse')) return 'Pulse: ' + (ctx.raw != null ? ctx.raw.toFixed(1) : '—');
                  return ctx.dataset.label + ': ' + (ctx.raw != null ? ctx.raw.toFixed(1) : '—');
                }}
              }}
            }}
          }},
          scales: {{
            x: {{ ticks: {{ color:'#8b949e', font:{{size:9}}, maxRotation:0,
                            callback: function(v,i) {{ return labels[i]; }} }},
                 grid: {{ color:'rgba(255,255,255,.03)' }} }},
            y: {{ min:20, max:100,
                 ticks: {{ color:'#8b949e', font:{{size:9}}, stepSize:20 }},
                 grid: {{ color:'rgba(255,255,255,.05)' }} }},
          }}
        }}
      }});
    }};
    _tabInits['portada'] = function() {{}};  // rendered on load

    // Si INICIO ya está activo cuando este IIFE corre (ej. URL con #inicio),
    // ejecutar el chart ahora mismo (no esperar click de nav).
    var _inicioSec = document.getElementById('inicio');
    if (_inicioSec && _inicioSec.classList.contains('tab-active')) {{
      var _chartFn = _tabInits['inicio'];
      _tabInits['inicio'] = null;
      setTimeout(_chartFn, 60);
    }}
  }}
}})();

</script>
</body>
</html>"""

    # ── DASHBOARD: UN ÚNICO ARCHIVO en la raíz del proyecto ─────────────────────
    # Ruta canónica: C:\Users\pipeg\Documents\Claude\Projects\
    #                Investigación Indicador Macroeconomico Venezuela\iciv_dashboard.html
    # _ROOT      = carpeta iciv/  (donde vive main.py)
    # _ROOT.parent = raíz del proyecto (Investigación Indicador Macroeconomico Venezuela/)
    # NO crear copias en iciv/ ni en data/processed/. Un solo archivo, siempre aquí.
    out_path = _ROOT.parent / "iciv_dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    logger.info("  OK Dashboard -> %s", out_path)
    return out_path


def _get_recommendation(score: float) -> str:
    if score <= 30:
        return ("Venezuela presenta condiciones de <strong>alto riesgo</strong> para la inversión. "
                "No se recomienda entrada de capital nuevo. Empresas con presencia existente deben "
                "evaluar estrategias de protección o salida con mínima exposición adicional.")
    if score <= 50:
        return ("El clima de inversión es de <strong>riesgo moderado-alto</strong>. "
                "Viable únicamente para sectores con alta tolerancia al riesgo (minería, energía) "
                "con estructuras de máxima protección contractual y seguros de riesgo político.")
    if score <= 65:
        return ("Condiciones de <strong>riesgo moderado</strong>. Inversión viable con due diligence "
                "reforzado, análisis sectorial específico, socios locales sólidos y estructuras de "
                "mitigación (seguros, arbitraje internacional).")
    if score <= 80:
        return ("Condiciones <strong>favorables</strong> para la mayoría de sectores. Se recomienda "
                "análisis sectorial estándar antes de comprometer capital. Monitorear indicadores "
                "institucionales para identificar cambios en el entorno.")
    return ("Clima de inversión <strong>sólido</strong>, comparable a mercados emergentes estables. "
            "Entrada recomendada con análisis sectorial convencional.")


# =============================================================================
# MAIN
# =============================================================================

# =============================================================================
# FASE 5 -- VALIDACION DEL MODELO
# =============================================================================

def fase_validacion(open_browser: bool = False) -> Path:
    """Delega en scripts/validate_model.py — mantiene main.py limpio."""
    import importlib
    sys.path.insert(0, str(_ROOT / "scripts"))
    vm = importlib.import_module("validate_model")
    return vm.run_validation(open_browser=open_browser)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ICIV -- Pipeline completo del Indicador de Clima de Inversión Venezuela"
    )
    parser.add_argument(
        "--no-fetch", action="store_true",
        help="Omitir descarga de datos (usa archivos existentes en data/raw/)"
    )
    parser.add_argument(
        "--no-open", action="store_true",
        help="No abrir el navegador al terminar"
    )
    parser.add_argument(
        "--validate-only", action="store_true",
        help="Solo ejecutar la validacion del modelo (requiere datos ya procesados)"
    )
    args = parser.parse_args()

    t0 = time.time()

    print("\n" + "=" * 60)
    print("  ICIV -- Indicador de Clima de Inversion Venezuela")
    print("  Pipeline completo - " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    print("=" * 60)

    settings = Settings()
    settings.paths.ensure_exists()

    if args.validate_only:
        # Solo validacion — salta fetch, pipeline y modelo
        val_path = fase_validacion(open_browser=not args.no_open)
        elapsed = time.time() - t0
        print(f"\n  OK Validacion completada en {elapsed:.1f}s")
        print(f"      iciv_validacion.html")
        print("=" * 60 + "\n")
        return

    # -- Fase 1: Fetch ----------------------------------------------------------
    if not args.no_fetch:
        fase_fetch(settings)
    else:
        logger.info("\n  [i] --no-fetch: usando datos existentes en data/raw/")

    # -- Fase 2: Pipeline -------------------------------------------------------
    df_raw, df_norm = fase_pipeline(settings)
    fase_dataset_publico(df_raw, df_norm, settings)

    # -- Fase 3: Modelo ---------------------------------------------------------
    df_fixed, df_ahp, ahp = fase_modelo(df_norm, settings)

    # -- Fase 3b: ICIV Pulse Mensual (co-indicador) ----------------------------
    pulse_data = fase_pulse(settings)

    # -- Fase 3c: SATV Pulse ----------------------------------------------------
    satv_data = fase_satv(settings, pulse_data)

    # -- Fase 3d: Correlación ICIV → IED ----------------------------------------
    correlacion_data = fase_correlacion(df_raw, df_ahp)

    # -- Fase 3e: Radar Sectorial -----------------------------------------------
    # Las proyecciones anuales por escenario, Simulacion probabilistica retirada y red de sanciones dejaron de
    # exponerse en el dashboard principal; el pipeline semanal calcula solo las
    # piezas defendibles que se usan en la experiencia final.
    escenarios_data: dict = {}
    sanciones_data: dict = {}
    mc_data: dict = {}
    sector_data = fase_sector_radar(df_ahp)

    # -- Fase 3f: Forecast mensual Pulse ----------------------------------------
    ml_forecast = fase_ml_forecast(pulse_data, df_ahp)

    # -- Fase 4: Dashboard ------------------------------------------------------
    dashboard_path = fase_dashboard(
        df_raw, df_norm, df_fixed, df_ahp, ahp, settings,
        satv_data, escenarios_data, correlacion_data, sanciones_data,
        mc_data, sector_data, pulse_data, ml_forecast
    )

    # -- Fase 5: Validacion -----------------------------------------------------
    val_path = fase_validacion(open_browser=False)

    # -- Resumen final ----------------------------------------------------------
    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"  OK Pipeline completado en {elapsed:.1f}s")
    print(f"  OK Archivos en data/processed/:")
    print(f"      iciv_normalizado.csv")
    print(f"      iciv_scores.csv           (pesos fijos)")
    print(f"      iciv_scores_ahp.csv       (pesos AHP)")
    print(f"      iciv_dashboard.html       (dashboard interactivo)")
    print(f"      iciv_validacion.html      (validacion del modelo)")
    print("=" * 60 + "\n")

    # -- Abrir dashboard --------------------------------------------------------
    if not args.no_open:
        logger.info("  Abriendo dashboard en el navegador...")
        webbrowser.open(dashboard_path.as_uri())


if __name__ == "__main__":
    main()
