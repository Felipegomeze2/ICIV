# Cierre técnico y académico · v2

## Cambios ejecutados

Corrección semántica de IPC, empleo vulnerable y petróleo mensual; conservación de originales; exclusión de CPI no comparable; cobertura de universo fijo y pesos efectivamente consumidos; benchmark igualitario; extracción satelital estricta separada del histórico; eliminación de sustituciones automáticas de fuentes y de ajustes sectoriales no calibrados; Pulse causal con calendario y composición; pronóstico explícito de persistencia; validación externa común en niveles/diferencias con HAC y Holm; release con snapshots y hashes; documentación metodológica unificada.

## Revisión de pasos 1–4 ejecutada

- Fuentes: contraste reproducible con archivos oficiales, hashes y estados WEO por observación; CPI comparable automatizado, historial anterior apartado. Ver [auditoría y límites](AUDITORIA_FUENTES_ACTUAL.md).
- Satélite: recuperados 16 meses QA, incluido todo 2025. Cobertura espacial 2025 de 0,60–48,09%; exclusión deliberada del índice, sin sustitución. Ver [evidencia](REVISION_SATELITAL.md).
- Robustez: 79 escenarios deterministas y descomposición anual de composición. Los resultados y categorías dependen del diseño; se publican las diferencias, no una declaración de robustez absoluta.
- Metodología: decisiones justificadas y alternativas preparadas en [validación pendiente](VALIDACION_PENDIENTE.md). Aprobación académica aún no otorgada.

## Acciones del autor y asesor

- Revocación de la clave EIA anterior confirmada por el titular el 17 de septiembre de 2026, sin comprobación directa con el proveedor. La credencial de reemplazo no fue confirmada. Para futuras descargas, configurar una credencial vigente por entorno, sin versionarla.
- Justificar y someter a revisión académica los pesos del autor, umbrales de cobertura, transformaciones y alcance. Un CR pequeño no sustituye esa validación.
- Revisar y aceptar las decisiones del documento de validación. Si la exigencia académica prohíbe estimaciones del proveedor, el universo debe cambiar; etiquetarlas no convierte una estimación en medición directa.

La congelación de una nueva release y la redacción de tesis quedan excluidas de esta etapa por instrucción del autor. `--no-package` permite reproducir el trabajo sin alterar las releases anteriores.

Estos son pendientes sustantivos de evidencia y gobierno, no simples retoques de estilo. El software mejorado no permite prometer que todos hayan quedado resueltos.

## Tesis que falta redactar

1. Problema, pregunta y objetivo descriptivo verificable; población temporal y límites de inferencia.
2. Marco de indicadores compuestos, economía venezolana, fuentes y comparación con literatura.
3. Diseño de datos, diccionario, arquitectura reproducible y calidad por observación.
4. Metodología de transformación, ponderación, cobertura, sensibilidad y pronóstico.
5. Resultados de la release congelada: niveles, cambios, composición, tamaños de muestra y resultados negativos.
6. Discusión económica sin causalidad injustificada, limitaciones y agenda de vintages.
7. Anexos: matriz AHP, decisiones de exclusión, diccionario, manifiesto, pruebas y evidencia de reproducción.

## Extensiones posteriores

Recolectar vintages y fechas reales de publicación; backtesting verdaderamente en tiempo real; calibrar pesos con un protocolo experto externo; validar noticias con anotaciones humanas; estudiar rupturas estructurales y cobertura espacial satelital; ampliar a un panel multipaís solo con fuentes y unidades comparables. Estas extensiones no están implementadas. La comparación de normalizadores sí forma parte de la revisión actual.
