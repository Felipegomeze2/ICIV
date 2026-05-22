# Bitácora 02 — Decisiones de Normalización y Transformaciones
**Fecha:** Abril 2026  
**Etapa:** Modelado — Normalización Min-Max y transformaciones previas  
**Archivos afectados:** `main.py`, `scripts/fetch_wdi.py`, `src/iciv/data/catalog.py`

---

## 1. Problema: Tipo de Cambio con Tres Reconversiones

### Contexto
Venezuela ha sufrido tres reconversiones monetarias que hacen la serie del tipo de cambio nominal completamente incomparable entre períodos:

| Era | Denominación | Equivalencia en BsF | Período |
|-----|-------------|---------------------|---------|
| VEB | Bolívar (original) | ÷1000 → BsF | Antes de 2008 |
| BsF | Bolívar Fuerte | ×1 | 2008–2018 |
| BsS | Bolívar Soberano | ×1.000 | 2018–2021 |
| Bs  | Bolívar Digital | ×10⁹ | 2022+ |

El WDI de Banco Mundial retroconvierte VEB a BsF (divide entre 1.000) para el período 2000–2007, lo que permite que 2000–2017 estén comparables en BsF. Pero los períodos post-2018 siguen en sus denominaciones originales.

### Síntoma del error
Sin transformación, el normalizador Min-Max ve que 2026 tiene tipo_cambio = 38 Bs y 2000 tiene tipo_cambio = 0.70 BsF. Como 38 > 0.70, el normalizador interpreta 2026 como el año de mayor devaluación... ¡pero en la escala incorrecta! El resultado era `score = 100.0` para 2026, cuando debería ser `score ≈ 0`.

### Solución implementada
En `main.py`, antes de llamar al pipeline, se aplica la equivalencia monetaria y la transformación log₁₀:

```python
import numpy as np

if "tipo_cambio_oficial_lcu_usd" in master.columns:
    _tc = master["tipo_cambio_oficial_lcu_usd"].copy()
    _mask_bss = (master["año"] >= 2018) & (master["año"] <= 2021)
    _mask_bs  = master["año"] >= 2022
    _tc[_mask_bss] = _tc[_mask_bss] * 1_000          # BsS → BsF
    _tc[_mask_bs]  = _tc[_mask_bs]  * 1_000_000_000   # Bs  → BsF
    master["tipo_cambio_oficial_lcu_usd"] = np.log10(_tc.clip(lower=1e-9))
```

**¿Por qué log₁₀?** El rango en BsF va de ~0.70 (2000) a ~10¹³ (2026 estimado). Sin log, el normalizador Min-Max comprimiría todos los valores pre-2018 al 0% de la escala. El log₁₀ convierte ese rango de 13 órdenes de magnitud a una escala lineal de 0 a 13, que el Min-Max puede manejar correctamente.

**Resultado:** Score 2026 = 0.0 (máxima devaluación = peor clima). Score ~2000 = ~50. Correcto.

---

## 2. Problema: Datos Estáticos para Gaps Críticos

### Reservas Internacionales (post-2018)
Venezuela dejó de reportar reservas al Banco Mundial en 2018. El WDI retorna NaN para 2018–2026. **Decisión:** Usar datos del Informe Económico del BCV y estimaciones del IMF Article IV Consultation.

Implementado en `scripts/fetch_wdi.py`:
```python
_STATIC_RESERVAS = {  # USD
    2018: 8_840_000_000, 2019: 6_470_000_000, 2020: 5_980_000_000,
    2021: 9_020_000_000, 2022: 9_480_000_000, 2023: 9_020_000_000,
    2024: 8_800_000_000, 2025: 8_600_000_000, 2026: 8_600_000_000,
}
```
Estos valores son estimaciones — no cifras oficiales verificadas. Se documenta esta distinción en el texto académico.

### Tipo de Cambio Oficial (valores nominales por era)
Los datos estáticos en `_STATIC_TIPO_CAMBIO` se almacenan en las denominaciones originales de cada era (BsF, BsS, Bs), exactamente como los retornaría el WDI o el BCV. La conversión a BsF equivalente se hace en `main.py`, no en el script de fetch. Esto mantiene la consistencia con lo que publicaría cualquier actualización futura del WDI.

### Tasa de Alfabetización Adulta
El WDI tiene solo ~5–7 observaciones para Venezuela en 2000–2024. El pipeline usa `forward_fill` + datos estáticos UNESCO-extrapolados para completar la serie. El cambio en alfabetización adulta es estructuralmente lento (< 0.5% por año), lo que hace esta imputación metodológicamente aceptable.

---

## 3. Transformación log₁₀ para Inflación

El deflactor del PIB para Venezuela incluye el valor de 2018: **225.690%**. Sin transformación, este outlier extremo haría que todos los otros años parezcan con inflación cero en la escala normalizada.

**Transformación aplicada en el normalizador:**
```
V_log = log₁₀(V + 1)
V_norm = (V_log_max - V_log) / (V_log_max - V_log_min) × 100
```

La dirección es negativa (más inflación = peor), por eso se invierte en el normalizador. El `+1` maneja valores cercanos a cero (años con deflación leve o inflación ~1%).

---

## 4. Impacto en el Modelo Final

| Variable | Antes de corrección | Después | Correctitud |
|----------|--------------------|---------|----|
| `tipo_cambio_oficial_lcu_usd` score 2026 | 100.0 (incorrecto — interpretaba como mínimo histórico) | 0.0 | ✅ |
| `reservas_internacionales_usd` cobertura | ~67% (NaN post-2018) | ~100% (estáticos) | ✅ |
| `inflacion_deflactor_pib_pct` score 2000 | ~0% (aplastado por 2018) | ~80% (correctamente mejor que 2018) | ✅ |

---

*Ver también: `CATALOGO_DE_DATOS.md` Sección 3.2 (transformaciones especiales) y Sección 5 (decisiones metodológicas).*
