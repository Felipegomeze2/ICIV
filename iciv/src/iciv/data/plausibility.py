"""Controles de plausibilidad sobre valores publicados por los proveedores.

Un proveedor internacional puede publicar valores que son imposibles para la
serie que dicen medir. El caso documentado: el API del Banco Mundial devuelve
``0`` para ``NE.EXP.GNFS.ZS`` (exportaciones de bienes y servicios, % del PIB)
de Venezuela entre 1995 y 2011. Un exportador de petróleo no puede tener
exportaciones nulas; ese cero es un marcador de ausencia, no una medición.

Reglas:

* ``valor_imposible``: el valor se excluye (pasa a NaN) antes de transformar y
  normalizar. El valor original queda en el archivo crudo del proveedor y en el
  registro ``plausibilidad_proveedor.csv``. No se reemplaza por ninguna otra
  cifra: el año queda sin dato y la cobertura lo refleja.
* ``valor_repetido``: rachas largas de valores idénticos en series que no
  deberían ser constantes. Solo se **marcan**; el valor no se cambia, porque
  descartarlo es una decisión metodológica del autor y no una corrección.

El módulo no crea, interpola ni sustituye observaciones.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

REGISTRY_FILENAME = "plausibilidad_proveedor.csv"
REGISTRY_COLUMNS = ["año", "variable", "valor_proveedor", "regla", "accion", "detalle"]


@dataclass(frozen=True)
class ImpossibleValueRule:
    """Valor que la serie no puede tomar; se excluye del cálculo."""
    variable: str
    value: float
    reason: str


@dataclass(frozen=True)
class RepeatedValueRule:
    """Racha de valores idénticos en una serie continua; solo se marca."""
    variable: str
    min_run: int
    reason: str


IMPOSSIBLE_VALUE_RULES: tuple[ImpossibleValueRule, ...] = (
    ImpossibleValueRule(
        "exportaciones_pct_pib", 0.0,
        "Banco Mundial NE.EXP.GNFS.ZS publica 0 para Venezuela 1995-2011; "
        "un exportador de petróleo no puede tener exportaciones nulas.",
    ),
)

REPEATED_VALUE_RULES: tuple[RepeatedValueRule, ...] = (
    RepeatedValueRule(
        "mortalidad_infantil_x1000", 5,
        "Banco Mundial SP.DYN.IMRT.IN repite el mismo valor durante años "
        "consecutivos; probable arrastre del proveedor, no medición anual.",
    ),
    RepeatedValueRule("esperanza_vida_anos", 5, "Serie demográfica continua."),
    RepeatedValueRule("hdi", 5, "Índice compuesto continuo."),
)


def _runs(values: pd.Series) -> list[tuple[int, int]]:
    """Posiciones (inicio, fin) de rachas de valores idénticos no nulos."""
    runs: list[tuple[int, int]] = []
    start = 0
    arr = values.to_numpy(dtype=float)
    for i in range(1, len(arr) + 1):
        same = i < len(arr) and not np.isnan(arr[i]) and not np.isnan(arr[start]) and arr[i] == arr[start]
        if not same:
            if not np.isnan(arr[start]) and i - start > 1:
                runs.append((start, i - 1))
            start = i
    return runs


def apply_plausibility(master: pd.DataFrame, year_col: str = "año") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Excluye valores imposibles y marca rachas repetidas.

    Devuelve el panel con los valores imposibles convertidos en NaN y el
    registro de cada observación afectada. El panel de entrada no se modifica.
    """
    out = master.copy()
    records: list[dict] = []
    for rule in IMPOSSIBLE_VALUE_RULES:
        if rule.variable not in out.columns:
            continue
        values = pd.to_numeric(out[rule.variable], errors="coerce")
        mask = values.eq(rule.value)
        for idx in out.index[mask]:
            records.append({
                year_col: int(out.at[idx, year_col]), "variable": rule.variable,
                "valor_proveedor": float(values.at[idx]), "regla": "valor_imposible",
                "accion": "excluido_del_calculo", "detalle": rule.reason,
            })
        out.loc[mask, rule.variable] = np.nan
    for rule in REPEATED_VALUE_RULES:
        if rule.variable not in out.columns:
            continue
        ordered = out.sort_values(year_col)
        values = pd.to_numeric(ordered[rule.variable], errors="coerce").reset_index(drop=True)
        years = ordered[year_col].reset_index(drop=True)
        for start, end in _runs(values):
            length = end - start + 1
            if length < rule.min_run:
                continue
            for pos in range(start, end + 1):
                records.append({
                    year_col: int(years.iloc[pos]), "variable": rule.variable,
                    "valor_proveedor": float(values.iloc[pos]), "regla": "valor_repetido",
                    "accion": "marcado_sin_cambio",
                    "detalle": f"{rule.reason} Racha de {length} años "
                               f"({int(years.iloc[start])}-{int(years.iloc[end])}).",
                })
    registry = pd.DataFrame(records, columns=REGISTRY_COLUMNS)
    return out, registry
