"""
Investment Entry Radar Sectorial (IERS)

Transforma el ICIV macro en una herramienta de decisión empresarial por sector.
Para cada sector calcula:
  - Score base: promedio ponderado de dimension scores según sensibilidad sectorial
  - Ajustadores: penalizacion regulatoria, penalizacion CAPEX, bonus demanda defensiva
  - Recomendación categórica (NO ENTRAR → PRIORITARIA)
  - Riesgo principal dominante
  - Racional ejecutivo (determinístico, basado en plantillas)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "data" / "config" / "sector_weights.json"

DIM_COLS = [
    "D1_macro",
    "D2_energia",
    "D3_institucional",
    "D4_comercial",
    "D5_capital_humano",
    "D6_percepcion",
]

DIM_LABELS = {
    "D1_macro":          "Estabilidad Macroeconómica",
    "D2_energia":        "Sector Energético",
    "D3_institucional":  "Entorno Institucional",
    "D4_comercial":      "Apertura Comercial",
    "D5_capital_humano": "Capital Humano",
    "D6_percepcion":     "Percepción Internacional",
}

# ── Plantillas de racional ────────────────────────────────────────────────────

_RATIONALE_TEMPLATES: dict[str, list[str]] = {
    "NO ENTRAR": [
        (
            "{label} no presenta condiciones mínimas de entrada en el entorno actual. "
            "La combinación de {riesgo_dim} ({dim_score:.0f}/100) y exposición {sancion_nivel} "
            "a sanciones genera un perfil de riesgo que supera el retorno esperado."
        ),
        (
            "La alta intensidad de capital requerida en {descripcion_sector} —sin "
            "protección contractual robusta— hace inviable la inversión hasta que "
            "{dim_debil_label} supere al menos los 40 puntos."
        ),
    ],
    "ESPERAR": [
        (
            "{label} muestra señales de deterioro que aún no se han estabilizado. "
            "El principal obstáculo es {riesgo_principal} "
            "(dimensión {dim_debil_label}: {dim_score:.0f}/100). "
            "Se recomienda monitoreo trimestral sin compromisos de capital."
        ),
        (
            "Con un ICIV general de {iciv_actual:.1f}/100, las condiciones en "
            "{descripcion_sector} son restrictivas pero no permanentes. "
            "El sector podría escalar a 'Piloto' si {dim_debil_label} mejora ≥ 5 puntos."
        ),
    ],
    "PILOTO": [
        (
            "{label} ofrece una ventana de entrada con estructura piloto. "
            "La fortaleza relativa de {dim_fuerte_label} ({dim_fuerte_score:.0f}/100) "
            "compensa parcialmente el {riesgo_principal}. "
            "Se recomienda operación dolarizada con exposición de capital limitada."
        ),
        (
            "La demanda {demanda_adj} en {descripcion_sector} genera resiliencia "
            "ante la volatilidad macroeconómica (ICIV={iciv_actual:.1f}). "
            "Sin embargo, {riesgo_principal} exige contratos de corto plazo "
            "y mecanismos de salida definidos."
        ),
    ],
    "ENTRADA": [
        (
            "{label} presenta condiciones favorables para entrada con mitigantes de riesgo. "
            "{dim_fuerte_label} ({dim_fuerte_score:.0f}/100) lidera el perfil positivo del sector. "
            "Se sugiere estructura de JV local o distribuidor establecido para gestionar "
            "el {riesgo_principal}."
        ),
        (
            "Con exposición {sancion_nivel} a sanciones y demanda {demanda_adj}, "
            "{descripcion_sector} representa una oportunidad de posicionamiento anticipado. "
            "El flujo de caja debe diseñarse para absorber volatilidad cambiaria."
        ),
    ],
    "PRIORITARIA": [
        (
            "{label} es el sector con mayor atractivo de entrada en el entorno actual. "
            "Combina {dim_fuerte_label} sólido ({dim_fuerte_score:.0f}/100), "
            "demanda {demanda_adj} y exposición {sancion_nivel} a riesgo sancionatorio. "
            "Momento óptimo para compromisos de mediano plazo."
        ),
    ],
}

_DEMANDA_ADJ_TEXTO = {"alta": "defensiva y estructuralmente resiliente", "media": "moderadamente resiliente", "baja": "cíclica y sensible al entorno"}
_SANCION_ADJ_TEXTO = {"alta": "alta", "media": "moderada", "baja": "baja"}


class SectorRadar:
    """
    Motor del Investment Entry Radar Sectorial.

    Uso:
        engine = SectorRadar(df_scores, config)
        data   = engine.compute_all()
    """

    def __init__(
        self,
        df_scores: pd.DataFrame,
        config: dict | None = None,
        riesgo_regulatorio_count: int = 0,
    ) -> None:
        """
        Parameters
        ----------
        df_scores : DataFrame con columnas [año, D1_macro, …, D6_percepcion, iciv_score]
        config    : dict cargado de sector_weights.json (se carga automáticamente si None)
        riesgo_regulatorio_count : parametro legado; se mantiene en cero en la version vigente
        """
        if config is None:
            config = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        self.cfg = config
        self.sectores = config["sectores"]
        self.params = config["parametros_ajustadores"]
        self.categorias = config["categorias"]
        self.riesgo_dim_map = config["mapa_riesgo_dimension"]
        self.riesgo_regulatorio_count = riesgo_regulatorio_count

        # Asegurar que el DataFrame tenga todas las columnas necesarias
        df = df_scores.copy()
        if "año" not in df.columns and df.index.name == "año":
            df = df.reset_index()
        # Requiere solo iciv_score para filtrar
        df = df.dropna(subset=["iciv_score"]).copy()
        # CERO datos artificiales: dimensiones NaN se mantienen NaN.
        # El radar visualizará 0/sin dato para esos ejes — comportamiento honesto.
        # NOTA: anteriormente se imputaba con iciv_score, lo cual creaba datos
        # artificiales para dimensiones sin información real ese año.
        for d in DIM_COLS:
            if d not in df.columns:
                df[d] = pd.NA
        df["año"] = df["año"].astype(int)
        self.df = df.sort_values("año").reset_index(drop=True)

        self.años = self.df["año"].tolist()
        complete_years = self.df.dropna(subset=DIM_COLS)["año"].tolist()
        # Radar sectorial requiere perfil dimensional completo; no fuerza el
        # ultimo año provisional si las fuentes anuales aun no publicaron.
        self.año_actual = complete_years[-1] if complete_years else self.años[-1]
        self.iciv_actual = float(self.df.loc[self.df["año"] == self.año_actual, "iciv_score"].iloc[0])

    # ── API pública ───────────────────────────────────────────────────────────

    def compute_all(self) -> dict:
        """Calcula el radar sectorial para todos los años y sectores."""

        # Dimension scores del año actual
        row_actual = self.df[self.df["año"] == self.año_actual].iloc[0]
        dim_actual = {d: float(row_actual[d]) for d in DIM_COLS}

        # Histórico por sector (None cuando NaN en alguna dim crítica)
        series_hist: dict[str, list] = {sid: [] for sid in self.sectores}
        for _, row in self.df.iterrows():
            dim_row = {d: (float(row[d]) if (row[d] is not None
                            and not (isinstance(row[d], float) and row[d] != row[d]))
                          else None)
                       for d in DIM_COLS}
            iciv_row = float(row["iciv_score"])
            for sid, scfg in self.sectores.items():
                score = self._final_score(scfg, dim_row, iciv_row)
                series_hist[sid].append(round(score, 2) if score == score else None)

        # Ranking del año actual
        ranking = []
        # Detectar dimensiones con dato real (no NaN) en el año actual
        dims_disponibles = [d for d, v in dim_actual.items()
                           if v is not None and not (isinstance(v, float) and v != v)]
        cobertura_dims = len(dims_disponibles) / len(DIM_COLS)

        for sid, scfg in self.sectores.items():
            base_raw = self._base_score(scfg, dim_actual)
            # D3 may be NaN → neutral sanction penalty
            d3 = dim_actual.get("D3_institucional")
            if d3 is None or (isinstance(d3, float) and d3 != d3):
                sp = 0.0
            else:
                sp = self._sanction_penalty(scfg, d3)
            cp = self._capex_penalty(scfg, self.iciv_actual) if base_raw == base_raw else 0.0
            db = self._defensive_bonus(scfg)

            if base_raw != base_raw:  # NaN — datos insuficientes
                final = None
                base = None
                rec = {"label": "Datos insuficientes", "short": "SIN DATOS",
                       "color": "#8b949e", "hex": "#8b949e"}
            else:
                base = base_raw
                final = round(max(0.0, min(100.0, base - sp - cp + db)), 2)
                rec = self._get_recommendation(final)

            weighted = {d: (round(dim_actual[d] * scfg["pesos"][d], 2)
                            if (dim_actual.get(d) is not None
                                and not (isinstance(dim_actual.get(d), float) and dim_actual.get(d) != dim_actual.get(d)))
                            else None)
                        for d in DIM_COLS}
            riesgo = self._get_main_risk(sid, scfg, dim_actual, weighted, final or 0)
            racional = self._generate_rationale(sid, scfg, final or 0, rec, riesgo, dim_actual)

            ranking.append({
                "sector_id": sid,
                "label": scfg["label"],
                "label_corto": scfg["label_corto"],
                "score": final,
                "score_base": round(base, 2) if base is not None else None,
                "penalizacion_sancion": round(sp, 2),
                "penalizacion_capex": round(cp, 2),
                "bonus_defensivo": round(db, 2),
                "recomendacion": rec["label"],
                "recomendacion_short": rec["short"],
                "color": rec["color"],
                "hex": rec["hex"],
                "riesgo_principal": riesgo,
                "racional": racional,
                "pesos": scfg["pesos"],
                "scores_dim_ponderados": weighted,
                "ajustadores": scfg["ajustadores"],
            })

        # Ordenar: scores válidos descendente, SIN DATOS al final
        ranking.sort(key=lambda x: (x["score"] is None, -(x["score"] or 0)))
        for i, r in enumerate(ranking, 1):
            r["rank"] = i

        # Resumen por categoría (incluye SIN DATOS)
        resumen = {"NO ENTRAR": 0, "ESPERAR": 0, "PILOTO": 0, "ENTRADA": 0,
                   "PRIORITARIA": 0, "SIN DATOS": 0}
        for r in ranking:
            k = r["recomendacion_short"]
            if k in resumen:
                resumen[k] += 1

        return {
            "año_actual": self.año_actual,
            "iciv_actual": round(self.iciv_actual, 2),
            "dim_scores_actuales": {d: round(dim_actual[d], 2) for d in DIM_COLS},
            "ranking": ranking,
            "resumen_categorias": resumen,
            "series_historicas": {
                "años": self.años,
                "sectores": series_hist,
            },
            "sector_labels": {sid: scfg["label"] for sid, scfg in self.sectores.items()},
            "categorias": self.categorias,
            "metodologia": (
                "Investment Entry Radar Sectorial v1.0. "
                "Score base = Σ DimScore(d) × PesoSectorial(s,d). "
                "Ajustadores: penalizacion regulatoria, penalizacion CAPEX "
                "(escala con ICIV < 50), bonus de demanda defensiva. "
                f"ICIV actual: {self.iciv_actual:.1f}/100. "
                "Umbrales: ≤35 No entrar · 36-50 Esperar · 51-65 Piloto · "
                "66-80 Entrada · >80 Prioritaria."
            ),
        }

    # ── Score base ────────────────────────────────────────────────────────────

    def _base_score(self, sector_cfg: dict, dim_scores: dict) -> float:
        """
        Promedio ponderado de dims con redistribución cuando hay NaN.
        Si una dimensión es NaN, se EXCLUYE y los pesos se renormalizan
        sobre las dims disponibles (igual lógica que aggregator ICIV).
        Si TODAS son NaN, retorna NaN (sin datos suficientes).
        """
        total_weight = 0.0
        weighted_sum = 0.0
        for d in DIM_COLS:
            v = dim_scores.get(d)
            if v is None or (isinstance(v, float) and (v != v)):  # NaN check
                continue
            w = sector_cfg["pesos"][d]
            weighted_sum += v * w
            total_weight += w
        if total_weight < 0.5:  # menos del 50% del peso AHP disponible
            return float("nan")
        return weighted_sum / total_weight

    def _final_score(self, sector_cfg: dict, dim_scores: dict, iciv: float) -> float:
        base = self._base_score(sector_cfg, dim_scores)
        if base != base:  # NaN
            return float("nan")
        # D3 puede ser NaN → la penalización se asume neutra
        d3 = dim_scores.get("D3_institucional")
        if d3 is None or (isinstance(d3, float) and d3 != d3):
            sp = 0.0
        else:
            sp = self._sanction_penalty(sector_cfg, d3)
        cp = self._capex_penalty(sector_cfg, iciv)
        db = self._defensive_bonus(sector_cfg)
        return max(0.0, min(100.0, base - sp - cp + db))

    # ── Ajustadores ──────────────────────────────────────────────────────────

    def _sanction_penalty(self, sector_cfg: dict, d3_score: float) -> float:
        """
        Penalizacion por exposicion regulatoria e institucional.
        Se escala con la debilidad institucional (D3 bajo → mayor impacto).
        Máx cuando D3 = 0; mínimo cuando D3 ≥ 80.
        """
        nivel = sector_cfg["ajustadores"]["sancion"]
        base_penalty = self.params["sancion"][nivel]
        # Escalar por debilidad institucional: D3 muy bajo amplifica el riesgo
        inst_factor = max(0.0, (80.0 - d3_score) / 80.0)
        return base_penalty * inst_factor

    def _capex_penalty(self, sector_cfg: dict, iciv_score: float) -> float:
        """
        Penalización por alta intensidad de capital cuando el ICIV está bajo.
        Solo activa cuando ICIV < umbral; escala linealmente.
        """
        nivel = sector_cfg["ajustadores"]["capex"]
        max_penalty = self.params["capex"][nivel]
        umbral = self.params["capex"]["iciv_umbral"]
        if max_penalty == 0 or iciv_score >= umbral:
            return 0.0
        factor = (umbral - iciv_score) / umbral
        return max_penalty * factor

    def _defensive_bonus(self, sector_cfg: dict) -> float:
        """Bonus fijo por resiliencia de demanda en contextos de crisis."""
        nivel = sector_cfg["ajustadores"]["demanda_defensiva"]
        return float(self.params["demanda_defensiva"][nivel])

    # ── Recomendación ─────────────────────────────────────────────────────────

    def _get_recommendation(self, score: float) -> dict:
        # Recorre en orden descendente; devuelve la primera categoría cuyo umbral
        # mínimo el score supera — evita gaps entre rangos enteros con scores decimales.
        for cat in reversed(self.categorias):
            if score >= cat["min"]:
                return cat
        return self.categorias[0]  # fallback: más conservadora

    # ── Riesgo principal ──────────────────────────────────────────────────────

    def _get_main_risk(
        self,
        sector_id: str,
        sector_cfg: dict,
        dim_scores: dict,
        weighted: dict,
        final_score: float,
    ) -> str:
        """
        Identifica el riesgo dominante combinando:
        1. Dimensión con menor contribución ponderada (score × peso)
        2. Exposicion regulatoria del sector
        3. Candidatos de riesgo propios del sector
        """
        # Forzar riesgo sancionatorio si exposición alta y score bajo
        if sector_cfg["ajustadores"]["sancion"] == "alta" and final_score < 55:
            return "Riesgo sancionatorio"

        # Dimensión con menor contribución ponderada (excluir dimensiones con peso 0 o sin dato)
        dim_activas = {d: weighted[d] for d in DIM_COLS
                       if sector_cfg["pesos"][d] > 0 and weighted.get(d) is not None}
        if not dim_activas:
            return sector_cfg["riesgos_candidatos"][0]

        dim_debil = min(dim_activas, key=dim_activas.get)

        # Usar riesgo del candidato si coincide con la dimensión débil
        candidatos = sector_cfg["riesgos_candidatos"]
        riesgo_dim = self.riesgo_dim_map.get(dim_debil, "Riesgo operacional")

        # Heurística: si D3 está entre las 2 peores y hay candidato institucional
        dim_sorted = sorted(dim_activas, key=dim_activas.get)
        if "D3_institucional" in dim_sorted[:2] and any("institucional" in c or "contractual" in c for c in candidatos):
            return next(c for c in candidatos if "institucional" in c or "contractual" in c)

        return riesgo_dim

    # ── Racional ejecutivo ────────────────────────────────────────────────────

    def _generate_rationale(
        self,
        sector_id: str,
        sector_cfg: dict,
        score: float,
        rec: dict,
        riesgo: str,
        dim_scores: dict,
    ) -> str:
        short = rec["short"]
        templates = _RATIONALE_TEMPLATES.get(short, _RATIONALE_TEMPLATES["ESPERAR"])
        template = templates[hash(sector_id) % len(templates)]

        # Dimensión más fuerte y más débil (con peso > 0)
        pesos = sector_cfg["pesos"]
        activas = [(d, dim_scores[d] * pesos[d]) for d in DIM_COLS if pesos[d] > 0]
        activas_sorted = sorted(activas, key=lambda x: x[1], reverse=True)
        dim_fuerte_id = activas_sorted[0][0]
        dim_debil_id = activas_sorted[-1][0]

        context = {
            "label": sector_cfg["label"],
            "descripcion_sector": sector_cfg["descripcion_sector"],
            "riesgo_principal": riesgo,
            "riesgo_dim": self.riesgo_dim_map.get(dim_debil_id, "riesgo operacional"),
            "dim_fuerte_label": DIM_LABELS[dim_fuerte_id],
            "dim_fuerte_score": dim_scores[dim_fuerte_id],
            "dim_debil_label": DIM_LABELS[dim_debil_id],
            "dim_score": dim_scores[dim_debil_id],
            "iciv_actual": self.iciv_actual,
            "sancion_nivel": _SANCION_ADJ_TEXTO[sector_cfg["ajustadores"]["sancion"]],
            "demanda_adj": _DEMANDA_ADJ_TEXTO[sector_cfg["ajustadores"]["demanda_defensiva"]],
        }
        try:
            return template.format(**context)
        except KeyError:
            return (
                f"{sector_cfg['label']}: score {score:.1f}/100 — "
                f"Recomendación: {rec['label']}. Riesgo principal: {riesgo}."
            )
