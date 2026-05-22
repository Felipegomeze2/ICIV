# Análisis: ¿Debe el ICIV pasar de Anual a Mensual?

**Fecha:** 12 mayo 2026 — Sesión 12
**Pregunta:** ¿Es viable convertir el ICIV de un indicador anual a uno mensual/trimestral/semestral?
**Objetivo del usuario:** habilitar análisis mes-a-mes y modelos de machine learning sobre series temporales más densas.

---

## 1. RESPUESTA EJECUTIVA

**Veredicto:** ❌ **Convertir el ICIV completo a mensual NO es viable**, pero ✅ **construir un "ICIV Pulse" paralelo mensual SÍ es la solución correcta**.

**Razón principal:** **Solo 12 de 38 variables (32%) tienen disponibilidad real mensual.**
Las 26 restantes son **intrínsecamente anuales** porque sus organismos publicadores
(WDI, WGI, UNDP HDR, V-Dem, BTI, CPI, FH, IEF, WJP, RSF, FSI, WHO HDI...) operan en
ciclos anuales o bienales. Forzar mensualidad requeriría **interpolación → datos
artificiales → viola la regla cero del proyecto**.

**Solución recomendada:** **Doble frecuencia con dashboard estratificado.**
- 🟢 ICIV Anual: el indicador oficial (28 variables, score 0-100, ya construido)
- 🟢 ICIV Pulse Mensual: indicador derivado con 12 variables de alta frecuencia
- 🟢 ML futura: usar Pulse como feature para predecir ICIV anual; o forecast el Pulse mismo

---

## 2. AUDITORÍA DE FRECUENCIA POR DIMENSIÓN

### D1 — Estabilidad Macroeconómica (25% AHP)

| Variable | Frecuencia nativa | Mensual viable | Fuente alternativa mensual |
|----------|-------------------|----------------|----------------------------|
| `inflacion_deflactor_pib_pct` | Anual (IMF WEO) | ❌ | Solo BCV (prohibido) u OVF (no credibilidad académica) |
| `pib_crecimiento_real_pct` | Anual (WDI/IMF) | ❌ | PIB es trimestral mínimo; no hay PIB mensual para VEN |
| `reservas_internacionales_usd` | Anual (WDI) | ❌ | VEN dejó de reportar desde 2018 |
| `tipo_cambio_oficial_lcu_usd` | Anual (WDI) | ❌ | BCV prohibido; DolarToday no académico |
| `wti_precio_usd` | **Diario** (FRED) | ✅ | Ya disponible |
| `tasa_fed_funds_pct` | **Mensual** (FRED) | ✅ | Ya disponible |
| `brent_precio_usd` | **Diario** (FRED) ⭐ | ✅ | Sesión 12 |
| `usd_index_broad` | **Diario** (FRED) ⭐ | ✅ | Sesión 12 |
| `vix_volatility` | **Diario** (FRED) ⭐ | ✅ | Sesión 12 |
| `ust_10y_yield_pct` | **Diario** (FRED) ⭐ | ✅ | Sesión 12 |

**D1 viable mensual:** 6/10 vars (60%) → pero todas son **externas a Venezuela** (precios commodities + tasas EE.UU.). Los drivers internos (inflación, PIB, reservas, FX) **NO son mensualizables sin BCV.**

### D2 — Sector Energético (20% AHP)

| Variable | Frecuencia nativa | Mensual viable |
|----------|-------------------|----------------|
| `petroleo_crudo_produccion_tbpd` | **Mensual** (EIA International) | ✅ |
| `gas_natural_produccion_bcf` | Anual (EIA) | 🟡 EIA tiene mensual para algunos países, no VEN consistentemente |
| `electricidad_generacion_bkwh` | Anual (EIA) | ❌ Sin reporte mensual para VEN |
| `luminosidad_nocturna_idx` | Anual (Li et al. composites) | 🟡 NOAA EOG tiene composites mensuales (requiere NASA login) |

**D2 viable mensual:** 1-2/4 vars (25-50%).

### D3 — Entorno Institucional (20% AHP)

| Variable | Frecuencia nativa | Mensual viable |
|----------|-------------------|----------------|
| `cpi_score` (Transparency Intl) | **Anual** (publicación enero) | ❌ Por diseño |
| `wgi_promedio_sc` (Banco Mundial) | **Anual** (publicación septiembre) | ❌ Por diseño |
| `ief_overall_score` (Heritage) | **Anual** (publicación enero) | ❌ Por diseño |
| `freedom_house_score` | **Anual** (publicación febrero) | ❌ Por diseño |
| `ofac_sanciones_count` | Snapshot diario | 🟡 Pero solo 1 punto por año en práctica |
| `pts_terror_politico` | **Anual** | ❌ Por diseño |
| `vdem_libdem_index` | **Anual** | ❌ Por diseño |
| `fragile_states_index` | **Anual** | ❌ Por diseño |
| `wjp_rule_of_law` | **Anual** | ❌ Por diseño |
| `rsf_press_freedom` | **Anual** | ❌ Por diseño |
| `bti_governance_index` | **Bienal** | ❌ Por diseño |
| `acled_eventos_violencia` | **Semanal** | ✅ (requiere API key) |
| `ucdp_conflicto_idx` | **Anual** (algunos mensuales) | 🟡 |

**D3 viable mensual:** 1-2/13 vars (8-15%). **Las dimensiones institucionales son intrínsecamente anuales** porque miden estados estructurales (corrupción, libertades, gobernanza) que no fluctúan significativamente mes-a-mes.

### D4 — Apertura Comercial (15% AHP)

| Variable | Frecuencia nativa | Mensual viable |
|----------|-------------------|----------------|
| `ied_neta_usd` | Anual (WDI) | ❌ IED tiene lag 12-18 meses |
| `exportaciones_pct_pib` | Anual (WDI) | 🟡 UN Comtrade tiene mensual bilateral |
| `desempleo_pct` | Anual (IMF) | ❌ VEN no reporta mensual |
| `migrantes_vzla_millones` | **Anual (agregado)**; UNHCR publica mensual | ✅ R4V/UNHCR |
| `lsci_conectividad_maritima` | Anual (WB) | ❌ Por diseño |
| `vuelos_aerolineas_int_count` | Sin datos | ❌ OpenSky no histórico |
| `remesas_recibidas_usd` | Anual (WDI) | 🟡 Banco Mundial Bilateral Migration & Remittances tiene trimestral |

**D4 viable mensual:** 1-2/7 vars (15-30%).

### D5 — Capital Humano (10% AHP)

| Variable | Frecuencia nativa | Mensual viable |
|----------|-------------------|----------------|
| `hdi` | Anual (UNDP) | ❌ Por diseño |
| `tasa_alfabetizacion_adulta_pct` | Anual (WDI) | ❌ |
| `acceso_electricidad_pct` | Anual (WDI) | ❌ |
| `esperanza_vida_anos` | Anual (WHO) | ❌ |
| `mortalidad_infantil_x1000` | Anual (WHO) | ❌ |

**D5 viable mensual:** 0/5 vars (0%). **Las variables de capital humano cambian en escalas anuales/decenales por naturaleza.**

### D6 — Percepción Internacional (10% AHP)

| Variable | Frecuencia nativa | Mensual viable |
|----------|-------------------|----------------|
| `guardian_tono_titulares` | **Diario** (agregado anual) | ✅ |
| `guardian_articulos_venezuela` | **Diario** | ✅ |
| `google_trends_vzla` | **Semanal** (bloqueado en esta IP) | 🟡 |

**D6 viable mensual:** 2-3/3 vars (67-100%). **La percepción es la dimensión más mensualizable**.

---

## 3. RESUMEN AGREGADO

| Dimensión | Peso AHP | Vars totales | Vars con monthly | % monthly coverage |
|-----------|----------|--------------|------------------|---------------------|
| D1 Macro | 25% | 10 | 6 | 60% |
| D2 Energía | 20% | 4 | 1-2 | 25-50% |
| D3 Institucional | 20% | 13 | 1-2 | 8-15% |
| D4 Comercial | 15% | 7 | 1-2 | 15-30% |
| D5 Capital Humano | 10% | 5 | 0 | 0% |
| D6 Percepción | 10% | 3 | 2-3 | 67-100% |
| **TOTAL** | 100% | 42 | ~12 | ~28% |

**Peso AHP cubierto por variables mensualizables:** ~30-35%.

**Conclusión técnica:** No se puede construir un ICIV mensual con la misma metodología actual sin renunciar al 65-70% del peso AHP. **Eso destruiría la coherencia del indicador**.

---

## 4. TRES APROXIMACIONES POSIBLES

### Aproximación A: ICIV mensual completo con interpolación
**Cómo:** Las 26 variables anuales se interpolan a mensual.
**Académicamente:** ❌ Inaceptable. Crea ~30 datos artificiales por variable × 26 variables = **780 datos inventados por año**.
**Veredicto:** 🚫 **VIOLA LA REGLA CERO** del proyecto. **DESCARTADO**.

### Aproximación B: Mixed-Frequency Composite Indicator (MIDAS)
**Cómo:** Modelo MIDAS (Ghysels, Sinko & Valkanov 2007) que combina variables de
distintas frecuencias en una sola ecuación, sin interpolar.
**Académicamente:** ✅ Válido (literatura macro establecida).
**Costo:** Reescritura completa del aggregator. ~80 horas. Pérdida de simplicidad metodológica.
**Veredicto:** 🟡 **TÉCNICAMENTE POSIBLE pero excede el alcance de una tesis de especialización**.

### Aproximación C: Dual-frequency dashboard (ICIV Anual + ICIV Pulse mensual)
**Cómo:**
- ICIV Anual permanece (28 vars, AHP, lo que ya tenemos)
- ICIV Pulse Mensual nuevo (12 vars, pesos renormalizados, actualización mensual)
- Dashboard muestra ambos lado a lado con disclaimer claro
**Académicamente:** ✅ Equivalente a "nowcasting indicator" de Stock & Watson (2002).
**Costo:** ~15-20 horas de desarrollo.
**Veredicto:** ✅ **RECOMENDADO**.

---

## 5. ICIV PULSE — PROPUESTA DETALLADA

### Variables candidatas (todas con frecuencia ≥mensual)

| Variable | Frecuencia | Peso AHP original | Peso Pulse renormalizado |
|----------|-----------|--------------------|-------------------------|
| `wti_precio_usd` | Diario→Mensual | 4.2% | 9.0% |
| `brent_precio_usd` | Diario→Mensual | 0% (nuevo) | 5.0% |
| `tasa_fed_funds_pct` | Mensual | 4.2% | 7.0% |
| `usd_index_broad` | Diario→Mensual | 0% (nuevo) | 5.0% |
| `vix_volatility` | Diario→Mensual | 0% (nuevo) | 5.0% |
| `ust_10y_yield_pct` | Diario→Mensual | 0% (nuevo) | 4.0% |
| `petroleo_crudo_produccion_tbpd` | Mensual (EIA) | 8.0% | 18.0% |
| `ofac_sanciones_count` | Diario (snapshot) | 3.0% | 8.0% |
| `migrantes_vzla_millones` | Mensual (UNHCR/R4V) | 4.5% | 12.0% |
| `guardian_tono_titulares` | Diario→Mensual | 5.0% | 13.0% |
| `guardian_articulos_venezuela` | Diario→Mensual | 5.0% | 9.0% |
| `acled_eventos_violencia` | Semanal (requiere key) | 1.5% | 5.0% |

**Total peso renormalizado:** 100% (de un subconjunto coherente).

### Características del ICIV Pulse

- **Escala:** 0-100 (mismo como ICIV)
- **Frecuencia:** Mensual
- **Granularidad temporal:** desde enero 2020 (cuando EIA monthly comienza con consistencia)
- **Cobertura promedio:** 80-95% por mes (alta porque solo variables disponibles)
- **Categorías:** las mismas 5 bandas (Alto Riesgo, Moderado-Alto, Moderado, Bajo, Muy Bajo)

### Interpretación correcta para el usuario

> "El ICIV Pulse mensual es un **co-indicador de alta frecuencia** que captura los
> movimientos macroeconómicos y geopolíticos rápidos. **NO reemplaza el ICIV anual**,
> que tiene cobertura institucional completa. Pulse predice; Anual valida."

---

## 6. CASO DE USO ML — POR QUÉ LA DUALIDAD ES IDEAL

### Modelo 1 — Pulse → Anual (nowcasting)
- **Target:** ICIV Anual (publicado cada 12 meses)
- **Features:** ICIV Pulse mensual + sus 12 componentes (medias móviles, deltas, etc.)
- **Tipo:** Regresión con `pulse_avg_12m`, `pulse_volatility`, `pulse_min`, `pulse_trend`
- **Útil para:** estimar el ICIV anual antes de que se publiquen las fuentes lentas
- **Académicamente:** Stock & Watson 2002 (factor-augmented forecasting)

### Modelo 2 — Pulse → Pulse (forecasting)
- **Target:** ICIV Pulse t+k
- **Features:** ICIV Pulse t, t-1, t-2... + drivers externos (WTI futures, VIX)
- **Tipo:** SARIMA, Prophet, LSTM (con suficiente data)
- **Útil para:** alertas tempranas, escenarios mensuales
- **Académicamente:** Hyndman-Athanasopoulos textbook

### Modelo 3 — Mixed-frequency factor model (avanzado)
- **Target:** factor latente que explica ICIV Anual + Pulse simultáneamente
- **Features:** todas las series de cualquier frecuencia
- **Tipo:** Kalman filter, MF-DFM, MIDAS
- **Útil para:** investigación académica posterior a tesis
- **Académicamente:** Bańbura & Modugno 2014

### ¿Por qué NO un solo ICIV mensual?
Porque sin interpolación, **el "indicador mensual" tendría 65-70% NaN** la mayor
parte del tiempo, lo cual hace inviable cualquier modelo ML supervisado.
La dualidad **respeta la naturaleza real de los datos** y aún así permite ML potente.

---

## 7. PLAN DE IMPLEMENTACIÓN (si decides ir adelante)

### Fase 1 — ICIV Pulse base (15h)
1. Reorganizar `fetch_eia_monthly.py` para emitir datos mensuales sin agregar
2. Crear `fetch_fred_monthly.py` (agregación mensual de WTI/Brent/VIX/USD/UST/Fed)
3. Crear `fetch_guardian_monthly.py` (agregación mensual de tono + artículos)
4. Refactor UNHCR para preservar granularidad mensual
5. Nueva clase `iciv.index.PulseAggregator` con pesos renormalizados
6. Nuevo CSV `data/processed/iciv_pulse_monthly.csv`

### Fase 2 — Dashboard Pulse (10h)
1. Nueva sección "Pulse Mensual" en dashboard
2. Gráfico de líneas mensual 2020-presente
3. Comparación visual ICIV Anual vs Pulse anualizado
4. Drill-down por componente

### Fase 3 — ML básico (10h)
1. Modelo de regresión Pulse → Anual (R² esperado >0.70)
2. SARIMA del Pulse para forecast 3-6 meses
3. Dashboard de proyección integrada

**Total esfuerzo:** ~35 horas. **Adecuado para tesis ampliada o trabajo post-defensa.**

---

## 8. RECOMENDACIÓN FINAL

✅ **PROCEDE con la dualidad ICIV Anual + ICIV Pulse Mensual.**

**Razones:**
1. **Respeta** el principio CERO datos artificiales
2. **Maximiza** el valor de las variables high-frequency ya integradas
3. **Habilita** análisis ML serios (regresión, SARIMA, MF-VAR)
4. **No destruye** la metodología actual: el ICIV oficial sigue intacto
5. **Aporta** un activo defendible académicamente (Stock-Watson nowcasting)
6. **Es realista**: 35h vs 80+h de MIDAS puro

**Lo que NO se debe hacer:**
- ❌ Interpolar variables anuales a mensual
- ❌ Mezclar fuentes anuales y mensuales en un solo score sin distinción
- ❌ Vender el "Pulse" como reemplazo del ICIV (es complemento)
- ❌ Usar BCV/INE como excusa para obtener mensualidad (siguen prohibidas)

---

## 9. PRECEDENTES ACADÉMICOS QUE RESPALDAN LA DUALIDAD

1. **EMBI+ vs ICRG** — JPMorgan/EMBI publica diario; ICRG (Political Risk) publica mensual. Industria reconoce ambos sin fusionar.
2. **Fed BBKI vs ADS** — Brave-Butters-Kelley (mensual) y Aruoba-Diebold-Scotti (diario) coexisten como nowcasting indicators del business cycle. Ninguno reemplaza al GDP trimestral del BEA.
3. **Atlanta Fed GDPNow** — nowcast mensual del PIB trimestral. Modelo establecido.
4. **Lahiri-Monokroussos (2013)** — composite leading indicators a múltiples frecuencias en literatura de la NBER.

---

## 10. CHECKLIST PARA DECISIÓN

- [ ] ¿El usuario acepta que ICIV Anual sigue siendo el indicador "oficial"? (sí/no)
- [ ] ¿El Pulse será presentado como co-indicador, no reemplazo? (sí/no)
- [ ] ¿Se acepta que el Pulse cubre solo D1+D2+D6 fuertemente, D3+D4 débilmente, D5 nada? (sí/no)
- [ ] ¿Hay tiempo para 35h adicionales antes de defensa de tesis? (sí/no)
- [ ] ¿Se contemplan modelos ML solo post-tesis o como parte del documento? (definir)

Si todos los anteriores son **sí**: proceder a Fase 1.

---

*Documento creado: 12 mayo 2026 — Sesión 12 ICIV*
*Próximo paso: decisión del usuario sobre proceder con ICIV Pulse*
