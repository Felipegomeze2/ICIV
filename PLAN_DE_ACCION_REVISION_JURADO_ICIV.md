# Plan de Accion Derivado de la Revision de Jurado del ICIV
## Hoja de ruta para convertir el estado actual del proyecto en una entrega defendible

> **Proyecto revisado:** ICIV - Indicador de Clima de Inversion Venezuela  
> **Fecha de referencia de la revision:** 21 de mayo de 2026  
> **Proposito de este documento:** transformar los hallazgos de la revision tecnica, academica y economica en tareas concretas, priorizadas y verificables.  
> **Alcance:** documentacion, metodologia, datos, codigo, validacion, dashboard, entregables de tesis y trabajo futuro.  
> **Regla de datos que gobierna este plan:** el proyecto no debe defender datos inventados, datos artificiales, rellenos estaticos, fallbacks no aceptados ni fuentes originadas en Venezuela.

---

## 1. Veredicto Ejecutivo

El proyecto tiene una base valiosa y una ambicion adecuada para una entrega de posgrado:

1. Construye un indice compuesto para una pregunta economica relevante: evaluar el clima de inversion en Venezuela.
2. Tiene una implementacion modular en Python con ingesta, procesamiento, normalizacion, ponderacion, agregacion, validacion, escenarios, SATV y dashboard.
3. Usa varias fuentes internacionales y en varias partes del pipeline conserva valores faltantes cuando no hay dato real disponible.
4. Reporta cobertura del indice por anio, lo que permite reconocer que los puntajes recientes son parciales.

Sin embargo, antes de una defensa exigente el proyecto debe resolver cuatro problemas mayores:

1. **No existe una unica version metodologica consistente** entre documentos, configuracion y codigo.
2. **La trazabilidad de varias series manuales o hardcoded no es suficiente** para certificar con rigor que no hay datos artificiales o no verificables.
3. **Parte de la validacion actual es circular**, especialmente cuando se usa IED para validar un indice que ya contiene IED.
4. **La interpretacion de los puntajes recientes necesita disciplina**, porque 2025 y 2026 tienen cobertura considerablemente menor que los anios historicos.

La prioridad no es agregar mas variables de inmediato. La prioridad es hacer que lo que ya existe sea:

- coherente;
- auditable;
- reproducible;
- economicamente justificable;
- defendible ante jurados con perfiles distintos.

---

## 2. Calificacion Diagnostica de Referencia

Esta calificacion no es una nota final. Es una forma de medir el estado actual y orientar el plan de mejora.

| Perspectiva de jurado | Calificacion diagnostica | Lectura |
|---|---:|---|
| Maestria en Ciencia de Datos y Analitica | 3.8 / 5.0 | Buen desarrollo tecnico y buena complejidad, con debilidades en validacion, trazabilidad y consistencia metodologica. |
| Especializacion en Big Data e Inteligencia de Negocios | 3.6 / 5.0 | Buen producto analitico y visual, pero falta gobierno de datos, lineage, contratos de calidad y arquitectura de operacion mas clara. |
| Jurado Economista | 3.5 / 5.0 | Constructo relevante, pero requiere mejor marco economico, limites de interpretacion y validacion externa no endogena. |

### Meta razonable despues de aplicar este plan

| Dimension | Meta |
|---|---|
| Calidad academica | que el lector identifique sin ambiguedad que indice se construyo, con que datos y bajo que supuestos |
| Calidad de datos | que cada serie tenga fuente, evidencia, cobertura, transformaciones y estado de aceptacion |
| Calidad tecnica | que el pipeline se pueda ejecutar y verificar con pruebas coherentes con los datos vigentes |
| Calidad economica | que el indicador no se venda como mas causal, mas preciso o mas completo de lo que realmente es |
| Calidad de defensa | que cada objecion fuerte tenga respuesta documental y evidencia en el repositorio |

---

## 3. Principios Que Deben Gobernar la Correccion

### 3.1. Una sola fuente de verdad metodologica

El proyecto no puede sostener simultaneamente versiones de 25, 27, 29 y 40 variables. Antes de corregir redaccion fina se debe decidir cual es el indice que sera defendido.

La version final debe responder de forma uniforme:

- nombre oficial del indice;
- objetivo;
- periodo historico;
- periodicidad;
- numero de dimensiones;
- numero de variables;
- lista exacta de variables;
- fuente exacta por variable;
- direccion economica de cada variable;
- metodo de normalizacion;
- metodo de ponderacion;
- metodo de agregacion;
- reglas de datos faltantes;
- interpretacion de cobertura;
- limite de inferencias permitidas.

### 3.2. Dato real o dato faltante

La regla del proyecto debe quedar operacionalizada, no solo declarada.

Para cada observacion se debe poder contestar:

1. ?De donde salio?
2. ?Quien la publica?
3. ?Se descargo automaticamente, se transcribio manualmente o se calculo desde campos publicados?
4. ?La transformacion es reversible o auditable?
5. ?Se usa en el score final o solo como insumo auxiliar?
6. ?Cumple la restriccion de no usar fuente originada en Venezuela?

### 3.3. Separar estado implementado de vision futura

El repositorio hoy contiene ideas de producto final, propuestas ampliadas, SATV, dashboard y documentos de tesis que no siempre describen la misma madurez.

La version final debe separar:

- **Implementado y medido hoy**.
- **Implementado como prototipo o modulo experimental**.
- **Propuesto como trabajo futuro**.

### 3.4. No confundir asociacion con validacion

Una correlacion atractiva no convierte automaticamente una construccion en un indicador validado. Si una variable participa en el indice, usarla luego para demostrar que el indice funciona exige mucha cautela.

---

## 4. Inventario de Hallazgos y Acciones Obligatorias

## 4.1. Hallazgo Critico A - Inconsistencia entre documentacion y codigo

### Evidencia encontrada

| Artefacto | Problema observado |
|---|---|
| `iciv/src/iciv/index/dimensions.py` | define el modelo ejecutable actual con 6 dimensiones y una lista ampliada de variables |
| `iciv/config/settings.yaml` | conserva listas y notas que no parecen reflejar completamente el modelo efectivo |
| `iciv/README.md` | menciona un catalogo de 25 variables y fallbacks estaticos |
| `PROYECTO_ICIV_MASTER.md` | menciona 27 y 29 variables en distintos puntos |
| `CATALOGO_DE_DATOS.md` | describe coberturas y estrategias que corresponden a una version anterior |
| `FUENTES_DE_DATOS.md` | mezcla regla de cero fallback con tablas que todavia listan BCV y estaticos |

### Riesgo ante jurado

Un jurado puede concluir que:

- la metodologia fue modificada sin control;
- el documento no corresponde al codigo;
- los resultados no se pueden reproducir desde la tesis;
- la seleccion de variables no esta cerrada;
- el dashboard muestra un indice distinto al descrito.

### Acciones concretas

1. Definir formalmente la version que sera defendida.
2. Crear una tabla maestra de variables que sea la referencia unica del proyecto.
3. Corregir todos los documentos para que repitan los mismos conteos.
4. Corregir cualquier diagrama, checklist, tabla de entregables y texto narrativo que conserve conteos anteriores.
5. Marcar como historicos, obsoletos o eliminables los fragmentos que describen versiones abandonadas.

### Entregable recomendado

Crear un documento o tabla maestra con estructura minima:

| Campo | Descripcion |
|---|---|
| `variable_id` | nombre exacto usado en codigo |
| `nombre_humano` | etiqueta para tesis/dashboard |
| `dimension` | D1-D6 |
| `peso_variable` | peso intradimension si aplica |
| `peso_dimension` | peso AHP o metodo elegido |
| `fuente` | institucion y dataset |
| `acceso` | API, descarga, transcripcion, calculo derivado |
| `cobertura` | anios con dato real |
| `direccion` | positiva o negativa |
| `tratamiento_faltantes` | NaN, interpolacion permitida, no aplica |
| `uso` | score final, validacion, auxiliar, dashboard |
| `estado` | aceptada, revisar, excluir |

### Criterio de aceptacion

Despues de la correccion:

- una busqueda por `25 variables`, `27 variables`, `29 variables` y cualquier conteo obsoleto no debe dejar contradicciones;
- el numero de variables en tesis, README, catalogo, dashboard y codigo debe coincidir;
- las dimensiones y nombres de variables deben poder trazarse desde documento a codigo.

---

## 4.2. Hallazgo Critico B - Documentos que aun declaran BCV, fuentes venezolanas y fallbacks no aceptados

### Evidencia encontrada

Existen textos que todavia hablan de:

- datos estaticos para reservas;
- datos estaticos para tipo de cambio;
- alfabetizacion completada con valores estaticos;
- scraping o uso del BCV;
- fuentes venezolanas independientes o de terceros originadas en Venezuela;
- cobertura completa alcanzada despues de imputar o rellenar.

### Riesgo ante jurado

Este hallazgo choca directamente con la regla central definida por el proyecto. Aunque el pipeline actual haya evolucionado, el lector revisa el expediente completo y no puede asumir que un texto viejo esta descartado.

### Acciones concretas

1. Revisar de forma completa estos archivos:
   - `PROYECTO_ICIV_MASTER.md`
   - `CATALOGO_DE_DATOS.md`
   - `FUENTES_DE_DATOS.md`
   - `iciv/README.md`
   - `iciv/config/settings.yaml`
2. Identificar cada aparicion de:
   - `BCV`
   - `OVF`
   - `IIES`
   - `UCAB`
   - `PDVSA`
   - `fallback`
   - `estatico`
   - `estaticos`
   - `relleno`
   - `imputacion`
   - `forward_fill`
3. Clasificar cada aparicion en una de estas categorias:
   - fuente usada y aceptada;
   - fuente historica ya excluida;
   - nota contextual que no entra al dataset;
   - error documental que debe corregirse.
4. Reescribir la politica de datos como una regla formal:
   - si el dato no proviene de una fuente aceptada y verificable, no entra al score;
   - si una fuente es rechazada por origen, se documenta su exclusion;
   - si una variable queda sin cobertura suficiente, se elimina del score o se mantiene como experimental con etiqueta visible.

### Redaccion recomendada para la metodologia

> El ICIV adopta una politica restrictiva de datos. Para la version defendida del indice solo se aceptan observaciones trazables a fuentes internacionales aprobadas y verificables. Cuando una observacion no esta disponible bajo esa regla, se conserva como valor faltante y su ausencia se refleja en la cobertura anual del indice. El proyecto no completa series con valores inventados, proxies manuales no auditables ni fuentes excluidas por criterio de origen.

### Criterio de aceptacion

El proyecto debe permitir afirmar con evidencia:

- que los documentos oficiales no prometen el uso de fuentes que fueron rechazadas;
- que las fuentes excluidas no alimentan el score final;
- que no se presenta como "dato real" un valor que fue agregado manualmente sin respaldo archivado.

---

## 4.3. Hallazgo Critico C - Procedencia insuficiente de series manuales o hardcoded

### Evidencia encontrada

La carpeta `iciv/data/sources` no contiene todos los originales que la propia procedencia declara como pendientes.

Se identificaron casos sensibles:

| Serie o fuente | Riesgo |
|---|---|
| CPI | falta conservar el archivo original usado |
| IEF | falta conservar el archivo original usado |
| HDI/HDR | falta conservar el archivo original usado |
| Fragile States Index | hay transcripcion manual y faltan PDFs originales archivados |
| Freedom House | hay valores historicos hardcoded y falta original archivado |
| RSF | hay valores hardcoded, conversiones de escala y referencias secundarias que deben depurarse |

### Riesgo ante jurado

Un jurado puede preguntar:

- ?Como se demuestra que esos valores no fueron copiados mal?
- ?Como se reproduce la serie dentro de seis meses si el sitio cambia?
- ?Por que una fuente secundaria aparece donde hay fuente primaria posible?
- ?Que filas fueron transcritas y cuales se descargaron automaticamente?

### Acciones concretas

1. Crear un inventario de toda serie que no provenga de una API reproducible.
2. Para cada serie manual:
   - conservar archivo original descargado;
   - conservar fecha de descarga;
   - conservar URL o referencia bibliografica;
   - conservar hash del archivo original si es posible;
   - describir el metodo de extraccion;
   - describir validaciones de transcripcion.
3. Reemplazar fuentes secundarias por fuentes primarias cuando sea viable.
4. Si no se puede obtener original confiable:
   - excluir la variable del score final;
   - o etiquetarla como experimental y fuera de la version defendida.
5. Para valores derivados:
   - documentar formula;
   - documentar columnas fuente;
   - documentar cambio de escala;
   - incluir prueba automatizada de transformacion.

### Regla especifica para series manuales

Una serie manual solo debe ser defendible si cumple todo esto:

| Requisito | Estado esperado |
|---|---|
| Archivo original | archivado |
| Fuente primaria | identificada |
| Cobertura | declarada |
| Metodo de extraccion | documentado |
| Transformaciones | replicables |
| Revisor de calidad | registrado o validacion automatizada |
| Uso en score | explicitado |

### Criterio de aceptacion

Para cada serie del score final debe ser posible reconstruir el camino:

`fuente original -> extraccion -> archivo raw -> transformacion -> variable normalizada -> aporte al score`

---

## 4.4. Hallazgo Alto D - Validacion circular con IED

### Evidencia encontrada

La IED forma parte del indice y tambien se usa en analisis de correlacion, regresion o causalidad para argumentar validez del ICIV.

### Problema metodologico

Si una variable esta dentro del indice, la relacion entre esa variable y el indice puede aparecer por construccion. Usar esa relacion como validacion externa puede sobreestimar la evidencia de desempenio del modelo.

### Riesgo ante jurado

Un jurado de ciencia de datos o economia puede objetar:

- endogeneidad;
- leakage conceptual;
- validez tautologica;
- interpretacion causal no justificada;
- muestra pequena para pruebas temporales exigentes.

### Acciones concretas

1. Mantener el analisis ICIV-IED solo si se renombra de forma honesta:
   - analisis descriptivo;
   - coherencia interna;
   - exploracion economica;
   - no validacion externa principal.
2. Construir un bloque de validacion externa con variables no incluidas en el score final.
3. Definir de antemano que espera observar el proyecto:
   - signo esperado;
   - rezago razonable;
   - limitaciones;
   - criterio minimo de interpretacion.
4. Separar:
   - validacion estadistica;
   - validacion economica;
   - sensibilidad metodologica;
   - validacion por expertos.

### Candidatos para validacion externa

La seleccion final debe respetar la politica de fuentes aceptadas. Posibles familias:

- spreads o riesgo soberano internacional;
- cambios en ratings o outlook de calificadoras;
- anuncios de inversion extranjera verificables;
- comercio o conectividad internacional que no participe en el score;
- comparacion regional con shocks reconocibles;
- encuestas o indices de confianza empresarial externos.

### Criterio de aceptacion

La tesis debe poder declarar:

- cuales pruebas son internas;
- cuales pruebas son externas;
- cuales resultados son exploratorios;
- que evidencia no autoriza conclusiones causales.

---

## 4.5. Hallazgo Alto E - AHP implementado pero aun no suficientemente respaldado

### Evidencia encontrada

El codigo implementa AHP, matrices, razones de consistencia y comparacion con PCA. Sin embargo, la defensa documental aun reconoce que falta fortalecimiento mediante expertos.

### Riesgo ante jurado

El AHP puede verse como una parametrizacion subjetiva del autor si no se explica:

- quien juzgo la importancia relativa;
- por que esas comparaciones por pares son razonables;
- como se controlo inconsistencia;
- que tan robustos son los resultados si los pesos cambian.

### Acciones concretas

1. Definir si la version defendida usara:
   - AHP como metodo principal;
   - PCA como alternativa;
   - pesos iguales como baseline;
   - o una combinacion explicada.
2. Si AHP queda como principal:
   - preparar instrumento de elicitacion;
   - seleccionar expertos con criterio verificable;
   - registrar matrices individuales;
   - reportar CR por matriz;
   - documentar consenso o agregacion;
   - conservar evidencia de respuestas.
3. Reportar sensibilidad:
   - perturbacion de pesos;
   - ranking de anios;
   - cambio de categoria;
   - comparacion con PCA y pesos iguales.
4. Explicar por que el metodo elegido se ajusta al objetivo del indice:
   - interpretabilidad;
   - juicio economico;
   - disponibilidad de muestra;
   - heterogeneidad de dimensiones.

### Criterio de aceptacion

La defensa debe poder mostrar:

- una matriz AHP justificada;
- consistencia aceptable;
- razon de eleccion sobre metodos alternativos;
- sensibilidad suficiente para no depender de una unica ponderacion arbitraria.

---

## 4.6. Hallazgo Alto F - Cobertura baja en puntajes recientes

### Evidencia encontrada

Los resultados procesados muestran coberturas menores al final de la serie:

| Anio | Cobertura observada en score AHP |
|---|---:|
| 2024 | 78.4% |
| 2025 | 51.9% |
| 2026 | 35.1% |

### Riesgo ante jurado y usuario final

Un puntaje parcial puede interpretarse como una mejora o deterioro real cuando en realidad cambio la base informativa disponible.

### Acciones concretas

1. Definir umbrales de interpretacion por cobertura.
2. Etiquetar los anios recientes:
   - completo;
   - parcial;
   - provisional;
   - no comparable.
3. Evaluar si el dashboard debe:
   - mostrar score;
   - mostrar banda de advertencia;
   - ocultar categoria de inversion cuando la cobertura sea demasiado baja;
   - separar historico comparable de nowcast parcial.
4. Incluir un analisis de estabilidad del score ante faltantes:
   - score sobre panel balanceado;
   - score con variables disponibles;
   - diferencia por dimension;
   - sensibilidad de categorias.

### Propuesta de umbrales iniciales

| Cobertura | Lectura sugerida |
|---|---|
| 85% o mas | score historico suficientemente cubierto |
| 70% a 84.9% | score util con advertencia |
| 50% a 69.9% | score parcial, interpretacion cautelosa |
| menos de 50% | score provisional o experimental |

Estos umbrales deben justificarse en metodologia y mantenerse iguales en tesis y dashboard.

### Criterio de aceptacion

Ningun score de baja cobertura debe presentarse como si tuviera la misma fuerza interpretativa que un anio bien cubierto.

---

## 4.7. Hallazgo Medio G - Documento DOCX y repositorio no parecen describir exactamente el mismo entregable

### Evidencia encontrada

El DOCX presenta una propuesta ampliada de IMIV-VEN + SATV con elementos que no se reflejan de forma equivalente en el estado actual del repositorio.

### Riesgo ante jurado

El jurado puede detectar una brecha entre:

- promesa del documento;
- evidencia del codigo;
- dashboard entregado;
- alcance real del proyecto.

### Acciones concretas

1. Decidir la funcion del DOCX:
   - documento de propuesta;
   - avance;
   - entrega final;
   - anexo de trabajo futuro.
2. Si es entrega final:
   - alinear el contenido con lo implementado;
   - bajar a trabajo futuro lo no implementado;
   - distinguir SATV actual de SATV objetivo.
3. Si es propuesta:
   - dejarlo explicitamente marcado como propuesta;
   - evitar que contradiga la tesis final.

### Criterio de aceptacion

Cada entregable debe indicar su estado y no prometer capacidades que no se puedan mostrar.

---

## 4.8. Hallazgo Medio H - Pruebas y reproducibilidad aun no cierran

### Evidencia encontrada

La suite de pruebas revisada no termina limpia: una prueba del loader WDI espera que el anio maximo no supere 2024, mientras los datos actuales llegan a 2026.

### Riesgo ante jurado

Esto puede parecer menor, pero en una defensa tecnica sugiere:

- tests no actualizados;
- contratos de datos temporales fragiles;
- poca separacion entre datos vigentes y supuestos historicos.

### Acciones concretas

1. Revisar pruebas que fijan anios duros.
2. Cambiar pruebas fragiles por contratos mas utiles:
   - columnas requeridas;
   - tipos;
   - unicidad por anio;
   - rangos validos;
   - ausencia de duplicados;
   - trazabilidad de fuente;
   - comportamiento con NaN.
3. Agregar pruebas para:
   - politicas de faltantes;
   - normalizacion;
   - agregacion con cobertura parcial;
   - transformaciones de series manuales;
   - consistencia de catalogo de variables.
4. Crear un checklist de ejecucion antes de generar dashboard y anexos.

### Criterio de aceptacion

La version que se entregue debe tener pruebas coherentes con los datos de la version defendida y no depender de supuestos temporales vencidos.

---

## 5. Auditoria Especifica de Datos Rechazados o Sospechosos

## 5.1. Objetivo

Demostrar con evidencia que la version defendida:

- no usa datos inventados;
- no usa valores de relleno estatico no aceptados;
- no usa fuentes originadas en Venezuela;
- no disfraza transcripcion manual como descarga automatica;
- no oculta cobertura insuficiente.

## 5.2. Matriz de decision por fuente

Se recomienda construir una matriz con estas columnas:

| Campo | Pregunta |
|---|---|
| Fuente | ?Que institucion publica el dato? |
| Pais/origen institucional | ?La fuente cumple la regla de origen? |
| Dataset | ?Cual producto o tabla exacta se usa? |
| Metodo de acceso | ?API, CSV, Excel, PDF, transcripcion? |
| Evidencia archivada | ?Existe copia o referencia verificable? |
| Uso | ?Score, validacion, contexto, futuro? |
| Riesgo | bajo, medio, alto |
| Decision | aceptar, aceptar con control, excluir |

## 5.3. Revision minima por carpeta

### `iciv/data/raw`

Revisar:

- archivos con pocas filas;
- archivos vacios;
- archivos manuales;
- columnas `fuente`, `source`, `notes` o equivalentes;
- valores duplicados por anio;
- periodos futuros o preliminares;
- signos economicos extraños;
- cambios de escala entre anios.

### `iciv/data/processed`

Revisar:

- que el score final solo use variables aceptadas;
- que las coberturas se calculen despues de aplicar reglas de aceptacion;
- que un anio parcial no quede etiquetado como completo;
- que las variables eliminadas no sigan apareciendo en el dashboard como si fueran parte del modelo.

### `iciv/data/sources`

Completar:

- originales de archivos manuales;
- PDFs o Excels base;
- notas de descarga;
- hashes;
- instrucciones para reproducir la extraccion.

## 5.4. Tratamiento recomendado de casos sensibles

| Caso | Accion recomendada |
|---|---|
| Fuente venezolana listada en docs pero no usada | marcarla como excluida por criterio metodologico |
| Fuente venezolana usada en score | removerla de la version defendida |
| Dato hardcoded con original archivado | mantener solo si la transformacion es auditable |
| Dato hardcoded sin original | excluir o dejar fuera del score |
| Fuente secundaria con fuente primaria disponible | migrar a primaria |
| Variable con cobertura minima | evaluar excluir del score o reservar para exploracion |
| Serie con cambio metodologico | documentar corte, empalme y limitacion |

---

## 6. Plan de Correccion por Archivos

## 6.1. `PROYECTO_ICIV_MASTER.md`

### Que revisar

- conteo de variables;
- definicion de dimensiones;
- periodicidad real del indice;
- estado real del SATV;
- referencias a BCV;
- referencias a fallbacks estaticos;
- afirmaciones de cobertura completa;
- afirmaciones de validacion con IED;
- afirmaciones de "justificacion experta" si aun no hay expertos documentados.

### Resultado esperado

Debe quedar como documento maestro de la version defendida, no como mezcla de:

- idea original;
- backlog;
- resultados actuales;
- promesas futuras.

## 6.2. `CATALOGO_DE_DATOS.md`

### Que revisar

- cada variable que aparece pero ya no participa;
- fuentes rechazadas;
- cobertura real;
- reglas de faltantes;
- notas sobre imputacion;
- estaticos o rellenos heredados;
- variables con datos escasos.

### Resultado esperado

Debe convertirse en catalogo verificable del dataset final:

- variable;
- fuente aceptada;
- cobertura real;
- transformacion;
- limitacion;
- rol en el indice.

## 6.3. `FUENTES_DE_DATOS.md`

### Que revisar

- tabla de fuentes integradas;
- tabla de fuentes manuales;
- fuentes venezolanas;
- incoherencia entre la regla de cero fallback y tablas que los mencionan;
- fuentes disponibles pero no usadas.

### Resultado esperado

Debe separar claramente:

1. fuentes aprobadas y usadas;
2. fuentes evaluadas y descartadas;
3. fuentes candidatas para trabajo futuro.

## 6.4. `iciv/README.md`

### Que revisar

- descripcion de pipeline;
- numero de variables;
- explicacion de fallbacks;
- explicacion de validacion;
- estado de scripts.

### Resultado esperado

Debe servir como guia tecnica honesta para ejecutar la version actual.

## 6.5. `iciv/config/settings.yaml`

### Que revisar

- descripciones heredadas;
- listas de variables obsoletas;
- notas de fuentes estaticas;
- politicas de imputacion;
- correspondencia con `dimensions.py`.

### Resultado esperado

Debe quedar alineado con el modelo ejecutable o, si no es fuente efectiva de verdad, debe documentarse su rol exacto.

## 6.6. `iciv/src/iciv/index/dimensions.py`

### Que revisar

- lista final de variables;
- peso por dimension;
- texto descriptivo;
- variables parciales;
- variables experimentales.

### Resultado esperado

Debe coincidir con la tabla maestra defendida.

## 6.7. `iciv/scripts/fetch_freedom_house.py`

### Que revisar

- datos hardcoded;
- metodo de calculo para anios construidos desde puntajes publicados;
- evidencia de fuente original;
- cobertura;
- estado de uso en el score.

### Resultado esperado

Debe ser auditable y respaldado por originales o quedar fuera de la version final.

## 6.8. `iciv/scripts/fetch_rsf.py`

### Que revisar

- referencias secundarias;
- valores hardcoded;
- cambio metodologico de RSF;
- inversion de escalas;
- fallback manual;
- empalme de periodos.

### Resultado esperado

Debe quedar claro:

- que escala se usa;
- por que es comparable o donde deja de serlo;
- que fuente primaria sustenta cada tramo.

## 6.9. `iciv/scripts/validate_model.py` y `iciv/src/iciv/analytics/correlation.py`

### Que revisar

- lenguaje que llama "validacion" a IED;
- conclusiones de causalidad;
- interpretacion de Granger con muestra corta;
- uso de variables internas del score.

### Resultado esperado

Separar la validacion externa real de los analisis exploratorios.

## 6.10. Dashboard y artefactos visuales

### Que revisar

- conteo de variables mostrado;
- etiquetas de cobertura;
- explicacion de 2025-2026;
- graficos de validacion;
- nombres del indice y del SATV;
- afirmaciones de fuentes.

### Resultado esperado

El dashboard debe ser coherente con la version defendida y advertir limites cuando el usuario mas necesita cautela.

---

## 7. Recomendaciones Metodologicas de Fondo

## 7.1. Definir el constructo economico con precision

El proyecto debe responder si mide principalmente:

1. clima de inversion;
2. riesgo pais operativo;
3. atractivo macroinstitucional;
4. probabilidad de entrada empresarial;
5. deterioro o recuperacion de condiciones de negocio.

Puede cubrir varias dimensiones, pero no debe prometer que mide todo con la misma fuerza.

## 7.2. Evitar mezclar seniales sin teoria suficiente

Una variable puede ser tecnicamente disponible y aun asi no ser adecuada para el constructo. Cada variable debe justificar:

- mecanismo economico;
- direccion esperada;
- posible rezago;
- sensibilidad a shocks;
- sesgo de medicion;
- razon para estar en el indice y no solo en un panel auxiliar.

## 7.3. Separar indice estructural y alerta temprana

Recomendacion fuerte:

| Componente | Naturaleza | Uso |
|---|---|---|
| ICIV anual | estructural | comparar clima de inversion historico |
| SATV mensual o de alta frecuencia | coyuntural | detectar seniales tempranas y eventos |

No conviene que una senial de cobertura periodistica o una proxy de alta frecuencia altere sin control un indice estructural si su interpretacion economica es distinta.

## 7.4. Formalizar la comparabilidad temporal

Debe discutirse:

- revisiones de fuentes;
- series que cambian metodologia;
- anios con cobertura distinta;
- periodos de crisis extrema;
- transformaciones logaritmicas;
- estabilidad de min-max si el rango cambia con nuevos anios.

## 7.5. Tratar el indice como apoyo a decision, no como veredicto automatico

El dashboard puede orientar, pero la tesis debe recordar que decisiones de inversion requieren:

- analisis sectorial;
- riesgo legal;
- sanciones;
- estructura contractual;
- liquidez;
- repatriacion de capital;
- diligencia debida.

---

## 8. Recomendaciones Tecnicas y de BI

## 8.1. Gobierno de datos

Implementar una capa minima de gobierno:

- catalogo de variables versionado;
- manifiesto de fuentes;
- reglas de calidad;
- estado de aceptacion por fuente;
- evidencia archivada;
- fecha de refresco.

## 8.2. Contratos de datos

Cada loader importante deberia tener un contrato:

- columnas obligatorias;
- tipos esperados;
- llave temporal unica;
- rango de valores plausible;
- fuente declarada;
- manejo de ausencia.

## 8.3. Observabilidad del pipeline

Para una entrega de especializacion en BI y Big Data ayuda mostrar:

- que fuentes corrieron;
- que fuentes fallaron;
- cuantas filas llegaron;
- que cobertura obtuvo cada dimension;
- que variables quedaron fuera del score de cada anio.

## 8.4. Dashboard

El dashboard deberia incorporar:

- etiqueta visible de cobertura del score;
- tooltip o nota corta sobre score parcial;
- separacion entre historico y provisional;
- tabla de fuente por variable;
- descarga o vista del catalogo de datos;
- vista de auditoria del ultimo refresco.

---

## 9. Trabajo Futuro Recomendado

## 9.1. Corto plazo

Prioridad: cerrar la version defendible.

1. Congelar version metodologica.
2. Alinear todos los documentos.
3. Completar procedencia de series manuales.
4. Excluir fuentes y datos no aceptados.
5. Reetiquetar validacion IED.
6. Definir umbrales de cobertura.
7. Ajustar pruebas que hoy fallan por supuestos temporales viejos.
8. Revisar dashboard contra la version congelada.

## 9.2. Mediano plazo

Prioridad: elevar validez cientifica.

1. Ejecutar validacion AHP con expertos.
2. Construir validacion externa no circular.
3. Preparar panel regional comparable.
4. Medir sensibilidad a faltantes.
5. Evaluar estabilidad frente a:
   - PCA;
   - pesos iguales;
   - agregacion geometrica;
   - panel balanceado.
6. Documentar incertidumbre y provisionalidad.

## 9.3. Largo plazo

Prioridad: convertirlo en plataforma analitica robusta.

1. Separar producto anual y SATV de alta frecuencia.
2. Versionar datasets y resultados.
3. Automatizar lineage y reportes de calidad.
4. Incorporar monitoreo de revisiones de fuentes.
5. Explorar modelos econometricos o de forecasting con validacion fuera de muestra.
6. Crear escenarios sectoriales:
   - energia;
   - consumo;
   - logistica;
   - servicios financieros;
   - manufactura.

---

## 10. Backlog Priorizado

## 10.1. Prioridad P0 - Antes de defensa o entrega formal

| Tarea | Resultado esperado |
|---|---|
| Congelar version del indice | un unico conteo de variables y dimensiones |
| Limpiar contradicciones documentales | documentos alineados con codigo y datos |
| Auditar fuentes prohibidas | ninguna fuente rechazada alimenta el score final |
| Completar evidencia de series manuales | originales y metodo de extraccion disponibles |
| Revisar RSF y Freedom House | trazabilidad y comparabilidad documentadas |
| Reetiquetar validacion IED | no se presenta como validacion externa fuerte |
| Etiquetar 2025-2026 | score parcial o provisional segun cobertura |

## 10.2. Prioridad P1 - Para subir calidad de tesis

| Tarea | Resultado esperado |
|---|---|
| Tabla maestra de variables | catalogo unico defendible |
| Matriz de aceptacion de fuentes | decision clara por fuente |
| Validacion externa | evidencia no circular |
| Paquete AHP con expertos | pesos respaldados |
| Analisis de faltantes | limites cuantificados |
| Suite de pruebas coherente | pipeline verificable |

## 10.3. Prioridad P2 - Para llevar el proyecto a otro nivel

| Tarea | Resultado esperado |
|---|---|
| Panel regional | benchmark y contexto |
| SATV de alta frecuencia | alerta temprana diferenciada |
| Reporte automatizado de calidad | trazabilidad operativa |
| Incertidumbre del score | interpretacion mas responsable |
| Escenarios sectoriales | mayor utilidad para decision empresarial |

---

## 11. Checklist de Defensa

Antes de presentar, deberia poder marcarse todo:

### Metodologia

- [ ] El nombre del indice es consistente en todos los entregables.
- [ ] El objetivo del indice esta definido en una sola frase precisa.
- [ ] El numero de variables coincide entre codigo, tesis, README y dashboard.
- [ ] Las dimensiones tienen justificacion economica.
- [ ] Cada variable tiene direccion economica y rol.
- [ ] El tratamiento de datos faltantes esta explicado.
- [ ] La cobertura modifica la interpretacion del score.

### Datos

- [ ] Toda fuente del score final esta aprobada por la politica del proyecto.
- [ ] No hay fuentes venezolanas en el score final.
- [ ] No hay fallbacks estaticos no aceptados en la version defendida.
- [ ] Toda serie manual tiene original archivado.
- [ ] Toda transformacion relevante tiene explicacion reproducible.
- [ ] Variables con cobertura insuficiente estan justificadas o excluidas.

### Validacion

- [ ] La validacion externa no depende de variables incluidas en el indice.
- [ ] Las correlaciones exploratorias estan etiquetadas como tales.
- [ ] AHP tiene respaldo suficiente o se declara su limitacion.
- [ ] Se reporta sensibilidad a pesos y faltantes.
- [ ] Se distinguen asociacion, prediccion y causalidad.

### Producto tecnico

- [ ] El pipeline corre para la version final.
- [ ] Las pruebas relevantes pasan.
- [ ] El dashboard muestra advertencias de cobertura.
- [ ] La documentacion tecnica permite reproducir el flujo.
- [ ] El entregable final no promete modulos que no existen.

---

## 12. Preguntas Que Probablemente Hara un Jurado

Preparar respuestas para estas preguntas:

1. ?Por que estas variables y no otras?
2. ?Que diferencia hay entre clima de inversion, riesgo pais y atractivo economico?
3. ?Como se valida un indice compuesto cuando no existe una verdad terreno directa?
4. ?Por que AHP y no pesos iguales o PCA?
5. ?Quienes respaldan los juicios del AHP?
6. ?Que ocurre cuando faltan variables en 2025 o 2026?
7. ?Como se evita que el score reciente sea incomparable con el historico?
8. ?Como se demuestra que una serie manual no fue inventada?
9. ?Por que se excluyen ciertas fuentes?
10. ?Puede el indice anticipar inversion o solo describir condiciones?
11. ?Que parte del SATV esta implementada hoy y que parte es trabajo futuro?
12. ?Que decision real deberia tomar una empresa con este dashboard?

---

## 13. Estructura Recomendada para la Version Final de la Tesis

Una estructura mas defendible seria:

1. Problema y motivacion economica.
2. Definicion del constructo: clima de inversion.
3. Revision de indices compuestos y riesgos de medicion.
4. Politica de fuentes y restricciones de datos.
5. Seleccion de variables.
6. Arquitectura de datos y pipeline.
7. Preprocesamiento, normalizacion y faltantes.
8. Ponderacion y agregacion.
9. Resultados historicos del ICIV.
10. Cobertura, sensibilidad e incertidumbre.
11. Validacion interna y externa.
12. Dashboard y utilidad de negocio.
13. Limitaciones.
14. Trabajo futuro.

---

## 14. Definicion de Hecho para Cerrar la Correccion

La correccion puede considerarse cerrada cuando:

1. El repositorio tiene una version metodologica unica.
2. El score final se calcula solo con variables y fuentes aceptadas.
3. La documentacion no contradice al codigo.
4. La procedencia de datos manuales esta respaldada.
5. La validacion no se presenta con afirmaciones mas fuertes que la evidencia.
6. Los anios parciales estan claramente etiquetados.
7. El dashboard, README, catalogo y tesis cuentan la misma historia.
8. Existe una lista explicita de limitaciones y trabajo futuro.

---

## 15. Orden Recomendado de Ejecucion

Este orden evita invertir esfuerzo en pulir documentos que luego volveran a cambiar.

1. **Congelar la version del indice.**
2. **Auditar fuentes y variables contra la regla de datos.**
3. **Decidir que variables quedan en score final, auxiliares o trabajo futuro.**
4. **Completar procedencia y evidencia de series manuales.**
5. **Alinear codigo/configuracion/documentacion.**
6. **Corregir validacion y limites de interpretacion.**
7. **Ajustar pruebas y checklist tecnico.**
8. **Revisar dashboard y entregables de defensa.**
9. **Preparar narrativa final para jurados.**

---

## 16. Resumen Final

El proyecto ya tiene materia prima para una entrega fuerte. Su mejora no depende primero de hacer mas grande el indice, sino de hacerlo mas riguroso.

La version final debe convencer a tres tipos de lector:

1. al cientifico de datos de que el modelo y la validacion son honestos;
2. al especialista BI de que la canalizacion y la trazabilidad son controlables;
3. al economista de que el constructo, los pesos y la interpretacion tienen sentido.

Si se ejecutan las prioridades P0 y P1, el proyecto puede pasar de un prototipo analitico ambicioso a una tesis mucho mas defendible y util.
