# Registro de decisiones metodológicas

Decisiones de diseño del ICIV y su estado. "Aprobada por el autor" significa que Felipe Gómez Espinal la tomó o aceptó; el proyecto es individual y no cuenta con asesor, según aclaración del autor del 28 de octubre de 2026. Nada de esta tabla constituye la aprobación de un panel de expertos.

| Decisión | Contenido | Estado |
|---|---|---|
| Alcance | Indicador descriptivo relativo a la historia de Venezuela. Sin inferencia de rentabilidad, riesgo crediticio ni causalidad sobre la IED. | Aprobada por el autor |
| Fuentes | Solo fuentes internacionales; ningún organismo venezolano como fuente. La dependencia indirecta de compiladores internacionales se declara. | Aprobada por el autor (9 oct. 2026) |
| Datos | Ningún dato inventado, interpolado o sustituido. Valores imposibles del proveedor excluidos y registrados; valores repetidos solo marcados. | Aprobada por el autor (9 oct. 2026) |
| Serie oficial | 2012–2026 (universo de seis dimensiones; disponibilidad por año declarada). 2000–2011 publicado como tramo extendido exploratorio. | Aprobada por el autor (9 oct. 2026) |
| Ceros de exportaciones | `NE.EXP.GNFS.ZS` = 0 en 2000–2011 se excluye por imposible. | Aprobada por el autor (9 oct. 2026) |
| Portada del dashboard | Muestra el mes y el año en curso aunque tengan baja cobertura, marcados como provisionales, junto al último mes y año confiables. | Aprobada por el autor (9 oct. 2026) |
| Alcance descartado | Escenarios 2027–2030, Monte Carlo, indicadores líderes y comparación regional pasan a trabajo futuro. | Aprobada por el autor (9 oct. 2026) |
| Pesos | AHP entre dimensiones como juicio explícito del autor (CR = 0,0081); pesos internos declarados; benchmark de pesos iguales y 79 escenarios. El CR evalúa coherencia, no verdad económica. | Decisión del autor; evaluada mediante robustez; sin panel experto |
| Normalización | Min-max sobre la historia venezolana y log10 del IPC positivo; sensibilidad a rangos, percentiles 5/95 y retirada del log. No comparable entre países. | Decisión del autor; evaluada mediante robustez; sin panel experto |
| Categorías | Etiquetas descriptivas con cortes 31/51/66/81; siempre junto al score continuo y la cobertura. | Decisión del autor; evaluada mediante robustez; sin panel experto |
| Cobertura | Universo fijo y piso dimensional del 50%, comparado con 25/75/100%. | Decisión del autor; evaluada mediante robustez; sin panel experto |
| Satélite | Luminosidad fuera del índice por representatividad espacial y estacional no acreditada; QA recuperado como diagnóstico; mapa como contexto. | Aprobada por el autor |
| Estimaciones del proveedor | Se mantienen etiquetadas; la robustez compara la retirada de estimaciones WEO verificadas. | Aprobada por el autor |
| Pulse | Monitor de corto plazo del entorno externo y petrolero; no replica el índice anual. Pronóstico público de persistencia. | Aprobada por el autor |
| Lectura 2026 | Año provisional: el cambio publicado incluye un efecto de composición grande. No se describe como recuperación de la misma magnitud. | Aprobada por el autor |

## Cierre del trabajo individual

El autor aclaró el 28 de octubre de 2026 que no tiene asesor y que la entrega exigida es el artículo IEEE. Por tanto, no corresponde mantener una aprobación de asesor como trámite pendiente. Las decisiones quedan documentadas como juicios del autor, con sus escenarios y límites; esto no equivale a validación externa de contenido.

La release `tesis-2026-10b` permanece inmutable. Las correcciones de redacción y reproducción no cambian sus datos, pesos, umbrales ni resultados. La evaluación con especialistas, la anotación humana de sentimiento y el estudio con usuarios se mantienen como trabajo futuro, no como verificaciones ya realizadas.
