"""
Pipeline completo del ICIV: carga → limpieza → imputación → normalización → índice.

Lee los CSVs de data/raw/, procesa todas las fuentes y escribe dos archivos en
data/processed/:
  - iciv_normalizado.csv   variables normalizadas 0-100 por año
  - iciv_scores.csv        puntajes por dimensión + ICIV final + categoría de riesgo

Uso:
    python scripts/run_pipeline.py
"""

from __future__ import annotations

import sys
import logging
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import Settings
from iciv.data.loaders import ALL_LOADERS
from iciv.data.catalog import CATALOG
from iciv.processing.pipeline import Pipeline
from iciv.processing.transformers.cleaner import DataCleaner
from iciv.processing.transformers.imputer import GapImputer
from iciv.processing.transformers.normalizer import MinMaxNormalizer
from iciv.index.aggregator import ICIVAggregator

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def load_all_sources(settings: Settings) -> pd.DataFrame:
    """
    Carga todas las fuentes disponibles y las une en un DataFrame maestro.

    Las fuentes con archivos faltantes se omiten con un aviso; el pipeline
    continúa con las que sí están disponibles.

    Returns:
        DataFrame con columna 'año' y una columna por cada variable cargada.
    """
    years = list(range(settings.series.start_year, settings.series.end_year + 1))
    master = pd.DataFrame({"año": years})

    for loader_cls in ALL_LOADERS:
        loader = loader_cls(settings=settings)
        source_name = loader.get_source_id().value

        try:
            result = loader.load_validated()
        except FileNotFoundError as exc:
            logger.warning("  [OMITIDA] %s — %s", source_name, exc.args[0].split("\n")[0])
            continue
        except Exception as exc:
            logger.warning("  [ERROR]   %s — %s", source_name, exc)
            continue

        # Unir al maestro por año (left join para mantener todos los años)
        cols_to_merge = [c for c in result.df.columns if c != "año"]
        master = master.merge(result.df[["año"] + cols_to_merge], on="año", how="left")

    return master


def run() -> None:
    settings = Settings()
    settings.paths.ensure_exists()

    logger.info("=" * 60)
    logger.info("ICIV Pipeline — Venezuela %s-%s",
                settings.series.start_year, settings.series.end_year)
    logger.info("=" * 60)

    # ── 1. Carga ──────────────────────────────────────────────────────────────
    logger.info("\n[1/4] Cargando fuentes ...")
    df_raw = load_all_sources(settings)
    logger.info("  Maestro: %d años × %d variables", len(df_raw), len(df_raw.columns) - 1)

    if df_raw.shape[1] == 1:
        logger.error("No se encontró ningún archivo en data/raw/. "
                     "Ejecuta primero los scripts fetch_*.py.")
        sys.exit(1)

    # ── 2. Limpieza e imputación ──────────────────────────────────────────────
    logger.info("\n[2/4] Limpieza e imputación ...")
    pipeline = Pipeline([
        ("clean",   DataCleaner(
            start_year=settings.series.start_year,
            end_year=settings.series.end_year,
        )),
        ("impute",  GapImputer(default_strategy="interpolate", limit=4)),
        ("normalize", MinMaxNormalizer()),
    ])

    df_normalizado = pipeline.fit_transform(df_raw)

    # Mostrar resumen de imputaciones
    imputer: GapImputer = pipeline.get_step("impute")  # type: ignore[assignment]
    if imputer.imputation_log_:
        logger.info("  Imputaciones realizadas:")
        for col, n in sorted(imputer.imputation_log_.items(), key=lambda x: -x[1]):
            logger.info("    %-40s %d valores", col, n)

    # ── 3. Guardar normalizado ────────────────────────────────────────────────
    logger.info("\n[3/4] Guardando variables normalizadas ...")
    out_norm = settings.paths.data_processed / "iciv_normalizado.csv"

    # Mantener solo columnas del catálogo + año
    catalog_cols = list(CATALOG.keys())
    available_cols = ["año"] + [c for c in catalog_cols if c in df_normalizado.columns]
    df_normalizado[available_cols].to_csv(out_norm, index=False, encoding="utf-8-sig")
    logger.info("  Guardado: %s", out_norm.relative_to(settings.paths.root))

    # ── 4. Calcular y guardar índice ──────────────────────────────────────────
    logger.info("\n[4/4] Calculando índice ICIV (%s) ...", settings.aggregation.method)
    aggregator = ICIVAggregator(method=settings.aggregation.method)  # type: ignore[arg-type]
    df_scores = aggregator.compute(df_normalizado[available_cols])

    out_scores = settings.paths.data_processed / "iciv_scores.csv"
    df_scores.to_csv(out_scores, index=False, encoding="utf-8-sig")
    logger.info("  Guardado: %s", out_scores.relative_to(settings.paths.root))

    # ── Resumen final ─────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN ICIV %s-%s",
                settings.series.start_year, settings.series.end_year)
    logger.info("=" * 60)
    logger.info("%-6s  %-6s  %s", "Año", "ICIV", "Categoría")
    logger.info("-" * 50)
    for _, row in df_scores.dropna(subset=["iciv_score"]).iterrows():
        logger.info("%-6d  %-6.1f  %s",
                    int(row["año"]), row["iciv_score"], row["iciv_categoria"])

    valid = df_scores["iciv_score"].dropna()
    if not valid.empty:
        logger.info("-" * 50)
        logger.info("Promedio: %.1f  |  Mín: %.1f (%d)  |  Máx: %.1f (%d)",
                    valid.mean(),
                    valid.min(), int(df_scores.loc[valid.idxmin(), "año"]),
                    valid.max(), int(df_scores.loc[valid.idxmax(), "año"]))

    logger.info("\nArchivos generados en data/processed/:")
    logger.info("  iciv_normalizado.csv — variables normalizadas 0-100")
    logger.info("  iciv_scores.csv      — puntajes por dimensión + ICIV + categoría")


if __name__ == "__main__":
    run()
