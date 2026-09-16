"""
Liner Shipping Connectivity Index (LSCI) — Venezuela.

El LSCI mide el grado de integración de un país en las redes globales de
transporte marítimo de contenedores. Lo publica la UNCTAD trimestralmente.

Fuente PRIMARIA (2026-07): UNCTADstat Data Centre, bulk download oficial
    https://unctadstat.unctad.org/datacentre/dataviewer/US.LSCI
    https://unctadstat-api.unctad.org/bulkdownload/US.LSCI/US_LSCI
  Archivo 7z con CSV trimestral, base "Average Q1 2023 = 100".
  Cobertura Venezuela: 2006Q1 → presente (a jul-2026: hasta 2026Q2).
  Agregación anual: promedio de los trimestres realmente publicados de cada
  año (sin imputar trimestres faltantes). El año en curso usa los trimestres
  disponibles y la fuente lo declara.

Fuente única: UNCTADstat. Si la descarga no responde o falta py7zr,
se lanza un error y se conserva el archivo previo. Nunca se sustituye la
serie por WDI, cuya base y cobertura no son equivalentes.

Principio de datos: si una fuente no tiene datos para un año, ese año queda
NaN. NO se usan estimaciones manuales ni datos inventados.

Salida: data/raw/unctad.csv
  Columnas: año, lsci_conectividad_maritima, fuente

Uso:
    python scripts/fetch_unctad.py
"""

from __future__ import annotations

import io
import sys
import tempfile
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

_HEADERS = {"User-Agent": "Mozilla/5.0 (academic research project ICIV)"}

# UNCTADstat bulk (primaria)
_UNCTAD_BULK_URL = "https://unctadstat-api.unctad.org/bulkdownload/US.LSCI/US_LSCI"
_UNCTAD_CITA = (
    "UNCTADstat US.LSCI trimestral (base Q1 2023=100), promedio de trimestres "
    "publicados {qs}. https://unctadstat.unctad.org/datacentre/dataviewer/US.LSCI"
)

def _fetch_unctadstat() -> pd.DataFrame | None:
    """Serie anual desde el bulk trimestral oficial de UNCTADstat."""
    try:
        import py7zr
    except ImportError:
        print("  [ERROR] py7zr no instalado; UNCTAD no actualizado")
        return None

    try:
        resp = requests.get(_UNCTAD_BULK_URL, timeout=120, headers=_HEADERS)
        resp.raise_for_status()
        tmp = tempfile.mkdtemp()
        with py7zr.SevenZipFile(io.BytesIO(resp.content)) as z:
            names = z.getnames()
            z.extractall(tmp)
        csv_path = Path(tmp) / names[0]
        df = pd.read_csv(csv_path)

        eco_col = next(c for c in df.columns if "Economy Label" in c)
        idx_col = next(c for c in df.columns if c.startswith("Index ("))
        q_col   = "Quarter" if "Quarter" in df.columns else df.columns[0]

        ven = df[df[eco_col].astype(str).str.contains("Venezuela", case=False, na=False)].copy()
        if ven.empty:
            print("  [WARN] UNCTADstat: Venezuela no encontrada")
            return None

        ven["valor_q"] = pd.to_numeric(ven[idx_col], errors="coerce")
        ven = ven.dropna(subset=["valor_q"])
        ven["año"] = ven[q_col].astype(str).str[:4].astype(int)
        ven["trimestre"] = ven[q_col].astype(str).str[-2:].astype(int)

        rows = []
        for year, grp in ven.groupby("año"):
            if not (START <= year <= END):
                continue
            qs = sorted(grp["trimestre"].tolist())
            qs_label = "Q" + "-Q".join(str(q) for q in qs) if len(qs) < 4 else "Q1-Q4"
            rows.append({
                "año": int(year),
                "lsci_conectividad_maritima": round(float(grp["valor_q"].mean()), 2),
                "fuente": _UNCTAD_CITA.format(qs=qs_label),
            })
        out = pd.DataFrame(rows).sort_values("año").reset_index(drop=True)
        print(f"  UNCTADstat: {len(out)} años "
              f"({int(out['año'].min())}-{int(out['año'].max())}), "
              f"{len(ven)} trimestres reales")
        return out if not out.empty else None
    except Exception as exc:
        print(f"  [WARN] UNCTADstat bulk fallo: {exc}")
        return None


def fetch_unctad() -> pd.DataFrame:
    """LSCI Venezuela anual. Una sola fuente por serie; jamás se mezclan bases."""
    df = _fetch_unctadstat()
    if df is None or df.empty:
        raise RuntimeError("UNCTADstat no disponible; unctad.csv no actualizado.")
    return df


if __name__ == "__main__":
    print(f"Descargando LSCI Venezuela ({START}–{END}) ...")
    settings.paths.ensure_exists()

    df = fetch_unctad()
    if not df.empty:
        from iciv.utils import save_dataframe
        save_dataframe(df, OUTPUT)
        print(f"Guardado: {OUTPUT}  ({len(df)} años con datos reales)")
        print(df[["año", "lsci_conectividad_maritima"]].to_string(index=False))
    else:
        print("No se guardó archivo (0 años de datos).")
