# ICIV — Indicador de Clima de Inversión de Venezuela

**Diseño metodológico, pipeline de datos automatizado y tablero de inteligencia de negocios para el seguimiento del entorno de inversión venezolano (2012–2026)**

Trabajo de grado — Especialización en Big Data e Inteligencia de Negocios
Universidad EIA

Autor: Felipe Gómez Espinal
Fecha del borrador: 9 de octubre de 2026 · Versión metodológica del sistema: 2.1

---

> **Estado de este borrador.** Contiene solo las partes estables del documento: introducción, problema, objetivos, marco teórico, búsqueda de información y arquitectura de datos. Los capítulos de metodología detallada, resultados, discusión y conclusiones se redactarán sobre la release congelada de la tesis, para que todas las cifras sean citables y reproducibles. Las marcas **[citar]** indican afirmaciones que necesitan referencia antes de la entrega. Las marcas **[completar]** indican datos que se llenan al ejecutar la búsqueda bibliográfica o al congelar la release. Ninguna cifra de resultados aparece aquí a propósito.

---

## Resumen (borrador)

Venezuela carece de un instrumento público, trazable y reproducible para seguir su clima de inversión. Las estadísticas oficiales se publicaron de forma irregular durante la crisis, y las lecturas disponibles mezclan percepción, noticias y datos macroeconómicos sin una estructura comparable. Este trabajo diseña, construye y publica el ICIV, un indicador compuesto descriptivo del entorno de inversión venezolano. Está construido exclusivamente con fuentes internacionales y procesado por un pipeline de datos automatizado.

El sistema tiene tres componentes:

- un índice anual de 21 variables en seis dimensiones (macroeconomía, energía, instituciones, apertura comercial, capital humano y percepción internacional), ponderado con el Proceso Analítico Jerárquico (AHP);
- una señal mensual de 15 variables (Pulse) que monitorea el entorno externo y petrolero;
- un semáforo de alertas descriptivas (SATV).

Los resultados se publican en un tablero web que se actualiza cada semana con GitHub Actions. La arquitectura aplica controles de calidad de datos: universo fijo de variables, preservación de faltantes, exclusión y registro de valores imposibles del proveedor, verificación de la identidad de las series y releases con hashes criptográficos.

La validación combina análisis de sensibilidad de pesos, comparación con pesos iguales y con PCA, 79 escenarios de robustez, contrastes externos sin circularidad (*leave-one-out*) contra migración, luminosidad satelital y V-Dem, y un *backtesting* del pronóstico mensual. **[completar con los resultados principales de la release congelada]**

**Palabras clave:** indicador compuesto, clima de inversión, Venezuela, AHP, nowcasting, pipeline de datos, calidad de datos, inteligencia de negocios, reproducibilidad.

---

## 1. Introducción

### 1.1 Contexto

Entre 2013 y 2021 Venezuela atravesó una de las contracciones económicas más profundas registradas en tiempos de paz fuera de una guerra **[citar]**. El colapso combinó la caída de la producción petrolera, hiperinflación, sanciones financieras y petroleras, deterioro institucional y una emigración masiva. Para un inversionista, un analista de riesgo o un investigador, seguir ese entorno es difícil por dos razones:

- **La información oficial dejó de ser confiable o se dejó de publicar.** El banco central suspendió durante años la publicación regular de indicadores clave **[citar]**, y el país no tuvo consultas del Artículo IV con el FMI durante un período prolongado **[citar]**.
- **Las lecturas disponibles están fragmentadas.** Calificaciones de riesgo, índices institucionales internacionales, noticias y datos de comercio se publican en frecuencias, escalas y rezagos distintos, sin una estructura común que permita compararlos en el tiempo.

En 2026 el entorno volvió a cambiar de forma abrupta: la cobertura internacional registra la salida de Nicolás Maduro en enero y un acuerdo petrolero con Estados Unidos en agosto. Esto refuerza la necesidad de un instrumento que se actualice con frecuencia y que separe con claridad lo que está medido de lo que es provisional.

### 1.2 Planteamiento del problema

No existe un indicador público del clima de inversión venezolano que cumpla a la vez cuatro condiciones:

1. **Trazabilidad:** cada cifra puede rastrearse hasta su fuente y su versión.
2. **Independencia de fuentes nacionales:** el cálculo no depende de organismos venezolanos cuya publicación fue irregular durante la crisis.
3. **Cobertura longitudinal con calidad declarada:** la serie histórica es continua y cada período declara qué parte del indicador está realmente medida.
4. **Actualización y reproducibilidad:** cualquier tercero puede regenerar el indicador desde los datos y el código públicos.

Las herramientas existentes cubren solo parte de estas condiciones. Los índices globales comparan países pero no se diseñaron para seguir un caso con fuertes rupturas y faltantes. Las calificaciones de riesgo son productos propietarios y no reproducibles. Los análisis académicos sobre Venezuela suelen ser estudios puntuales, no instrumentos de seguimiento.

### 1.3 Pregunta de investigación

¿Es posible construir, solo con fuentes internacionales verificables y un pipeline reproducible, un indicador compuesto que describa la evolución del clima de inversión de Venezuela, declare explícitamente su cobertura y sus limitaciones, y muestre coherencia con mediciones externas independientes?

### 1.4 Justificación

**Académica.** El trabajo aplica el marco de construcción de indicadores compuestos (OECD & JRC, 2008) a un caso extremo de escasez y ruptura de datos. Documenta las decisiones que en la literatura suelen quedar implícitas: imputación, normalización, ponderación, cobertura y validación. Aporta evidencia sobre lo que puede y no puede afirmarse con un indicador así.

**Práctica.** Ofrece a analistas, investigadores, prensa y organismos que siguen a Venezuela desde fuera un tablero público y gratuito con la evolución del entorno, sus componentes y la calidad de cada lectura.

**Desde Big Data e inteligencia de negocios.** El proyecto integra fuentes heterogéneas en frecuencia, formato y semántica: APIs estadísticas, series financieras diarias, texto periodístico, ráster satelital y archivos institucionales. Las convierte en un producto analítico con gobierno de datos explícito: linaje por observación, controles de calidad automatizados, versionado y despliegue continuo.

### 1.5 Alcance y limitaciones

- **Descriptivo, no causal.** El índice describe la posición relativa de Venezuela respecto de su propia historia. No estima el efecto de ninguna variable sobre la inversión ni predice rentabilidad.
- **Escala relativa.** La normalización usa la historia venezolana como referencia. Un puntaje "favorable" significa favorable respecto del pasado del país, no respecto de otros países.
- **Serie oficial 2012–2026.** Antes de 2012 la dimensión institucional no alcanza la cobertura mínima. Los años 2000–2011 se publican como tramo exploratorio, no comparable.
- **Fuentes revisables.** Los proveedores revisan sus series. Los resultados corresponden a la release congelada que se cite.
- **Alcance descartado.** Escenarios prospectivos 2027–2030, simulación Monte Carlo, indicadores líderes y comparación regional quedan como trabajo futuro (ver sección 2.3).

---

## 2. Objetivos

### 2.1 Objetivo general

Diseñar, construir y publicar un indicador compuesto, transparente y reproducible del clima de inversión de Venezuela, basado exclusivamente en fuentes internacionales verificables, con cobertura declarada por período y reglas explícitas de calidad de datos.

### 2.2 Objetivos específicos

- **OE1.** Integrar variables macroeconómicas, energéticas, institucionales, comerciales, de capital humano y de percepción en un índice anual de seis dimensiones, con ponderación AHP de consistencia verificada.
- **OE2.** Desarrollar un pipeline automatizado que extraiga, valide, transforme, normalice y agregue datos de más de quince fuentes internacionales sin intervención manual, preservando los faltantes y el linaje de cada observación.
- **OE3.** Implementar una señal mensual (Pulse) que monitoree el entorno externo y petrolero entre publicaciones anuales, con indicación explícita de cobertura y elegibilidad.
- **OE4.** Publicar un tablero interactivo de acceso público, actualizado automáticamente, con lectura ejecutiva, historia, mapa de contexto, noticias internacionales, sensibilidad sectorial, laboratorio de escenarios y evidencia descargable.
- **OE5.** Documentar la metodología, las fuentes, los criterios de inclusión y exclusión y las decisiones de diseño para que el sistema sea auditable y replicable.
- **OE6.** Evaluar el indicador mediante análisis de sensibilidad de pesos, comparación con pesos iguales y PCA, escenarios de robustez, validación externa no circular (*leave-one-out*) y *backtesting* con origen móvil del pronóstico mensual.

### 2.3 Cambios respecto al anteproyecto

| Elemento del anteproyecto (mayo de 2026) | Estado final | Razón |
|---|---|---|
| 26 variables core a seleccionar | 21 variables | Se retiraron cinco series que el proveedor dejó de publicar por más de tres años o cuyo rezago impedía cubrir el año anterior (reservas, tipo de cambio oficial, desempleo, gas natural, electricidad). |
| Pulse de 11 variables | 15 variables | Se añadieron crudo Dubai, spread de bonos emergentes e importaciones de EE.UU. desde Venezuela (crudo y productos). |
| Luminosidad nocturna en el índice | Fuera del índice; mapa de contexto | La muestra satelital con control de calidad estricto no alcanzó cobertura espacial y estacional suficiente para una media nacional comparable. |
| Forecast SARIMA | Persistencia como pronóstico público; SARIMA como comparador | En el *backtesting* con muestra común, SARIMA no superó a la persistencia. |
| Imputación por interpolación entre datos reales | Sin imputación | Regla más estricta: ningún valor que el proveedor no haya publicado. |
| Sección bibliográfica en el tablero | Documentación en el repositorio | El tablero se orientó al usuario final; la metodología vive en la documentación. |
| Escenarios 2027–2030, Monte Carlo, indicadores líderes y comparación regional | Descartados para esta entrega | Prioridad a la calidad y validación del núcleo. La escala relativa no permite comparar niveles entre países sin rediseñar la normalización. |
| Serie 2000–2026 | Serie oficial 2012–2026; 2000–2011 exploratorio | Cobertura institucional insuficiente antes de 2012. |

---

## 3. Marco teórico

### 3.1 El clima de inversión

El Banco Mundial define el clima de inversión como el conjunto de factores específicos de un lugar que moldean las oportunidades e incentivos de las empresas para invertir productivamente, crear empleo y expandirse (World Bank, 2004). La definición distingue factores sobre los que el Estado tiene influencia directa (estabilidad macroeconómica, seguridad jurídica, regulación, infraestructura) de factores externos o geográficos.

La teoría ecléctica de Dunning (1980) explica la inversión extranjera directa por la combinación de ventajas de propiedad, localización e internalización. El clima de inversión se relaciona sobre todo con las **ventajas de localización**: lo que un país ofrece o deja de ofrecer frente a alternativas. La literatura empírica muestra que la calidad institucional y el riesgo político son determinantes relevantes de la inversión extranjera (Bénassy-Quéré et al., 2007; Busse & Hefeker, 2007). En los mercados emergentes, además, las condiciones financieras globales y la integración con los mercados internacionales afectan el costo del capital (Bekaert & Harvey, 2003).

Esta literatura justifica las seis dimensiones del ICIV:

- **Estabilidad macroeconómica:** incluye condiciones externas como el precio del petróleo y la tasa de interés de EE.UU., relevantes para una economía petrolera que compite por capital global.
- **Sector energético:** el motor de divisas e ingresos fiscales de Venezuela.
- **Entorno institucional y legal.**
- **Apertura comercial y financiera.**
- **Capital humano.**
- **Percepción internacional.**

La medición del clima de inversión ha tenido instrumentos influyentes y también críticas. El informe *Doing Business* del Banco Mundial se descontinuó en 2021 y fue sucedido por *Business Ready* (World Bank, 2024) **[citar comunicado de descontinuación]**. Los Indicadores Mundiales de Gobernanza (Kaufmann et al., 2010) agregan percepciones de múltiples fuentes sobre seis dimensiones de gobernanza. Las calificaciones de riesgo país son productos propietarios con metodologías parcialmente públicas. Ninguno de estos instrumentos se diseñó para seguir con frecuencia y transparencia un caso con rupturas severas de datos, que es el vacío que aborda este trabajo.

### 3.2 Indicadores compuestos

Un indicador compuesto combina indicadores individuales en un índice único según un modelo subyacente del fenómeno (Nardo et al., 2005). El manual de la OCDE y el Centro Común de Investigación de la Comisión Europea (OECD & JRC, 2008) propone diez etapas:

1. Marco teórico.
2. Selección de datos.
3. Imputación de faltantes.
4. Análisis multivariado.
5. Normalización.
6. Ponderación.
7. Agregación.
8. Análisis de incertidumbre y sensibilidad.
9. Vínculo con otras variables.
10. Visualización.

El ICIV sigue esa secuencia y documenta la decisión tomada en cada etapa.

Los indicadores compuestos son útiles para resumir fenómenos multidimensionales y comunicarlos, pero tienen riesgos conocidos. Saltelli (2007) los describe como herramientas situadas entre el análisis y la promoción: la elección de variables, pesos y agregación puede producir conclusiones distintas a partir de los mismos datos. Paruolo et al. (2013) muestran que los pesos nominales de un índice no equivalen a la importancia efectiva de cada variable en el resultado. Becker et al. (2017) proponen medir esa brecha. Greco et al. (2019) revisan las alternativas de ponderación, agregación y robustez, y concluyen que ninguna es neutral. Por eso el ICIV publica la sensibilidad de sus resultados a decisiones alternativas en lugar de presentar un resultado único como definitivo.

**Ponderación con AHP.** El Proceso Analítico Jerárquico (Saaty, 1980, 1990) obtiene pesos a partir de comparaciones por pares en una escala de 1 a 9. El vector de pesos es el vector propio principal de la matriz de comparaciones. La razón de consistencia (CR) compara la inconsistencia de los juicios con la de matrices aleatorias; por convención, CR < 0,10 se considera aceptable. El CR mide coherencia interna de los juicios, no su validez económica. Por eso el ICIV complementa el AHP con un comparador de pesos iguales, una ponderación por componentes principales (PCA) y escenarios de pesos alternativos.

**Agregación y compensabilidad.** La agregación lineal permite que un buen desempeño en una dimensión compense uno malo en otra. La geométrica reduce esa compensación (Greco et al., 2019). El ICIV usa agregación lineal como base y reporta la geométrica como escenario de robustez.

### 3.3 Normalización y escalas relativas

La normalización lleva variables con unidades distintas a una escala común. La normalización min-max reescala cada variable entre su mínimo y su máximo observados (OECD & JRC, 2008). Es fácil de interpretar, pero sensible a valores extremos y dependiente del período de referencia. Cuando una variable recorre varios órdenes de magnitud, como la inflación venezolana durante la hiperinflación, una transformación logarítmica previa evita que unos pocos años extremos aplasten el resto de la serie.

Normalizar contra la historia del propio país produce una **escala relativa**: 100 representa el mejor registro de Venezuela en el período, no un estándar internacional. Esta propiedad es adecuada para seguir la evolución de un caso, pero impide comparar niveles entre países. Es una de las razones por las que la comparación regional se dejó fuera del alcance.

### 3.4 Indicadores de alta frecuencia, nowcasting y evaluación de pronósticos

El *nowcasting* estima el estado presente de la economía con información que se publica antes que las estadísticas oficiales de baja frecuencia (Giannone et al., 2008). Los índices de difusión (Stock & Watson, 2002) y los índices de condiciones de negocio en tiempo real (Aruoba et al., 2009) muestran que muchas series de alta frecuencia pueden resumirse en una señal común.

Un modelo de pronóstico solo agrega valor si supera a referencias simples. La persistencia (el último valor observado se mantiene) y el naive estacional son las referencias estándar (Hyndman & Athanasopoulos, 2021). La evaluación debe hacerse fuera de muestra, con origen móvil y sin usar información futura (Tashman, 2000). Cuando ningún modelo supera a la persistencia, la conclusión honesta es publicar la persistencia como pronóstico y reportar el resultado negativo. Ese es el criterio que adoptó el ICIV para su señal mensual.

### 3.5 Datos alternativos: luminosidad nocturna y texto

**Luminosidad nocturna.** La radiancia nocturna captada por satélite se ha usado como indicador indirecto de actividad económica cuando las cuentas nacionales son débiles o inexistentes (Chen & Nordhaus, 2011; Henderson et al., 2012). El producto Black Marble de la NASA ofrece radiancia diaria y mensual corregida por geometría, atmósfera, luz lunar y nieve, con indicadores de calidad por píxel (Román et al., 2018). Li et al. (2020) armonizan las series de los sensores DMSP y VIIRS en una serie larga, aunque con una ruptura entre sensores. El uso de luminosidad exige controlar la nubosidad, la cobertura espacial válida y la quema de gas en zonas petroleras. Estas razones llevaron al ICIV a excluirla del índice y usarla como contexto y validación externa.

**Texto y noticias.** El tono de las noticias contiene información económica: Tetlock (2007) encuentra que el pesimismo en la prensa financiera anticipa movimientos de precios, y Baker et al. (2016) construyen un índice de incertidumbre de política económica a partir de la frecuencia de términos en la prensa. Gentzkow et al. (2019) revisan el uso del texto como dato en economía. VADER es un modelo de sentimiento basado en reglas, diseñado para textos cortos (Hutto & Gilbert, 2014). GDELT monitorea la cobertura mediática global y su tono (Leetaru & Schrodt, 2013). Estas fuentes tienen sesgos de idioma, medio y selección. En el ICIV se usan como medida de percepción internacional, no como opinión pública representativa.

### 3.6 Big Data e inteligencia de negocios

Laney (2001) caracterizó los datos masivos por su volumen, velocidad y variedad. En el ICIV el desafío principal no es el volumen tabular, sino:

- **Variedad:** APIs estadísticas, series financieras diarias, texto, archivos institucionales y ráster satelital, con frecuencias desde diaria hasta anual.
- **Velocidad:** actualización semanal automatizada.
- **Volumen localizado:** el procesamiento satelital (millones de píxeles por mes).

La inteligencia de negocios y la analítica convierten datos en información útil para decidir (Chen et al., 2012). El ICIV aplica ese enfoque: el panel largo de observaciones se organiza como una tabla de hechos con dimensiones de variable, fuente, tiempo y estado, siguiendo los principios del modelado dimensional (Kimball & Ross, 2013). Se presenta además en un tablero diseñado para lectura rápida y jerarquizada (Few, 2006).

### 3.7 Calidad de datos y reproducibilidad

Wang y Strong (1996) definen la calidad de datos desde la perspectiva del usuario e identifican dimensiones como exactitud, oportunidad, completitud, consistencia e interpretabilidad. El ICIV traduce esas dimensiones en controles automatizados:

| Dimensión | Control en el ICIV |
|---|---|
| Exactitud | Contraste de valores contra archivos oficiales; exclusión de valores imposibles del proveedor; verificación de la identidad de las series. |
| Oportunidad | Control de vigencia de cada fuente contra su calendario de publicación. |
| Completitud | Cobertura declarada por variable, dimensión y período, sobre un universo fijo. |
| Consistencia | Una fuente por serie, sin empalmar bases distintas ni sustituir proveedores. |
| Interpretabilidad | Distinción entre observación, estimación del proveedor y agregado parcial. |

En contextos de crisis la calidad de las estadísticas oficiales puede deteriorarse hasta volverse inutilizable (Jerven, 2013). Eso fundamenta la política de usar solo fuentes internacionales.

La reproducibilidad computacional exige que datos, código y entorno permitan regenerar cada resultado (Peng, 2011; Sandve et al., 2013). Los principios FAIR piden que los datos sean localizables, accesibles, interoperables y reutilizables (Wilkinson et al., 2016). El ICIV publica código, datos crudos, dataset procesado, diccionario, manifiesto con hashes y un script de verificación.

### 3.8 Validación de indicadores compuestos

Un indicador compuesto no tiene un valor "verdadero" contra el cual compararse. Su validez se evalúa por coherencia interna, robustez a decisiones de diseño y **validez convergente**: asociación con mediciones independientes del mismo fenómeno o de fenómenos relacionados (OECD & JRC, 2008; Saisana et al., 2005).

Dos riesgos estadísticos son centrales:

- **Correlaciones espurias.** Dos series con tendencia pueden correlacionarse aunque no estén relacionadas. Por eso se reportan niveles y primeras diferencias, y se usan errores estándar robustos a heterocedasticidad y autocorrelación (Newey & West, 1987).
- **Comparaciones múltiples.** Al probar varios contrastes aumenta la probabilidad de falsos positivos. El ajuste de Holm (1979) controla ese error.

Para evitar la **circularidad**, cada contraste se hace con el índice recalculado sin la variable o dimensión que se contrasta (*leave-one-out*).

### 3.9 Contexto venezolano 2000–2026

La economía venezolana depende del petróleo como fuente principal de divisas e ingresos fiscales **[citar]**. Hitos que el indicador debe poder reflejar:

- **2002–2003:** paro petrolero.
- **2007:** nacionalizaciones en sectores estratégicos.
- **2014:** caída del precio del petróleo.
- **2017 en adelante:** hiperinflación (la inflación del IPC según el FMI superó el 65.000% en 2018).
- **2017 y 2019:** sanciones financieras y petroleras de EE.UU.
- **Marzo de 2019:** apagón nacional.
- **2020:** contracción asociada a la pandemia.
- **Desde 2015:** emigración de millones de personas registrada por ACNUR y la plataforma R4V **[citar cifras de la fuente]**.
- **2026:** salida de Maduro en enero y acuerdo petrolero con EE.UU. en agosto, según la cobertura internacional.

Hausmann y Rodríguez (2014) y Corrales y Penfold (2015) analizan los antecedentes y la economía política del colapso.

---

## 4. Búsqueda de información

### 4.1 Protocolo de búsqueda bibliográfica

**Objetivo.** Identificar literatura sobre (a) construcción y validación de indicadores compuestos, (b) determinantes y medición del clima de inversión, (c) nowcasting e indicadores de alta frecuencia, (d) datos alternativos (luminosidad y texto), (e) calidad de datos y reproducibilidad, y (f) economía venezolana reciente.

**Bases consultadas.** Scopus, Web of Science, Google Scholar, RePEc/IDEAS, SSRN y los repositorios de la OCDE, el Banco Mundial y el FMI. **[confirmar las bases efectivamente usadas]**

**Ecuaciones de búsqueda (ejemplos):**

- `"composite indicator*" AND (weighting OR "sensitivity analysis" OR robustness)`
- `"analytic hierarchy process" AND "composite index"`
- `("investment climate" OR "business environment") AND (measurement OR index)`
- `("foreign direct investment") AND (institutions OR "political risk")`
- `nowcasting AND ("high-frequency" OR "dynamic factor")`
- `("night lights" OR "nighttime lights" OR luminosity) AND (GDP OR "economic activity")`
- `("news sentiment" OR "text as data") AND economics`
- `"data quality" AND (dimensions OR framework)`
- `Venezuela AND (hyperinflation OR "economic collapse" OR "oil production")`

**Criterios de inclusión.** Artículos revisados por pares, libros académicos y documentos metodológicos de organismos internacionales; en inglés o español; con aporte directo a alguna de las seis áreas. Para la metodología no se restringe el año; para el contexto venezolano se priorizan publicaciones desde 2010.

**Criterios de exclusión.** Notas de opinión sin metodología, documentos sin autoría identificable y fuentes que no permitan verificar sus datos.

**Registro.** Número de resultados por base, duplicados eliminados, documentos revisados por título y resumen, y documentos incluidos. **[completar]**

### 4.2 Antecedentes

**[completar tras la búsqueda]** Organizar en cuatro grupos:

1. Índices globales de clima de negocios y gobernanza: *Doing Business* y *Business Ready*, WGI, índices de libertad económica.
2. Calificaciones de riesgo país y sus limitaciones de transparencia.
3. Indicadores compuestos aplicados a economías en crisis o con datos escasos.
4. Estudios sobre la economía venezolana que usan fuentes alternativas: luminosidad, comercio espejo, migración.

Para cada antecedente, indicar qué mide, con qué fuentes, con qué frecuencia y qué limitación del problema planteado deja abierta.

### 4.3 Búsqueda y selección de fuentes de datos

La búsqueda de fuentes aplicó seis criterios:

1. Origen internacional (ningún organismo venezolano como fuente).
2. Acceso público y descarga automatizable.
3. Cobertura histórica suficiente.
4. Rezago de publicación compatible con el seguimiento.
5. Correspondencia semántica entre la serie y el concepto que se quiere medir.
6. No redundancia con otras variables.

Decisiones documentadas en el repositorio:

| Fuente o serie evaluada | Decisión | Motivo |
|---|---|---|
| Heritage (libertad económica) y Fraser | No usadas | Bloquean la descarga automatizada (HTTP 403). |
| OPEP, informe mensual | No usada | Bloquea la descarga automatizada. |
| Desempleo modelado por la OIT como sustituto del FMI | Descartado | Difiere hasta 85% de la serie del FMI y no refleja el colapso laboral. |
| Reservas, tipo de cambio oficial, desempleo, gas natural, electricidad | Retiradas del índice | El proveedor dejó de publicarlas o el rezago impide cubrir el año anterior. |
| Salud de la OMS | Reemplazada por el Banco Mundial | Mayor actualidad, con comparabilidad verificada; sin empalmar series. |
| Luminosidad de Li et al. y Black Marble | Fuera del índice | Cobertura válida insuficiente y ruptura de sensor; se usan como contexto y validación. |
| Exportaciones (% del PIB), Banco Mundial | Usada desde 2012 | El proveedor publica 0 en 1995–2011, valor imposible que se excluye. |
| Comercio espejo IMF IMTS y UN Comtrade | Capas auxiliares | Útiles como contexto; mayor rezago o cobertura parcial de socios. |
| Importaciones de EE.UU. desde Venezuela (EIA) | Usada en el Pulse | Registro de aduana del socio, volumen físico, rezago corto. |
| ACLED (eventos de conflicto) | Capa auxiliar | El nivel de acceso disponible entrega datos con unos 12 meses de rezago. |
| V-Dem | Solo validación | Mide constructos cercanos a la dimensión institucional; no entra al índice. |

---

## 5. Arquitectura y diseño de datos

### 5.1 Visión general

El sistema es un pipeline en Python orquestado por `iciv/main.py`, con estas fases:

1. Extracción opcional desde las fuentes.
2. Carga y control de plausibilidad.
3. Transformación y normalización.
4. Cálculo del índice anual.
5. Cálculo de la señal mensual y del semáforo.
6. Pronóstico y *backtesting*.
7. Validación externa y robustez.
8. Generación del tablero.
9. Empaquetado de la release.

El código está organizado en módulos: datos, procesamiento, índice, señal mensual y alertas, aprendizaje automático y analítica. Cuenta con pruebas automatizadas en Python y JavaScript.

### 5.2 Capas de datos

| Capa | Ubicación | Contenido |
|---|---|---|
| Cruda | `iciv/data/raw/` | Un archivo por fuente, tal como lo publica el proveedor. |
| Evidencia | `iciv/data/sources/` | Archivos oficiales descargados para auditoría, con URL, fecha y hash. |
| Procesada | `iciv/data/processed/` | Panel transformado y normalizado, scores, señal mensual, validación, robustez y registro de plausibilidad. |
| Release | `iciv/data/releases/<id>/` | Copia congelada de datos, diccionario, cobertura, procedencia y manifiesto con hashes SHA-256. |
| Producto | `iciv_dashboard.html` | Tablero autocontenido, publicado en GitHub Pages. |

### 5.3 Modelo de datos

El dataset largo (`iciv_dataset_largo.csv`) funciona como tabla de hechos: una fila por año y variable, con valor crudo, transformado y normalizado. Sus atributos descriptivos actúan como dimensiones:

- **Variable:** descripción, unidad, dirección y dimensión del índice.
- **Fuente:** proveedor y archivo de origen.
- **Tiempo:** año, meses usados en agregados parciales.
- **Estado:** observación publicada, estimación del proveedor, agregado parcial, valor excluido por plausibilidad, sin dato.

El diccionario de datos se genera desde el catálogo del código, de modo que documentación y cálculo no pueden divergir.

### 5.4 Automatización y despliegue

Dos flujos de GitHub Actions sostienen la operación:

- **Integración continua:** en cada cambio ejecuta las pruebas, reproduce el pipeline desde los datos archivados y verifica la release.
- **Actualización programada:** cada lunes descarga las fuentes de alta frecuencia; el primer día de cada mes, además, las anuales. Luego controla la vigencia de cada fuente, regenera el índice y el tablero, publica los resultados y despliega en GitHub Pages. Si una fuente crítica está desactualizada, la corrida se marca en rojo después de publicar, para que el problema sea visible.

### 5.5 Controles de calidad

- **Universo fijo:** una fuente ausente reduce la cobertura, no el denominador.
- **Faltantes preservados:** sin interpolación, arrastre ni sustitución de proveedores.
- **Plausibilidad:** valores imposibles excluidos y registrados; rachas repetidas marcadas.
- **Identidad de series:** el fetcher compara la descripción del proveedor con la esperada.
- **Protección contra pérdida de datos:** una descarga fallida no sobrescribe datos válidos.
- **Linaje:** cada observación conserva fuente, estado y transformación.
- **Releases verificables:** hashes SHA-256 y reproducción de normalización, AHP y cobertura.

Los incidentes que motivaron algunos de estos controles están documentados en el repositorio: sobrescritura de una fuente con valores vacíos en agosto de 2026 y series mal identificadas en el bloque de comercio de la señal mensual entre agosto y octubre de 2026.

---

## 6. Metodología (esquema; se redacta sobre la release congelada)

1. Selección de variables y dimensiones: tabla de las 21 variables con fuente, dirección y justificación (ver `docs/METODOLOGIA.md`).
2. Tratamiento de datos: plausibilidad, transformaciones (log10 de inflación), agregados parciales.
3. Normalización min-max sobre la historia venezolana.
4. Ponderación AHP: matriz entre dimensiones, CR, pesos internos declarados, comparadores (pesos iguales, PCA).
5. Agregación, cobertura y piso dimensional; serie oficial y tramo exploratorio.
6. Señal mensual: variables, normalización expansiva, elegibilidad, descomposición del cambio.
7. Semáforo SATV y alertas.
8. Pronóstico y *backtesting*.
9. Validación externa, sensibilidad y robustez.

## 7. Resultados (pendiente de release congelada)

**[completar]** Serie oficial 2012–2026 con cobertura; dimensiones; descomposición del cambio anual; señal mensual y su relación con el índice anual; *backtesting*; validación externa por tramo; robustez; lectura de 2026 como año provisional.

## 8. Discusión (pendiente)

**[completar]** Qué captura el índice y qué no; por qué el Pulse no replica el índice anual; validez convergente de tendencia frente a capacidad de explicar cambios anuales; límites de la escala relativa; aportes desde Big Data e inteligencia de negocios.

## 9. Conclusiones y trabajo futuro (pendiente)

**[completar]** Respuesta a la pregunta de investigación; cumplimiento de objetivos; trabajo futuro: vintages históricos, panel experto para pesos, comparación regional con normalización común, escenarios prospectivos.

## Referencias

Ver [docs/BIBLIOGRAFIA.md](../BIBLIOGRAFIA.md). Las referencias citadas en este borrador están todas en esa lista.

## Anexos previstos

- A. Matriz AHP y pesos (generados por el pipeline).
- B. Diccionario de datos (`data_dictionary.csv`).
- C. Registro de plausibilidad y decisiones de exclusión.
- D. Manifiesto de la release y verificación.
- E. Resultados completos de robustez y validación.
- F. Incidentes documentados.
