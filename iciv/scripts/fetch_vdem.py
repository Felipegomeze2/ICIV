"""V-Dem — indices institucionales para VALIDACION CONVERGENTE del ICIV.

Que hace aqui
-------------
Estas series NO entran al indice. Son el validador externo de validez
convergente: miden un constructo vecino (calidad institucional) desde una
institucion independiente y con un metodo distinto, asi que sirven para
preguntarse si el ICIV mide clima de inversion o solo "Venezuela empeoro".

Por que V-Dem y no Heritage o Fraser
------------------------------------
El Index of Economic Freedom de Heritage y el Economic Freedom of the World de
Fraser serian validadores mas cercanos al constructo, pero ambos **bloquean la
descarga automatizada**: devuelven HTTP 403 a peticiones programaticas
(verificado el 2026-08-11, mismo comportamiento que el MOMR de la OPEP). Una
descarga manual no es reproducible y el proyecto exige que todo artefacto se
pueda regenerar desde cero.

V-Dem se distribuye por Our World in Data con licencia abierta y URL estable,
que es la misma via ya usada para el HDI.

Advertencia de circularidad
---------------------------
V-Dem comparte terreno con la dimension D3 del ICIV (CPI, WGI, Freedom House,
WJP, PTS). Correlacionar el ICIV COMPLETO contra V-Dem seria en parte circular.
Por eso `external_validation.py` reporta dos numeros: el ICIV completo y el
**ICIV recalculado sin D3**, que es el contraste limpio.

Salida: data/raw/vdem.csv   (formato largo: año | indicador | valor | pais | fuente)

Uso:
    python scripts/fetch_vdem.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
import requests

_ICIV_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ICIV_DIR / "src"))

from iciv.utils import save_dataframe  # noqa: E402

OUTPUT = _ICIV_DIR / "data" / "raw" / "vdem.csv"

_HDRS = {"User-Agent": "Mozilla/5.0 (compatible; ICIV-research/1.0)"}

# indicador_iciv -> (slug de OWID, fragmento del nombre de columna)
_SERIES = {
    "vdem_libdem_index":    ("liberal-democracy-index", "Liberal democracy"),
    "vdem_rule_of_law":     ("rule-of-law-index", "Rule of Law"),
    "vdem_corrupcion_pol":  ("political-corruption-index", "Political Corruption"),
}

_FUENTE = (
    "V-Dem Institute (Varieties of Democracy) via Our World in Data, "
    "https://ourworldindata.org/grapher/{slug} — validacion convergente, "
    "NO entra al indice ICIV"
)

_START_YEAR = 2000


def _fetch_serie(slug: str, fragmento: str) -> pd.Series:
    url = f"https://ourworldindata.org/grapher/{slug}.csv"
    r = requests.get(url, timeout=60, headers=_HDRS)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))

    col_pais = next((c for c in d.columns if c.lower() in ("entity", "country")), None)
    if col_pais is None:
        raise RuntimeError(f"{slug}: no encontre la columna de pais")

    ven = d[d[col_pais].astype(str).str.strip().str.lower() == "venezuela"]
    if ven.empty:
        raise RuntimeError(f"{slug}: sin filas de Venezuela")

    col_val = next((c for c in d.columns if fragmento.lower() in c.lower()), None)
    if col_val is None:
        candidatas = [c for c in d.columns if c not in (col_pais, "Code", "Year")]
        if len(candidatas) != 1:
            raise RuntimeError(f"{slug}: no identifique la columna de valor entre {candidatas}")
        col_val = candidatas[0]

    s = (ven[["Year", col_val]]
         .dropna(subset=[col_val])
         .astype({"Year": int})
         .set_index("Year")[col_val]
         .astype(float))
    return s[s.index >= _START_YEAR]


def fetch_vdem() -> pd.DataFrame:
    filas: list[dict] = []
    for indicador, (slug, fragmento) in _SERIES.items():
        print(f"  Descargando {slug} -> {indicador} ...", end=" ", flush=True)
        try:
            s = _fetch_serie(slug, fragmento)
            for anio, valor in s.items():
                filas.append({
                    "año": int(anio),
                    "indicador": indicador,
                    "valor": round(float(valor), 6),
                    "pais": "Venezuela",
                    "fuente": _FUENTE.format(slug=slug),
                })
            print(f"OK: {len(s)} anios ({int(s.index.min())}-{int(s.index.max())})")
        except Exception as exc:
            # No se fabrica sustituto: la serie simplemente no entra.
            print(f"FALLO: {exc}")

    return pd.DataFrame(filas).sort_values(["indicador", "año"]).reset_index(drop=True)


if __name__ == "__main__":
    print("Descargando indices V-Dem para validacion convergente ...")
    df = fetch_vdem()
    # save_dataframe no sobrescribe si la descarga vino vacia
    save_dataframe(df, OUTPUT, value_columns=["valor"])
    print(f"\nGuardado: {OUTPUT}")
    for ind, g in df.groupby("indicador"):
        print(f"  {ind:24s} {len(g):>3} anios  "
              f"{int(g['año'].min())}-{int(g['año'].max())}  "
              f"rango {g['valor'].min():.3f}-{g['valor'].max():.3f}")
