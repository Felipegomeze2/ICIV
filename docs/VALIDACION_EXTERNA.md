# Validación externa del ICIV (no circular)

**Fecha:** 2026-07-21 (recalculada tras la auditoría de fuentes institucionales WJP/FH/HDI/PTS) · **Script:** `iciv/scripts/external_validation.py` · **Outputs:** `iciv/data/processed/external_validation.csv`, `external_validation_summary.csv`

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

Regenerados el 2026-08-11, después de la purga que dejó el core en 21 variables.
Las cifras cambian respecto a ediciones anteriores porque cambió el modelo.

### A. Leave-one-out contra fenómenos observables

| Test | Periodo | n | Pearson r | p | Spearman ρ | p | Veredicto |
|---|---|---|---|---|---|---|---|
| ICIV (sin migrantes) vs stock migrantes UNHCR | 2000–2025 | 26 | **−0.853** | <0.001 | −0.588 | 0.002 | ✅ Confirmada |
| ICIV (sin luminosidad) vs luminosidad nocturna, era VIIRS | 2014–2024 | 11 | **+0.806** | 0.003 | +0.673 | 0.023 | ✅ Confirmada |
| ICIV (sin luminosidad) vs luminosidad, periodo completo | 2000–2024 | 25 | −0.419 | 0.037 | −0.555 | 0.004 | ⚠️ No interpretable* |
| ICIV completo vs IED neta (outcome externo) | 2000–2024 | 25 | **+0.419** | 0.037 | +0.419 | 0.037 | ✅ Confirmada |

La IED **pasó a ser significativa** tras la purga (antes r=+0.390, p=0.054). No
se tocó nada de la IED: al retirar variables sin fuente viva, el índice quedó
mejor alineado con el flujo de inversión observado. Sigue siendo evidencia
exploratoria por el tamaño muestral, pero ya no es un resultado nulo.

Nota sobre la luminosidad: desde el 2026-08-11 la variable del score se alimenta
de **NASA Black Marble**, mientras el validador sigue siendo la serie de
**Li et al.** Son productos distintos, con sensores y escalas distintas, así que
el test es ahora más limpio que antes: ya no comparte ni siquiera el mismo
procesamiento.

### B. Validez convergente contra V-Dem

Responde la pregunta que un jurado hace siempre: *¿esto mide clima de inversión
o simplemente "Venezuela empeoró"?* V-Dem mide un constructo vecino —calidad
institucional— desde otra institución y con otro método.

Se reportan dos números por índice, porque **el ICIV completo comparte terreno
con V-Dem** a través de la dimensión D3 (CPI, WGI, Freedom House, WJP, PTS):

| Índice V-Dem | ICIV completo (solape declarado) | **ICIV sin D3 (contraste limpio)** | n |
|---|---:|---:|---:|
| Democracia liberal | +0.701 (p<0.001) | **+0.592 (p=0.001)** ✅ | 26 |
| Estado de derecho | +0.529 (p=0.005) | **+0.404 (p=0.041)** ✅ | 26 |
| Corrupción política | −0.329 (p=0.101) | −0.212 (p=0.297) ⚠️ | 26 |

Lo relevante es la columna del medio-derecha. **Al anular la dimensión
institucional entera**, lo que queda del ICIV —macro, energía, comercio, capital
humano y percepción— sigue correlacionando +0.59 con la democracia liberal y
+0.40 con el estado de derecho, ambas significativas. Es decir: la parte
económica y satelital del índice se mueve con el deterioro institucional medido
por un tercero que no participa en su cálculo.

La corrupción política no alcanza significancia y se reporta igual. Tiene
explicación razonable: el índice de V-Dem está saturado en el rango 0.89–0.97
durante los 26 años, con muy poca varianza que correlacionar.

**Por qué V-Dem y no Heritage o Fraser.** El Index of Economic Freedom y el
Economic Freedom of the World serían validadores más cercanos al constructo,
pero ambos devuelven **HTTP 403 a descargas automatizadas** (verificado
2026-08-11). Una descarga manual no es reproducible, y el proyecto exige que
todo artefacto se regenere desde cero. V-Dem se distribuye por Our World in Data
con licencia abierta y URL estable, la misma vía ya usada para el HDI.

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

- El ICIV **sin saber nada de migración** explica el 80% de la varianza (r²) del
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
> El índice sin migración predice la emigración (r=−0.85); el índice sin
> luminosidad sigue la luz nocturna medida por otro satélite y otro equipo
> (r=+0.81). Y si anulamos la dimensión institucional entera, lo que queda
> —economía, energía y percepción— todavía correlaciona +0.59 con el índice de
> democracia liberal de V-Dem, que no participa en el cálculo. Tres fenómenos
> independientes y no manipulables desde Venezuela apuntan en la misma
> dirección."

## Reproducir

```bash
cd iciv
python scripts/external_validation.py
```
