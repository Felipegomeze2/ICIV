# Ficha del modelo · ICIV v2

**Uso previsto:** investigación académica, análisis descriptivo del entorno venezolano y exploración de sensibilidad. **Responsable:** Felipe Gómez Espinal, Universidad EIA.

**Entradas:** snapshots de distribuidores internacionales y productos satelitales; algunas fuentes contienen estimaciones modeladas y proyecciones. **Salidas:** score anual relativo, cobertura, componentes, Pulse, alertas descriptivas y pronóstico explícito de persistencia.

**Exclusiones:** decisiones automáticas de inversión, probabilidades de impago, rentabilidad sectorial, comparación internacional directa y afirmaciones causales.

**Controles:** universo fijo, faltantes preservados, pérdida de datos protegida, fuente única por serie, separación de transformaciones, distinción de estados, normalización mensual causal, calendario con huecos, comparación de pronósticos en muestra común y validación anual en niveles/diferencias con HAC y Holm.

**Limitaciones abiertas:** pesos del autor; escasa muestra anual; fuentes revisables; datos nacionales redistribuidos; mezcla de observaciones/estimaciones del proveedor cuyo estado individual no siempre se conoce; sesgo de noticias; umbrales heurísticos; archivos satelitales históricos sin QA acreditado excluidos del índice; falta de vintages históricos para evaluación en tiempo real.

**Gobierno:** cada cambio de variable, fuente, transformación, pesos o elegibilidad exige nueva versión metodológica y regeneración completa. Congelar una release antes de citar cifras en la tesis. Ver [cierre](CIERRE_PROYECTO.md).

**Revisión de trabajo posterior:** estado WEO acreditado contra el vintage oficial; contraste de CPI/WJP/FH/HDI; 79 escenarios y composición anual. Satélite QA continúa excluido por representatividad no acreditada. El dashboard usa `processed`; las releases anteriores se conservan y no certifican esta revisión. Ver [decisiones pendientes](VALIDACION_PENDIENTE.md).
