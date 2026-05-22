"""
Configuración centralizada del sistema de logging del ICIV.

Proporciona dos handlers:
  - Consola: nivel INFO, formato conciso
  - Archivo:  nivel DEBUG, formato completo con timestamp

Uso:
    from iciv.utils.logging_config import setup_logging
    setup_logging()           # configuración default
    setup_logging(level="DEBUG", log_file=Path("logs/run.log"))
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    logger_name: str = "iciv",
) -> logging.Logger:
    """
    Configura y retorna el logger raíz del proyecto.

    Args:
        level:       nivel mínimo para la consola ('DEBUG', 'INFO', 'WARNING')
        log_file:    ruta al archivo de log. Si None, solo escribe en consola.
        logger_name: nombre del logger (default: 'iciv')
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt_console = logging.Formatter("%(levelname)-8s %(name)s — %(message)s")
    fmt_file    = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s:%(lineno)d — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler de consola
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, level.upper()))
    console.setFormatter(fmt_console)
    logger.addHandler(console)

    # Handler de archivo (opcional)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt_file)
        logger.addHandler(file_handler)

    return logger


def get_timestamped_log_path(base_dir: Path, prefix: str = "iciv") -> Path:
    """Genera una ruta de log con timestamp, ej. logs/iciv_20260416_143022.log"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base_dir / f"{prefix}_{ts}.log"
