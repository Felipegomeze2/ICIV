"""
Validacion de agregaciones Black Marble vs serie anual Li et al.

Pregunta: cual agregacion mensual de la radiancia VNP46A3 (media, mediana,
log-media, p90, fraccion iluminada) correlaciona mejor con la serie anual
armonizada de Li et al. (data/raw/viirs.csv), que ya alimenta el score
anual? La hipotesis es que la mediana / log-media / fraccion iluminada, al
atenuar el flaring petrolero del Orinoco, capturan mejor la actividad
economica real que la media aritmetica.

Metodo: se agrega cada variable mensual a promedio anual (solo anos con 12
meses completos) y se correlaciona (Pearson y Spearman) contra Li et al. en
el periodo comun.

Salida: data/processed/blackmarble_validation.csv
Uso:    python scripts/validate_blackmarble.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

_ICIV_DIR = Path(__file__).resolve().parents[1]
BM   = _ICIV_DIR / "data" / "raw" / "blackmarble_monthly.csv"
LI   = _ICIV_DIR / "data" / "raw" / "viirs.csv"
OUT  = _ICIV_DIR / "data" / "processed" / "blackmarble_validation.csv"

_LABELS = {
    "luminosidad_nocturna_mensual_nwcm2sr": "Media aritmetica",
    "luminosidad_nocturna_mediana":         "Mediana",
    "luminosidad_nocturna_logmedia":        "Log-media (geometrica)",
    "luminosidad_nocturna_p90":             "Percentil 90",
    "luminosidad_nocturna_frac_iluminada":  "Fraccion iluminada (%)",
}


def main() -> None:
    if not BM.exists():
        print("  blackmarble_monthly.csv no existe.")
        return
    bm = pd.read_csv(BM)
    li = pd.read_csv(LI)[["año", "valor"]].rename(columns={"valor": "li"})

    rows = []
    print("=" * 68)
    print("  Validacion Black Marble vs Li et al. (anual)")
    print("=" * 68)
    for var, label in _LABELS.items():
        sub = bm[bm["variable"] == var]
        if sub.empty:
            continue
        counts = sub.groupby("año")["mes"].count()
        full_years = counts[counts == 12].index
        ann = sub[sub["año"].isin(full_years)].groupby("año")["valor"].mean().reset_index()
        m = ann.merge(li, on="año")
        if len(m) < 4:
            continue
        rp, pp = pearsonr(m["valor"], m["li"])
        rs, ps = spearmanr(m["valor"], m["li"])
        rows.append({
            "agregacion": label, "variable": var, "n_años": len(m),
            "pearson_r": round(rp, 4), "pearson_p": round(pp, 4),
            "spearman_rho": round(rs, 4), "spearman_p": round(ps, 4),
        })
        print(f"  {label:26s} n={len(m):2d}  Pearson r={rp:+.3f} (p={pp:.3f})  "
              f"Spearman rho={rs:+.3f} (p={ps:.3f})")

    if not rows:
        print("  Sin variables suficientes (¿falta reprocesar con --reprocess?).")
        return
    df = pd.DataFrame(rows).sort_values("pearson_r", key=lambda s: s.abs(), ascending=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    best = df.iloc[0]
    print("-" * 68)
    print(f"  Mejor agregacion: {best['agregacion']} (Pearson r={best['pearson_r']:+.3f})")
    print(f"  Guardado: {OUT}")


if __name__ == "__main__":
    main()
