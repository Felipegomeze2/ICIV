"""
UN Comtrade — comercio espejo mensual de socios adicionales con Venezuela.

Fuente: UN Comtrade Database, API oficial v1
    https://comtradeapi.un.org/data/v1/get/{typeCode}/{freqCode}/{clCode}
    Portal y suscripcion: https://comtradedeveloper.un.org

Principio "mirror statistics": igual que el IMTS (EEUU), pero ampliando la
base de socios que reportan su comercio con Venezuela. Los datos los
reportan las aduanas de los SOCIOS — origen NO venezolano.

Socios espejo (codigo M49 del reporter):
    724 Espana | 76 Brasil | 699 India | 792 Turkiye | 156 China

Variables de salida (millones de USD por mes, suma de los 5 socios que
hayan reportado ese mes):
  - importaciones_espejo_socios_musd : exportaciones de los socios hacia VEN
        (= importaciones venezolanas desde esos socios)
  - exportaciones_espejo_socios_musd : importaciones de los socios desde VEN
        (= exportaciones venezolanas hacia esos socios)

Rol en el proyecto: capa auxiliar de contexto y validacion del bloque de
comercio espejo del Pulse (que usa IMF IMTS/EEUU). NO entra al score ni al
Pulse mientras no se decida peso y se re-ejecute el backtest.

Credenciales: variable de entorno COMTRADE_API_KEY o iciv/.env (ignorado
por git). Tier gratuito: ~500 llamadas/dia — este script usa ~85 llamadas
(1 por reporter-ano, ambos flujos juntos).

Politica de datos: meses sin reporte de un socio simplemente no suman ese
socio; si el API falla se conserva el CSV previo. Sin datos inventados.

Salida: data/raw/comtrade_monthly.csv
Formato: año | mes | variable | valor | fuente

Uso:
    python scripts/fetch_comtrade_monthly.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

_ICIV_DIR = Path(__file__).resolve().parents[1]
_CFG = yaml.safe_load((_ICIV_DIR / "config" / "settings.yaml").read_text(encoding="utf-8"))

START_YEAR = 2010
END_YEAR   = _CFG["serie"]["end_year"]

OUTPUT = _ICIV_DIR / "data" / "raw" / "comtrade_monthly.csv"

_BASE_URL = "https://comtradeapi.un.org/data/v1/get/C/M/HS"
_HEADERS  = {"User-Agent": "Mozilla/5.0 (academic research project ICIV)"}

_VEN_M49 = 862
_REPORTERS = {
    724: "Espana",
    76:  "Brasil",
    699: "India",
    792: "Turkiye",
    156: "China",
}

_FUENTE = (
    "UN Comtrade API v1 (comtradeapi.un.org), comercio mensual HS TOTAL "
    "reportado por {socios} con Venezuela (M49 862). Mirror statistics, "
    "origen no venezolano."
).format(socios=", ".join(_REPORTERS.values()))


def _load_key() -> str | None:
    """Lee COMTRADE_API_KEY del entorno o de iciv/.env. Nunca la imprime."""
    env_file = _ICIV_DIR / ".env"
    if os.environ.get("COMTRADE_API_KEY"):
        return os.environ["COMTRADE_API_KEY"]
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "COMTRADE_API_KEY":
                val = val.strip().strip('"').strip("'")
                if val:
                    return val
    return None


def _fetch_year(key: str, reporter: int, year: int) -> pd.DataFrame:
    """Una llamada: ambos flujos (X, M) de un reporter con VEN, 12 meses."""
    periods = ",".join(f"{year}{m:02d}" for m in range(1, 13))
    params = {
        "reporterCode": reporter,
        "partnerCode": _VEN_M49,
        "period": periods,
        "flowCode": "X,M",
        "cmdCode": "TOTAL",
        "subscription-key": key,
    }
    resp = requests.get(_BASE_URL, params=params, headers=_HEADERS, timeout=90)
    if resp.status_code == 429:
        time.sleep(10)
        resp = requests.get(_BASE_URL, params=params, headers=_HEADERS, timeout=90)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return pd.DataFrame(data) if data else pd.DataFrame()


def fetch_comtrade_monthly() -> pd.DataFrame:
    """Descarga comercio espejo mensual de los 5 socios. Sin datos inventados."""
    key = _load_key()
    if key is None:
        print(
            "  [WARN] COMTRADE_API_KEY no configurada.\n"
            "  Definirla como variable de entorno o en iciv/.env\n"
            "  (Primary key de comtradedeveloper.un.org). No se escribe nada nuevo."
        )
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    frames = []
    errores = 0
    for reporter, nombre in _REPORTERS.items():
        for year in range(START_YEAR, END_YEAR + 1):
            try:
                df = _fetch_year(key, reporter, year)
                if not df.empty:
                    frames.append(df)
                time.sleep(1.2)  # cortesia con el rate limit del tier gratuito
            except Exception as exc:
                errores += 1
                print(f"  [WARN] Comtrade {nombre} {year}: {exc}")
                if errores >= 8:
                    print("  [ERROR] Demasiados errores consecutivos del API — se detiene.")
                    break
        else:
            print(f"  Comtrade {nombre}: descargado")
            continue
        break

    if not frames:
        print("  [WARN] Comtrade devolvio 0 registros.")
        return pd.DataFrame(columns=["año", "mes", "variable", "valor", "fuente"])

    ev = pd.concat(frames, ignore_index=True)
    ev["primaryValue"] = pd.to_numeric(ev["primaryValue"], errors="coerce")
    ev = ev.dropna(subset=["primaryValue"])
    ev["period"] = ev["period"].astype(str)
    ev["año"] = ev["period"].str[:4].astype(int)
    ev["mes"] = ev["period"].str[4:6].astype(int)

    rows = []
    for (year, month), grp in ev.groupby(["año", "mes"]):
        exp_socios = grp[grp["flowCode"] == "X"]["primaryValue"].sum()  # socios → VEN
        imp_socios = grp[grp["flowCode"] == "M"]["primaryValue"].sum()  # VEN → socios
        if exp_socios > 0:
            rows.append({
                "año": int(year), "mes": int(month),
                "variable": "importaciones_espejo_socios_musd",
                "valor": round(float(exp_socios) / 1e6, 2),
                "fuente": _FUENTE,
            })
        if imp_socios > 0:
            rows.append({
                "año": int(year), "mes": int(month),
                "variable": "exportaciones_espejo_socios_musd",
                "valor": round(float(imp_socios) / 1e6, 2),
                "fuente": _FUENTE,
            })

    out = pd.DataFrame(rows).sort_values(["variable", "año", "mes"]).reset_index(drop=True)
    if not out.empty:
        n_meses = out[["año", "mes"]].drop_duplicates().shape[0]
        print(f"  Comtrade: {len(ev)} registros → {n_meses} meses agregados "
              f"({out['año'].min()}-{out['año'].max()})")
    return out


if __name__ == "__main__":
    print("=" * 65)
    print("  UN Comtrade — comercio espejo mensual socios-Venezuela")
    print("=" * 65)
    settings.paths.ensure_exists()
    df = fetch_comtrade_monthly()
    if df.empty:
        if OUTPUT.exists():
            print("\n  Sin datos nuevos. Se conserva el CSV existente.")
        else:
            print("\n  0 filas. comtrade_monthly.csv NO creado.")
    else:
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  Guardado: {OUTPUT}  ({len(df)} filas)")
