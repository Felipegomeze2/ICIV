# Validación externa del ICIV (no circular)

**Fecha:** 2026-06-10 · **Script:** `iciv/scripts/external_validation.py` · **Outputs:** `iciv/data/processed/external_validation.csv`, `external_validation_summary.csv`

## Problema que resuelve

La validación original del proyecto correlacionaba el ICIV con la IED. Aunque la IED
fue excluida del score (es un outcome externo), la correlación resultó débil y no
significativa (r=0.37, p=0.067), insuficiente como evidencia de validez. Las dos
señales externas más informativas disponibles — migración UNHCR y luminosidad
nocturna satelital — **forman parte del score** (D4 y D2), por lo que correlacionar
el ICIV completo contra ellas sería circular.

## Diseño: leave-one-out

Para cada variable de validación se recalcula el ICIV completo **excluyendo esa
variable**. El `ICIVAggregator` redistribuye automáticamente su peso entre las demás
variables de su dimensión, de modo que el score resultante no contiene información
directa de la serie contra la que se valida. La correlación se mide entre el ICIV
leave-one-out y la serie cruda (no normalizada) de la variable excluida.

## Hipótesis económicas (falsables, formuladas ex ante)

1. **Migración:** peor clima de inversión → más emigración. Correlación esperada: **negativa**.
2. **Luminosidad nocturna:** mejor clima → más actividad económica observable desde
   satélite (Henderson, Storeygard & Weil 2012, *AER*). Correlación esperada: **positiva**.

## Resultados

| Test | Periodo | n | Pearson r | p | Spearman ρ | p | Veredicto |
|---|---|---|---|---|---|---|---|
| ICIV (sin migrantes) vs stock migrantes UNHCR | 2000–2025 | 26 | **−0.883** | <0.001 | −0.848 | <0.001 | ✅ Confirmada |
| ICIV (sin luminosidad) vs luminosidad nocturna, era VIIRS | 2014–2024 | 11 | **+0.826** | 0.002 | +0.782 | 0.004 | ✅ Confirmada |
| ICIV (sin luminosidad) vs luminosidad, periodo completo | 2000–2024 | 25 | −0.525 | 0.007 | −0.717 | <0.001 | ⚠️ No interpretable* |
| ICIV completo vs IED neta (outcome externo) | 2000–2024 | 25 | +0.372 | 0.067 | +0.322 | 0.116 | Signo correcto, no significativa |

\* **Por qué el periodo completo de luminosidad no es interpretable:** la serie
armonizada de Li et al. (2020) combina dos sensores — DMSP-OLS hasta 2013 y VIIRS
desde 2014 — con un escalón de calibración visible en la transición (15.2 → 22.2
entre 2013 y 2014). Además, el tramo 2000–2013 refleja la expansión eléctrica y
urbana del boom petrolero, que elevó la luminosidad mientras el ICIV ya descendía
por deterioro institucional. Restringir el test a la era VIIRS (2014–2024, sensor
homogéneo) elimina el artefacto y cubre el periodo de colapso económico: la
luminosidad cae 32% (22.2 → 15.1) en paralelo con el índice. Reportamos ambos
resultados por transparencia.

## Interpretación

- El ICIV **sin saber nada de migración** explica el 78% de la varianza (r²) del
  stock de emigrantes venezolanos registrado por UNHCR. Cuando el índice cae, la
  gente se va. Es la validación externa más fuerte del proyecto.
- El ICIV **sin saber nada de luminosidad** sigue el apagón económico observable
  desde el espacio durante la era VIIRS (r=+0.83). Dos fuentes de naturaleza
  completamente distinta (estadísticas internacionales vs. radiometría satelital)
  cuentan la misma historia.
- La IED se mantiene como referencia exploratoria honesta: signo correcto pero no
  significativa, consistente con que la IED en Venezuela está dominada por shocks
  idiosincráticos (sanciones, expropiaciones, contabilidad opaca de PDVSA).

## Cómo defenderlo en 30 segundos

> "No validamos el índice contra sus propios componentes. Recalculamos el ICIV
> excluyendo la variable de validación y correlacionamos contra la serie cruda.
> El índice sin migración predice la emigración (r=−0.88); el índice sin
> luminosidad sigue la luz nocturna del país medida por satélite (r=+0.83).
> Dos fenómenos observables, independientes y no manipulables por el gobierno
> venezolano, confirman lo que el índice mide."

## Reproducir

```bash
cd iciv
python scripts/external_validation.py
```
