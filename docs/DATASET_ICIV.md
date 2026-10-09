# Dataset y reproducción · v2.1

`python iciv/main.py --no-fetch --no-open` procesa los snapshots locales y genera la release después de los modelos y la validación. `--release-id nombre` crea una entrega inmutable; el nombre `latest` es mutable.

El panel ancho contiene los valores usados, en unidades originales. El largo separa `valor_crudo`, `valor_transformado` y `valor_normalizado`, e incluye unidad, archivo de origen, estado conocido, transformación, meses utilizados e indicador de imputación por el proyecto (siempre falso). Una columna ausente no se interpreta como cero.

Un valor imposible del proveedor (por ejemplo, exportaciones = 0% del PIB en 2000–2011) aparece vacío en el panel con estado `valor_no_plausible_del_proveedor_excluido`. Su valor original queda en el archivo crudo del proveedor y en `data/processed/plausibilidad_proveedor.csv`. Las rachas repetidas se marcan con `valor_repetido_por_proveedor` sin cambiar el valor.

Los scores anuales incluyen `tramo_serie`: `oficial` (desde 2012) o `extendido_exploratorio` (2000–2011).

El paquete incluye diccionario, cobertura, scores anual/Pulse, parámetros de normalización, validación externa, forecast/backtest y copia de CSV de origen. El manifiesto registra versión metodológica, commit base, si había cambios locales, hashes del código y versiones de librerías. El commit base por sí solo no representa cambios aún no confirmados.

SHA-256 verifica los bytes empaquetados. También se registra hash con finales LF canónicos para distinguir alteraciones reales de la conversión LF/CRLF de Git en Windows. Verificar mediante `python iciv/scripts/verify_release.py`.

Limitaciones de procedencia: las fechas originales de consulta/publicación no se reconstruyen del mtime; están ausentes cuando no se archivaron. La copia de snapshots permite iniciar el archivo de vintages hacia adelante, pero no convierte el pasado en un experimento en tiempo real.
