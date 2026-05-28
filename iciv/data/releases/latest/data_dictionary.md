# Data dictionary

| Variable | Rol | ICIV anual | Pulse mensual | Dimension | Fuente | Unidad | Direccion | Peso ICIV | Descripcion |
|---|---|---:|---:|---|---|---|---|---:|---|
| inflacion_deflactor_pib_pct | core_anual | True | False | D1_macro | IMF | % log10 | negative | 0.07 | Inflacion, deflactor del PIB |
| pib_crecimiento_real_pct | core_anual | True | False | D1_macro | WDI | % | positive | 0.055 | Crecimiento real del PIB |
| reservas_internacionales_usd | core_anual | True | False | D1_macro | WDI | USD | positive | 0.045 | Reservas internacionales |
| tipo_cambio_oficial_lcu_usd | core_anual | True | False | D1_macro | WDI | log10 BsF/USD equivalente | negative | 0.03 | Tipo de cambio oficial homogeneizado |
| wti_precio_usd | core_anual | True | True | D1_macro | FRED | USD/barril | positive | 0.03 | Precio WTI del petroleo |
| tasa_fed_funds_pct | core_anual | True | True | D1_macro | FRED | % | negative | 0.02 | Tasa efectiva de fondos federales de EE. UU. |
| petroleo_crudo_produccion_tbpd | core_anual | True | True | D2_energia | EIA | mil barriles/dia | positive | 0.09 | Produccion de petroleo crudo |
| gas_natural_produccion_bcf | core_anual | True | False | D2_energia | EIA | BCF | positive | 0.05 | Produccion de gas natural |
| electricidad_generacion_bkwh | core_anual | True | False | D2_energia | EIA | bkWh | positive | 0.03 | Generacion electrica |
| luminosidad_nocturna_idx | core_anual | True | False | D2_energia | VIIRS | indice 0-100 | positive | 0.03 | Luminosidad nocturna satelital |
| cpi_score | core_anual | True | False | D3_institucional | CPI | 0-100 | positive | 0.048 | Indice de percepcion de corrupcion |
| wgi_promedio_sc | core_anual | True | False | D3_institucional | WGI | percentil 0-100 | positive | 0.048 | Promedio WGI de gobernanza |
| freedom_house_score | core_anual | True | False | D3_institucional | FREEDOM_HOUSE | 0-100 | positive | 0.036 | Freedom House aggregate score |
| wjp_rule_of_law | core_anual | True | False | D3_institucional | WJP | 0-1 | positive | 0.036 | World Justice Project Rule of Law |
| pts_terror_politico | core_anual | True | False | D3_institucional | PTS | 1-5 | negative | 0.032 | Political Terror Scale |
| exportaciones_pct_pib | core_anual | True | False | D4_comercial | WDI | % PIB | positive | 0.051 | Exportaciones de bienes y servicios |
| desempleo_pct | core_anual | True | False | D4_comercial | IMF | % | negative | 0.036 | Tasa de desempleo |
| migrantes_vzla_millones | core_anual | True | False | D4_comercial | UNHCR | millones | negative | 0.036 | Migrantes y refugiados venezolanos |
| lsci_conectividad_maritima | core_anual | True | False | D4_comercial | UNCTAD | 0-100 | positive | 0.027 | Liner Shipping Connectivity Index |
| hdi | core_anual | True | False | D5_capital_humano | HDI | 0-1 | positive | 0.028 | Indice de Desarrollo Humano |
| esperanza_vida_anos | core_anual | True | False | D5_capital_humano | WHO | anos | positive | 0.018 | Esperanza de vida al nacer |
| mortalidad_infantil_x1000 | core_anual | True | False | D5_capital_humano | WHO | muertes por 1.000 nacidos vivos | negative | 0.018 | Mortalidad infantil |
| acceso_electricidad_pct | core_anual | True | False | D5_capital_humano | WDI | % poblacion | positive | 0.018 | Acceso a electricidad |
| ilo_empleo_informal_pct | core_anual | True | False | D5_capital_humano | ILOSTAT | % empleo | negative | 0.018 | Empleo informal |
| guardian_tono_titulares | core_anual | True | True | D6_percepcion | GUARDIAN | VADER compound | positive | 0.065 | Tono de titulares internacionales |
| guardian_articulos_venezuela | core_anual | True | True | D6_percepcion | GUARDIAN | articulos | negative | 0.035 | Volumen de cobertura internacional |
| ied_neta_usd | outcome_externo | False | False | D4_comercial | WDI | USD | positive | 0.0 | Inversion extranjera directa neta |
| brent_precio_usd | pulse_mensual | False | True | D1_macro | FRED | USD/barril | positive | 0.0 | Precio Brent del petroleo |
| usd_index_broad | pulse_mensual | False | True | D1_macro | FRED | indice | negative | 0.0 | Indice amplio del dolar |
| vix_volatility | pulse_mensual | False | True | D1_macro | FRED | indice | negative | 0.0 | VIX volatilidad financiera |
| ust_10y_yield_pct | pulse_mensual | False | True | D1_macro | FRED | % | negative | 0.0 | Treasury 10Y yield |
| gdelt_cobertura_vol | pulse_mensual | False | True | D6_percepcion | GDELT | indice | negative | 0.0 | Volumen de cobertura GDELT |
| gdelt_tono_noticias | pulse_mensual | False | True | D6_percepcion | GDELT | tono | positive | 0.0 | Tono de cobertura GDELT |
