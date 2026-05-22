# EDA — Hallazgos Iniciales del Dataset ICIV
**Fecha:** Abril 2026  
**Etapa:** Ingesta y Análisis Exploratorio  
**Fuentes analizadas:** WDI, WGI, EIA, IMF, CPI, IEF, HDI  
**Período:** 2000–2024

---

## 1. Cobertura de Datos por Variable

| Variable | Fuente | Años disponibles | Cobertura | Problema |
|---|---|---|---|---|
| Inflación IPC | WDI | 2009–2016 | 32% | Hiperinflación (2017–2024) sin dato — usar deflactor IMF como proxy |
| CPI Corrupción | Transp. Int. | 2010–2019, 2023 | 44% | Solo 11 observaciones para modelar |
| HDI | PNUD | 2000, 2005, 2010–2022 | 60% | Sin 2023–2024; quinquenal hasta 2010 |
| Cuenta Corriente | IMF | 2000–2016 | 68% | Venezuela suspendió reportes al FMI en 2017 |
| Reservas Internacionales | WDI | 2000–2017 | 72% | Sin reporte oficial desde 2018 — período de crisis más aguda |
| IEF Libertad Económica | Heritage | 2000, 2005, 2008–2024 | 76% | Gaps en 2001–2004 y 2006–2007 |
| Tipo de Cambio Oficial | WDI | 2000–2017, 2020–2024 | 92% | Reconversiones monetarias hacen la serie discontinua e incomparable |
| PIB Crecimiento Real | WDI | 2002–2024 | 92% | Solo faltan 2000–2001 |
| WGI (6 indicadores) | Banco Mundial | 2000, 2002–2024 | 96% | Solo falta 2001 |
| PIB Nominal / Per Cápita | WDI | 2000–2024 | 100% | Completo |
| IED Neta | WDI | 2000–2024 | 100% | Completo |
| Desempleo | IMF | 2000–2024 | 100% | Completo |
| Deflactor PIB (inflación) | IMF | 2000–2024 | 100% | Completo — pero escala logarítmica obligatoria por hiperinflación |
| EIA (8 series energéticas) | EIA | 2000–2024 | 100% | Fuente más completa del dataset |

**Cobertura global del dataset:** ~434 / 550 celdas (79%)

---

## 2. Hallazgos Cuantitativos Clave

### Economía (WDI / IMF)
- **PIB per cápita:** cayó de $13,646 (2010) a $1,506 (2020) → contracción del **89% en una década**. Sin precedente en América Latina en tiempos de paz.
- **Crecimiento real acumulado 2013–2020:** aprox. −75% (recesión de 8 años consecutivos).
- **Peor año de crecimiento:** −30.0% en 2020 (COVID + crisis estructural acumulada).
- **Hiperinflación 2018:** deflactor PIB = **225,690%**. El pico más alto registrado en la región.
- **IED negativa en 2017:** −$299M → señal directa de fuga de capital neto. Segundo episodio negativo fue 2009 (−$1.1B, crisis global).

### Energía (EIA)
- **Producción de petróleo crudo:** colapsó de 2,893 Mbpd (2000) a 527 Mbpd (2020) → caída del **82%** en dos décadas.
- **Recuperación parcial:** 863 Mbpd en 2024 (solo el 30% del nivel del año 2000).
- **Generación eléctrica:** pico de 135 bkWh (2013) → 72 bkWh (2023) → crisis de infraestructura documentada.
- **Gas natural:** relativamente estable pero con caída de 2001–2009; recuperación leve desde 2015.

### Gobernanza (WGI)
- **Deterioro monotónico en todos los indicadores** desde 2000. Sin ninguna mejora sostenida en ningún indicador.
- **Estado de Derecho (RL):** pasó de percentil 41.8 (2000) → 19.0 (2024). La caída más pronunciada.
- **Promedio 6 indicadores:** 44.5 percentil en 2000 → 22.2 en 2024. **Caída del 50% en 24 años.**
- **Control de Corrupción (CC):** de 34.5 → 15.7 (percentil). Cerca del umbral de los países más corruptos del mundo.

### Índices compuestos (CPI / IEF / HDI)
- **CPI 2023:** 13/100 → mínimo histórico de Venezuela.
- **IEF:** categorizó a Venezuela como economía "Reprimida" (< 40) desde 2013. Mínimo: 24.6 (2022).
- **HDI:** pico en 0.768 (2015) → retroceso a 0.699 (2021), equivalente al nivel de 2005 → **16 años de progreso humano borrados**.

---

## 3. Períodos Críticos para el Análisis

| Período | Evento | Impacto en datos |
|---|---|---|
| **2002–2003** | Paro petrolero / crisis política | Caída PIB −8.9% y −7.8% · desempleo sube a 16.8% |
| **2013–2016** | Inicio crisis estructural + caída precio petróleo | Reservas colapsan, PIB en recesión continua |
| **2017–2018** | Hiperinflación · reconversión monetaria | Tipo de cambio y reservas dejan de reportarse. Inflación >1,000% |
| **2018–2021** | **Período con peor cobertura de datos** | Múltiples fuentes suspenden reportes. Análisis más difícil. |
| **2020** | COVID-19 sobre economía ya en crisis | PIB −30% · desempleo sube a 7.5% |
| **2021–2024** | Recuperación parcial | PIB crece pero desde base muy baja. Petróleo se recupera parcialmente. |

---

## 4. Decisiones Metodológicas Sugeridas (para construcción del ICIV)

1. **Inflación:** usar el Deflactor del PIB (IMF) como variable principal, dada su cobertura completa. El IPC del WDI es demasiado incompleto.
2. **Tipo de cambio:** considerar excluir o segmentar la serie en sub-períodos por reconversiones (2008, 2018, 2021).
3. **Reservas:** usar la serie hasta 2017 y documentar el gap. No imputar.
4. **CPI e IEF:** son útiles como variables explicativas pero requieren interpolación o imputación para los años con gaps.
5. **Normalización:** la hiperinflación de 2018 requiere deflactado cuidadoso antes de cualquier normalización de índices nominales.
6. **Período base recomendado para el ICIV:** **2004–2024** para maximizar cobertura, excluyendo los años con más gaps en gobernanza y capital humano.

---

## 5. Fuentes por Nivel de Confiabilidad

| Nivel | Fuentes | Motivo |
|---|---|---|
| **Alta** | EIA, IMF (desempleo/deflactor), WDI (PIB/IED) | Cobertura completa, metodología estable |
| **Media** | WGI, WDI (reservas), IMF (cuenta corriente) | Gaps en períodos clave o discontinuidades |
| **Baja** | CPI, IEF, HDI | Cobertura parcial, cambios metodológicos, series cortas |

---

*Archivo generado durante la fase de EDA · Ver dashboard interactivo: `EDA_Dashboard.html`*
