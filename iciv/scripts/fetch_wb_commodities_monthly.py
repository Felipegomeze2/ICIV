"""
World Bank Commodity Prices ("Pink Sheet") — precios mensuales de crudo.

Fuente OFICIAL: World Bank — Commodity Markets ("Pink Sheet"), archivo
mensual CMO-Historical-Data-Monthly.xlsx:
    https://www.worldbank.org/en/research/commodity-markets

El URL del Excel cambia de doc-id cada cierto tiempo, por eso este script
primero lee la página oficial y extrae el enlace vigente; como fallback
usa los últimos URLs conocidos.

Variable de salida:
  - crudo_dubai_usd (USD/barril, hoja "Monthly Prices", columna
    "Crude oil, Dubai"). Dubai es el benchmark de crudo mediano-pesado
    ácido: aproxima mejor el precio relevante para la cesta venezolana
    (Merey, extra-pesado) que WTI/Brent, que ya están en el Pulse via
    FRED. Dirección positiva.

Política de datos: si la página o el Excel no responden, no se escribe
nada nuevo (se conserva el CSV previo si existe). Sin estimaciones.

Salida: data/raw/wb_commodities_monthly.csv
Formato: año | mes | variable | valor | fuente

Uso:
    python scripts/fetch_wb_commodities_monthly.py
"""

from __future__ import annotations

import re
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START_YEAR = 2010
END_YEAR   = _CFG["serie"]["end_year"]

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "wb_commodities_monthly.csv"

_HEADERS = {"User-Agent": "Mozilla/5.0 (academic research project ICIV)"}
_CMO_PAGE = "https://www.worldbank.org/en/research/commodity-markets"
_XLSX_RE  = re.compile(
    r"https://thedocs\.worldbank\.org/[^\"']+CMO-Historical-Data-Monthly\.xlsx"
)
# Fallbacks: últimos doc-ids conocidos (el más reciente primero)
_KNOWN_URLS = [
    "https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx",
    "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx",
]

_SHEET  = "Monthly Prices"
_COLUMN = "Crude oil, Dubai"
_VARIABLE = "crudo_dubai_usd"


def _current_xlsx_url() -> list[str]:
    """Lee la página oficial y devuelve URLs candidatos del Excel mensual."""
    urls: list[str] = []
    try:
        resp = requests.get(_CMO_PAGE, timeout=90, headers=_HEADERS)
        resp.raise_for_status()
        found = _XLSX_RE.findall(resp.text)
        if found:
            print(f"  Pink Sheet: URL vigente detectado en la pagina oficial")
            urls.extend(dict.fromkeys(found))  # dedup preservando orden
    except Exception as exc:
        print(f"  [WARN] No se pudo leer la pagina de commodity markets: {exc}")
    for u in _KNOWN_URLS:
        if u not in urls:
            urls.append(u)
    return urls


def fetch_wb_commodities_monthly() -> pd.DataFrame:
    """Descarga el Pink Sheet mensual y extrae Crude oil, Dubai."""
    content = None
    used_url = None
    for url in _current_xlsx_url():
        try:
            resp = requests.get(url, timeout=120, headers=_HEADERS)
            ct = resp.headers.get("Content-Type", "")
            if resp.status_code == 200 and "html" not in ct.lower():
                content, used_url = resp.content, url
                break
            print(f"  Pink Sheet {url.split('/')[-2][:16]}...: HTTP {resp.status_code} — se omite")
        except Exception as exc:
            print(f"  Pink Sheet fallo: {exc}")

    if content is None:
        print("  [ERROR] Pink Sheet no disponible. No se escribe nada nuevo.")
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    df = pd.read_excel(BytesIO(content), sheet_name=_SHEET, header=4)
    date_col = df.columns[0]
    if _COLUMN not in df.columns:
        print(f"  [ERROR] Columna '{_COLUMN}' no encontrada en '{_SHEET}'.")
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    rows = []
    for _, r in df.iterrows():
        label = str(r[date_col]).strip()          # formato '2026M06'
        m = re.fullmatch(r"(\d{4})M(\d{2})", label)
        if not m:
            continue
        year, month = int(m.group(1)), int(m.group(2))
        if not (START_YEAR <= year <= END_YEAR):
            continue
        val = pd.to_numeric(r[_COLUMN], errors="coerce")
        if pd.isna(val) or val <= 0:
            continue
        rows.append({
            "año":      year,
            "mes":      month,
            "variable": _VARIABLE,
            "valor":    round(float(val), 2),
            "fuente":   (
                "World Bank — Commodity Markets 'Pink Sheet', Monthly Prices, "
                f"'{_COLUMN}' (USD/bbl). {used_url}"
            ),
        })

    out = pd.DataFrame(rows).sort_values(["año", "mes"]).reset_index(drop=True)
    if not out.empty:
        print(f"  Pink Sheet: {len(out)} meses de {_VARIABLE} "
              f"({out['año'].min()} a {out['año'].max()}-{int(out['mes'].iloc[-1]):02d})")
    return out


if __name__ == "__main__":
    print("=" * 65)
    print("  World Bank Pink Sheet — crudo Dubai mensual")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_wb_commodities_monthly()
    if df.empty:
        if OUTPUT.exists():
            print("\n  Sin datos nuevos. Se conserva el CSV existente.")
        else:
            print("\n  0 filas. wb_commodities_monthly.csv NO creado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} filas)")
