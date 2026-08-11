# Fuentes y variables ICIV

## Regla de seleccion

Una variable entra al core cuando cumple cuatro condiciones:

1. Fuente internacional o satelital verificable.
2. Interpretacion economica clara para clima de inversion.
3. Cobertura suficiente para aportar historia y no solo una fotografia.
4. Aporte no redundante frente a variables mas fuertes de su dimension.

Si una variable es interesante pero no cumple estas condiciones, puede quedar
como dato auxiliar, validacion, backlog de investigacion o exclusion explicita.

## Variables core del ICIV anual

| Dim | Variable | Fuente principal | Direccion | Razon de uso |
|---|---|---|---|---|
| D1 | `inflacion_deflactor_pib_pct` | IMF/WDI | negativa | inestabilidad de precios |
| D1 | `pib_crecimiento_real_pct` | IMF/WDI | positiva | dinamica agregada de actividad |
| D1 | `wti_precio_usd` | FRED | positiva | condicion externa petrolera |
| D1 | `tasa_fed_funds_pct` | FRED | negativa | costo financiero global |
| D2 | `petroleo_crudo_produccion_tbpd` | EIA | positiva | capacidad petrolera central |
| D2 | `luminosidad_nocturna_idx` | NASA Black Marble VNP46A3 | positiva | proxy satelital de actividad; migrado desde Li et al. el 2026-08-11, cubre 2014-2026 con 2 meses de rezago |
| D3 | `cpi_score` | Transparency International | positiva | corrupcion percibida |
| D3 | `wgi_promedio_sc` | World Bank WGI | positiva | gobernanza compuesta |
| D3 | `freedom_house_score` | Freedom House | positiva | libertades relevantes al entorno; solo Aggregate Score publicado (2012+) |
| D3 | `wjp_rule_of_law` | WJP | positiva | regla de derecho; el indice existe desde 2012, antes NaN |
| D3 | `pts_terror_politico` | Political Terror Scale | negativa | coercion y riesgo institucional |
| D4 | `exportaciones_pct_pib` | WDI/OWID | positiva | apertura comercial |
| D4 | `migrantes_vzla_millones` | UNHCR/R4V | negativa | salida poblacional acumulada |
| D4 | `lsci_conectividad_maritima` | UNCTADstat (trimestral → promedio anual) | positiva | conectividad logistica; serie 2006-2026 base Q1-2023=100 |
| D5 | `hdi` | UNDP/OWID | positiva | capital humano agregado |
| D5 | `esperanza_vida_anos` | World Bank `SP.DYN.LE00.IN` | positiva | condicion sanitaria; migrada desde WHO GHO el 2026-08-11 |
| D5 | `mortalidad_infantil_x1000` | World Bank `SP.DYN.IMRT.IN` | negativa | fragilidad social; migrada desde WHO GHO el 2026-08-11 |
| D5 | `acceso_electricidad_pct` | WDI | positiva | acceso basico de infraestructura |
| D5 | `ilo_empleo_informal_pct` | ILO/WDI proxy | negativa | calidad del mercado laboral |
| D6 | `guardian_tono_titulares` | Guardian + VADER | positiva | tono mediatico externo |
| D6 | `guardian_articulos_venezuela` | Guardian | negativa | volumen de cobertura de crisis |

## Variables Pulse

| Variable | Fuente | Peso base Pulse | Decision |
|---|---|---:|---|
| `wti_precio_usd` | FRED | 6.5% | incluir |
| `brent_precio_usd` | FRED | 4% | incluir |
| `crudo_dubai_usd` | World Bank Pink Sheet | 4% | incluir (2026-07); benchmark mediano-pesado cercano al Merey |
| `tasa_fed_funds_pct` | FRED | 4% | incluir |
| `usd_index_broad` | FRED | 3.5% | incluir |
| `vix_volatility` | FRED | 6% | incluir |
| `ust_10y_yield_pct` | FRED | 3% | incluir |
| `em_bond_spread_pct` | FRED (ICE BofA EM Corporate Plus OAS) | 4% | incluir (2026-07); cobertura desde 2023-07 por ventana movil de FRED |
| `petroleo_crudo_produccion_tbpd` | EIA International | 25% | incluir; cobertura refleja lag |
| `importaciones_eeuu_crudo_ven_tbpd` | FRED `IR14270` (aduana EEUU) | 5% | sustituye a IMF IMTS el 2026-08-11: 2 meses de rezago en vez de 4, volumen fisico, 198 meses de historia |
| `importaciones_eeuu_productos_ven_tbpd` | FRED `IR14260` (aduana EEUU) | 5% | idem; captura actividad refinadora y licencias |
| `guardian_articulos_venezuela` | Guardian | 6.5% | incluir |
| `guardian_tono_titulares` | Guardian + VADER | 10% | incluir |
| `gdelt_cobertura_vol` | GDELT DOC | 5.5% | incluir si API entrega datos |
| `gdelt_tono_noticias` | GDELT DOC | 8% | incluir si API entrega datos |

Ampliacion 2026-07: se agregaron cuatro variables mensuales de tres fuentes
nuevas (IMF IMTS, WB Pink Sheet, ICE BofA via FRED). Los pesos previos se
reescalaron proporcionalmente (x0.82) para ceder 18% a las nuevas variables;
la estructura relativa entre bloques queda: macro externo 35%, energia 25%,
comercio espejo 10%, percepcion 30%.

El comercio espejo (mirror statistics) usa exclusivamente lo que EEUU reporta
de su comercio con Venezuela via IMF IMTS: dato mensual real de actividad
sin tocar fuentes venezolanas. Es la practica estandar cuando un pais deja
de reportar comercio confiable.

Pulse no incluye snapshots sanciones externas ni acumulados migratorios como si fueran
series mensuales de alta frecuencia cuando el pipeline no dispone de una
historia mensual real y reproducible.

## Variables apartadas o con rol distinto

| Variable o grupo | Rol actual | Motivo |
|---|---|---|
| `ied_neta_usd` | outcome externo | evita circularidad ICIV-IED |
| `remesas_recibidas_usd` | apartada | publicacion insuficiente reciente |
| `vuelos_aerolineas_int_count` | apartada | sin historia verificable robusta en OpenSky actual |
| `ief_overall_score` | apartada | redundancia institucional frente a CPI/WGI/FH/WJP |
| `vdem_libdem_index` | apartada | fuerte solape institucional; util como benchmark |
| `fragile_states_index` | apartada | solape y menor consistencia temporal que el core |
| `rsf_press_freedom` | apartada | cobertura/metodologia menos limpia para score core |
| `bti_governance_index` | apartada | periodicidad y redundancia |
| `ucdp_conflicto_idx` | apartada | aporta poco a clima de inversion Venezuela en core actual |
| `basel_aml_index` | apartada | historia automatizada no asegurada |
| `tasa_alfabetizacion_adulta_pct` | apartada | actualizacion irregular |
| `ghi_score` | apartada | cobertura y periodicidad mas debiles que salud/HDI |
| `fao_calorias_per_capita` | apartada | solape social y menor foco inversion |
| `google_trends_vzla` | apartada | rate limits y cobertura inestable |
| `viirs_states.csv` (Li et al. por estado) | apartada 2026-07-29 | extraia por **bbox rectangular**: mediana 2x el area real del estado, 11 de 25 estados >2x, 56 pares de bboxes solapados (doble conteo de pixeles). El mapa subnacional usa ahora Black Marble con mascara poligonal exacta. Script y CSV se conservan para auditoria; fuera del pipeline. La serie **nacional** `viirs.csv` sigue en el score |

Apartar no significa borrar el fetch inmediatamente. Una fuente puede quedar
en el repositorio como evidencia auxiliar o backlog mientras no entre al score
core ni se publicite como cobertura efectiva.

## Auditoria de fuentes institucionales (2026-07-21)

Se auditaron los archivos manuales de D3/D5 contra las publicaciones
oficiales. Hallazgos y correcciones aplicadas:

| Archivo | Hallazgo | Correccion |
|---|---|---|
| `wjp.csv` | contenia la serie Rule of Law de V-Dem (via fallback OWID) etiquetada como WJP, con valores 0.211-0.009 y cobertura 2000-2025 imposible (el indice WJP existe desde 2012 y Venezuela puntua ~0.26-0.36) | reemplazado por el Historical Data File oficial del WJP (ediciones 2012-2013 a 2025); fallback OWID eliminado del fetch |
| `freedom_house.csv` | valores hardcodeados que no coincidian con los publicados (ej. 2012: decia 19, publicado 39; 2022: decia 11, publicado 15) y una formula PR/CL→0-100 presentada como oficial que Freedom House nunca publico | reemplazado por el Excel oficial All Data FIW (ediciones 2013-2024) mas ediciones 2025-2026 verificadas contra la pagina del pais; anos 2000-2011 quedan NaN |
| `hdi.csv` | mezclaba vintages de HDR distintos (2000=0.671 de un HDR viejo vs 0.703 del vigente) y tenia huecos 2001-2004, 2006-2009 | reemplazado por la serie completa de un solo vintage (UNDP HDR via OWID), 2000-2023 sin huecos; nuevo `fetch_hdi.py` |
| `pts.csv` | valores correctos pero terminaba en 2023 | actualizado a la edicion PTS 2025 (cubre hasta 2024) |

Consecuencia en el score: la dimension D3 pierde cobertura antes de 2012
(quedan CPI, WGI y PTS) y los scores 2012+ cambian porque los valores
corregidos de FH/WJP son mas altos que los erroneos. La cobertura se
reporta como siempre: faltante es faltante.

## Fuentes aprobadas presentes

- World Bank WDI y WGI.
- IMF WEO/DataMapper.
- US EIA International.
- FRED.
- Transparency International.
- Freedom House.
- WJP.
- Political Terror Scale.
- UNCTAD.
- UNHCR/R4V.
- WHO/UN IGME segun loader disponible.
- UNDP/OWID para HDI distribuido.
- Guardian API.
- GDELT DOC API.
- IMF IMTS (International Trade in Goods by partner country, sucesor de DOTS)
  para comercio espejo mensual EEUU-Venezuela.
- World Bank Commodity Markets "Pink Sheet" para crudo Dubai mensual.
- ICE BofA (via FRED) para spread de bonos emergentes.
- Google News RSS filtrado por whitelist internacional para la pestana de
  noticias; no entra al score.
- Figshare/Li et al. para luces nocturnas.

## Noticias internacionales del dashboard

La pestana `Noticias` combina dos capas:

| Capa | Archivo / API | Uso | Entra al score |
|---|---|---|---|
| Guardian | API abierta de The Guardian | tarjetas en vivo y variables Guardian mensual | Guardian mensual si entra al Pulse |
| Snapshot internacional | `data/raw/international_news.csv` desde Google News RSS | contexto cualitativo y diversidad de medios | no |

El snapshot internacional se filtra con una lista cerrada de medios
internacionales: Reuters, AP, BBC, Financial Times, Bloomberg, CNBC, CNN, NPR,
The Guardian, Al Jazeera, France 24, DW, The New York Times, The Washington Post,
The Economist, Miami Herald, Yahoo Finance, MarketWatch, The Wall Street Journal,
Forbes, Voice of America, The Independent, ABC, CBS, NBC, Politico, Semafor y
Euronews, entre otros definidos en codigo.

Se excluyen fuentes locales venezolanas o dominios `.ve`. Si el RSS no entrega
noticias que pasen el filtro, el archivo queda vacio; no se crean noticias de
relleno.

## GDELT

GDELT DOC API alimenta dos variables de percepcion mensual del Pulse. Su API
publica aplica rate limit (HTTP 429) por **frecuencia** de peticiones, no por
tamano de ventana: se verifico el 2026-07-29 que una ventana de 3 meses pasaba
mientras otra de 1 mes fallaba segundos antes.

Estrategia vigente (2026-07-29), tras estar vacio varias semanas:

- La serie se pide en **tramos anuales** en vez de un unico rango de 11 anos.
- `--years N` limita los tramos por corrida; el workflow semanal usa 4.
- Cada tramo reintenta con backoff (10s, 30s, 60s).
- Los anos ya completos (12 meses y 2 variables) no se vuelven a pedir; el ano
  en curso siempre se refresca.
- Lo descargado se **acumula** sobre el CSV previo: una corrida parcial mejora
  la cobertura sin borrar lo obtenido antes.
- Nunca se crea fallback sintetico para simular cobertura.

El fetch escribe `iciv/data/raw/gdelt_monthly.status.json` con los anos
logrados y los tramos que fallaron, para auditar la cobertura real.

Resultado: la serie paso de 0 a **91 meses (2019-2026)** y la cobertura del
Pulse subio de 43.5% a 57% en el mes en curso, alcanzando **100% con las 15
variables** en los meses ya publicados por todas las fuentes.

## Fuentes candidatas para subir coverage o valor

### Candidatas de corto plazo

| Fuente | Uso potencial | Condicion de entrada |
|---|---|---|
| OPEC MOMR (fuentes secundarias) | produccion de crudo venezolano mensual, mas oportuna que EIA | el sitio OPEC bloquea descargas automatizadas (HTTP 403, verificado 2026-07); requiere parseo PDF reproducible |
| US Census intltrade API | comercio espejo EEUU-VEN mas oportuno que IMTS (~2 meses lag) | requiere API key gratuita (api.census.gov); complementa IMTS |
| UN Comtrade | DATOS DESCARGADOS (2026-07-22): `comtrade_monthly.csv`, comercio espejo de 5 socios (Espana, Brasil, India, Turkiye, China) con Venezuela, 2010-01 a 2026-06 (198 meses, ambos flujos). MAS OPORTUNO que IMF IMTS (junio 2026 vs marzo 2026). Advertencia de lectura: los ultimos ~3 meses son PARCIALES porque no todos los socios han reportado (ej. una caida abrupta en el ultimo trimestre refleja socios faltantes, no colapso comercial). Capa auxiliar de contexto/validacion del bloque espejo IMTS; NO entra al score ni al Pulse sin decision de peso + backtest | reporte parcial de socios en meses recientes |
| NASA Black Marble monthly | COMPLETO (2026-07-22). `blackmarble_monthly.csv`: **149 meses 2014-2026 con 5 agregaciones nacionales** (media, mediana, log-media, p90, fraccion iluminada). `blackmarble_states_monthly.csv`: radiancia media por los **25 estados** (3725 filas), habilita el **mapa coropletico animado 2014-2026** del dashboard (verificado: brillo 2014 alto → minimo 2017-2020 → recuperacion hasta 2026; ranking Distrito Capital 46.7, Monagas 12.2 petroleo, Amazonas 0.02 selva — fisicamente correcto). VALIDACION de agregaciones vs Li et al. anual (`blackmarble_validation.csv`, 11 años): la **media es la que mejor correlaciona** (Pearson r=+0.649, p=0.031); las robustas NO mejoran (log-media r=+0.17, p90 r≈0, mediana degenerada por pais mayormente oscuro) — resultado honesto: capturan una señal distinta de la serie armonizada, no una mejor. DECISION: capa auxiliar/contextual de alta frecuencia y subnacional; NO entra al Pulse (la media ya esta representada por la luminosidad anual del score). Workflow semanal mantiene al dia (--months 4) | token Earthdata expira cada ~60 dias |

Integradas en 2026-07 (ya no son candidatas): IMF IMTS (antes DOTS), World
Bank Pink Sheet, spread EM de ICE BofA via FRED, y UNCTADstat LSCI
trimestral (reemplaza al WDI congelado en 2021; serie completa 2006-2026 en
base Q1-2023=100, promedio anual de trimestres publicados, sin mezclar
bases con la serie WDI antigua).

### Candidatas de mediano plazo

| Fuente | Uso potencial | Riesgo |
|---|---|---|
| ACLED | DATOS DESCARGADOS (2026-07-22): `acled_monthly.csv` con 4 variables mensuales (eventos, protestas, violencia politica, fatalidades), 2018-01 a 2025-07, 27,247 eventos. LIMITACION CLAVE: la cuenta actual entrega los datos con ~12 meses de rezago (la serie termina exactamente 12 meses atras), por lo que NO sirve para alertas SATV en tiempo real — solo para contexto historico y validacion. Solucion posible: solicitar acceso academico completo a ACLED con el correo institucional .edu.co. NO entra al score ni al Pulse | rezago de acceso ~12 meses en el tier actual; sesgo de reporte |
| OpenSanctions API | historial estructurado de sanciones OFAC/EU/UK (reactivaria `ofac_sanciones_count`) | historia temporal limitada; validar reproducibilidad |
| R4V (ACNUR/OIM) | cortes intra-anuales de migracion venezolana | formato de publicacion cambia entre reportes |
| Global Database of Events alternatives | percepcion/noticias | redundancia con Guardian/GDELT |
| Shipping/AIS internacional | conectividad | costo, licencia y reproducibilidad |

Una fuente nueva debe competir con la variable core que reemplazaria. Agregar
por cantidad baja claridad y puede bajar cobertura efectiva.

## Purga de variables y resultado de cobertura (2026-08-11, segunda ronda)

El core paso de **26 a 21 variables**. Detalle y criterio en
[METODOLOGIA.md](./METODOLOGIA.md) seccion 2.8.

Eliminadas: `reservas_internacionales_usd`, `tipo_cambio_oficial_lcu_usd`,
`desempleo_pct`, `gas_natural_produccion_bcf`, `electricidad_generacion_bkwh`.
Sus fetchers y CSV se conservan; solo dejan de contar en el score.

Migrada: `luminosidad_nocturna_idx` de Li et al. (rezago ~2 anios) a NASA Black
Marble (rezago 2 meses). Serie completa 2014-2026, sin empalmar con la anterior.

### Cobertura anual

| Anio | Antes | Ahora |
|---:|---:|---:|
| 2020 | 91,9 % | **100 %** |
| 2022 | 88,9 % | **100 %** |
| 2023 | 88,9 % | **100 %** |
| 2024 | 86,1 % | **97,2 %** |
| 2025 | 61,7 % | **83,8 %** |
| 2026 | 33,7 % | **50,7 %** |

Media 2000-2024: **92,6 %**. Diez anios al 100 %.

**Coste declarado:** 2000-2013 bajan (2000: 88,9 % → 84,2 %) porque Black Marble
empieza en 2014 y esos anios pierden la luminosidad. Se acepta: el indice debe
poder describir el presente, y D2 conserva la produccion petrolera con historia
completa.

### Cobertura mensual (Pulse)

- 198 de 200 meses con cobertura >= 70 % (99 %).
- Cobertura media: **90,4 %**.
- El ultimo mes con cobertura suficiente paso de **t-4 a t-2** al sustituir el
  comercio espejo de IMF IMTS por las series de aduana de EEUU en FRED.

## Auditoria de cobertura (2026-08-11)

Se midio variable por variable cuanto peso pierde cada anio y por que causa.
Detalle metodologico en [METODOLOGIA.md](./METODOLOGIA.md) secciones 2.5, 2.6 y 9.

Resultado de las medidas aplicadas:

| Anio | Cobertura antes | Cobertura despues |
|---:|---:|---:|
| 2023 | 90,1 % | 88,9 % |
| 2024 | 83,7 % | 86,1 % |
| 2025 | 51,1 % | **61,7 %** |
| 2026 | 24,7 % | **33,7 %** |

Cambios que la produjeron:

1. **Las fuentes anuales no se refrescaban.** Solo se actualizaban a mano; la
   ultima vez fue el 2026-07-21. Al re-descargar aparecio un anio mas en cinco
   indicadores WDI. Ahora hay un job mensual en el workflow.
2. **Salud migrada de WHO GHO al World Bank** (ver tabla de variables core).
3. **Produccion petrolera del anio en curso** desde la serie mensual del mismo
   producto EIA (57), validada al 0,05 % contra la anual.

Retrocesos, declarados:

- 2022 y 2023 bajan 1,2 puntos porque el World Bank **retiro** los valores
  2020-2024 del tipo de cambio oficial. Ver METODOLOGIA seccion 9.4.

Descartado tras verificarlo: sustituir `desempleo_pct` por la estimacion
modelada de la OIT. Las series difieren hasta un 85 % y no son empalmables
(METODOLOGIA seccion 9.6).

## Politica de coverage

- Score anual: mostrar cobertura de peso disponible por ano.
- Pulse: mostrar cobertura por mes y numero de variables disponibles.
- Control semanal: FRED, Guardian y EIA son core; GDELT y noticias RSS son
  complementarias. Si una fuente core queda demasiado vieja, el workflow falla
  antes de publicar una actualizacion.
- Faltante es faltante. No se rellena con un numero inventado para que la grafica
  parezca continua.
