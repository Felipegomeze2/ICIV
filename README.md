# ICIV · Indicador de Clima de Inversión de Venezuela

Proyecto de grado de Felipe Gómez Espinal, Especialización en Big Data e Inteligencia de Negocios, Universidad EIA.

ICIV es un indicador compuesto **descriptivo** del entorno venezolano. Combina un índice anual de seis dimensiones con Pulse mensual, controles de cobertura, exploración satelital y validación retrospectiva. La escala compara períodos de Venezuela; no estima rentabilidad ni probabilidad de riesgo país.

## Versión metodológica 2

- Universo anual fijo de 21 variables; cobertura calculada con los pesos realmente utilizados.
- AHP público y benchmark de pesos iguales entre dimensiones; sin imputación de observaciones.
- IPC del FMI correctamente identificado; empleo vulnerable OIT distribuido por WDI, distinto de informalidad.
- CPI comparable desde 2012; ediciones WJP dobles asignadas una sola vez al año final.
- Pulse con normalización expansiva, calendario regular, elegibilidad y cambios sobre componentes comunes.
- Persistencia como pronóstico explícito; SARIMA y naive estacional comparados en los mismos pares origen/horizonte.
- Dataset con valores originales, transformados, normalizados y estados conocidos; release con snapshots y hashes.
- Histórico satelital sin QA acreditado conservado como contexto y excluido del índice. El recolector estricto produce archivos separados.

## Reproducción

Python 3.11 o posterior. Desde la raíz:

```sh
python -m pip install -e "iciv/[dev]"
python -m pytest iciv/tests -q
python iciv/main.py --no-fetch --no-open
python iciv/scripts/verify_release.py
```

`--no-fetch` reproduce los CSV archivados; no significa que estén actualizados. Para intentar refrescarlos se omite esa opción. Las credenciales van en variables de entorno; nunca en archivos versionados. Un fallo no debe reemplazar observaciones con ceros, interpolaciones u otra fuente.

El dashboard se genera en `iciv_dashboard.html`; la validación en `iciv/data/processed/iciv_validacion.html`. `iciv/data/releases/latest/` contiene los datos publicables. Para una entrega congelada, ejecutar `--release-id nombre-unico`: no se sobrescriben releases nombrados existentes.

## Documentación vigente

- [Metodología](docs/METODOLOGIA.md)
- [Fuentes y semántica](docs/FUENTES_Y_VARIABLES.md)
- [Dataset y reproducción](docs/DATASET_ICIV.md)
- [Validación externa](docs/VALIDACION_EXTERNA.md)
- [Backtesting](docs/BACKTESTING_FORECAST.md)
- [Ficha del modelo](docs/MODEL_CARD.md)
- [Cierre y pendientes](docs/CIERRE_PROYECTO.md)

Las presentaciones y documentos de avances anteriores son históricos. Sus cifras y descripciones no sustituyen la metodología v2 ni los resultados de la release actual. La tesis aún debe redactarse y justificar las decisiones de diseño; el software por sí solo no acredita validez económica o causal.
