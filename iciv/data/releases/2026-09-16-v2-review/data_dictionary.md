# Data dictionary

| Variable | Rol | ICIV anual | Pulse mensual | Dimension | Fuente | Unidad | Direccion | Peso ICIV | Descripcion |
|---|---|---:|---:|---|---|---|---|---:|---|
| inflacion_ipc_imf_pct | core_anual | True | False | D1_macro | IMF | % anual | negative | 0.101602 | Inflacion de precios al consumidor (FMI) |
| pib_crecimiento_real_pct | core_anual | True | False | D1_macro | WDI | % | positive | 0.079834 | Crecimiento real del PIB |
| reservas_internacionales_usd | auxiliar | False | False | D1_macro | WDI | USD | positive | 0.0 | Reservas internacionales |
| tipo_cambio_oficial_lcu_usd | auxiliar | False | False | D1_macro | WDI | BsF/USD equivalente | negative | 0.0 | Tipo de cambio oficial (unidad original WDI) |
| wti_precio_usd | core_anual | True | True | D1_macro | FRED | USD/barril | positive | 0.043537 | Precio WTI del petroleo |
| tasa_fed_funds_pct | core_anual | True | True | D1_macro | FRED | % | negative | 0.029033 | Tasa efectiva de fondos federales de EE. UU. |
| petroleo_crudo_produccion_tbpd | core_anual | True | False | D2_energia | EIA | mil barriles/dia | positive | 0.146434 | Produccion de crudo y condensado de arrendamiento (EIA producto 57) |
| gas_natural_produccion_bcf | auxiliar | False | False | D2_energia | EIA | BCF | positive | 0.0 | Produccion de gas natural |
| electricidad_generacion_bkwh | auxiliar | False | False | D2_energia | EIA | bkWh | positive | 0.0 | Generacion electrica |
| luminosidad_nocturna_idx | core_anual | True | False | D2_energia | VIIRS | nW/cm2/sr | positive | 0.048811 | Luminosidad nocturna satelital |
| cpi_score | core_anual | True | False | D3_institucional | CPI | 0-100 | positive | 0.046859 | Indice de percepcion de corrupcion |
| wgi_promedio_sc | core_anual | True | False | D3_institucional | WGI | percentil 0-100 | positive | 0.046859 | Promedio WGI de gobernanza |
| freedom_house_score | core_anual | True | False | D3_institucional | FREEDOM_HOUSE | 0-100 | positive | 0.035144 | Freedom House aggregate score |
| wjp_rule_of_law | core_anual | True | False | D3_institucional | WJP | 0-1 | positive | 0.035144 | World Justice Project Rule of Law |
| pts_terror_politico | core_anual | True | False | D3_institucional | PTS | 1-5 | negative | 0.031239 | Political Terror Scale |
| exportaciones_pct_pib | core_anual | True | False | D4_comercial | WDI | % PIB | positive | 0.077961 | Exportaciones de bienes y servicios |
| desempleo_pct | auxiliar | False | False | D4_comercial | IMF | % | negative | 0.0 | Tasa de desempleo |
| migrantes_vzla_millones | core_anual | True | False | D4_comercial | UNHCR | millones | negative | 0.055029 | Refugiados y solicitantes de asilo venezolanos |
| lsci_conectividad_maritima | core_anual | True | False | D4_comercial | UNCTAD | indice (base promedio Q1 2023 = 100) | positive | 0.041263 | Liner Shipping Connectivity Index |
| hdi | core_anual | True | False | D5_capital_humano | HDI | 0-1 | positive | 0.025375 | Indice de Desarrollo Humano |
| esperanza_vida_anos | core_anual | True | False | D5_capital_humano | WDI | anos | positive | 0.016313 | Esperanza de vida al nacer |
| mortalidad_infantil_x1000 | core_anual | True | False | D5_capital_humano | WDI | muertes por 1.000 nacidos vivos | negative | 0.016313 | Mortalidad infantil |
| acceso_electricidad_pct | core_anual | True | False | D5_capital_humano | WDI | % poblacion | positive | 0.016313 | Acceso a electricidad |
| empleo_vulnerable_oit_pct | core_anual | True | False | D5_capital_humano | WDI | % empleo | negative | 0.016313 | Empleo vulnerable (estimacion modelada OIT) |
| guardian_tono_titulares | core_anual | True | True | D6_percepcion | GUARDIAN | VADER compound | positive | 0.058906 | Tono de titulares internacionales |
| guardian_articulos_venezuela | core_anual | True | True | D6_percepcion | GUARDIAN | articulos | negative | 0.031719 | Volumen de cobertura internacional |
| ied_neta_usd | outcome_externo | False | False | D4_comercial | WDI | USD | positive | 0.0 | Inversion extranjera directa neta |
| petroleo_liquidos_totales_tbpd | pulse_mensual | False | True | D2_energia | EIA | mil barriles/dia | positive | 0.0 | Produccion total de petroleo y otros liquidos |
| crudo_dubai_usd | pulse_mensual | False | True | D1_macro | WDI | USD/barril | positive | 0.0 | Precio del crudo Dubai |
| em_bond_spread_pct | pulse_mensual | False | True | D1_macro | FRED | puntos porcentuales | negative | 0.0 | Diferencial corporativo de mercados emergentes |
| importaciones_eeuu_crudo_ven_tbpd | pulse_mensual | False | True | D4_comercial | FRED | mil barriles/dia | positive | 0.0 | Importaciones de crudo venezolano en EE. UU. |
| importaciones_eeuu_productos_ven_tbpd | pulse_mensual | False | True | D4_comercial | FRED | mil barriles/dia | positive | 0.0 | Importaciones de productos petroleros venezolanos en EE. UU. |
| brent_precio_usd | pulse_mensual | False | True | D1_macro | FRED | USD/barril | positive | 0.0 | Precio Brent del petroleo |
| usd_index_broad | pulse_mensual | False | True | D1_macro | FRED | indice | negative | 0.0 | Indice amplio del dolar |
| vix_volatility | pulse_mensual | False | True | D1_macro | FRED | indice | negative | 0.0 | VIX volatilidad financiera |
| ust_10y_yield_pct | pulse_mensual | False | True | D1_macro | FRED | % | negative | 0.0 | Treasury 10Y yield |
| gdelt_cobertura_vol | pulse_mensual | False | True | D6_percepcion | GDELT | indice | negative | 0.0 | Volumen de cobertura GDELT |
| gdelt_tono_noticias | pulse_mensual | False | True | D6_percepcion | GDELT | tono | positive | 0.0 | Tono de cobertura GDELT |
