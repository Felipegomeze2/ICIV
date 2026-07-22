"""
NASA Black Marble (VNP46A3) — luminosidad nocturna MENSUAL de Venezuela.

Fuente OFICIAL: NASA LAADS DAAC, producto VNP46A3 (composite mensual
gap-filled de radiancia nocturna VIIRS DNB, 15 arc-seg, coleccion 002).
  Descubrimiento de granulos: CMR (catalogo publico, sin auth)
      https://cmr.earthdata.nasa.gov/search/granules.json
  Descarga de archivos .h5 (requiere token Earthdata Bearer):
      https://data.laadsdaac.earthdatacloud.nasa.gov/prod-lads/VNP46A3/

Cobertura espacial: Venezuela ocupa 6 tiles de 10x10 grados:
  h10v07 h11v07 h12v07 (lat 10-20N) | h10v08 h11v08 h12v08 (lat 0-10N)
Cada tile es una grilla lineal lat/lon de 2400x2400 pixeles.

Metodo:
  1. CMR lista los 6 granulos del mes (bounding box de Venezuela).
  2. Se descarga cada tile .h5 (token EARTHDATA_TOKEN de env o iciv/.env).
  3. Se lee la capa NearNadir_Composite_Snow_Free (radiancia nW/cm2/sr,
     estandar en la literatura economica, p.ej. Henderson et al. 2012).
  4. Se enmascara al territorio con data/raw/venezuela_states.geojson
     (mascara por tile cacheada en data/interim/bm_mask_{tile}.npy).
  5. valor del mes = promedio de radiancia sobre pixeles de Venezuela
     (suma ponderada entre tiles por numero de pixeles del pais).
  6. Los .h5 se borran tras procesar (no se acumulan gigas en el repo).

Incremental: los meses ya presentes en el CSV no se reprocesan. El
backfill se acota con --months N (procesa N meses faltantes por corrida,
del mas reciente al mas antiguo) para que cada corrida sea manejable.

Variable de salida:
  - luminosidad_nocturna_mensual_nwcm2sr (promedio pais, nW/cm2/sr)

Rol: capa auxiliar en evaluacion. NO entra al Pulse hasta validar la
serie mensual contra la anual (Li et al./VIIRS) y decidir peso + backtest.

Politica de datos: mes sin los 6 tiles o sin token → no se escribe ese
mes. Sin estimaciones ni rellenos.

Uso:
    python scripts/fetch_blackmarble_monthly.py                # 3 meses faltantes mas recientes
    python scripts/fetch_blackmarble_monthly.py --months 12    # backfill mas agresivo
    python scripts/fetch_blackmarble_monthly.py --start 2014-01
"""

from __future__ import annotations

import argparse
import calendar
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

_ICIV_DIR = Path(__file__).resolve().parents[1]
_CFG = yaml.safe_load((_ICIV_DIR / "config" / "settings.yaml").read_text(encoding="utf-8"))

DEFAULT_START = "2014-01"   # era VIIRS homogenea usada en la validacion externa
END_YEAR = _CFG["serie"]["end_year"]

OUTPUT    = _ICIV_DIR / "data" / "raw" / "blackmarble_monthly.csv"
GEOJSON   = _ICIV_DIR / "data" / "raw" / "venezuela_states.geojson"
INTERIM   = _ICIV_DIR / "data" / "interim"

_CMR_URL  = "https://cmr.earthdata.nasa.gov/search/granules.json"
_HEADERS  = {"User-Agent": "Mozilla/5.0 (academic research project ICIV)"}
_BBOX     = "-73.5,0.5,-59.5,12.5"
_TILES    = {"h10v07", "h11v07", "h12v07", "h10v08", "h11v08", "h12v08"}
_H5_LAYER = "HDFEOS/GRIDS/VNP_Grid_DNB/Data Fields/NearNadir_Composite_Snow_Free"
_PIX      = 2400  # pixeles por lado de tile (15 arc-seg)

_VARIABLE = "luminosidad_nocturna_mensual_nwcm2sr"
_FUENTE = (
    "NASA Black Marble VNP46A3 (LAADS DAAC, coleccion 002), radiancia "
    "NearNadir Composite Snow Free promediada sobre Venezuela "
    "(mascara venezuela_states.geojson, 6 tiles). nW/cm2/sr."
)


def _load_token() -> str | None:
    """Lee EARTHDATA_TOKEN del entorno o de iciv/.env. Nunca lo imprime."""
    if os.environ.get("EARTHDATA_TOKEN"):
        return os.environ["EARTHDATA_TOKEN"]
    env_file = _ICIV_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line.startswith("EARTHDATA_TOKEN=") :
                val = line.partition("=")[2].strip().strip('"').strip("'")
                if val:
                    return val
    return None


def _tile_bounds(tile: str) -> tuple[float, float]:
    """(lon_oeste, lat_norte) del tile lineal Black Marble."""
    h = int(tile[1:3])
    v = int(tile[4:6])
    return -180.0 + 10.0 * h, 90.0 - 10.0 * v


def _tile_mask(tile: str) -> np.ndarray:
    """Mascara booleana 2400x2400 de pixeles dentro de Venezuela (cacheada)."""
    INTERIM.mkdir(parents=True, exist_ok=True)
    cache = INTERIM / f"bm_mask_{tile}.npy"
    if cache.exists():
        return np.load(cache)

    import json as _json
    from matplotlib.path import Path as MplPath

    lon0, lat0 = _tile_bounds(tile)
    step = 10.0 / _PIX
    lons = lon0 + (np.arange(_PIX) + 0.5) * step
    lats = lat0 - (np.arange(_PIX) + 0.5) * step
    lon_g, lat_g = np.meshgrid(lons, lats)
    pts = np.column_stack([lon_g.ravel(), lat_g.ravel()])

    mask = np.zeros(_PIX * _PIX, dtype=bool)
    gj = _json.loads(GEOJSON.read_text(encoding="utf-8"))
    for feat in gj.get("features", []):
        geom = feat.get("geometry") or {}
        polys = []
        if geom.get("type") == "Polygon":
            polys = [geom["coordinates"]]
        elif geom.get("type") == "MultiPolygon":
            polys = geom["coordinates"]
        for poly in polys:
            outer = np.asarray(poly[0], dtype=float)
            # bounding box rapido para saltar poligonos fuera del tile
            if (outer[:, 0].max() < lon0 or outer[:, 0].min() > lon0 + 10 or
                    outer[:, 1].max() < lat0 - 10 or outer[:, 1].min() > lat0):
                continue
            inside = MplPath(outer).contains_points(pts)
            for ring in poly[1:]:  # huecos
                inside &= ~MplPath(np.asarray(ring, dtype=float)).contains_points(pts)
            mask |= inside

    mask = mask.reshape(_PIX, _PIX)
    np.save(cache, mask)
    print(f"    mascara {tile}: {int(mask.sum())} pixeles de Venezuela (cacheada)")
    return mask


def _cmr_granules(year: int, month: int) -> dict[str, str]:
    """{tile: url_h5} de los granulos VNP46A3 del mes via CMR (publico)."""
    last = calendar.monthrange(year, month)[1]
    params = {
        "short_name": "VNP46A3",
        "bounding_box": _BBOX,
        "temporal": f"{year}-{month:02d}-01T00:00:00Z,{year}-{month:02d}-{last:02d}T23:59:59Z",
        "page_size": 40,
    }
    resp = requests.get(_CMR_URL, params=params, timeout=90, headers=_HEADERS)
    resp.raise_for_status()
    out: dict[str, str] = {}
    for entry in resp.json().get("feed", {}).get("entry", []):
        gid = entry.get("producer_granule_id") or entry.get("title", "")
        tile = next((t for t in _TILES if t in gid), None)
        if tile is None:
            continue
        url = next((l["href"] for l in entry.get("links", [])
                    if l.get("href", "").endswith(".h5")
                    and l["href"].startswith("https")), None)
        if url:
            out[tile] = url
    return out


def _download(url: str, token: str, dest: Path) -> None:
    with requests.get(url, headers={**_HEADERS, "Authorization": f"Bearer {token}"},
                      stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)


def _tile_stats(h5_path: Path, tile: str) -> tuple[float, int]:
    """(suma_radiancia, n_pixeles_validos) del tile dentro de Venezuela."""
    import h5py

    with h5py.File(h5_path, "r") as f:
        if _H5_LAYER in f:
            ds = f[_H5_LAYER]
        else:  # buscar la capa por nombre si la ruta del grupo cambia
            found = []
            f.visit(lambda name: found.append(name)
                    if name.endswith("NearNadir_Composite_Snow_Free") else None)
            if not found:
                raise KeyError("capa NearNadir_Composite_Snow_Free no encontrada")
            ds = f[found[0]]
        data = ds[()].astype(np.float64)
        fill = ds.attrs.get("_FillValue", [65535])
        fill = float(np.ravel(fill)[0])
        scale = ds.attrs.get("scale_factor", [1.0])
        scale = float(np.ravel(scale)[0])
        offset = ds.attrs.get("add_offset", [0.0])
        offset = float(np.ravel(offset)[0])

    mask = _tile_mask(tile)
    valid = mask & (data != fill)
    vals = data[valid] * scale + offset
    return float(vals.sum()), int(valid.sum())


def _existing_months() -> set[str]:
    if not OUTPUT.exists():
        return set()
    df = pd.read_csv(OUTPUT)
    return {f"{int(r['año'])}-{int(r['mes']):02d}" for _, r in df.iterrows()}


def _candidate_months(start: str) -> list[tuple[int, int]]:
    """Meses candidatos (mas reciente primero), con ~2 meses de margen de publicacion."""
    sy, sm = int(start[:4]), int(start[5:7])
    today = date.today()
    end_y, end_m = today.year, today.month - 2
    while end_m <= 0:
        end_y, end_m = end_y - 1, end_m + 12
    months = []
    y, m = sy, sm
    while (y, m) <= (end_y, end_m) and y <= END_YEAR:
        months.append((y, m))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return months[::-1]


def fetch_blackmarble(months_per_run: int, start: str) -> pd.DataFrame:
    token = _load_token()
    if token is None:
        print(
            "  [WARN] EARTHDATA_TOKEN no configurado (env o iciv/.env).\n"
            "  Generarlo en urs.earthdata.nasa.gov (dura ~60 dias).\n"
            "  No se descarga nada."
        )
        return pd.DataFrame()

    try:
        import h5py  # noqa: F401
    except ImportError:
        print("  [WARN] h5py no instalado (pip install h5py). No se procesa nada.")
        return pd.DataFrame()

    done = _existing_months()
    pending = [(y, m) for (y, m) in _candidate_months(start)
               if f"{y}-{m:02d}" not in done][:months_per_run]
    if not pending:
        print("  Sin meses pendientes. CSV al dia.")
        return pd.DataFrame()

    rows = []
    for year, month in pending:
        label = f"{year}-{month:02d}"
        try:
            granules = _cmr_granules(year, month)
            if set(granules) != _TILES:
                print(f"  [WARN] {label}: {len(granules)}/6 tiles en CMR — mes omitido")
                continue
            total, npix = 0.0, 0
            with tempfile.TemporaryDirectory() as tmp:
                for tile, url in sorted(granules.items()):
                    dest = Path(tmp) / f"{tile}.h5"
                    print(f"  {label} {tile}: descargando...")
                    _download(url, token, dest)
                    s, n = _tile_stats(dest, tile)
                    total += s
                    npix += n
                    dest.unlink(missing_ok=True)
            if npix == 0:
                print(f"  [WARN] {label}: 0 pixeles validos — mes omitido")
                continue
            valor = round(total / npix, 4)
            rows.append({"año": year, "mes": month, "variable": _VARIABLE,
                         "valor": valor, "fuente": _FUENTE})
            print(f"  {label}: OK — {valor} nW/cm2/sr sobre {npix} pixeles")
        except Exception as exc:
            print(f"  [ERROR] {label}: {exc} — mes omitido")

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Black Marble VNP46A3 mensual Venezuela")
    parser.add_argument("--months", type=int, default=3,
                        help="meses faltantes a procesar por corrida (default 3)")
    parser.add_argument("--start", default=DEFAULT_START,
                        help=f"primer mes del backfill YYYY-MM (default {DEFAULT_START})")
    args = parser.parse_args()

    print("=" * 65)
    print("  NASA Black Marble VNP46A3 — luminosidad mensual Venezuela")
    print("=" * 65)
    settings.paths.ensure_exists()
    df_new = fetch_blackmarble(args.months, args.start)
    if df_new.empty:
        print("\n  Sin filas nuevas.")
        return
    if OUTPUT.exists():
        df = pd.concat([pd.read_csv(OUTPUT), df_new], ignore_index=True)
        df = df.drop_duplicates(subset=["año", "mes", "variable"], keep="last")
    else:
        df = df_new
    df = df.sort_values(["año", "mes"]).reset_index(drop=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\n  Guardado: {OUTPUT}  ({len(df)} filas totales, +{len(df_new)} nuevas)")


if __name__ == "__main__":
    main()
