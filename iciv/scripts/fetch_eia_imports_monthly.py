"""
EIA — importaciones mensuales de EE.UU. desde Venezuela (crudo y productos).

Fuente: U.S. Energy Information Administration (EIA), Petroleum & Other Liquids,
        "U.S. Imports by Country of Origin" (API v2, ruta petroleum/move/impcus).

Series (verificadas el 2026-10-09 contra la descripción que devuelve la API):
  MCRIMUSVE2  U.S. Imports from Venezuela of Crude Oil (Thousand Barrels per Day)
  MTPIMUSVE2  U.S. Imports from Venezuela of Total Petroleum Products (Thousand Barrels per Day)

Son registros de aduana de EE.UU. (socio comercial), no estadísticas venezolanas.
Durante el embargo petrolero (mediados de 2019 a 2023) la EIA no publica valor
para la mayoría de los meses: esos meses quedan SIN DATO. No se convierten en
cero aunque la ausencia de importaciones sea plausible, porque el proveedor no
publica la cifra. Cada fila conserva la descripción y la unidad que publica la
EIA, para que la identidad de la serie quede auditada en el propio CSV.

Corrige el bloque de comercio del Pulse: entre el 2026-08-11 y el 2026-10-09 el
proyecto descargaba por error las series FRED IR14270/IR14260, que son índices de
precios de importación de oro no monetario y de zinc, no importaciones desde
Venezuela. Ver docs/INCIDENTE_SERIES_COMERCIO.md.

Credencial: EIA_API_KEY desde el entorno o iciv/.env (nunca versionada).

Salida: data/raw/eia_imports_monthly.csv
  Columnas: año | mes | variable | valor | unidad | serie_eia | descripcion_eia | fuente
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.utils import save_dataframe  # noqa: E402
from iciv.utils.env import load_env_key  # noqa: E402

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "eia_imports_monthly.csv"
START = "2010-01"
_URL = "https://api.eia.gov/v2/petroleum/move/impcus/data/"
SERIES = {
    "MCRIMUSVE2": ("importaciones_eeuu_crudo_ven_tbpd",
                   "U.S. Imports from Venezuela of Crude Oil"),
    "MTPIMUSVE2": ("importaciones_eeuu_productos_ven_tbpd",
                   "U.S. Imports from Venezuela of Total Petroleum Products"),
}
_SOURCE = ("U.S. Energy Information Administration (EIA), U.S. Imports by Country of Origin. "
           "https://www.eia.gov/dnav/pet/pet_move_impcus_a2_nus_ep00_im0_mbblpd_m.htm")


def fetch_eia_imports_monthly() -> pd.DataFrame:
    api_key = load_env_key("EIA_API_KEY")
    if not api_key:
        raise RuntimeError("EIA_API_KEY no encontrada; CSV no actualizado")
    rows: list[dict] = []
    for series_id, (variable, expected) in SERIES.items():
        params = {"api_key": api_key, "frequency": "monthly", "data[0]": "value",
                  "facets[series][]": series_id, "start": START, "length": 5000}
        try:
            resp = requests.get(_URL, params=params, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            # No se propaga la URL: contiene la credencial.
            raise RuntimeError(f"EIA {series_id}: descarga fallida ({type(exc).__name__}); CSV no actualizado") from None
        data = resp.json().get("response", {}).get("data", [])
        if not data:
            raise RuntimeError(f"EIA {series_id}: sin observaciones; CSV no actualizado")
        for d in data:
            description = str(d.get("series-description", ""))
            # La identidad de la serie se verifica en cada descarga: si la EIA
            # cambiara el contenido del código, no se acepta en silencio.
            if not description.startswith(expected):
                raise RuntimeError(f"EIA {series_id}: descripción inesperada '{description}'")
            period = str(d.get("period", ""))
            value = d.get("value")
            if "-" not in period or value in (None, "", "--", "NA"):
                continue
            year, month = period.split("-")[:2]
            rows.append({"año": int(year), "mes": int(month), "variable": variable,
                         "valor": float(value), "unidad": d.get("units", ""),
                         "serie_eia": series_id, "descripcion_eia": description,
                         "fuente": _SOURCE})
        print(f"  {series_id} ({variable}): {sum(r['serie_eia'] == series_id for r in rows)} meses")
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["variable", "año", "mes"]).drop_duplicates(
        subset=["año", "mes", "variable"], keep="last").reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 65)
    print("  EIA - Importaciones de EE.UU. desde Venezuela (mensual)")
    print("=" * 65)
    frame = fetch_eia_imports_monthly()
    if frame.empty:
        print("  0 filas. eia_imports_monthly.csv NO actualizado.")
        sys.exit(1)
    save_dataframe(frame, OUTPUT, value_columns=["valor"])
    print(f"  Guardado: {OUTPUT} ({len(frame)} filas, hasta "
          f"{int(frame['año'].max())}-{int(frame.loc[frame['año'].eq(frame['año'].max()), 'mes'].max()):02d})")
