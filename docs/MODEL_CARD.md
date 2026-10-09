# Ficha del modelo · ICIV v2.1

**Uso previsto:** investigación académica, análisis descriptivo del entorno venezolano y exploración de sensibilidad. **Responsable:** Felipe Gómez Espinal, Universidad EIA.

**Entradas:** snapshots de organismos internacionales y productos satelitales. Ninguna fuente venezolana se usa directamente. Algunas series contienen estimaciones modeladas y proyecciones de su proveedor, etiquetadas como tales.

**Salidas:** score anual relativo (serie oficial 2012–2026 y tramo exploratorio 2000–2011), cobertura, componentes, Pulse mensual, semáforo SATV, alertas descriptivas y pronóstico explícito de persistencia.

**Exclusiones:** decisiones automáticas de inversión, probabilidades de impago, rentabilidad sectorial, comparación internacional directa y afirmaciones causales.

**Controles:** universo fijo de variables; faltantes preservados; control de plausibilidad de valores del proveedor (excluir imposibles, marcar repetidos, nunca sustituir); validación de la identidad de las series en los fetchers nuevos; protección contra pérdida de datos en descargas fallidas; fuente única por serie; separación de valores crudos, transformados y normalizados; normalización mensual causal; comparación de pronósticos en muestra común; validación anual por tramo, en niveles y diferencias, con HAC y Holm; releases con hashes.

**Limitaciones abiertas:**
- Pesos definidos por el autor.
- Muestra anual pequeña (14 años en la serie oficial).
- Fuentes revisables.
- Estimaciones del proveedor cuyo estado individual no siempre se conoce.
- Sesgo de noticias.
- Umbrales heurísticos.
- Luminosidad satelital excluida del índice.
- Sin vintages históricos para una evaluación en tiempo real.
- El Pulse no replica el índice anual.

**Incidentes documentados:** sobrescritura de Guardian con NaN (agosto de 2026), ejecución 38 de Actions (septiembre de 2026) y [series equivocadas en el bloque de comercio del Pulse](INCIDENTE_SERIES_COMERCIO.md) (agosto a octubre de 2026).

**Gobierno:** cada cambio de variable, fuente, transformación, pesos, plausibilidad o elegibilidad exige una nueva versión metodológica y regeneración completa. Congelar una release antes de citar cifras en la tesis. Ver [cierre](CIERRE_PROYECTO.md).
