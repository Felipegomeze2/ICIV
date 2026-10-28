# Dataset y reproducción · v2.1

`python iciv/main.py --no-fetch --no-open` procesa los snapshots locales y genera la release después de los modelos y la validación. `--release-id nombre` crea una entrega inmutable; el nombre `latest` es mutable.

El panel ancho contiene los valores usados, en unidades originales. El largo separa `valor_crudo`, `valor_transformado` y `valor_normalizado`, e incluye unidad, archivo de origen, estado conocido, transformación, meses utilizados e indicador de imputación por el proyecto (siempre falso). Una columna ausente no se interpreta como cero.

Un valor imposible del proveedor (por ejemplo, exportaciones = 0% del PIB en 2000–2011) aparece vacío en el panel con estado `valor_no_plausible_del_proveedor_excluido`. Su valor original queda en el archivo crudo del proveedor y en `data/processed/plausibilidad_proveedor.csv`. Las rachas repetidas se marcan con `valor_repetido_por_proveedor` sin cambiar el valor.

Los scores anuales incluyen `tramo_serie`: `oficial` (desde 2012) o `extendido_exploratorio` (2000–2011).

El paquete incluye diccionario, cobertura, scores anual/Pulse, parámetros de normalización, validación externa, forecast/backtest, composición anual, registro de plausibilidad, robustez ampliada y copia de CSV de origen. El manifiesto registra versión metodológica, commit base, hashes del código y versiones de librerías, y dos indicadores: `working_tree_modified` (el árbol completo difería del commit; suele ser verdadero tras una corrida, porque el pipeline reescribe datos y documentos versionados) y `code_modified_vs_commit` (solo `src`, `scripts`, `main.py`, `config` y `pyproject.toml`; falso significa que el código es exactamente el del commit base).

La release de la tesis es `tesis-2026-10b`: `python iciv/scripts/verify_release.py --release iciv/data/releases/tesis-2026-10b`.

SHA-256 verifica los bytes empaquetados. También se registra hash con finales LF canónicos para distinguir alteraciones reales de la conversión LF/CRLF de Git en Windows. Verificar mediante `python iciv/scripts/verify_release.py`.

Limitaciones de procedencia: las fechas originales de consulta/publicación no se reconstruyen del mtime; están ausentes cuando no se archivaron. La copia de snapshots permite iniciar el archivo de vintages hacia adelante, pero no convierte el pasado en un experimento en tiempo real.
