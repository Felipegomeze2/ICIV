# ICIV — Indicador de Clima de Inversión Venezuela

> **Tesis de Posgrado** · Especialización en Big Data e Inteligencia de Negocios  
> **Autor:** Felipe Gómez Espinal  
> **Institución:** EAFIT  
> **Período del modelo:** 2000–2026 (27 años)  
> **Última actualización:** 21 de mayo de 2026

---

## ¿Qué es el ICIV?

El **ICIV** (Indicador de Clima de Inversión Venezuela) es el único indicador mensual de clima de inversión para Venezuela construido íntegramente con **datos satelitales e internacionales auditables**, sin ninguna fuente del gobierno venezolano, con 25 años de historia.

| Característica | Valor |
|---|---|
| Variables | 41 en 6 dimensiones |
| Método de ponderación | AHP — Saaty (1980), CR = 0.0081 |
| Validación externa | Pearson r = 0.46 vs. 9 índices independientes |
| Sensibilidad | SI = 0.0408 (Robusto, umbral < 0.15) |
| Score 2024 | **33.8 / 100** · Riesgo Moderado-Alto (78.4% cobertura) |
| Score 2026 | **34.3 / 100** · Provisional (35.1% cobertura) |

---

## Módulos

### 1 · ICIV Anual (índice principal)
- 41 variables internacionales en 6 dimensiones (D1 Macro, D2 Energía, D3 Institucional, D4 Comercial, D5 Capital Humano, D6 Percepción)
- Scores 2000–2026, rango histórico 26.2–71.0 (pico 2012, mínimo 2020)
- Pesos AHP con consistencia validada (CR = 0.0081)

### 2 · ICIV Pulse Mensual (co-indicador)
- 12 variables de alta frecuencia internacionales (WTI, Brent, Fed, USD, VIX, UST10Y, petróleo VEN, OFAC, migrantes UNHCR, Guardian)
- 197 meses de historia (2010-01 a 2026-05), rango 31.2–91.4
- Ninguna fuente del gobierno venezolano

### 3 · SATV — Sistema de Alertas Tempranas Venezuela
- Semáforo por dimensión (Normal / Precaución / Crítico)
- Detección de tendencias (deterioro / estabilización / recuperación)
- 6 alertas compuestas nombradas (Colapso Energético, Contagio Sistémico, etc.)

---

## Fuentes (todas internacionales, cero venezolanas)

| Fuente | Variables | Cobertura |
|---|---|---|
| World Bank WDI | PIB, inflación, IED, exportaciones, tipo cambio… | 25+ años |
| World Bank WGI | Gobernanza (6 indicadores → promedio) | 24 años |
| IMF WEO | Inflación, desempleo, cuenta corriente | 27 años |
| EIA | Producción petróleo/gas, electricidad | 25+ años |
| FRED | WTI, Fed funds, VIX, USD Index, UST10Y | 27 años |
| CPI (TI) | Índice de percepción de corrupción | 27 años |
| IEF (Heritage) | Libertad económica | 20 años |
| HDI (UNDP) | Índice de desarrollo humano | 15 años |
| Freedom House | Democracia y libertades civiles | 25 años |
| V-Dem | Índice de democracia liberal | 26 años |
| WJP Rule of Law | Estado de derecho | Disponible |
| Fund for Peace FSI | Fragilidad estatal | 19 años |
| RSF | Libertad de prensa | 13 años |
| UNHCR | Migrantes venezolanos | 26 años |
| The Guardian API | Cobertura mediática | 27 años |
| Li et al. VIIRS | Luminosidad nocturna (satélite) | 25 años |

---

## Estructura del Repositorio

```
ICIV/
├── README.md                        ← Este archivo
├── iciv_dashboard.html              ← Dashboard interactivo (entregable)
├── VARIABLES_MASTER.md              ← Catálogo canónico de 41 variables
├── PROYECTO_ICIV_MASTER.md          ← Documento maestro del proyecto
├── FUENTES_DE_DATOS.md              ← Documentación completa de fuentes
├── CATALOGO_DE_DATOS.md             ← Catálogo técnico de variables
├── CHECKLIST_DEFENSA.md             ← Lista de verificación para defensa
├── RESPUESTAS_JURADO.md             ← Respuestas preparadas para el jurado
├── PLAN_DE_ACCION_REVISION_JURADO_ICIV.md
│
└── iciv/                            ← Pipeline Python principal
    ├── main.py                      ← Punto de entrada
    ├── pyproject.toml               ← Dependencias del proyecto
    ├── config/
    │   └── settings.yaml            ← Configuración y pesos AHP
    ├── data/
    │   ├── raw/                     ← Datos fuente (CSV auditables)
    │   └── processed/               ← Outputs generados (no versionados)
    ├── scripts/                     ← 29 scripts fetch por fuente
    ├── src/iciv/                    ← Paquete Python
    │   ├── data/                    ← Catálogo, loaders, modelos
    │   ├── processing/              ← Pipeline ETL (Cleaner, Imputer, Normalizer)
    │   ├── index/                   ← Aggregator AHP, PCA, dimensiones
    │   ├── satv/                    ← Sistema de Alertas Tempranas
    │   ├── analytics/               ← Correlación, indicadores líderes
    │   ├── scenarios/               ← Escenarios 2027–2030
    │   └── ml/                      ← Forecast SARIMA + Nowcast OLS
    └── tests/                       ← Suite de tests
```

---

## Ejecución Rápida

```bash
# Instalar dependencias
cd iciv
pip install -e ".[dev]"

# Ejecutar pipeline completo (descarga + procesa + dashboard)
python main.py

# Solo procesar (sin re-descargar, sin abrir browser)
python main.py --no-fetch --no-open
```

El dashboard se genera en `iciv_dashboard.html` en la raíz del repositorio.

---

## Scores ICIV (mayo 2026)

| Año | Score | Cobertura | Tier |
|-----|-------|-----------|------|
| 2024 | **33.8** | 78.4% | Útil |
| 2025 | **30.8** | 51.9% | Parcial |
| 2026 | **34.3** | 35.1% | Provisional |

Escala ICIV: 0 = Riesgo Extremo · 100 = Clima Óptimo

---

## Limitaciones Declaradas

1. **Lag estructural** de publicación: WGI 2025 → sep-2026; HDI 2024 → sep-2026
2. **RSF escala discontinua**: empalme metodológico 2022
3. **Freedom House 2000–2002**: derivados de PR/CL con fórmula oficial
4. **OFAC sanciones**: solo snapshot actual, sin histórico verificable
5. **Google Trends**: HTTP 429 frecuente, cobertura 22%
6. **Validación Granger ICIV→IED**: parcialmente circular (IED es componente del ICIV)
7. **AHP**: basado en juicio del investigador, sin panel de expertos externos
8. **Opacidad estadística venezolana**: cobertura limitada incluso con fuentes internacionales
9. **Nowcast OLS**: R²_LOO = −5.18 — insuficiente data histórica para generalizar

---

## Cita Sugerida

```
Gómez Espinal, F. (2026). ICIV: Indicador de Clima de Inversión Venezuela
2000–2026. Tesis de posgrado, Especialización Big Data e Inteligencia de
Negocios, EAFIT. Pipeline disponible en: https://github.com/Felipegomeze2/ICIV
```

---

*Datos 100% internacionales · Sin fuentes del gobierno venezolano · Cero datos artificiales*
