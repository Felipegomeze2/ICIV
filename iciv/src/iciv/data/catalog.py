"""
Catálogo central de variables del ICIV.

Este es el documento de verdad sobre qué variables existen, de dónde vienen,
cómo se deben interpretar y qué peso tienen dentro de su dimensión.

Principio: si quieres agregar, remover o ajustar una variable del índice,
este archivo (y iciv_config.yaml) son los únicos que deberías tocar.
"""

from __future__ import annotations

from .models.indicators import (
    Direction,
    DimensionID,
    SourceID,
    VariableMetadata,
)


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGO COMPLETO
# Los dim_weight dentro de cada dimensión suman 1.0.
# ─────────────────────────────────────────────────────────────────────────────

CATALOG: dict[str, VariableMetadata] = {

    # ── DIMENSIÓN 1: ESTABILIDAD MACROECONÓMICA (30% del ICIV) ───────────────
    "inflacion_deflactor_pib_pct": VariableMetadata(
        column_name="inflacion_deflactor_pib_pct",
        description="Inflación — Deflactor del PIB (%)",
        source=SourceID.IMF,
        unit="%",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.MACRO,
        dim_weight=0.28,
        available_from=2000,
        notes="Proxy principal de inflación. IPC del WDI solo cubre 2009–2016.",
    ),
    "pib_crecimiento_real_pct": VariableMetadata(
        column_name="pib_crecimiento_real_pct",
        description="Crecimiento real del PIB (%)",
        source=SourceID.WDI,
        unit="%",
        direction=Direction.POSITIVE,
        dimension=DimensionID.MACRO,
        dim_weight=0.22,
        available_from=2002,
        notes="Falta 2000–2001 en WDI. Imputable desde IMF.",
    ),
    "reservas_internacionales_usd": VariableMetadata(
        column_name="reservas_internacionales_usd",
        description="Reservas internacionales (USD)",
        source=SourceID.WDI,
        unit="USD",
        direction=Direction.POSITIVE,
        dimension=DimensionID.MACRO,
        dim_weight=0.18,
        available_from=2000,
        notes="Sin datos desde 2018. Venezuela dejó de reportar al BM.",
    ),
    "tipo_cambio_oficial_lcu_usd": VariableMetadata(
        column_name="tipo_cambio_oficial_lcu_usd",
        description="Tipo de cambio oficial — log₁₀(BsF/USD equiv.)",
        source=SourceID.WDI,
        unit="log₁₀(BsF/USD)",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.MACRO,
        dim_weight=0.12,
        available_from=2000,
        notes=(
            "Serie homogeneizada en BsF/USD equivalente (3 reconversiones: "
            "2008 ÷1 000, 2018 ÷1 000, 2021 ÷10^6) y transformada a log₁₀ "
            "antes del MinMax para comprimir 11 órdenes de magnitud."
        ),
    ),

    # ── DIMENSIÓN 2: SECTOR ENERGÉTICO (25% del ICIV) ────────────────────────
    "petroleo_crudo_produccion_tbpd": VariableMetadata(
        column_name="petroleo_crudo_produccion_tbpd",
        description="Producción de petróleo crudo (Miles Bpd)",
        source=SourceID.EIA,
        unit="Mbpd",
        direction=Direction.POSITIVE,
        dimension=DimensionID.ENERGY,
        dim_weight=0.50,
        available_from=2000,
        notes="Serie completa 2000–2024. Fuente más confiable del dataset.",
    ),
    "gas_natural_produccion_bcf": VariableMetadata(
        column_name="gas_natural_produccion_bcf",
        description="Producción de gas natural (BCF/año)",
        source=SourceID.EIA,
        unit="BCF",
        direction=Direction.POSITIVE,
        dimension=DimensionID.ENERGY,
        dim_weight=0.30,
        available_from=2000,
    ),
    "electricidad_generacion_bkwh": VariableMetadata(
        column_name="electricidad_generacion_bkwh",
        description="Generación eléctrica (bkWh/año)",
        source=SourceID.EIA,
        unit="bkWh",
        direction=Direction.POSITIVE,
        dimension=DimensionID.ENERGY,
        dim_weight=0.20,
        available_from=2000,
        notes="Proxy de capacidad de infraestructura energética.",
    ),

    # ── DIMENSIÓN 3: ENTORNO INSTITUCIONAL (20% del ICIV) ────────────────────
    "cpi_score": VariableMetadata(
        column_name="cpi_score",
        description="CPI — Índice de Percepción de Corrupción (0–100)",
        source=SourceID.CPI,
        unit="score 0-100",
        direction=Direction.POSITIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.25,
        available_from=2010,
        notes=(
            "Solo 11 observaciones (2010–2019, 2023). "
            "Metodología cambió en 2012. Requiere interpolación."
        ),
    ),
    "wgi_promedio_sc": VariableMetadata(
        column_name="wgi_promedio_sc",
        description="WGI — Promedio 6 indicadores de gobernanza (percentil 0–100)",
        source=SourceID.WGI,
        unit="percentil 0-100",
        direction=Direction.POSITIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.25,
        available_from=2000,
        notes="Promedio simple de CC, GE, PV, RL, RQ, VA en escala SC (percentil).",
    ),
    "ief_overall_score": VariableMetadata(
        column_name="ief_overall_score",
        description="IEF — Índice de Libertad Económica Heritage (0–100)",
        source=SourceID.IEF,
        unit="score 0-100",
        direction=Direction.POSITIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.18,
        available_from=2000,
        notes="Gaps en 2001–2004 y 2006–2007. Serie interpolable.",
    ),

    # ── DIMENSIÓN 4: APERTURA COMERCIAL Y FINANCIERA (15% del ICIV) ──────────
    "ied_neta_usd": VariableMetadata(
        column_name="ied_neta_usd",
        description="Inversión Extranjera Directa neta (USD)",
        source=SourceID.WDI,
        unit="USD",
        direction=Direction.POSITIVE,
        dimension=DimensionID.COMMERCIAL,
        dim_weight=0.28,
        available_from=2000,
        notes="Serie completa. Valores negativos indican fuga de capital neto.",
    ),
    "exportaciones_pct_pib": VariableMetadata(
        column_name="exportaciones_pct_pib",
        description="Exportaciones (% del PIB)",
        source=SourceID.WDI,
        unit="% PIB",
        direction=Direction.POSITIVE,
        dimension=DimensionID.COMMERCIAL,
        dim_weight=0.22,
        available_from=2000,
    ),
    "desempleo_pct": VariableMetadata(
        column_name="desempleo_pct",
        description="Tasa de desempleo (%)",
        source=SourceID.IMF,
        unit="%",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.COMMERCIAL,
        dim_weight=0.16,
        available_from=2000,
        notes="Dato discutido para 2014–2020 dado el contexto de informalidad.",
    ),
    "lsci_conectividad_maritima": VariableMetadata(
        column_name="lsci_conectividad_maritima",
        description="LSCI — Conectividad Marítima de Contenedores UNCTAD (0–100)",
        source=SourceID.UNCTAD,
        unit="índice 0-100",
        direction=Direction.POSITIVE,
        dimension=DimensionID.COMMERCIAL,
        dim_weight=0.12,
        available_from=2004,
        notes="Liner Shipping Connectivity Index. Venezuela pico ~23 pts (2007); colapso post-sanciones 2019.",
    ),
    "vuelos_aerolineas_int_count": VariableMetadata(
        column_name="vuelos_aerolineas_int_count",
        description="Aerolíneas internacionales con servicio regular a Venezuela (nº)",
        source=SourceID.OPENSKY,
        unit="número",
        direction=Direction.POSITIVE,
        dimension=DimensionID.COMMERCIAL,
        dim_weight=0.08,
        available_from=2000,
        notes="Proxy de conectividad aérea y apertura comercial. Pico 42 aerolíneas (2013); mínimo 6 en COVID-2020.",
    ),

    # ── DIMENSIÓN 5: CAPITAL HUMANO E INFRAESTRUCTURA (10% del ICIV) ─────────
    "hdi": VariableMetadata(
        column_name="hdi",
        description="HDI — Índice de Desarrollo Humano PNUD (0–1)",
        source=SourceID.HDI,
        unit="índice 0-1",
        direction=Direction.POSITIVE,
        dimension=DimensionID.HUMAN,
        dim_weight=0.30,
        available_from=2000,
        notes="Quinquenal hasta 2010, luego anual hasta 2022.",
    ),
    "tasa_alfabetizacion_adulta_pct": VariableMetadata(
        column_name="tasa_alfabetizacion_adulta_pct",
        description="Tasa de alfabetización adulta (%)",
        source=SourceID.WDI,
        unit="%",
        direction=Direction.POSITIVE,
        dimension=DimensionID.HUMAN,
        dim_weight=0.20,
        available_from=2001,
        notes="Muy pocos puntos de datos. Usar con cautela.",
    ),
    "acceso_electricidad_pct": VariableMetadata(
        column_name="acceso_electricidad_pct",
        description="Acceso a electricidad (% población)",
        source=SourceID.WDI,
        unit="%",
        direction=Direction.POSITIVE,
        dimension=DimensionID.HUMAN,
        dim_weight=0.20,
        available_from=2000,
    ),
    "esperanza_vida_anos": VariableMetadata(
        column_name="esperanza_vida_anos",
        description="Esperanza de vida al nacer — ambos sexos (años) — WHO GHO",
        source=SourceID.WHO,
        unit="años",
        direction=Direction.POSITIVE,
        dimension=DimensionID.HUMAN,
        dim_weight=0.20,
        available_from=2000,
        notes=(
            "Fuente: WHO GHO (WHOSIS_000001). Cobertura 2000-2021 (22 años). "
            "Venezuela cayó de 74.7 años (2006) a 71.2 (2021) — retroceso de "
            "25 años de progreso, el peor de América Latina. "
            "Post-2021: estimaciones OMS basadas en métodos de estimación indirecta "
            "dado que MPPS suspendió boletines epidemiológicos 2016-2019."
        ),
    ),
    "mortalidad_infantil_x1000": VariableMetadata(
        column_name="mortalidad_infantil_x1000",
        description="Tasa de mortalidad infantil (0-11 meses, ambos sexos, x1000 NV) — WHO/IGME",
        source=SourceID.WHO,
        unit="muertes x 1,000 nacidos vivos",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.HUMAN,
        dim_weight=0.10,
        available_from=2000,
        notes=(
            "Fuente: WHO GHO / UN IGME (MDG_0000000001). Cobertura 2000-2023 (24 años). "
            "Venezuela: cayó de 17.5 (2000) hasta mínimo 14.3 (2008), luego aumentó "
            "hasta 21.5 (2016+) — reversión del descenso histórico documentada "
            "por ENCOVI/IIES-UCAB. Nota: post-2016 hay poca variación porque el IGME "
            "usa modelos de suavizado ante ausencia de registros nacionales."
        ),
    ),

    # ── DIMENSIÓN 2 AMPLIADA: VIIRS — Luminosidad nocturna satelital ─────────
    "luminosidad_nocturna_idx": VariableMetadata(
        column_name="luminosidad_nocturna_idx",
        description="VIIRS/DMSP — Índice de luminosidad nocturna Venezuela (0-100)",
        source=SourceID.VIIRS,
        unit="índice normalizado 0-100",
        direction=Direction.POSITIVE,
        dimension=DimensionID.ENERGY,
        dim_weight=0.15,
        available_from=2000,
        notes=(
            "Proxy de actividad económica real independiente de estadísticas "
            "oficiales venezolanas. Combina DMSP-OLS (2000-2013) y VIIRS DNB "
            "(2013-2024). Captura apagones, desindustrialización y colapso "
            "eléctrico. Mínimo histórico en 2019 por Gran Apagón Nacional "
            "(falla de la represa Guri, 7-mar-2019). "
            "Fuente: NOAA EOG / Henderson et al. (2012) AER."
        ),
    ),

    # ── DIMENSIÓN 1 AMPLIADA: FRED — Contexto financiero global ──────────────
    "wti_precio_usd": VariableMetadata(
        column_name="wti_precio_usd",
        description="Precio WTI del petróleo crudo (USD/barril) — promedio anual",
        source=SourceID.FRED,
        unit="USD/barril",
        direction=Direction.POSITIVE,
        dimension=DimensionID.MACRO,
        dim_weight=0.12,
        available_from=2000,
        notes=(
            "Venezuela genera >95% de divisas del petróleo. WTI es el driver "
            "externo más importante del ciclo fiscal y de inversión venezolano. "
            "Fuente: FRED series DCOILWTICO (promedio anual)."
        ),
    ),
    "tasa_fed_funds_pct": VariableMetadata(
        column_name="tasa_fed_funds_pct",
        description="Tasa de fondos federales EE.UU. (%) — promedio anual",
        source=SourceID.FRED,
        unit="%",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.MACRO,
        dim_weight=0.08,
        available_from=2000,
        notes=(
            "Ciclos monetarios de EE.UU. determinan flujos de capital global "
            "hacia mercados emergentes. FEDFUNDS alta = costo de oportunidad "
            "elevado para IED en economías riesgosas. Fuente: FRED FEDFUNDS."
        ),
    ),

    # ── DIMENSIÓN 3 AMPLIADA: Freedom House y OFAC ───────────────────────────
    "freedom_house_score": VariableMetadata(
        column_name="freedom_house_score",
        description="Freedom House — Aggregate Score (0-100, mayor = más libre)",
        source=SourceID.FREEDOM_HOUSE,
        unit="score 0-100",
        direction=Direction.POSITIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.14,
        available_from=2000,
        notes=(
            "Combina derechos políticos y libertades civiles en una escala 0-100. "
            "Venezuela: Parcialmente Libre 2000-2005, No Libre desde 2006. "
            "Declive continuo hasta 10/100 en 2024. "
            "Fuente: Freedom House Freedom in the World 2000-2024."
        ),
    ),
    "ofac_sanciones_count": VariableMetadata(
        column_name="ofac_sanciones_count",
        description="OFAC — Entidades venezolanas en lista SDN (conteo acumulado)",
        source=SourceID.OFAC,
        unit="número de entidades",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.08,
        available_from=2004,
        notes=(
            "Proxy cuantitativo del riesgo de contraparte y aislamiento financiero "
            "internacional. Escalada fuerte en 2015 (EO 13692), 2017 (EO 13808) "
            "y 2019 (PDVSA). Mayor conteo = mayor riesgo de compliance para inversores. "
            "Fuente: OFAC SDN List / CRS Reports Venezuela Sanctions."
        ),
    ),
    "pts_terror_politico": VariableMetadata(
        column_name="pts_terror_politico",
        description="PTS — Escala de Terror Político (promedio AI/HRW/State Dept., 1-5)",
        source=SourceID.PTS,
        unit="escala 1-5",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.10,
        available_from=2000,
        notes=(
            "Political Terror Scale: promedio de PTS_A (Amnesty Intl), PTS_H "
            "(Human Rights Watch) y PTS_S (U.S. State Dept.). Escala 1=seguro, "
            "5=terror generalizado. Venezuela alcanzó 5.0 en 2020. "
            "Fuente: Gibney, Cornett, Wood, Haschke & Arnon (2024). "
            "http://www.politicalterrorscale.org"
        ),
    ),

    # ── DIMENSIÓN 4 AMPLIADA: Migración venezolana ───────────────────────────
    "migrantes_vzla_millones": VariableMetadata(
        column_name="migrantes_vzla_millones",
        description="Venezolanos fuera del país — refugiados y migrantes (millones)",
        source=SourceID.UNHCR,
        unit="millones de personas",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.COMMERCIAL,
        dim_weight=0.14,
        available_from=2000,
        notes=(
            "El mayor éxodo de la historia latinoamericana: >7.7M personas para 2024 "
            "(2da crisis de desplazamiento del mundo según ACNUR). "
            "Proxy directo de destrucción del capital humano y pérdida de confianza "
            "ciudadana en el entorno económico-institucional. "
            "Fuente: ACNUR / R4V — Situación Venezuela."
        ),
    ),

    # ── DIMENSIÓN 6 AMPLIADA: Google Trends ──────────────────────────────────
    "google_trends_vzla": VariableMetadata(
        column_name="google_trends_vzla",
        description="Google Trends — Interés global en 'Venezuela inversión' (0-100)",
        source=SourceID.GTRENDS,
        unit="índice relativo 0-100",
        direction=Direction.POSITIVE,
        dimension=DimensionID.PERCEPTION,
        dim_weight=0.30,
        available_from=2004,
        notes=(
            "Índice relativo de búsqueda (0=mínimo, 100=máximo histórico). "
            "Promedio de queries: 'Venezuela inversión', 'Venezuela economy', "
            "'invertir Venezuela'. Proxy nowcasting de percepción global. "
            "Metodología: Choi & Varian (2012), The Economic Journal. "
            "Fuente: Google Trends vía pytrends."
        ),
    ),

    # ── DIMENSIÓN 4 AMPLIADA: Remesas ────────────────────────────────────────
    "remesas_recibidas_usd": VariableMetadata(
        column_name="remesas_recibidas_usd",
        description="Remesas personales recibidas (USD) — WB WDI",
        source=SourceID.WDI,
        unit="USD",
        direction=Direction.POSITIVE,
        dimension=DimensionID.COMMERCIAL,
        dim_weight=0.10,
        available_from=2000,
        notes=(
            "BX.TRF.PWKR.CD.DT — remesas personales recibidas en USD corrientes. "
            "Para Venezuela superaron USD 3.5B en 2023, más que la IED. "
            "Señal de la diáspora y válvula de escape socioeconómica. "
            "WDI cubre ~2000-2022 (lag 1-2 años)."
        ),
    ),

    # ── DIMENSIÓN 3 AMPLIADA: Nuevas fuentes institucionales ─────────────────
    "vdem_libdem_index": VariableMetadata(
        column_name="vdem_libdem_index",
        description="V-Dem — Índice de Democracia Liberal (0-1)",
        source=SourceID.VDEM,
        unit="índice 0-1",
        direction=Direction.POSITIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.12,
        available_from=2000,
        notes=(
            "v2x_libdem: Índice de democracia liberal V-Dem v14. Combina "
            "democracia electoral, estado de derecho e igualdad ante la ley. "
            "Venezuela: 0.42 (2000) → 0.03 (2020). "
            "Fuente: V-Dem Institute (www.v-dem.net), Coppedge et al. (2024)."
        ),
    ),
    "fragile_states_index": VariableMetadata(
        column_name="fragile_states_index",
        description="Fragile States Index — Índice de fragilidad estatal (0-120)",
        source=SourceID.FRAGILE,
        unit="índice 0-120 (mayor=más frágil)",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.08,
        available_from=2005,
        notes=(
            "Fund for Peace FSI: 12 indicadores de fragilidad (cohesión, economía, "
            "política, social). Venezuela pasó de ~63 (2005) a ~98 (2023). "
            "Fuente: Fund for Peace (fragilestatesindex.org), descarga Excel anual."
        ),
    ),
    "wjp_rule_of_law": VariableMetadata(
        column_name="wjp_rule_of_law",
        description="WJP Rule of Law Index — Estado de derecho (0-1)",
        source=SourceID.WJP,
        unit="índice 0-1",
        direction=Direction.POSITIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.10,
        available_from=2007,
        notes=(
            "World Justice Project Rule of Law Index: gobierno abierto, ausencia de "
            "corrupción, orden y seguridad, justicia civil y penal. "
            "Venezuela: consistentemente en quintil inferior global. "
            "Fuente: worldjusticeproject.org, descarga Excel anual."
        ),
    ),
    "rsf_press_freedom": VariableMetadata(
        column_name="rsf_press_freedom",
        description="RSF — Índice de Libertad de Prensa (0-100, mayor=más libre)",
        source=SourceID.RSF,
        unit="score 0-100",
        direction=Direction.POSITIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.06,
        available_from=2002,
        notes=(
            "Reporters Without Borders World Press Freedom Index. "
            "Venezuela ocupa puesto ~159/180 en 2024. "
            "Fuente: rsf.org/index, descarga JSON/Excel anual."
        ),
    ),
    "bti_governance_index": VariableMetadata(
        column_name="bti_governance_index",
        description="BTI — Índice de Gobernanza Política (1-10)",
        source=SourceID.BTI,
        unit="índice 1-10",
        direction=Direction.POSITIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.06,
        available_from=2006,
        notes=(
            "Bertelsmann Transformation Index: calidad de gobernanza ejecutiva, "
            "democracia, estado de derecho. Bienal (años pares). "
            "Venezuela: de 4.5 (2006) a 1.8 (2024). "
            "Fuente: bti-project.org, descarga Excel."
        ),
    ),
    "basel_aml_index": VariableMetadata(
        column_name="basel_aml_index",
        description="Basel AML Index — Riesgo lavado de dinero (0-10, mayor=más riesgo)",
        source=SourceID.BASEL_AML,
        unit="índice 0-10",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.06,
        available_from=2012,
        notes=(
            "Basel Institute on Governance: riesgo de lavado de activos y "
            "financiamiento del terrorismo (17 indicadores). "
            "Venezuela consistentemente en top 10 países de mayor riesgo global. "
            "Fuente: baselgovernance.org/basel-aml-index, descarga Excel."
        ),
    ),
    "ucdp_conflicto_idx": VariableMetadata(
        column_name="ucdp_conflicto_idx",
        description="UCDP — Muertes por conflicto armado (per cápita, normalizado)",
        source=SourceID.UCDP,
        unit="muertes por 100k habitantes",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.INSTITUTIONAL,
        dim_weight=0.05,
        available_from=2000,
        notes=(
            "Uppsala Conflict Data Program: muertes anuales por conflicto "
            "armado organizado (estado + no-estado + violencia unilateral). "
            "Normalizado per cápita sobre población venezolana. "
            "Fuente: ucdp.uu.se, descarga CSV directa (sin auth)."
        ),
    ),

    # ── DIMENSIÓN 5 AMPLIADA: Capital humano y seguridad alimentaria ──────────
    "ghi_score": VariableMetadata(
        column_name="ghi_score",
        description="GHI — Índice de Hambre Global (0-100, mayor=más hambre)",
        source=SourceID.GHI,
        unit="score 0-100",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.HUMAN,
        dim_weight=0.08,
        available_from=2000,
        notes=(
            "Global Hunger Index: desnutrición, retraso de crecimiento infantil, "
            "emaciación infantil y mortalidad infantil. Venezuela pasó de 'bajo' "
            "a 'serio' entre 2000 y 2022. "
            "Fuente: globalhungerindex.org, descarga Excel anual."
        ),
    ),
    "fao_calorias_per_capita": VariableMetadata(
        column_name="fao_calorias_per_capita",
        description="FAO — Disponibilidad calórica per cápita (kcal/día)",
        source=SourceID.FAO,
        unit="kcal/persona/día",
        direction=Direction.POSITIVE,
        dimension=DimensionID.HUMAN,
        dim_weight=0.06,
        available_from=2000,
        notes=(
            "FAO Food Balance Sheets: disponibilidad total de alimentos per cápita. "
            "Venezuela cayó de ~2,700 kcal (2000) a ~1,900 kcal (2018). "
            "Fuente: FAO FAOSTAT (fao.org/faostat), API pública."
        ),
    ),
    "ilo_empleo_informal_pct": VariableMetadata(
        column_name="ilo_empleo_informal_pct",
        description="ILO — Empleo informal (% del empleo total)",
        source=SourceID.ILOSTAT,
        unit="%",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.HUMAN,
        dim_weight=0.06,
        available_from=2000,
        notes=(
            "ILO ILOSTAT: proporción del empleo en economía informal. "
            "Proxy de vulnerabilidad laboral y falta de protección social. "
            "Venezuela ~50-60% informal incluso antes de la crisis. "
            "Fuente: ilostat.ilo.org API (EMP_2EMP_SEX_ECO_NB_A)."
        ),
    ),

    # ── DIMENSIÓN 6: PERCEPCIÓN INTERNACIONAL (10% del ICIV) ─────────────────
    "guardian_tono_titulares": VariableMetadata(
        column_name="guardian_tono_titulares",
        description="Guardian — Tono de titulares (VADER)",
        source=SourceID.GUARDIAN,
        unit="VADER compound -1..+1",
        direction=Direction.POSITIVE,
        dimension=DimensionID.PERCEPTION,
        dim_weight=0.45,
        available_from=2000,
        notes=(
            "Promedio del compound score VADER sobre los 50 titulares más "
            "recientes de cada año. Score positivo = cobertura favorable."
        ),
    ),
    "guardian_articulos_venezuela": VariableMetadata(
        column_name="guardian_articulos_venezuela",
        description="Guardian — Volumen de cobertura (artículos/año)",
        source=SourceID.GUARDIAN,
        unit="n° artículos",
        direction=Direction.NEGATIVE,
        dimension=DimensionID.PERCEPTION,
        dim_weight=0.25,
        available_from=2000,
        notes=(
            "Alta cobertura internacional correlaciona con crisis "
            "políticas/económicas — proxy inverso de estabilidad."
        ),
    ),
}


def get_variables_by_dimension(dim: DimensionID) -> list[str]:
    """Devuelve los nombres de columnas que pertenecen a una dimensión."""
    return [name for name, meta in CATALOG.items() if meta.dimension == dim]


def get_negative_variables() -> list[str]:
    """Variables de dirección negativa (deben invertirse al normalizar)."""
    return [name for name, meta in CATALOG.items() if meta.direction == Direction.NEGATIVE]


def get_catalog_summary() -> list[dict]:
    """Resumen tabular del catálogo, útil para reportes."""
    return [
        {
            "variable": name,
            "descripción": meta.description,
            "fuente": meta.source.value,
            "dimensión": meta.dimension.value,
            "peso_dim": meta.dim_weight,
            "dirección": meta.direction.value,
            "desde": meta.available_from,
        }
        for name, meta in CATALOG.items()
    ]
