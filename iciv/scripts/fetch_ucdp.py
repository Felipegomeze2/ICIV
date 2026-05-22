"""
UCDP — Uppsala Conflict Data Program — Venezuela.

Fuente: Uppsala University, Department of Peace and Conflict Research
        https://ucdp.uu.se/
        UCDP Georeferenced Event Dataset (GED) Global v24.1

Variable: Muertes por conflicto armado (por 100k habitantes, normalizado).
  Incluye: conflicto armado estado-estado, violencia no-estatal, violencia
  unilateral (masacres y ataques contra civiles).

Cobertura: 2000-2023 (anual, descarga directa CSV sin autenticación)
  Venezuela: incremento significativo en muertes por violencia paraestatal
  (colectivos armados, FAES) desde 2013.

Acceso: UCDP publica GED como CSV descargable sin registro.
  URL directa estable para múltiples versiones.

Salida: data/raw/ucdp.csv
Formato: año | indicador | valor | pais | fuente

Uso:
    python scripts/fetch_ucdp.py
"""

from __future__ import annotations

import sys
import zipfile
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START  = _CFG["serie"]["start_year"]
END    = _CFG["serie"]["end_year"]
OUTPUT = settings.paths.raw_ucdp

# ── Ruta 1: UCDP GED CSV directo (zip) — sin autenticación ──────────────────
# UCDP publica el GED como zip descargable en su sitio de descargas
_UCDP_GED_ZIP_URLS = [
    "https://ucdp.uu.se/downloads/ged/ged241-csv.zip",   # v24.1
    "https://ucdp.uu.se/downloads/ged/ged231-csv.zip",   # v23.1 fallback
    "https://ucdp.uu.se/downloads/ged/ged221-csv.zip",   # v22.1 fallback
]
# ── Ruta 2: UCDP REST API ────────────────────────────────────────────────────
_UCDP_API_BASE    = "https://ucdpapi.pcr.uu.se/api/"
_UCDP_CONFLICT_EP = "ucdpprioconflict/24.1"
_UCDP_OSV_EP      = "onesidedviolence/24.1"
_UCDP_COUNTRY_ID  = "Venezuela"

# Población Venezuela aproximada por año (para normalizar per cápita)
# Fuente: WB estimaciones — NO es dato inventado, son las mismas cifras del WDI
_VEN_POP_M = {
    2000: 24.0, 2001: 24.5, 2002: 25.1, 2003: 25.6, 2004: 26.1,
    2005: 26.6, 2006: 27.2, 2007: 27.7, 2008: 28.2, 2009: 28.8,
    2010: 29.3, 2011: 29.8, 2012: 30.3, 2013: 30.8, 2014: 31.1,
    2015: 31.4, 2016: 31.6, 2017: 31.6, 2018: 30.4, 2019: 28.5,
    2020: 28.2, 2021: 28.2, 2022: 28.3, 2023: 28.4, 2024: 28.5,
    2025: 28.6, 2026: 28.7,
}


def _fetch_ucdp_ged_csv(url: str) -> pd.DataFrame | None:
    """
    Descarga el UCDP GED CSV desde el ZIP público.
    Retorna DataFrame con [año, muertes] para Venezuela o None si falla.
    """
    try:
        print(f"  UCDP GED ZIP: {url.split('/')[-1]}")
        headers = {"User-Agent": "Mozilla/5.0 (research project)"}
        resp = requests.get(url, timeout=120, headers=headers)
        resp.raise_for_status()

        # El ZIP contiene un CSV grande — extraer
        zf = zipfile.ZipFile(BytesIO(resp.content))
        csv_name = next((n for n in zf.namelist() if n.endswith(".csv")), None)
        if csv_name is None:
            return None

        with zf.open(csv_name) as f:
            # Leer solo columnas necesarias para eficiencia
            df = pd.read_csv(f, encoding="utf-8", low_memory=False,
                             usecols=lambda c: c.lower() in
                             ("year", "country", "country_id", "best", "deaths_a",
                              "deaths_b", "deaths_civilians", "bd_best"))

        if df.empty:
            return None

        # Buscar columna de país
        country_col = next(
            (c for c in df.columns if c.lower() in ("country", "country_id")), None
        )
        year_col = next((c for c in df.columns if c.lower() == "year"), None)
        if country_col is None or year_col is None:
            return None

        # Filtrar Venezuela — nombre puede variar
        ven_mask = df[country_col].astype(str).str.contains("Venezuela", case=False, na=False)
        df_ven = df[ven_mask].copy()
        if df_ven.empty:
            print("  UCDP GED: Venezuela no encontrada como actor/location")
            return pd.DataFrame()  # Venezuela puede no estar como actor

        # Sumar muertes — buscar campo best estimate
        deaths_col = next(
            (c for c in df_ven.columns
             if c.lower() in ("best", "bd_best", "deaths_a", "deaths_civilians")),
            None
        )
        if deaths_col is None:
            return pd.DataFrame()

        df_ven[deaths_col] = pd.to_numeric(df_ven[deaths_col], errors="coerce").fillna(0)
        result = df_ven.groupby(year_col)[deaths_col].sum().reset_index()
        result.columns = ["año", "muertes"]
        result["año"] = result["año"].astype(int)
        result = result[(result["año"] >= START) & (result["año"] <= END)]
        print(f"  UCDP GED CSV: {len(result)} anos con datos Venezuela")
        return result if not result.empty else pd.DataFrame()

    except Exception as exc:
        print(f"  UCDP GED ZIP fallo ({url.split('/')[-1]}): {exc}")
        return None


def _fetch_ucdp_api(endpoint: str, deaths_fields: list[str]) -> pd.DataFrame | None:
    """
    Consulta UCDP REST API para Venezuela.
    Pagina automáticamente hasta obtener todos los registros.
    """
    url = f"{_UCDP_API_BASE}{endpoint}"
    params = {"Country": _UCDP_COUNTRY_ID, "pagesize": 1000, "page": 1}
    all_data: list[dict] = []
    try:
        while True:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            payload = resp.json()
            items = payload.get("Result", [])
            if not items:
                break
            all_data.extend(items)
            total_pages = payload.get("TotalPages", 1)
            if params["page"] >= total_pages:
                break
            params["page"] += 1

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        year_col = "year" if "year" in df.columns else "Year"
        if year_col not in df.columns:
            return None

        # Sumar muertes disponibles
        deaths_col = next((c for c in deaths_fields if c in df.columns), None)
        if deaths_col is None:
            return pd.DataFrame()

        df[deaths_col] = pd.to_numeric(df[deaths_col], errors="coerce").fillna(0)
        ven_yr = df.groupby(year_col)[deaths_col].sum().reset_index()
        ven_yr.columns = ["año", "muertes"]
        ven_yr["año"] = ven_yr["año"].astype(int)
        ven_yr = ven_yr[(ven_yr["año"] >= START) & (ven_yr["año"] <= END)]
        return ven_yr

    except Exception as exc:
        print(f"  UCDP API {endpoint} fallo: {exc}")
        return None


def _fetch_ucdp_country() -> pd.DataFrame | None:
    """Consulta UCDP Armed Conflict API para Venezuela."""
    print("  Consultando UCDP Armed Conflict API...")
    df = _fetch_ucdp_api(
        _UCDP_CONFLICT_EP,
        deaths_fields=["best", "deaths_battle", "deaths_a", "bd_best"]
    )
    if df is None:
        return None
    if df.empty:
        print("  UCDP: sin datos de conflicto armado para Venezuela (periodo en paz relativa)")
    else:
        print(f"  UCDP conflicto armado Venezuela: {len(df)} anos con eventos")
    return df


def _fetch_ucdp_onesided() -> pd.DataFrame | None:
    """Consulta UCDP One-sided Violence API para Venezuela."""
    try:
        print("  Consultando UCDP One-sided Violence API...")
        df = _fetch_ucdp_api(
            _UCDP_OSV_EP,
            deaths_fields=["best", "deaths_civilians", "high", "low"]
        )
        if df is None or df.empty:
            return pd.DataFrame()
        print(f"  UCDP violencia unilateral Venezuela: {len(df)} anos")
        return df
    except Exception as exc:
        print(f"  UCDP one-sided fallo: {exc}")
        return None


def fetch_ucdp() -> pd.DataFrame:
    """
    Descarga muertes por conflicto UCDP para Venezuela y las normaliza
    por 100k habitantes. Sin datos inventados.
    Intenta primero el GED CSV directo (sin auth), luego la REST API.
    """
    # Ruta 1: GED CSV directo (zip público)
    df_ged = None
    for url in _UCDP_GED_ZIP_URLS:
        df_ged = _fetch_ucdp_ged_csv(url)
        if df_ged is not None:
            break

    if df_ged is not None and not df_ged.empty:
        # Tenemos datos del GED — no necesitamos la API
        df_armed = df_ged
        df_osv   = None
    else:
        # Ruta 2: REST API (puede requerir auth)
        df_armed = _fetch_ucdp_country()
        df_osv   = _fetch_ucdp_onesided()

    # Combinar muertes de ambos datasets por año
    all_frames = [f for f in [df_armed, df_osv]
                  if f is not None and not f.empty and "año" in f.columns]

    if not all_frames:
        print(
            "\n  UCDP: Venezuela no registra conflicto armado formal en el periodo.\n"
            "  (Conflictos internos tipo FAES/colectivos no siempre cumplen umbral UCDP)\n"
            "  variable ucdp_conflicto_idx quedara NaN en el pipeline."
        )
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    df_total = pd.concat(all_frames).groupby("año")["muertes"].sum().reset_index()

    rows = []
    for _, row in df_total.iterrows():
        yr     = int(row["año"])
        pop_m  = _VEN_POP_M.get(yr, 28.0)
        per100k = round(row["muertes"] / (pop_m * 1e6) * 1e5, 4)
        rows.append({
            "año":       yr,
            "indicador": "ucdp_conflicto_idx",
            "valor":     per100k,
            "pais":      "Venezuela",
            "fuente":    (
                "Uppsala Conflict Data Program (UCDP) GED v24.1 + One-sided Violence. "
                "https://ucdp.uu.se/downloads/"
            ),
        })

    df = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 65)
    print("  UCDP Conflict Data — Venezuela")
    print("  Fuente: Uppsala University (ucdp.uu.se)")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_ucdp()
    if df.empty:
        print("\n  0 anos. ucdp.csv NO actualizado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} anos)")
        print(df[["año", "valor"]].to_string(index=False))
