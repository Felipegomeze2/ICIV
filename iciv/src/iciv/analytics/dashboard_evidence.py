"""Audit surface built from the same artifacts used by the public index."""
from html import escape
import json
import pandas as pd

def evidence_panel(settings, annual, forecast):
    def table(df):
        return '<div style="overflow:auto">'+df.to_html(index=False, border=0, na_rep='—', float_format=lambda x:f'{x:.4g}', classes='audit-table')+'</div>'
    def panel(title, text, content=''):
        return f'<div class="panel"><div class="block-title">{escape(title)}</div><p class="block-sub">{escape(text)}</p>{content}</div>'
    out=panel('Una versión, una cadena de evidencia',
              'Versión metodológica 2.0. Los datos originales, transformaciones, cobertura y resultados se exportan juntos. Generar el dashboard no equivale a refrescar las fuentes.')
    links=[('iciv_dataset_largo.csv','Datos originales y trazabilidad'),('run_status.json','Estado de ejecución'),
           ('external_validation_summary.csv','Validación externa'),('pulse_forecast_backtest.csv','Backtest por origen'),('forecast.json','Pronóstico y diagnósticos'),('iciv_validacion.html','Informe de sensibilidad')]
    out+=panel('Descargar evidencia de esta ejecución','Archivos de trabajo en processed. La release anterior se conserva por separado; no representa automáticamente esta revisión.',
        '<ul>'+''.join(f'<li><a style="color:var(--accent)" href="iciv/data/processed/{path}">{escape(label)}</a></li>' for path,label in links)+'</ul>'
        '<p><a href="iciv/data/releases/latest/manifest.json">Manifiesto de la release anterior</a> · <a href="docs/VALIDACION_PENDIENTE.md">Decisiones para validar</a></p>')
    out+=panel('Cobertura efectiva del índice anual','Es el peso del universo fijo que realmente participa después del piso dimensional. No mide certeza ni independencia de la fuente.',
               table(annual[['año','iciv_score','cobertura_observada_pct','cobertura_efectiva_pct','dimensiones_publicadas']].tail(6)))
    result=settings.paths.data_processed/'external_validation_summary.csv'
    if result.exists():
        data=pd.read_csv(result)
        rows=data[data.test.eq('ICIV_vs_IED_neta')][['representacion','n','pearson_r','hac_p_holm','veredicto']]
        out+=panel('Contraste con inversión extranjera directa','Mismo modelo AHP. Niveles y diferencias, HAC y ajuste Holm. Asociación exploratoria: no demuestra causalidad ni rentabilidad.',table(rows))
    bt=forecast.get('backtest',{})
    if bt.get('summary'):
        out+=panel('Evaluación mensual comparable',
                   f"Último vintage retrospectivo. {bt.get('n_failures',0)} predicciones candidatas no disponibles se registran por separado. Todos los modelos usan los mismos pares origen/horizonte en esta tabla.",
                   table(pd.DataFrame(bt['summary'])[['model','horizon','n','mae','rmse']]))
    origin=forecast.get('forecast',{}).get('origin_date','sin origen elegible')
    out+=panel('Estado del pronóstico',f'Persistencia prespecificada desde {origin}. Sus bandas son empíricas; no son garantía de cobertura futura. No se introduce ninguna predicción en el dataset observado.')
    audit=settings.paths.data_raw.parent/'sources/audit_20260917/summary.json'
    if audit.exists():
        a=json.loads(audit.read_text(encoding='utf-8'))
        out+=panel('Contraste de fuentes archivado',
            f"{a['matching']} de {a['compared']} valores contrastados coinciden con la precisión declarada. Alcance: CPI desde 2012, WJP, Freedom House, HDI vía OWID y WEO. No certifica todas las fuentes ni su independencia. {len(a['issues'])} incidencias de verificación.",
            '<p><a href="iciv/data/sources/audit_20260917/comparisons.csv">Comparaciones por observación</a> · <a href="docs/AUDITORIA_FUENTES_ACTUAL.md">Interpretación y límites</a></p>')
    robust=settings.paths.data_processed/'robustness_summary.csv'
    if robust.exists():
        r=pd.read_csv(robust)
        top=r[r.muestra.eq('base_cobertura80')].sort_values('mae_vs_base',ascending=False).head(8)
        out+=panel('Robustez ante decisiones metodológicas',
            f"{r.escenario.nunique()} alternativas deterministas; no son datos simulados ni intervalos de confianza. Esta tabla utiliza años con cobertura base ≥80% y resultados comparables.",
            table(top[['escenario','n','mae_vs_base','max_abs_vs_base','spearman','cambios_categoria']])+
            '<p><a href="iciv/data/processed/robustness_summary.csv">Resultados completos</a> · <a href="docs/ROBUSTEZ_AMPLIADA.md">Protocolo e interpretación</a></p>')
    composition=settings.paths.data_processed/'annual_composition.csv'
    if composition.exists():
        out+=panel('Cambio anual y composición',
            'La canasta común fija los indicadores disponibles en ambos años. El residuo de composición no demuestra causas económicas.',
            table(pd.read_csv(composition).tail(5)))
    out+=panel('Límites abiertos y exclusiones',
        'Los pesos y umbrales son supuestos del autor pendientes de revisión académica. Faltan vintages históricos de publicación. El estado WEO se acredita por observación cuando coincide con el archivo oficial auditado. Luminosidad queda fuera del score por cobertura espacial y temporal insuficientemente validada, incluso cuando un píxel supera QA. El mapa histórico es contexto sin QA certificado. CPI anterior a 2012 y asignaciones duplicadas de ediciones WJP quedan fuera.')
    return '<style>.audit-table{width:100%;border-collapse:collapse;font-size:.78rem}.audit-table td,.audit-table th{padding:10px;text-align:left;border-bottom:1px solid var(--border)}.audit-table th{color:var(--accent)}</style>'+out
