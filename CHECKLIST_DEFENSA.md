# CHECKLIST DE DEFENSA — ICIV Venezuela
## Lista de verificación para la presentación ante el jurado

> **Estado:** 21 de mayo de 2026 — Post-auditoría completa del plan de revisión del jurado  
> **Uso:** Marcar cada ítem antes de la defensa. Un ítem ❌ pendiente no bloquea la defensa si está documentado como "trabajo futuro".

---

## BLOQUE A — Consistencia metodológica (P0)

| Estado | Ítem | Evidencia |
|--------|------|-----------|
| ✅ | Una sola definición del índice en todos los documentos | `VARIABLES_MASTER.md` — tabla canónica única |
| ✅ | Número de variables consistente (41 en código y docs) | `dimensions.py` (41 vars) = `VARIABLES_MASTER.md` |
| ✅ | Pesos AHP iguales en `dimensions.py` y `settings.yaml` | Sincronizado en auditoría 21-may-2026 |
| ✅ | CR AHP documentado y aceptable | CR = 0.0081 < 0.10 (umbral Saaty) |
| ✅ | Periodicidad del índice correctamente declarada | Anual + Módulo Pulse mensual 2010–2026 |
| ✅ | Cobertura histórica correcta | 2000–2026 (27 años) |
| ✅ | Scores actuales documentados | 2024=33.8 (78.4%) · 2025=30.8 (51.9%) · 2026=34.3 (35.1%) |

---

## BLOQUE B — Trazabilidad de fuentes (P0)

| Estado | Ítem | Evidencia |
|--------|------|-----------|
| ✅ | Ninguna fuente venezolana en el pipeline | `iciv/CLAUDE.md` — regla absoluta + auditoría |
| ✅ | BCV eliminado de todos los documentos | Correcciones 21-may-2026 en PROYECTO y FUENTES |
| ✅ | `fsi_manual.csv` con columna fuente documentada | URLs Fund for Peace por año 2006–2024 |
| ✅ | `freedom_house.csv` — 2000–2002 derivados de PR/CL | Fórmula oficial FH documentada en fuente col. |
| ✅ | `rsf.csv` — cambio metodológico 2022 documentado | Pre-2022: OWID violations inverted; post-2022: RSF directo |
| ✅ | `cpi.csv` — conversión 0-10 → 0-100 documentada | fuente col. en cada fila |
| ✅ | `opensky.csv` — sin datos fabricados | Solo header, todos NaN |
| ✅ | `ofac.csv` — solo snapshot real 2026 | 1 fila, sin histórico inventado |
| ⚠️ | `hdi.csv` / `ief.csv` — fuente genérica | "UNDP HDR validada" / "Heritage IEF validada" (sin URL específica por año) |
| ✅ | Interpolación y forward-fill solo dentro de rangos reales | `limit_area='inside'` en GapImputer |
| ✅ | Variables sin datos → NaN explícito | 3 vars sin datos: ofac, vuelos, basel_aml |

---

## BLOQUE C — Validación honesta (P1)

| Estado | Ítem | Evidencia |
|--------|------|-----------|
| ✅ | Circularidad IED documentada | Dashboard bloque A → "Coherencia interna / Exploración" + nota de advertencia |
| ✅ | Validación externa independiente en bloque B | 9 índices no-componentes: WGI, CPI, FH, HDI, V-Dem, WJP, FSI, PTS, RSF |
| ✅ | Sensibilidad SI documentada | SI = 0.0408 (Robusto — umbral < 0.15) |
| ✅ | AHP vs PCA documentado | r = 0.9938, PC1 = 56.5% varianza |
| ✅ | Granger ICIV→IED con nota de causalidad | En contexto exploratorio, no causalidad establecida |
| ✅ | Eventos políticos con Δ ICIV observado | 7/7 eventos coinciden con dirección esperada |
| ✅ | LOO-CV para Nowcast | R²_LOO = -5.18 — honestamente reportado (no generaliza con 5 años) |

---

## BLOQUE D — Etiquetas de cobertura (P1)

| Estado | Ítem | Evidencia |
|--------|------|-----------|
| ✅ | Tiers de cobertura implementados en dashboard | Histórico ≥85% · Útil 70–84.9% · Parcial 50–69.9% · Provisional <50% |
| ✅ | Badge de tier visible al cambiar de año | JS `covTier()` + `selectScoreYear()` actualizado |
| ✅ | Descripción de cada tier en la UI | Texto descriptivo para Histórico/Útil/Parcial/Provisional |
| ✅ | 2024 etiquetado como "Parcial" (78.4%) o "Útil" | Depende de valor exacto — umbral Útil: ≥70% |
| ✅ | 2025 etiquetado como "Parcial" (51.9%) | Correcto |
| ✅ | 2026 etiquetado como "Provisional" (35.1%) | Correcto — solo fuentes alta frecuencia |

---

## BLOQUE E — Calidad técnica (P1)

| Estado | Ítem | Evidencia |
|--------|------|-----------|
| ✅ | Tests actualizados para end_year=2026 | `test_wdi_loader.py` L36, `conftest.py` fixtures 27 años |
| ✅ | Pipeline ejecuta sin errores | 21-may-2026: 26.9s, 27 años, rango 26.2–71.0 |
| ✅ | Dashboard en ubicación única (raíz del proyecto) | `_ROOT.parent / "iciv_dashboard.html"` |
| ✅ | `settings.yaml` sincronizado con `dimensions.py` | D3 (13 vars), D4 (7 vars), D5 (8 vars) actualizados |
| ⚠️ | Tests de integración con datos reales | Los tests saltan si no hay raw/ disponible (OK para CI) |

---

## BLOQUE F — Documentación de entrega (P2)

| Estado | Ítem | Evidencia |
|--------|------|-----------|
| ✅ | `VARIABLES_MASTER.md` — tabla canónica de 41 variables | En raíz del proyecto |
| ✅ | `FUENTES_DE_DATOS.md` actualizado | BCV/OVF excluidas, fecha 21-may-2026 |
| ✅ | `PROYECTO_ICIV_MASTER.md` actualizado | Fases, variable count, correcciones auditadas |
| ✅ | `iciv/CLAUDE.md` con regla de dashboard y datos | Regla absoluta documentada |
| ✅ | `CHECKLIST_DEFENSA.md` (este documento) | ✓ |
| ✅ | `RESPUESTAS_JURADO.md` — 12 preguntas preparadas | Ver siguiente documento |
| ❌ | Capítulos 3–6 de la tesis redactados | Pendiente — no iniciar hasta indicación de Felipe |
| ❌ | Presentación PowerPoint de defensa | Pendiente |
| ❌ | Repositorio GitHub con README | Pendiente |

---

## BLOQUE G — Limitaciones declaradas (obligatorio en defensa)

Las siguientes limitaciones deben mencionarse proactivamente en la defensa:

1. **Cobertura 2025–2026**: lag estructural de publicación. WGI 2025 → sep-2026; HDI 2024 → sep-2026; WDI 2025 → dic-2026.
2. **RSF escala discontinua**: pre-2022 (violations inverted) vs post-2022 (nueva metodología RSF). Comparabilidad limitada.
3. **Freedom House 2000–2002**: derivados de PR/CL con fórmula oficial, no Aggregate Score publicado directamente.
4. **OFAC sanciones**: solo snapshot actual, no histórico verificable. Variable queda NaN excepto 2026.
5. **Google Trends**: HTTP 429 frecuente, 22% cobertura. Baja fiabilidad longitudinal.
6. **Validación Granger ICIV→IED**: parcialmente circular (IED es componente del ICIV). Exploratoria.
7. **AHP basado en juicio del investigador**: sin panel de expertos externos. Limitación metodológica reconocida.
8. **Venezuela**: opacidad estadística crónica → algunos años tienen cobertura baja aunque se usen todas las fuentes internacionales.
9. **Nowcast OLS Pulse→ICIV**: R²_LOO = -5.18 — insuficiente data histórica para generalizar (5 años Pulse disponibles).

---

## Criterios de "Aprobado para defensa"

El proyecto puede defenderse cuando:
- [ ] Bloques A, B, C, D, E tienen todos sus ítems ✅ o ⚠️ documentado
- [ ] Las limitaciones del Bloque G están preparadas como respuestas verbales
- [ ] `RESPUESTAS_JURADO.md` revisado y practicado
- [ ] Pipeline ejecuta limpiamente en `python main.py --no-fetch --no-open`
- [ ] Dashboard abre y muestra scores coherentes

---

*Generado: 21 de mayo de 2026 — Auditoría completa Plan de Revisión del Jurado ICIV*
