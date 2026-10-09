# Metodología ICIV · versión 2.1

## Objeto y alcance

Medir de forma descriptiva la evolución del entorno macroeconómico e institucional venezolano con un indicador compuesto auditable. No se identifica un efecto causal sobre la inversión, no se estima un retorno y no se compara internacionalmente el nivel del índice. La IED es un resultado externo reservado para contraste, nunca un componente del score.

## Política de datos

1. **Solo fuentes internacionales.** Ningún organismo venezolano (BCV, INE, PDVSA, Conatel u otros) se usa como fuente. Algunos organismos internacionales, como el FMI, compilan sus series con información que reciben de los países; esa dependencia indirecta se declara en la ficha de cada serie.
2. **Ningún dato inventado ni falso.** No se interpola, no se arrastran valores, no se rellena con medias y no se reemplaza un proveedor por otro cuando falla una descarga. Un faltante queda como faltante y la cobertura lo refleja.
3. **Valores imposibles del proveedor se excluyen, nunca se sustituyen** (ver *Control de plausibilidad*).
4. Las estimaciones y proyecciones que publican los proveedores (por ejemplo, el WEO del FMI) se etiquetan como tales; no se presentan como observaciones medidas ni como predicciones del proyecto.

## Contrato anual

`iciv/src/iciv/index/dimensions.py` fija 21 variables en seis dimensiones. `AHPWeights` calcula los pesos entre dimensiones desde una matriz de comparación por pares (escala de Saaty). Los pesos internos de cada dimensión son decisiones documentadas del autor; no provienen de un panel de expertos. El CR de la matriz entre dimensiones verifica consistencia interna, no validez económica. Las matrices internas se construyen por cocientes de pesos y son consistentes por construcción (CR = 0), por eso su CR no valida nada.

Matriz entre dimensiones: n = 6, λmax = 6,0501, CI = 0,0100, RI = 1,24, **CR = 0,0081**.

| Dimensión | Peso AHP | Variable | Peso interno | Peso en el índice | Fuente | Dirección |
|---|---:|---|---:|---:|---|---|
| Estabilidad macroeconómica | 25,40% | inflacion_ipc_imf_pct | 0,4000 | 10,16% | FMI WEO | − |
| | | pib_crecimiento_real_pct | 0,3143 | 7,98% | Banco Mundial WDI | + |
| | | wti_precio_usd | 0,1714 | 4,35% | FRED | + |
| | | tasa_fed_funds_pct | 0,1143 | 2,90% | FRED | − |
| Sector energético y petróleo | 19,52% | petroleo_crudo_produccion_tbpd | 0,7500 | 14,64% | EIA | + |
| | | luminosidad_nocturna_idx | 0,2500 | 4,88% | (excluida, ver *Satélite*) | + |
| Entorno institucional y legal | 19,52% | cpi_score | 0,2400 | 4,69% | Transparency International | + |
| | | wgi_promedio_sc | 0,2400 | 4,69% | Banco Mundial WGI | + |
| | | freedom_house_score | 0,1800 | 3,51% | Freedom House | + |
| | | wjp_rule_of_law | 0,1800 | 3,51% | World Justice Project | + |
| | | pts_terror_politico | 0,1600 | 3,12% | Political Terror Scale | − |
| Apertura comercial y financiera | 17,43% | exportaciones_pct_pib | 0,4474 | 7,80% | Banco Mundial WDI | + |
| | | migrantes_vzla_millones | 0,3158 | 5,50% | ACNUR | − |
| | | lsci_conectividad_maritima | 0,2368 | 4,13% | UNCTAD | + |
| Capital humano | 9,06% | hdi | 0,2800 | 2,54% | PNUD vía OWID | + |
| | | esperanza_vida_anos | 0,1800 | 1,63% | Banco Mundial WDI | + |
| | | mortalidad_infantil_x1000 | 0,1800 | 1,63% | Banco Mundial WDI | − |
| | | acceso_electricidad_pct | 0,1800 | 1,63% | Banco Mundial WDI | + |
| | | empleo_vulnerable_oit_pct | 0,1800 | 1,63% | OIT vía WDI | − |
| Percepción internacional | 9,06% | guardian_tono_titulares | 0,6500 | 5,89% | The Guardian + VADER | + |
| | | guardian_articulos_venezuela | 0,3500 | 3,17% | The Guardian | − |

Los pesos efectivos de cada ejecución se exportan en `data_dictionary.csv`. El comparador de pesos iguales aplica 1/6 a cada dimensión y conserva los pesos internos (`iciv_scores.csv`).

**Precio WTI y tasa de la Fed** pertenecen a la dimensión macro como condiciones externas que afectan a una economía petrolera y al costo global del capital. Son iguales para todos los países: su función es capturar el entorno externo que enfrenta Venezuela, no un desempeño propio.

## Tratamiento y escalamiento

1. Conservar el valor original y su unidad. La inflación PCPIPCH es variación porcentual anual del IPC. Empleo vulnerable no es informalidad.
2. CPI anterior a 2012 queda fuera por ruptura metodológica del propio índice. Una edición doble de WJP se registra una sola vez, en el año final.
3. **Control de plausibilidad** (`iciv/src/iciv/data/plausibility.py`):
   - *Valor imposible*: se excluye del cálculo y el año queda sin dato. Caso vigente: el Banco Mundial publica `NE.EXP.GNFS.ZS` = 0 para Venezuela en 1995–2011; un exportador de petróleo no puede tener exportaciones nulas.
   - *Valor repetido*: rachas de cinco años o más con el mismo valor en series continuas. Solo se marcan; el valor no cambia. Caso vigente: mortalidad infantil del Banco Mundial idéntica en 2016–2024.
   - Cada observación afectada se registra en `data/processed/plausibilidad_proveedor.csv` con el valor original del proveedor. El dataset largo marca su estado.
4. Inflación positiva con log10; valores no positivos no se convierten en una constante.
5. Min-max sobre el panel histórico de la release. Las variables de dirección negativa se invierten. Rango cero o falta de observaciones produce NaN. Los extremos se exportan; las revisiones de los proveedores pueden cambiar toda la historia.

El índice anual usa la información retrospectiva del vintage actual. No representa lo que un decisor sabía en cada año. No se inventa una fecha de publicación cuando no está archivada.

## Serie oficial y tramo exploratorio

La **serie oficial va de 2012 a 2026**. Desde 2012 las seis dimensiones superan el piso de cobertura. Antes de 2012 la dimensión institucional no lo alcanza (CPI comparable desde 2012, WJP desde 2012, Freedom House en escala 0–100 desde 2013) y, al excluir los ceros imposibles de exportaciones, la apertura comercial tampoco se publica en 2000–2005.

Los años 2000–2011 se calculan y publican como **tramo extendido exploratorio**: composición distinta, sin dimensión institucional y con cobertura efectiva de 58–68%. No se comparan con la serie oficial ni se usan para "mejor" o "peor" año. Cada fila del score lleva la columna `tramo_serie` (`oficial` o `extendido_exploratorio`), definida en `OFFICIAL_SERIES_START` de `aggregator.py`.

## Agregación y cobertura

Cada dimensión promedia el puntaje de sus variables disponibles con los pesos declarados, renormalizados. Se exige al menos 50% del peso de la dimensión. El índice agrega solo las dimensiones publicables y renormaliza sus pesos.

La cobertura observada es el peso original de todas las variables disponibles dividido por el universo fijo. La cobertura efectiva cuenta solo las variables de dimensiones que superaron el piso. `cobertura_pct` es alias de la efectiva. Una columna ausente reduce la cobertura; no reduce el denominador.

Bandas descriptivas: [0,31) muy desfavorable; [31,51) desfavorable; [51,66) intermedio; [66,81) favorable; [81,100] muy favorable. Son posiciones relativas a la historia venezolana, no probabilidades de pérdida ni calificaciones crediticias. Los cortes son convenciones del autor.

## Agregados parciales

La producción anual EIA (producto 57) del año en curso puede derivarse de al menos tres meses del mismo producto. Se registra el número de meses en `anualizacion_parcial.csv` y se conserva la observación anual publicada cuando existe. Un promedio del año corrido no es un dato anual cerrado.

## Satélite

La luminosidad nocturna queda fuera del score anual y del Pulse. La muestra estricta de NASA Black Marble (calidad 0, más de tres observaciones válidas por píxel) no alcanza cobertura espacial y estacional suficiente para una media nacional comparable. No se usa Li et al. como sustituto. La variable conserva su peso en el denominador de cobertura para no inflar la cobertura al excluirla; por eso la dimensión energética publica con 75% de cobertura y depende de la producción petrolera. El mapa estatal es contexto visual. Ver [diagnóstico satelital](REVISION_SATELITAL.md).

## Señal mensual (Pulse)

Quince variables en `PULSE_WEIGHTS` (`pulse_aggregator.py`):

| Bloque | Peso | Variables |
|---|---:|---|
| Condiciones externas | 35% | WTI, Brent, Dubai (Pink Sheet), tasa Fed, índice dólar, VIX, bono EE.UU. 10 años, spread de bonos emergentes |
| Producción petrolera | 25% | Petróleo y otros líquidos, EIA (producto 53) |
| Comercio petrolero con EE.UU. | 10% | Importaciones de EE.UU. desde Venezuela, crudo y productos (EIA MCRIMUSVE2, MTPIMUSVE2) |
| Cobertura internacional | 30% | Volumen y tono de The Guardian y GDELT |

Cada valor se normaliza solo con el rango observado hasta ese mes (min-max expansivo, sin usar datos futuros). Publicación mínima: 30% del peso. Elegibilidad para modelado: 70% de cobertura normalizable, producción doméstica disponible y mes cerrado. La portada muestra el mes en curso aunque su cobertura sea baja, siempre marcado como provisional, junto con el último mes elegible.

**Lectura correcta.** El Pulse es un monitor de corto plazo del entorno externo y petrolero de Venezuela, y de su visibilidad en la prensa internacional. No replica el índice anual: casi dos tercios de su peso son condiciones globales y prensa. Su relación con el índice anual es moderada en niveles y débil en cambios; el valor exacto de cada ejecución se publica en [RESULTADOS_ACTUALES.md](RESULTADOS_ACTUALES.md).

Se exportan cambios totales, cambios sobre componentes comunes y efecto de composición a uno y tres meses.

**Semáforo SATV.** Agrupa el Pulse en los cuatro bloques anteriores y los lee en el último mes elegible: crítico bajo 30, precaución bajo 50. Las alertas de cobertura y composición se evalúan sobre el último mes publicado. Umbrales heurísticos, no probabilidades.

## Validación y escenarios

La validación externa aplica el mismo AHP y piso dimensional. Reporta la serie oficial y la serie completa, en niveles y en primeras diferencias, con errores HAC y ajuste Holm dentro de cada tramo. Es exploratoria: muestra anual pequeña, tendencias compartidas y revisiones de las fuentes. La comparación con PCA usa casos completos, sin rellenar medias.

Los perfiles sectoriales son sensibilidad a pesos supuestos, sin bonos ni penalizaciones manuales.

El pronóstico mensual público es persistencia (naive); se compara con naive estacional y SARIMA sobre los mismos pares origen/horizonte. Ver [backtesting](BACKTESTING_FORECAST.md).

La [robustez ampliada](ROBUSTEZ_AMPLIADA.md) evalúa 79 escenarios deterministas de pesos, normalización, agregación, cobertura, exclusiones e indisponibilidad. `annual_composition.csv` separa el cambio anual con canasta común del efecto de composición. La [auditoría de fuentes](AUDITORIA_FUENTES_ACTUAL.md) acredita el estado WEO por observación cuando coincide la evidencia archivada.

## Alcance descartado

Por decisión del autor (9 de octubre de 2026), quedan fuera de esta entrega y pasan a trabajo futuro: escenarios prospectivos 2027–2030, simulación Monte Carlo, indicadores líderes y comparación regional (Colombia, Perú, Ecuador, Bolivia). La escala relativa a la historia venezolana no permite comparar niveles entre países sin rediseñar la normalización.

## Historial de versiones

- **2.1.0 (9 de octubre de 2026).** Corrección del bloque de comercio del Pulse (las series FRED IR14270/IR14260 eran precios de importación de oro y zinc; se reemplazan por las importaciones de EE.UU. desde Venezuela publicadas por la EIA); control de plausibilidad de valores del proveedor; exclusión de los ceros de exportaciones 2000–2011; serie oficial 2012–2026 con tramo exploratorio declarado; validación externa por tramo; semáforo SATV visible; alcance descartado formalizado.
- **2.0.0 (16–17 de septiembre de 2026).** Satélite fuera del índice, pronóstico de persistencia, validación HAC + Holm, CPI desde 2012, auditoría de 164 valores, 79 escenarios de robustez, releases con hashes.
