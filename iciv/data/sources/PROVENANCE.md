# Procedencia vigente · revisión septiembre de 2026

Los originales se conservan; un faltante no se rellena ni se sustituye por otra fuente. Un proveedor internacional **no garantiza origen primario independiente de Venezuela**: el WEO auditado identifica al Banco Central y la oficina estadística nacional como fuentes históricas.

| Bloque | Proveedor y archivos | Precisión de la atribución |
|---|---|---|
| Macro | FMI WEO `imf.csv`; WDI `wdi.csv`; FRED `fred.csv` | IPC: PCPIPCH. WEO incluye estimaciones; el último año histórico varía por serie. PIB WDI y PIB FMI son variables distintas. |
| Energía | EIA `eia.csv`, `eia_monthly.csv`; WDI para acceso eléctrico | Crudo anual, producto 57; líquidos totales mensual, producto 53. No intercambiables. |
| Instituciones | `wgi.csv`, `cpi.csv`, `freedom_house.csv`, `wjp.csv` | Índices publicados, no mediciones directas libres de error. CPI activo desde 2012. WJP asigna cada edición doble solo al año final. |
| Comercial | WDI, FMI, `unhcr.csv`, `unctad.csv` | LSCI desde UNCTAD; no hay sustitución por WDI cuando falla. |
| Capital humano | WDI, `hdi.csv`, `ilostat.csv` | HDI: UNDP distribuido por OWID. Empleo vulnerable: estimación modelada OIT distribuida por WDI, no informalidad. |
| Percepción | `guardian.csv` | VADER derivado del texto; no encuesta de confianza de inversionistas. |

El catálogo con peso es `src/iciv/index/dimensions.py`. PTS/WHO/V-Dem y otros archivos auxiliares no entran por el hecho de existir en raw.

Pulse utiliza FRED, EIA mensual, Guardian/GDELT, IMTS del FMI (comercio bilateral espejo reportado por EE. UU.) y Pink Sheet del Banco Mundial. Sus diferencias distinguen cambio en componentes comunes y composición. El universo de cobertura es fijo; una fuente fallida no desaparece del denominador.

## Evidencia de esta revisión

`audit_20260917/` contiene respuestas oficiales, URL, fecha de recuperación, SHA-256, comparación numérica y estados por observación. `scripts/audit_sources.py` reproduce el contraste sin modificar los raw. Alcance: CPI 2012–2025, WJP, Freedom House, HDI vía OWID y WEO; no certifica todas las fuentes.

El estado individual se propaga únicamente cuando coinciden hashes del raw y la evidencia, año, variable y valor. La fecha de publicación es la del vintage auditado, **no la primera disponibilidad histórica**.

## Satélite y archivos apartados

- `blackmarble_monthly.csv` y `blackmarble_states_monthly.csv`: histórico exploratorio sin QA acreditado; mapa contextual.
- `blackmarble_qa_monthly.csv` y `blackmarble_qa_states_monthly.csv`: muestra diagnóstica de calidad 0 y más de tres observaciones; excluye gap-filled y publica cobertura espacial. No es un histórico completo certificado.
- **Ambas versiones quedan fuera del score anual y de Pulse**. QA por píxel no acredita representatividad territorial/estacional. Ver `docs/REVISION_SATELITAL.md`.
- `viirs.csv`: referencia externa Li et al.; no sustituye Black Marble ni entra al score.
- `data/archive/cpi_pre2012_noncomparable.csv`: valores históricos no comparables apartados del raw; no verificados por esta auditoría.
- `data/archive/wjp_duplicate_edition_assignments_pre_v2.csv`: asignaciones antiguas fuera del cálculo.

## Reproducción sin congelación

Desde `iciv`: `python scripts/audit_sources.py`, `python main.py --no-fetch --no-open --no-package`, `python -m pytest`.

`data/processed` y el dashboard representan el trabajo actual. `data/releases/latest` y la entrega de septiembre 16 se conservan intactos; no deben confundirse con esta revisión. Congelación final y tesis quedan fuera de esta etapa.
