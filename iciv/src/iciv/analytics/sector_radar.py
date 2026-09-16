"""Escenarios de sensibilidad a pesos, sin rendimientos ni recomendaciones.

Los perfiles son supuestos del autor, no estimaciones sectoriales empíricas.
No se calculan bonos, sanciones ni ajustes CAPEX sin datos calibrados.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from iciv.index.aggregator import _get_risk_category

DIM_COLS = ["D1_macro", "D2_energia", "D3_institucional", "D4_comercial", "D5_capital_humano", "D6_percepcion"]
_CONFIG_PATH = Path(__file__).resolve().parents[3] / "data/config/sector_weights.json"
COLORS = dict(zip(["Muy desfavorable", "Desfavorable", "Intermedio", "Favorable", "Muy favorable"],
                  ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#27ae60"]))

class SectorRadar:
    def __init__(self, df_scores, config=None, **kwargs):
        self.cfg = config or json.loads(_CONFIG_PATH.read_text(encoding="utf8"))
        self.df = df_scores.reindex(columns=["año", "iciv_score"] + DIM_COLS).sort_values("año")
        for sector in self.cfg["sectores"].values():
            weights = sector["pesos"]
            if set(weights) != set(DIM_COLS) or any(w < 0 or not np.isfinite(w) for w in weights.values()) or not np.isclose(sum(weights.values()), 1):
                raise ValueError("Los perfiles deben declarar seis pesos no negativos con suma 1")

    def _base_score(self, sector_cfg, dim_scores):
        weights = sector_cfg["pesos"]
        if any(pd.isna(dim_scores.get(d)) for d, w in weights.items() if w > 0):
            return float("nan")
        return sum(float(dim_scores[d]) * w for d, w in weights.items() if w > 0)

    def compute_all(self):
        eligible = self.df.dropna(subset=DIM_COLS + ["iciv_score"])
        if eligible.empty:
            return {"available": False, "ranking": [], "reason": "Sin un año con todas las dimensiones publicadas"}
        row = eligible.iloc[-1]
        ranking, series = [], {}
        counts = {cat: 0 for cat in COLORS}
        for sid, cfg in self.cfg["sectores"].items():
            score = self._base_score(cfg, row)
            cat = _get_risk_category(score)
            deficit = {d: (100 - row[d]) * w for d, w in cfg["pesos"].items() if w > 0}
            weak = max(deficit, key=deficit.get)
            counts[cat] += 1
            ranking.append({"sector_id": sid, "label": cfg["label"], "label_corto": cfg["label_corto"],
                            "score": round(score, 2), "score_base": round(score, 2), "hex": COLORS[cat],
                            "color": COLORS[cat], "recomendacion": cat, "recomendacion_short": cat,
                            "riesgo_principal": "Mayor déficit ponderado: " + weak,
                            "racional": "Perfil hipotético definido por pesos del autor. No mide desempeño ni atractivo inversor del sector.",
                            "pesos": cfg["pesos"], "scores_dim_ponderados": {d: row[d]*w for d,w in cfg["pesos"].items()},
                            "ajustadores": {}})
            values = [self._base_score(cfg, r) for _, r in self.df.iterrows()]
            series[sid] = [round(v, 2) if np.isfinite(v) else None for v in values]
        ranking.sort(key=lambda r: -r["score"])
        for i, r in enumerate(ranking, 1): r["rank"] = i
        return {"available": True, "año_actual": int(row["año"]), "iciv_actual": float(row["iciv_score"]),
                "dim_scores_actuales": {d: float(row[d]) for d in DIM_COLS}, "ranking": ranking,
                "resumen_categorias": counts, "series_historicas": {"años": self.df["año"].tolist(), "sectores": series},
                "sector_labels": {sid: cfg["label"] for sid,cfg in self.cfg["sectores"].items()},
                "categorias": [], "metodologia": "Sensibilidad por perfiles hipotéticos: suma de dimensiones por pesos declarados; exige todas las dimensiones. Sin ajustes manuales ni recomendación de inversión."}
