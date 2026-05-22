"""
Conectividad Aérea Internacional de Venezuela — OpenSky Network API.

Fuente: OpenSky Network REST API (acceso libre, sin key)
        https://opensky-network.org/api/flights/arrival
        Cobertura real: ~2016 en adelante (datos ADS-B).

Métrica: número de aerolíneas distintas con vuelos de llegada registrados
en al menos un aeropuerto venezolano principal durante una semana
representativa de octubre de cada año.

NOTA IMPORTANTE: OpenSky no tiene datos históricos anteriores a ~2016.
Para años sin cobertura ADS-B disponible (2000-2015), la variable queda
NaN. No existe fuente reproducible y gratuita para esos años.

Aeropuertos monitoreados (ICAO):
  SVMI — Aeropuerto Internacional Simón Bolívar (Maiquetía)
  SVVA — Aeropuerto Internacional Arturo Michelena (Valencia)
  SVBC — Aeropuerto Internacional General José Antonio Anzoátegui (Barcelona)
  SVMC — Aeropuerto Internacional La Chinita (Maracaibo)
  SVMG — Aeropuerto Internacional José Tadeo Monagas (Maturín)

Salida: data/raw/opensky.csv
Formato: año | vuelos_aerolineas_int_count | fuente

Uso:
    python scripts/fetch_opensky.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, date
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
OUTPUT = settings.paths.raw_opensky

# Aeropuertos venezolanos principales (ICAO)
_AIRPORTS = ["SVMI", "SVVA", "SVBC", "SVMC", "SVMG"]

# OpenSky cubre desde ~2016 (datos ADS-B históricos)
OPENSKY_COVERAGE_START = 2016


def _opensky_unique_airlines(airport: str, year: int) -> set[str] | None:
    """
    Consulta la primera semana completa de octubre de cada año en OpenSky
    para obtener callsigns únicos de aerolíneas llegando a un aeropuerto.
    Retorna None si la API no responde o no hay datos.
    """
    try:
        begin_dt = datetime(year, 10, 2)
        end_dt   = datetime(year, 10, 9)
        begin_ts = int(begin_dt.timestamp())
        end_ts   = int(end_dt.timestamp())
    except ValueError:
        return None

    url = "https://opensky-network.org/api/flights/arrival"
    params = {"airport": airport, "begin": begin_ts, "end": end_ts}
    try:
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            # Callsign: primeros 3 caracteres = código ICAO de aerolínea
            airlines = {
                f["callsign"][:3]
                for f in data
                if f.get("callsign") and len(f.get("callsign", "")) >= 3
            }
            return airlines
        elif resp.status_code == 429:
            print("    Rate limit OpenSky — esperando 5s...")
            time.sleep(5)
    except Exception as exc:
        print(f"    OpenSky error ({airport} {year}): {exc}")
    return None


def fetch_opensky() -> pd.DataFrame:
    """
    Descarga datos reales de OpenSky API para años 2016+.
    Retorna solo filas con datos verificables. Sin fallbacks estáticos.
    Años sin cobertura ADS-B (2000-2015) → no se incluyen (NaN en pipeline).
    """
    current_year = date.today().year
    rows = []

    for year in range(max(START, OPENSKY_COVERAGE_START), min(END, current_year - 1) + 1):
        all_airlines: set[str] = set()
        year_ok = False

        for airport in _AIRPORTS[:2]:  # SVMI + SVVA — los que tienen más tráfico
            result = _opensky_unique_airlines(airport, year)
            if result is not None:
                all_airlines.update(result)
                year_ok = True
            time.sleep(0.4)

        if year_ok and all_airlines:
            # Filtrar prefijos que no son aerolíneas comerciales
            # (militares YV*, privados de un solo carácter, matrícula venezolana)
            comerciales = {
                c for c in all_airlines
                if c.isalpha() and len(c) == 3 and c not in {"YVA", "YVB", "YVC"}
            }
            if comerciales:
                rows.append({
                    "año": year,
                    "vuelos_aerolineas_int_count": len(comerciales),
                    "fuente": (
                        f"OpenSky Network API — llegadas SVMI+SVVA semana Oct {year} "
                        f"(https://opensky-network.org)"
                    ),
                })
                print(f"  {year}: {len(comerciales)} aerolíneas únicas (OpenSky)")
            else:
                print(f"  {year}: sin callsigns comerciales válidos en OpenSky")
        else:
            print(f"  {year}: sin respuesta de OpenSky — año omitido (NaN)")

    if not rows:
        print(
            "\n  ADVERTENCIA: OpenSky no devolvio datos.\n"
            "  La variable vuelos_aerolineas_int_count quedara NaN para todos los anyos.\n"
            "  Esto es correcto segun la regla del proyecto: sin dato real -> NaN."
        )
        return pd.DataFrame(columns=["año", "vuelos_aerolineas_int_count", "fuente"])

    df = pd.DataFrame(rows)
    return df.sort_values("año").reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 60)
    print(f"  OpenSky — Conectividad Aérea Venezuela ({START}–{END})")
    print(f"  Cobertura real API: {OPENSKY_COVERAGE_START}+")
    print(f"  Años 2000-{OPENSKY_COVERAGE_START-1}: NaN (sin datos ADS-B históricos)")
    print("=" * 60)
    settings.paths.ensure_exists()

    df = fetch_opensky()

    if df.empty:
        print("\n  0 años con datos reales.")
        print("  opensky.csv no actualizado (se mantiene el anterior si existe).")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} años reales)")
        print(df[["año", "vuelos_aerolineas_int_count"]].to_string(index=False))
