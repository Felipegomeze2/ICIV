"""Observation-level lineage without inventing publication dates or source status."""
from __future__ import annotations
import pandas as pd
import hashlib
from functools import lru_cache
from pathlib import Path
from iciv.data.catalog import CATALOG

SOURCE_FILES = {
    "WDI": "wdi.csv", "IMF": "imf.csv", "EIA": "eia.csv", "FRED": "fred.csv",
    "WGI": "wgi.csv", "CPI": "cpi.csv", "HDI": "hdi.csv", "GUARDIAN": "guardian.csv",
    "UNHCR": "unhcr.csv", "UNCTAD": "unctad.csv", "WJP": "wjp.csv",
    "FREEDOM_HOUSE": "freedom_house.csv", "VIIRS": "blackmarble_qa_monthly.csv",
}

@lru_cache(maxsize=32)
def _read_audit(path, modified):
    return pd.read_csv(path)

@lru_cache(maxsize=128)
def _sha(path, modified, size, canonical=False):
    data = Path(path).read_bytes()
    return hashlib.sha256(data.replace(b"\r\n", b"\n") if canonical else data).hexdigest()

def _current_sha(path, canonical=False):
    stat = path.stat()
    return _sha(str(path), stat.st_mtime_ns, stat.st_size, canonical)

def verified_metadata(variable, year, value, settings):
    """Apply metadata only to the raw bytes and numeric value actually audited."""
    path = settings.paths.data_raw.parent / "sources/audit_20260917/verified_observations.csv"
    if not path.exists() or pd.isna(value):
        return {}
    data = _read_audit(str(path), path.stat().st_mtime_ns)
    selected = data[data.variable.eq(variable) & data["año"].eq(year)]
    if len(selected) != 1:
        return {}
    row = selected.iloc[0]
    raw = settings.paths.data_raw / row.archivo_origen
    evidence = path.parent / row.evidencia
    if (not raw.exists() or not evidence.exists()
            or (_current_sha(raw) != row.raw_sha256 and _current_sha(raw, True) != row.get("raw_canonical_lf_sha256"))
            or _current_sha(evidence) != row.evidence_sha256
            or abs(float(value)-float(row.valor_verificado)) > 1e-8):
        return {}
    return {"estado_observacion": row.estado_observacion,
            "fecha_publicacion": row.fecha_publicacion if pd.notna(row.fecha_publicacion) else None,
            "fecha_publicacion_estado": "fecha_del_vintage_auditado" if pd.notna(row.fecha_publicacion) else "no_archivada",
            "evidencia_verificacion": row.evidencia, "url_verificacion": row.url}

def observation_metadata(variable, year, value, settings):
    meta = CATALOG[variable]
    filename = SOURCE_FILES.get(meta.source.value, "")
    status = "publicado_por_proveedor_estado_no_desagregado"
    method = "identidad"
    if variable == "empleo_vulnerable_oit_pct":
        filename = "ilostat.csv"
        status = "estimacion_modelada_OIT_distribuida_WDI"
    if meta.source.value == "IMF":
        status = "WEO_estimaciones_y_proyecciones_estado_individual_no_verificado"
    if variable == "luminosidad_nocturna_idx":
        status = "derivado_satelital_quality0_mas_de3_observaciones"
        method = "media_de_meses_publicados_minimo_3"
    if variable == "inflacion_ipc_imf_pct":
        method = "log10_porcentaje_positivo; no se imputan valores no positivos"
    if variable == "tipo_cambio_oficial_lcu_usd":
        method = "log10_BsF_equivalente;2018_2021:x1e5;2022_en_adelante:x1e11"
    months = None
    partial = settings.paths.data_processed / "anualizacion_parcial.csv"
    if partial.exists():
        data = pd.read_csv(partial)
        selected = data[(data["año"] == year) & (data["variable"] == variable)]
        if not selected.empty:
            months = int(selected.iloc[0]["meses_usados"])
            status = "agregado_mensual_parcial" if months < 12 else "agregado_mensual_12_meses"
            filename = "eia_monthly.csv" if variable.startswith("petroleo_") else filename
    if pd.isna(value):
        status = "sin_dato"
    result = {
        "unidad_original": "LCU/USD en denominacion del proveedor" if variable == "tipo_cambio_oficial_lcu_usd" else meta.unit,
        "archivo_origen": filename,
        "estado_observacion": status,
        "transformacion": method,
        "meses_usados": months,
        "fecha_publicacion": None,
        "fecha_publicacion_estado": "no_archivada; no inferir del periodo ni del mtime",
        "imputado_por_proyecto": False,
    }
    if months is None:
        result.update(verified_metadata(variable, year, value, settings))
    return result
