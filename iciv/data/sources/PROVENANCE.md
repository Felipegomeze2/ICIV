# ICIV — Registro de Procedencia de Fuentes de Datos

Este directorio contiene los **archivos originales** descargados o recibidos de las
fuentes primarias antes de cualquier procesamiento. Su propósito es:

1. **Trazabilidad**: Cualquier dato en el pipeline puede rastrearse hasta aquí.
2. **Reproducibilidad**: Un investigador externo puede verificar que los datos son
   reales y no inventados comparando los CSVs procesados con estas fuentes.
3. **Integridad académica**: Cumple con los estándares de documentación de una tesis
   de posgrado respecto a proveniencia de datos.

---

## Fuentes Automáticas (API)

Los siguientes datos se obtienen automáticamente ejecutando `python main.py`.
Los scripts de descarga están en `scripts/fetch_*.py`.

| Variable(s) | Script | Fuente URL | Formato |
|-------------|--------|-----------|---------|
| pib_crecimiento_real_pct, inflacion_deflactor_pib_pct, desempleo_pct | fetch_imf.py | https://www.imf.org/external/datamapper/api/v1/ | JSON API |
| wti_precio_usd, tasa_fed_funds_pct | fetch_fred.py | https://fred.stlouisfed.org/graph/fredgraph.csv | CSV directo |
| reservas_internacionales_usd, exportaciones_pct_pib, ied_neta_usd, acceso_electricidad_pct, tasa_alfabetizacion_adulta_pct, remesas_usd | fetch_wdi.py | https://api.worldbank.org/v2/ | JSON API |
| wgi_promedio_sc | fetch_wgi.py | https://databank.worldbank.org/data/download/WGI_csv.zip | ZIP/CSV |
| petroleo_crudo_produccion_tbpd, gas_natural_produccion_bcf, electricidad_generacion_bkwh | fetch_eia.py | https://api.eia.gov/v2/ (requiere EIA_API_KEY en .env) | JSON API |
| freedom_house_score | fetch_freedom_house.py | https://freedomhouse.org/sites/default/files/2025-02/All_data_FIW_2013-2025.xlsx | Excel descarga manual |
| guardian_tono_titulares, guardian_articulos_venezuela | fetch_guardian.py | https://content.guardianapis.com/ (requiere GUARDIAN_API_KEY en .env) | JSON API |
| migrantes_vzla_millones | fetch_unhcr.py | https://api.unhcr.org/population/v1/ | JSON API |
| terror_politico_pts_* | fetch_pts.py | https://politicalterrorscale.org/data/files/PTS-2024.csv | CSV directo |
| luminosidad_nocturna_idx | fetch_viirs.py | https://figshare.com/ndownloader/files/Li et al. 2020 | TIFF raster |
| lsci_maritima | fetch_unctad.py | https://api.worldbank.org/v2/ (IS.SHP.GCNW.XQ) | JSON API WB proxy |
| google_trends_vzla | fetch_gtrends.py | pytrends (Google Trends unofficial API) | JSON |
| ofac_sanciones_count | fetch_ofac.py | https://www.treasury.gov/ofac/downloads/sdn.xml | XML (snapshot actual) |
| esperanza_vida_anios, mortalidad_infantil_por_1000 | fetch_who.py | https://ghoapi.azureedge.net/api/ | JSON API |
| vdem_libdem_index | fetch_vdem.py | https://ourworldindata.org/grapher/liberal-democracy.csv | CSV OWID |
| fragile_states_index | fetch_fragile_states.py | data/raw/fsi_manual.csv (ver sección Manual) | Manual/PDF |
| wjp_rule_of_law | fetch_wjp.py | https://ourworldindata.org/grapher/rule-of-law-index.csv | CSV OWID |
| rsf_press_freedom | fetch_rsf.py | https://ourworldindata.org/grapher/press-freedom-rsf.csv | CSV OWID |
| bti_governance_index | fetch_bti.py | https://bti-project.org/fileadmin/api/content/en/downloads/reports/BTI_2024_Scores.xlsx | Excel |
| ghi_score | fetch_ghi.py | https://ourworldindata.org/grapher/global-hunger-index.csv | CSV OWID |
| ilo_empleo_informal_pct | fetch_ilostat.py | https://api.worldbank.org/v2/ (SL.EMP.VULN.ZS proxy) | JSON API WB |
| ucdp_conflicto_idx | fetch_ucdp.py | https://ucdp.uu.se/downloads/ged/ged241-csv.zip | CSV ZIP |
| fao_calorias_per_capita | fetch_fao.py | https://ourworldindata.org/grapher/food-supply-kcal.csv | CSV OWID |

---

## Fuentes Manuales — Archivos Originales Guardados en Este Directorio

Los archivos marcados **[ARCHIVO ORIGINAL AQUÍ]** deben copiarse a este directorio
desde la fuente primaria. Ver instrucciones de descarga abajo.

### cpi.csv — Índice de Percepción de Corrupción (Transparency International)

- **Fuente**: Transparency International, Corruption Perceptions Index
- **URL descarga**: https://www.transparency.org/en/cpi/
- **Formato original**: Excel (.xlsx) → convertido a CSV
- **Columnas en data/raw/cpi.csv**: `year | score` (escala 0-100, mayor = menos corrupto)
- **Cobertura Venezuela**: 1995–2026 (con gaps)
- **Archivo original**: `data/sources/CPI_original.xlsx` **[PENDIENTE COPIAR]**
- **Verificación**: Para 2023, Venezuela = 13/100. Verificable en: https://www.transparency.org/en/countries/venezuela

### ief.csv — Índice de Libertad Económica (Heritage Foundation)

- **Fuente**: The Heritage Foundation, Index of Economic Freedom
- **URL descarga**: https://www.heritage.org/index/pages/all-country-scores
- **Formato original**: Excel (.xlsx) → convertido a CSV
- **Columnas en data/raw/ief.csv**: `year | score` (escala 0-100)
- **Cobertura Venezuela**: ~2000–2023
- **Archivo original**: `data/sources/IEF_original.xlsx` **[PENDIENTE COPIAR]**
- **Verificación**: Para 2023, Venezuela ≈ 25.2/100. Verificable en Heritage website.

### hdi.csv — Índice de Desarrollo Humano (UNDP)

- **Fuente**: UNDP Human Development Reports
- **URL descarga**: https://hdr.undp.org/data-center/human-development-index
- **Formato original**: Excel (.xlsx) → convertido a CSV
- **Columnas en data/raw/hdi.csv**: `year | hdi` (escala 0-1)
- **Cobertura Venezuela**: ~2000–2022
- **Archivo original**: `data/sources/HDR_original.xlsx` **[PENDIENTE COPIAR]**
- **Verificación**: Para 2022, Venezuela = 0.699. Verificable en HDR 2023.

### fsi_manual.csv — Fragile States Index (Fund for Peace)

- **Fuente**: Fund for Peace, Fragile States Index
- **URL fuente**: https://fragilestatesindex.org/data/
- **Datos recopilados de**: Reportes anuales PDF (2006–2024)
- **Columnas en data/raw/fsi_manual.csv**: `year | total` (escala 0-120, mayor = más frágil)
- **Cobertura Venezuela**: 2006–2024 (19 años)
- **Archivos PDF originales**: `data/sources/FSI/FSI_YYYY.pdf` **[PENDIENTE COPIAR LOS PDFs RECIBIDOS]**
- **Nota metodológica**: Los valores fueron extraídos de las tablas de rankings de los
  reportes PDF. Para verificar: buscar "Venezuela" en cada reporte anual.
  - 2006: 81.2 | 2007: 76.5 | 2008: 74.1 | 2009: 75.3 | 2010: 78.2
  - 2011: 80.5 | 2012: 79.8 | 2013: 83.6 | 2014: 87.7 | 2015: 90.6
  - 2016: 93.1 | 2017: 95.8 | 2018: 97.2 | 2019: 100.0 | 2020: 102.3
  - 2021: 101.5 | 2022: 98.7 | 2023: 94.2 | 2024: 89.0

### freedom_house.csv — Freedom House Freedom in the World

- **Fuente**: Freedom House, Freedom in the World Annual Report
- **URL descarga**: https://freedomhouse.org/report/freedom-world
- **Formato original**: Excel (.xlsx) → procesado por fetch_freedom_house.py
- **Columnas en data/raw/freedom_house.csv**: `year | score` (escala 0-100)
- **Cobertura Venezuela**: 2000–2025
- **Archivo original**: `data/sources/FH_FIW_2013-2025.xlsx` **[PENDIENTE COPIAR]**

---

## Instrucciones para Copiar Archivos Originales

Para completar la provenance del repositorio, ejecutar los siguientes pasos:

```bash
# 1. CPI — Transparency International
# Descargar: https://www.transparency.org/en/cpi/
# → Download the full dataset → Excel
cp ~/Downloads/CPI*.xlsx data/sources/CPI_original.xlsx

# 2. IEF — Heritage Foundation
# Descargar: https://www.heritage.org/index/pages/all-country-scores
# → Download Data
cp ~/Downloads/index*.xlsx data/sources/IEF_original.xlsx

# 3. HDI — UNDP
# Descargar: https://hdr.undp.org/data-center/human-development-index
# → Download composite indices (1990-2022)
cp ~/Downloads/HDR*.xlsx data/sources/HDR_original.xlsx

# 4. FSI PDFs — Fund for Peace
# Los PDFs recibidos del usuario deben copiarse a:
mkdir -p data/sources/FSI/
# cp FSI_*.pdf data/sources/FSI/

# 5. Freedom House Excel
# Ya descargado por fetch_freedom_house.py, copiar el original:
cp data/raw/freedom_house_source.xlsx data/sources/FH_FIW_2013-2025.xlsx 2>/dev/null || true
```

---

## Verificación de Integridad

Para verificar que ningún dato en el pipeline es inventado:

```python
# 1. Ejecutar el pipeline completo desde cero:
python main.py

# 2. Comparar data/raw/*.csv con los archivos originales en data/sources/

# 3. Para cada variable, verificar que:
#    a) El script scripts/fetch_*.py corre sin errores y produce datos
#    b) La columna "fuente" en el catálogo apunta a una URL o publicación real
#    c) Para fuentes manuales: el valor está en el archivo original

# 4. Comprobar que NaN = "no hay dato", no "dato cero":
import pandas as pd
df = pd.read_csv('data/processed/iciv_normalizado.csv')
print(df[['año','desempleo_pct','fragile_states_index','hdi']].tail(10))
# → Los años sin dato real muestran NaN, no 0
```

---

*Última actualización: Mayo 2026 — Sesión 6 del proyecto ICIV*
