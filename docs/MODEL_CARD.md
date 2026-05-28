# Model card ICIV

## Proposito

El ICIV resume informacion internacional y satelital sobre el clima de inversion
de Venezuela en una serie anual y en un monitor mensual separado. El diseno
actual prioriza defensa metodologica, trazabilidad de fuentes y lectura clara:

- **ICIV anual**: indice principal.
- **Pulse mensual**: co-indicador de senales oportunas.
- **SATV Pulse**: reglas de alerta sobre Pulse.
- **Laboratorio**: simulacion de sensibilidad, no pronostico politico.

## Preguntas que responde

1. Como evoluciono el clima de inversion estructural entre 2000 y 2026.
2. Que dimensiones explican los cambios del score anual.
3. Que senales mensuales internacionales cambian mientras las fuentes anuales
   publican con rezago.
4. Que tan sensible es el score anual a cambios hipoteticos por dimension.

## Preguntas que no responde por si solo

- No decide si una empresa concreta debe invertir.
- No estima retorno financiero sectorial.
- No afirma causalidad economica con una correlacion anual corta.
- No convierte una senal noticiosa mensual en medicion institucional anual.

## ICIV anual

### Unidad de observacion

Ano calendario. La serie maestra cubre 2000-2026. Los anos recientes pueden
tener menos cobertura por rezagos de publicacion de WDI, WGI, HDI y otras
fuentes internacionales.

### Dimensiones

| Dimension | Lectura |
|---|---|
| D1 macro | estabilidad macro y condiciones externas relevantes |
| D2 energia | produccion, electricidad y actividad nocturna |
| D3 institucional | gobernanza, corrupcion, libertades, rule of law y terror politico |
| D4 apertura | comercio, desempleo, migracion y conectividad logistica |
| D5 capital humano | desarrollo humano, salud, electricidad e informalidad |
| D6 percepcion | cobertura y tono Guardian |

### Tratamiento

1. Cada loader conserva las observaciones publicadas por su fuente.
2. El pipeline limpia tipos, aplica transformaciones justificadas y normaliza
   a escala 0-100.
3. Variables negativas se invierten para que un score mayor signifique mejor
   clima.
4. AHP define pesos por dimension y dentro de cada dimension.
5. Si una observacion falta, el agregador renormaliza el peso disponible y
   reporta cobertura. No se sustituye por un valor inventado.

### Por que 26 variables core

La version anterior acumulaba variables declaradas, experimentales y series con
historia insuficiente. La version core conserva variables que cubren mecanismos
distintos, tienen trazabilidad razonable y pueden explicarse frente a jurado.
Menos variables mejora auditabilidad cuando la alternativa es una cobertura
aparente basada en NaN, snapshots o series redundantes.

## Pulse mensual

Pulse usa 11 variables mensuales observadas:

- FRED: WTI, Brent, Fed Funds, USD index, VIX y UST 10Y.
- EIA International: produccion petrolera mensual.
- Guardian: volumen y tono de titulares.
- GDELT: volumen de cobertura y tono del timeline DOC.

El score mensual:

1. Normaliza cada serie mensual en su historia disponible.
2. Invierte variables de riesgo.
3. Agrega con pesos definidos para Pulse.
4. Expone `cobertura_pct` y `n_vars`.
5. No forward-fillea el rezago mensual de EIA; si el dato no llego, baja la
   cobertura del mes.

GDELT es opcional en el control semanal porque su API publica puede aplicar
rate limits. Si falla, Pulse no fabrica sustituto y la cobertura lo revela. El
fetch deja un `gdelt_monthly.status.json` para auditar si la falla fue de API,
red o ausencia de respuesta valida.

## SATV Pulse

SATV se calcula solo con Pulse para evitar comparar anos con meses dentro de la
misma alerta. Resume:

- grupo macro global;
- energia;
- noticias internacionales;
- cobertura mensual parcial;
- Pulse bajo;
- deterioro acumulado de tres meses.

SATV es una capa de monitoreo y comunicacion. Sus umbrales deben revisarse con
backtesting formal si se quiere convertir en sistema operativo de alertas para
usuarios externos.

## IED

La IED neta se aparta del score anual. Su rol actual es outcome externo:
permite examinar si cambios en el clima medido anteceden flujos de inversion
mas favorables. Esta decision evita circularidad obvia en el bloque ICIV-IED.

La correlacion, OLS y Granger que aparecen en dashboard siguen siendo
exploratorios por muestra anual pequena, rezagos de publicacion, shocks de
sanciones y la presencia de desinversion neta. Deben presentarse como evidencia
complementaria, no como prueba causal final.

## Prediccion

La prediccion publica visible es SARIMA sobre Pulse a seis meses. Es razonable
como baseline de serie temporal porque:

- el target visible tambien es mensual;
- usa historia observada del propio Pulse;
- entrega bandas de incertidumbre;
- evita inventar escenarios politicos futuros.

El proyecto ya incluye backtesting rolling-origin contra naive, seasonal naive
y ETS. Un modelo mas complejo con regresores exogenos solo debe subir a la vista
publica si mejora error fuera de muestra y conserva interpretabilidad.

## Visualizacion

La portada debe mantener una jerarquia sencilla:

1. Pulse actual y cobertura.
2. ICIV anual como referencia estructural.
3. Historia anual y dimensiones.
4. SATV Pulse, noticias y mapa satelital.
5. Validacion, metodologia y laboratorio.

El mapa satelital encaja en historia/actividad por estado. Da diferenciacion al
proyecto y permite mostrar heterogeneidad espacial sin convertir el dashboard
en una galeria separada.

## Riesgos metodologicos abiertos

- Cobertura anual reciente baja para algunas fuentes con lag.
- AHP aun depende del juicio del investigador.
- Guardian y GDELT miden percepcion mediada por cobertura internacional.
- Pulse mezcla factores externos y una senal domestica EIA; debe llamarse
  co-indicador, no reemplazo mensual del anual.
- Benchmarks internacionales que comparten variables con el score prueban
  convergencia, no independencia estricta.
