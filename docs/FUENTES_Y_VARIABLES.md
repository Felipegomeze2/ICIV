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
| D1 | `reservas_internacionales_usd` | World Bank WDI | positiva | buffer externo con faltantes visibles |
| D1 | `tipo_cambio_oficial_lcu_usd` | World Bank WDI | negativa | estres cambiario publicado |
| D1 | `wti_precio_usd` | FRED | positiva | condicion externa petrolera |
| D1 | `tasa_fed_funds_pct` | FRED | negativa | costo financiero global |
| D2 | `petroleo_crudo_produccion_tbpd` | EIA | positiva | capacidad petrolera central |
| D2 | `gas_natural_produccion_bcf` | EIA | positiva | energia complementaria |
| D2 | `electricidad_generacion_bkwh` | EIA | positiva | infraestructura energetica |
| D2 | `luminosidad_nocturna_idx` | Li et al./Figshare | positiva | proxy satelital de actividad |
| D3 | `cpi_score` | Transparency International | positiva | corrupcion percibida |
| D3 | `wgi_promedio_sc` | World Bank WGI | positiva | gobernanza compuesta |
| D3 | `freedom_house_score` | Freedom House | positiva | libertades relevantes al entorno; solo Aggregate Score publicado (2012+) |
| D3 | `wjp_rule_of_law` | WJP | positiva | regla de derecho; el indice existe desde 2012, antes NaN |
| D3 | `pts_terror_politico` | Political Terror Scale | negativa | coercion y riesgo institucional |
| D4 | `exportaciones_pct_pib` | WDI/OWID | positiva | apertura comercial |
| D4 | `desempleo_pct` | IMF/OWID | negativa | absorcion economica |
| D4 | `migrantes_vzla_millones` | UNHCR/R4V | negativa | salida poblacional acumulada |
| D4 | `lsci_conectividad_maritima` | UNCTADstat (trimestral → promedio anual) | positiva | conectividad logistica; serie 2006-2026 base Q1-2023=100 |
| D5 | `hdi` | UNDP/OWID | positiva | capital humano agregado |
| D5 | `esperanza_vida_anos` | WHO/WDI | positiva | condicion sanitaria |
| D5 | `mortalidad_infantil_x1000` | WHO/WDI | negativa | fragilidad social |
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
| `importaciones_espejo_usa_musd` | IMF IMTS (reporta EEUU) | 5% | incluir (2026-07); mirror statistics, sin fuente venezolana |
| `exportaciones_espejo_usa_musd` | IMF IMTS (reporta EEUU) | 5% | incluir (2026-07); captura dinamica de licencias petroleras |
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

GDELT DOC API se conserva como fuente opcional de percepcion mensual. Como su API
publica puede rate-limit o devolver respuestas no JSON, el fetch escribe un
archivo de estado:

```text
iciv/data/raw/gdelt_monthly.status.json
```

Politica vigente:

- Si GDELT entrega filas reales, se actualiza `gdelt_monthly.csv`.
- Si falla y existe una serie previa no vacia, se preserva la serie previa y se
  registra la advertencia.
- Si falla y no existe serie real previa, el CSV queda vacio.
- Nunca se crea fallback sintetico para simular cobertura.

## Fuentes candidatas para subir coverage o valor

### Candidatas de corto plazo

| Fuente | Uso potencial | Condicion de entrada |
|---|---|---|
| OPEC MOMR (fuentes secundarias) | produccion de crudo venezolano mensual, mas oportuna que EIA | el sitio OPEC bloquea descargas automatizadas (HTTP 403, verificado 2026-07); requiere parseo PDF reproducible |
| US Census intltrade API | comercio espejo EEUU-VEN mas oportuno que IMTS (~2 meses lag) | requiere API key gratuita (api.census.gov); complementa IMTS |
| UN Comtrade | comercio mensual observado (mirror, mas socios) | evaluar token, historia, cobertura y stable product groups |
| NASA Black Marble monthly | actividad nocturna mas oportuna | pipeline raster reproducible y comparabilidad con serie anual |

Integradas en 2026-07 (ya no son candidatas): IMF IMTS (antes DOTS), World
Bank Pink Sheet, spread EM de ICE BofA via FRED, y UNCTADstat LSCI
trimestral (reemplaza al WDI congelado en 2021; serie completa 2006-2026 en
base Q1-2023=100, promedio anual de trimestres publicados, sin mezclar
bases con la serie WDI antigua).

### Candidatas de mediano plazo

| Fuente | Uso potencial | Riesgo |
|---|---|---|
| ACLED | conflicto/eventos | coverage reciente y sesgo de reporte |
| OpenSanctions API | historial estructurado de sanciones OFAC/EU/UK (reactivaria `ofac_sanciones_count`) | historia temporal limitada; validar reproducibilidad |
| R4V (ACNUR/OIM) | cortes intra-anuales de migracion venezolana | formato de publicacion cambia entre reportes |
| Global Database of Events alternatives | percepcion/noticias | redundancia con Guardian/GDELT |
| Shipping/AIS internacional | conectividad | costo, licencia y reproducibilidad |

Una fuente nueva debe competir con la variable core que reemplazaria. Agregar
por cantidad baja claridad y puede bajar cobertura efectiva.

## Politica de coverage

- Score anual: mostrar cobertura de peso disponible por ano.
- Pulse: mostrar cobertura por mes y numero de variables disponibles.
- Control semanal: FRED, Guardian y EIA son core; GDELT y noticias RSS son
  complementarias. Si una fuente core queda demasiado vieja, el workflow falla
  antes de publicar una actualizacion.
- Faltante es faltante. No se rellena con un numero inventado para que la grafica
  parezca continua.
