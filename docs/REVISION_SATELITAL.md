# Revisión satelital · decisión de exclusión

Se recuperaron granulos reales NASA VNP46A3 colección 002 usando las credenciales configuradas. El extractor excluye calidad distinta de 0, rellenos y píxeles con tres observaciones o menos. No se usaron datos simulados ni el histórico sin QA para completar faltantes.

La muestra recuperada contiene 16 meses: todos los de 2025, meses de referencia de 2014/2019 y julio de 2026. No representa un reprocesamiento de todo el histórico 2014–2026.

En 2025 la cobertura válida va de **0.60% a 48.09%** sobre la máscara de 4,300,361 píxeles. Solo 0 de 12 meses alcanza 50%. Este umbral es diagnóstico, no un estándar NASA ni una calibración externa.

| Año | Mes | Radiancia media válida | Píxeles válidos % |
|---|---:|---:|---:|
| 2014 | 7 | 0.7385 | 12.8099 |
| 2019 | 1 | 0.5641 | 55.3069 |
| 2019 | 7 | 0.6608 | 9.9429 |
| 2025 | 1 | 1.1667 | 48.0942 |
| 2025 | 2 | 1.0268 | 37.0918 |
| 2025 | 3 | 0.9337 | 42.2516 |
| 2025 | 4 | 1.7161 | 2.8354 |
| 2025 | 5 | 0.0835 | 0.8564 |
| 2025 | 6 | 1.0790 | 0.5979 |
| 2025 | 7 | 0.4299 | 3.5342 |
| 2025 | 8 | 0.7680 | 5.5231 |
| 2025 | 9 | 0.8561 | 9.0076 |
| 2025 | 10 | 1.5252 | 4.2250 |
| 2025 | 11 | 1.3867 | 5.6897 |
| 2025 | 12 | 1.4048 | 22.4719 |
| 2026 | 7 | 0.1934 | 1.6782 |

## Decisión implementada

Luminosidad permanece **fuera del score anual y de Pulse**, incluso si existe el CSV QA. La variable mantiene su lugar en el universo de cobertura v2 para no mejorar artificialmente la cobertura al excluirla. No se introduce Li et al. como sustituto. Los score anuales no cambian por estas nuevas descargas.

La media mensual representa los píxeles válidos de ese mes, cuya distribución cambia con nubes, geometría de observación y disponibilidad. Una media de meses con territorios distintos no acredita un indicador nacional comparable. No se infiere caída de actividad a partir de una caída de radiancia en un mes de baja cobertura.

Cada mes tiene URL e identificador de sus cinco granulos, hash de los bytes descargados, hash del GeoJSON y conteos en `iciv/data/sources/blackmarble_qa`. Los HDF5 se eliminan tras procesarlos; los hashes no sustituyen los archivos y reproducir la extracción requiere volver a descargarlos. La máscara está en una cuadrícula angular; las medias ponderan píxeles por igual, no por superficie geodésica.

El mapa heredado conserva la advertencia de contexto sin QA acreditado. La muestra estricta queda como evidencia auxiliar separada. Una futura reincorporación necesita cobertura espacial/estacional suficiente, verificación de máscaras, ponderación de área, comparación de canastas espaciales comunes y validación económica, sin rellenar píxeles ausentes.

Referencia QA: [NASA Black Marble Collection 2 User Guide](https://landweb.modaps.eosdis.nasa.gov/data/userguide/BlackMarbleUserGuide_Collection2.0_20241203.pdf). Los criterios de representatividad propuestos son del proyecto, no una certificación NASA.
