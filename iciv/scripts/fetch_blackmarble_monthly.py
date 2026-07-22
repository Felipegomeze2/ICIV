"""
NASA Black Marble (VNP46A3) — luminosidad nocturna MENSUAL de Venezuela.

Fuente OFICIAL: NASA LAADS DAAC, producto VNP46A3 (composite mensual
gap-filled de radiancia nocturna VIIRS DNB, 15 arc-seg, coleccion 002).
  Descubrimiento de granulos: CMR (catalogo publico, sin auth)
      https://cmr.earthdata.nasa.gov/search/granules.json
  Descarga de archivos .h5 (requiere token Earthdata Bearer):
      https://data.laadsdaac.earthdatacloud.nasa.gov/prod-lads/VNP46A3/

Cobertura espacial: Venezuela ocupa 5 tiles de 10x10 grados:
  h10v07 h11v07 (lat 10-20N) | h10v08 h11v08 h12v08 (lat 0-10N)
  (h12v07 es oceano/Guyana: 0 pixeles de Venezuela, se omite)

Salidas (dos archivos):
  data/raw/blackmarble_monthly.csv  (nacional, formato largo año|mes|variable|valor|fuente)
    variables por mes:
      luminosidad_nocturna_mensual_nwcm2sr   media aritmetica (compat historica)
      luminosidad_nocturna_mediana           mediana — robusta al flaring petrolero
      luminosidad_nocturna_logmedia          media geometrica-log — atenua brillos extremos
      luminosidad_nocturna_p90               percentil 90 — nucleos mas iluminados
      luminosidad_nocturna_frac_iluminada    fraccion de pixeles > 1 nW/cm2/sr (proxy urbano)
  data/raw/blackmarble_states_monthly.csv  (subnacional año|mes|estado|cod|radiancia_media|fuente)
    radiancia media por cada uno de los 25 estados/entidades → habilita el mapa mensual.

Por que varias agregaciones: la media puede estar dominada por el flaring de
gas del Orinoco (llamas de gas extremadamente brillantes que NO son actividad
economica). La mediana, la log-media y la fraccion iluminada atenuan ese
sesgo y suelen correlacionar mejor con actividad economica real.

Metodo:
  1. CMR lista los 5 granulos del mes (bounding box de Venezuela).
  2. Se descarga cada tile .h5 (token EARTHDATA_TOKEN de env o iciv/.env).
  3. Capa NearNadir_Composite_Snow_Free (radiancia nW/cm2/sr).
  4. Se asigna cada pixel a su estado con etiquetas cacheadas
     (data/sources/bm_masks/bm_states_{tile}.npz) generadas desde
     venezuela_states.geojson en una sola pasada.
  5. Agregaciones nacionales + media por estado; se borran los .h5.

Incremental: --months N procesa N meses faltantes (mas reciente primero).
--reprocess recomputa TODOS los meses (necesario al anadir agregaciones).

Rol: capa auxiliar en evaluacion. NO entra al Pulse hasta validar variantes
de agregacion vs la serie anual (Li et al.) y decidir peso + backtest.

Politica de datos: mes sin los 5 tiles o sin token -> no se escribe ese mes.
Sin estimaciones ni rellenos.

Uso:
    python scripts/fetch_blackmarble_monthly.py                # 3 meses faltantes
    python scripts/fetch_blackmarble_monthly.py --months 200   # backfill completo
    python scripts/fetch_blackmarble_monthly.py --reprocess --months 200  # recomputar todo
"""

from __future__ import annotations

import argparse
import calendar
import json
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

DEFAULT_START = "2014-01"
END_YEAR = _CFG["serie"]["end_year"]

OUTPUT        = _ICIV_DIR / "data" / "raw" / "blackmarble_monthly.csv"
OUTPUT_STATES = _ICIV_DIR / "data" / "raw" / "blackmarble_states_monthly.csv"
GEOJSON       = _ICIV_DIR / "data" / "raw" / "venezuela_states.geojson"
INTERIM       = _ICIV_DIR / "data" / "interim"
_MASKS_DIR    = _ICIV_DIR / "data" / "sources" / "bm_masks"

_CMR_URL  = "https://cmr.earthdata.nasa.gov/search/granules.json"
_HEADERS  = {"User-Agent": "Mozilla/5.0 (academic research project ICIV)"}
_BBOX     = "-73.5,0.5,-59.5,12.5"
_TILES    = {"h10v07", "h11v07", "h10v08", "h11v08", "h12v08"}
_H5_LAYER = "HDFEOS/GRIDS/VNP_Grid_DNB/Data Fields/NearNadir_Composite_Snow_Free"
_PIX      = 2400
_LIT_THRESHOLD = 1.0  # nW/cm2/sr — umbral "iluminado" (proxy urbano)

# Variables nacionales: (sufijo_variable, funcion sobre el vector de radiancia del pais)
_NAT_STATS = {
    "luminosidad_nocturna_mensual_nwcm2sr": lambda v: float(np.mean(v)),
    "luminosidad_nocturna_mediana":         lambda v: float(np.median(v)),
    "luminosidad_nocturna_logmedia":        lambda v: float(np.expm1(np.mean(np.log1p(np.clip(v, 0, None))))),
    "luminosidad_nocturna_p90":             lambda v: float(np.percentile(v, 90)),
    "luminosidad_nocturna_frac_iluminada":  lambda v: float(np.mean(v > _LIT_THRESHOLD) * 100.0),
}

_FUENTE = (
    "NASA Black Marble VNP46A3 (LAADS DAAC, coleccion 002), radiancia "
    "NearNadir Composite Snow Free sobre Venezuela (mascara venezuela_states.geojson, "
    "5 tiles). nW/cm2/sr salvo frac_iluminada (%)."
)


def _load_token() -> str | None:
    if os.environ.get("EARTHDATA_TOKEN"):
        return os.environ["EARTHDATA_TOKEN"]
    env_file = _ICIV_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "EARTHDATA_TOKEN":
                val = val.strip().strip('"').strip("'")
                if val:
                    return val
    return None


def _state_names() -> list[tuple[str, str]]:
    """[(cod, nombre)] en orden del geojson."""
    gj = json.loads(GEOJSON.read_text(encoding="utf-8"))
    return [(f["properties"].get("cod", str(i)), f["properties"].get("nombre", str(i)))
            for i, f in enumerate(gj.get("features", []))]


def _tile_bounds(tile: str) -> tuple[float, float]:
    h = int(tile[1:3]); v = int(tile[4:6])
    return -180.0 + 10.0 * h, 90.0 - 10.0 * v


def _tile_state_labels(tile: str) -> np.ndarray:
    """Etiqueta de estado por pixel (int16 2400x2400): -1 fuera de Venezuela,
    si no el indice del estado en el orden del geojson. Cacheada."""
    _MASKS_DIR.mkdir(parents=True, exist_ok=True)
    cache = _MASKS_DIR / f"bm_states_{tile}.npz"
    if cache.exists():
        return np.load(cache)["labels"]

    from matplotlib.path import Path as MplPath

    lon0, lat0 = _tile_bounds(tile)
    step = 10.0 / _PIX
    lons = lon0 + (np.arange(_PIX) + 0.5) * step
    lats = lat0 - (np.arange(_PIX) + 0.5) * step
    lon_g, lat_g = np.meshgrid(lons, lats)
    pts = np.column_stack([lon_g.ravel(), lat_g.ravel()])

    labels = np.full(_PIX * _PIX, -1, dtype=np.int16)
    gj = json.loads(GEOJSON.read_text(encoding="utf-8"))
    for si, feat in enumerate(gj.get("features", [])):
        geom = feat.get("geometry") or {}
        polys = ([geom["coordinates"]] if geom.get("type") == "Polygon"
                 else geom.get("coordinates", []) if geom.get("type") == "MultiPolygon" else [])
        for poly in polys:
            outer = np.asarray(poly[0], dtype=float)
            if (outer[:, 0].max() < lon0 or outer[:, 0].min() > lon0 + 10 or
                    outer[:, 1].max() < lat0 - 10 or outer[:, 1].min() > lat0):
                continue
            inside = MplPath(outer).contains_points(pts)
            for ring in poly[1:]:
                inside &= ~MplPath(np.asarray(ring, dtype=float)).contains_points(pts)
            take = inside & (labels == -1)
            labels[take] = si

    labels = labels.reshape(_PIX, _PIX)
    np.savez_compressed(cache, labels=labels)
    print(f"    etiquetas {tile}: {int((labels >= 0).sum())} pixeles de Venezuela (cacheada)")
    return labels


def _cmr_granules(year: int, month: int) -> dict[str, str]:
    last = calendar.monthrange(year, month)[1]
    params = {
        "short_name": "VNP46A3", "bounding_box": _BBOX,
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
                    if l.get("href", "").endswith(".h5") and l["href"].startswith("https")), None)
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


def _tile_radiance(h5_path: Path) -> np.ndarray:
    """Devuelve la radiancia escalada 2400x2400; los pixeles fill quedan NaN.

    El fill se filtra sobre el dato CRUDO antes de escalar (el fill 65535 no
    debe multiplicarse por el scale_factor: contaminaria las estadisticas)."""
    import h5py
    with h5py.File(h5_path, "r") as f:
        if _H5_LAYER in f:
            ds = f[_H5_LAYER]
        else:
            found = []
            f.visit(lambda name: found.append(name)
                    if name.endswith("NearNadir_Composite_Snow_Free") else None)
            if not found:
                raise KeyError("capa NearNadir_Composite_Snow_Free no encontrada")
            ds = f[found[0]]
        raw = ds[()].astype(np.float64)
        fill  = float(np.ravel(ds.attrs.get("_FillValue", [65535]))[0])
        scale = float(np.ravel(ds.attrs.get("scale_factor", [1.0]))[0])
        offset = float(np.ravel(ds.attrs.get("add_offset", [0.0]))[0])
    valid_raw = raw != fill
    scaled = np.full(raw.shape, np.nan, dtype=np.float64)
    scaled[valid_raw] = raw[valid_raw] * scale + offset
    return scaled


def _process_month(year: int, month: int, token: str,
                   states: list[tuple[str, str]]) -> tuple[list[dict], list[dict]] | None:
    granules = _cmr_granules(year, month)
    if set(granules) != _TILES:
        print(f"  [WARN] {year}-{month:02d}: {len(granules)}/{len(_TILES)} tiles — mes omitido")
        return None

    nat_vals: list[np.ndarray] = []
    st_sum = np.zeros(len(states)); st_cnt = np.zeros(len(states))
    with tempfile.TemporaryDirectory() as tmp:
        for tile, url in sorted(granules.items()):
            dest = Path(tmp) / f"{tile}.h5"
            _download(url, token, dest)
            scaled = _tile_radiance(dest)
            labels = _tile_state_labels(tile)
            in_ve = labels >= 0
            # el fill ya quedo como NaN dentro de _tile_radiance
            valid = in_ve & np.isfinite(scaled)
            vals = scaled[valid]
            nat_vals.append(vals)
            lab = labels[valid]
            # acumular por estado
            np.add.at(st_sum, lab, vals)
            np.add.at(st_cnt, lab, 1.0)
            dest.unlink(missing_ok=True)

    allv = np.concatenate(nat_vals)
    if allv.size == 0:
        print(f"  [WARN] {year}-{month:02d}: 0 pixeles validos")
        return None

    nat_rows = [{
        "año": year, "mes": month, "variable": var,
        "valor": round(fn(allv), 4), "fuente": _FUENTE,
    } for var, fn in _NAT_STATS.items()]

    st_rows = []
    for i, (cod, nombre) in enumerate(states):
        if st_cnt[i] > 0:
            st_rows.append({
                "año": year, "mes": month, "estado": nombre, "cod": cod,
                "radiancia_media": round(float(st_sum[i] / st_cnt[i]), 4),
                "fuente": _FUENTE,
            })
    mean_v = round(float(np.mean(allv)), 4)
    med_v = round(float(np.median(allv)), 4)
    print(f"  {year}-{month:02d}: OK — media={mean_v} mediana={med_v} "
          f"nW/cm2/sr sobre {allv.size} px, {len(st_rows)} estados")
    return nat_rows, st_rows


def _existing_months(path: Path) -> set[str]:
    if not path.exists():
        return set()
    df = pd.read_csv(path)
    return {f"{int(r['año'])}-{int(r['mes']):02d}" for _, r in df.iterrows()}


def _candidate_months(start: str) -> list[tuple[int, int]]:
    sy, sm = int(start[:4]), int(start[5:7])
    today = date.today()
    end_y, end_m = today.year, today.month - 2
    while end_m <= 0:
        end_y, end_m = end_y - 1, end_m + 12
    months = []
    y, m = sy, sm
    while (y, m) <= (end_y, end_m) and y <= END_YEAR:
        months.append((y, m)); m += 1
        if m > 12:
            y, m = y + 1, 1
    return months[::-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Black Marble VNP46A3 mensual Venezuela")
    parser.add_argument("--months", type=int, default=3)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--reprocess", action="store_true",
                        help="recomputar meses ya presentes (para anadir agregaciones)")
    args = parser.parse_args()

    print("=" * 65)
    print("  NASA Black Marble VNP46A3 — luminosidad mensual + subnacional Venezuela")
    print("=" * 65)
    settings.paths.ensure_exists()

    token = _load_token()
    if token is None:
        print("  [WARN] EARTHDATA_TOKEN no configurado. No se descarga nada.")
        return
    try:
        import h5py  # noqa: F401
    except ImportError:
        print("  [WARN] h5py no instalado. No se procesa nada.")
        return

    states = _state_names()
    # Si la salida nacional aun no tiene las nuevas variables, forzar reprocess.
    if OUTPUT.exists() and not args.reprocess:
        existing_vars = set(pd.read_csv(OUTPUT)["variable"].unique())
        if not set(_NAT_STATS).issubset(existing_vars):
            print("  [INFO] faltan agregaciones nuevas en el CSV → activando --reprocess")
            args.reprocess = True

    # Meses con las 5 agregaciones ya completas (para reanudar sin reprocesar)
    complete = set()
    if OUTPUT.exists():
        _cur = pd.read_csv(OUTPUT)
        _cnt = _cur.groupby(["año", "mes"])["variable"].nunique()
        complete = {f"{int(y)}-{int(m):02d}" for (y, m), n in _cnt.items() if n >= len(_NAT_STATS)}
    done = complete if args.reprocess else _existing_months(OUTPUT)
    pending = [(y, m) for (y, m) in _candidate_months(args.start)
               if f"{y}-{m:02d}" not in done][:args.months]
    if not pending:
        print("  Sin meses pendientes. CSV al dia.")
        return

    def _upsert(path: Path, new_rows: list[dict], keys: list[str]) -> pd.DataFrame:
        df_new = pd.DataFrame(new_rows)
        if path.exists():
            old = pd.read_csv(path)
            proc = {(int(r["año"]), int(r["mes"])) for _, r in df_new.iterrows()}
            old = old[~old.apply(lambda r: (int(r["año"]), int(r["mes"])) in proc, axis=1)]
            df = pd.concat([old, df_new], ignore_index=True)
        else:
            df = df_new
        return df.drop_duplicates(subset=keys, keep="last").sort_values(
            [k for k in keys if k in df.columns]).reset_index(drop=True)

    processed = 0
    for year, month in pending:
        try:
            res = _process_month(year, month, token, states)
        except Exception as exc:
            print(f"  [ERROR] {year}-{month:02d}: {exc} — mes omitido")
            continue
        if not res:
            continue
        # Guardado incremental tras cada mes (reanudable ante cortes)
        _upsert(OUTPUT, res[0], ["año", "mes", "variable"]).to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        _upsert(OUTPUT_STATES, res[1], ["año", "mes", "estado"]).to_csv(OUTPUT_STATES, index=False, encoding="utf-8-sig")
        processed += 1

    if processed == 0:
        print("\n  Sin filas nuevas.")
        return
    df_nat = pd.read_csv(OUTPUT)
    df_st = pd.read_csv(OUTPUT_STATES)
    n_meses = df_nat[["año", "mes"]].drop_duplicates().shape[0]
    print(f"\n  Nacional: {OUTPUT.name} — {n_meses} meses × {len(_NAT_STATS)} variables (+{processed} reprocesados)")
    print(f"  Subnacional: {OUTPUT_STATES.name} — {len(df_st)} filas ({df_st['estado'].nunique()} estados)")


if __name__ == "__main__":
    main()
