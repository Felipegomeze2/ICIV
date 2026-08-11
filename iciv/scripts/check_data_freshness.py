"""Control de vigencia de TODAS las fuentes del ICIV.

Por que existe
--------------
En el workflow cada fetcher va envuelto en `|| echo WARN`, de modo que un fallo
no aborta la corrida. Eso es deseable —no queremos perder el dashboard porque
una API este caida— pero deja un punto ciego: el paso reporta "success" aunque
media fuente haya fallado, y nadie lee los logs. Entre el 3 y el 11 de agosto de
2026 el indice se publico ocho dias sin la dimension D6 sin que nada avisara.

Este script no comprueba si el fetcher termino bien: comprueba el RESULTADO, que
es lo que importa. Mira el ultimo dato de cada CSV y lo compara con el rezago
maximo tolerable de esa fuente. Asi detecta tanto "el fetch fallo" como "el fetch
funciono pero devolvio datos viejos", que el codigo de salida no distingue.

Tolerancias
-----------
Cada fuente tiene su calendario. No es lo mismo FRED, que publica en tiempo real,
que el HDR del PNUD, que se refiere a dos anios atras por construccion. Las
tolerancias reflejan el calendario REAL de cada publicador, verificado en agosto
de 2026; no son deseos.

Salida
------
- Tabla legible por consola.
- Si corre en GitHub Actions, escribe un resumen en $GITHUB_STEP_SUMMARY (se ve
  en la portada del run, sin abrir logs) y emite anotaciones ::warning:: /
  ::error:: que quedan visibles en la interfaz.
- Codigo de salida 1 si alguna fuente CRITICA esta fuera de tolerancia.

Uso:
    python scripts/check_data_freshness.py
    python scripts/check_data_freshness.py --strict   # falla tambien con avisos
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

_RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


@dataclass(frozen=True)
class Fuente:
    archivo: str
    etiqueta: str
    frecuencia: str          # "mensual" | "anual"
    max_rezago: int          # meses si mensual, anios si anual
    critica: bool
    nota: str = ""


# Tolerancias segun el calendario REAL de cada publicador (verificado 2026-08).
FUENTES: list[Fuente] = [
    # ── Mensuales ────────────────────────────────────────────────────────────
    Fuente("fred_monthly.csv", "FRED (macro global + aduana EEUU)", "mensual", 3, True,
           "las globales son diarias; las de aduana llegan a 2 meses"),
    Fuente("guardian_monthly.csv", "Guardian", "mensual", 2, True, "API en vivo"),
    Fuente("gdelt_monthly.csv", "GDELT", "mensual", 3, False,
           "opcional: rate limit por frecuencia de peticiones"),
    Fuente("eia_monthly.csv", "EIA International (petroleo)", "mensual", 6, True,
           "EIA publica el mes t alrededor de t+4"),
    Fuente("wb_commodities_monthly.csv", "WB Pink Sheet", "mensual", 3, False, ""),
    Fuente("blackmarble_monthly.csv", "NASA Black Marble", "mensual", 4, True,
           "alimenta la luminosidad del score anual"),
    Fuente("comtrade_monthly.csv", "UN Comtrade", "mensual", 5, False, "capa auxiliar"),
    Fuente("imts_monthly.csv", "IMF IMTS", "mensual", 7, False,
           "capa auxiliar desde 2026-08: el Pulse usa las series FRED de aduana"),
    Fuente("acled_monthly.csv", "ACLED", "mensual", 14, False,
           "el tier gratuito entrega con ~12 meses de rezago"),

    # ── Anuales ──────────────────────────────────────────────────────────────
    Fuente("wdi.csv", "World Bank WDI", "anual", 2, True, "publica en diciembre"),
    Fuente("wgi.csv", "World Bank WGI", "anual", 2, True, "publica en septiembre"),
    Fuente("imf.csv", "IMF WEO", "anual", 1, True, "dos ediciones al anio"),
    Fuente("eia.csv", "EIA anual", "anual", 2, True, ""),
    Fuente("guardian.csv", "Guardian anual", "anual", 1, True,
           "alimenta D6; su caida vacio el indice en agosto de 2026"),
    Fuente("cpi.csv", "Transparency CPI", "anual", 2, True, "publica en enero"),
    Fuente("freedom_house.csv", "Freedom House", "anual", 2, True, "publica en febrero"),
    Fuente("wjp.csv", "World Justice Project", "anual", 2, True, "publica en octubre"),
    Fuente("pts.csv", "Political Terror Scale", "anual", 3, False, "rezago habitual de ~1 anio"),
    Fuente("hdi.csv", "UNDP HDI", "anual", 3, False,
           "el HDR se refiere a t-2 por construccion; 2023 es lo ultimo publicado"),
    Fuente("unctad.csv", "UNCTAD LSCI", "anual", 2, True, "trimestral agregada"),
    Fuente("ilostat.csv", "ILOSTAT", "anual", 3, False, ""),
    Fuente("unhcr.csv", "UNHCR", "anual", 2, True, ""),
    Fuente("viirs.csv", "Li et al. (validacion externa)", "anual", 3, False,
           "ya no alimenta el score; se conserva como validador no circular"),
]


def _ultimo_periodo(archivo: str) -> tuple[int, int] | None:
    """Devuelve (anio, mes) del ultimo dato real. mes=12 para series anuales."""
    ruta = _RAW / archivo
    if not ruta.exists():
        return None
    try:
        d = pd.read_csv(ruta)
    except Exception:
        return None
    if "año" not in d.columns or d.empty:
        return None

    # Descarta filas sin ningun valor real
    if "valor" in d.columns:
        d = d.dropna(subset=["valor"])
    else:
        medibles = [c for c in d.columns if c not in ("año", "mes", "fuente", "pais",
                                                      "indicador", "variable", "unidad")]
        if medibles:
            d = d.dropna(subset=medibles, how="all")
    if d.empty:
        return None

    anio = int(d["año"].max())
    if "mes" in d.columns:
        mes = int(d[d["año"] == anio]["mes"].max())
    else:
        mes = 12
    return anio, mes


def evaluar(hoy: date | None = None) -> list[dict]:
    hoy = hoy or date.today()
    filas = []
    for f in FUENTES:
        ult = _ultimo_periodo(f.archivo)
        if ult is None:
            filas.append({"fuente": f.etiqueta, "archivo": f.archivo, "ultimo": "SIN DATOS",
                          "rezago": None, "limite": f.max_rezago, "critica": f.critica,
                          "estado": "FALLO", "nota": f.nota})
            continue
        anio, mes = ult
        if f.frecuencia == "mensual":
            rezago = (hoy.year - anio) * 12 + (hoy.month - mes)
            etiqueta_ult = f"{anio}-{mes:02d}"
            unidad = "meses"
        else:
            rezago = hoy.year - anio
            etiqueta_ult = str(anio)
            unidad = "anios"
        if rezago > f.max_rezago:
            estado = "FALLO" if f.critica else "AVISO"
        else:
            estado = "OK"
        filas.append({"fuente": f.etiqueta, "archivo": f.archivo, "ultimo": etiqueta_ult,
                      "rezago": rezago, "unidad": unidad, "limite": f.max_rezago,
                      "critica": f.critica, "estado": estado, "nota": f.nota})
    return filas


def main() -> int:
    ap = argparse.ArgumentParser(description="Control de vigencia de las fuentes del ICIV")
    ap.add_argument("--strict", action="store_true",
                    help="devuelve error tambien cuando hay avisos en fuentes no criticas")
    args = ap.parse_args()

    filas = evaluar()
    fallos = [f for f in filas if f["estado"] == "FALLO"]
    avisos = [f for f in filas if f["estado"] == "AVISO"]

    ICONO = {"OK": "OK ", "AVISO": "!  ", "FALLO": "XX "}
    print("=" * 88)
    print("  CONTROL DE VIGENCIA DE FUENTES")
    print("=" * 88)
    print(f"  {'':3s} {'fuente':40s} {'ultimo':>9s} {'rezago':>8s} {'limite':>7s}")
    print("  " + "-" * 84)
    for f in filas:
        rez = f"{f['rezago']} {f.get('unidad','')}" if f["rezago"] is not None else "--"
        marca = "*" if f["critica"] else " "
        print(f"  {ICONO[f['estado']]}{marca}{f['fuente']:39s} {f['ultimo']:>9s} "
              f"{rez:>8s} {f['limite']:>7d}")
    print("  " + "-" * 84)
    print(f"  * = fuente critica    |    {len(filas)} fuentes    "
          f"{len(fallos)} fallos    {len(avisos)} avisos")

    # ── Anotaciones y resumen para GitHub Actions ────────────────────────────
    if os.environ.get("GITHUB_ACTIONS") == "true":
        for f in fallos:
            print(f"::error title=Fuente critica desactualizada::{f['fuente']} "
                  f"({f['archivo']}): ultimo dato {f['ultimo']}, "
                  f"rezago {f['rezago']} > limite {f['limite']}")
        for f in avisos:
            print(f"::warning title=Fuente con rezago::{f['fuente']} "
                  f"({f['archivo']}): ultimo dato {f['ultimo']}, "
                  f"rezago {f['rezago']} > limite {f['limite']}")

        resumen = os.environ.get("GITHUB_STEP_SUMMARY")
        if resumen:
            with open(resumen, "a", encoding="utf-8") as fh:
                fh.write("## Vigencia de fuentes ICIV\n\n")
                if fallos:
                    fh.write(f"**{len(fallos)} fuente(s) critica(s) fuera de tolerancia.**\n\n")
                elif avisos:
                    fh.write(f"{len(avisos)} aviso(s) en fuentes no criticas. "
                             "Ninguna critica falla.\n\n")
                else:
                    fh.write("Todas las fuentes dentro de su tolerancia.\n\n")
                fh.write("| | Fuente | Ultimo dato | Rezago | Limite |\n")
                fh.write("|---|---|---:|---:|---:|\n")
                emoji = {"OK": "✅", "AVISO": "⚠️", "FALLO": "❌"}
                for f in filas:
                    rez = f"{f['rezago']} {f.get('unidad','')}" if f["rezago"] is not None else "—"
                    nombre = f["fuente"] + (" *" if f["critica"] else "")
                    fh.write(f"| {emoji[f['estado']]} | {nombre} | {f['ultimo']} | "
                             f"{rez} | {f['limite']} |\n")
                fh.write("\n`*` fuente critica. El limite refleja el calendario real "
                         "del publicador, no un deseo.\n")

    if fallos:
        print("\n  RESULTADO: hay fuentes CRITICAS desactualizadas. Revisar el fetch.")
        return 1
    if avisos and args.strict:
        print("\n  RESULTADO: hay avisos y --strict esta activo.")
        return 1
    print("\n  RESULTADO: sin fuentes criticas desactualizadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
