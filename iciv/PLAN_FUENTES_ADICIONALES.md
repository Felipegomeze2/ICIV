# Plan de Fuentes Adicionales — ICIV
## Sesión 12 (12 mayo 2026)

> **REGLAS INVIOLABLES:**
> 1. **NUNCA** fuentes gubernamentales venezolanas (BCV, INE, PDVSA, Conatel, ONAPRE)
> 2. **NUNCA** datos inventados, estimados manualmente o fallbacks artificiales
> 3. **SOLO** organismos multilaterales, instituciones académicas internacionales o NGOs reconocidos
> 4. **Preferencia** por fuentes de alta frecuencia (diaria, semanal, mensual, trimestral)

---

## 🎯 OBJETIVO

Subir la cobertura de **2025 (51.9% actual)** y **2026 (32.0% actual)** mediante la
integración sistemática de **fuentes internacionales de alta frecuencia** que publican
datos sobre Venezuela en tiempo real o con lag muy corto (<3 meses).

---

## 📋 PLAN DE INTEGRACIÓN POR TIER

### TIER 1 — Implementación inmediata (≤2 horas cada una)

#### 1.1 ✅ FRED extras (Federal Reserve Bank of St. Louis) — DIARIO/MENSUAL
**Estado:** Parcialmente integrado (WTI + Fed Funds) — agregar más series macroeconómicas
**Series a añadir:**
| Series ID | Variable | Frecuencia | Relevancia |
|-----------|----------|-----------|------------|
| `DCOILBRENTEU` | Brent oil price (USD/bbl) | Daily | Complemento WTI — precio de exportación Venezuela |
| `DTWEXBGS` | Trade Weighted USD Index (Broad) | Daily | Fortaleza del dólar — flujos de capital EM |
| `VIXCLS` | CBOE Volatility Index (VIX) | Daily | Aversión global al riesgo — sentimiento inversor |
| `DGS10` | 10-Year Treasury Constant Maturity | Daily | Tasa libre de riesgo USD |
| `BAMLEMCBPIOAS` | ICE BofA Emerging Markets Corp Bond Spread | Daily | Riesgo país emergentes |
| `DEXVZUS` | Venezuela / U.S. Foreign Exchange Rate | Daily (descontinuada 2018) | Histórico tipo de cambio |
| `EM EMBI Latam` | JPMorgan EMBI+ Latin America | Daily | Riesgo país EM via FRED |

**Implementación:** `scripts/fetch_fred.py` ya tiene infraestructura. Solo extender `SERIES` dict.
**Esfuerzo:** 30 minutos. **Impacto cobertura:** +3-5% en D1 macro.

#### 1.2 ✅ World Bank Pink Sheet — MENSUAL
**Fuente:** https://www.worldbank.org/en/research/commodity-markets
**Variables:** Precios mensuales de commodities (petróleo, oro, hierro, aluminio, café, cacao)
**Método:** Descarga Excel `CMOHistoricalDataMonthly.xlsx`
**Esfuerzo:** 1h (parser Excel + ETL).
**Impacto:** Petroleum benchmark mensual independiente.

#### 1.3 ✅ R4V — Plataforma Coordinación Refugiados Venezolanos (UN)
**Fuente:** https://www.r4v.info/en/refugeeandmigrants
**Variables:** Venezolanos en el exterior por país de destino, ACTUALIZACIÓN MENSUAL
**Método:** Scraping PowerBI dashboard (datos públicos)
**Esfuerzo:** 2h (PowerBI tiene URLs JSON expuestos)
**Impacto:** Granularidad mensual de migrantes 2025-2026 (vs anual UNHCR).

#### 1.4 ✅ OECD Latin America Economic Outlook — TRIMESTRAL
**Fuente:** https://www.oecd.org/dev/americas/latin-american-economic-outlook/
**Variables:** Datos macro regionales (Venezuela mencionado en comparativos)
**Método:** Descarga PDF + parsing.
**Esfuerzo:** 3h.
**Impacto:** Validación cruzada con LAC peer countries.

---

### TIER 2 — Implementación media (3-5 horas cada una)

#### 2.1 OPEC Monthly Oil Market Report (MOMR) — MENSUAL
**Fuente:** https://www.opec.org/opec_web/en/publications/202.htm
**Variables:** Producción petrolera Venezuela según "secondary sources" (independientes del gobierno)
**Método:** Descarga PDF + extracción tabla con `pdfplumber`
**Esfuerzo:** 4h.
**Impacto:** D2 nowcast mensual independiente.
**Ventaja vs EIA:** OPEC publica datos "secondary sources" que excluyen reportes oficiales del país, lo cual aumenta credibilidad.

#### 2.2 JODI Oil/Gas Database — MENSUAL
**Fuente:** https://www.jodidata.org/
**Variables:** Oil + gas production/imports/exports/stocks (auto-reporte con auditoría)
**Método:** Descarga CSV mensual + filtro VEN
**Esfuerzo:** 3h.
**Impacto:** Validación cruzada con EIA + OPEC. Para Venezuela JODI no es muy reportada pero los importadores sí.

#### 2.3 UN Comtrade — MENSUAL
**Fuente:** https://comtradeapi.un.org/
**Variables:** Comercio bilateral Venezuela ↔ resto del mundo, mensual
**Método:** API REST (requiere registro gratuito)
**Esfuerzo:** 4h (registrar + integrar paginación).
**Impacto:** Exportaciones reales mensuales (vs estimaciones anuales WDI).

#### 2.4 GDELT Project 2.0 — DIARIO
**Fuente:** https://www.gdeltproject.org/
**Variables:** Eventos políticos/económicos diarios sobre Venezuela en medios globales
**Método:** API HTTPS / BigQuery (BigQuery requiere proyecto GCP)
**Esfuerzo:** 5h (API REST DOC v2 + agregación temporal).
**Impacto:** Sentimiento + cobertura diaria. Reemplaza Google Trends.
**Bloqueo actual:** `api.gdeltproject.org` da timeout desde esta red — necesita probar desde otra IP/proxy.

#### 2.5 ITU DataHub — TRIMESTRAL
**Fuente:** https://datahub.itu.int/
**Variables:** Penetración internet, telefonía móvil
**Método:** API REST oficial (clave gratuita)
**Esfuerzo:** 3h.
**Impacto:** +D5 infraestructura digital trimestral.

---

### TIER 3 — Implementación avanzada (>6 horas o costo)

#### 3.1 ACLED API (Conflict Database)
**Fuente:** https://acleddata.com/
**Variables:** Eventos violencia política Venezuela, semanal
**Método:** API REST con API key gratuita registrada
**Esfuerzo:** 3h.
**Impacto:** +D3 institucional (semanal).
**Bloqueo:** No se ha registrado API key.

#### 3.2 EM-DAT (Disasters Database)
**Fuente:** https://www.emdat.be/
**Variables:** Desastres naturales VEN (impacto humano/económico)
**Método:** Descarga CSV / API
**Esfuerzo:** 3h.
**Impacto:** Nueva variable D5 (humanitarian crises).

#### 3.3 FAO GIEWS Country Briefs (mensuales)
**Fuente:** https://www.fao.org/giews/
**Variables:** Inseguridad alimentaria, producción agrícola
**Método:** Web scraping de Country Brief Venezuela mensual
**Esfuerzo:** 4h.
**Impacto:** +D5 seguridad alimentaria mensual.

#### 3.4 OEC — Observatory of Economic Complexity
**Fuente:** https://oec.world/
**Variables:** Exportaciones/importaciones VEN por producto y socio comercial
**Método:** API REST
**Esfuerzo:** 4h.
**Impacto:** Granularidad D4 comercial.

#### 3.5 WB Logistics Performance Index 2026
**Fuente:** https://lpi.worldbank.org/
**Variables:** Aduanas, infraestructura, envíos internacionales
**Método:** API + Excel manual
**Esfuerzo:** 2h.
**Impacto:** Nueva variable D4.

#### 3.6 PCWS — UN Peace Operations and Conflict Monitoring
**Fuente:** https://peacekeeping.un.org/
**Variables:** Tensiones regionales VEN-Colombia, presencia ONU
**Método:** Web scraping informes mensuales.
**Esfuerzo:** 5h.

#### 3.7 BIS Effective Exchange Rates
**Fuente:** https://www.bis.org/statistics/eer.htm
**Variables:** Real effective exchange rate (REER) Venezuela
**Método:** API REST oficial
**Esfuerzo:** 2h.
**Impacto:** Tipo de cambio real ponderado (no nominal BCV).

#### 3.8 IMF Direction of Trade Statistics (DOTS)
**Fuente:** https://data.imf.org/dots
**Variables:** Comercio bilateral mensual desde reporters (no Venezuela como reporter)
**Método:** API SDMX
**Esfuerzo:** 5h (SDMX es complejo).
**Impacto:** Mensual D4 comercial desde socios comerciales (reverso).

---

## 📅 PROYECCIÓN DE COBERTURA con plan completo

| Fase | Implementación | Cobertura 2025 | Cobertura 2026 |
|------|----------------|----------------|----------------|
| **Hoy** | Estado actual | 51.9% | 32.0% |
| **+1 día** | TIER 1 (FRED extras + Pink Sheet + R4V) | **60-65%** | **40-45%** |
| **+1 semana** | TIER 2 (OPEC + JODI + UN Comtrade + GDELT + ITU) | **70-75%** | **50-55%** |
| **+2 semanas** | TIER 3 (ACLED + EM-DAT + GIEWS + OEC + BIS) | **80%+** | **60%+** |
| **Pasivo sep-2026** | WGI 2025 + HDI 2024 publicación | **88%+** | **70%+** |
| **Pasivo dic-2026** | WDI 2025 publicación | **92%+** | **80%+** |

---

## 🚫 FUENTES EXPLÍCITAMENTE PROHIBIDAS

Estas fuentes están vetadas del proyecto por **falta de credibilidad internacional**
o **manipulación documentada**:

| Fuente | Por qué |
|--------|---------|
| BCV (Banco Central Venezuela) | Manipulación estadística documentada (Hanke 2018; Vera 2017) |
| INE Venezuela | No publica desde 2015 |
| Ministerio Petróleo / PDVSA | Cifras contradichas por OPEP/EIA |
| Conatel (telecom regulator) | Sin transparencia metodológica |
| ONAPRE (presupuesto) | Sin publicación pública |
| Diarios oficialistas VEN | No son fuentes primarias |
| Twitter/X de funcionarios | Sin verificabilidad metodológica |
| Trading Economics paywall | Datos detrás de paywall sin licencia |

---

## ⏭️ SIGUIENTES PASOS RECOMENDADOS (orden de implementación)

1. **HOY:** Implementar FRED extras (30 min, baja complejidad)
2. **Mañana:** WB Pink Sheet (1h, parser Excel)
3. **Esta semana:** R4V scraping mensual de migrantes (2h, alto impacto)
4. **Próxima semana:** OPEC MOMR + JODI (5h, validación cruzada D2)
5. **2 semanas:** ACLED API key registro + integración (4h)
6. **Mes:** GDELT (necesita IP no bloqueada)

---

*Documento creado: 12 mayo 2026 — Sesión 12 ICIV*
*Para actualizar: añadir nuevas fuentes evaluadas con su esfuerzo e impacto estimado.*
