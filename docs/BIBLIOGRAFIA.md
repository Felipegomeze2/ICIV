# Bibliografía y fuentes ICIV

Referencias que sostienen el diseño metodológico y el catálogo de datos. Hasta
agosto de 2026 esta lista vivía en la pestaña "Bibliografía" del dashboard; se
trasladó aquí cuando el dashboard pasó a ser el producto para el usuario final.

---

## 1. Marco metodológico

Índices compuestos, ponderación, normalización y validación.

1. **Saaty, T. L. (1980).** *The Analytic Hierarchy Process: Planning, Priority
   Setting, Resource Allocation*. McGraw-Hill.
   — Base del cálculo de pesos AHP y de la Razón de Consistencia (CR).

2. **OECD & JRC. (2008).** *Handbook on Constructing Composite Indicators:
   Methodology and User Guide*. París: OECD Publishing.
   — Estándar de referencia para construcción de índices compuestos.

3. **Nardo, M., Saisana, M., Saltelli, A., et al. (2005).** *Tools for composite
   indicators building*. EUR 21682 EN. Joint Research Centre.

4. **Saisana, M., Saltelli, A., & Tarantola, S. (2005).** Uncertainty and
   sensitivity analysis techniques as tools for the quality assessment of
   composite indicators. *Journal of the Royal Statistical Society A*, 168(2).
   — Fundamento del análisis de sensibilidad (SI) del ICIV.

5. **Bekaert, G., & Harvey, C. R. (2003).** Emerging markets finance.
   *Journal of Empirical Finance*, 10(1–2), 3–55.

6. **Jerven, M. (2013).** *Poor Numbers: How We Are Misled by African Development
   Statistics*. Cornell University Press.
   — Limitaciones de los datos oficiales en países en crisis; sustenta la
   política de excluir fuentes originadas en Venezuela.

## 2. Series de tiempo, nowcasting y predicción

7. **Stock, J. H., & Watson, M. W. (2002).** Macroeconomic forecasting using
   diffusion indexes. *Journal of Business & Economic Statistics*, 20(2), 147–162.
   — Base teórica del ICIV Pulse y del nowcast OLS.

8. **Aruoba, S. B., Diebold, F. X., & Scotti, C. (2009).** Real-time measurement
   of business conditions. *Journal of Business & Economic Statistics*, 27(4).
   — Índice ADS de condiciones de negocio; marco del co-indicador de alta frecuencia.

9. **Hyndman, R. J., & Athanasopoulos, G. (2018).** *Forecasting: Principles and
   Practice*, 3ª ed. OTexts. Capítulos 8–9.
   — SARIMA, selección de orden por AIC y evaluación rolling-origin.

10. **Granger, C. W. J. (1969).** Investigating causal relations by econometric
    models and cross-spectral methods. *Econometrica*, 37(3), 424–438.
    — Prueba de causalidad usada en el bloque exploratorio ICIV → IED.

## 3. Luminosidad nocturna como proxy de actividad económica

11. **Henderson, J. V., Storeygard, A., & Weil, D. N. (2012).** Measuring economic
    growth from outer space. *American Economic Review*, 102(2), 994–1028.
    — Fundamento de usar radiancia nocturna como proxy de actividad económica.

12. **Li, X., Zhou, Y., et al. (2020).** A harmonized global nighttime light
    dataset 1992–2024. *Scientific Data*, 7(1).
    Figshare DOI: 10.6084/m9.figshare.9828827
    — Serie nacional armonizada usada en `luminosidad_nocturna_idx` (cubre
    2000–2013, previo a VIIRS).

## 4. Análisis de sentimiento

13. **Hutto, C. J., & Gilbert, E. (2014).** VADER: A Parsimonious Rule-based Model
    for Sentiment Analysis of Social Media Text. *ICWSM*.
    — Motor de tono aplicado a titulares del Guardian.

## 5. Datos de conflicto

14. **Raleigh, C., Kishi, R., & Linke, A. (2023).** Political instability patterns
    are obscured by conflict dataset scope conditions, sources, and coding choices.
    *Humanities and Social Sciences Communications*, 10(1).
    — Referencia del dataset ACLED (capa auxiliar).

---

## 6. Fuentes de datos

Todas internacionales. **Ninguna originada en Venezuela.** El detalle de qué
variable sale de cada fuente está en
[FUENTES_Y_VARIABLES.md](./FUENTES_Y_VARIABLES.md) y la trazabilidad por archivo
en [../iciv/data/sources/PROVENANCE.md](../iciv/data/sources/PROVENANCE.md).

### Organismos multilaterales

| Fuente | Uso | Enlace |
|---|---|---|
| World Bank — World Development Indicators (WDI) | Macro, comercio, capital humano | https://databank.worldbank.org/source/world-development-indicators |
| World Bank — Worldwide Governance Indicators (WGI) | `wgi_promedio_sc` | Kaufmann, Kraay & Mastruzzi (2010), *Policy Research* 5430 |
| World Bank — Commodity Markets "Pink Sheet" | `crudo_dubai_usd` | https://www.worldbank.org/en/research/commodity-markets |
| IMF — World Economic Outlook | PIB e inflación | https://www.imf.org/en/Publications/WEO |
| IMF — International Trade in Goods (IMTS) | Comercio espejo EEUU–Venezuela | https://data.imf.org/en/datasets/IMF.STA:IMTS |
| UN Comtrade | Comercio espejo multi-socio (capa auxiliar) | https://comtradeplus.un.org |
| UNCTAD — UNCTADstat | `lsci_conectividad_maritima` (bulk oficial US.LSCI) | https://unctadstat.unctad.org |
| UNDP — Human Development Report | `hdi` | https://hdr.undp.org |
| UNHCR — Refugee Data Finder | `migrantes_vzla_millones` | https://www.unhcr.org/refugee-statistics |
| World Bank WDI | Esperanza de vida (`SP.DYN.LE00.IN`), mortalidad infantil (`SP.DYN.IMRT.IN`) | https://databank.worldbank.org |
| WHO — Global Health Observatory | Fuente anterior de salud, retirada del core el 2026-08-11; se conserva para auditoria | https://www.who.int/data/gho |
| ILO — ILOSTAT | `ilo_empleo_informal_pct` | https://ilostat.ilo.org |

### Gobierno de EEUU y banca central

| Fuente | Uso | Enlace |
|---|---|---|
| U.S. Energy Information Administration (EIA) | Producción de petróleo, gas y electricidad (anual y mensual) | https://www.eia.gov/international/data/ |
| Federal Reserve Bank of St. Louis (FRED) | WTI, Brent, Fed Funds, USD index, VIX, UST 10Y, spread EM | https://fred.stlouisfed.org |
| ICE BofA EM Corporate Plus OAS (vía FRED) | `em_bond_spread_pct` | https://fred.stlouisfed.org/series/BAMLEMCBPIOAS |

### Índices institucionales

| Fuente | Uso | Enlace |
|---|---|---|
| Transparency International — CPI | `cpi_score` | https://www.transparency.org/en/cpi |
| Freedom House — Freedom in the World | `freedom_house_score` | https://freedomhouse.org |
| World Justice Project — Rule of Law Index | `wjp_rule_of_law` | https://worldjusticeproject.org |
| Political Terror Scale — Gibney, Cornett, Wood et al. | `pts_terror_politico` | https://www.politicalterrorscale.org |

### Satélite

| Fuente | Uso | Enlace |
|---|---|---|
| NASA Black Marble VNP46A3 (LAADS DAAC, colección 002) | Mapa subnacional de radiancia nocturna | https://ladsweb.modaps.eosdis.nasa.gov |
| Li et al. (2020) harmonized NTL | `luminosidad_nocturna_idx` nacional | Figshare DOI: 10.6084/m9.figshare.9828827 |

### Prensa

| Fuente | Uso | Enlace |
|---|---|---|
| The Guardian Open Platform | `guardian_articulos_venezuela`, `guardian_tono_titulares`, pestaña de Noticias en vivo | https://open-platform.theguardian.com/ |
| GDELT DOC 2.0 API | `gdelt_cobertura_vol`, `gdelt_tono_noticias` | https://api.gdeltproject.org |
| Google News RSS (snapshot filtrado) | Prensa internacional del producto; **no entra al score** | https://news.google.com |

### Redistribución

| Fuente | Uso |
|---|---|
| Our World in Data | Redistribución con licencia abierta de HDI y otras series |

### Fuentes excluidas por política del proyecto

BCV, INE, PDVSA, OVF, IIES-UCAB y cualquier otra originada en Venezuela.
La razón está en `MODEL_CARD.md` y en Jerven (2013): en un país donde la
estadística oficial dejó de ser confiable o verificable, incorporarla
contaminaría el índice y lo haría indefendible.

---

## 7. Software

Todo open source.

| Capa | Herramientas |
|---|---|
| Lenguaje | Python 3.10+ |
| Análisis | pandas, numpy, scipy, statsmodels |
| NLP | vaderSentiment (Hutto & Gilbert, 2014) |
| Raster | h5py + numpy (Black Marble VNP46A3, máscara poligonal por estado) |
| Visualización | Chart.js, SVG nativo (mapa coroplético), matplotlib |
| HTTP / scraping | requests, BeautifulSoup4 |
| Descompresión | py7zr (bulk UNCTADstat) |

---

## 8. Cita sugerida

> Gómez Espinal, F. (2026). *ICIV — Indicador de Clima de Inversión Venezuela:
> diseño metodológico, pipeline ETL automatizado y dashboard interactivo*.
> Tesis de Especialización en Big Data e Inteligencia de Negocios,
> Universidad EIA. Disponible en: `github.com/Felipegomeze2/ICIV`
