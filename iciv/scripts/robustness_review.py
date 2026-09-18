"""Generate working robustness evidence without freezing or altering releases."""
from pathlib import Path
import sys
import json
import hashlib
import logging
from datetime import datetime, timezone
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from iciv.analytics.robustness import evaluate_scenarios

def main():
    logging.getLogger("iciv.index.aggregator").setLevel(logging.WARNING)
    processed = ROOT / "data/processed"
    files = [processed/"iciv_normalizado.csv", processed/"iciv_transformado.csv"]
    verified = ROOT / "data/sources/audit_20260917/verified_observations.csv"
    status = pd.read_csv(verified) if verified.exists() else None
    if status is not None:
        # Metadata may only describe the exact raw snapshot that was compared.
        hashes = {n: (hashlib.sha256((ROOT/"data/raw"/n).read_bytes()).hexdigest(),
                      hashlib.sha256((ROOT/"data/raw"/n).read_bytes().replace(b"\r\n",b"\n")).hexdigest())
                  for n in status.archivo_origen.unique()}
        status = status[status.apply(lambda r: hashes[r.archivo_origen][0] == r.raw_sha256
                                    or hashes[r.archivo_origen][1] == r.get("raw_canonical_lf_sha256"), axis=1)]
        files.append(verified)
    summary, detail, changes = evaluate_scenarios(pd.read_csv(files[0]), pd.read_csv(files[1]), status)
    for name, data in (("robustness_summary", summary), ("robustness_scenarios", detail), ("annual_composition", changes)):
        data.to_csv(processed/(name+".csv"), index=False)
    meta = {"generated_at": datetime.now(timezone.utc).isoformat(), "scenarios": int(detail.escenario.nunique()),
            "inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            "interpretation": "Deterministic design alternatives. Not observations, confidence intervals or expert approval."}
    (processed/"robustness_run.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    selected = summary[summary.muestra.eq("base_cobertura80")].sort_values("mae_vs_base", ascending=False)
    lines = ["# Robustez ampliada · revisión de trabajo", "", f"Generación UTC: {meta['generated_at']}. Escenarios: {meta['scenarios']}.", "",
             "Alternativas deterministas sobre datos reales; no se generan ni rellenan observaciones. La dispersión entre diseños no es un intervalo de confianza. No se eligieron pesos para maximizar correlación con IED.", "",
             "Se varían pesos dimensionales ±5/10/20%, normalización, agregación, transformación de inflación, piso de cobertura, exclusión de cada variable y dimensión, y ausencia de datos por dimensión. Se añade la retirada de estimaciones WEO verificadas cuando existe evidencia.", "",
             "## Mayor diferencia respecto al modelo base", "", "Muestra: años con cobertura base ≥80% y score disponible en ambos diseños. El CSV también muestra todos los años comparables. Comparar n: los pisos más estrictos pueden reducirlo.", "",
             "| Escenario | n | MAE puntos | Máximo absoluto | Spearman | Cambios de categoría |", "|---|---:|---:|---:|---:|---:|"]
    for _,r in selected.head(15).iterrows():
        lines.append(f"| {r.escenario} | {r.n} | {r.mae_vs_base:.3f} | {r.max_abs_vs_base:.3f} | {r.spearman:.3f} | {r.cambios_categoria} |")
    lines += ["", "## Composición interanual", "", "La canasta común utiliza los mismos indicadores disponibles en ambos años, mantiene el universo de cobertura y aplica el piso dimensional. El residuo es el efecto neto de composición; no atribuye causas económicas.", "",
              "| Año | Cambio publicado | Cambio canasta común | Residuo composición | Cobertura común % |", "|---|---:|---:|---:|---:|"]
    for _,r in changes.tail(7).iterrows():
        lines.append(f"| {int(r['año'])} | {r.delta_publicado:.2f} | {r.delta_canasta_comun:.2f} | {r.efecto_composicion_neto:.2f} | {r.cobertura_comun_pct:.1f} |")
    lines += ["", "Artefactos: `iciv/data/processed/robustness_summary.csv`, `robustness_scenarios.csv`, `annual_composition.csv` y `robustness_run.json`.", "",
              "Referencia de protocolo: [OECD/JRC, Handbook on Constructing Composite Indicators (2008), análisis de incertidumbre y sensibilidad](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf). Las decisiones concretas y los umbrales son del proyecto; no son una certificación OECD.", ""]
    (ROOT.parent/"docs/ROBUSTEZ_AMPLIADA.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(meta, indent=2))

if __name__ == "__main__":
    main()
