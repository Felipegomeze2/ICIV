# Guía VIIRS — Luminosidad Nocturna Venezuela

**Por qué importa:** `luminosidad_nocturna_idx` tiene un 15% de peso en D2 (Sector Energético) y es el único indicador en el ICIV **completamente independiente de estadísticas oficiales venezolanas**. No depende del BCV, PDVSA ni INE. Es un proxy satelital de la actividad económica real — visible en el colapso de 2014–2019 y el apagón nacional de marzo 2019.

---

## ¿Qué es VIIRS?

**VIIRS** = Visible Infrared Imaging Radiometer Suite. Sensor a bordo del satélite Suomi NPP (NASA/NOAA). Mide la emisión de luz artificial nocturna desde el espacio — en Venezuela, principalmente ciudades, flares de gas y actividad industrial.

**Producto que necesitamos:** VNL (VIIRS Nighttime Lights) Annual Composite v2  
**Organización:** Earth Observation Group (EOG) — Colorado School of Mines  
**Período disponible:** 2012–2024 (anual)  
**Para 2000–2011:** DMSP-OLS (sensor anterior, NASA NCEI) — resolución más baja pero aceptable

---

## Por qué Postman da Timeout (y cómo resolverlo)

NASA Earthdata **no usa Basic Auth directa** — usa **OAuth2 con redirect**. El flujo es:
1. Postman envía GET a eogdata.mines.edu
2. El servidor responde 302 → redirect a `urs.earthdata.nasa.gov/oauth/authorize`
3. El usuario autenticaen URS
4. URS redirige de vuelta a eogdata.mines.edu con un token
5. Se genera una cookie de sesión

Postman no sigue ese redirect chain con las credenciales automáticamente → timeout.

**La solución no es Basic Auth en Postman. Hay 3 caminos alternativos.**

---

## Paso a Paso para Obtener los Datos

### OPCIÓN 1 — Descarga Manual (más rápida, sin código)

#### Paso 1: Crear cuenta en EOG/NASA Earthdata

1. Ve a: **https://eogdata.mines.edu/products/vnl/**
2. Haz clic en cualquier archivo → te redirige a login de NASA Earthdata
3. Si no tienes cuenta: **https://urs.earthdata.nasa.gov/users/new**
   - Es gratis, para uso académico/investigación
   - Rellena: nombre, email, institución (pon tu universidad)
   - Acepta los términos de uso
   - Confirma el email
4. Vuelve a **eogdata.mines.edu** y loguéate con las credenciales NASA Earthdata

#### Paso 2: Descargar las estadísticas anuales para Venezuela (archivo pequeño)

Una vez logueado, el endpoint que necesitas es:

```
https://eogdata.mines.edu/nighttime_light/annual/v22/
```

Dentro verás carpetas por año: `2012/`, `2013/`, ... `2024/`

Lo que necesitas **no son los rasters completos** (son enormes, >1GB por año). Necesitas los archivos de **estadísticas por país**, que son pequeños CSVs/TXTs:

Para cada año ve a:
```
/annual/v22/YYYY/0_global_statistics/
```

Busca el archivo:
```
VNL_v22_npp_YYYY_global_vcmslcfg_c202304011200.average_masked.dat.gz
```
O el equivalente con sufijo `_country_stats.csv.gz`

**Para Venezuela (VEN)**, solo necesitas extraer la fila correspondiente.

#### Paso 3: Formato del archivo

El CSV de estadísticas tiene estas columnas:
```
country_iso3  | country_name | mean_masked | sum_masked | count_pixels | ...
VEN           | Venezuela    | 2.34        | 18200.5    | 7782         | ...
```

El valor que usamos es **`mean_masked`** = promedio de radianza nocturna en la zona terrestre de Venezuela, con nubes y temporadas de quema enmascaradas.

#### Paso 4: Preparar el CSV para el pipeline

El pipeline espera `data/raw/viirs.csv` con formato:
```csv
año,indicador,valor,pais,fuente
2012,luminosidad_nocturna_idx,2.34,Venezuela,NOAA EOG VNL v22 annual composite
2013,luminosidad_nocturna_idx,2.21,Venezuela,NOAA EOG VNL v22 annual composite
...
```

Donde `valor` = `mean_masked` de la estadística del año.

---

### OPCIÓN 2 — Descarga Semi-Automática (Python + credenciales)

Una vez que tengas la cuenta NASA Earthdata, puedes automatizar la descarga con el script siguiente (ya está en el proyecto pero necesita credenciales).

#### Paso 1: Guardar credenciales

Crea el archivo `~/.netrc` (o `%USERPROFILE%\_netrc` en Windows):
```
machine urs.earthdata.nasa.gov
login TU_USUARIO_NASA
password TU_PASSWORD_NASA
```

En Windows específicamente:
```
C:\Users\pipeg\_netrc
```
Contenido:
```
machine urs.earthdata.nasa.gov
login TU_USUARIO
password TU_PASSWORD
```

#### Paso 2: Instalar dependencias

```bash
pip install requests netrc4 rasterio
```

#### Paso 3: Script de descarga automática

El endpoint para estadísticas anuales (no el raster completo):

```python
import requests
from pathlib import Path

# Autenticación con netrc (archivo _netrc en Windows)
session = requests.Session()

BASE = "https://eogdata.mines.edu/nighttime_light/annual/v22"
YEARS = range(2012, 2025)

rows = []
for year in YEARS:
    url = f"{BASE}/{year}/0_global_statistics/"
    # Listar archivos disponibles
    r = session.get(url, timeout=30)
    # Buscar el archivo country stats
    # Formato: VNL_v22_npp_{year}_global_vcmslcfg_*_country_stats.csv.gz
    ...
```

**NOTA:** Para el scraping del índice de directorio, se necesita netrc configurado correctamente. EOG usa el sistema de autenticación de NASA Earthdata.

---

### OPCIÓN 3 — Google Earth Engine (más completa, requiere verificación)

Google Earth Engine (GEE) tiene los datasets VIIRS y DMSP integrados y accesibles vía API Python (`earthengine-api`). Ventaja: cubre también 2000–2011 con DMSP.

1. Crear cuenta GEE: **https://earthengine.google.com/signup/**
   - Requiere cuenta Google
   - Para uso académico/investigación: aprobación automática o en 24–48h
2. Instalar: `pip install earthengine-api`
3. Autenticar: `earthengine authenticate`

El dataset de VIIRS en GEE:
```python
import ee
ee.Initialize()

# VIIRS Nighttime Day/Night Band (2012-presente)
viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")

# Venezuela boundary
vzla = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filter(
    ee.Filter.eq('country_na', 'Venezuela')
)

# Calcular media anual para Venezuela
for year in range(2012, 2025):
    img = viirs.filterDate(f'{year}-01-01', f'{year}-12-31').mean()
    mean = img.select('avg_rad').reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=vzla.geometry(),
        scale=500,
        maxPixels=1e9
    ).getInfo()
    print(f"{year}: {mean}")
```

---

## Prueba en Postman — NOAA EOG

Para probar el acceso antes de escribir código, usa Postman así:

### Request 1: Verificar acceso al índice del directorio

```
GET https://eogdata.mines.edu/nighttime_light/annual/v22/2023/0_global_statistics/
Authorization: Basic (con usuario:password de NASA Earthdata en Base64)
```

Si devuelve HTML con listado de archivos → credenciales correctas.
Si devuelve 401 → credenciales incorrectas o sesión no iniciada.

### Request 2: Descargar archivo de estadísticas

```
GET https://eogdata.mines.edu/nighttime_light/annual/v22/2023/0_global_statistics/VNL_v22_npp_2023_global_vcmslcfg_c202404021200.average_masked.dat.gz
Authorization: Basic TU_BASE64_CREDS
```

**Configurar Basic Auth en Postman:**
- Tab "Authorization" → Type: "Basic Auth"
- Username: tu usuario NASA Earthdata
- Password: tu password NASA Earthdata

---

## Valores de Referencia para Venezuela

Una vez que obtengas los datos, estos son los valores históricos esperados (basados en literatura académica y datos NOAA EOG publicados en papers):

| Año | Evento | Valor esperado (relativo) |
|-----|--------|--------------------------|
| 2012–2013 | Boom: alta actividad | Máximo histórico VIIRS |
| 2016–2018 | Crisis económica | Caída pronunciada |
| 2019 (mar) | Apagón Nacional 7–9 marzo | Mínimo mensual absoluto |
| 2019 (anual) | Año del apagón | Mínimo histórico anual |
| 2020–2021 | Pandemia + dolarización informal | Ligera recuperación vs 2019 |
| 2022–2024 | Recuperación parcial | Sube pero no vuelve a 2012 |

El apagón de marzo 2019 es el evento más visible en datos satelitales — la imagen nocturna de Venezuela ese mes muestra oscuridad casi completa. **Este es el dato que hace único al ICIV.**

---

## Qué Hacer Cuando Tengas los Datos

1. Descarga los CSVs de estadísticas para todos los años disponibles (2012–2024)
2. Para 2000–2011 usa DMSP-OLS (ver instrucciones DMSP abajo)
3. Construye el CSV en este formato:

```csv
año,indicador,valor,pais,fuente
2000,luminosidad_nocturna_idx,X,Venezuela,NOAA DMSP-OLS v4 global_F15
...
2012,luminosidad_nocturna_idx,X,Venezuela,NOAA EOG VNL v22 annual composite
...
2024,luminosidad_nocturna_idx,X,Venezuela,NOAA EOG VNL v22 annual composite
```

4. Guarda en `iciv/data/raw/viirs.csv`
5. Corre `python main.py` → el pipeline lo detecta automáticamente

---

## DMSP-OLS para 2000–2011

**Dataset:** DMSP-OLS Nighttime Lights (versión 4, NOAA NCEI)  
**URL:** https://www.ngdc.noaa.gov/eog/dmsp/downloadV4composites.html  
**Acceso:** Libre sin autenticación, descarga directa

Los archivos son rasters .tif anuales. Para extraer el valor de Venezuela:
- Descarga el composite anual F15_YYYY_v4b_cf_cvg.avg_vis.tif.gz
- Usa rasterio + shapefile de Venezuela para calcular la media
- O descarga los country-level statistics si los hay disponibles

**NOTA:** Los valores DMSP y VIIRS no son directamente comparables en escala absoluta. Se necesita calibración intercalibración. El método más simple: normalizar ambas series por separado (Min-Max) y luego unirlas como índice 0–100.

---

## Resumen de Opciones

| Opción | Dificultad | Tiempo | Auth necesaria |
|--------|-----------|--------|---------------|
| Descarga manual EOG (CSV stats) | Baja | 30 min | Cuenta NASA Earthdata |
| Script Python + netrc | Media | 2h | Cuenta NASA Earthdata |
| Google Earth Engine | Alta | 4h | Cuenta GEE (gratis académica) |
| Postman para verificar acceso | Muy baja | 10 min | Cuenta NASA Earthdata |

**Recomendación:** Primero crea la cuenta NASA Earthdata → prueba en Postman con Basic Auth → si funciona, descarga los CSVs de estadísticas manualmente año a año (son archivos pequeños ~100KB). Es la forma más rápida.
