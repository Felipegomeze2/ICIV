"""Lectura de credenciales desde el entorno o desde iciv/.env.

El repositorio no guarda claves. Cada fetcher las toma de una variable de
entorno (en GitHub Actions vienen de los secrets) o, en local, de `iciv/.env`,
que está en .gitignore.

El parser tolera espacios alrededor del `=` y comillas alrededor del valor,
porque los archivos .env escritos a mano suelen traerlos.
"""

from __future__ import annotations

import os
from pathlib import Path

# iciv/src/iciv/utils/env.py -> parents[3] == iciv/
_ICIV_DIR = Path(__file__).resolve().parents[3]
_ENV_FILE = _ICIV_DIR / ".env"


def load_env_key(name: str, default: str = "") -> str:
    """Devuelve el valor de `name` desde el entorno o iciv/.env.

    Nunca imprime ni registra el valor. Si no existe, devuelve `default`.
    """
    valor = os.environ.get(name)
    if valor:
        return valor.strip()

    if _ENV_FILE.exists():
        # utf-8-sig: PowerShell en Windows escribe BOM con frecuencia
        for linea in _ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, _, val = linea.partition("=")
            if clave.strip() == name:
                val = val.strip().strip('"').strip("'")
                if val:
                    return val

    return default
