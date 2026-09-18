# Metodología ICIV · versión 2.0

## Objeto y alcance

Medir de forma descriptiva la evolución del entorno macroeconómico e institucional venezolano con un indicador compuesto auditable. No se identifica un efecto causal sobre inversión, no se estima un retorno y no se compara internacionalmente el nivel del índice. La IED es un resultado externo reservado para contraste, nunca un componente del score.

## Contrato anual

`iciv/src/iciv/index/dimensions.py` fija 21 variables en seis dimensiones. `AHPWeights` calcula los pesos entre dimensiones desde la matriz declarada; los pesos internos son decisiones del autor, no un panel de expertos empíricamente levantado. El CR de la matriz interdimensional verifica consistencia interna, no validez económica. Las matrices internas construidas por cocientes de pesos son consistentes por construcción.

Los pesos efectivos se exportan en `data_dictionary.csv`. No deben sustituirse por los porcentajes redondeados del antiguo benchmark 25/20/20/15/10/10. El comparador de dimensiones iguales aplica 1/6 a cada dimensión y mantiene sus pesos internos.

## Tratamiento y escalamiento

1. Conservar el valor original y su unidad. La inflación PCPIPCH es variación porcentual anual del IPC. Empleo vulnerable no es informalidad.
2. CPI anterior a 2012 queda fuera por ruptura metodológica. WJP de una edición doble se registra una sola vez al final del período.
3. Transformar inflación positiva con log10; valores no positivos no se convierten en una constante. El cambio oficial se expresa en BsF equivalentes según la convención del archivo WDI: ×1 hasta 2017, ×10⁵ en 2018–2021 y ×10¹¹ desde 2022, antes de log10. Esta convención debe revisarse si el proveedor cambia la denominación de su serie.
4. Min-max anual retrospectivo sobre el panel de la release. Dirección negativa se invierte. Rango cero o falta de observaciones produce NaN. Los extremos y el período se exportan; las revisiones pueden cambiar toda la historia.
5. No interpolar, arrastrar valores, llenar con medias o reemplazar proveedores.

El anual usa información retrospectiva del vintage actual. No representa lo que un decisor sabía en cada año. Los valores del FMI pueden ser estimaciones o proyecciones del proveedor: no deben describirse como observaciones medidas ni como predicciones del proyecto. No se inventa una fecha de publicación cuando no está archivada.

## Agregación y cobertura

Para cada dimensión se promedia el score de sus variables disponibles utilizando los pesos declarados y renormalizándolos. Se exige al menos 50% de su peso disponible. El índice agrega solo dimensiones publicables y renormaliza sus pesos.

La cobertura observada es el peso original de todas las variables disponibles dividido por el universo fijo. La cobertura efectiva cuenta únicamente las variables de dimensiones que superaron el piso. `cobertura_pct` es alias de cobertura efectiva. La ausencia de una columna completa reduce la cobertura; no reduce el denominador.

Las bandas son descriptivas: [0,31) muy desfavorable; [31,51) desfavorable; [51,66) intermedio; [66,81) favorable; [81,100] muy favorable. No son probabilidades de pérdida o calificaciones crediticias. Los puntos de corte son convenciones del autor.

## Agregados parciales

Producción anual EIA producto 57 puede derivarse de al menos tres meses del mismo producto. Se registra el número de meses y se conserva la observación anual publicada si existe. Un promedio de año corrido no es un dato anual cerrado. El registro `anualizacion_parcial.csv` se regenera en cada ejecución, incluso vacío.

Black Marble queda fuera del score anual y de Pulse por decisión explícita de esta revisión. Se recuperó una muestra de `blackmarble_qa_monthly.csv` con calidad 0 y más de tres observaciones válidas por píxel, excluyendo fill, mala calidad y gap-filled. Sin embargo, la cobertura espacial/estacional no acredita una media nacional comparable. No se usa Li et al. como sustituto. La variable conserva su peso en el denominador de cobertura. El mapa previo es contexto sin QA acreditado. Ver [diagnóstico satelital](REVISION_SATELITAL.md).

## Pulse

El universo de 15 variables y sus pesos está en `PULSE_WEIGHTS`. Cada valor se normaliza únicamente con el rango observado hasta ese mes. Con menos de dos valores o sin rango, no hay score utilizable. Cobertura de datos crudos y cobertura normalizable se distinguen. El mínimo de publicación es 30% del peso; elegibilidad para modelado requiere 70%, producción doméstica y mes cerrado.

Se exportan cambios totales, cambios sobre componentes comunes y efecto de composición a uno y tres meses. Un cambio comparable mantiene el conjunto de componentes; aun así puede incorporar movimientos de sus escalas expansivas. No equivale a crecimiento económico.

## Validación y escenarios

La validación externa aplica el mismo AHP y piso dimensional. Reporta niveles y primeras diferencias, intervalos y pruebas HAC y ajuste Holm. Sigue siendo exploratoria por muestra pequeña, dependencia y revisión de fuentes. La comparación con PCA utiliza casos completos, sin rellenar medias.

Los perfiles sectoriales son sensibilidad a pesos supuestos. Se eliminaron bonos defensivos, penalizaciones CAPEX y sanciones inferidas de instituciones. Se requieren todas las dimensiones del perfil; no se generan recomendaciones de entrada.

El pronóstico mensual es persistencia prespecificada; los errores se comparan con naive estacional y SARIMA en pares comunes. Ver [backtesting](BACKTESTING_FORECAST.md).

La [robustez ampliada](ROBUSTEZ_AMPLIADA.md) añade 79 escenarios deterministas de pesos, normalizadores, agregación, cobertura, exclusiones e indisponibilidad. No son observaciones sintéticas ni intervalos de confianza. `annual_composition.csv` separa cambio anual con canasta común y residuo de composición manteniendo el piso dimensional. La [auditoría de fuentes](AUDITORIA_FUENTES_ACTUAL.md) acredita el estado WEO por observación solo cuando coincide la evidencia archivada.
