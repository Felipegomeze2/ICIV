# Fuentes y variables · v2

El inventario vigente se genera desde `CATALOG`, `DIMENSIONS` y `PULSE_WEIGHTS` en la release: `data_dictionary.csv`, `source_provenance.csv` y `coverage_annual.csv`. Esos archivos contienen los pesos y la cobertura de la ejecución; esta página explica decisiones semánticas.

| Serie | Contrato |
|---|---|
| FMI PCPIPCH | IPC anual porcentual, `inflacion_ipc_imf_pct`; no deflactor. WEO incorpora estimaciones y proyecciones. |
| WB SL.EMP.VULN.ZS | `empleo_vulnerable_oit_pct`: trabajadores por cuenta propia y familiares auxiliares; estimación modelada OIT distribuida por WDI. No empleo informal. |
| EIA producto 57 | Crudo incluido condensado; serie anual y mensual anualizable del mismo producto. |
| EIA producto 53 | Petróleo y otros líquidos totales; `petroleo_liquidos_totales_tbpd`, componente Pulse. |
| CPI | Solo 2012+ en el modelo; archivo anterior preservado como archivo histórico. |
| WJP | Ediciones dobles asignadas al año final una sola vez. |
| UNHCR | Stock de refugiados y solicitantes de asilo registrados; no diáspora total ni flujo anual. |
| Guardian | Muestra de titulares y tono VADER; sesgos de idioma, medio y selección. No opinión pública representativa. |
| Black Marble | Histórico y muestra QA estricta separados; ambos fuera del índice por representatividad espacial/estacional no acreditada. |
| Li et al. | Referencia satelital externa exploratoria; comparte sensor VIIRS con Black Marble y tiene cambio DMSP/VIIRS. |

Un distribuidor internacional puede incorporar productores nacionales. La independencia del origen primario no está demostrada por utilizar WDI o FMI. No se afirma exclusión total de estadísticas venezolanas.

La revisión contrasta 164 valores de CPI, WJP, Freedom House, HDI vía OWID y WEO: [evidencia y límites](AUDITORIA_FUENTES_ACTUAL.md). Los CSV procesados incorporan estados verificados por hash; la release previa no se modifica durante esta etapa.

Las fechas de publicación del histórico no están archivadas sistemáticamente. El año o mes del dato y la fecha del archivo no se usan como fechas de publicación. Los archivos de cada release permiten conservar snapshots hacia adelante.

No se cambian proveedores automáticamente al fallar una API. Las descargas fallidas preservan el archivo anterior y se declaran fallidas; reproducirlo con `--no-fetch` es una ejecución explícita de snapshot, no una actualización exitosa.

Fuentes primarias de semántica: [WB empleo vulnerable](https://databank.worldbank.org/metadataglossary/jobs/series/SL.EMP.VULN.ZS), [FMI WEO](https://www.imf.org/external/datamapper/datasets/WEO), [CPI metodología](https://images.transparencycdn.org/images/2019_CPI_methodology.pdf), [NASA Collection 2](https://landweb.modaps.eosdis.nasa.gov/data/userguide/BlackMarbleUserGuide_Collection2.0_20241203.pdf).
