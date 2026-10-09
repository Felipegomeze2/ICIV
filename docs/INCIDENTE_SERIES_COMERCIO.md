# Incidente: series equivocadas en el bloque de comercio del Pulse

**Detectado y corregido:** 9 de octubre de 2026. **Período afectado:** del 11 de agosto al 9 de octubre de 2026.

## Qué pasó

El 11 de agosto de 2026 (commit `354412d`) el bloque de comercio del Pulse (10% del peso) pasó de IMF IMTS a dos códigos de FRED que se documentaron como importaciones de EE.UU. desde Venezuela:

| Código usado | Se documentó como | Lo que publica FRED realmente |
|---|---|---|
| IR14270 | Importaciones de crudo venezolano (miles de barriles diarios) | *Import Price Index (End Use): Nonmonetary Gold* |
| IR14260 | Importaciones de productos petroleros venezolanos | *Import Price Index (End Use): Zinc* |

El título de cada serie se comprobó en la página oficial de FRED el 9 de octubre de 2026. Las series descargadas eran índices de precios de importación de oro y zinc de EE.UU.: datos reales de FRED, pero **sin relación con Venezuela**. Durante ese período el Pulse, el semáforo de comercio y el backtest usaron esas dos series con la etiqueta equivocada. El índice anual **no** se vio afectado: estas variables solo entran al Pulse.

## Corrección

- Nuevo `iciv/scripts/fetch_eia_imports_monthly.py`, que descarga de la EIA (API v2, `petroleum/move/impcus`) las series correctas:
  - `MCRIMUSVE2`: *U.S. Imports from Venezuela of Crude Oil* (miles de barriles diarios).
  - `MTPIMUSVE2`: *U.S. Imports from Venezuela of Total Petroleum Products* (miles de barriles diarios).
- El fetcher compara en cada descarga la descripción que devuelve la API con la esperada. Si la EIA cambiara el contenido de un código, la descarga se rechaza y no se guarda.
- El CSV conserva el código EIA, la descripción y la unidad por fila (`data/raw/eia_imports_monthly.csv`).
- Se eliminaron de `data/raw/fred_monthly.csv` las 400 filas con etiqueta equivocada (borrado de líneas, sin tocar las demás) y los códigos IR142xx de `fetch_fred_monthly.py`.
- Durante el embargo petrolero (mediados de 2019 a 2023) la EIA no publica valor para la mayoría de los meses. Esos meses quedan **sin dato**, no en cero.
- Se verificaron también los demás códigos del proyecto contra sus proveedores: FRED (DCOILWTICO, DCOILBRENTEU, FEDFUNDS, DTWEXBGS, VIXCLS, DGS10, BAMLEMCBPIOAS), Banco Mundial (NY.GDP.MKTP.KD.ZG, BX.KLT.DINV.CD.WD, NE.EXP.GNFS.ZS, EG.ELC.ACCS.ZS, SP.DYN.LE00.IN, SP.DYN.IMRT.IN, SL.EMP.VULN.ZS). Todos corresponden a lo que el proyecto dice medir.

## Efecto

Pulse, semáforo y backtest se regeneraron con las series correctas. Las cifras vigentes están en [RESULTADOS_ACTUALES.md](RESULTADOS_ACTUALES.md). Las versiones del dashboard publicadas entre el 11 de agosto y el 9 de octubre, y la presentación de avances de septiembre, contienen un Pulse calculado con esas series y no deben citarse.

## Lección

Un código de serie se documenta con el **título que devuelve el proveedor**, no con el que se espera. Los fetchers nuevos deben validar la descripción de la serie en cada descarga.
