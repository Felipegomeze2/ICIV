# Bitacora tecnica vigente

Fecha de corte: 2026-07-21.

La bitacora tecnica resume el estado actual del codigo. Las notas antiguas que
describian versiones con sanciones externas en el core, busquedas web en percepcion, escenarios
optimista/pesimista/neutro o fuentes descartadas fueron eliminadas.

## Arquitectura actual

- `main.py`: orquesta fetch opcional, pipeline, score anual, Pulse mensual,
  SATV mensual, correlacion ICIV-IED, radar sectorial, forecast Pulse y dashboard.
- `src/iciv/index/dimensions.py`: fuente de verdad del core anual, 26 variables.
- `src/iciv/index/pulse_aggregator.py`: fuente de verdad del Pulse mensual,
  15 variables (ampliado 2026-07 con IMF IMTS, WB Pink Sheet e ICE BofA/FRED).
- `src/iciv/ml/pulse_forecast.py`: forecast publico SARIMA del Pulse.
- `src/iciv/satv/pulse_engine.py`: alertas tempranas basadas solo en Pulse.
- `docs/`: documentacion de defensa, fuentes, decisiones y dataset.

## Criterios de limpieza

- Se retiran modulos que ya no se ejecutan ni se exponen.
- Se retiran documentos de trabajo que contradicen la version final.
- Se mantienen datos crudos verificables aunque esten apartados, siempre que
  sirvan para auditoria o para reconstruir decisiones.
- Se evita borrar fuentes sin reemplazo cuando una seccion del dashboard aun
  depende de ellas.
