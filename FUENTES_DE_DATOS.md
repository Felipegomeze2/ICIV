# ICIV — Guía Completa de Fuentes de Datos
## Todas las fuentes públicas disponibles para el proyecto

> **Última actualización:** 21 de mayo de 2026 — Correcciones: BCV/OVF/PDVSA marcadas como excluidas; actualización de estado de pipeline  
> **Criterio:** Solo fuentes 100% públicas y gratuitas. **CERO datos inventados, CERO fallbacks estáticos.**  
> **Organización:** Por tipo de acceso → API nativa · Descarga directa · Scraping/Manual
>
> ⛔ **REGLA PRINCIPAL:** Si no hay dato real de una fuente verificable, la variable queda NaN. No se inventa, no se estima, no se llena con fallback. Ver `iciv/CLAUDE.md` para la regla completa.

---

## Índice rápido

| Tipo de acceso | Fuentes |
|---------------|---------|
| 🟢 **API REST pública (sin key)** | Banco Mundial WDI, WGI, IMF DataMapper, UNHCR, WHO GHO |
| 🔵 **API REST (requiere key gratis)** | EIA (energía), FRED (Federal Reserve), The Guardian, OFAC SDN |
| 🟡 **Descarga directa CSV/Excel** | Transparency Int. CPI, UNDP HDI, Heritage Foundation IEF, UNCTAD, Freedom House, PTS |
| ⛔ **EXCLUIDAS (fuentes venezolanas)** | BCV, OVF, IIES-UCAB, PDVSA — no son fuentes confiables internacionalmente; usar IMF/WB/EIA como sustitutos |
| 🌐 **pytrends (Python unofficial)** | Google Trends (requiere instalación) |

> **Nota:** Las fuentes marcadas con ★ están integradas en el pipeline. Dato real o NaN — sin substituciones manuales.

**Fuentes actualmente integradas en el pipeline ICIV ★ (18 loaders):**
WDI · WGI · EIA · IMF DataMapper · CPI (TI) · IEF (Heritage) · HDI (UNDP) · The Guardian API · FRED · Freedom House · OFAC · **UNHCR** (coo=VEN) · Google Trends · UNCTAD · OpenSky · **PTS** _(nuevo)_ · **WHO GHO** _(nuevo)_

**Fuentes con datos pero sin automatizar (disponibles si se descarga manualmente):**
VIIRS/NASA — requiere cuenta NASA Earthdata · ACLED — requiere registro · V-Dem — dataset >500MB

---

## GRUPO A — APIs con librería Python oficial o bien documentada

Estas son las fuentes más fáciles de automatizar. Se pueden integrar directamente en el pipeline sin descargar archivos manualmente.

---

### A1. Banco Mundial — World Development Indicators (WDI)
**🟢 API gratis, sin API key, librería Python disponible**

- **URL principal:** https://data.worldbank.org/country/venezuela-rb
- **API base:** `https://api.worldbank.org/v2/country/VEN/indicator/[CODIGO]?format=json`
- **Documentación API:** https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- **Librería Python recomendada:** `wbdata` — `pip install wbdata`
- **Código de Venezuela:** `VEN`

**Datos disponibles para Venezuela:**

| Indicador | Código API | Dimensión ICIV |
|-----------|-----------|---------------|
| PIB (USD corrientes) | `NY.GDP.MKTP.CD` | Estabilidad Macro |
| Crecimiento del PIB (%) | `NY.GDP.MKTP.KD.ZG` | Estabilidad Macro |
| Inflación (deflactor PIB) | `NY.GDP.DEFL.KD.ZG` | Estabilidad Macro |
| Inversión Extranjera Directa neta (USD) | `BX.KLT.DINV.CD.WD` | Apertura Comercial |
| IED (% del PIB) | `BX.KLT.DINV.WD.GD.ZS` | Apertura Comercial |
| Exportaciones de bienes y servicios (% PIB) | `NE.EXP.GNFS.ZS` | Apertura Comercial |
| Acceso a electricidad (% población) | `EG.ELC.ACCS.ZS` | Capital Humano |
| Tasa de alfabetización adulta (%) | `SE.ADT.LITR.ZS` | Capital Humano |
| Índice de Capital Humano | `HD.HCI.OVRL` | Capital Humano |
| Tipo de cambio oficial (LCU/USD) | `PA.NUS.FCRF` | Apertura Financiera |
| Reservas totales (USD) | `FI.RES.TOTL.CD` | Estabilidad Macro |
| Deuda externa total (USD) | `DT.DOD.DECT.CD` | Estabilidad Macro |
| Doing Business — facilidad de hacer negocios | `IC.BUS.EASE.XQ` | Apertura Comercial |
| Doing Business — puntaje general | `IC.BUS.DFRN.XQ` | Apertura Comercial |

**Cobertura temporal:** Series desde 1960, con datos hasta 2023-2024 según indicador.

**Ejemplo de uso en Python:**
```python
import wbdata
import datetime

# Descargar PIB de Venezuela 2010-2023
indicadores = {
    'NY.GDP.MKTP.KD.ZG': 'crecimiento_pib',
    'BX.KLT.DINV.CD.WD': 'IED_neta',
    'EG.ELC.ACCS.ZS': 'acceso_electricidad'
}
paises = ['VEN']
fecha_inicio = datetime.datetime(2010, 1, 1)
fecha_fin = datetime.datetime(2023, 12, 31)

df = wbdata.get_dataframe(indicadores, country=paises)
```

**⚠️ Limitaciones:** El Doing Business fue descontinuado por el Banco Mundial en 2021 (último año: 2020). Los datos siguen disponibles históricamente.

---

### A2. Banco Mundial — Worldwide Governance Indicators (WGI)
**🟢 API gratis, sin API key, accesible vía wbdata**

- **URL principal:** https://info.worldbank.org/governance/wgi/
- **DataBank:** https://databank.worldbank.org/source/worldwide-governance-indicators
- **Código de Venezuela:** `VEN`

**Los 6 indicadores de gobernanza para Venezuela:**

| Indicador | Código API | Descripción |
|-----------|-----------|-------------|
| Voz y Rendición de Cuentas | `VA.EST` | Libertad de expresión, elecciones, prensa |
| Estabilidad Política / Ausencia de Violencia | `PV.EST` | Probabilidad de desestabilización violenta |
| Efectividad del Gobierno | `GE.EST` | Calidad de servicios públicos y burocracia |
| Calidad Regulatoria | `RQ.EST` | Capacidad para promover sector privado |
| Estado de Derecho | `RL.EST` | Confianza en reglas y cumplimiento de contratos |
| Control de la Corrupción | `CC.EST` | Percepción del poder ejercido para ganancia privada |

**Escala:** −2.5 (peor) a +2.5 (mejor).  
**Cobertura temporal:** 1996–2024 (anual). Sin gaps para Venezuela.

**Descarga directa (Excel):**
https://databank.worldbank.org/data/download/WGI_excel.zip

---

### A3. UN Comtrade — Estadísticas de Comercio Internacional
**🟢 API pública, librería Python oficial disponible**

- **URL principal:** https://comtradeplus.un.org/
- **Developer portal / API docs:** https://comtradedeveloper.un.org/
- **Librería Python:** `comtradeapicall` — `pip install comtradeapicall`
- **Código de Venezuela:** `484`
- **API key:** Gratuita, requiere registro en https://comtradeplus.un.org/

**Datos disponibles:**
- Exportaciones e importaciones de Venezuela por producto (clasificación HS)
- Flujos comerciales bilaterales (con qué países comercia Venezuela)
- Exportaciones petroleras vs. no petroleras (diferenciables por código HS)
- Valor USD, cantidad (toneladas), precio unitario

**Cobertura temporal:** 1988–presente (anual); 2000–presente (mensual).

**Ejemplo de uso en Python:**
```python
import comtradeapicall

# Exportaciones de Venezuela en 2022
df = comtradeapicall.getFinalData(
    subscription_key='TU_API_KEY',
    typeCode='C',       # Commodities
    freqCode='A',       # Annual
    clCode='HS',        # Clasificación HS
    period='2022',
    reporterCode='484', # Venezuela
    cmdCode='TOTAL',
    flowCode='X',       # Exports
    partnerCode=None,   # All partners
    partner2Code=None
)
```

---

## GRUPO B — API REST (requiere registro gratuito)

---

### B1. EIA — U.S. Energy Information Administration
**🔵 API REST, requiere API key gratis**

- **URL Venezuela:** https://www.eia.gov/international/data/country/VEN
- **Portal API:** https://www.eia.gov/opendata/
- **Documentación:** https://www.eia.gov/opendata/documentation.php
- **Registro API key (gratis):** https://www.eia.gov/opendata/register.php
- **API base:** `https://api.eia.gov/v2/`

**Datos disponibles para Venezuela:**

| Indicador | Descripción | Frecuencia |
|-----------|-------------|-----------|
| Producción de petróleo crudo | Miles de barriles/día | Mensual |
| Exportaciones de crudo | Miles de barriles/día | Mensual |
| Producción de gas natural | Bcf (pies cúbicos) | Mensual/Anual |
| Consumo de energía total | Quad BTU | Anual |
| Intensidad energética | BTU por USD del PIB | Anual |
| Capacidad de refinación | Miles de bpd | Anual |
| Generación eléctrica | Millones de kWh | Anual |

**Cobertura temporal:** 1980–presente para la mayoría. Actualizaciones mensuales.

**Ejemplo de llamada API:**
```
https://api.eia.gov/v2/international/data/?api_key=TU_KEY&facets[countryRegionCode][]=VEN&facets[productName][]=Crude+oil+production
```

**Descarga directa (sin API):** https://www.eia.gov/international/data/country/VEN — botones de descarga CSV por indicador.

---

### B2. IMF — Fondo Monetario Internacional
**🔵 API disponible + Descarga masiva Excel (recomendada)**

- **Portal de datos:** https://data.imf.org/en
- **DataMapper (Venezuela):** https://www.imf.org/external/datamapper/profile/VEN
- **WEO Database:** https://www.imf.org/en/Publications/WEO/weo-database/2024/October

**⭐ Recomendación práctica: descarga el Excel completo del WEO**

Descarga directa del World Economic Outlook (todos los países, todos los indicadores):
- **Abril 2025 — Dataset completo:** https://www.imf.org/en/Publications/WEO/weo-database/2025/April/download-entire-database

El archivo Excel contiene Venezuela con los siguientes indicadores:

| Indicador IMF (código WEO) | Descripción |
|---------------------------|-------------|
| `NGDP_RPCH` | Crecimiento real del PIB (%) |
| `PCPIPCH` | Variación del IPC / Inflación (%) |
| `PCPIE` | Índice de precios al consumidor (fin de período) |
| `LUR` | Tasa de desempleo (%) |
| `BCA` | Cuenta corriente (USD) |
| `BCA_NGDPD` | Cuenta corriente (% del PIB) |
| `GGXCNL_NGDP` | Préstamo/endeudamiento neto del gobierno (% PIB) |
| `GGXWDG_NGDP` | Deuda bruta del gobierno (% PIB) |
| `NGDPD` | PIB nominal en USD |
| `LP` | Población total |

**Cobertura temporal:** 1980–2029 (incluye proyecciones hasta 5 años).

**⚠️ Nota crítica Venezuela:** El IMF suspendió la consulta del Artículo IV con Venezuela en 2004. Los datos recientes son estimaciones, no cifras oficiales reportadas. Igual son las mejores estimaciones internacionales disponibles.

---

### B3. CEPALSTAT — Comisión Económica para América Latina
**🔵 API experimental + Descarga web**

- **Portal:** https://statistics.cepal.org/portal/cepalstat/
- **Perfil Venezuela:** https://statistics.cepal.org/portal/cepalstat/perfil-nacional-economico.html?lang=es&country=VEN
- **API base (experimental):** `https://cepalstat-prod.cepal.org/api/v1/`

**Datos disponibles:**
- PIB y sus componentes (consumo, inversión, exportaciones)
- Formación bruta de capital fijo
- Balanza de pagos
- Deuda externa
- Inflación (IPC)
- Pobreza e indigencia (% de la población)
- Distribución del ingreso (coeficiente de Gini)
- Datos fiscales

**Cobertura temporal:** Desde 1950 para algunas series; mayoría desde 1990. Actualizaciones anuales.

**Acceso práctico:** El portal web permite filtrar Venezuela, seleccionar indicadores y exportar a CSV desde la interfaz. La API requiere exploración pero funciona.

---

## GRUPO C — Descarga directa CSV / Excel

Estas fuentes no tienen API formal pero publican archivos descargables directamente desde su web.

---

### C1. Transparency International — CPI (Índice de Percepción de Corrupción)
**🟡 Descarga CSV/Excel directa**

- **URL:** https://www.transparency.org/en/cpi
- **Descarga directa de datos históricos:** https://images.transparencycdn.org/images/CPI-full-data-2023.zip (reemplazar año)
- **Últimas versiones disponibles:** 2012–2023

**Datos para Venezuela:**
- Puntaje CPI (0–100, donde 0 = muy corrupto, 100 = muy limpio)
- Ranking global (posición entre ~180 países)
- Número de fuentes usadas para calcular el score

**Venezuela histórico (referencia):**
- 2023: 13/100 — puesto 169 de 180
- 2015: 17/100
- 2010: 19/100

**Frecuencia:** Anual (publicación en enero/febrero de cada año).

---

### C2. UNDP — Índice de Desarrollo Humano (IDH)
**🟡 Descarga Excel directa**

- **URL:** https://hdr.undp.org/data-center/human-development-index
- **Descarga directa HDI histórico:** https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Statistical_Annex_HDI_Table.xlsx
- **Data center completo:** https://hdr.undp.org/data-center/documentation-and-downloads

**Datos para Venezuela:**
- IDH compuesto (0–1)
- Esperanza de vida al nacer (años)
- Años promedio de escolaridad
- Años esperados de escolaridad
- INB per cápita (USD PPP)
- IDH ajustado por desigualdad (IDHI)
- Índice de Desarrollo de Género (IDG)
- Índice de Pobreza Multidimensional (IPM)

**Cobertura temporal:** 1990–2023 (series consistentes para análisis longitudinal).

**⚠️ Nota:** Venezuela tiene un IDH de rango "alto" históricamente por su capital humano acumulado, pero ha caído significativamente desde 2013.

---

### C3. Heritage Foundation — Índice de Libertad Económica
**🟡 Descarga CSV/Excel directa**

- **URL Venezuela:** https://www.heritage.org/index/country/venezuela
- **Descarga de datos históricos:** https://www.heritage.org/index/pages/all-country-scores
- **Bulk download:** https://www.heritage.org/index/download

**12 componentes del índice para Venezuela:**
Derechos de propiedad, efectividad judicial, integridad gubernamental, carga fiscal, gasto gubernamental, salud fiscal, libertad de negocios, libertad laboral, libertad monetaria, libertad de comercio, libertad de inversión, libertad financiera.

**Cobertura temporal:** 1995–2024 (anual).

**Venezuela 2024:** 26.2/100 — clasificada como "Reprimida" (última categoría).

**⚠️ Nota:** La metodología cambió en 2017. Para análisis longitudinal, verificar consistencia pre/post cambio.

---

### C4. OPEC — Annual Statistical Bulletin (ASB)
**🟡 Descarga Excel desde portal interactivo**

- **URL portal interactivo:** https://asb.opec.org
- **URL publicaciones:** https://publications.opec.org/asb
- **Página Venezuela:** Sección "Member Countries" → Venezuela

**Datos para Venezuela:**
- Producción cruda de petróleo (miles bpd, mensual y anual)
- Reservas probadas de petróleo (miles de millones de barriles)
- Exportaciones de crudo y derivados
- Ingresos de exportaciones petroleras
- PIB de Venezuela (metodología OPEC)
- Refinación y capacidad instalada

**Cobertura:** Edición actual 2024; archivos históricos 2020–2024 disponibles. Para datos más largos, combinar con EIA.

**Descarga:** El portal ASB permite exportar tablas a Excel desde cada sección.

---

### C5. UNCTAD — Estadísticas de Inversión y Comercio
**🟡 Descarga CSV/Excel directa**

- **Portal estadístico:** https://unctadstat.unctad.org/EN/Index.html
- **Perfil Venezuela:** https://unctadstat.unctad.org/CountryProfile/en-GB/index.html?codeN=862
- **World Investment Report:** https://unctad.org/topic/investment/world-investment-report

**Datos para Venezuela:**
- Flujos de IED entrante y saliente (anuales, USD)
- Stock de IED acumulado
- Exportaciones de bienes (USD y % del PIB)
- Exportaciones de servicios
- Indicadores de productividad

**Cobertura temporal:** IED desde 1970; comercio desde 1995. Actualización anual.

**⚠️ Nota:** Los datos de IED para Venezuela se vuelven cada vez más incompletos a partir de 2014 por las restricciones de capital y la salida de inversores.

---

### C6. UNESCO — Institute for Statistics (UIS)
**🟡 Descarga CSV + API**

- **Venezuela:** https://uis.unesco.org/en/country/ve
- **Bulk download:** https://apidata.uis.unesco.org/sdmx/v2/data/UNESCO,DF_UIS_SEA_COMP_M,1.0/VEN..._T.?format=csv
- **API docs:** https://apidata.uis.unesco.org/

**Datos para Venezuela:**
- Tasa de alfabetización adulta (15+ años)
- Tasa de alfabetización juvenil (15–24 años)
- Tasas de matrícula (primaria, secundaria, terciaria)
- Gasto en educación (% del PIB)
- Razón alumnos/maestro

**⚠️ Nota:** Venezuela dejó de reportar datos completos de educación a partir de 2015. Los valores recientes son estimaciones del modelo UNESCO, no cifras oficiales.

---

### C7. WEF — Global Competitiveness Index (HISTÓRICO SOLAMENTE)
**🟡 Descarga PDF / Excel (datos históricos únicamente)**

- **Último reporte con Venezuela:** https://www.weforum.org/publications/global-competitiveness-report-2019/
- **Archivo de reportes:** https://www.weforum.org/publications/?type=report

**⛔ IMPORTANTE:** El WEF **dejó de incluir a Venezuela** en el Global Competitiveness Index a partir de 2019 por falta de datos confiables. Solo tienes datos hasta 2018–2019.

**Datos históricos disponibles (2006–2018):**
- Puntaje GCI general (0–7)
- 12 pilares: instituciones, infraestructura, estabilidad macroeconómica, salud, educación, mercado de bienes, mercado laboral, sistema financiero, tamaño del mercado, dinamismo empresarial, capacidad innovadora.

**Uso recomendado:** Como variable histórica para la serie 2010–2018. Para 2019–2024, usar Heritage Foundation o WGI como sustitutos del pilar institucional.

---

## GRUPO D — Scraping / Extracción manual

Estas fuentes requieren más trabajo para obtener los datos, pero contienen información crítica y única para Venezuela.

---

### D1. BCV — Banco Central de Venezuela
**🔴 Scraping web / Descarga manual**

- **URL principal:** https://www.bcv.org.ve
- **Estadísticas:** https://www.bcv.org.ve/estadisticas
- **Tipo de cambio:** https://www.bcv.org.ve/tasas-de-cambio

**Datos disponibles (actualmente):**
- Tipo de cambio oficial USD/VES (diario)
- Tipo de cambio de divisas internacionales
- Tasas de interés activas y pasivas
- Índice Nacional de Precios al Consumidor (INPC)
- Liquidez monetaria
- Reservas internacionales
- Cuentas nacionales (PIB trimestral — publicación irregular)

**Acceso:**
- Los datos están en la web como tablas HTML o archivos PDF
- Requiere scraping con `BeautifulSoup` + `requests` en Python
- Algunas series se publican como archivos Excel descargables directamente

**⚠️ PROBLEMA CRÍTICO — El gran apagón estadístico del BCV (2014–2019):**
- El BCV no publicó prácticamente ninguna estadística oficial durante 5 años
- Para cubrir ese período hay que usar:
  - IMF WEO (estimaciones del FMI)
  - CEPAL (estimaciones regionales)
  - OVF (fuente venezolana alternativa)
  - Publicaciones académicas (IEES-UCAB, IESA)

**Estrategia de scraping básica:**
```python
import requests
from bs4 import BeautifulSoup

url = "https://www.bcv.org.ve/tasas-de-cambio"
headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')
# Extraer tabla de tasas
tablas = soup.find_all('table')
```

---

### D2. OVF — Observatorio Venezolano de Finanzas
**🔴 Descarga manual de PDFs + extracción**

- **URL:** https://observatoriodefinanzas.com/
- **Noticias/reportes:** https://observatoriodefinanzas.com/noticias/

**Por qué es importante esta fuente:**
Es la fuente venezolana independiente más completa para el período 2014–presente. Publica mensualmente datos que el BCV no divulga.

**Datos publicados (mensuales):**
- Índice de Actividad Económica OVF (proxy mensual del PIB)
- Inflación mensual desagregada
- Evolución de salarios reales
- Análisis de pobreza
- Tipo de cambio (paralelo y oficial)
- Expectativas económicas (encuesta)

**Acceso:** PDFs publicados en el sitio web. Requiere:
1. Descargar los PDFs mensualmente
2. Usar `pdfplumber` o `PyMuPDF` en Python para extraer las tablas
3. Construir la serie histórica manualmente

```python
import pdfplumber

with pdfplumber.open("reporte_ovf_marzo2025.pdf") as pdf:
    pagina = pdf.pages[0]
    tabla = pagina.extract_table()
```

---

### D3. IIES-UCAB — Instituto de Investigaciones Económicas y Sociales
**🔴 Descarga manual de PDFs**

- **URL:** https://www.ucab.edu.ve/investigacion/centros-e-institutos-de-investigacion/iies/
- **Publicaciones:** https://www.ucab.edu.ve/publicaciones-iies/

**Publicaciones clave:**
- **Informe de Coyuntura** (mensual) — análisis macroeconómico de Venezuela
- **Encuesta sobre condiciones de vida (ENCOVI)** — datos de pobreza, acceso a servicios, calidad de vida

La ENCOVI es la encuesta de condiciones de vida más rigurosa disponible para Venezuela desde que el INE dejó de publicar datos sociales.

**Acceso:** PDFs descargables desde el sitio. Mismo proceso de extracción que OVF.

---

### D4. PDVSA — Petróleos de Venezuela
**🔴 No usar directamente — usar EIA u OPEP como sustitutos**

- **URL:** http://www.pdvsa.com
- **Estado:** PDVSA no ha publicado reportes anuales ni memorias desde 2016.

**Estrategia:** Para datos de producción petrolera venezolana, usar exclusivamente:
1. EIA International Data (Venezuela): https://www.eia.gov/international/data/country/VEN
2. OPEP Annual Statistical Bulletin: https://asb.opec.org
3. S&P Global Commodity Insights (gratuito parcialmente): https://www.spglobal.com/commodityinsights

---

## GRUPO E — Fuentes complementarias y de verificación

Estas fuentes no entran directamente en el modelo pero son esenciales para **cubrir gaps de datos**, **verificar cifras** y construir el argumento académico.

---

### E1. Trading Economics — Venezuela
- **URL:** https://tradingeconomics.com/venezuela
- **Uso:** Agregador de datos de BCV, IMF, Banco Mundial. Útil para verificar valores rápidamente y encontrar series actualizadas cuando otras fuentes tienen lag.
- **Acceso:** Datos históricos básicos gratuitos en web. API de pago (no necesaria para la tesis).

---

### E2. The Global Economy — Venezuela
- **URL:** https://www.theglobaleconomy.com/Venezuela/
- **Uso:** Otro agregador. Buena visualización de series largas. Descarga CSV de indicadores individuales gratuita.
- **Acceso:** Descarga directa por indicador en CSV.

---

### E3. Macrotrends — Venezuela
- **URL:** https://www.macrotrends.net/countries/VEN/venezuela/gdp-growth-rate
- **Uso:** Series históricas largas (50+ años) de PIB, inflación, deuda. Útil para contexto histórico y verificación.

---

### E4. CountryEconomy — Venezuela
- **URL:** https://countryeconomy.com/countries/venezuela
- **Uso:** Agregador con buena cobertura de indicadores de deuda soberana, ratings crediticios, PIB per cápita histórico.

---

### E5. IMF DataMapper — Venezuela
- **URL:** https://www.imf.org/external/datamapper/profile/VEN
- **Uso:** Dashboard visual del IMF para Venezuela. No es para descargar datos, sino para verificar visualmente las proyecciones.

---

### E6. World Bank DataBank
- **URL:** https://databank.worldbank.org
- **Uso:** Interfaz gráfica del Banco Mundial para construir consultas personalizadas y descargar tablas en Excel. Útil cuando la API es compleja.

---

### E7. FRED — Federal Reserve Bank of St. Louis
- **URL:** https://fred.stlouisfed.org/categories/32251
- **Uso:** Series sobre Venezuela disponibles: precio del petróleo venezolano, tipo de cambio, algunos indicadores macroeconómicos importados de otras fuentes.
- **API:** Sí, disponible y gratuita. `pip install fredapi`

---

## Resumen estratégico: ¿Qué usa cada dimensión del ICIV?

| Dimensión ICIV | Fuentes en el modelo | Variables |
|----------------|---------------------|-----------|
| **D1 — Estabilidad Macroeconómica** | IMF DataMapper + WDI + FRED + estáticos BCV | inflación, PIB, reservas, tipo_cambio, WTI, Fed Funds |
| **D2 — Sector Energético** | EIA | producción crudo, gas, electricidad, luminosidad nocturna |
| **D3 — Entorno Institucional** | TI-CPI + WGI + Heritage IEF + Freedom House + OFAC | CPI, WGI, IEF, FH score, sanciones SDN |
| **D4 — Apertura Comercial** | WDI + IMF + UNHCR/R4V | IED, exportaciones, desempleo, migración |
| **D5 — Capital Humano** | UNDP HDI + WDI + estáticos UNESCO | HDI, alfabetización, acceso eléctrico |
| **D6 — Percepción Internacional** | The Guardian API + Google Trends | tono VADER, volumen artículos, búsquedas |

---

## Checklist de acceso: Lo que tienes que registrar/descargar

### Registros necesarios (gratuitos):
- [ ] **EIA API key:** https://www.eia.gov/opendata/register.php
- [ ] **UN Comtrade API key:** https://comtradeplus.un.org/ (crear cuenta)

### Librerías Python a instalar:
```bash
pip install wbdata          # Banco Mundial
pip install comtradeapicall  # UN Comtrade
pip install pandas numpy     # Manipulación de datos
pip install requests         # HTTP requests
pip install beautifulsoup4   # Web scraping BCV
pip install pdfplumber        # Extraer datos de PDFs (OVF, UCAB)
pip install fredapi           # FRED (opcional)
pip install openpyxl          # Leer archivos Excel
```

### Archivos a descargar manualmente (una sola vez):
- [ ] IMF WEO Excel completo: https://www.imf.org/en/Publications/WEO/weo-database/2025/April/download-entire-database
- [ ] WGI Excel completo: https://databank.worldbank.org/data/download/WGI_excel.zip
- [ ] TI-CPI histórico: https://www.transparency.org/en/cpi (sección "Download the data")
- [ ] UNDP HDI: https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Statistical_Annex_HDI_Table.xlsx
- [ ] Heritage Foundation: https://www.heritage.org/index/download
- [ ] OPEP ASB: https://asb.opec.org (descargar tablas de Venezuela)

---

---

## Nuevas fuentes integradas en Abril 2026

### FRED — Federal Reserve Bank of St. Louis ★
- **URL:** https://fred.stlouisfed.org
- **API:** `pip install fredapi` — requiere API key gratuita
- **Series usadas en ICIV:**
  - `DCOILWTICO` → `wti_precio_usd` (precio WTI anual, USD/barril)
  - `FEDFUNDS` → `tasa_fed_funds_pct` (tasa Fed Funds efectiva anual)
- **Relevancia:** El precio del crudo es el principal determinante del ingreso fiscal venezolano; la Fed Funds afecta el costo del capital global y los spreads de deuda emergente.

### Freedom House ★
- **URL:** https://freedomhouse.org/countries/freedom-world/scores
- **Acceso:** Descarga CSV anual desde el portal
- **Serie:** `freedom_house_score` — puntuación agregada de libertades políticas y civiles (0–100)
- **Cobertura Venezuela:** 2003–2026
- **Relevancia:** Captura el deterioro democrático post-2012 que no está completamente reflejado en el WGI.

### OFAC / US Treasury SDN ★
- **URL:** https://sanctionssearch.ofac.treas.gov / https://www.treasury.gov/ofac/downloads/sdn.xml
- **Acceso:** Archivo XML público descargable, sin API key
- **Serie:** `ofac_sanciones_count` — conteo de entidades venezolanas en la lista SDN activa por año
- **Relevancia:** Las sanciones OFAC bloquean transacciones financieras internacionales, acceso a banca corresponsal y mercados de capitales. Son un obstáculo directo a la inversión extranjera.

### UNHCR / R4V — Plataforma Regional de Refugiados y Migrantes ★
- **URL:** https://www.r4v.info/es/refugiadosymigrantes
- **Acceso:** Descarga CSV desde el portal R4V
- **Serie:** `migrantes_vzla_millones` — venezolanos en el exterior (millones de personas)
- **Relevancia:** El éxodo de 7+ millones de venezolanos (2015–2024) es el mayor movimiento de población en la historia de América Latina. Es un proxy inverso de condiciones de vida y confianza en el país.

### Google Trends ★
- **URL:** https://trends.google.com
- **Acceso:** `pip install pytrends` (API no oficial de Google)
- **Serie:** `google_trends_vzla` — interés de búsqueda global por "Venezuela inversión" (índice 0–100)
- **Relevancia:** El interés de búsqueda refleja la percepción de oportunidad de inversores, periodistas y tomadores de decisiones. Es un indicador adelantado de sentimiento.

---

*Este documento forma parte del proyecto ICIV. Ver también: `PROYECTO_ICIV_MASTER.md` y `CATALOGO_DE_DATOS.md`.*
