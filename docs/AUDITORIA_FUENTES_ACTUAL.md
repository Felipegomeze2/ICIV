# Auditoría de fuentes · septiembre de 2026

Se contrastaron **164 valores y todos coinciden** con la precisión almacenada. El resultado se limita al conjunto siguiente; no demuestra que todas las fuentes sean correctas ni que sean observaciones directas.

| Fuente | Evidencia archivada | Criterio |
|---|---|---|
| Transparency International | CPI2025_Results.xlsx, series 2012–2025 | Igualdad del score. Lectura del archivo oficial Strict OOXML sin convertir otras escalas. |
| World Justice Project | Historical Data File 2025 | Redondeo a cuatro decimales; edición doble asignada al año final. |
| Freedom House | All Data FIW 2013–2024 y páginas oficiales 2025/2026 | Igualdad del Aggregate Score; año de referencia = edición − 1. |
| UNDP mediante OWID | CSV completo de HDI | Redondeo a tres decimales. Contraste con el distribuidor utilizado, no auditoría independiente de microdatos UNDP. |
| FMI | WEO abril de 2026, hoja Countries | Diferencia máxima de media unidad de redondeo del raw a un decimal. |

Respuestas, URL y hashes: `iciv/data/sources/audit_20260917`. `comparisons.csv` permite revisar cada celda; `verified_observations.csv` alimenta la trazabilidad. Reproducción: `python iciv/scripts/audit_sources.py`; `--refresh` vuelve a descargar las URL fijadas.

Git conserva sin conversión los bytes de evidencia descargada. Para los raw CSV se registra además un SHA-256 con saltos de línea LF: acepta únicamente la equivalencia CRLF/LF entre Windows y Linux, no cambios de valores, columnas u orden. La verificación de CI reproduce el snapshot sin sobrescribir releases.

## Estado WEO por serie

El archivo oficial incluye `LATEST_ACTUAL_ANNUAL_DATA`. Venezuela, abril de 2026:

| Serie | Último año histórico según FMI | Tratamiento posterior |
|---|---:|---|
| Inflación IPC, PCPIPCH | 2025 | 2026 es estimación/proyección FMI. |
| Crecimiento real, NGDP_RPCH | 2018 | Posteriores: estimaciones/proyecciones. No sustituye al crecimiento WDI del score. |
| Desempleo, LUR | 2011 | Valores disponibles posteriores: estimaciones. Faltantes permanecen vacíos. |
| Cuenta corriente, BCA_NGDPD | 2018 | Posteriores: estimaciones/proyecciones. |

“Histórico según proveedor” no significa definitivo ni independiente. El WEO identifica Central Bank / National Statistics Office como fuentes históricas. La [FAQ FMI](https://data.imf.org/Datasets/WEO/Frequently-Asked-Questions) explica el campo; el [archivo oficial del vintage](https://data.imf.org/-/media/iData/External-Storage/Documents/2F78EE59F79143A7921E5E203D3AAA80/en/WEOApr2026all.xlsx) aporta evidencia por serie.

Publicación del vintage: 14 de abril de 2026. No se infiere cuándo estuvo disponible cada valor en 2000–2025. Los backtests siguen siendo de último vintage, no evaluaciones históricas en tiempo real.

## Cambios y límites

- Se apartaron 12 registros CPI anteriores a 2012 hacia `data/archive`, como no comparables y no verificados. Puntajes activos sin cambios. Nuevo recolector oficial CPI sin valores manuales.
- Se distinguen índice publicado, estimación OIT, histórico WEO revisable y estimación/proyección WEO acreditada. Si cambia el raw, la verificación anterior deja de aplicarse.
- Sin sustitución de fuentes ni imputación del proyecto. Las estimaciones publicadas por proveedores permanecen etiquetadas como estimaciones.
- Este contraste no certifica WDI/WGI/EIA/FRED/UNCTAD/UNHCR/noticias fila por fila. Conservan procedencia y limitaciones, sin recibir la etiqueta de verificación de esta auditoría.
- La revocación de la clave EIA expuesta anteriormente corresponde al titular. El código actual y una prueba de conexión no confirman su revocación. No se reproduce la credencial.
