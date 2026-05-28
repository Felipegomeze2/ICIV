# Dataset publico ICIV

Fecha de corte: 2026-05-28.

El proyecto genera un paquete de dataset auditable junto con el dashboard. Su
objetivo es que la defensa no dependa solo de la visualizacion, sino de una base
replicable con diccionario, cobertura, provenance y manifest.

## Ubicacion

```text
iciv/data/releases/latest/
```

Esta carpeta es el snapshot publico vigente. Se regenera con:

```bash
cd iciv
python main.py --no-fetch --no-open
```

Tambien puede reconstruirse desde artefactos procesados existentes:

```bash
cd iciv
python scripts/build_dataset_package.py
```

## Archivos del paquete

| Archivo | Uso |
|---|---|
| `iciv_dataset_wide.csv` | Panel anual ancho: una fila por ano y una columna por variable publicada. |
| `iciv_dataset_largo.csv` | Panel anual largo: una fila por ano-variable con valor crudo, valor normalizado, fuente, dimension, direccion y rol. |
| `data_dictionary.csv` | Diccionario de variables generado desde el catalogo del codigo. |
| `data_dictionary.md` | Version legible del diccionario para revision rapida. |
| `coverage_annual.csv` | Cobertura anual por variable: anos con dato, porcentaje y anos faltantes. |
| `source_provenance.csv` | Fuente, archivos crudos asociados, roles y politica de uso. |
| `manifest.json` | Release id, fecha UTC, conteos, hashes SHA-256 y tamano de archivos. |
| `pulse_forecast_backtest_summary.csv` | Resumen del backtesting del forecast Pulse, si esta disponible. |
| `pulse_forecast_backtest.csv` | Detalle del backtesting rolling-origin, si esta disponible. |
| `README.md` | Guia corta del paquete. |

## Roles

| Rol | Significado |
|---|---|
| `core_anual` | Variable que entra al ICIV anual. |
| `outcome_externo` | Variable usada para validacion, no entra al score. Actualmente: IED. |
| `pulse_mensual` | Variable mensual usada por Pulse y que no es core anual. |
| `auxiliar` | Variable disponible en el catalogo, sin peso en el score vigente. |

Algunas variables tienen doble uso: por ejemplo WTI, Fed Funds, petroleo y
Guardian son parte del ICIV anual y tambien entran al Pulse mensual. Para evitar
ambiguedad, el dataset incluye banderas explicitas:

- `entra_iciv_anual`
- `entra_pulse_mensual`
- `entra_validacion_outcome`

## Politica de datos

- No se aceptan fuentes gubernamentales venezolanas ni fuentes locales
  originadas en Venezuela para el score.
- No se inventan datos.
- No se crean fallbacks sinteticos.
- Los faltantes se conservan como faltantes.
- Si una API opcional falla, el paquete documenta la ausencia o el estado de la
  fuente; no rellena la serie.

## Como defenderlo

1. Use `data_dictionary.csv` para explicar cada variable, fuente, unidad,
   direccion y rol.
2. Use `coverage_annual.csv` para mostrar donde hay datos reales y donde hay
   faltantes.
3. Use `source_provenance.csv` para defender que las fuentes son externas a
   Venezuela.
4. Use `manifest.json` para mostrar que el paquete es auditable y verificable
   por hash.
5. Use `iciv_dataset_largo.csv` para revisar una observacion especifica:
   ano-variable-fuente-valor.

## Que no es

El paquete no es una base cruda completa. Es una capa derivada y documentada que
resume los datos realmente usados o defendidos por el proyecto. Los archivos
crudos siguen en `iciv/data/raw/` y el pipeline conserva la trazabilidad hacia
ellos.

## Proximos pasos

1. Versionar releases historicos, por ejemplo `iciv_2026_05_defensa`.
2. Publicar un changelog metodologico por release.
3. Agregar una matriz mensual de cobertura Pulse al paquete.
4. Agregar pruebas automaticas para validar que ninguna fuente bloqueada entre
   al diccionario.
