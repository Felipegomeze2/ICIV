# Validación externa · v2

Los contrastes usan el mismo índice AHP publicado, con universo fijo y piso de cobertura dimensional del 50%. La IED nunca entra al índice. Para UNHCR y luminosidad se calcula la variante sin el componente correspondiente; V-Dem también se contrasta sin D3.

Cada contraste reporta niveles y primeras diferencias, tamaño de muestra, correlaciones y regresión con errores HAC. Los p-valores inferenciales se ajustan conjuntamente con Holm. Consultar `external_validation_summary.csv`; `external_validation.csv` contiene las series alineadas. Una relación de niveles no basta si las diferencias no la sostienen. Significancia, causalidad y capacidad predictiva son afirmaciones distintas.

La luminosidad DMSP/VIIRS completa tiene ruptura de sensor y se describe sin prueba confirmatoria. El segmento VIIRS mantiene sensor compartido con Black Marble: proveedor distinto no equivale a evidencia independiente. V-Dem y los índices institucionales pueden compartir constructos y fuentes; quitar D3 reduce circularidad directa pero no elimina tendencias o dependencia.

Las pruebas son exploratorias: muestra anual pequeña, vintages retrospectivos, composición variable y decisiones de diseño elegidas por el autor. No se describe una hipótesis como confirmada por una sola correlación. PCA usa filas completas de las seis dimensiones, cobertura efectiva ≥80% y mínimo siete años; no imputa valores para aumentar n.

Las presentaciones anteriores a v2 no contienen estos controles. Toda cifra para defensa o tesis debe recalcularse desde la release congelada que se cite.
