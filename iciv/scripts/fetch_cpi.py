"""CPI 2012–2025 from the pinned official TI workbook; no manual scores."""
from pathlib import Path
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from audit_sources import cpi_values, retrieve, URLS, EVIDENCE
from iciv.utils import save_dataframe
OUTPUT = ROOT / "data/raw/cpi.csv"

def fetch_cpi():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = retrieve("cpi2025.xlsx", refresh=True)
    values = cpi_values(path)
    if set(values) != set(range(2012, 2026)):
        raise ValueError("CPI: cobertura del vintage oficial incompleta; no se actualiza")
    if any(not 0 <= value <= 100 for value in values.values()):
        raise ValueError("CPI: puntuacion fuera de escala")
    return pd.DataFrame([{"año": year, "indicador": "cpi_score", "valor": value,
                          "pais": "Venezuela", "fuente": "Transparency International CPI 2025; serie comparable 2012-2025: " + URLS["cpi2025.xlsx"]}
                         for year, value in sorted(values.items())])

if __name__ == "__main__":
    save_dataframe(fetch_cpi(), OUTPUT)
