# Validación externa · v2.1

Los contrastes usan el mismo índice AHP publicado, con universo fijo y piso de cobertura dimensional del 50%. La IED nunca entra al índice. Para ACNUR y la luminosidad se calcula la variante sin el componente correspondiente (leave-one-out); V-Dem también se contrasta sin la dimensión institucional.

Cada contraste se reporta en dos tramos:

- **Serie oficial** (desde 2012, las seis dimensiones): resultado principal.
- **Serie completa** (desde 2000, incluye el tramo exploratorio sin dimensión institucional): sensibilidad.

Para cada tramo se dan niveles y primeras diferencias, tamaño de muestra, correlaciones de Pearson y Spearman, y una regresión con errores HAC (Newey-West). Los p-valores se ajustan con Holm dentro de cada tramo. Resultados: `iciv/data/processed/external_validation_summary.csv` (columna `tramo`); series alineadas: `external_validation.csv`; tabla resumida y vigente: [RESULTADOS_ACTUALES.md](RESULTADOS_ACTUALES.md).

## Lectura

Una relación en niveles no basta si las diferencias no la sostienen. Significancia, causalidad y capacidad predictiva son afirmaciones distintas. En la versión vigente, los contrastes con ACNUR, luminosidad VIIRS y V-Dem (democracia liberal y estado de derecho) son compatibles con el signo esperado en niveles, y ninguno lo es en primeras diferencias. La lectura defendible es **validez convergente de tendencia**: el índice se mueve en la misma dirección de largo plazo que mediciones independientes. No mide cambios de año a año. La IED no muestra asociación concluyente.

La luminosidad DMSP/VIIRS completa tiene ruptura de sensor y se describe sin prueba confirmatoria. El segmento VIIRS (desde 2014) comparte sensor con Black Marble: un proveedor distinto no equivale a evidencia independiente. V-Dem y los índices institucionales pueden compartir constructos y fuentes; quitar la dimensión institucional reduce la circularidad directa, pero no elimina tendencias comunes.

Las pruebas son exploratorias: muestra anual pequeña, vintages retrospectivos, composición variable y decisiones de diseño del autor. La comparación con PCA usa filas completas de las seis dimensiones, cobertura efectiva ≥80% y mínimo siete años; no imputa valores para aumentar n.

Toda cifra para defensa o tesis debe recalcularse desde la release congelada que se cite.
