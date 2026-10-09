# Cierre técnico y académico · v2.1

Estado al 9 de octubre de 2026. Defensa prevista: 28 de noviembre de 2026.

## Sistema terminado

- Pipeline reproducible: `python iciv/main.py --no-fetch --no-open` regenera índice, Pulse, validación, robustez, dashboard y release; `verify_release.py` comprueba hashes y reproduce normalización, AHP y cobertura.
- Actualización automática semanal y mensual en GitHub Actions, con control de vigencia de fuentes y publicación en GitHub Pages.
- 85 pruebas Python y 7 pruebas JavaScript, ejecutadas en CI.
- Política de datos aplicada en el código: solo fuentes internacionales, faltantes preservados, valores imposibles del proveedor excluidos y registrados, sin sustitución de fuentes.

## Cambios de la versión 2.1 (9 de octubre de 2026)

1. **Corrección del bloque de comercio del Pulse.** Las series FRED IR14270/IR14260 eran índices de precios de importación de oro y zinc. Se reemplazaron por las importaciones de EE.UU. desde Venezuela que publica la EIA (MCRIMUSVE2, MTPIMUSVE2), con validación de identidad en cada descarga. Ver [incidente](INCIDENTE_SERIES_COMERCIO.md).
2. **Control de plausibilidad.** Los ceros de exportaciones del Banco Mundial (2000–2011) se excluyen. La mortalidad infantil repetida 2016–2024 se marca.
3. **Serie oficial 2012–2026** y tramo exploratorio 2000–2011 declarado en datos, dashboard, laboratorio y figura de defensa.
4. **Validación externa por tramo** (serie oficial y serie completa).
5. **Semáforo SATV visible** en la portada, leído en el último mes elegible.
6. **Evidencia sincronizada:** la corrida automática publica `data/processed` y los resultados junto con el dashboard.
7. **Documentación alineada** y figura de defensa regenerada con categorías v2 y eventos de 2026.
8. **Alcance descartado formalizado** (ver abajo).

## Alcance descartado (trabajo futuro)

Escenarios prospectivos 2027–2030, simulación Monte Carlo, indicadores líderes y comparación regional (Colombia, Perú, Ecuador, Bolivia). La escala relativa a la historia venezolana no permite comparar niveles entre países sin rediseñar la normalización.

## Pendientes antes de la defensa

1. Reunión con el asesor para las decisiones pendientes de [VALIDACION_PENDIENTE.md](VALIDACION_PENDIENTE.md).
2. Congelar la release de la tesis: `python iciv/main.py --no-fetch --no-open --release-id tesis-2026-10` (o el nombre que se elija). Desde ahí, todas las cifras de la tesis salen de esa release.
3. Redactar los capítulos de metodología, resultados y discusión sobre la release congelada. El boceto de los capítulos estables está en [docs/tesis](tesis/BORRADOR_TESIS.md).
4. Preparar la presentación de defensa. Las presentaciones de avances anteriores contienen cifras que ya no son válidas (pronóstico SARIMA, IED significativa, Pulse con series de comercio equivocadas).

## Extensiones posteriores

Recolectar vintages y fechas reales de publicación; backtesting en tiempo real; calibrar pesos con un protocolo experto externo; validar el sentimiento de noticias con anotación humana; estudiar rupturas estructurales y cobertura espacial satelital; panel multipaís con fuentes y unidades comparables.
