"""
Descarga datos de Google Trends para Venezuela como proxy de percepción global.

Fuente: Google Trends via pytrends
Salida: data/raw/gtrends.csv
Formato: año|indicador|valor|pais|fuente

Requiere: pip install pytrends

Metodología:
  Google Trends mide el interés relativo de búsqueda (0-100) para un término
  dado, normalizado respecto al máximo histórico del período analizado.

  Queries utilizadas (promedio anual):
  1. "Venezuela inversión" — interés en invertir en Venezuela
  2. "Venezuela economy"   — cobertura angloparlante del estado económico
  3. "invertir Venezuela"  — búsquedas en español de inversión

  El score final es el promedio anual de los tres queries, luego promediado
  entre sí. Un score alto = mayor interés global en Venezuela como economía.

  Interpretación de dirección POSITIVA:
  Mayor interés de búsqueda correlaciona con períodos de transición,
  negociación o apertura — no necesariamente con crisis (que generan búsquedas
  de noticias, no de "inversión"). Esta dirección es validada en la literatura
  de nowcasting económico (Choi & Varian, 2012; Askitas & Zimmermann, 2009).

Cita: Choi, H., & Varian, H. (2012). Predicting the present with Google Trends.
      The Economic Journal, 122(556), 306-328.

Uso:
    pip install pytrends
    python scripts/fetch_gtrends.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START    = _CFG["serie"]["start_year"]
END      = _CFG["serie"]["end_year"]
QUERIES  = _CFG["sources"]["gtrends"]["queries"]
OUTPUT   = settings.paths.raw_gtrends


def build_gtrends() -> pd.DataFrame:
    """
    Descarga Google Trends via pytrends y retorna DataFrame con valores reales.
    Falla con RuntimeError si pytrends no está instalado o la API no responde.
    No usa datos de fallback — solo datos descargados directamente de Google.
    """
    try:
        from pytrends.request import TrendReq  # type: ignore
    except ImportError:
        raise RuntimeError(
            "pytrends no está instalado.\n"
            "Instálalo con: pip install pytrends\n"
            "Esta variable (google_trends_vzla) no tendrá datos hasta que se instale."
        )

    pytrends = TrendReq(hl="es-VE", tz=360, timeout=(10, 25))
    annual_scores: dict[int, list[float]] = {y: [] for y in range(START, END + 1)}
    errors: list[str] = []

    for query in QUERIES:
        print(f"  Consultando: '{query}' ...")
        try:
            for chunk_start in range(START, END + 1, 5):
                chunk_end = min(chunk_start + 4, END)
                timeframe = f"{chunk_start}-01-01 {chunk_end}-12-31"
                pytrends.build_payload(
                    kw_list=[query],
                    cat=0,
                    timeframe=timeframe,
                    geo="",
                    gprop="",
                )
                df_chunk = pytrends.interest_over_time()
                if df_chunk.empty:
                    continue

                df_chunk["year"] = df_chunk.index.year
                yearly = df_chunk.groupby("year")[query].mean()
                for yr, val in yearly.items():
                    if START <= yr <= END:
                        annual_scores[yr].append(float(val))

                time.sleep(2)

        except Exception as exc:
            errors.append(f"'{query}': {exc}")
            print(f"    ERROR en '{query}': {exc}")

    if errors:
        print(f"  ADVERTENCIA: {len(errors)} queries fallaron: {errors}")

    result = {}
    for yr, vals in annual_scores.items():
        if vals:
            result[yr] = round(sum(vals) / len(vals), 2)

    if not result:
        raise RuntimeError(
            "Google Trends API no devolvió ningún dato.\n"
            "Verifica tu conexión a internet y que pytrends pueda acceder a Google.\n"
            "Esta variable no tendrá datos en el pipeline."
        )

    df = pd.DataFrame(list(result.items()), columns=["año", "google_trends_vzla"])
    df = df.sort_values("año").reset_index(drop=True)

    # Convertir a formato largo estándar del pipeline
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "año":       int(row["año"]),
            "indicador": "google_trends_vzla",
            "valor":     row["google_trends_vzla"],
            "pais":      "Venezuela",
            "fuente":    "Google Trends — pytrends API",
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(f"Descargando Google Trends Venezuela ({START}-{END}) ...")
    settings.paths.ensure_exists()

    try:
        df = build_gtrends()
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"Guardado: {OUTPUT}  ({len(df)} años)")
        print(df[["año", "valor"]].tail(10).to_string(index=False))
    except RuntimeError as e:
        print(f"\n[ERROR] Google Trends no disponible:\n{e}")
        print("El pipeline continuará sin esta variable (quedará como NaN).")
