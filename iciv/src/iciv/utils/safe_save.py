"""Escritura protegida de CSV para los fetchers.

Motivo (incidencia 2026-08-03): `fetch_guardian.py` recorria anio por anio,
registraba None cuando la peticion fallaba y al terminar escribia el CSV
igualmente. Cuando la clave de la API dejo de servir fallaron los 27 anios y el
script sobrescribio 27 anios de datos buenos con NaN, saliendo con codigo 0.
D6 Perceccion Internacional (10% del indice) dejo de aportar durante ocho dias
sin que nada avisara.

La politica del proyecto es no fabricar datos cuando una fuente falla. Destruir
los que ya existen es peor: conserva la apariencia de un pipeline sano mientras
vacia el indice. `save_dataframe` cierra ese hueco.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class NoDataError(RuntimeError):
    """La descarga no trajo ningun valor utilizable; no se escribio nada."""


def save_dataframe(
    df: pd.DataFrame,
    path: Path | str,
    *,
    value_columns: list[str] | None = None,
    strict: bool = True,
) -> bool:
    """Escribe `df` en `path` solo si trae al menos un valor real.

    Args:
        df: datos a guardar.
        path: destino del CSV.
        value_columns: columnas que deben tener algun valor. Si es None, se
            consideran todas menos las de indice temporal (`anio`/`año`, `mes`).
        strict: si True lanza NoDataError cuando no hay datos; si False solo
            registra el aviso y devuelve False.

    Returns:
        True si escribio, False si no habia datos y `strict` era False.

    Raises:
        NoDataError: si no hay ningun valor y `strict` es True.
    """
    path = Path(path)

    if value_columns is None:
        excluir = {"año", "anio", "year", "mes", "month", "fecha", "fuente"}
        value_columns = [c for c in df.columns if c.lower() not in excluir]

    presentes = [c for c in value_columns if c in df.columns]
    n_validos = int(df[presentes].notna().sum().sum()) if presentes else 0

    if df.empty or n_validos == 0:
        mensaje = (
            f"{path.name}: la descarga no trajo ningun valor "
            f"({len(df)} filas, 0 datos). NO se sobrescribe el archivo existente."
        )
        if strict:
            raise NoDataError(mensaje)
        logger.warning("  %s", mensaje)
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info("  OK %s (%d filas, %d valores)", path.name, len(df), n_validos)
    return True
