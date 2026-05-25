# Dataset publico ICIV

Fecha de corte: 2026-05-23.

El proyecto ahora exporta un dataset publico junto con el dashboard. La idea es
que la defensa no dependa solo de la visualizacion, sino de una base auditable
que permita replicar, revisar y reutilizar los datos.

## Archivos generados

| Archivo | Uso |
|---|---|
| `iciv/data/processed/iciv_dataset_wide.csv` | Panel anual ancho: una fila por ano y una columna por variable publicada. |
| `iciv/data/processed/iciv_dataset_largo.csv` | Panel largo: una fila por ano-variable con valor crudo, valor normalizado, fuente, dimension, direccion y rol. |

## Roles

| Rol | Significado |
|---|---|
| `core_anual` | Variable que entra al ICIV anual. |
| `outcome_externo` | Variable usada para validacion, no entra al score. Actualmente: IED. |
| `pulse_mensual` | Variable mensual usada por Pulse cuando existe granularidad mensual. |
| `auxiliar` | Variable documentada o disponible para auditoria, sin peso en el score vigente. |

## Por que vale la pena

- Hace transparente que variable entra y cual no.
- Permite revisar faltantes sin abrir el codigo.
- Facilita backtesting, analisis de sensibilidad y replicacion externa.
- Separa datos crudos de datos normalizados.
- Ayuda a responder preguntas de jurado sobre cobertura, fuente y direccion.

## Que no hace

- No rellena faltantes.
- No convierte fuentes apartadas en variables del score.
- No crea datos nuevos.
- No reemplaza los CSV crudos de `iciv/data/raw/`; los resume para uso analitico.

## Uso recomendado para defensa

1. Mostrar `iciv_dataset_largo.csv` como evidencia de trazabilidad.
2. Filtrar `rol = core_anual` para explicar el indicador oficial.
3. Filtrar `rol = outcome_externo` para explicar la validacion ICIV-IED.
4. Filtrar variables con `valor_crudo` vacio para discutir cobertura.
5. Usar el archivo largo como base para backtesting y pruebas de robustez.
