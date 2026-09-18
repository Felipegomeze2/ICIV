# Decisiones para validar con el autor y asesor

Esta revisión ejecuta los pasos 1–4. No congela la entrega final ni redacta la tesis. No constituye aprobación de un panel experto.

| Decisión | Propuesta y evidencia | Validación humana |
|---|---|---|
| Alcance | Indicador descriptivo relativo a Venezuela, sin inferencia de rentabilidad, riesgo crediticio o causalidad sobre IED. | Compatibilidad con pregunta y objetivos académicos. |
| Pesos | AHP como supuesto explícito del autor, benchmark igualitario y 79 escenarios. CR evalúa coherencia interna, no verdad económica. | Relevancia de dimensiones y juicios. No atribuirlos a expertos que no participaron. |
| Normalización | Min–max histórico y log10 del IPC positivo; sensibilidad a rangos, percentiles 5/95 y retirada del log. | Dependencia de la escala; no comparable entre países. |
| Categorías | Etiquetas descriptivas y cortes declarados; acompañar con score continuo y cobertura. Rangos cambian 10/13 etiquetas en la muestra de alta cobertura. | No interpretarlas como clases calibradas de riesgo. |
| Cobertura | Universo fijo y piso dimensional 50%, comparado con 25/75/100%. | Compromiso entre disponibilidad y representatividad; piso no calibrado externamente. |
| Satélite | Fuera del índice por representatividad espacial/estacional no acreditada; QA recuperado como diagnóstico. | Aceptar exclusión. Reincorporarlo exigiría otro estudio y revisión de versión. |
| Estimaciones ajenas | Mantenerlas etiquetadas; comparar retirada de estimaciones WEO verificadas. | Si se exige solo medición observada, redefinir universo: OIT, HDI e índices también contienen estimación/modelación. |
| Lectura 2026 | Provisional: +14,95 publicado, +3,36 en canasta común, residuo +11,59; cobertura común 41,1%. | No describirlo como recuperación económica de la misma magnitud. |
| Validación | IED exploratoria HAC/Holm; persistencia mensual y backtest común. | Aceptar muestra pequeña, revisiones y falta de vintages históricos; reportar resultados negativos. |
| Clave EIA | Sin clave incrustada en código actual; secreto no divulgado durante revisión. | Revocación de la clave antigua confirmada por el titular el 17 de septiembre de 2026; no verificada directamente con el proveedor. Credencial de reemplazo no confirmada. |

## Orden de revisión

1. Leer `AUDITORIA_FUENTES_ACTUAL.md`, `REVISION_SATELITAL.md` y la pestaña Evidencia.
2. Revisar `ROBUSTEZ_AMPLIADA.md` y aceptar o ajustar las decisiones de la tabla.
3. Revocación de la clave antigua: confirmada por el titular el 17 de septiembre de 2026. Para futuras descargas, usar una credencial vigente por variable de entorno; nunca versionarla.
4. Registrar observaciones del asesor y decisiones aprobadas antes de una congelación futura.

Estas decisiones humanas no impiden terminar las pruebas técnicas y documentación de esta etapa.
