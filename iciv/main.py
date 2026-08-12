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
import math
import os
import re
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
from iciv.utils import load_env_key

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
        # fetch_viirs_states (Li et al. por bbox estatal) se retiró del pipeline
        # el 2026-07-29: el mapa subnacional ahora usa Black Marble con máscara
        # poligonal. El script y su CSV se conservan para auditoría.
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

    # ── Año en curso de producción petrolera desde la serie mensual ────────────
    # `petroleo_crudo_produccion_tbpd` pesa 9% del índice, más que ninguna otra
    # variable, y la serie ANUAL de EIA llega con ~1 año de rezago. La serie
    # MENSUAL del MISMO producto (57, crude oil incl. lease condensate) ya se
    # descarga y su promedio reproduce la serie anual con 0,05% de diferencia
    # media sobre 11 años completos — es el mismo estadístico, no una base
    # distinta. Por eso se puede completar el año en curso sin inventar nada.
    #
    # Reglas, para que esto no se convierta en un relleno silencioso:
    #   · Solo se rellenan años cuyo valor anual es NaN. Nunca se pisa un dato real.
    #   · El valor es el promedio de los meses REALMENTE publicados (año corrido).
    #   · Se exige un mínimo de meses para no extrapolar de una sola observación.
    #   · Queda registrado en el log y en data/processed/anualizacion_parcial.csv.
    _MIN_MESES_ANUALIZAR = 3
    _VAR_ANUAL = "petroleo_crudo_produccion_tbpd"
    _VAR_MENSUAL = "petroleo_crudo_mensual_anualizable_tbpd"
    _ruta_eia_m = settings.paths.data_raw / "eia_monthly.csv"
    _anualizados: list[dict] = []
    if _VAR_ANUAL in master.columns and _ruta_eia_m.exists():
        try:
            _em = pd.read_csv(_ruta_eia_m)
            _em = _em[_em["variable"] == _VAR_MENSUAL]
            if not _em.empty:
                _agg = _em.groupby("año")["valor"].agg(["mean", "count"])
                for _a, _f in _agg.iterrows():
                    _fila = master["año"] == int(_a)
                    if not _fila.any():
                        continue
                    _ya_tiene = master.loc[_fila, _VAR_ANUAL].notna().all()
                    if _ya_tiene or _f["count"] < _MIN_MESES_ANUALIZAR:
                        continue
                    master.loc[_fila, _VAR_ANUAL] = float(_f["mean"])
                    _anualizados.append({
                        "año": int(_a),
                        "variable": _VAR_ANUAL,
                        "valor": round(float(_f["mean"]), 2),
                        "meses_usados": int(_f["count"]),
                        "origen": "EIA International mensual, producto 57 (crude oil incl. lease condensate)",
                        "nota": "promedio de los meses publicados; año incompleto",
                    })
                    logger.info(
                        "  %s %d completado con %d meses reales de EIA -> %.1f tbpd (año corrido)",
                        _VAR_ANUAL, int(_a), int(_f["count"]), _f["mean"],
                    )
        except Exception as _exc:
            logger.warning("  No se pudo anualizar %s: %s", _VAR_ANUAL, _exc)

    # ── Luminosidad nocturna: Li et al. → NASA Black Marble ───────────────────
    # La serie de Li et al. (viirs.csv) cubre 2000-2024 pero es un dataset
    # académico de actualización irregular: llega con ~2 años de rezago, así que
    # no puede describir el año en curso ni el anterior.
    #
    # Black Marble (VNP46A3) ya se descarga mensualmente con ~2 meses de rezago y
    # cubre 2014-2026 con máscara poligonal exacta y unidades físicas reales.
    # Se sustituye la variable COMPLETA por el promedio anual de Black Marble.
    # NO se empalman las dos series: son productos distintos con escalas distintas
    # (Li et al. ~11,6 en índice adimensional; Black Marble ~0,9 nW/cm²/sr).
    # Mezclarlas sería repetir el error del LSCI.
    #
    # Coste asumido y declarado: 2000-2013 pierden esta variable. Se acepta porque
    # el índice debe poder describir el presente, y D2 conserva la producción
    # petrolera de EIA con historia completa para esos años.
    # viirs.csv y fetch_viirs.py se conservan: siguen siendo el validador externo
    # no circular de la validación leave-one-out.
    _VAR_LUM = "luminosidad_nocturna_idx"
    _ruta_bm = settings.paths.data_raw / "blackmarble_monthly.csv"
    if _ruta_bm.exists():
        try:
            _bm = pd.read_csv(_ruta_bm)
            _bm = _bm[_bm["variable"] == "luminosidad_nocturna_mensual_nwcm2sr"]
            if not _bm.empty:
                _bm_anual = _bm.groupby("año")["valor"].agg(["mean", "count"])
                _bm_anual = _bm_anual[_bm_anual["count"] >= _MIN_MESES_ANUALIZAR]
                master[_VAR_LUM] = master["año"].map(_bm_anual["mean"])
                _n_ok = int(master[_VAR_LUM].notna().sum())
                logger.info(
                    "  %s <- NASA Black Marble: %d años (%d-%d), sustituye a Li et al.",
                    _VAR_LUM, _n_ok,
                    int(_bm_anual.index.min()), int(_bm_anual.index.max()),
                )
                for _a, _f in _bm_anual.iterrows():
                    if _f["count"] < 12:
                        _anualizados.append({
                            "año": int(_a),
                            "variable": _VAR_LUM,
                            "valor": round(float(_f["mean"]), 4),
                            "meses_usados": int(_f["count"]),
                            "origen": "NASA Black Marble VNP46A3, media nacional mensual",
                            "nota": "promedio de los meses publicados; año incompleto",
                        })
        except Exception as _exc:
            logger.warning("  No se pudo construir %s desde Black Marble: %s", _VAR_LUM, _exc)

    if _anualizados:
        _ruta_anual_parcial = settings.paths.data_processed / "anualizacion_parcial.csv"
        pd.DataFrame(_anualizados).to_csv(_ruta_anual_parcial, index=False, encoding="utf-8-sig")
        logger.info("  Registro de anualizaciones parciales -> %s", _ruta_anual_parcial.name)

    # ── Reconversión monetaria + log10 para tipo_cambio_oficial_lcu_usd ─────────
    # El WDI publica la serie en la denominación vigente de cada año, sin unificar:
    #   2000-2017 → BsF/USD  (el API ya expresa estos años en bolívar fuerte)
    #   2018-2021 → BsS/USD  (bolívar soberano)
    #   2022+     → Bs.D/USD (bolívar digital)
    #
    # Reconversiones OFICIALES (Gaceta Oficial):
    #   2008-01-01  BsF  = 1.000 Bs        → quita 3 ceros
    #   2018-08-20  BsS  = 100.000 BsF     → quita 5 ceros
    #   2021-10-01  Bs.D = 1.000.000 BsS   → quita 6 ceros
    #
    # Para llevar todo a BsF equivalente:
    #   BsS  → BsF : x 1e5
    #   Bs.D → BsF : x 1e5 * 1e6 = 1e11
    #
    # CORREGIDO 2026-08-11: los factores anteriores (1e3 y 1e9) usaban 1.000 para
    # la reconversión de 2018, que en realidad quitó 5 ceros y no 3. Ambos estaban
    # 100x por debajo, lo que comprimía el salto real 2017→2020 de 9,5 a 7,5
    # órdenes de magnitud y alteraba la normalización Min-Max de toda la serie.
    _BSS_A_BSF = 100_000            # 1e5
    _BSD_A_BSF = 100_000_000_000    # 1e11
    if "tipo_cambio_oficial_lcu_usd" in master.columns:
        _tc = master["tipo_cambio_oficial_lcu_usd"].copy()
        _mask_bss = (master["año"] >= 2018) & (master["año"] <= 2021)
        _mask_bs  = master["año"] >= 2022
        _tc[_mask_bss] = _tc[_mask_bss] * _BSS_A_BSF
        _tc[_mask_bs]  = _tc[_mask_bs]  * _BSD_A_BSF
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
    agg_fixed = ICIVAggregator(
        method="linear",
        strategy=FixedWeights(override=_equal_overrides),
        min_dimension_coverage=settings.aggregation.min_dimension_coverage,
    )
    df_fixed = agg_fixed.compute(df_norm)
    df_fixed.to_csv(settings.paths.data_processed / "iciv_scores.csv",
                    index=False, encoding="utf-8-sig")
    logger.info("  OK Pesos Iguales (1/6 por dimensión) -> data/processed/iciv_scores.csv")

    # -- AHP (Saaty) -----------------------------------------------------------
    # compute_weights() debe llamarse antes de pasarlo al aggregator
    # para que dimension_result_ esté disponible al momento de agregar.
    ahp = AHPWeights()
    ahp.compute_weights(df_norm)  # inicializa dimension_result_ y variable_results_
    agg_ahp = ICIVAggregator(
        method="linear",
        strategy=ahp,
        min_dimension_coverage=settings.aggregation.min_dimension_coverage,
    )
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
        # min_dimension_coverage=0: en un leave-one-out el objetivo es aislar el
        # aporte de UNA variable. Aplicar el piso de cobertura aquí anularía la
        # dimensión entera cuando la variable retirada la deja por debajo del
        # umbral, y el test mediría eso en vez del efecto de la variable.
        df_loo = df_norm.copy()
        df_loo[col] = np.nan
        return (ICIVAggregator(method="linear", min_dimension_coverage=0.0)
                .compute(df_loo).set_index("año")["iciv_score"])

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
            "ICIV recalculado sin migración", "Refugiados y solicitantes de asilo (millones)",
            "ICIV (leave-one-out) vs Desplazamiento registrado UNHCR")
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


# Etiquetas cortas por dimensión para ejes de gráficos. Los nombres completos
# de DIMENSIONS no caben en el eje y del gráfico "Dónde está el problema".
_DIM_SHORT = {
    "D1_macro":          "Macroeconomía",
    "D2_energia":        "Energía y petróleo",
    "D3_institucional":  "Instituciones y ley",
    "D4_comercial":      "Apertura comercial",
    "D5_capital_humano": "Capital humano",
    "D6_percepcion":     "Percepción externa",
}


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

    # Barras de diagnóstico por dimensión.
    # Cada dimensión se toma de su ÚLTIMO año con dato real, no del año en curso:
    # en el año corriente varias fuentes anuales aún no publicaron y un 0 se leería
    # como "colapso total" cuando en realidad significa "todavía sin publicar".
    last_row  = _current_row
    dim_vals, dim_lbls, dim_clrs, dim_years, dim_covs = [], [], [], [], []
    for _i, _d in enumerate(available_dims):
        _cols = ["año", _d] + ([f"cobertura_{_d}"] if f"cobertura_{_d}" in df_plot.columns else [])
        _serie = df_plot[_cols].dropna(subset=[_d]) if _d in df_plot.columns else None
        if _serie is None or _serie.empty:
            continue   # dimensión sin ningún dato: se omite en vez de dibujar un cero
        _fila = _serie.iloc[-1]
        dim_vals.append(round(float(_fila[_d]), 2))
        # Etiqueta corta: el nombre completo de la dimensión no cabe en el eje y
        # Chart.js lo recortaba por la izquierda ("apital Humano e Infra...").
        dim_lbls.append(_DIM_SHORT.get(_d, dim_names.get(_d, _d)))
        dim_clrs.append(DIM_COLORS[_i % len(DIM_COLORS)])
        dim_years.append(int(_fila["año"]))
        # Cobertura de la dimensión ESE año. Un 0.0 con 60% de cobertura es un
        # dato ("el peor registro de la serie"); el mismo 0.0 con 18% sería
        # ruido — por eso el agregador ya no lo publica y por eso el gráfico
        # declara la cobertura en vez de dibujar todas las barras igual.
        _cov_col = f"cobertura_{_d}"
        dim_covs.append(round(float(_fila[_cov_col]), 1)
                        if _cov_col in _serie.columns and pd.notna(_fila.get(_cov_col))
                        else None)
    dim_years_js = json.dumps(dim_years)
    dim_covs_js  = json.dumps(dim_covs)
    # Año más antiguo entre las dimensiones mostradas — se declara en el subtítulo
    dim_year_min = min(dim_years) if dim_years else current_year_val
    dim_year_max = max(dim_years) if dim_years else current_year_val
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

    # ── Clave Guardian para el fetch en vivo del navegador ───────────────────
    #
    # Incrustar la clave la vuelve PÚBLICA: iciv_dashboard.html se versiona en
    # git y se publica en GitHub Pages, así que la clave queda en el historial
    # del repo y a la vista de cualquiera. Rotarla no basta —la siguiente queda
    # expuesta igual en la siguiente corrida.
    #
    # Desde que el bloque de noticias se alimenta del snapshot generado en el
    # fetch (guardian_headlines.csv), el fetch en vivo no aporta nada que el
    # snapshot no cubra, así que NO se incrusta por defecto.
    #
    # Para reactivar el fetch en vivo, asumiendo que la clave será pública:
    #     ICIV_EMBED_GUARDIAN_KEY=1 python main.py
    _embed_key = str(os.environ.get("ICIV_EMBED_GUARDIAN_KEY", "")).strip().lower()
    if _embed_key in {"1", "true", "yes", "si", "sí"}:
        guardian_key = load_env_key("GUARDIAN_API_KEY") or ""
        if guardian_key:
            logger.warning(
                "  ICIV_EMBED_GUARDIAN_KEY activo: la clave de The Guardian se "
                "incrusta en el HTML y sera PUBLICA al publicar el dashboard."
            )
        else:
            logger.warning(
                "  ICIV_EMBED_GUARDIAN_KEY activo pero GUARDIAN_API_KEY ausente: "
                "el bloque de noticias usara solo el snapshot."
            )
    else:
        guardian_key = ""
        logger.info(
            "  Clave Guardian NO incrustada (por defecto). El bloque de noticias "
            "usa guardian_headlines.csv. Para el fetch en vivo: ICIV_EMBED_GUARDIAN_KEY=1."
        )

    # ── Datos del Simulador ───────────────────────────────────────────────────
    # Solo entran dimensiones con datos reales: una dimensión vacía tratada como 0
    # hunde el resultado simulado y lo aleja del índice publicado. Los pesos se
    # renormalizan sobre las incluidas, igual que hace el índice anual.
    _sim_usable = [
        (_d_id.value, _d) for _d_id, _d in DIMENSIONS.items()
        if _d_id.value in df_plot.columns and df_plot[_d_id.value].notna().any()
    ]
    # Año base: el más reciente con dato en TODAS las dimensiones utilizables
    _sim_complete = df_plot.dropna(subset=[k for k, _ in _sim_usable])
    _sim_base_row = _sim_complete.iloc[-1] if not _sim_complete.empty else df_plot.iloc[-1]
    sim_base_year = int(_sim_base_row["año"])

    # Pesos del simulador: los MISMOS que publica el índice.
    # Antes se usaba _d.iciv_weight (los pesos fijos 25/20/20/15/10/10) mientras
    # cada slider se rotulaba "Peso AHP", que son otros (25,4/19,5/19,5/17,4/
    # 9,1/9,1). El rótulo mentía y el botón "Volver a {año}" no reproducía el
    # score publicado de ese año. Se toman de la estrategia AHP ya calculada.
    _ahp_dim_w = {}
    _ahp_res = getattr(ahp, "dimension_result_", None)
    if _ahp_res and _ahp_res.get("weights"):
        _ahp_dim_w = dict(_ahp_res["weights"])

    def _dim_weight(key: str, dim) -> float:
        return float(_ahp_dim_w.get(key, dim.iciv_weight))

    _sim_weight_total = sum(_dim_weight(_k, _d) for _k, _d in _sim_usable) or 1.0
    _sim_dims: list[dict] = []
    for _key, _d in _sim_usable:
        _hist_vals = [round(float(v), 2) if v is not None and str(v) != "nan" else None
                      for v in df_plot[_key].tolist()]
        _cur_raw = _sim_base_row.get(_key)
        _cur = round(float(_cur_raw), 1) if _cur_raw is not None and not pd.isna(_cur_raw) else 0.0
        _sim_dims.append({
            "id":      _key,
            "label":   _d.name,
            "weight":  round(_dim_weight(_key, _d) / _sim_weight_total, 6),
            "current": _cur,
            "hist":    _hist_vals,
            "max_hist": max((v for v in _hist_vals if v is not None), default=100.0),
        })
    sim_dims_json = json.dumps(_sim_dims, ensure_ascii=False)
    sim_years_js  = years_js   # same years already computed
    sim_scores_js = scores_ahp_js  # same AHP scores already computed

    # ── Validación y correlación ─────────────────────────────────────────────
    # El dashboard es el producto para el usuario final y ya no incrusta bloques
    # metodológicos, así que no se generan aquí las figuras matplotlib ni las
    # tablas de OLS/Granger/leave-one-out: costaban segundos de pipeline y cientos
    # de KB de base64 para nada. Ese material vive en:
    #   · iciv/data/processed/iciv_validacion.html  (scripts/validate_model.py)
    #   · docs/VALIDACION_EXTERNA.md, docs/MODEL_CARD.md, docs/BACKTESTING_FORECAST.md
    # Las funciones _generate_corr_charts_b64 / _build_corr_stats_html /
    # _generate_loo_validation_html se conservan por si se necesitan en el anexo.

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

    # Mapa coroplético subnacional Black Marble — radiancia por estado, anual y mensual
    _bmmap: dict = {
        "viewbox": [1000, 700], "estados": [],
        "years": [], "radiance": {},          # promedio anual por estado
        "months": [], "radiance_m": {},       # valor mensual por estado
        "vmin": 0.01, "vmax": 1.0,
    }
    try:
        _st_path = settings.paths.data_raw / "blackmarble_states_monthly.csv"
        _geojson_bm = settings.paths.data_raw / "venezuela_states.geojson"
        if _st_path.exists() and _geojson_bm.exists():
            _gj = json.loads(_geojson_bm.read_text(encoding="utf-8"))
            _feats = _gj.get("features", [])

            # Encuadre: Venezuela continental + islas principales. Isla de Aves
            # (15.7 N) queda fuera del encuadre visual porque estiraria el mapa
            # un 25% por un punto de 4 km2; sus datos siguen en el CSV.
            _LAT_MAX_VIEW = 12.9
            _lons, _lats = [], []
            for _f in _feats:
                _g = _f.get("geometry") or {}
                _polys = ([_g["coordinates"]] if _g.get("type") == "Polygon"
                          else _g.get("coordinates", []) if _g.get("type") == "MultiPolygon" else [])
                for _poly in _polys:
                    for _ring in _poly:
                        for _pt in _ring:
                            if _pt[1] <= _LAT_MAX_VIEW:
                                _lons.append(_pt[0]); _lats.append(_pt[1])
            _lo0, _lo1, _la0, _la1 = min(_lons), max(_lons), min(_lats), max(_lats)
            # Proyección equirectangular con corrección de latitud (aspecto real)
            _cos_lat = math.cos(math.radians((_la0 + _la1) / 2.0))
            _W = 1000.0
            _H = round(_W * (_la1 - _la0) / ((_lo1 - _lo0) * _cos_lat))
            _bmmap["viewbox"] = [int(_W), int(_H)]

            def _proj(pt):
                x = (pt[0] - _lo0) / (_lo1 - _lo0) * _W
                y = (_la1 - pt[1]) / (_la1 - _la0) * _H
                return f"{x:.1f},{y:.1f}"

            def _pretty(name: str) -> str:
                # DistritoCapital -> Distrito Capital ; DeltaAmacuro -> Delta Amacuro
                return re.sub(r"(?<=[a-záéíóú])(?=[A-ZÁÉÍÓÚ])", " ", name)

            for _f in _feats:
                _g = _f.get("geometry") or {}
                _polys = ([_g["coordinates"]] if _g.get("type") == "Polygon"
                          else _g.get("coordinates", []) if _g.get("type") == "MultiPolygon" else [])
                _d = []
                for _poly in _polys:
                    for _ring in _poly:
                        if len(_ring) < 3:
                            continue
                        _pts = [p for p in _ring if p[1] <= _LAT_MAX_VIEW + 0.5]
                        if len(_pts) < 3:
                            continue
                        # simplificación suave: conserva forma sin inflar el HTML
                        _step = 2 if len(_pts) > 400 else 1
                        _d.append("M" + "L".join(_proj(p) for p in _pts[::_step]) + "Z")
                _bmmap["estados"].append({
                    "cod": _f["properties"].get("cod", ""),
                    "nombre": _pretty(_f["properties"].get("nombre", "")),
                    "d": "".join(_d),
                })

            _st = pd.read_csv(_st_path)
            # Serie anual (promedio de los meses disponibles de cada año)
            _st_annual = _st.groupby(["año", "cod"])["radiancia_media"].mean().reset_index()
            _bmmap["years"] = [int(y) for y in sorted(_st_annual["año"].unique())]
            for _y in _bmmap["years"]:
                _sub = _st_annual[_st_annual["año"] == _y]
                _bmmap["radiance"][str(_y)] = {
                    r["cod"]: round(float(r["radiancia_media"]), 3) for _, r in _sub.iterrows()
                }
            # Serie mensual
            _st = _st.sort_values(["año", "mes"])
            _st["mstr"] = (_st["año"].astype(int).astype(str) + "-"
                           + _st["mes"].astype(int).astype(str).str.zfill(2))
            _bmmap["months"] = sorted(_st["mstr"].unique().tolist())
            for _m, _sub in _st.groupby("mstr"):
                _bmmap["radiance_m"][_m] = {
                    r["cod"]: round(float(r["radiancia_media"]), 3) for _, r in _sub.iterrows()
                }
            # Escala de color compartida por ambos modos (log): p2 a p98 mensual
            _allvals = _st["radiancia_media"].values
            if len(_allvals):
                _bmmap["vmin"] = max(round(float(np.percentile(_allvals, 2)), 4), 0.001)
                _bmmap["vmax"] = round(float(np.percentile(_allvals, 98)), 3)
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

    # Snapshot de titulares de The Guardian generado en el fetch.
    # Es la fuente PRIMARIA del bloque: el fetch en vivo del navegador es una
    # mejora opcional que lo reemplaza si funciona. Antes el bloque dependia
    # unicamente del fetch en vivo y mostraba "Failed to fetch" en crudo cuando
    # un bloqueador o una red corporativa cortaba content.guardianapis.com.
    _guardian_snapshot: list[dict] = []
    _guardian_snapshot_date = ""
    try:
        _gh_path = settings.paths.raw_guardian_headlines
        if _gh_path.exists() and _gh_path.stat().st_size > 40:
            _gh_df = pd.read_csv(_gh_path, encoding="utf-8-sig").fillna("")
            _guardian_snapshot = _gh_df.head(24).to_dict("records")
            if _guardian_snapshot:
                _guardian_snapshot_date = str(_guardian_snapshot[0].get("published_at", ""))[:10]
        else:
            logger.warning(
                "  guardian_headlines.csv ausente: el bloque de noticias dependera "
                "solo del fetch en vivo. Corre scripts/fetch_guardian.py."
            )
    except Exception as _ge:
        logger.warning(f"  Guardian snapshot load failed: {_ge}")
    guardian_snapshot_json = json.dumps(_guardian_snapshot, cls=_NumpyEncoder, ensure_ascii=False)

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

    # KPI strip — una tarjeta por categoría.
    # 'SIN DATOS' se calcula en resumen_categorias pero no se pintaba: si algún
    # sector caía ahí, las tarjetas sumaban menos que el total de sectores sin
    # ninguna explicación. Ahora se muestra, pero solo cuando hay alguno, para
    # no dejar una tarjeta en cero permanente en el caso normal.
    _KPI_CATS = [
        ("PRIORITARIA", "Prioritaria", "#00d4aa"),
        ("ENTRADA",     "Entrada",     "#2ecc71"),
        ("PILOTO",      "Piloto",      "#f1c40f"),
        ("ESPERAR",     "Esperar",     "#e67e22"),
        ("NO ENTRAR",   "No entrar",   "#e05c5c"),
    ]
    if _sector_resumen.get("SIN DATOS", 0) > 0:
        _KPI_CATS.append(("SIN DATOS", "Sin datos", "#8b949e"))
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
        # El "racional" se omite en el producto: es texto largo por fila.
        # Sigue disponible en el payload sector_json para documentación.
        _table_rows_html += (
            f'<tr style="border-bottom:1px solid var(--border)" data-sid="{r["sector_id"]}">'
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
            f'</tr>'
        )

    # El mapa por estado se alimenta del payload blackmarble_map_json (arriba);
    # ya no se carga el geojson aparte para Leaflet.
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
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script>
// Chart.js y d3 vienen de CDN. Si no cargan —sin red, CDN bloqueado por una
// extension o por la red corporativa— los canvas quedaban en blanco y el
// dashboard parecia roto sin decir por que. Esto lo declara explicitamente.
window.addEventListener('DOMContentLoaded', function() {{
  var faltan = [];
  if (typeof Chart === 'undefined') faltan.push('Chart.js');
  if (typeof d3    === 'undefined') faltan.push('d3');
  if (!faltan.length) return;
  var aviso = document.createElement('div');
  aviso.style.cssText = 'position:sticky;top:0;z-index:999;background:#3a1d1d;'
    + 'border-bottom:1px solid #e05c5c;color:#f5c6c6;padding:12px 20px;'
    + 'font-size:.8rem;line-height:1.5;font-family:Inter,sans-serif';
  aviso.innerHTML = '<strong>Los graficos no se pudieron cargar.</strong> '
    + 'No se alcanzo el CDN de ' + faltan.join(' y ') + ' (cdn.jsdelivr.net). '
    + 'Revisa la conexion, un bloqueador de anuncios o el filtrado de tu red. '
    + 'Las cifras y tablas de esta pagina siguen siendo validas.';
  document.body.insertBefore(aviso, document.body.firstChild);
}});
</script>
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

/* ── Diseño minimalista: héroe, KPIs y bloques de la vista de producto ── */
.lead{{font-size:.9rem;color:var(--muted);line-height:1.6;max-width:640px;margin:0 0 22px}}
.hero-grid{{display:grid;grid-template-columns:1.25fr 1fr;gap:16px;margin-bottom:22px}}
.hero-card{{background:var(--card);border:1px solid var(--border);border-radius:16px;
            padding:30px 32px;position:relative;overflow:hidden}}
.hero-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;
                    background:var(--accent);opacity:.9}}
.hero-card.is-annual::before{{background:#f1c40f}}
.hero-tag{{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1.1px;
           color:var(--muted);margin-bottom:14px}}
.hero-num{{font-size:4.4rem;font-weight:700;line-height:.92;letter-spacing:-2px;color:var(--text)}}
.hero-card.is-annual .hero-num{{font-size:3.4rem}}
.hero-lbl{{font-size:1rem;font-weight:600;margin-top:10px;color:var(--text)}}
.hero-meta{{font-size:.74rem;color:var(--muted);margin-top:8px}}
.hero-note{{font-size:.72rem;color:var(--muted);margin-top:14px;padding-top:12px;
            border-top:1px solid var(--border);line-height:1.5}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:12px;margin-bottom:22px}}
.kpi{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 18px}}
.kpi-lbl{{font-size:.62rem;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-bottom:8px}}
.kpi-val{{font-size:1.55rem;font-weight:700;color:var(--text);line-height:1}}
.kpi-sub{{font-size:.65rem;color:#6b7280;margin-top:6px}}
.block-title{{font-size:.95rem;font-weight:600;color:var(--text);margin-bottom:4px}}
.block-sub{{font-size:.76rem;color:var(--muted);margin-bottom:16px;line-height:1.5}}
.panel{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:24px 26px;margin-bottom:20px}}
.hint{{font-size:.72rem;color:#6b7280;line-height:1.55;margin-top:12px}}
details.more{{margin-top:14px}}
details.more summary{{cursor:pointer;color:var(--accent);font-size:.74rem;font-weight:600;list-style:none}}
details.more summary::-webkit-details-marker{{display:none}}
details.more summary::before{{content:'ⓘ ';opacity:.8}}
details.more .more-body{{font-size:.73rem;color:var(--muted);line-height:1.7;margin-top:10px}}

/* Sectores. Estas dos rejillas estaban en atributos style= inline, que ningun
   @media alcanza: a 375px la seccion medía 458px y desbordaba la pagina en
   horizontal. Pasan a clases para poder colapsarlas en pantallas estrechas. */
.sector-kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:22px}}
.sector-split{{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:16px;align-items:start}}
.sector-split > *{{min-width:0}}   /* deja que la columna fluida se encoja */

@media(max-width:900px){{
  .charts-grid{{grid-template-columns:1fr}}
  .chart-card.wide{{grid-column:span 1}}
  .section{{padding:24px 20px}}
  .header{{padding:24px 20px}}
  .nav{{padding:0 16px}}
  .hero-grid{{grid-template-columns:1fr}}
  .hero-num{{font-size:3.4rem}}
  .sector-split{{grid-template-columns:minmax(0,1fr)}}
  .sector-kpis{{grid-template-columns:repeat(3,1fr)}}
}}
@media(max-width:560px){{
  .sector-kpis{{grid-template-columns:repeat(2,1fr);gap:8px}}
}}
</style>
</head>
<body>

<!-- NAV plana — una sola fila, sin sub-pestañas -->
<div class="nav-wrap">
  <div class="nav-top">
    <a class="nav-brand" href="#" onclick="event.preventDefault();showSection('hoy')" title="Ir al inicio">ICIV</a>
    <a href="#hoy">Hoy</a>
    <a href="#historia">Historia</a>
    <a href="#mapa">Mapa</a>
    <a href="#noticias">Noticias</a>
    <a href="#sectores">Sectores</a>
    <a href="#laboratorio">Laboratorio</a>
  </div>
</div>

<!-- ===== HOY ===== -->
<section class="section tab-section tab-active" id="hoy">
  <div class="section-header">
    <span class="section-title">Clima de inversión</span>
    <span class="section-sub">Venezuela · actualizado {generated_at}</span>
  </div>

  <p class="lead">
    Dos lecturas del mismo país: la señal mensual se mueve rápido, el índice anual mide el fondo estructural.
    Ninguna cifra viene de fuentes venezolanas.
  </p>

  <div class="hero-grid">
    <div class="hero-card">
      <div class="hero-tag">Señal mensual</div>
      <div class="hero-num" id="inicioPS">—</div>
      <div class="hero-lbl" id="inicioPL">—</div>
      <div class="hero-meta"><span id="inicioPF">—</span> · cobertura <span id="inicioPC">—</span></div>
      <div class="hero-note"><span id="inicioPDW">Cambio vs. mes anterior: <span id="inicioPD">—</span><br></span><span id="inicioPR">—</span></div>
    </div>
    <div class="hero-card is-annual">
      <div class="hero-tag">Índice anual</div>
      <div class="hero-num" id="inicioAS">—</div>
      <div class="hero-lbl" id="inicioAL">—</div>
      <div class="hero-meta" id="inicioAY">—</div>
      <div class="hero-note"><span id="inicioADW">Cambio vs. año anterior: <span id="inicioAD">—</span><br></span><span id="inicioAR">—</span></div>
    </div>
  </div>

  <div class="block-title">Señales del momento</div>
  <div class="block-sub">Precios, producción y contexto global que mueven la aguja.</div>
  <div class="kpi-grid" id="inicioGrid"></div>

  <div id="satvWrap">
    <div class="block-title">Alertas</div>
    <div class="block-sub">Lo que cambió y merece atención.</div>
    <div id="satvAlertas" style="display:flex;flex-direction:column;gap:10px;margin-bottom:22px"></div>
  </div>

  <div class="panel">
    <div class="block-title">Dónde está el problema</div>
    <div class="block-sub">Cada área puntuada de 0 a 100. Más bajo, peor. Se muestra el último dato publicado de cada una ({dim_year_min}–{dim_year_max}).
      <strong>Un 0 significa el peor registro de Venezuela desde 2000, no ausencia de dato.</strong>
      Donde la cobertura es parcial se indica junto a la barra.</div>
    <div class="chart-wrap" style="height:300px"><canvas id="cDimBar"></canvas></div>
  </div>

  <div class="hint">
    La escala va de 0 a 100 y se mide contra la propia historia de Venezuela:
    100 sería su mejor año desde 2000 y 0 el peor. No compara con otros países.
    La cobertura indica cuántos datos ya publicaron las fuentes para ese periodo.
  </div>
</section>

<!-- ===== HISTORIA ===== -->
<section class="section tab-section" id="historia">
  <div class="section-header">
    <span class="section-title">Historia</span>
    <span class="section-sub">2000–{settings.series.end_year}</span>
  </div>

  <p class="lead">
    Veinticinco años en dos gráficos: el arco largo del país y hacia dónde apunta la señal mensual.
  </p>

  <div class="panel">
    <div class="block-title">El arco de 25 años</div>
    <div class="block-sub">Índice anual con las bandas de riesgo de fondo. Los rombos naranjas son años donde aún faltan datos por publicar.</div>
    <div class="chart-wrap" style="height:400px"><canvas id="cHistoria"></canvas></div>
  </div>

  <div class="panel">
    <div class="block-title">Hacia dónde va</div>
    <div class="block-sub">Señal mensual reciente y proyección a seis meses. La franja verde es el margen de error: cuanto más ancha, menos certeza.</div>
    <div class="chart-wrap" style="height:360px"><canvas id="cPulseTrend"></canvas></div>
  </div>
</section>

<!-- ===== MAPA ===== -->
<section class="section tab-section" id="mapa">
  <div class="section-header">
    <span class="section-title">Mapa</span>
    <span class="section-sub">Actividad nocturna por estado · 2014–{settings.series.end_year}</span>
  </div>

  <p class="lead">
    La luz que emite cada estado de noche, medida por satélite de la NASA.
    Más brillo, más actividad económica. Es la única cifra de este proyecto que nadie puede manipular desde Venezuela.
  </p>

  <div class="panel">
    <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">
      <div class="block-title">Venezuela de noche — <span id="bmMapYear">—</span></div>
      <div style="font-size:.72rem;color:var(--muted)">Pulsa Animar para ver el apagón y su recuperación</div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin:16px 0 10px;flex-wrap:wrap">
      <div style="display:inline-flex;border:1px solid var(--border);border-radius:8px;overflow:hidden">
        <button id="bmModeYear" style="background:var(--accent);color:#0d1117;border:0;padding:7px 16px;cursor:pointer;font-size:.76rem;font-weight:600;font-family:inherit">Por año</button>
        <button id="bmModeMonth" style="background:var(--card);color:var(--text);border:0;padding:7px 16px;cursor:pointer;font-size:.76rem;font-family:inherit">Por mes</button>
      </div>
      <input type="range" id="bmMapSlider" min="0" max="0" value="0" step="1" style="flex:1;min-width:180px;accent-color:var(--accent)">
      <button id="bmMapPlay" style="background:var(--card);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:7px 16px;cursor:pointer;font-size:.78rem;font-family:inherit">▶ Animar</button>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start">
      <div style="flex:2 1 440px;min-width:300px">
        <svg id="bmMapSvg" viewBox="0 0 1000 880" preserveAspectRatio="xMidYMid meet"
             style="width:100%;max-height:460px;height:auto;display:block;background:#0d1117;border-radius:10px"></svg>
        <div style="display:flex;align-items:center;gap:8px;margin-top:10px;font-size:.68rem;color:var(--muted)">
          <span>Menos luz</span>
          <span id="bmMapGradient" style="flex:1;height:10px;border-radius:5px;display:block"></span>
          <span>Más luz</span>
          <span id="bmLegMin" style="display:none"></span><span id="bmLegMax" style="display:none"></span>
        </div>
      </div>
      <div style="flex:1 1 240px;min-width:220px">
        <div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-bottom:10px">Estados más activos</div>
        <div id="bmMapRanking" style="font-size:.75rem;line-height:1.5"></div>
      </div>
    </div>
    <div id="bmMapTip" style="font-size:.72rem;color:var(--muted);margin-top:12px;min-height:1.2em"></div>
  </div>
</section>

<!-- ===== NOTICIAS ===== -->
<section class="section tab-section" id="noticias">
  <div class="section-header">
    <span class="section-title">Noticias</span>
    <span class="section-sub">Prensa internacional sobre Venezuela</span>
  </div>

  <p class="lead">
    Lo que se está publicando fuera del país. Solo medios internacionales; ningún medio venezolano entra aquí.
  </p>

  <div class="block-title">Portada internacional</div>
  <div class="block-sub">Titulares recientes de agencias y diarios globales.</div>
  <div class="news-grid" id="intlNewsGrid" style="margin-bottom:32px">
    <div class="news-status">Cargando…</div>
  </div>

  <div style="display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:16px">
    <div>
      <div class="block-title">The Guardian</div>
      <div class="block-sub" style="margin-bottom:0">Cobertura de los últimos 90 días ·
        <span id="newsSource">cargando…</span></div>
    </div>
    <!-- Los chips los construye buildChips() con las secciones que realmente
         devuelve la consulta. Fijarlos aquí garantizaba filtros vacíos. -->
    <div class="news-filter" id="newsFilter" style="margin-bottom:0"></div>
  </div>

  <div class="news-grid" id="newsGrid">
    <div class="news-status" id="newsStatus">
      <div class="news-skeleton" style="height:14px;width:220px;margin:0 auto 8px"></div>
      <div>Cargando noticias…</div>
    </div>
  </div>

  <div style="text-align:center;margin-top:24px">
    <button id="newsLoadMore" style="display:none;background:rgba(0,212,170,.1);border:1px solid var(--accent);
      color:var(--accent);padding:9px 26px;border-radius:20px;cursor:pointer;font-size:.82rem;font-family:inherit">
      Ver más
    </button>
  </div>
</section>

<!-- ===== SECTORES ===== -->
<section class="section tab-section" id="sectores">
  <div class="section-header">
    <span class="section-title">Sectores</span>
    <span class="section-sub">Dónde entrar primero · {_sector_year}</span>
  </div>

  <p class="lead">
    Cada sector reacciona distinto al clima del país. Este es el orden de atractivo hoy, y el riesgo que domina en cada uno.
  </p>

  <div class="sector-kpis">{_kpi_html}</div>

  <div class="sector-split">
    <div class="chart-card" style="padding:0;overflow:hidden">
      <div style="padding:18px 20px;border-bottom:1px solid var(--border)">
        <div class="block-title">Ranking</div>
        <div class="block-sub" style="margin-bottom:0">Ordenado de mayor a menor atractivo.</div>
      </div>
      <div style="overflow-x:auto">
        <table id="sectorTable" style="width:100%;border-collapse:collapse;font-size:.78rem">
          <thead>
            <tr style="background:#21262d;color:var(--muted);text-align:left">
              <th style="padding:9px 14px;font-weight:600">#</th>
              <th style="padding:9px 14px;font-weight:600">Sector</th>
              <th style="padding:9px 14px;font-weight:600;text-align:center">Score</th>
              <th style="padding:9px 14px;font-weight:600">Recomendación</th>
              <th style="padding:9px 14px;font-weight:600">Riesgo principal</th>
            </tr>
          </thead>
          <tbody>{_table_rows_html}</tbody>
        </table>
      </div>
    </div>

    <div class="chart-card">
      <div class="block-title">Comparación</div>
      <div class="block-sub">Score de 0 a 100 por sector.</div>
      <div class="chart-wrap" style="height:400px"><canvas id="cSectorBar"></canvas></div>
    </div>
  </div>
</section>

<!-- ===== LABORATORIO ===== -->
<section class="section tab-section" id="laboratorio">
  <div class="section-header">
    <span class="section-title">Laboratorio</span>
    <span class="section-sub">Simula tus propios escenarios</span>
  </div>

  <p class="lead">
    Mueve cada palanca y mira cómo cambia el índice. Las áreas no pesan igual: mejorar la institucionalidad mueve más la aguja que subir el petróleo.
  </p>

  <div style="display:flex;gap:22px;flex-wrap:wrap">
    <div style="flex:1;min-width:290px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <span style="font-size:.8rem;font-weight:600">Ajusta cada área</span>
        <button id="simReset" style="background:var(--card);border:1px solid var(--border);
          color:var(--muted);padding:5px 14px;border-radius:6px;cursor:pointer;font-size:.74rem;font-family:inherit">
          Volver a {sim_base_year}
        </button>
      </div>
      <div id="simSliders"></div>
      <div style="margin-top:18px;display:flex;gap:8px;flex-wrap:wrap">
        <button class="sim-preset" data-preset="peak"
          style="background:var(--card);border:1px solid var(--border);color:var(--muted);
                 padding:6px 14px;border-radius:6px;cursor:pointer;font-size:.75rem;font-family:inherit">
          El mejor año
        </button>
        <button class="sim-preset" data-preset="min"
          style="background:var(--card);border:1px solid var(--border);color:var(--muted);
                 padding:6px 14px;border-radius:6px;cursor:pointer;font-size:.75rem;font-family:inherit">
          El peor año
        </button>
      </div>
    </div>

    <div style="flex:1;min-width:250px">
      <div class="hero-card" style="text-align:center;margin-bottom:16px">
        <div class="hero-tag">Resultado</div>
        <div id="simScore" class="hero-num" style="font-size:3.6rem">—</div>
        <div id="simCategory" class="hero-lbl">—</div>
        <div id="simAnalog" class="hero-meta">—</div>
      </div>
      <div class="panel" style="margin-bottom:0">
        <div style="font-size:.78rem;font-weight:600;margin-bottom:12px">Cuánto aporta cada área</div>
        <div id="simContribBars"></div>
      </div>
    </div>
  </div>

  <div class="panel" style="margin-top:20px">
    <div class="block-title">Tu escenario frente a la historia</div>
    <div class="block-sub">La línea amarilla es el valor que acabas de simular.</div>
    <div class="chart-wrap" style="height:280px"><canvas id="cSimChart"></canvas></div>
  </div>
</section>

<!-- FOOTER -->
<footer class="footer">
  <a href="#" onclick="event.preventDefault();showSection('hoy')"
     style="color:var(--accent);text-decoration:none;font-weight:600">ICIV</a>
  &nbsp;·&nbsp; Indicador de Clima de Inversión Venezuela
  &nbsp;·&nbsp; Felipe Gómez Espinal · Universidad EIA
  &nbsp;·&nbsp; {generated_at}
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

// ── Diagnóstico por área — último dato publicado de cada una ────────────────
//
// Una dimensión puede valer exactamente 0.00: con normalización Min-Max sobre
// la serie propia de Venezuela, 0 = "el peor registro desde 2000", no "sin
// dato". Ocurrió en 2025 con D3 institucional (CPI, Freedom House y WJP en su
// mínimo histórico a la vez). Dibujada como barra de 0px era indistinguible de
// un hueco de datos, que es exactamente lo contrario de lo que significa.
//
// Solución: barra con ancho mínimo visible, valor numérico impreso al lado y
// cobertura declarada en el tooltip.
const dimYears = {dim_years_js};
const dimCovs  = {dim_covs_js};
const DIM_MIN_BAR = 0.9;   // puntos de escala: ancho mínimo para que un 0 se vea

// Plugin local: escribe el valor real al final de cada barra.
const dimValueLabels = {{
  id: 'dimValueLabels',
  afterDatasetsDraw(chart) {{
    const {{ ctx }} = chart;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.font = '600 11px Inter, sans-serif';
    ctx.textBaseline = 'middle';
    meta.data.forEach((bar, i) => {{
      const v   = radarVals[i];
      const cov = dimCovs[i];
      ctx.fillStyle = radarClrs[i];
      ctx.textAlign = 'left';
      let txt = v.toFixed(1);
      // Cobertura parcial: se avisa en la propia barra, no solo en el tooltip.
      if (cov != null && cov < 100) txt += '  (' + cov.toFixed(0) + '% cob.)';
      ctx.fillText(txt, bar.x + 6, bar.y);
    }});
    ctx.restore();
  }}
}};

new Chart(document.getElementById('cDimBar'), {{
  type: 'bar',
  data: {{
    labels: dimLbls,
    datasets: [{{
      label: 'Puntaje',
      // El valor dibujado nunca baja de DIM_MIN_BAR para que un 0 real siga
      // siendo visible. El número impreso y el tooltip usan el valor exacto.
      data: radarVals.map(v => Math.max(v, DIM_MIN_BAR)),
      backgroundColor: radarClrs.map(c => c + '99'),
      borderColor: radarClrs,
      borderWidth: 1,
      borderRadius: 4,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true, maintainAspectRatio: false,
    layout: {{ padding: {{ right: 96 }} }},   // espacio para las etiquetas de valor
    plugins: {{
      legend:{{ display:false }},
      tooltip:{{ callbacks:{{
        label: c => radarVals[c.dataIndex].toFixed(1) + ' / 100  ·  dato de '
                    + (dimYears[c.dataIndex] ?? '—'),
        afterLabel: c => {{
          const cov = dimCovs[c.dataIndex];
          if (cov == null) return '';
          return cov >= 100
            ? 'Cobertura: todas las variables del área publicaron.'
            : 'Cobertura: ' + cov.toFixed(0) + '% del peso del área. '
              + 'El resto de sus variables aún no publica para ese año.';
        }}
      }}}}
    }},
    scales: {{
      x: {{ min:0, max:100, grid:{{color:'#21262d'}} }},
      y: {{ grid:{{display:false}}, ticks:{{font:{{size:10}}}} }}
    }}
  }},
  plugins: [dimValueLabels]
}});

// ── Navegación plana (SPA) ───────────────────────────────────────────────────
// Una sola fila de pestañas: cada enlace apunta directo a su sección.

const navLinks    = document.querySelectorAll('.nav-top a[href^="#"]');
const tabSections = document.querySelectorAll('.tab-section');
const SECTIONS    = ['hoy','historia','mapa','noticias','sectores','laboratorio'];

const _tabInits = {{}};   // id → fn — se llena de forma perezosa desde cada IIFE

function showSection(targetId) {{
  if (SECTIONS.indexOf(targetId) === -1) targetId = 'hoy';

  tabSections.forEach(s => s.classList.remove('tab-active'));
  const section = document.getElementById(targetId);
  if (section) {{
    section.classList.add('tab-active');
    window.dispatchEvent(new Event('resize'));
  }}

  navLinks.forEach(a => a.classList.toggle(
    'nav-top-active', a.getAttribute('href') === '#' + targetId));

  if (_tabInits[targetId]) {{
    var _fn = _tabInits[targetId];
    _tabInits[targetId] = null;   // run-once: evita re-crear Chart.js sobre el mismo canvas
    setTimeout(_fn, 60);
  }}
}}

navLinks.forEach(link => {{
  link.addEventListener('click', e => {{
    e.preventDefault();
    const targetId = link.getAttribute('href').slice(1);
    showSection(targetId);
    history.pushState(null, '', '#' + targetId);
  }});
}});

window.addEventListener('popstate', () => showSection(location.hash.slice(1) || 'hoy'));

(function() {{ showSection(location.hash.slice(1) || 'hoy'); }})();

// ── SATV ──────────────────────────────────────────────────────────────────────
(function() {{
  const SATV = {satv_json};
  if (!SATV || !SATV.resumen) return;

  const NIV_COLOR = {{ critico:'#e05c5c', precaucion:'#e67e22', normal:'#2ecc71' }};

  // ── Alertas activas — único bloque SATV visible en el producto ──────────────
  const alertasEl = document.getElementById('satvAlertas');
  if (!alertasEl) return;
  if (!SATV.alertas_activas || SATV.alertas_activas.length === 0) {{
    alertasEl.innerHTML = '<div class="satv-alert normal"><div class="satv-alert-msg">Sin alertas activas este mes.</div></div>';
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
}})();

// ── Guardian News ─────────────────────────────────────────────────────────────
(function() {{
  const INTL_NEWS = {intl_news_json};
  // Snapshot generado por scripts/fetch_guardian.py en la última corrida del
  // pipeline. Se pinta de inmediato: el bloque nunca queda vacío ni muestra un
  // error de red en crudo. El fetch en vivo, si prospera, lo reemplaza.
  const GUARDIAN_SNAPSHOT = {guardian_snapshot_json};
  const SNAPSHOT_DATE     = '{_guardian_snapshot_date}';
  const GUARDIAN_KEY = '{guardian_key}';
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

  // Normaliza un artículo del snapshot (formato CSV) al formato de la API,
  // para que renderCard() no tenga que distinguir de dónde vino.
  function fromSnapshot(a) {{
    return {{
      webTitle:           a.title,
      webUrl:             a.url,
      webPublicationDate: a.published_at,
      sectionId:          a.section_id,
      sectionName:        a.section_name,
      fields: {{ trailText: a.trail || '', thumbnail: a.thumbnail || '' }},
    }};
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

  // Los chips se construyen a partir de las secciones que REALMENTE trae la
  // consulta. Antes estaban fijos en HTML (Economía/Política/Internacional/
  // Negocios) mientras la consulta iba clavada a `section=world`: todos los
  // artículos volvían con sectionId 'world', así que tres de los cuatro filtros
  // no podían devolver nada y siempre mostraban "no se encontraron artículos".
  function buildChips() {{
    const cont = document.getElementById('newsFilter');
    if (!cont) return;
    const counts = new Map();
    allArticles.forEach(a => {{
      const id = a.sectionId || 'other';
      if (!counts.has(id)) counts.set(id, {{ name: a.sectionName || id, n: 0 }});
      counts.get(id).n++;
    }});
    const secciones = [...counts.entries()]
      .sort((x, y) => y[1].n - x[1].n)
      .filter(([, v]) => v.n > 0);

    cont.innerHTML =
      `<span class="news-chip${{activeTag === 'all' ? ' active' : ''}}" data-tag="all">`
      + `Todas (${{allArticles.length}})</span>`
      + secciones.map(([id, v]) =>
          `<span class="news-chip${{activeTag === id ? ' active' : ''}}" data-tag="${{id}}">`
          + `${{v.name}} (${{v.n}})</span>`).join('');
  }}

  function applyFilter() {{
    filtered = activeTag === 'all'
      ? allArticles
      : allArticles.filter(a => (a.sectionId || 'other') === activeTag);
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

  function setNewsSource(txt) {{
    const el = document.getElementById('newsSource');
    if (el) el.textContent = txt;
  }}

  async function loadNews() {{
    renderIntlNews();
    const grid = document.getElementById('newsGrid');

    // 1) Snapshot primero — el bloque queda utilizable de inmediato y sin red.
    if (GUARDIAN_SNAPSHOT.length) {{
      allArticles = GUARDIAN_SNAPSHOT.map(fromSnapshot);
      buildChips();
      applyFilter();
      setNewsSource('Snapshot del pipeline' + (SNAPSHOT_DATE ? ' · último titular ' + SNAPSHOT_DATE : ''));
    }}

    // 2) Fetch en vivo como mejora. Sin key incrustada no se intenta siquiera.
    if (!GUARDIAN_KEY) {{
      if (!GUARDIAN_SNAPSHOT.length) {{
        grid.innerHTML = `<div class="news-status">No hay titulares disponibles.
          Corre <code>scripts/fetch_guardian.py</code> para generar el snapshot.<br>
          <a href="https://www.theguardian.com/world/venezuela" target="_blank" rel="noopener"
             style="color:var(--accent)">Ver en The Guardian →</a></div>`;
      }}
      return;
    }}

    // Sin `section=world`: esa restricción dejaba fuera us-news, opinión,
    // medio ambiente y global-development, que son parte real de la cobertura.
    const url  = `https://content.guardianapis.com/search`
               + `?tag=world/venezuela`
               + `&api-key=${{GUARDIAN_KEY}}`
               + `&order-by=newest&page-size=50`
               + `&show-fields=trailText,thumbnail`
               + `&from-date=${{fromDate()}}`;
    try {{
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${{resp.status}}`);
      const data = await resp.json();
      const live = data.response?.results || [];
      if (live.length === 0) throw new Error('sin resultados');
      allArticles = live;
      activeTag = 'all';
      buildChips();
      applyFilter();
      setNewsSource('En vivo desde The Guardian · últimos 90 días');
    }} catch(err) {{
      // Caída del fetch en vivo: NO se borra lo ya pintado. El snapshot se
      // queda y solo se avisa que no pudo refrescarse.
      if (GUARDIAN_SNAPSHOT.length) {{
        setNewsSource('Snapshot del pipeline'
          + (SNAPSHOT_DATE ? ' · último titular ' + SNAPSHOT_DATE : '')
          + ' — no se pudo refrescar en vivo (' + err.message + ')');
      }} else {{
        grid.innerHTML = `<div class="news-status">No se pudo cargar noticias: ${{err.message}}<br>
          <a href="https://www.theguardian.com/world/venezuela" target="_blank" rel="noopener"
             style="color:var(--accent)">Ver en The Guardian →</a></div>`;
      }}
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

// ── MAPA POR ESTADO — init del coroplético NASA Black Marble ───────────────
// El mapa Leaflet de la serie Li et al. se retiró (2026-07-29): extraía la
// luminosidad por BBOX rectangular (mediana 2x el área real del estado, 56
// pares de bboxes solapados) y normalizaba cada estado contra su propio máximo,
// lo que no es comparable entre estados. El mapa Black Marble usa máscara
// poligonal exacta y radiancia absoluta. La serie NACIONAL de Li et al. sigue
// alimentando el score anual (cubre 2000-2013, previo a VIIRS).
(function() {{
  function initMapTab() {{
    setTimeout(function() {{ if (window.__buildBMMap) window.__buildBMMap(); }}, 60);
  }}
  if (typeof _tabInits !== 'undefined') {{
    _tabInits['mapa'] = initMapTab;
  }}
  document.querySelectorAll('[href="#mapa"]').forEach(function(el) {{
    el.addEventListener('click', initMapTab);
  }});
  if (window.location.hash === '#mapa') setTimeout(initMapTab, 200);
}})();

// ── LABORATORIO — simulador interactivo ────────────────────────────────────────
(function() {{
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
          .replace('Capital Humano e Infraestructura Social','Cap. Humano')
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
            .replace('Capital Humano e Infraestructura Social','Capital Humano')
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
    // preset: 'peak' (mejor año histórico), 'min' (peor año), 'current' (reset)
    SIM_DIMS.forEach(d => {{
      let val;
      if (preset === 'peak') {{
        // Usar max histórico de cada dimensión
        val = d.max_hist;
      }} else if (preset === 'min') {{
        // Usar el año con ICIV más bajo — buscar valores de ese año
        const minIdx = SIM_HIST.indexOf(Math.min(...SIM_HIST));
        val = d.hist[minIdx] !== null ? d.hist[minIdx] : d.current;
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
    document.getElementById('simReset')?.addEventListener('click', () => setPreset('current'));
    document.querySelectorAll('.sim-preset').forEach(btn => {{
      btn.addEventListener('click', () => setPreset(btn.dataset.preset));
    }});
  }}

  // El laboratorio se arma al abrir la pestaña: así el canvas ya tiene tamaño real.
  var simReady = false;
  function initOnce() {{ if (!simReady) {{ simReady = true; initSimulator(); }} }}
  if (typeof _tabInits !== 'undefined') {{
    _tabInits['laboratorio'] = initOnce;
  }}
  if (window.location.hash === '#laboratorio') initOnce();
}})();

// ── Correlación y Sanciones — renderizadas server-side (matplotlib / HTML) ──

// ── [INDICADORES LÍDERES y COMPARACIÓN REGIONAL eliminados] ─────────────────

// ── RADAR SECTORIAL — gráficos creados al cargar, resize al activar tab ─────
(function() {{
  var SR = {sector_json};
  if (!SR || !SR.ranking || !SR.ranking.length) return;

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

  // ── Tab activation: solo resize (charts ya existen) ───────────────────────
  if (typeof _tabInits !== 'undefined') {{
    _tabInits['sectores'] = function() {{ if (barChart) barChart.resize(); }};
  }}
}})();
// ── [INDICADORES LÍDERES y COMPARACIÓN REGIONAL eliminados] ─────────────────

// ── MAPA NOCTURNO POR ESTADO (NASA Black Marble) ────────────────────────────
(function() {{
  var BMMAP = {blackmarble_map_json};

  function _bmColor(v) {{
    var vmin = BMMAP.vmin || 0.01, vmax = BMMAP.vmax || 1;
    if (v == null || !isFinite(v)) return '#161b22';
    var lv = Math.log(Math.max(v, vmin)), l0 = Math.log(vmin), l1 = Math.log(vmax);
    var t = Math.max(0, Math.min(1, (lv - l0) / (l1 - l0 || 1)));
    var stops = [[10,14,24],[45,32,72],[122,52,80],[200,94,52],[240,168,44],[255,243,205]];
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
    var mode = 'year';   // 'year' | 'month'
    function keys() {{ return mode === 'year' ? BMMAP.years.map(String) : BMMAP.months; }}
    function dataFor(k) {{ return (mode === 'year' ? BMMAP.radiance[k] : BMMAP.radiance_m[k]) || {{}}; }}

    BMMAP.estados.forEach(function(e) {{
      var p = document.createElementNS(NS, 'path');
      p.setAttribute('d', e.d);
      p.setAttribute('stroke', '#0d1117');
      p.setAttribute('stroke-width', '0.8');
      p.style.cursor = 'pointer';
      p.addEventListener('mousemove', function() {{
        var k = keys()[+document.getElementById('bmMapSlider').value];
        var v = dataFor(k)[e.cod];
        document.getElementById('bmMapTip').textContent =
          e.nombre + ' · ' + (v != null ? v.toFixed(3) + ' nW/cm²/sr' : 'sin dato') + ' (' + k + ')';
      }});
      p.addEventListener('mouseleave', function() {{
        document.getElementById('bmMapTip').textContent = '';
      }});
      svg.appendChild(p);
      paths[e.cod] = p;
    }});

    // leyenda: gradiente log + etiquetas numéricas reales
    var grad = document.getElementById('bmMapGradient');
    if (grad) {{
      var css = [];
      var l0 = Math.log(BMMAP.vmin), l1 = Math.log(BMMAP.vmax);
      for (var s = 0; s <= 12; s++) css.push(_bmColor(Math.exp(l0 + (l1-l0)*s/12)));
      grad.style.background = 'linear-gradient(90deg,' + css.join(',') + ')';
      document.getElementById('bmLegMin').textContent = BMMAP.vmin.toFixed(2);
      document.getElementById('bmLegMax').textContent = BMMAP.vmax.toFixed(1) + ' nW/cm²/sr';
    }}

    function render(idx) {{
      var ks = keys();
      idx = Math.max(0, Math.min(ks.length - 1, idx));
      var k = ks[idx];
      var rad = dataFor(k);
      BMMAP.estados.forEach(function(e) {{
        paths[e.cod].setAttribute('fill', _bmColor(rad[e.cod]));
      }});
      document.getElementById('bmMapYear').textContent = k;
      var ranked = BMMAP.estados.map(function(e){{return {{n:e.nombre, v:rad[e.cod]}}}})
                    .filter(function(x){{return x.v!=null}}).sort(function(a,b){{return b.v-a.v}}).slice(0,8);
      var l0 = Math.log(BMMAP.vmin), l1 = Math.log(BMMAP.vmax);
      document.getElementById('bmMapRanking').innerHTML = ranked.map(function(x){{
        var t = (Math.log(Math.max(x.v, BMMAP.vmin)) - l0) / (l1 - l0 || 1);
        var w = Math.max(4, Math.min(100, t * 100));
        return '<div style="display:flex;align-items:center;gap:6px;margin:2px 0">' +
          '<span style="width:104px;color:#c9d1d9;font-size:.72rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+x.n+'</span>' +
          '<span style="flex:1;background:#161b22;border-radius:3px"><span style="display:block;height:9px;border-radius:3px;width:'+w+'%;background:'+_bmColor(x.v)+'"></span></span>' +
          '<span style="width:42px;text-align:right;color:#8b949e;font-size:.72rem">'+x.v.toFixed(2)+'</span></div>';
      }}).join('');
    }}

    var slider = document.getElementById('bmMapSlider');
    var playBtn = document.getElementById('bmMapPlay');
    var timer = null;
    function stopAnim() {{
      if (timer) {{ clearInterval(timer); timer = null; playBtn.textContent = '▶ Animar'; }}
    }}
    function setMode(m) {{
      stopAnim();
      mode = m;
      var ks = keys();
      slider.max = ks.length - 1;
      slider.value = ks.length - 1;
      var bY = document.getElementById('bmModeYear'), bM = document.getElementById('bmModeMonth');
      var on = 'var(--accent)', onTxt = '#0d1117', off = 'var(--card)', offTxt = 'var(--text)';
      bY.style.background = m === 'year' ? on : off;
      bY.style.color      = m === 'year' ? onTxt : offTxt;
      bY.style.fontWeight = m === 'year' ? '600' : '400';
      bM.style.background = m === 'month' ? on : off;
      bM.style.color      = m === 'month' ? onTxt : offTxt;
      bM.style.fontWeight = m === 'month' ? '600' : '400';
      render(ks.length - 1);
    }}
    slider.addEventListener('input', function() {{ stopAnim(); render(+slider.value); }});
    document.getElementById('bmModeYear').addEventListener('click', function() {{ setMode('year'); }});
    document.getElementById('bmModeMonth').addEventListener('click', function() {{ setMode('month'); }});
    setMode('year');

    playBtn.addEventListener('click', function() {{
      if (timer) {{ stopAnim(); return; }}
      playBtn.textContent = '⏸ Pausar';
      var ks = keys();
      var i = 0;
      var step = mode === 'month' ? 180 : 700;   // mensual más rápido: 149 cuadros
      timer = setInterval(function() {{
        slider.value = i; render(i); i++;
        if (i >= ks.length) stopAnim();
      }}, step);
    }});
  }}

  // El mapa Black Marble vive en la pestaña "Actividad por Estado" (#mapa);
  // se expone para que ese tab lo construya al activarse.
  window.__buildBMMap = buildBlackMarbleMap;

}})();

// ── PROYECCIÓN A 6 MESES (se dibuja dentro de Historia) ──────────────────────────────────────────
(function() {{
  var ML = {ml_forecast_json};
  var PULSE = {pulse_json};
  if (!ML || (!ML.sarima && !ML.nowcast)) return;

  // Forecast chart
  function buildForecastChart() {{
    var ctx = document.getElementById('cPulseTrend');
    if (!ctx) return;
    if (typeof Chart !== 'undefined' && Chart.getChart && Chart.getChart(ctx)) return;
    if (!ML.sarima || !ML.sarima.fecha || !ML.sarima.fecha.length) return;

    // Datos históricos del Pulse — SOLO últimos 30 meses para que el forecast sea visible
    var N_HIST = 60;  // ventana visible: 5 años de historia + 6 meses de proyección
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
    _tabInits['historia'] = buildForecastChart;
  }}
  if (window.location.hash === '#historia') {{
    buildForecastChart();
  }}
}})();

// ─────────────────────────────────────────────────────────────────────────────
// HOY — dos cifras protagonistas + señales del momento
// ─────────────────────────────────────────────────────────────────────────────
(function() {{
  var VH = {ven_hoy_json};
  if (!VH) return;

  var MESES = ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];

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
    if (score > 65) return 'Riesgo muy bajo';
    if (score > 50) return 'Riesgo bajo';
    if (score > 35) return 'Riesgo moderado';
    if (score > 20) return 'Riesgo alto';
    return 'Riesgo muy alto';
  }}
  function _deltaStr(d, dec, suf) {{
    if (d == null) return '—';
    var flecha = d >= 0 ? '▲ +' : '▼ ';
    return '<span style="color:' + (d >= 0 ? '#2ecc71' : '#e05c5c') + ';font-weight:600">'
           + flecha + Math.abs(d).toFixed(dec) + (suf || '') + '</span>';
  }}
  function _set(id, txt, color) {{
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = txt;
    if (color) el.style.color = color;
  }}

  // ── Señal mensual ──
  if (VH.pulse) {{
    var p = VH.pulse;
    var pColor = p.is_reliable ? _col(p.score) : '#e6a817';
    _set('inicioPS', p.score.toFixed(1), pColor);
    _set('inicioPL', p.is_reliable ? _lbl(p.score) : 'Lectura provisional', pColor);
    _set('inicioPF', (p.label_mes || '') + ' ' + (p.year || ''));
    _set('inicioPC', p.coverage != null ? p.coverage + '%' : '—');
    // Mismo criterio que el índice anual: el delta de un mes provisional
    // compara coberturas distintas (el mes en curso contra el último mes
    // completo), así que no mide variación real. Se suprime.
    var elPDW = document.getElementById('inicioPDW');
    if (p.is_reliable) {{
      var elPD = document.getElementById('inicioPD');
      if (elPD) elPD.innerHTML = _deltaStr(p.delta, 1, ' pts');
      _set('inicioPR', 'Todas las fuentes del mes ya publicaron.');
    }} else {{
      if (elPDW) elPDW.style.display = 'none';
      _set('inicioPR',
        'Lectura provisional: faltan fuentes por publicar, no comparable con el mes previo. ' +
        'Último mes completo: ' + p.reliable_label_mes + ' ' + p.reliable_year +
        ' con ' + p.reliable_score.toFixed(1) + '.');
    }}
  }}

  // ── Índice anual ──
  //
  // La tarjeta encabeza SIEMPRE con el año en curso, aunque su cobertura sea
  // parcial — igual que la señal mensual encabeza con el mes en curso.
  //
  // Lo que sí se suprime es el DELTA interanual mientras el año sea provisional.
  // Motivo: cuando faltan dimensiones, el agregador redistribuye sus pesos entre
  // las presentes, y en Venezuela las que publican tarde (D3 institucional,
  // D5 capital humano) son justamente las de peor puntaje. Eso hace que el score
  // provisional SUBA por calendario y no por país, así que un "+17,1 pts" contra
  // un año con 83,8% de cobertura no mide ningún cambio real. En su lugar se
  // declara la cobertura y el score del último año completo, como referencia.
  if (VH.iciv) {{
    var ic = VH.iciv;
    var icColor = ic.color || _col(ic.score);
    _set('inicioAS', ic.score.toFixed(1), icColor);
    _set('inicioAL', ic.is_reliable ? _lbl(ic.score) : 'Lectura provisional', icColor);
    _set('inicioAY', ic.year + ' · cobertura ' + (ic.coverage != null ? ic.coverage + '%' : '—'));

    var elADW = document.getElementById('inicioADW');
    if (ic.is_reliable) {{
      var elAD = document.getElementById('inicioAD');
      if (elAD) elAD.innerHTML = _deltaStr(ic.delta, 1, ' pts');
      _set('inicioAR', 'Todas las fuentes del año ya publicaron.');
    }} else {{
      if (elADW) elADW.style.display = 'none';
      _set('inicioAR',
        'Lectura provisional: faltan fuentes por publicar, no comparable con el año ' +
        'previo. Las que aún no salen son las de peor puntaje, así que este número ' +
        'tiende a bajar al cerrar el año. Último año completo: ' + ic.reliable_year +
        ' con ' + ic.reliable_score.toFixed(1) + '.');
    }}
  }}

  // ── Señales del momento ──
  // Cada tarjeta declara que mide EXACTAMENTE, no un apodo. Las etiquetas
  // anteriores ("Diáspora", "Nervios global", "Inflación") no permitían saber
  // que había detrás del número; "Diáspora · personas fuera" era ademas
  // incorrecta: UNHCR coo=VEN cuenta refugiados y solicitantes de asilo
  // REGISTRADOS (~1,6 M), no los ~7,9 M de la diaspora total segun R4V/OIM.
  // `nota` se muestra como tooltip; `proy` marca las series que son proyeccion.
  var ICARDS = [
    {{ key:'wti',          label:'Petróleo WTI',
       fmt:function(v){{return '$' + v.toFixed(1)}},        unit:'USD por barril',
       nota:'West Texas Intermediate, precio spot mensual (FRED).' }},
    {{ key:'petroleo_ven', label:'Producción petrolera',
       fmt:function(v){{return (v/1000).toFixed(2) + 'M'}}, unit:'barriles/día (EIA)',
       nota:'Crudo incl. condensado de arrendamiento. EIA International, producto 57.' }},
    {{ key:'inflacion',    label:'Inflación (deflactor PIB)',
       fmt:function(v){{return v.toFixed(0) + '%'}},        unit:'anual · FMI', proy:true,
       nota:'Deflactor del PIB, no IPC. El dato del año en curso es proyección del World Economic Outlook, no inflación observada.' }},
    {{ key:'migrantes',    label:'Refugiados y asilo',
       fmt:function(v){{return v.toFixed(1) + 'M'}},        unit:'registrados ante ACNUR',
       nota:'UNHCR coo=VEN: refugiados + solicitantes de asilo registrados. NO es la diáspora total, estimada en ~7,9 M por R4V/OIM, que incluye migrantes sin registro.' }},
    {{ key:'fh',           label:'Libertades civiles y políticas',
       fmt:function(v){{return v.toFixed(0) + '/100'}},     unit:'Freedom House',
       nota:'Freedom in the World, puntaje agregado 0-100. Más alto, más libertades.' }},
    {{ key:'vix',          label:'Volatilidad de mercados',
       fmt:function(v){{return v.toFixed(1)}},              unit:'índice VIX · global',
       nota:'CBOE VIX: aversión al riesgo en mercados globales. No es un indicador de Venezuela.' }},
  ];
  var igrid = document.getElementById('inicioGrid');
  if (igrid) {{
    igrid.innerHTML = ICARDS.map(function(c) {{
      var d = VH[c.key];
      if (!d) return '';
      var fecha = d.mes ? (MESES[d.mes] + ' ' + d.año) : String(d.año);
      // Una serie anual cuyo último dato es el año en curso todavía no ocurrió:
      // se marca como proyección en vez de presentarse como observación.
      var esProy = !!c.proy && !d.mes && d.año >= {current_year_val};
      var sub    = c.unit + ' · ' + (esProy ? 'proyección ' : '') + fecha;
      return '<div class="kpi" title="' + c.nota.replace(/"/g,'&quot;') + '">'
           + '<div class="kpi-lbl">' + c.label + '</div>'
           + '<div class="kpi-val">' + c.fmt(d.valor)
           + (esProy ? '<span style="font-size:.75rem;color:var(--muted);font-weight:400"> proy.</span>' : '')
           + '</div>'
           + '<div class="kpi-sub">' + sub + '</div>'
           + '</div>';
    }}).join('');
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
