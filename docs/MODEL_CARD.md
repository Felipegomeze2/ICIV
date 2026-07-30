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

Pulse usa 15 variables mensuales observadas (ampliado 2026-07):

- FRED: WTI, Brent, Fed Funds, USD index, VIX, UST 10Y y spread de bonos
  emergentes (ICE BofA EM Corporate Plus OAS; FRED solo redistribuye una
  ventana movil ~3 anos por licenciamiento, cobertura desde 2023-07).
- World Bank Pink Sheet: crudo Dubai mensual (benchmark mediano-pesado, mas
  cercano al Merey venezolano que WTI/Brent).
- EIA International: produccion petrolera mensual.
- IMF IMTS (sucesor de DOTS): comercio espejo EEUU-Venezuela — importaciones
  y exportaciones venezolanas segun lo reporta EEUU (mirror statistics;
  actividad real observada sin usar fuentes venezolanas).
- Guardian: volumen y tono de titulares.
- GDELT: volumen de cobertura y tono del timeline DOC.

El score mensual:

1. Normaliza cada serie mensual en su historia disponible.
2. Invierte variables de riesgo.
3. Agrega con pesos definidos para Pulse.
4. Expone `cobertura_pct` y `n_vars`.
5. No forward-fillea el rezago mensual de EIA; si el dato no llego, baja la
   cobertura del mes.

GDELT es opcional en el control semanal porque su API publica aplica rate limit
por frecuencia de peticiones. Desde 2026-07-29 la serie se descarga en tramos
anuales acumulativos (ver docs/FUENTES_Y_VARIABLES.md), lo que la llevo de
vacia a 91 meses (2019-2026). Si un tramo falla, Pulse no fabrica sustituto y
la cobertura lo revela; el fetch deja un `gdelt_monthly.status.json` con los
anos logrados y los fallidos.

## Mapa subnacional: un solo producto (NASA Black Marble)

El dashboard tiene **un unico mapa por estado**, alimentado por NASA Black
Marble (VNP46A3): radiancia absoluta en nW/cm2/sr, 25 estados, 149 meses
(2014-2026), con vistas anual y mensual.

### Por que se retiro el segundo mapa (2026-07-29)

Hasta esa fecha convivia un mapa de la serie armonizada Li et al. Se retiro
tras auditar su metodo de extraccion subnacional:

| Criterio | Li et al. subnacional (retirado) | NASA Black Marble (vigente) |
|---|---|---|
| Extraccion por estado | **bbox rectangular** | **mascara poligonal exacta** |
| Sesgo de area | bbox mide en **mediana 2x** el territorio real; 11 de 25 estados >2x; Dependencias Federales 386x | cada pixel se asigna a un solo estado |
| Doble conteo | **56 pares de estados con bbox solapado** (Bolivar y Amazonas comparten 9 grados cuadrados) | ninguno |
| Unidad | DN 0-63, sin significado fisico | nW/cm2/sr, radiancia calibrada |
| Comparabilidad | normalizada por estado (100 = maximo de ese estado): solo temporal | absoluta: entre estados y en el tiempo |
| Frecuencia y alcance | anual, 2000-2024 | mensual, 2014-2026 |

Ambas series concordaban (Pearson 0.90 en 2024, mismo ordenamiento del
territorio), por lo que retirar una no elimina informacion: elimina un metodo
menos preciso y una ambiguedad de lectura. Mantener dos mapas que parecian
contradecirse restaba credibilidad sin aportar evidencia nueva.

**Lo que NO se retiro:** la serie **nacional** de Li et al. (`viirs.csv`) sigue
alimentando la variable `luminosidad_nocturna_idx` del score anual, porque
cubre 2000-2013 (previo a VIIRS) y es la base de la validacion externa
(r=+0.84 en la era VIIRS). A escala nacional el encuadre es constante en el
tiempo y no hay comparacion entre estados que distorsionar.

`scripts/fetch_viirs_states.py` y `viirs_states.csv` se conservan en el
repositorio para auditoria y trazabilidad, pero salieron del pipeline: ya no
alimentan ninguna vista. Reconstruir el historico 2000-2013 subnacional con la
misma mascara poligonal queda como mejora futura documentada.

El mapa usa escala **logaritmica** porque la radiancia va de ~0.005 (selva) a
~46 (Caracas); en escala lineal el 90% del pais se veria negro.

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

## Capas auxiliares / contextuales

Ademas del score anual y el Pulse, el proyecto mantiene capas contextuales que
**no entran al score ni al Pulse**. Sirven para validacion cruzada, contexto y
diferenciacion frente a jurado:

- **Comercio espejo multi-socio** (IMF IMTS reportado por EEUU + UN Comtrade con
  Espana, Brasil, India, Turkiye y China): actividad comercial real observada
  desde las aduanas de los socios, sin fuentes venezolanas. Los ultimos ~3 meses
  de Comtrade son parciales (no todos los socios reportaron aun).
- **ACLED**: eventos mensuales de conflicto y protesta desde 2018. El tier de
  cuenta actual entrega los datos con ~12 meses de rezago, por lo que es contexto
  historico, no alerta en tiempo real.
- **NASA Black Marble mensual y subnacional** (VNP46A3, 2014-2026): radiancia
  nocturna nacional (5 agregaciones) y por los 25 estados; alimenta el mapa
  coropletico animado. Validacion honesta vs la serie anual Li et al.: la media
  aritmetica es la que mejor correlaciona (Pearson r=+0.65, p=0.03); las
  variantes robustas al flaring (mediana, log-media, p90) no mejoran — capturan
  una senal distinta, no una mejor. Por eso no se agrega al Pulse: la media ya
  esta representada por la luminosidad anual en la dimension energetica.

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

El mapa satelital vive en la pestana "Actividad por Estado" (bloque Historia).
Da diferenciacion al proyecto y permite mostrar heterogeneidad espacial sin
convertir el dashboard en una galeria separada. Es un solo mapa (Black Marble)
para que la lectura sea inequivoca. Se dibuja en SVG nativo, sin librerias de
mapas externas, lo que reduce dependencias del entregable.

## Riesgos metodologicos abiertos

- Cobertura anual reciente baja para algunas fuentes con lag.
- AHP aun depende del juicio del investigador.
- Guardian y GDELT miden percepcion mediada por cobertura internacional.
- Pulse mezcla factores externos y una senal domestica EIA; debe llamarse
  co-indicador, no reemplazo mensual del anual.
- Benchmarks internacionales que comparten variables con el score prueban
  convergencia, no independencia estricta.
