"""Generate a short, synchronized report from the current run or release.

Every number in docs/RESULTADOS_ACTUALES.md is read from pipeline artifacts.
Nothing here is typed by hand, so the document cannot drift from the data.
"""
from pathlib import Path
import json
import pandas as pd


def _fmt(value, digits=4):
    return "—" if pd.isna(value) else f"{value:.{digits}f}"


def write_summary(root=None, working=False):
    root = Path(root) if root else Path(__file__).resolve().parents[2]
    release = root / ('iciv/data/processed' if working else 'iciv/data/releases/latest')
    manifest = json.loads((release / ('run_status.json' if working else 'manifest.json')).read_text(encoding='utf8'))
    annual = pd.read_csv(release / 'iciv_scores_ahp.csv')
    pulse = pd.read_csv(release / 'iciv_pulse_monthly.csv')
    bt = pd.read_csv(release / 'pulse_forecast_backtest_summary.csv')
    external = pd.read_csv(release / 'external_validation_summary.csv')
    plaus_path = root / 'iciv/data/processed/plausibilidad_proveedor.csv'
    lines = ['# Resultados actuales · ' + ('revisión de trabajo sin congelar' if working else 'generados desde la release'), '',
             f"Versión metodológica: {manifest['methodology_version']}. Generación: {manifest.get('generated_at_utc', manifest.get('generated_at'))}.",
             '', 'Documento generado automáticamente por `iciv/scripts/write_results_summary.py`. No copiar estos resultados a una entrega sin citar su manifiesto. '
                 'Anual: retrospectivo; meses provisionales y estimaciones del proveedor no son observaciones cerradas.', '',
             '## Índice anual (últimos años)', '',
             '| Año | ICIV AHP | Cobertura efectiva % | Categoría relativa | Tramo |', '|---|---:|---:|---|---|']
    for _, r in annual.tail(6).iterrows():
        tramo = r['tramo_serie'] if 'tramo_serie' in annual.columns else '—'
        lines.append(f"| {int(r['año'])} | {r.iciv_score:.2f} | {r.cobertura_pct:.1f} | {r.iciv_categoria} | {tramo} |")
    if 'tramo_serie' in annual.columns:
        official = annual[annual.tramo_serie.eq('oficial')].dropna(subset=['iciv_score'])
        if not official.empty:
            hi, lo = official.loc[official.iciv_score.idxmax()], official.loc[official.iciv_score.idxmin()]
            lines += ['', f"Serie oficial {int(official['año'].min())}–{int(official['año'].max())}: máximo {hi.iciv_score:.2f} ({int(hi['año'])}), "
                          f"mínimo {lo.iciv_score:.2f} ({int(lo['año'])}). El tramo anterior es exploratorio: no incluye la dimensión institucional."]
    eligible = pulse[pulse.elegible_modelo]
    last = pulse.dropna(subset=['pulse_score']).iloc[-1] if pulse.pulse_score.notna().any() else None
    lines += ['', '## Señal mensual (Pulse)', '']
    if last is not None:
        lines.append(f"Último mes publicado: {int(last['año'])}-{int(last['mes']):02d}, {last.pulse_score:.2f}; cobertura {last.cobertura_pct:.1f}% "
                     f"({'elegible' if last.elegible_modelo else 'provisional'}).")
    if not eligible.empty:
        r = eligible.iloc[-1]
        lines.append(f"Último mes elegible: {int(r['año'])}-{int(r['mes']):02d}, {r.pulse_score:.2f}; cobertura {r.cobertura_pct:.1f}%.")
    # Relación entre la señal mensual y el índice anual en la serie oficial:
    # promedio anual de los meses elegibles frente al score anual publicado.
    if not eligible.empty and 'tramo_serie' in annual.columns:
        yearly = eligible.groupby('año')['pulse_score'].mean()
        both = annual[annual.tramo_serie.eq('oficial') & annual.cobertura_pct.ge(70)].set_index('año')[['iciv_score']].join(
            yearly.rename('pulse_media_anual'), how='inner').dropna()
        if len(both) >= 5:
            r_lvl = both.corr().iloc[0, 1]
            diffs = both.reindex(range(int(both.index.min()), int(both.index.max()) + 1)).diff().dropna()
            r_dif = diffs.corr().iloc[0, 1] if len(diffs) >= 4 else float('nan')
            lines += ['', f"Relación con el índice anual ({int(both.index.min())}–{int(both.index.max())}, años oficiales con cobertura ≥70%, "
                          f"n={len(both)}): correlación de Pearson {r_lvl:.2f} en niveles y {_fmt(r_dif, 2)} en cambios anuales. "
                          "La señal mensual pondera condiciones externas, petróleo y prensa; no replica el índice anual."]
    lines += ['', '## Pronóstico mensual', '', 'Backtest: muestra común por horizonte, último vintage, sin simulación de publicaciones históricas. '
              'El modelo público es persistencia (naive).', '',
              '| Modelo | Horizonte meses | n | MAE | RMSE |', '|---|---:|---:|---:|---:|']
    for _, r in bt.iterrows():
        lines.append(f"| {r.model} | {int(r.horizon)} | {int(r.n)} | {r.mae:.4f} | {r.rmse:.4f} |")
    lines += ['', '## Validación externa (exploratoria)', '', 'Asociaciones retrospectivas, no causales. Holm se aplica dentro de cada tramo.', '',
              '| Contraste | Tramo | Representación | n | Pearson r | p HAC + Holm |', '|---|---|---|---:|---:|---:|']
    for _, r in external.iterrows():
        tramo = r['tramo'] if 'tramo' in external.columns else '—'
        lines.append(f"| {r.test} | {tramo} | {r.representacion} | {int(r.n)} | {_fmt(r.pearson_r)} | {_fmt(r.hac_p_holm)} |")
    if plaus_path.exists():
        plaus = pd.read_csv(plaus_path)
        if not plaus.empty:
            lines += ['', '## Valores del proveedor excluidos o marcados', '', '| Variable | Regla | Acción | Años |', '|---|---|---|---|']
            for (var, regla, accion), g in plaus.groupby(['variable', 'regla', 'accion']):
                lines.append(f"| {var} | {regla} | {accion} | {int(g['año'].min())}–{int(g['año'].max())} ({len(g)}) |")
    lines += ['', 'Luminosidad satelital (Black Marble y Li et al.) está excluida del índice; el mapa es contexto. '
              'Detalle de decisiones en `docs/METODOLOGIA.md` y `docs/CIERRE_PROYECTO.md`.', '']
    (root / 'docs/RESULTADOS_ACTUALES.md').write_text('\n'.join(lines), encoding='utf8')


if __name__ == '__main__':
    write_summary()
