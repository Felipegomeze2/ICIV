"""
EIA International (monthly) — datos mensuales de producción petrolera Venezuela.

Fuente: U.S. Energy Information Administration (EIA) International Energy Data
        https://www.eia.gov/international/data/

Variable: petroleo_crudo_produccion_tbpd (Total petroleum and liquids, TBPD)

Frecuencia: Mensual (a diferencia de fetch_eia.py que descarga anual agregada)

Propósito académico:
  El indicador ICIV es anual, pero para el año en curso (2026) los promedios
  anuales agregados están incompletos. Esta fuente mensual permite:
  1. Validar el dato anual de EIA (debería ser ~promedio de los 12 meses)
  2. Aportar un "nowcast" para 2026 promediando solo los meses disponibles
  3. Cobertura intra-anual auditable (qué mes se incluyó)

Cobertura confirmada (consulta 2026-05-12):
  - 2020-01 a 2026-01: 73 observaciones mensuales
  - Próximos meses se publican con lag de ~3-4 meses

Método: API key gratuita EIA en .env (EIA_API_KEY)

Salida: data/raw/eia_monthly.csv
  Columnas: año | mes | productId | productName | valor | unidad | fuente

Uso:
    python scripts/fetch_eia_monthly.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

_CFG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
_CFG = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8"))

START = _CFG["serie"]["start_year"]
END   = _CFG["serie"]["end_year"]
OUTPUT_MONTHLY = Path(__file__).resolve().parents[1] / "data" / "raw" / "eia_monthly.csv"

_EIA_BASE = "https://api.eia.gov/v2/international/data/"
# Product IDs (verificados via api.eia.gov/v2/international/facet/productId)
_PRODUCTS = {
    53: "petroleo_crudo_produccion_tbpd",  # Total petroleum and other liquids
    55: "gas_natural_plant_liquids_tbpd",  # Natural gas plant liquids
}


def _api_key() -> str:
    """Lee EIA_API_KEY del .env o entorno."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("EIA_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("EIA_API_KEY", "")


def fetch_eia_monthly() -> pd.DataFrame:
    """
    Descarga datos mensuales EIA International para Venezuela.

    Returns:
        DataFrame con columnas: año, mes, productId, productName, valor, unidad, fuente
    """
    api_key = _api_key()
    if not api_key:
        raise RuntimeError("EIA_API_KEY no encontrado en .env")

    rows: list[dict] = []
    for pid, var_name in _PRODUCTS.items():
        url = (
            f"{_EIA_BASE}?frequency=monthly&data[0]=value"
            f"&facets[productId][]={pid}"
            f"&facets[countryRegionId][]=VEN"
            f"&start={START}-01&end={END}-12"
            f"&api_key={api_key}"
            f"&length=5000"
        )
        try:
            resp = requests.get(url, timeout=45)
            resp.raise_for_status()
            data = resp.json().get("response", {}).get("data", [])
            print(f"  Producto {pid} ({var_name}): {len(data)} meses")
            for d in data:
                period = d["period"]  # YYYY-MM
                if not period or "-" not in period:
                    continue
                year, mes = period.split("-")
                try:
                    rows.append({
                        "año": int(year),
                        "mes": int(mes),
                        "productId": pid,
                        "productName": d.get("productName", ""),
                        "variable": var_name,
                        "valor": float(d["value"]) if d.get("value") else None,
                        "unidad": d.get("unit", ""),
                        "fuente": (
                            "U.S. Energy Information Administration (EIA), "
                            "International Energy Statistics, monthly series. "
                            "https://www.eia.gov/international/data/"
                        ),
                    })
                except (ValueError, TypeError):
                    continue
        except Exception as exc:
            print(f"  Error en producto {pid}: {exc}")

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values(["productId", "año", "mes"]).reset_index(drop=True)
    return df


def aggregate_to_annual(df_monthly: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega datos mensuales a anuales para integrar con el pipeline.

    Para el año en curso (incompleto), calcula el promedio de meses disponibles
    y guarda metadata sobre cuántos meses se usaron (transparencia).
    """
    if df_monthly.empty:
        return pd.DataFrame(columns=["año", "indicador", "valor", "pais", "fuente"])

    # Solo producto 53 (Total petroleum and liquids) para el pipeline
    df = df_monthly[df_monthly["productId"] == 53].copy()
    df = df.dropna(subset=["valor"])

    agg = (
        df.groupby("año")
          .agg(valor=("valor", "mean"),
               n_meses=("mes", "count"),
               meses_lista=("mes", lambda s: ",".join(map(str, sorted(s)))))
          .reset_index()
    )

    rows = []
    for _, r in agg.iterrows():
        yr = int(r["año"])
        n_meses = int(r["n_meses"])
        completeness = (
            f"{n_meses}/12 meses ({r['meses_lista']})"
            if n_meses < 12 else "12/12 meses (año completo)"
        )
        rows.append({
            "año": yr,
            "indicador": "petroleo_crudo_produccion_tbpd",
            "valor": round(float(r["valor"]), 2),
            "pais": "Venezuela",
            "fuente": (
                f"EIA International monthly aggregated. Cobertura intra-anual: {completeness}. "
                f"https://www.eia.gov/international/data/"
            ),
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("=" * 65)
    print("  EIA International (monthly) - Venezuela petroleo")
    print("  Fuente: U.S. Energy Information Administration")
    print("=" * 65)

    df_monthly = fetch_eia_monthly()
    if df_monthly.empty:
        print("\n  0 datos mensuales. eia_monthly.csv NO actualizado.")
        sys.exit(1)

    # Guardar mensual
    OUTPUT_MONTHLY.parent.mkdir(parents=True, exist_ok=True)
    df_monthly.to_csv(OUTPUT_MONTHLY, index=False, encoding="utf-8-sig")
    print(f"\n  Guardado mensual: {OUTPUT_MONTHLY}  ({len(df_monthly)} filas)")

    # Agregado anual (último de cada año)
    df_annual = aggregate_to_annual(df_monthly)
    print(f"\n  Agregado anual ({len(df_annual)} anos):")
    for _, r in df_annual.iterrows():
        print(f"    {r['año']}: {r['valor']:.1f} TBPD")
