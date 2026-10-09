# Fuentes y variables · v2.1

El inventario de cada ejecución se genera desde `CATALOG`, `DIMENSIONS` y `PULSE_WEIGHTS` en la release: `data_dictionary.csv`, `source_provenance.csv` y `coverage_annual.csv`. Esta página explica la política de fuentes y las decisiones semánticas. Los pesos están en [METODOLOGIA.md](METODOLOGIA.md).

## Política

- **Solo fuentes internacionales.** Ningún organismo venezolano (BCV, INE, PDVSA, Conatel, OVF, IIES-UCAB) se usa como fuente del proyecto.
- Algunos organismos internacionales compilan sus series con información reportada por los países. Por ejemplo, el WEO del FMI declara a las autoridades nacionales como fuente histórica de varias series. Esa dependencia indirecta se declara; no convierte al proyecto en usuario de fuentes venezolanas, pero tampoco se oculta.
- No se cambia de proveedor automáticamente cuando falla una API. Una descarga fallida conserva el archivo anterior y se declara; `--no-fetch` reproduce el snapshot, no lo actualiza.
- Valores imposibles del proveedor se excluyen y se registran; nunca se reemplazan.

## Semántica de las series

| Serie | Contrato |
|---|---|
| FMI PCPIPCH | IPC anual porcentual, `inflacion_ipc_imf_pct`; no deflactor. El WEO incorpora estimaciones y proyecciones, etiquetadas por observación cuando hay evidencia archivada. |
| WB NY.GDP.MKTP.KD.ZG | `pib_crecimiento_real_pct`. Serie del Banco Mundial; distinta del crecimiento del FMI. |
| WB NE.EXP.GNFS.ZS | `exportaciones_pct_pib`. El proveedor publica 0 en 1995–2011: valor imposible, excluido. Serie usable desde 2012. |
| WB SL.EMP.VULN.ZS | `empleo_vulnerable_oit_pct`: trabajadores por cuenta propia y familiares auxiliares; estimación modelada de la OIT distribuida por el Banco Mundial. No es empleo informal. |
| WB SP.DYN.IMRT.IN | `mortalidad_infantil_x1000`. El proveedor repite 21,2 en 2016–2024; se marca como valor repetido sin cambiarlo. |
| EIA producto 57 | Crudo incluido condensado; serie anual y mensual anualizable del mismo producto. |
| EIA producto 53 | Petróleo y otros líquidos totales; `petroleo_liquidos_totales_tbpd`, componente del Pulse. No intercambiable con el producto 57. |
| EIA MCRIMUSVE2 / MTPIMUSVE2 | Importaciones de EE.UU. desde Venezuela de crudo y de productos petroleros (miles de barriles diarios), registro de aduana de EE.UU.; componentes del Pulse. Los meses del embargo sin valor publicado quedan sin dato. Ver [incidente de series de comercio](INCIDENTE_SERIES_COMERCIO.md). |
| CPI | Solo 2012+ en el modelo; el archivo anterior se preserva en `data/archive`. |
| WJP | Ediciones dobles asignadas una sola vez al año final. |
| Freedom House | Puntaje agregado 0–100, disponible desde la edición 2013. |
| ACNUR | Stock de refugiados y solicitantes de asilo registrados; no es la diáspora total ni un flujo anual. |
| The Guardian | Volumen de artículos y tono VADER de titulares; sesgos de idioma, medio y selección. No es opinión pública representativa. |
| GDELT | Volumen y tono de cobertura global; componente opcional del Pulse por límites de la API. |
| Black Marble | Histórico y muestra QA estricta separados; ambos fuera del índice. El mapa estatal es contexto. |
| Li et al. | Referencia satelital externa para validación; comparte sensor VIIRS con Black Marble y tiene cambio DMSP/VIIRS. |

## Capas auxiliares (fuera del índice)

IMF IMTS y UN Comtrade (comercio espejo), ACLED (eventos de conflicto, ~12 meses de rezago en el nivel gratuito), V-Dem (validación convergente), WHO GHO (fuente anterior de salud) y Li et al. por estado (retirado del mapa). Existir en `data/raw` no implica entrar al score.

## Auditoría y fechas

La revisión del 17 de septiembre contrasta 164 valores de CPI, WJP, Freedom House, HDI vía OWID y WEO contra archivos oficiales: [evidencia y límites](AUDITORIA_FUENTES_ACTUAL.md).

Las fechas de publicación del histórico no están archivadas sistemáticamente. El año o mes del dato y la fecha del archivo no se usan como fechas de publicación. Cada release conserva snapshots hacia adelante.

Fuentes primarias de semántica: [WB empleo vulnerable](https://databank.worldbank.org/metadataglossary/jobs/series/SL.EMP.VULN.ZS), [FMI WEO](https://www.imf.org/external/datamapper/datasets/WEO), [CPI metodología](https://images.transparencycdn.org/images/2019_CPI_methodology.pdf), [NASA Black Marble Collection 2](https://landweb.modaps.eosdis.nasa.gov/data/userguide/BlackMarbleUserGuide_Collection2.0_20241203.pdf).
