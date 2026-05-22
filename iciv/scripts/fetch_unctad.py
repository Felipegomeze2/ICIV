"""
Liner Shipping Connectivity Index (LSCI) — Venezuela.

El LSCI mide el grado de integración de un país en las redes globales de
transporte marítimo de contenedores. Es un indicador oficial publicado
anualmente por la UNCTAD y también disponible como indicador derivado
en el World Development Indicators (WDI) del Banco Mundial.

Fuente primaria: World Bank WDI — indicador IS.SHP.GCNW.XQ
  (Liner Shipping Connectivity Index, UNCTAD, calculado en base 2006=China 100)
  API: https://api.worldbank.org/v2/country/VEN/indicator/IS.SHP.GCNW.XQ
  Cobertura Venezuela: 2006–2021 (16 años de datos reales)
  Años 2022 en adelante: NaN (no reportado aún en WDI)
  Años 2000–2005: NaN (serie no existía — LSCI comenzó en 2004/2006)

Nota sobre el API UNCTAD Stat:
  El endpoint https://unctadstat.unctad.org/api/v1/en/data/MT_TMS_LSCI_I/VEN
  devuelve HTTP 404 (comprobado mayo 2026). Se usa WDI como fuente alternativa
  verificable y pública.

Principio de datos: si WDI no tiene datos para un año, ese año queda NaN.
NO se usan estimaciones manuales ni datos estáticos inventados.

Salida: data/raw/unctad.csv
  Columnas: año, lsci_conectividad_maritima
  (solo años con datos reales del WDI; sin valores para años sin cobertura)

Uso:
    python scripts/fetch_unctad.py
"""

from __future__ import annotations

import sys
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
OUTPUT = settings.paths.raw_unctad

# World Bank WDI indicator for LSCI
WB_INDICATOR = "IS.SHP.GCNW.XQ"
WB_COUNTRY   = _CFG["serie"]["country_wb"]
WB_BASE_URL  = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"


def _fetch_wb_lsci() -> dict[int, float]:
    """
    Descarga LSCI Venezuela desde el World Bank WDI API.
    Retorna dict {año: valor} solo con años que tienen datos reales.
    """
    url = WB_BASE_URL.format(country=WB_COUNTRY, indicator=WB_INDICATOR)
    params = {
        "format": "json",
        "per_page": 100,
        "mrv": 30,
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        if not isinstance(payload, list) or len(payload) < 2:
            raise ValueError(f"Respuesta inesperada del WB API: {str(payload)[:200]}")

        records = payload[1]
        if not records:
            raise ValueError("WB API devolvió 0 registros para IS.SHP.GCNW.XQ / VEN")

        results: dict[int, float] = {}
        for rec in records:
            year_str = rec.get("date")
            value    = rec.get("value")
            if year_str is not None and value is not None:
                try:
                    yr = int(year_str)
                    if START <= yr <= END:
                        results[yr] = round(float(value), 2)
                except (ValueError, TypeError):
                    continue

        return results

    except requests.RequestException as exc:
        raise RuntimeError(f"Error HTTP al consultar WB WDI LSCI: {exc}") from exc


def fetch_unctad() -> pd.DataFrame:
    """
    Descarga LSCI Venezuela desde World Bank WDI (IS.SHP.GCNW.XQ).
    Solo retorna años con datos reales. NaN para años sin cobertura.
    """
    print("  Fuente: World Bank WDI (IS.SHP.GCNW.XQ)")
    data = _fetch_wb_lsci()

    if not data:
        print("  ADVERTENCIA: WB API devolvió 0 años para LSCI Venezuela.")
        print("  La variable lsci_conectividad_maritima quedará NaN en el pipeline.")
        return pd.DataFrame(columns=["año", "lsci_conectividad_maritima"])

    rows = []
    for year in range(START, END + 1):
        val = data.get(year)
        if val is not None:
            rows.append({"año": year, "lsci_conectividad_maritima": val})

    df = pd.DataFrame(rows)
    return df.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Descargando LSCI Venezuela via World Bank WDI ({START}–{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_unctad()
    if not df.empty:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"Guardado: {OUTPUT}  ({len(df)} años con datos reales)")
        print(f"  Período cubierto: {int(df['año'].min())} – {int(df['año'].max())}")
        print(df.to_string(index=False))
    else:
        print(f"No se guardó archivo (0 años de datos).")
        print("La variable lsci_conectividad_maritima será NaN en el pipeline.")
