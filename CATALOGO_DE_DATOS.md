# Catálogo de Datos — ICIV Venezuela
## Indicador de Clima de Inversión Venezuela · Documentación de Fuentes y Variables

> **Período de cobertura del modelo:** 2000–2026 (27 años)
> **País:** Venezuela (VEN)  
> **Variables:** 27 en 6 dimensiones  
> **Fuentes:** 15 fuentes de datos  
> **Autor:** Felipe  
> **Última actualización:** Abril 2026

---

## Tabla de Contenidos

1. [Fuentes de Datos](#1-fuentes-de-datos)
2. [Variables por Dimensión](#2-variables-por-dimensión)
   - [D1 — Estabilidad Macroeconómica](#d1--estabilidad-macroeconómica-25-del-iciv)
   - [D2 — Sector Energético y Petróleo](#d2--sector-energético-y-petróleo-20-del-iciv)
   - [D3 — Entorno Institucional y Legal](#d3--entorno-institucional-y-legal-20-del-iciv)
   - [D4 — Apertura Comercial y Financiera](#d4--apertura-comercial-y-financiera-15-del-iciv)
   - [D5 — Capital Humano e Infraestructura](#d5--capital-humano-e-infraestructura-10-del-iciv)
   - [D6 — Percepción Internacional](#d6--percepción-internacional-10-del-iciv)
3. [Normalización de Variables](#3-normalización-de-variables)
4. [Cobertura Temporal por Variable](#4-cobertura-temporal-por-variable)
5. [Decisiones Metodológicas de Calidad de Datos](#5-decisiones-metodológicas-de-calidad-de-datos)

---

## 1. Fuentes de Datos

El ICIV usa **13 fuentes de datos**, todas públicas y gratuitas. Se clasifican por método de acceso:

---

### 1.1 World Development Indicators (WDI) — Banco Mundial

| Campo | Detalle |
|-------|---------|
| **Organización** | Banco Mundial (World Bank Group) |
| **Nombre completo** | World Development Indicators |
| **URL de acceso** | `https://api.worldbank.org/v2/country/VEN/indicator/{indicator}` |
| **Método de acceso** | API REST pública, sin autenticación requerida |
| **Formato de respuesta** | JSON o XML |
| **Periodicidad** | Anual |
| **Cobertura histórica Venezuela** | 1960–2024 (varía por indicador) |
| **Código de país** | `VEN` |

**¿Qué es el WDI?**
El WDI es la base de datos estadística más completa del Banco Mundial. Recopila más de 1.600 indicadores de desarrollo para 217 países, construidos a partir de fuentes nacionales e internacionales verificadas. Para Venezuela, provee datos macroeconómicos, sociales y sectoriales, aunque con crecientes brechas desde 2017 cuando el BCV dejó de reportar al Banco Mundial.

**Variables del ICIV que provee:**

| Indicador API | Columna ICIV | Descripción |
|---------------|-------------|-------------|
| `NY.GDP.MKTP.KD.ZG` | `pib_crecimiento_real_pct` | Crecimiento real del PIB |
| `FI.RES.TOTL.CD` | `reservas_internacionales_usd` | Reservas internacionales totales |
| `PA.NUS.FCRF` | `tipo_cambio_oficial_lcu_usd` | Tipo de cambio oficial |
| `BX.KLT.DINV.CD.WD` | `ied_neta_usd` | Inversión Extranjera Directa neta |
| `NE.EXP.GNFS.ZS` | `exportaciones_pct_pib` | Exportaciones como % del PIB |
| `EG.ELC.ACCS.ZS` | `acceso_electricidad_pct` | Acceso a electricidad |
| `SE.ADT.LITR.ZS` | `tasa_alfabetizacion_adulta_pct` | Tasa de alfabetización adulta |

**Nota crítica:** Venezuela dejó de reportar datos al Banco Mundial de manera sistemática a partir de 2018. Para reservas y tipo de cambio, los años 2018–2026 se completan con datos estáticos validados (BCV Informe Económico, IMF Article IV). Ver `scripts/fetch_wdi.py` sección `_STATIC_FALLBACKS`.

---

### 1.2 World Governance Indicators (WGI) — Banco Mundial

| Campo | Detalle |
|-------|---------|
| **Organización** | Banco Mundial — Programa de Gobernanza Global |
| **Nombre completo** | Worldwide Governance Indicators |
| **URL de datos** | `https://databank.worldbank.org/data/download/WGI_csv.zip` |
| **Método de acceso** | Descarga de archivo ZIP con CSVs anuales |
| **Periodicidad** | Anual (desde 1996) |
| **Cobertura Venezuela** | 1996–2024 |
| **Escala** | Percentil 0–100 (escala SC) o puntuación estándar (-2.5 a +2.5) |

**¿Qué son los WGI?**
Los WGI son un proyecto de investigación del Banco Mundial que mide la calidad de la gobernanza en más de 200 países mediante la agregación de cientos de variables de decenas de organizaciones (encuestas de empresas, ONGs, think tanks, agencias de calificación). Se publican anualmente desde 1996.

**Los 6 indicadores que usa el ICIV:**

| Código | Nombre | Qué mide |
|--------|--------|----------|
| `GOV_WGI_CC.SC` | Control de Corrupción | Percepción de corrupción en el sector público |
| `GOV_WGI_GE.SC` | Efectividad del Gobierno | Calidad de servicios públicos y burocracia |
| `GOV_WGI_PV.SC` | Estabilidad Política | Probabilidad de desestabilización por violencia |
| `GOV_WGI_RL.SC` | Estado de Derecho | Confianza en reglas sociales, policía y tribunales |
| `GOV_WGI_RQ.SC` | Calidad Regulatoria | Capacidad del gobierno para proveer regulación efectiva |
| `GOV_WGI_VA.SC` | Voz y Rendición de Cuentas | Participación ciudadana, libertad de expresión |

El ICIV usa el **promedio simple de los 6 indicadores** en la escala de percentil (0–100), almacenado en la columna `wgi_promedio_sc`.

---

### 1.3 EIA International Energy Statistics

| Campo | Detalle |
|-------|---------|
| **Organización** | U.S. Energy Information Administration (EIA) |
| **Nombre completo** | EIA International Energy Data |
| **URL de API** | `https://api.eia.gov/v2/international/data/` |
| **Método de acceso** | API REST, requiere API key gratuita (registro en eia.gov) |
| **Variable de entorno** | `EIA_API_KEY` |
| **Periodicidad** | Anual (datos preliminares del año en curso disponibles ~Q1 siguiente) |
| **Cobertura Venezuela** | 1980–2025 (2026 pendiente) |

**¿Qué es la EIA?**
La EIA es la agencia estadística y analítica principal del Departamento de Energía de Estados Unidos. Sus datos de producción energética internacional son el estándar de referencia para análisis de la industria petrolera venezolana, al ser independientes del gobierno venezolano y verificados contra datos de comercio exterior.

**Series energéticas del ICIV:**

| Serie EIA | Columna ICIV | Descripción |
|-----------|-------------|-------------|
| `INTL.57-1-VEN-TBPD.A` | `petroleo_crudo_produccion_tbpd` | Producción de petróleo crudo (miles de barriles/día) |
| `INTL.26-1-VEN-BCF.A` | `gas_natural_produccion_bcf` | Producción de gas natural (billones de pies cúbicos/año) |
| `INTL.2-12-VEN-BKWH.A` | `electricidad_generacion_bkwh` | Generación total de electricidad (billones de kWh/año) |

**Esta es la fuente más confiable del dataset:** cobertura completa 2000–2025, metodología estable, datos independientes del gobierno venezolano.

---

### 1.4 IMF DataMapper — Fondo Monetario Internacional

| Campo | Detalle |
|-------|---------|
| **Organización** | Fondo Monetario Internacional (FMI / IMF) |
| **Nombre completo** | IMF DataMapper / World Economic Outlook Database |
| **URL de API** | `https://www.imf.org/external/datamapper/api/v1` |
| **Método de acceso** | API REST pública, sin autenticación |
| **Periodicidad** | Anual (actualización semestral: Abril y Octubre) |
| **Cobertura Venezuela** | 1980–2026 (estimaciones para años en curso) |

**¿Qué es el IMF DataMapper?**
El FMI publica anualmente el World Economic Outlook (WEO) con proyecciones y datos históricos de todos sus países miembro. Para Venezuela, es especialmente crítico porque el IMF continúa publicando estimaciones del deflactor del PIB y desempleo aun cuando el BCV dejó de reportar (2014–2019). Las cifras del IMF para ese período son estimaciones, claramente marcadas como tales.

**Variables del ICIV que provee:**

| Concepto IMF | Columna ICIV | Descripción |
|-------------|-------------|-------------|
| `NGDP_D` | `inflacion_deflactor_pib_pct` | Deflactor del PIB (proxy de inflación) |
| `LUR` | `desempleo_pct` | Tasa de desempleo (% de la fuerza laboral) |
| `BCA_NGDPD` | `cuenta_corriente_pct_pib` | Cuenta corriente (% del PIB) — variable auxiliar |

**Por qué el Deflactor del PIB y no el IPC:** El IPC venezolano del WDI solo cubre 2009–2016. El Deflactor del PIB del IMF cubre 2000–2026 con datos completos, siendo el único proxy de inflación con cobertura histórica continua.

---

### 1.5 CPI — Índice de Percepción de Corrupción (Transparency International)

| Campo | Detalle |
|-------|---------|
| **Organización** | Transparency International |
| **Nombre completo** | Corruption Perceptions Index (CPI) |
| **URL de descarga** | `https://www.transparency.org/en/cpi` |
| **Método de acceso** | Descarga manual de Excel/CSV anual |
| **Periodicidad** | Anual (publicado cada enero para el año anterior) |
| **Escala** | 0 (más corrupto) a 100 (menos corrupto) |
| **Cobertura Venezuela** | 1995–2024 (pero metodología cambia en 2012) |

**¿Qué es el CPI?**
El CPI es el índice de percepción de corrupción más citado del mundo. Mide la percepción de la corrupción en el sector público de 180 países a partir de 13 fuentes de datos de organismos internacionales, encuestas a empresarios y análisis de riesgo país. **No mide corrupción directamente, sino la percepción de expertos y empresarios.**

**Limitación crítica para Venezuela:** La metodología cambió sustancialmente en 2012, haciendo los datos pre-2012 no directamente comparables con los post-2012. Además, Venezuela tiene solo 11 observaciones en el período de interés (2010–2023), lo que requiere interpolación. El archivo `data/raw/cpi.csv` sigue el formato estándar del pipeline.

---

### 1.6 IEF — Índice de Libertad Económica (Heritage Foundation)

| Campo | Detalle |
|-------|---------|
| **Organización** | The Heritage Foundation |
| **Nombre completo** | Index of Economic Freedom (IEF) |
| **URL de descarga** | `https://www.heritage.org/index/download` |
| **Método de acceso** | Descarga manual de Excel anual |
| **Periodicidad** | Anual (publicado en enero/febrero) |
| **Escala** | 0 (economía reprimida) a 100 (economía libre) |
| **Cobertura Venezuela** | 2000–2025 (con gaps en 2001–2004 y 2006–2007) |

**¿Qué es el IEF?**
El IEF evalúa la libertad económica en 184 países a partir de 12 componentes agrupados en 4 pilares: Estado de Derecho, Tamaño del Gobierno, Eficiencia Regulatoria y Apertura de Mercados. Venezuela ha sido categorizaba como economía "Reprimida" (puntaje < 40) desde 2013, con mínimo histórico de 24.6 en 2022.

**Venezuela por categoría IEF:**
- **Libre** (80–100): Nunca alcanzado
- **Mayormente libre** (70–79.9): Solo en los años 90
- **Moderadamente libre** (60–69.9): 2000–2005 aprox.
- **Mayormente no libre** (50–59.9): 2006–2012 aprox.
- **Reprimida** (0–49.9): Desde 2013 hasta hoy

---

### 1.7 HDI — Índice de Desarrollo Humano (PNUD)

| Campo | Detalle |
|-------|---------|
| **Organización** | Programa de las Naciones Unidas para el Desarrollo (PNUD / UNDP) |
| **Nombre completo** | Human Development Index (HDI) |
| **URL de descarga** | `https://hdr.undp.org/data-center/documentation-and-downloads` |
| **Método de acceso** | Descarga manual de CSV histórico |
| **Periodicidad** | Anual (publicado en el Informe de Desarrollo Humano) |
| **Escala** | 0 a 1 (se multiplica ×100 al normalizar para el ICIV) |
| **Cobertura Venezuela** | 1990–2022 (quinquenal hasta 2010, luego anual) |

**¿Qué es el HDI?**
El IDH es un índice compuesto del PNUD que mide tres dimensiones básicas del desarrollo humano: (1) vida larga y saludable (esperanza de vida), (2) educación (años de escolaridad), y (3) nivel de vida digno (ingreso per cápita). Para Venezuela, el IDH alcanzó su pico en 0.768 en 2015 y cayó a 0.699 en 2022, equivalente al nivel de 2005 — borrando 16 años de progreso.

---

### 1.8 The Guardian API

| Campo | Detalle |
|-------|---------|
| **Organización** | The Guardian Media Group |
| **Nombre completo** | The Guardian Open Platform API |
| **URL de API** | `https://content.guardianapis.com/search` |
| **Método de acceso** | API REST, requiere API key gratuita (registro en open-platform.theguardian.com) |
| **API key en proyecto** | Ver `settings.yaml` → `sources.guardian.api_key` |
| **Variable de entorno** | `GUARDIAN_API_KEY` (tiene prioridad sobre la key en yaml) |
| **Periodicidad** | Artículos disponibles desde 1999, en tiempo real |
| **Cobertura Venezuela** | 1999–2026 (histórica completa) |

**¿Qué es The Guardian API?**
The Guardian ofrece acceso programático a su archivo histórico de artículos desde 1999. Para el ICIV, se consultan todos los artículos que mencionan "Venezuela" por año, y se extrae: (1) el conteo total de artículos como proxy de intensidad de cobertura mediática, y (2) el tono de los primeros 50 titulares de cada año usando el análisis de sentimientos VADER.

**Variables del ICIV que provee:**

| Variable | Columna ICIV | Qué mide |
|----------|-------------|---------|
| Tono promedio VADER de titulares | `guardian_tono_titulares` | Sentimiento de la cobertura: positivo = buenas noticias |
| Conteo anual de artículos | `guardian_articulos_venezuela` | Volumen de atención mediática internacional |

**Nota metodológica (VADER):** VADER (Valence Aware Dictionary and sEntiment Reasoner) es un lexicón de análisis de sentimientos especialmente calibrado para textos cortos y titulares de noticias. El `compound score` va de -1 (muy negativo) a +1 (muy positivo). Un score cercano a 0 implica cobertura neutral.

---

### 1.9 GDELT Project

| Campo | Detalle |
|-------|---------|
| **Organización** | GDELT Project (financiado por Google Ideas) |
| **Nombre completo** | Global Database of Events, Language and Tone |
| **URL de API** | `https://api.gdeltproject.org/api/v2/doc/doc` |
| **Método de acceso** | API REST pública, sin autenticación |
| **Periodicidad** | Casi en tiempo real (actualización cada 15 minutos) |
| **Cobertura Venezuela** | 2015–2026 (DOC 2.0 API) |

**¿Qué es GDELT?**
GDELT es el proyecto de monitoreo de medios de comunicación globales más grande del mundo, procesando cientos de miles de artículos diariamente en decenas de idiomas. Para el ICIV, GDELT provee una perspectiva complementaria al Guardian: mide el tono de toda la cobertura mediática global sobre Venezuela (no solo un medio), aunque con cobertura histórica más limitada (desde 2015).

**Variables del ICIV que provee:**

| Variable | Columna ICIV | Qué mide |
|----------|-------------|---------|
| Tono promedio anual | `gdelt_tono_noticias` | Tono global de cobertura (-100 a +100) |
| Volumen anual de artículos | `gdelt_cobertura_vol` | Escala de atención mediática global |

> **Estado en el modelo:** GDELT se usa como variable auxiliar de validación. Las variables principales de la Dimensión 6 son las del Guardian, por su mayor cobertura histórica y mejor calidad de titulares en inglés.

---

## 2. Variables por Dimensión

A continuación se documenta cada variable con su significado, fuente, pesos y consideraciones de uso.

---

### D1 — Estabilidad Macroeconómica (25% del ICIV)

**Justificación de la dimensión:** La estabilidad macroeconómica es la condición necesaria para cualquier inversión sostenible. Sin control de la inflación y crecimiento económico positivo, las demás condiciones favorables se vuelven irrelevantes para un inversor racional. Es la dimensión con mayor peso en el índice.

---

#### `inflacion_deflactor_pib_pct` — Inflación (Deflactor del PIB)

| Campo | Detalle |
|-------|---------|
| **Fuente** | IMF DataMapper — concepto `NGDP_D` |
| **Unidad** | Porcentaje (%) |
| **Dirección** | **Negativa** — mayor inflación = peor clima de inversión |
| **Peso en D1** | 35% |
| **Peso en ICIV** | 8.75% |
| **Disponible desde** | 2000 (estimaciones para 2024–2026) |

**¿Qué mide?**
El deflactor del PIB mide el cambio de precios en toda la economía, no solo en la canasta de consumo del IPC. Se calcula como la razón entre el PIB nominal y el PIB real: `Deflactor = (PIB_nominal / PIB_real) × 100`. Un deflactor de 200% significa que los precios de toda la economía, en promedio, se duplicaron en un año.

**Por qué no se usa el IPC:** El IPC venezolano del WDI solo cubre 2009–2016. El deflactor del IMF cubre 2000–2026 de manera completa, siendo el único indicador de inflación con cobertura histórica continua. Para el período de hiperinflación (2018: 225.690%, 2019: 9.585%), los valores del deflactor son extremos que requieren transformación logarítmica antes de normalizar (ver Sección 3).

**Valores clave para Venezuela:**
- 2000–2010: 10%–50% (inflación alta pero manejable)
- 2018: **225.690%** — pico de hiperinflación
- 2024–2026: ~30–50% (recuperación parcial)

---

#### `pib_crecimiento_real_pct` — Crecimiento Real del PIB

| Campo | Detalle |
|-------|---------|
| **Fuente** | WDI — indicador `NY.GDP.MKTP.KD.ZG` |
| **Unidad** | Porcentaje (%) |
| **Dirección** | **Positiva** — mayor crecimiento = mejor clima |
| **Peso en D1** | 30% |
| **Peso en ICIV** | 7.5% |
| **Disponible desde** | 2002 (imputado para 2000–2001 desde IMF) |

**¿Qué mide?**
La variación porcentual del Producto Interno Bruto ajustado por inflación respecto al año anterior. Un PIB real que crece 5% significa que la economía produjo un 5% más de bienes y servicios reales que el año anterior. Para Venezuela, este indicador revela una de las contracciones económicas más severas de la historia moderna en tiempos de paz: −75% acumulado entre 2013 y 2020.

**Valores clave para Venezuela:**
- 2004: +18.3% (rebote tras el paro petrolero)
- 2013–2020: ocho años consecutivos de contracción
- 2020: **−30.0%** — peor año (COVID sobre crisis estructural)
- 2021–2024: recuperación parcial (+5% a +8% anuales desde base muy baja)

---

#### `reservas_internacionales_usd` — Reservas Internacionales

| Campo | Detalle |
|-------|---------|
| **Fuente** | WDI — indicador `FI.RES.TOTL.CD` + datos estáticos BCV/IMF |
| **Unidad** | USD (dólares estadounidenses) |
| **Dirección** | **Positiva** — mayores reservas = mayor capacidad de pago = mejor clima |
| **Peso en D1** | Peso igual (1/6 dentro de D1) |
| **Disponible desde** | 2000 (cobertura completa con estáticos) |

**¿Qué mide?**
Las reservas internacionales son los activos en divisas extranjeras y oro que el banco central mantiene para cubrir importaciones, pagar deuda externa y defender el tipo de cambio. Un país con reservas bajas es vulnerable a shocks externos y no puede garantizar el acceso a divisas para inversores extranjeros.

**Valores clave para Venezuela:**
- 2011: USD 29.900 M (pico histórico reciente)
- 2017: USD 9.660 M (último dato oficial del BM)
- 2018–2023: USD 5.980–9.480 M (estimaciones BCV/IMF Article IV)
- 2024–2026: ~USD 8.600–8.800 M (estimaciones IMF)

> **Decisión metodológica:** Post-2018 se usan datos estáticos del Informe Económico BCV y la Consulta del Artículo IV del IMF. Son estimaciones, no cifras oficiales verificadas — documentado en `scripts/fetch_wdi.py:_STATIC_RESERVAS`.

---

#### `tipo_cambio_oficial_lcu_usd` — Tipo de Cambio Oficial (log₁₀)

| Campo | Detalle |
|-------|---------|
| **Fuente** | WDI — indicador `PA.NUS.FCRF` + datos estáticos BCV |
| **Unidad** | log₁₀(BsF/USD equivalente) — ver transformación abajo |
| **Dirección** | **Negativa** — mayor devaluación = peor clima |
| **Peso en D1** | Peso igual (1/6 dentro de D1) |
| **Disponible desde** | 2000 (cobertura completa con estáticos) |

**¿Qué mide?**
El logaritmo en base 10 del tipo de cambio oficial expresado en Bolívares Fuertes equivalentes. La transformación log₁₀ es necesaria por las tres reconversiones monetarias venezolanas que hacen incomparable la serie nominal directa.

**Complejidad única de Venezuela — tres reconversiones monetarias:**
- **2000–2017:** WDI reporta en BsF directamente (retroconvirtió VEB÷1000)
- **2018–2021:** WDI reporta en BsS (1 BsS = 1.000 BsF) → pipeline multiplica ×1.000
- **2022+:** WDI reporta en Bs digital (1 Bs = 10⁶ BsS = 10⁹ BsF) → pipeline multiplica ×1.000.000.000

**Transformación aplicada en `main.py`:**
```python
# Llevar todo a BsF equivalente
tc[mask_bss] *= 1_000          # BsS→BsF
tc[mask_bs]  *= 1_000_000_000  # Bs→BsF
master["tipo_cambio_oficial_lcu_usd"] = np.log10(tc.clip(lower=1e-9))
```

**Resultado:** Score 2000 ≈ 50 (tipo de cambio bajo → buenas condiciones). Score 2026 = 0 (máxima devaluación en la serie histórica). Esta es la variable con el peor score en todo el dataset, lo que es económicamente correcto dado que la devaluación ha sido total desde 2018.

---

### D2 — Sector Energético y Petróleo (20% del ICIV)

**Justificación de la dimensión:** Venezuela posee las mayores reservas probadas de petróleo del mundo (303 mil millones de barriles, OPEP 2023). Los ingresos petroleros representan históricamente el 90–95% de las divisas del país. El estado de la industria petrolera es, por tanto, el principal determinante de la capacidad del Estado venezolano de funcionar y honrar compromisos con inversores.

---

#### `petroleo_crudo_produccion_tbpd` — Producción de Petróleo Crudo

| Campo | Detalle |
|-------|---------|
| **Fuente** | EIA — serie `INTL.57-1-VEN-TBPD.A` |
| **Unidad** | Miles de barriles por día (Mbpd) |
| **Dirección** | **Positiva** — mayor producción = más ingresos = mejor clima |
| **Peso en D2** | 50% |
| **Peso en ICIV** | 10% |
| **Disponible desde** | 2000 (serie completa) |

**¿Qué mide?**
El volumen diario promedio de petróleo crudo extraído y procesado por Venezuela. Es el indicador más directo del estado de la industria petrolera venezolana y el principal generador de divisas del país.

**Valores clave:**
- 2000: 2.893 Mbpd (nivel histórico de referencia)
- 2020: **527 Mbpd** — mínimo histórico (colapso de PDVSA + pandemia)
- 2024: 863 Mbpd — recuperación parcial (30% del nivel del año 2000)
- La caída del 82% entre 2000 y 2020 es la más pronunciada en la historia de la OPEP para un país en tiempos de paz.

---

#### `gas_natural_produccion_bcf` — Producción de Gas Natural

| Campo | Detalle |
|-------|---------|
| **Fuente** | EIA — serie `INTL.26-1-VEN-BCF.A` |
| **Unidad** | Billones de pies cúbicos por año (BCF/año) |
| **Dirección** | **Positiva** |
| **Peso en D2** | 30% |
| **Peso en ICIV** | 6% |
| **Disponible desde** | 2000 |

**¿Qué mide?**
La producción anual de gas natural. Venezuela tiene las octavas mayores reservas de gas del mundo. El gas es relevante para el ICIV porque alimenta la generación eléctrica, la industria petroquímica y potencialmente las exportaciones. La producción ha sido relativamente estable comparada con el petróleo, lo que modera la caída de D2.

---

#### `electricidad_generacion_bkwh` — Generación Eléctrica

| Campo | Detalle |
|-------|---------|
| **Fuente** | EIA — serie `INTL.2-12-VEN-BKWH.A` |
| **Unidad** | Billones de kilovatios-hora por año (bkWh/año) |
| **Dirección** | **Positiva** — mayor generación = mejor infraestructura |
| **Peso en D2** | 20% |
| **Peso en ICIV** | 4% |
| **Disponible desde** | 2000 |

**¿Qué mide?**
La producción total de electricidad (hidráulica + térmica). Es un proxy directo de la capacidad de infraestructura energética del país. Los cortes eléctricos masivos de 2019 (el "apagón" de marzo duró 5 días) se reflejan directamente en este indicador.

**Valores clave:**
- 2013: 135 bkWh — pico histórico
- 2023: 72 bkWh — caída del 47% desde el pico

---

### D3 — Entorno Institucional y Legal (20% del ICIV)

**Justificación de la dimensión:** La debilidad institucional genera el riesgo más temido por inversores extranjeros: expropiación, incumplimiento contractual e inseguridad jurídica. Venezuela ha experimentado múltiples expropiaciones masivas desde 2007 (PDVSA, acero, cementos, agroindustria, telecomunicaciones). Esta dimensión captura si las reglas del juego son predecibles y confiables.

---

#### `cpi_score` — Índice de Percepción de Corrupción

| Campo | Detalle |
|-------|---------|
| **Fuente** | Transparency International — CPI |
| **Unidad** | Score 0–100 (100 = sin corrupción percibida) |
| **Dirección** | **Positiva** — mayor score = menos corrupción = mejor clima |
| **Peso en D3** | 35% |
| **Peso en ICIV** | 7% |
| **Disponible desde** | 2010 (11 observaciones en 2010–2024) |

**¿Qué mide?**
La percepción de corrupción en el sector público según empresarios, analistas de riesgo y expertos. Un score de 13 (Venezuela 2023) significa que el país está entre los 5% más corruptos del mundo.

**Limitación:** Methodology cambió en 2012 (escala era 0–10, ahora 0–100). Solo hay datos para: 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2023. Los años intermedios (2020, 2021, 2022) y 2024–2025 se interpolan.

---

#### `wgi_promedio_sc` — Promedio WGI de Gobernanza

| Campo | Detalle |
|-------|---------|
| **Fuente** | Banco Mundial — WGI |
| **Unidad** | Percentil 0–100 (SC = Scaled Score) |
| **Dirección** | **Positiva** — mayor percentil = mejor gobernanza |
| **Peso en D3** | 35% |
| **Peso en ICIV** | 7% |
| **Disponible desde** | 2000 |

**¿Qué mide?**
El promedio simple de los 6 indicadores WGI (Control de Corrupción, Efectividad del Gobierno, Estabilidad Política, Estado de Derecho, Calidad Regulatoria, Voz y Rendición de Cuentas). Un percentil de 22 (Venezuela 2024) significa que Venezuela está peor que el 78% de los países del mundo en gobernanza agregada.

**Tendencia:** deterioro monotónico sin interrupción desde 2000 (44.5 percentil) hasta 2024 (22.2 percentil). Ningún indicador ha mostrado mejora sostenida en 24 años.

---

#### `ief_overall_score` — Índice de Libertad Económica

| Campo | Detalle |
|-------|---------|
| **Fuente** | Heritage Foundation — IEF |
| **Unidad** | Score 0–100 (100 = máxima libertad económica) |
| **Dirección** | **Positiva** |
| **Peso en D3** | 30% |
| **Peso en ICIV** | 6% |
| **Disponible desde** | 2000 (gaps 2001–2004, 2006–2007) |

**¿Qué mide?**
La libertad económica en 12 componentes: derechos de propiedad, efectividad judicial, integridad gubernamental, carga fiscal, gasto gubernamental, salud fiscal, libertad empresarial, libertad laboral, libertad monetaria, libertad comercial, libertad de inversión y libertad financiera.

**Venezuela en IEF:**
- 2000: 59.4 ("Mayormente no libre")
- 2013: primer año en categoría "Reprimida" (< 50)
- 2022: 24.6 — mínimo histórico

---

### D4 — Apertura Comercial y Financiera (15% del ICIV)

**Justificación de la dimensión:** Mide si es operativamente posible hacer negocios en Venezuela: acceder a divisas, traer capital, mover mercancías y repatriar ganancias. Una economía con controles de cambio estrictos, barreras comerciales y IED negativa es hostil para inversores incluso si otras condiciones fueran favorables.

---

#### `ied_neta_usd` — Inversión Extranjera Directa Neta

| Campo | Detalle |
|-------|---------|
| **Fuente** | WDI — indicador `BX.KLT.DINV.CD.WD` |
| **Unidad** | USD (millones) |
| **Dirección** | **Positiva** — IED positiva = entrada de capital externo |
| **Peso en D4** | 40% |
| **Peso en ICIV** | 6% |
| **Disponible desde** | 2000 (serie completa) |

**¿Qué mide?**
La diferencia entre el capital extranjero que entra a Venezuela (inversiones nuevas) y el que sale (desinversiones, repatriaciones). Un valor negativo significa que más capital externo salió del país del que entró — señal de fuga de inversión neta.

**Valores clave:**
- 2012: USD 5.973 M (pico del período)
- 2017: **−USD 299 M** — IED negativa: salida neta de capital
- 2023–2026: recuperación lenta, valores positivos pero bajos

---

#### `exportaciones_pct_pib` — Exportaciones (% del PIB)

| Campo | Detalle |
|-------|---------|
| **Fuente** | WDI — indicador `NE.EXP.GNFS.ZS` |
| **Unidad** | Porcentaje del PIB (%) |
| **Dirección** | **Positiva** — mayor apertura comercial = mejor |
| **Peso en D4** | 35% |
| **Peso en ICIV** | 5.25% |
| **Disponible desde** | 2000 |

**¿Qué mide?**
El total de exportaciones de bienes y servicios como proporción del PIB. En Venezuela, las exportaciones son casi exclusivamente petróleo, por lo que este indicador también captura la dependencia petrolera. Una caída en exportaciones/PIB puede reflejar tanto colapso de producción como caída del precio del crudo.

---

#### `desempleo_pct` — Tasa de Desempleo

| Campo | Detalle |
|-------|---------|
| **Fuente** | IMF DataMapper — concepto `LUR` |
| **Unidad** | Porcentaje de la fuerza laboral (%) |
| **Dirección** | **Negativa** — mayor desempleo = peor clima |
| **Peso en D4** | 25% |
| **Peso en ICIV** | 3.75% |
| **Disponible desde** | 2000 (serie completa) |

**¿Qué mide?**
La proporción de la población económicamente activa que está sin trabajo y buscando empleo activamente. En Venezuela, la tasa oficial de desempleo ha sido históricamente baja en los registros del IMF (6–8%), lo que probablemente subestima el desempleo real dado el enorme sector informal (estimado > 60% de la fuerza laboral).

> **Nota metodológica:** Este indicador debe interpretarse con cautela para Venezuela. La informalidad laboral masiva, la emigración de 7+ millones de venezolanos (2015–2024) y la falta de encuestas confiables hacen que la tasa de desempleo sea uno de los datos más discutibles del dataset.

---

### D5 — Capital Humano e Infraestructura (10% del ICIV)

**Justificación de la dimensión:** A pesar de todas las crisis, Venezuela conserva ventajas relativas en capital humano respecto a sus pares regionales: alta alfabetización histórica (95%+), una clase media técnicamente capacitada y universidades con tradición. Esta dimensión tiene el menor peso porque, aunque deteriorada, Venezuela sigue estando mejor que la media latinoamericana en estas métricas.

---

#### `hdi` — Índice de Desarrollo Humano

| Campo | Detalle |
|-------|---------|
| **Fuente** | PNUD / UNDP — HDI |
| **Unidad** | Índice 0–1 |
| **Dirección** | **Positiva** |
| **Peso en D5** | 40% |
| **Peso en ICIV** | 4% |
| **Disponible desde** | 2000 (quinquenal hasta 2010, anual desde 2011) |

**¿Qué mide?**
Un índice compuesto que combina esperanza de vida al nacer, años promedio de escolaridad y Renta Nacional Bruta per cápita (en PPP). Captura el bienestar humano más allá del ingreso económico puro.

**Venezuela en HDI:**
- 2015: 0.768 — pico histórico (desarrollo humano alto)
- 2022: 0.699 — equivalente al nivel de 2005 (retroceso de 17 años)

---

#### `tasa_alfabetizacion_adulta_pct` — Tasa de Alfabetización Adulta

| Campo | Detalle |
|-------|---------|
| **Fuente** | WDI — indicador `SE.ADT.LITR.ZS` |
| **Unidad** | Porcentaje de adultos ≥ 15 años (%) |
| **Dirección** | **Positiva** |
| **Peso en D5** | 30% |
| **Peso en ICIV** | 3% |
| **Disponible desde** | 2001 (muy pocos puntos: encuestas esporádicas) |

**¿Qué mide?**
La proporción de adultos mayores de 15 años que pueden leer y escribir. Venezuela históricamente ha tenido tasas altas (95%+), lo que representa una ventaja para industrias que requieren fuerza laboral calificada.

> **Advertencia:** La cobertura de esta variable es extremadamente esporádica en el WDI para Venezuela (solo 5–7 observaciones en 2000–2024). El pipeline aplica `forward_fill` para mantener el último valor disponible.

---

#### `acceso_electricidad_pct` — Acceso a Electricidad

| Campo | Detalle |
|-------|---------|
| **Fuente** | WDI — indicador `EG.ELC.ACCS.ZS` |
| **Unidad** | Porcentaje de la población (%) |
| **Dirección** | **Positiva** |
| **Peso en D5** | 30% |
| **Peso en ICIV** | 3% |
| **Disponible desde** | 2000 |

**¿Qué mide?**
La proporción de la población con acceso a energía eléctrica en el hogar. Es un proxy de la cobertura de infraestructura eléctrica, aunque no captura la calidad (frecuencia de cortes). Venezuela históricamente tiene cobertura casi universal (99%+) pero con calidad deteriorada en los últimos años.

---

### D6 — Percepción Internacional (10% del ICIV)

**Justificación de la dimensión:** La imagen de un país en los medios internacionales es un indicador adelantado del sentimiento inversor. Los ciclos de cobertura negativa preceden a las decisiones de desinversión, y los períodos de cobertura más neutral o positiva coinciden con reapertura de diálogos. Esta dimensión también captura riesgo reputacional para empresas que evalúan la exposición pública de operar en Venezuela.

---

#### `guardian_tono_titulares` — Tono de Cobertura Mediática (VADER)

| Campo | Detalle |
|-------|---------|
| **Fuente** | The Guardian API + análisis VADER |
| **Unidad** | Compound score VADER promedio (−1 a +1) |
| **Dirección** | **Positiva** — score más alto = cobertura más favorable |
| **Peso en D6** | 60% |
| **Peso en ICIV** | 6% |
| **Disponible desde** | 2000 |

**¿Qué mide?**
El sentimiento promedio de los primeros 50 titulares de artículos del Guardian sobre Venezuela en cada año, calculado con el algoritmo VADER. Un score de -0.30 (Venezuela en 2018–2019) indica cobertura predominantemente negativa. Un score cercano a 0 indica cobertura neutral.

**Proceso de cálculo:**
1. Se consultan todos los artículos del Guardian que mencionan "Venezuela" por año
2. Se seleccionan los primeros 50 por relevancia (ordenados por `relevance`)
3. Se aplica `SentimentIntensityAnalyzer().polarity_scores(headline)['compound']` a cada titular
4. Se toma el promedio aritmético de los 50 compound scores
5. Se normaliza de [-1, +1] a [0, 100] para el ICIV

---

#### `guardian_articulos_venezuela` — Volumen de Cobertura Mediática

| Campo | Detalle |
|-------|---------|
| **Fuente** | The Guardian API |
| **Unidad** | Número de artículos publicados en el año |
| **Dirección** | **Negativa** — más artículos = más crisis = peor clima |
| **Peso en D6** | 40% |
| **Peso en ICIV** | 4% |
| **Disponible desde** | 2000 |

**¿Qué mide?**
El conteo anual de artículos del Guardian que mencionan "Venezuela". La hipótesis es que una alta cobertura mediática internacional correlaciona con crisis políticas o económicas (recordar cobertura masiva en 2019 durante el intento de gobierno de Guaidó, en 2018 durante la hiperinflación, etc.). Se trata de un **proxy inverso de estabilidad**.

---

## 3. Normalización de Variables

El ICIV requiere que todas las variables estén en la misma escala (0–100) para poder combinarlas. El método de normalización es **Min-Max Rescaling**, el estándar recomendado por el OCDE Handbook on Constructing Composite Indicators (2008).

### 3.1 Fórmula General

**Para variables de dirección positiva** (mayor valor = mejor clima):
```
V_norm = (V - V_min) / (V_max - V_min) × 100
```

**Para variables de dirección negativa** (mayor valor = peor clima, ej. inflación, desempleo):
```
V_norm = (V_max - V) / (V_max - V_min) × 100
```

Donde `V_min` y `V_max` son el mínimo y máximo histórico de la serie completa (2000–2026).

### 3.2 Consideraciones Especiales por Variable

#### Inflación — `inflacion_deflactor_pib_pct`

**Problema:** La hiperinflación venezolana de 2018 (225.690%) crea un outlier extremo que comprimiría todos los otros valores al 0% de la escala normalizada.

**Solución:** Transformación logarítmica antes de normalizar.
```
V_log = log₁₀(V + 1)        # +1 para manejar valores cercanos a 0
V_norm = (V_log_max - V_log) / (V_log_max - V_log_min) × 100
```
Esto preserva la ordenación (mayor inflación = peor) pero reduce el efecto distorsionador del valor extremo de 2018.

#### Tipo de Cambio — `tipo_cambio_oficial_lcu_usd`

**Problema:** Las tres reconversiones monetarias (2008, 2018, 2021) hacen la serie nominal incomparable a través del tiempo. Sin conversión, el valor de 2026 (38 Bs) parece menor que el de 2000 (0.70 BsF), cuando en realidad representa una devaluación de 10¹⁰.

**Solución:** **Transformación en dos pasos en `main.py`:**
1. Convertir cada era a BsF equivalente (×1 para 2000–2017, ×1.000 para BsS, ×10⁹ para Bs)
2. Aplicar log₁₀ para comprimir el rango de magnitudes (de 10⁻¹ a 10¹³ en BsF, a una escala 0–13 en log₁₀)
La variable se normaliza normalmente (dirección negativa) después de la transformación.

#### Reservas Internacionales — `reservas_internacionales_usd`

**Problema:** Sin datos oficiales del Banco Mundial desde 2018.

**Solución:** Se usan **datos estáticos validados** del Informe Económico BCV y la Consulta del Artículo IV del IMF para 2018–2026. Estos son estimaciones, no cifras oficiales — se documenta explícitamente esta distinción en el texto académico.

#### Tono VADER — `guardian_tono_titulares`

**Escala original:** −1 a +1 (VADER compound score)  
**Transformación:** `(V + 1) / 2 × 100` lleva el rango a [0, 100] directamente, eliminando la necesidad del Min-Max estándar.

#### HDI — `hdi`

**Escala original:** 0 a 1 (índice de desarrollo humano)  
**Transformación Min-Max:** se aplica normalmente. El rango histórico de Venezuela (0.61–0.77) se usa como referencia, no el rango teórico absoluto 0–1.

### 3.3 Tabla de Parámetros de Normalización

La siguiente tabla documenta los parámetros aprendidos por el `MinMaxNormalizer` sobre el período 2000–2026. Estos valores son la referencia para la interpretación de cada puntaje normalizado.

| Variable | Min histórico | Max histórico | Dirección | Transformación especial |
|----------|--------------|--------------|-----------|------------------------|
| `inflacion_deflactor_pib_pct` | ~3% (2001) | ~225.690% (2018) | Negativa | log₁₀(V+1) antes de normalizar |
| `pib_crecimiento_real_pct` | −30% (2020) | +18.3% (2004) | Positiva | — |
| `reservas_internacionales_usd` | ~7.7 B USD (2017) | ~29.9 B USD (2011) | Positiva | Solo 2000–2017 |
| `tipo_cambio_oficial_lcu_usd` | — | — | Negativa | Excluida post-2017 |
| `petroleo_crudo_produccion_tbpd` | 527 Mbpd (2020) | 2.893 Mbpd (2000) | Positiva | — |
| `gas_natural_produccion_bcf` | — | — | Positiva | — |
| `electricidad_generacion_bkwh` | — | — | Positiva | — |
| `cpi_score` | 10/100 (2023) | 20/100 (2011) | Positiva | Interpolación lineal gaps |
| `wgi_promedio_sc` | ~22 percentil (2024) | ~44.5 percentil (2000) | Positiva | — |
| `ief_overall_score` | 24.6 (2022) | ~59 (2000) | Positiva | Interpolación lineal gaps |
| `ied_neta_usd` | −299 M USD (2017) | 5.973 B USD (2012) | Positiva | — |
| `exportaciones_pct_pib` | — | — | Positiva | — |
| `desempleo_pct` | ~5% | ~12% | Negativa | — |
| `hdi` | 0.699 (2022) | 0.768 (2015) | Positiva | — |
| `tasa_alfabetizacion_adulta_pct` | ~93% | ~97% | Positiva | Forward fill |
| `acceso_electricidad_pct` | ~90% | ~100% | Positiva | — |
| `guardian_tono_titulares` | −1 | +1 | Positiva | (V+1)/2 × 100 |
| `guardian_articulos_venezuela` | — | — | Negativa | — |

> **Nota:** Los valores exactos de Min y Max se calculan automáticamente por `MinMaxNormalizer.fit()` durante la ejecución del pipeline. Los valores aquí son aproximados para orientación.

---

## 4. Cobertura Temporal por Variable

| Variable | 2000–2009 | 2010–2017 | 2018–2021 | 2022–2026 | Cobertura post-imputación |
|----------|-----------|-----------|-----------|-----------|--------------------------|
| `inflacion_deflactor_pib_pct` | ✅ | ✅ | ✅ (est.) | ✅ (est.) | **100%** |
| `pib_crecimiento_real_pct` | 🟡 desde 2002 | ✅ | ✅ | ✅ | **~92%** |
| `reservas_internacionales_usd` | ✅ | ✅ | 🟡 estáticos BCV/IMF | 🟡 estáticos IMF | **100%** |
| `tipo_cambio_oficial_lcu_usd` | ✅ | ✅ | 🟡 estáticos BCV | 🟡 estáticos BCV | **100%** |
| `wti_precio_usd` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `tasa_fed_funds_pct` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `petroleo_crudo_produccion_tbpd` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `gas_natural_produccion_bcf` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `electricidad_generacion_bkwh` | ✅ | ✅ | ✅ | 🟡 hasta 2023 | **~96%** |
| `luminosidad_nocturna_idx` | 🟡 interpol. | ✅ | ✅ | ✅ | **~92%** |
| `cpi_score` | ❌ desde 2010 | ✅ | 🟡 interpolado | 🟡 solo 2023 | **100%** (interpol.) |
| `wgi_promedio_sc` | ✅ | ✅ | ✅ | ✅ | **~96%** |
| `ief_overall_score` | 🟡 gaps 01-04,06-07 | ✅ | ✅ | ✅ | **100%** (interpol.) |
| `freedom_house_score` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `ofac_sanciones_count` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `ied_neta_usd` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `exportaciones_pct_pib` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `desempleo_pct` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `migrantes_vzla_millones` | 🟡 interpol. | 🟡 interpol. | ✅ | ✅ | **100%** (interpol.) |
| `hdi` | 🟡 quinquenal | ✅ anual | ✅ | 🟡 hasta 2022 | **100%** (interpol.) |
| `tasa_alfabetizacion_adulta_pct` | 🟡 esporádica | 🟡 esporádica | 🟡 estáticos | 🟡 estáticos | **100%** (estáticos) |
| `acceso_electricidad_pct` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `guardian_tono_titulares` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `guardian_articulos_venezuela` | ✅ | ✅ | ✅ | ✅ | **100%** |
| `google_trends_vzla` | 🟡 desde 2004 | ✅ | ✅ | ✅ | **~96%** |

**Leyenda:**
- ✅ Datos completos de fuente primaria
- 🟡 Datos parciales / imputados / interpolados / estáticos validados
- ❌ Sin datos (no aplica al modelo final — todos los gaps tienen tratamiento)

> **Cobertura global del dataset post-imputación:** **~98%** de las 729 celdas totales (27 variables × 27 años). Los ~2% restantes son años sin dato en la fuente primaria donde la interpolación no puede aplicarse (ej. electricidad 2024–2026 EIA aún no publicado).

---

## 5. Decisiones Metodológicas de Calidad de Datos

Esta sección documenta las decisiones explícitas tomadas para manejar la calidad de datos, siguiendo el principio de transparencia metodológica requerido en tesis de posgrado.

| Decisión | Variable afectada | Estrategia aplicada | Justificación |
|----------|-----------------|-------------------|---------------|
| Proxy de inflación | `inflacion_deflactor_pib_pct` | Usar deflactor IMF en lugar de IPC WDI | IPC cubre solo 2009–2016; deflactor tiene cobertura 2000–2026 |
| Hiperinflación como outlier extremo | `inflacion_deflactor_pib_pct` | Transformación log₁₀(V+1) antes de normalizar | Sin log, 2018 (225.690%) comprimiría todo el resto al 0% de la escala |
| Tipo de cambio con reconversiones | `tipo_cambio_oficial_lcu_usd` | Normalizar a BsF equivalente + log₁₀ | Las reconversiones hacen la serie nominal incomparable; la equivalencia BsF + log resuelve el problema |
| Reservas post-2018 | `reservas_internacionales_usd` | Datos estáticos BCV/IMF Article IV | La opacidad estadística se documenta; los estáticos son estimaciones verificadas |
| CPI con gaps | `cpi_score` | Interpolación lineal + forward fill | Los gaps son ≤ 3 años; la interpolación lineal es justificable académicamente |
| IEF con gaps | `ief_overall_score` | Interpolación lineal | Misma justificación que CPI |
| HDI quinquenal hasta 2010 | `hdi` | Interpolación lineal entre puntos | Práctica estándar en índices que usan HDI como variable |
| Alfabetización sin datos recientes | `tasa_alfabetizacion_adulta_pct` | Datos estáticos UNESCO-extrapolados | El cambio en alfabetización adulta es lento; los valores ~97% son plausibles para Venezuela 2018–2026 |
| Migración sin datos históricos pre-2015 | `migrantes_vzla_millones` | Interpolación lineal desde 0 | El éxodo masivo comenzó ~2014; antes de eso la cifra era mínima |
| 2025–2026 con datos parciales | Múltiples variables | Estimaciones IMF/EIA donde disponibles; estáticos donde no | Solo fuentes con datos preliminares oficiales o estimaciones publicadas |

---

*Documento generado como parte del proyecto de tesis ICIV — Indicador de Clima de Inversión Venezuela.*  
*Para actualizar este catálogo, editar directamente este archivo y el módulo `src/iciv/data/catalog.py`.*
