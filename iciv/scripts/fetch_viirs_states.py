"""
Luminosidad Nocturna Satelital por Estado - Venezuela (2000-2024).

Fuente: Li et al. (2020, actualizado 2024) - "Harmonization of DMSP and VIIRS
        nighttime light data from 1992 to 2024 at the global scale"
        Figshare DOI: 10.6084/m9.figshare.9828827.v10

MISMA FUENTE que el indicador nacional (fetch_viirs.py).
Sin datos inventados, sin factores diferenciales manuales, sin fallbacks.
Cada valor es la media DN real extraida del raster GeoTIFF global
recortado al bounding box GADM del estado.

Metodologia:
  1. Para cada ano descarga el GeoTIFF global de Li et al. (~25-40 MB)
  2. Para ese mismo TIF extrae la media DN de los 25 estados (bboxes GADM)
  3. Borra el TIF
  4. Guarda resultados en viirs_states.csv

ntl_idx = media DN cruda del bbox estatal (escala 0-63, misma que nacional).
          Se muestra directamente sin normalizar para poder comparar entre
          estados y anos con la misma escala de referencia.

Cache inteligente: si ya existe viirs_states.csv con datos para un ano,
ese ano no se re-descarga.

Cita: Li, X., Zhou, Y., Zhao, M., & Gao, X. (2020). A harmonized global
      nighttime light dataset 1992-2020. Scientific Data, 7(1), 168.
      https://doi.org/10.1038/s41597-020-0510-y

Salida: data/raw/viirs_states.csv
Columnas: ano | estado | estado_cod | ntl_idx | fuente

Uso:
    pip install rasterio requests numpy
    python scripts/fetch_viirs_states.py
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

OUTPUT = settings.paths.raw_viirs_states

# ---------------------------------------------------------------------------
# ESTADOS DE VENEZUELA - 24 estados + Distrito Capital
# Bounding boxes (lon_min, lat_min, lon_max, lat_max) en WGS84
# Fuente geometria: GADM Venezuela Level 1 (gadm.org)
# ---------------------------------------------------------------------------
ESTADOS: list[dict] = [
    {"name": "Distrito Capital",  "code": "DC", "bbox": (-67.05,  10.37, -66.75, 10.61)},
    {"name": "Miranda",           "code": "MI", "bbox": (-67.35,  10.01, -65.90, 10.78)},
    {"name": "Zulia",             "code": "ZU", "bbox": (-73.35,   9.18, -70.92, 11.83)},
    {"name": "Carabobo",          "code": "CA", "bbox": (-68.72,   9.85, -67.68, 10.78)},
    {"name": "Aragua",            "code": "AR", "bbox": (-68.32,   9.60, -66.97, 10.67)},
    {"name": "Lara",              "code": "LA", "bbox": (-70.60,   9.16, -68.60, 10.88)},
    {"name": "Anzoategui",        "code": "AN", "bbox": (-66.32,   7.80, -62.62, 10.72)},
    {"name": "Bolivar",           "code": "BO", "bbox": (-63.48,   3.64, -60.00,  8.65)},
    {"name": "Monagas",           "code": "MO", "bbox": (-64.05,   8.45, -62.05, 10.52)},
    {"name": "Tachira",           "code": "TA", "bbox": (-72.50,   7.38, -71.40,  8.88)},
    {"name": "Merida",            "code": "ME", "bbox": (-71.90,   7.72, -70.50,  9.20)},
    {"name": "Falcon",            "code": "FA", "bbox": (-70.80,  10.55, -68.78, 11.90)},
    {"name": "Sucre",             "code": "SU", "bbox": (-64.08,  10.07, -62.05, 10.95)},
    {"name": "Nueva Esparta",     "code": "NE", "bbox": (-64.54,  10.73, -63.46, 11.22)},
    {"name": "Trujillo",          "code": "TR", "bbox": (-70.70,   8.90, -69.82, 10.00)},
    {"name": "Barinas",           "code": "BA", "bbox": (-70.68,   6.88, -68.55,  9.07)},
    {"name": "Portuguesa",        "code": "PO", "bbox": (-70.47,   8.05, -68.65,  9.82)},
    {"name": "Guarico",           "code": "GU", "bbox": (-67.90,   7.13, -65.22,  9.93)},
    {"name": "Cojedes",           "code": "CO", "bbox": (-68.90,   8.97, -67.92, 10.22)},
    {"name": "Yaracuy",           "code": "YA", "bbox": (-69.23,  10.00, -68.38, 10.78)},
    {"name": "Vargas",            "code": "VA", "bbox": (-67.38,  10.47, -66.75, 10.81)},
    {"name": "Apure",             "code": "AP", "bbox": (-70.87,   5.93, -66.15,  8.20)},
    {"name": "Amazonas",          "code": "AM", "bbox": (-68.03,   0.65, -60.00,  6.23)},
    {"name": "Delta Amacuro",     "code": "DE", "bbox": (-62.52,   7.83, -59.80, 10.30)},
    {"name": "Dependencias Fed.", "code": "DF", "bbox": (-67.50,  10.50, -61.00, 12.00)},
]

# Mismos file IDs que en fetch_viirs.py (Li et al. Figshare v10)
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


def _extract_state_means(tif_path: Path) -> dict[str, float | None]:
    """
    Abre el GeoTIFF y calcula la media DN para cada estado.
    Retorna {codigo_estado: mean_DN} con None si no hay pixeles validos.
    """
    try:
        import rasterio
        from rasterio.windows import from_bounds
    except ImportError:
        raise RuntimeError("rasterio no instalado: pip install rasterio")

    results: dict[str, float | None] = {}
    with rasterio.open(tif_path) as src:
        nodata_val = src.nodata if src.nodata is not None else -9999
        for estado in ESTADOS:
            lon_min, lat_min, lon_max, lat_max = estado["bbox"]
            try:
                window = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)
                data = src.read(1, window=window).astype(float)
                valid = data[(data != nodata_val) & (data > 0)]
                if valid.size == 0:
                    results[estado["code"]] = None
                else:
                    results[estado["code"]] = round(float(valid.mean()), 4)
            except Exception:
                results[estado["code"]] = None
    return results


def _download_tif(year: int, file_id: int) -> Path | None:
    """Descarga el TIF de Figshare y retorna la ruta al archivo temporal."""
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
        print("OK", flush=True)
        return tmp_path
    except requests.exceptions.Timeout:
        print("TIMEOUT")
        if tmp_path.exists():
            tmp_path.unlink()
        return None
    except requests.exceptions.HTTPError as exc:
        print(f"HTTP {exc.response.status_code}")
        if tmp_path.exists():
            tmp_path.unlink()
        return None
    except Exception as exc:
        print(f"ERROR: {exc}")
        if tmp_path.exists():
            tmp_path.unlink()
        return None


def _years_already_cached(output: Path) -> set[int]:
    """Lee el CSV existente y devuelve los anos que ya tienen datos."""
    if not output.exists():
        return set()
    try:
        df = pd.read_csv(output, encoding="utf-8-sig")
        col = "ano" if "ano" in df.columns else ("año" if "año" in df.columns else None)
        if col is None or df.empty:
            return set()
        return set(df[col].astype(int).unique())
    except Exception:
        return set()


def build_viirs_states(force_refresh: bool = False) -> pd.DataFrame:
    """
    Descarga TIFs de Li et al. Figshare y extrae la media DN por estado.
    Cache inteligente: omite anos ya presentes en el CSV de salida.
    Sin datos inventados. Sin factores diferenciales manuales.
    """
    cached_years = set() if force_refresh else _years_already_cached(OUTPUT)
    years_needed = [y for y in sorted(FIGSHARE_FILES.keys()) if y not in cached_years]

    if not years_needed:
        print("  Cache completo — todos los anos ya procesados. Leyendo CSV.")
        return pd.read_csv(OUTPUT, encoding="utf-8-sig")

    print(f"  Anos a descargar: {len(years_needed)} ({years_needed[0]}-{years_needed[-1]})")
    print(f"  Anos en cache: {len(cached_years)}")

    new_rows: list[dict] = []

    for year in years_needed:
        file_id, filename = FIGSHARE_FILES[year]
        sensor = "calDMSP" if "calDMSP" in filename else "simVIIRS"
        print(f"\n  [{year}] {sensor}", flush=True)

        tif_path = _download_tif(year, file_id)
        if tif_path is None:
            print(f"    Omitiendo {year} (descarga fallida)")
            continue

        try:
            state_means = _extract_state_means(tif_path)
            n_valid = sum(1 for v in state_means.values() if v is not None)
            print(f"    Extraidos {n_valid}/{len(ESTADOS)} estados")

            source = (
                f"Li et al. (2020/2024) Figshare:9828827 file:{file_id} "
                f"Harmonized NTL {year} {sensor}"
            )
            for estado in ESTADOS:
                val = state_means.get(estado["code"])
                if val is not None:
                    new_rows.append({
                        "ano":        year,
                        "estado":     estado["name"],
                        "estado_cod": estado["code"],
                        "ntl_idx":    val,
                        "fuente":     source,
                    })
        finally:
            if tif_path.exists():
                tif_path.unlink()

        time.sleep(0.5)

    if not new_rows and not cached_years:
        print("\n  0 datos obtenidos. viirs_states.csv NO actualizado.")
        return pd.DataFrame(columns=["ano", "estado", "estado_cod", "ntl_idx", "fuente"])

    df_new = pd.DataFrame(new_rows) if new_rows else pd.DataFrame()

    # Combinar con cache existente
    if cached_years and OUTPUT.exists():
        df_old = pd.read_csv(OUTPUT, encoding="utf-8-sig")
        col_ano = "ano" if "ano" in df_old.columns else "año"
        if col_ano == "año":
            df_old = df_old.rename(columns={"año": "ano"})
        df_combined = pd.concat([df_old, df_new], ignore_index=True) if not df_new.empty else df_old
    else:
        df_combined = df_new

    if df_combined.empty:
        return df_combined

    df_combined = df_combined.sort_values(["ano", "estado"]).reset_index(drop=True)
    return df_combined


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-descarga todos los anos")
    args = parser.parse_args()

    print("=" * 65)
    print("  VIIRS/DMSP Luminosidad por Estado - Venezuela")
    print("  Li et al. Figshare DOI:10.6084/m9.figshare.9828827")
    print("  Sin datos inventados. Sin factores diferenciales.")
    print("=" * 65)

    settings.paths.ensure_exists()
    df = build_viirs_states(force_refresh=args.force)

    if df.empty:
        print("\n  0 estados descargados.")
        sys.exit(1)

    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    n_years  = df["ano"].nunique()
    n_states = df["estado_cod"].nunique()
    print(f"\n{'='*65}")
    print(f"  Guardado: {OUTPUT}")
    print(f"  {n_years} anos x {n_states} estados = {len(df)} filas")
    print(f"  Rango DN: {df.ntl_idx.min():.4f} - {df.ntl_idx.max():.4f}")
    print()

    # Resumen por estado (media historica)
    resumen = (
        df.groupby("estado_cod")["ntl_idx"]
          .mean()
          .sort_values(ascending=False)
          .reset_index()
    )
    resumen.columns = ["cod", "mean_DN"]
    print(resumen.to_string(index=False))
