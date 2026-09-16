"""Empleo vulnerable: estimación modelada OIT distribuida por WDI.

Serie única: SL.EMP.VULN.ZS, trabajadores por cuenta propia y familiares
auxiliares como porcentaje del empleo total. No mide empleo informal.
El nombre del script se conserva por compatibilidad con los workflows.
No se consultan proxies ni fuentes alternativas. Una descarga fallida lanza
un error y conserva el CSV anterior sin presentarlo como una descarga nueva.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402
from iciv.utils import save_dataframe  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))
START = _CFG["serie"]["start_year"]
END = _CFG["serie"]["end_year"]
OUTPUT = settings.paths.raw_ilostat
INDICATOR = "SL.EMP.VULN.ZS"
VARIABLE = "empleo_vulnerable_oit_pct"
URL = f"https://api.worldbank.org/v2/country/VEN/indicator/{INDICATOR}"
SOURCE = (
    "OIT, estimacion modelada; distribuida por World Bank WDI SL.EMP.VULN.ZS. "
    "Empleo vulnerable (% del empleo total): trabajadores por cuenta propia "
    "y familiares auxiliares. No equivale a informalidad. "
    "https://data.worldbank.org/indicator/SL.EMP.VULN.ZS"
)


def fetch_ilostat() -> pd.DataFrame:
    """Descarga exclusivamente empleo vulnerable; nunca evalúa bool(DataFrame)."""
    response = requests.get(
        URL, params={"format": "json", "per_page": 100, "date": f"{START}:{END}"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        raise RuntimeError("WDI SL.EMP.VULN.ZS sin datos; ilostat.csv no actualizado.")
    rows = []
    for record in payload[1]:
        if record.get("value") is None:
            continue
        year = int(record["date"])
        if START <= year <= END:
            rows.append({
                "año": year, "indicador": VARIABLE,
                "valor": round(float(record["value"]), 2),
                "pais": "Venezuela", "fuente": SOURCE,
            })
    if not rows:
        raise RuntimeError("WDI SL.EMP.VULN.ZS sin valores en el periodo configurado.")
    result = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
    if result["año"].duplicated().any():
        raise ValueError("WDI SL.EMP.VULN.ZS devolvio años duplicados.")
    return result


if __name__ == "__main__":
    settings.paths.ensure_exists()
    result = fetch_ilostat()
    save_dataframe(result, OUTPUT, value_columns=["valor"])
    print(f"Guardado empleo vulnerable OIT/WDI: {len(result)} años.")
