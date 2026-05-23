# Guia de decisiones ICIV

## Diagnostico ejecutivo

El proyecto gana cuando se presenta como un sistema compacto con tres capas:
un indice anual defendible, un monitor mensual oportuno y un laboratorio
interactivo. Pierde fuerza cuando intenta mostrar a la vez escenarios politicos,
muchas variables institucionales repetidas, validaciones no independientes y
documentos que reportan conteos distintos.

La decision actual es correcta:

1. Core anual reducido.
2. Pulse mensual con variables realmente mensuales.
3. SATV unido solo a Pulse.
4. IED como outcome externo.
5. Una sola prediccion visible.
6. Mapa satelital conservado dentro de historia/actividad.

## Que debe quedar en la defensa

### Mensaje principal

> ICIV organiza informacion internacional y satelital para medir la trayectoria
> estructural del clima de inversion de Venezuela y monitorear senales mensuales
> sin depender de fuentes originadas en Venezuela.

Ese mensaje es mas defendible que afirmar unicidad absoluta. El valor diferencial
se demuestra con trazabilidad, cobertura visible, satelite, pipeline y separacion
de frecuencias.

### Narrativa sugerida

1. Problema: opacidad y rezago de informacion.
2. Regla de datos: internacionales, auditables, no inventados.
3. ICIV anual: seis dimensiones, AHP, cobertura por ano.
4. Pulse: senales mensuales y por que no reemplaza al anual.
5. Hallazgo visual: historia, quiebres, dimensiones y mapa de luces.
6. Validacion: sensibilidad, consistencia, benchmarks y outcome IED con cautela.
7. Laboratorio y trabajo futuro.

## Decisiones aplicadas

| Decision | Por que mejora el proyecto |
|---|---|
| Reducir el core anual a variables clave | baja redundancia y facilita auditoria |
| Sacar IED del score | permite usarla como resultado externo |
| Apartar snapshots OFAC del Pulse | evita fingir alta frecuencia sin historia |
| Agregar GDELT como senal mensual opcional | aumenta contraste noticioso sin fabricar datos |
| No forward-fill mensual EIA | la cobertura informa el rezago real |
| Mostrar una prediccion SARIMA Pulse | responde a serie mensual observada |
| Mantener simulador en laboratorio | conserva interaccion sin prometer futuro politico |
| Unificar docs | elimina contradicciones ante jurado |

## Como decidir si agregar o quitar variables

Use esta matriz antes de cualquier cambio:

| Criterio | Pregunta | Regla |
|---|---|---|
| Origen | proviene de fuente aprobada? | si no, no entra |
| Historia | cubre un tramo suficiente? | si es snapshot, no entra a score |
| Frecuencia | coincide con la capa? | mensual para Pulse, anual para ICIV |
| Aporte | mide algo distinto? | si duplica otra variable mejor, apartar |
| Defensa | se puede explicar en 30 segundos? | si no, simplificar |
| Mantenimiento | el fetch es reproducible? | si no, backlog o manual muy documentado |

En general es mejor tener menos variables con datos reales y rol claro que una
lista larga con huecos, proxies debiles o pesos redistribuidos casi siempre.

## Visual: que conservar y que recortar

### Conservar

- Pulse actual, cobertura y serie mensual.
- ICIV anual como referencia estructural.
- Evolucion historica anual.
- Dimensiones y detalle de variables.
- SATV Pulse.
- Noticias en pestaña propia.
- Mapa satelital por estado.
- Laboratorio con simulador.
- Metodologia y limitaciones.

### Recortar o dejar secundario

- Escenarios optimista/base/pesimista publicados como si fueran salida central.
- Monte Carlo si no tiene calibracion y validacion suficientemente defendibles.
- Nowcast anual OLS visible mientras su generalizacion fuera de muestra sea debil.
- Tablas de validacion llamadas "externas" cuando comparten inputs con el indice.
- Texto de marketing con afirmaciones absolutas.

### Minimalismo recomendado

No volver el proyecto plano. Volverlo jerarquico. El dashboard puede seguir
siendo rico en computador, pero cada bloque debe responder una pregunta. Si una
grafica no cambia una decision o no fortalece la defensa, debe ir a anexo o
desaparecer.

## Donde usar satelite y mapa

El mapa debe vivir cerca de la historia del indice y no aislado como una pagina
de curiosidad. Su secuencia ideal:

1. Serie anual muestra el deterioro y recuperaciones parciales.
2. Dimension D2 muestra energia y luces nocturnas.
3. Mapa enseña que la actividad nocturna no es homogenea por estado.

En defensa, use una captura del mapa para explicar diferenciacion espacial y
una grafica anual para explicar que el score final no depende solo del mapa.

## IED: decision recomendada

IED no debe volver al score core si el dashboard mantiene un bloque ICIV-IED.
Como outcome externo tiene mas valor:

- evita validar el indice con uno de sus propios componentes;
- conecta clima con una variable economica que el jurado economista entiende;
- permite discutir por que correlacion y causalidad son preguntas distintas.

Si la IED queda demasiado erratica o incompleta en defensa, mantenga la grafica
como evidencia exploratoria y apoye el argumento principal en cobertura,
consistencia AHP, sensibilidad y eventos historicos.

## Prediccion: decision recomendada

### Ahora

Mantenga SARIMA sobre Pulse como baseline visible de seis meses. Llame la salida
`prediccion Pulse`, muestre bandas y explique que extrapola patrones de la serie
mensual observada.

### Antes de subir un modelo mas ambicioso

Exija:

1. Backtesting rolling-origin.
2. Comparacion contra naive estacional y ETS.
3. MAE/RMSE y cobertura de intervalos.
4. Registro de meses de baja cobertura.
5. Explicacion clara de por que un regresor exogeno mejora el forecast.

Machine learning solo gana si mejora fuera de muestra. Un modelo complejo con
pocos anos anuales puede verse sofisticado y ser menos defendible.

## Fuentes nuevas y coverage

### Prioridad 1

Subir calidad antes que cantidad:

- cerrar huecos de fuentes ya core;
- monitorear freshness semanal;
- conservar GDELT si estabiliza cobertura;
- evaluar mensualidad real de comercio internacional con UN Comtrade.

### Prioridad 2

Subir diferenciacion:

- evaluar NASA Black Marble monthly para actividad nocturna oportuna;
- explorar logistica internacional con series reproducibles;
- documentar un panel de expertos para contrastar AHP.

### Datos que puede ser necesario conseguir

- UN Comtrade puede requerir token o limites de uso segun el endpoint escogido.
- Fuentes comerciales de shipping/AIS normalmente implican licencia o costo.
- Para NASA/Black Marble, el reto principal no es una llave sino el pipeline
  geoespacial y la comparabilidad temporal.

No agregue una fuente porque existe. Agreguela si reemplaza un hueco importante
o mejora una pregunta visible.

## Plan de trabajo

### Corto plazo

1. Revisar el HTML local tras cada cambio visual.
2. Congelar conteos y pesos en docs y dashboard.
3. Ejecutar pipeline con y sin fetch y guardar evidencia de cobertura.
4. Preparar una tabla de limitaciones para defensa.
5. Revisar referencias bibliograficas y nombres de fuentes en dashboard.

### Mediano plazo

1. Backtesting formal del forecast Pulse.
2. Panel de expertos o encuesta estructurada para AHP.
3. Outcome validation adicional que no comparta inputs con el score.
4. Estudio de NASA monthly y/o comercio mensual.
5. Pruebas de regresion visual del dashboard en desktop.

### Largo plazo

1. Versionar releases metodologicos del indicador.
2. Separar pipeline de datos, modelo y frontend si el dashboard crece.
3. Publicar dataset derivado con data dictionary y provenance por release.
4. Diseñar comparacion regional solo si la misma politica de fuentes puede
   sostenerse para todos los paises comparados.
5. Convertir SATV en sistema de alertas evaluado contra eventos si se requiere
   uso operativo.

## Checklist antes de aprobar publicacion

- Conteo del core anual coincide en codigo, README y dashboard.
- Pulse lista solo variables que realmente carga.
- IED no aparece como componente del core.
- SATV habla de meses y grupos Pulse, no de dimensiones anuales.
- El forecast visible es uno y sus limites se ven.
- No hay texto que prometa datos en tiempo real si la cobertura es parcial.
- Ningun documento promete continuidad si el codigo conserva faltantes y cobertura
  parcial.
- La pagina de noticias sigue accesible.
- El mapa satelital mantiene fuente y alcance temporal claros.
