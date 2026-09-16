"""Atomic source writes: an incomplete refresh never silently erases history."""
from __future__ import annotations
import logging
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class NoDataError(RuntimeError):
    """Invalid or destructive download; the previous file remains untouched."""

def save_dataframe(df: pd.DataFrame, path: Path | str, *,
                   value_columns: list[str] | None = None, strict: bool = True,
                   allow_loss: bool = False) -> bool:
    """Validate and atomically replace a snapshot, without filling missing cells.

    Partial new datasets are valid. Losing an existing published cell is not.
    allow_loss is only for explicitly rolling collections or an audited revision.
    """
    path = Path(path)
    keys = [c for c in df if c.lower() in {
        "año", "anio", "year", "mes", "month", "fecha", "date", "variable",
        "estado", "state", "iso3", "country", "region", "url",
    }]
    if value_columns is None:
        values = [c for c in df if c not in keys and c.lower() not in {
            "fuente", "source", "unidad", "unit", "status", "nota",
        } and pd.to_numeric(df[c], errors="coerce").notna().any()]
        if "valor" in df:
            values = ["valor"]
    else:
        values = [c for c in value_columns if c in df]
    def reject(message: str) -> bool:
        message = f"{path.name}: {message}. Archivo anterior conservado; actualización fallida."
        if strict:
            raise NoDataError(message)
        logger.warning(message)
        return False
    if df.empty or not values or not df[values].notna().any().any():
        return reject("sin observaciones utilizables")
    numeric = df[values].select_dtypes(include="number")
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        return reject("valores infinitos")
    if keys and (df[keys].isna().any().any() or df.duplicated(keys).any()):
        return reject("claves nulas o duplicadas")
    if path.exists() and not allow_loss:
        old = pd.read_csv(path)
        if not keys or not set(keys).issubset(old.columns):
            return reject("no se puede verificar la conservación del histórico por clave")
        if old.duplicated(keys).any():
            return reject("histórico con claves duplicadas; requiere revisión explícita")
        old_indexed = old.set_index(keys)
        new_indexed = df.set_index(keys).reindex(old_indexed.index)
        old_values = [c for c in old_indexed if pd.to_numeric(old_indexed[c], errors="coerce").notna().any()]
        lost = 0
        for col in old_values:
            observed = pd.to_numeric(old_indexed[col], errors="coerce").notna()
            if col not in new_indexed:
                lost += int(observed.sum())
            else:
                lost += int((observed & new_indexed[col].isna()).sum())
        if lost:
            return reject(f"la descarga perdería {lost} observaciones publicadas")
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8-sig", newline="",
                                         dir=path.parent, suffix=".tmp", delete=False) as tmp:
            name = tmp.name
            df.to_csv(tmp, index=False, lineterminator="\n")
        os.replace(name, path)
    finally:
        if name and Path(name).exists():
            Path(name).unlink()
    logger.info("  OK %s (%d filas)", path.name, len(df))
    return True
