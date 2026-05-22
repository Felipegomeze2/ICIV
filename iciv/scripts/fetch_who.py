"""
Indicadores de Salud de Venezuela desde la API de la OMS (WHO GHO).

Fuente: WHO Global Health Observatory (GHO) — OData API v1
  https://www.who.int/data/gho/info/gho-odata-api
  Endpoint base: https://ghoapi.azureedge.net/api/
  Acceso: público, sin autenticación requerida.

Indicadores descargados:
  1. WHOSIS_000001 — Esperanza de vida al nacer (ambos sexos)
     Cobertura Venezuela: 2000–2021 (22 años)
     Fuente: OMS World Health Statistics; registros civiles Venezuela.
     Unidades: años

  2. MDG_0000000001 — Tasa de mortalidad infantil (0-11 meses, ambos sexos)
     Cobertura Venezuela: 2000–2023 (24 años)
     Fuente: UN Inter-agency Group for Child Mortality Estimation (IGME).
     Unidades: muertes por 1,000 nacidos vivos

Nota metodológica:
  Los datos de la OMS para Venezuela en los últimos años (2016+) son estimaciones
  basadas en modelos estadísticos dado que el MPPS (Ministerio de Salud)
  suspendió la publicación de boletines epidemiológicos entre 2016 y 2019.
  La OMS los publica igualmente usando métodos de estimación indirecta.

Relevancia para el ICIV:
  Captura el colapso del sistema de salud venezolano:
  - Esperanza de vida cayó de ~74.7 años (2006) a ~70.0 (2020) — retroceso de
    25 años de progreso, el mayor de América Latina.
  - Mortalidad infantil aumentó del 15 al 25 por mil entre 2012 y 2020
    (reversión del descenso histórico), documentada por ENCOVI/IIES-UCAB.
  Estas variables capturan el deterioro del bienestar humano que no aparece en
  el PIB ni en otros indicadores económicos convencionales.

Citas:
  WHO (2024). Global Health Observatory Data Repository.
  https://www.who.int/data/gho
  UNICEF/WHO/World Bank/UNPD (2024). Levels and Trends in Child Mortality 2024.
  ENCOVI (2023). Encuesta de Condiciones de Vida Venezuela. IIES-UCAB, Caracas.

Salida: data/raw/who.csv (formato largo: año|indicador|valor|pais|fuente)

Uso:
    python scripts/fetch_who.py
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
OUTPUT = settings.paths.raw_who

GHO_BASE = "https://ghoapi.azureedge.net/api"

# Indicadores a descargar: (código GHO, nombre_columna_iciv, filtros adicionales)
_INDICATORS = [
    (
        "WHOSIS_000001",
        "esperanza_vida_anos",
        {"Dim1": "SEX_BTSX"},   # ambos sexos
        "WHO GHO — Life Expectancy at Birth (Both Sexes)",
    ),
    (
        "MDG_0000000001",
        "mortalidad_infantil_x1000",
        {"Dim1": "SEX_BTSX", "Dim2": "AGEGROUP_MONTHS0-11"},  # ambos sexos, 0-11 meses
        "WHO GHO / UN IGME — Infant Mortality Rate (Both Sexes, 0-11 months)",
    ),
]


def _fetch_indicator(code: str, col_name: str, filters: dict, fuente: str) -> list[dict]:
    """Descarga todos los registros de un indicador GHO y filtra para Venezuela."""
    url = f"{GHO_BASE}/{code}"
    try:
        resp = requests.get(url, timeout=45)
        resp.raise_for_status()
        items = resp.json().get("value", [])
    except Exception as exc:
        print(f"    [ERROR] {code}: {exc}")
        return []

    rows = []
    for item in items:
        if item.get("SpatialDim") != "VEN":
            continue
        yr = item.get("TimeDim")
        if yr is None or not (START <= int(yr) <= END):
            continue
        # Aplicar filtros adicionales (sexo, grupo de edad, etc.)
        skip = False
        for key, val in filters.items():
            if item.get(key) != val:
                skip = True
                break
        if skip:
            continue
        num_val = item.get("NumericValue")
        if num_val is None:
            continue
        rows.append({
            "año":       int(yr),
            "indicador": col_name,
            "valor":     round(float(num_val), 4),
            "pais":      "Venezuela",
            "fuente":    fuente,
        })

    return rows


def fetch_who() -> pd.DataFrame:
    """
    Descarga indicadores de salud de Venezuela desde la API WHO GHO.
    Retorna DataFrame largo con todos los indicadores.
    """
    all_rows: list[dict] = []

    for code, col_name, filters, fuente in _INDICATORS:
        print(f"  Descargando {code} ({col_name}) ...")
        rows = _fetch_indicator(code, col_name, filters, fuente)
        if rows:
            n = len(rows)
            yrs = sorted(set(r["año"] for r in rows))
            print(f"    OK: {n} años ({yrs[0]}-{yrs[-1]})")
            all_rows.extend(rows)
        else:
            print(f"    [WARN] {code}: sin datos para Venezuela en el rango solicitado.")

    if not all_rows:
        print("  [ERROR] WHO GHO: no se pudo obtener ningún indicador.")
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    df = pd.DataFrame(all_rows).sort_values(["indicador", "año"]).reset_index(drop=True)
    print(f"  Total WHO: {len(df)} registros ({df['indicador'].nunique()} indicadores)")
    return df


if __name__ == "__main__":
    print(f"Descargando WHO GHO Venezuela ({START}-{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_who()
    if df.empty:
        print("Sin datos disponibles.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"Guardado: {OUTPUT}  ({len(df)} registros)")
        for ind in df["indicador"].unique():
            sub = df[df["indicador"] == ind]
            print(f"\n  {ind} ({len(sub)} años):")
            print(sub[["año", "valor"]].to_string(index=False))
