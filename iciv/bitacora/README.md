# Bitacora tecnica vigente

Fecha de corte: 2026-10-09 (versión metodológica 2.1).

La bitacora tecnica resume el estado actual del codigo. Las notas antiguas que
describian versiones con sanciones externas en el core, busquedas web en percepcion, escenarios
optimista/pesimista/neutro o fuentes descartadas fueron eliminadas.

## Arquitectura actual

- `main.py`: orquesta fetch opcional, pipeline, score anual, Pulse mensual,
  SATV mensual, correlacion ICIV-IED, radar sectorial, forecast Pulse y dashboard.
  El mapa por estado es unico (NASA Black Marble, SVG nativo) y es contexto:
  la luminosidad esta fuera del score. El mapa Leaflet de Li et al. por bbox se
  retiro el 2026-07-29.
- `src/iciv/index/dimensions.py`: fuente de verdad del core anual, 21 variables.
- `src/iciv/index/pulse_aggregator.py`: fuente de verdad del Pulse mensual,
  15 variables (FRED, EIA produccion e importaciones de EE.UU. desde Venezuela,
  WB Pink Sheet, Guardian y GDELT).
- `src/iciv/data/plausibility.py`: control de plausibilidad de valores del
  proveedor (excluye imposibles, marca repetidos).
- `src/iciv/ml/pulse_forecast.py`: pronostico publico de persistencia; SARIMA
  y naive estacional como comparadores en el backtest.
- `src/iciv/satv/pulse_engine.py`: alertas tempranas basadas solo en Pulse.
- `docs/`: documentacion de defensa, fuentes, decisiones y dataset.

## Criterios de limpieza

- Se retiran modulos que ya no se ejecutan ni se exponen.
- Se retiran documentos de trabajo que contradicen la version final.
- Se mantienen datos crudos verificables aunque esten apartados, siempre que
  sirvan para auditoria o para reconstruir decisiones.
- Se evita borrar fuentes sin reemplazo cuando una seccion del dashboard aun
  depende de ellas.
