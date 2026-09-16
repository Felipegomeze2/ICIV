# Dataset y reproducción · v2

`python iciv/main.py --no-fetch --no-open` procesa los snapshots locales y genera la release después de los modelos y la validación. `--release-id nombre` crea una entrega inmutable; el nombre `latest` es mutable.

El panel ancho contiene valores en unidades originales. El largo separa `valor_crudo`, `valor_transformado` y `valor_normalizado`, e incluye unidad, archivo de origen, estado conocido, transformación, meses utilizados e indicador de imputación por el proyecto. Una columna ausente no se interpreta como cero.

El paquete incluye diccionario, cobertura, scores anual/Pulse, parámetros de normalización, validación externa, forecast/backtest y copia de CSV de origen. El manifiesto registra versión metodológica, commit base, si había cambios locales, hashes del código y versiones de librerías. El commit base por sí solo no representa cambios aún no confirmados.

SHA-256 verifica los bytes empaquetados. También se registra hash con finales LF canónicos para distinguir alteraciones reales de la conversión LF/CRLF de Git en Windows. Verificar mediante `python iciv/scripts/verify_release.py`.

Limitaciones de procedencia: las fechas originales de consulta/publicación no se reconstruyen del mtime; están ausentes cuando no se archivaron. La copia de snapshots permite iniciar el archivo de vintages hacia adelante, pero no convierte el pasado en un experimento en tiempo real.
