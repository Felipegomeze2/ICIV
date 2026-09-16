"""Generate a short, synchronized report from the current release."""
from pathlib import Path
import json
import pandas as pd

def write_summary(root=None):
    root=Path(root) if root else Path(__file__).resolve().parents[2]
    release=root/'iciv/data/releases/latest'
    manifest=json.loads((release/'manifest.json').read_text(encoding='utf8'))
    annual=pd.read_csv(release/'iciv_scores_ahp.csv')
    pulse=pd.read_csv(release/'iciv_pulse_monthly.csv')
    bt=pd.read_csv(release/'pulse_forecast_backtest_summary.csv')
    external=pd.read_csv(release/'external_validation_summary.csv')
    lines=['# Resultados actuales · generados desde la release', '',
           f"Versión metodológica: {manifest['methodology_version']}. Generación UTC: {manifest['generated_at_utc']}.",
           '', 'No copiar estos resultados a una entrega sin citar su manifiesto. Anual: retrospectivo; meses provisionales y estimaciones del proveedor no son observaciones cerradas.', '',
           '| Año | ICIV AHP | Cobertura efectiva % | Categoría relativa |','|---|---:|---:|---|']
    for _,r in annual.tail(5).iterrows(): lines.append(f"| {int(r['año'])} | {r.iciv_score:.2f} | {r.cobertura_pct:.1f} | {r.iciv_categoria} |")
    eligible=pulse[pulse.elegible_modelo]
    if not eligible.empty:
        r=eligible.iloc[-1]
        lines += ['',f"Último Pulse elegible: {int(r['año'])}-{int(r['mes']):02d}, {r.pulse_score:.2f}; cobertura {r.cobertura_pct:.1f}%."]
    lines += ['', 'Backtest: muestra común por horizonte, último vintage, sin simulación de publicaciones históricas.', '',
              '| Modelo | Horizonte meses | n | MAE | RMSE |','|---|---:|---:|---:|---:|']
    for _,r in bt.iterrows(): lines.append(f"| {r.model} | {int(r.horizon)} | {int(r.n)} | {r.mae:.4f} | {r.rmse:.4f} |")
    lines += ['', 'IED: asociación exploratoria, no causal.', '', '| Representación | n | Pearson r | p HAC + Holm |','|---|---:|---:|---:|']
    for _,r in external[external.test.eq('ICIV_vs_IED_neta')].iterrows(): lines.append(f"| {r.representacion} | {int(r.n)} | {r.pearson_r:.4f} | {r.hac_p_holm:.4f} |")
    lines += ['', 'El histórico Black Marble sin QA acreditado está excluido del índice. Ver CIERRE_PROYECTO.md antes de presentar esta versión como final.','']
    (root/'docs/RESULTADOS_ACTUALES.md').write_text('\n'.join(lines),encoding='utf8')

if __name__=='__main__': write_summary()
