# Incidente: FRED mensual sin actualizar por la ventana móvil de ICE BofA

**Detectado y corregido:** 28 de octubre de 2026. **Período afectado:** del 9 al 28 de octubre de 2026.

## Qué pasó

La ejecución programada 45 (26 de octubre de 2026) falló en `Verificar vigencia de fuentes Pulse`, antes del pipeline y del despliegue:

```
ERROR FRED macro monthly: ultimo mes 2026-08, rezago desde cierre 56 dias; maximo permitido 50
```

La serie atrasada era `FEDFUNDS` (tasa de fondos federales). FRED ya había publicado septiembre; el problema era que `data/raw/fred_monthly.csv` no se actualizaba desde el 9 de octubre.

La causa fue `BAMLEMCBPIOAS` (spread de bonos corporativos emergentes ICE BofA). Por licencia, FRED solo distribuye una ventana móvil de unos tres años de las series ICE BofA. Cuando la ventana avanzó, la descarga dejó de traer septiembre de 2023. La guarda `save_dataframe` interpretó esa ausencia como «la descarga perdería 1 observación publicada» y rechazó **todo** el archivo, con las siete series. El fetch está envuelto en `|| echo WARN`, así que el paso de descarga terminó en verde; el control de vigencia fue el que detectó el problema y bloqueó la publicación, como está diseñado.

Las corridas del 12 y el 19 de octubre publicaron el tablero con el archivo FRED del 9 de octubre. Esas cifras usaban datos reales de FRED, pero no los más recientes.

Al revisar la corrida se encontró un caso parecido: el snapshot de titulares de The Guardian (`guardian_headlines.csv`, sección *Noticias* del tablero) no se actualizaba desde el 14 de septiembre. Es una colección móvil de texto sin columnas numéricas, y la guarda la rechazaba siempre. No afecta al índice ni al Pulse.

## Corrección

- `fetch_fred_monthly.py` declara las series de ventana móvil (`_ROLLING_WINDOW = {"em_bond_spread_pct"}`). Antes de guardar, conserva del snapshot anterior los meses de esas series que ya no vienen en la descarga. Son observaciones que FRED publicó y que el proyecto ya había descargado: no se inventa ni se interpola nada. Si un mes viene en la descarga nueva, gana el valor nuevo.
- Las demás series FRED siguen bajo la regla estricta: si una descarga pierde un mes publicado, se rechaza.
- `fetch_guardian.py` guarda el snapshot de titulares con `value_columns=["title"], allow_loss=True`, igual que `fetch_international_news.py`. `allow_loss` existe para colecciones móviles explícitas.
- Prueba de regresión: `iciv/tests/test_fred_rolling_window.py` (la ventana se conserva y el guardado pasa; otra serie que pierde un mes sigue rechazándose).

No se modificó ninguna observación ni se relajó el control de vigencia.

## Lección

Una guarda contra pérdida de datos tiene que distinguir entre colecciones históricas, donde perder un dato publicado es un error, y colecciones con ventana móvil del distribuidor, donde los datos salen de la ventana por diseño. La distinción va declarada en el fetcher de cada serie, no como una excepción global.
