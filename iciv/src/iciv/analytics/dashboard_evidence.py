"""Audit surface built from the same artifacts used by the public index."""
from html import escape
import pandas as pd

def evidence_panel(settings, annual, forecast):
    def table(df):
        return '<div style="overflow:auto">'+df.to_html(index=False, border=0, na_rep='—', float_format=lambda x:f'{x:.4g}', classes='audit-table')+'</div>'
    def panel(title, text, content=''):
        return f'<div class="panel"><div class="block-title">{escape(title)}</div><p class="block-sub">{escape(text)}</p>{content}</div>'
    out=panel('Una versión, una cadena de evidencia',
              'Versión metodológica 2.0. Los datos originales, transformaciones, cobertura y resultados se exportan juntos. Generar el dashboard no equivale a refrescar las fuentes.')
    links=[('iciv_dataset_largo.csv','Datos originales y trazabilidad'),('data_dictionary.csv','Diccionario y pesos efectivos'),
           ('coverage_annual.csv','Cobertura por variable'),('manifest.json','Manifiesto y hashes'),('run_status.json','Estado de ejecución'),
           ('external_validation_summary.csv','Validación externa'),('pulse_forecast_backtest.csv','Backtest por origen'),('forecast.json','Pronóstico y diagnósticos'),('iciv_validacion.html','Informe de sensibilidad')]
    out+=panel('Descargar y reproducir','Los archivos pertenecen a la release latest. Congela una release antes de citar resultados.',
        '<ul>'+''.join(f'<li><a style="color:var(--accent)" href="iciv/data/releases/latest/{path}">{escape(label)}</a></li>' for path,label in links)+'</ul>')
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
    out+=panel('Límites abiertos y exclusiones',
        'Los pesos y umbrales son supuestos del autor. Faltan vintages históricos de publicación. WEO incluye estimaciones y proyecciones cuyo estado individual no siempre está desagregado. El histórico satelital sin QA acreditado está excluido del score; su mapa se conserva como contexto. CPI anterior a 2012 y asignaciones duplicadas de ediciones WJP quedan fuera.')
    return '<style>.audit-table{width:100%;border-collapse:collapse;font-size:.78rem}.audit-table td,.audit-table th{padding:10px;text-align:left;border-bottom:1px solid var(--border)}.audit-table th{color:var(--accent)}</style>'+out
