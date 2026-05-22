"""
Descarga y extrae luminosidad nocturna para Venezuela.

Fuente: Li et al. (2020, actualizado 2024) — "Harmonization of DMSP and VIIRS
        nighttime light data from 1992 to 2024 at the global scale"
        Figshare DOI: 10.6084/m9.figshare.9828827.v10

Acceso: PUBLICO, sin autenticacion. Descarga directa via Figshare.
        No requiere NASA Earthdata, ni cuenta, ni API key.

Cobertura: 2000-2024 (serie completa para el ICIV)
  - 2000-2013: calDMSP  (DMSP-OLS calibrado)
  - 2014-2024: simVIIRS (VIIRS simulado, escala armonica con DMSP)
  Ambas series en la MISMA escala DN 0-63. Serie continua y comparable.

Metodologia:
  1. Para cada anio descarga el raster GeoTIFF global desde Figshare (~25-40 MB)
  2. Recorta el bounding box de Venezuela continental: [-73.4, 0.6, -59.8, 12.2]
  3. Calcula la media de pixeles con valor > 0 (elimina oceano y nubes)
  4. Guarda el valor real sin modificar en data/raw/viirs.csv

Cita: Li, X., Zhou, Y., Zhao, M., & Gao, X. (2020). A harmonized global nighttime
      light dataset 1992-2020. Scientific Data, 7(1), 168.
      https://doi.org/10.1038/s41597-020-0510-y

Salida: data/raw/viirs.csv
Formato: anio|indicador|valor|pais|fuente

Uso:
    pip install rasterio requests numpy
    python scripts/fetch_viirs.py
"""

from __future__ import annotations

import sys
import time
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

OUTPUT = settings.paths.raw_viirs

# Bounding box Venezuela continental (lon_min, lat_min, lon_max, lat_max)
VEN_BBOX = (-73.4, 0.6, -59.8, 12.2)

# Mapeo anio -> (file_id_figshare, nombre_archivo)
# DOI: 10.6084/m9.figshare.9828827.v10  obtenido via Figshare API publica
FIGSHARE_FILES: dict[int, tuple[int, str]] = {
    2000: (17626085, "Harmonized_DN_NTL_2000_calDMSP.tif"),
    2001: (17626088, "Harmonized_DN_NTL_2001_calDMSP.tif"),
    2002: (17626091, "Harmonized_DN_NTL_2002_calDMSP.tif"),
    2003: (17626094, "Harmonized_DN_NTL_2003_calDMSP.tif"),
    2004: (17626097, "Harmonized_DN_NTL_2004_calDMSP.tif"),
    2005: (17626100, "Harmonized_DN_NTL_2005_calDMSP.tif"),
    2006: (17626103, "Harmonized_DN_NTL_2006_calDMSP.tif"),
    2007: (17626109, "Harmonized_DN_NTL_2007_calDMSP.tif"),
    2008: (17626016, "Harmonized_DN_NTL_2008_calDMSP.tif"),
    2009: (17626019, "Harmonized_DN_NTL_2009_calDMSP.tif"),
    2010: (17626022, "Harmonized_DN_NTL_2010_calDMSP.tif"),
    2011: (17626025, "Harmonized_DN_NTL_2011_calDMSP.tif"),
    2012: (17626031, "Harmonized_DN_NTL_2012_calDMSP.tif"),
    2013: (17626034, "Harmonized_DN_NTL_2013_calDMSP.tif"),
    2014: (57065276, "Harmonized_DN_NTL_2014_simVIIRS.tif"),
    2015: (57065321, "Harmonized_DN_NTL_2015_simVIIRS.tif"),
    2016: (57065291, "Harmonized_DN_NTL_2016_simVIIRS.tif"),
    2017: (57065282, "Harmonized_DN_NTL_2017_simVIIRS.tif"),
    2018: (57065288, "Harmonized_DN_NTL_2018_simVIIRS.tif"),
    2019: (57065285, "Harmonized_DN_NTL_2019_simVIIRS.tif"),
    2020: (57065297, "Harmonized_DN_NTL_2020_simVIIRS.tif"),
    2021: (57065294, "Harmonized_DN_NTL_2021_simVIIRS.tif"),
    2022: (57065303, "Harmonized_DN_NTL_2022_simVIIRS.tif"),
    2023: (57065300, "Harmonized_DN_NTL_2023_simVIIRS.tif"),
    2024: (57065306, "Harmonized_DN_NTL_2024_simVIIRS.tif"),
}


def _extract_venezuela_mean(tif_path: Path) -> float | None:
    """Abre el GeoTIFF y calcula la media DN en el bbox Venezuela."""
    try:
        import rasterio  # type: ignore
        from rasterio.windows import from_bounds  # type: ignore
    except ImportError:
        raise RuntimeError("rasterio no instalado: pip install rasterio")

    lon_min, lat_min, lon_max, lat_max = VEN_BBOX
    with rasterio.open(tif_path) as src:
        window = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)
        data = src.read(1, window=window).astype(float)
        nodata_val = src.nodata if src.nodata is not None else -9999

    valid = data[(data != nodata_val) & (data > 0)]
    if valid.size == 0:
        return None
    return round(float(valid.mean()), 4)


def _download_year(year: int, file_id: int, filename: str) -> float | None:
    """Descarga TIF de Figshare, extrae valor Venezuela, borra el TIF."""
    url = f"https://ndownloader.figshare.com/files/{file_id}"
    tmp_path = Path(tempfile.mktemp(suffix=f"_{year}.tif"))

    try:
        resp = requests.get(url, timeout=360, stream=True)
        resp.raise_for_status()

        size_mb = int(resp.headers.get("content-length", 0)) / 1e6
        print(f"    Descargando ({size_mb:.0f} MB)... ", end="", flush=True)

        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=524288):
                f.write(chunk)

        print("OK — Extrayendo Venezuela... ", end="", flush=True)
        val = _extract_venezuela_mean(tmp_path)

        if val is None:
            print("sin pixeles validos")
        else:
            print(f"mean_DN = {val:.4f}")
        return val

    except requests.exceptions.Timeout:
        print("TIMEOUT")
        return None
    except requests.exceptions.HTTPError as exc:
        print(f"HTTP {exc.response.status_code}")
        return None
    except Exception as exc:
        print(f"ERROR: {exc}")
        return None
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _years_cached(output: Path) -> set[int]:
    """
    Lee el CSV existente y retorna el conjunto de anos ya procesados.
    Si el archivo no existe o esta vacio, retorna conjunto vacio.
    """
    if not output.exists():
        return set()
    try:
        df = pd.read_csv(output, encoding="utf-8-sig")
        col = "año" if "año" in df.columns else ("anio" if "anio" in df.columns else None)
        if col is None or df.empty:
            return set()
        return set(df[col].dropna().astype(int).tolist())
    except Exception:
        return set()


def fetch_viirs(force_refresh: bool = False) -> pd.DataFrame:
    """
    Descarga luminosidad nocturna Venezuela 2000-2024.
    Fuente: Li et al. 2024 via Figshare (publico, sin auth).
    Solo retorna filas con datos reales. Sin valores inventados.

    Cache inteligente: si viirs.csv ya existe, solo descarga los anos
    que faltan. Usa force_refresh=True para forzar re-descarga completa.
    """
    # Cargar datos ya existentes
    cached = _years_cached(OUTPUT)
    all_years = sorted(FIGSHARE_FILES.keys())

    if force_refresh:
        years_to_download = all_years
        existing_rows: list[dict] = []
        print("  [VIIRS] force_refresh=True — re-descargando todos los anos")
    else:
        years_to_download = [y for y in all_years if y not in cached]
        if cached:
            print(f"  [VIIRS cache] {len(cached)} anos ya procesados: "
                  f"{min(cached)}-{max(cached)}")
        if years_to_download:
            print(f"  [VIIRS] Descargando {len(years_to_download)} anos nuevos: "
                  f"{years_to_download}")
        else:
            print("  [VIIRS] Todos los anos ya estan en cache — sin descargas.")

        # Leer filas existentes del CSV
        if cached and OUTPUT.exists():
            try:
                df_existing = pd.read_csv(OUTPUT, encoding="utf-8-sig")
                existing_rows = df_existing.to_dict("records")
            except Exception:
                existing_rows = []
        else:
            existing_rows = []

    rows: list[dict] = list(existing_rows) if not force_refresh else []

    for year in years_to_download:
        file_id, filename = FIGSHARE_FILES[year]
        sensor = "calDMSP" if "calDMSP" in filename else "simVIIRS"
        print(f"\n  [{year}] {sensor}", flush=True)
        val = _download_year(year, file_id, filename)
        if val is not None:
            rows.append({
                "año":       year,
                "indicador": "luminosidad_nocturna_idx",
                "valor":     val,
                "pais":      "Venezuela",
                "fuente": (
                    f"Li et al. (2020/2024) Figshare:9828827 file:{file_id} "
                    f"Harmonized NTL {year} {sensor}"
                ),
            })
        time.sleep(0.5)

    if not rows:
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    df = pd.DataFrame(rows)
    # Normalizar nombre de columna año/anio
    if "anio" in df.columns and "año" not in df.columns:
        df = df.rename(columns={"anio": "año"})
    return df.sort_values("año").reset_index(drop=True)


# Alias para compatibilidad con main.py (que llama build_viirs)
build_viirs = fetch_viirs


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="Re-descarga todos los anos aunque ya existan en cache")
    args = parser.parse_args()

    print("=" * 65)
    print("  VIIRS/DMSP Luminosidad Nocturna Venezuela")
    print("  Li et al. Figshare DOI:10.6084/m9.figshare.9828827")
    print("  Sin autenticacion requerida")
    if args.force:
        print("  MODO: --force (re-descarga completa)")
    else:
        print("  MODO: cache inteligente (solo anos faltantes)")
    print("=" * 65)

    settings.paths.ensure_exists()
    df = fetch_viirs(force_refresh=args.force)

    if df.empty:
        print("\n  0 anios disponibles. viirs.csv NO actualizado.")
        sys.exit(1)

    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    col_year = "año" if "año" in df.columns else "anio"
    print(f"\n{'='*65}")
    print(f"  Guardado: {OUTPUT}")
    print(f"  Total anos: {len(df)}  ({int(df[col_year].min())}-{int(df[col_year].max())})")
    print(f"  Rango DN: {df.valor.min():.4f} - {df.valor.max():.4f}")
    print(df[[col_year, "valor"]].to_string(index=False))
