"""
IMF IMTS — Comercio espejo mensual EE.UU. ↔ Venezuela (mirror statistics).

Fuente OFICIAL: IMF — International Trade in Goods (by partner country),
dataset IMTS del portal de datos del FMI (sucesor de DOTS; el propio
dataset lleva la keyword "DOTS"):
    https://data.imf.org/en/datasets/IMF.STA:IMTS
    API SDMX 2.1: https://api.imf.org/external/sdmx/2.1/data/IMF.STA,IMTS/{key}

Principio de "mirror statistics": Venezuela dejó de reportar comercio de
forma confiable, pero sus socios SÍ reportan. Aquí se usa exclusivamente
lo que EE.UU. (mayor socio comercial historico) reporta a las autoridades
estadísticas — dato de origen NO venezolano:

  - USA.XG_FOB_USD.VEN.M  → exportaciones de EE.UU. hacia Venezuela
        = importaciones venezolanas desde EE.UU. (proxy de demanda interna)
  - USA.MG_CIF_USD.VEN.M  → importaciones de EE.UU. desde Venezuela
        = exportaciones venezolanas a EE.UU. (proxy de ingreso petrolero;
          captura la dinámica de licencias OFAC/Chevron desde 2023)

Variables de salida (millones de USD por mes):
  - importaciones_espejo_usa_musd  (dirección positiva en el Pulse)
  - exportaciones_espejo_usa_musd  (dirección positiva en el Pulse)

Política de datos: si el API no responde o un flujo no tiene datos, las
filas simplemente no se escriben (NaN aguas abajo). No se estima, no se
interpola, no se inventa.

Salida: data/raw/imts_monthly.csv
Formato: año | mes | variable | valor | fuente

Uso:
    python scripts/fetch_imts_monthly.py
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START_YEAR = 2010  # inicio del Pulse
END_YEAR   = _CFG["serie"]["end_year"]

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "imts_monthly.csv"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (academic research project ICIV)",
    "Accept": "application/xml",
}
_BASE = "https://api.imf.org/external/sdmx/2.1/data/IMF.STA,IMTS"

# (clave SDMX, variable de salida, descripción corta)
_SERIES = [
    (
        "USA.XG_FOB_USD.VEN.M",
        "importaciones_espejo_usa_musd",
        "Exportaciones EEUU hacia VEN (FOB) = importaciones venezolanas desde EEUU",
    ),
    (
        "USA.MG_CIF_USD.VEN.M",
        "exportaciones_espejo_usa_musd",
        "Importaciones EEUU desde VEN (CIF) = exportaciones venezolanas a EEUU",
    ),
]

_FUENTE = (
    "IMF — International Trade in Goods by partner country (IMTS, sucesor de DOTS), "
    "reportado por EEUU (mirror statistics, origen no venezolano). "
    "https://data.imf.org/en/datasets/IMF.STA:IMTS — clave {key}"
)


def _fetch_series(key: str, variable: str) -> pd.DataFrame:
    """Descarga una serie IMTS y devuelve filas año|mes|variable|valor|fuente."""
    url = f"{_BASE}/{key}?startPeriod={START_YEAR}-01&endPeriod={END_YEAR}-12"
    resp = requests.get(url, timeout=180, headers=_HEADERS)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    rows = []
    for obs in root.iter():
        if not obs.tag.endswith("Obs"):
            continue
        period = obs.get("TIME_PERIOD")   # formato '2023-M01'
        value  = obs.get("OBS_VALUE")
        if not period or value is None:
            continue
        try:
            year_str, month_str = period.split("-M")
            year, month = int(year_str), int(month_str)
            val_musd = round(float(value) / 1e6, 2)  # USD → millones USD
        except (ValueError, AttributeError):
            continue
        if not (START_YEAR <= year <= END_YEAR):
            continue
        rows.append({
            "año":      year,
            "mes":      month,
            "variable": variable,
            "valor":    val_musd,
            "fuente":   _FUENTE.format(key=key),
        })
    return pd.DataFrame(rows)


def fetch_imts_monthly() -> pd.DataFrame:
    """Descarga los dos flujos espejo EEUU-Venezuela. Sin datos inventados."""
    frames = []
    for key, variable, desc in _SERIES:
        try:
            df = _fetch_series(key, variable)
            if df.empty:
                print(f"  [WARN] IMTS {key}: 0 observaciones — {variable} quedara NaN")
            else:
                print(f"  IMTS {key}: {len(df)} meses "
                      f"({df['año'].min()}-{df['mes'][df['año'].idxmin()]:02d} a "
                      f"{df['año'].max()}-{df['mes'][df['año'].idxmax()]:02d}) — {desc}")
                frames.append(df)
        except Exception as exc:
            print(f"  [ERROR] IMTS {key}: {exc} — {variable} quedara NaN")

    if not frames:
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["variable", "año", "mes"]).reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 65)
    print("  IMF IMTS — comercio espejo mensual EEUU-Venezuela")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_imts_monthly()
    if df.empty:
        if OUTPUT.exists():
            print("\n  0 filas nuevas. Se conserva el CSV existente (no se inventa nada).")
        else:
            print("\n  0 filas. imts_monthly.csv NO creado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} filas, "
              f"{df['variable'].nunique()} variables)")
