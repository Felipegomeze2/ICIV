# Reproducción de la entrega final

La entrega académica es un artículo IEEE individual. La release de sus cifras conserva el identificador `tesis-2026-10b`; ese nombre histórico no implica que deba entregarse una tesis. Los documentos y sus generadores permanecen en `entregables_local/`, fuera de Git por política del proyecto.

## Verificación del paquete

Desde la raíz del repositorio, con Python 3.11 o superior:

```powershell
pip install -e "iciv/[dev]"
python iciv/scripts/verify_release.py --release iciv/data/releases/tesis-2026-10b
```

Comprueba los 62 archivos del manifiesto y reproduce normalización, AHP, cobertura y valores originales. No descarga datos ni modifica la release.

## Ejecución completa con los datos congelados

```powershell
python iciv/scripts/reproduce_release.py --release iciv/data/releases/tesis-2026-10b --output ../ICIV_reproduccion_tesis
```

La salida debe ser una carpeta nueva. El script comprueba la identidad del código registrado en el manifiesto, copia el código y los datos `raw/` de la release a ese directorio y ejecuta `main.py --no-fetch --no-open --no-package` allí. El checkout original y la release no se sobrescriben. No usa los datos crudos de la ejecución corriente.

El informe `reproduction_report.json` compara estructura, etiquetas, faltantes y valores de siete salidas: normalización, puntajes anuales, dataset largo, Pulse, validación externa, robustez y resumen del backtest. La tolerancia numérica es `rtol=1e-7`, `atol=1e-8`. Un fallo de comparación termina con error. El registro completo queda en `pipeline.log`.

Las fechas de ejecución, HTML y etiquetas de vigencia dependientes del día no se comparan por identidad binaria. La evidencia auxiliar de fuentes se copia del repositorio; el dataset largo regenerado se contrasta con el congelado para detectar cambios de estado o linaje. El entorno instalado puede afectar resultados numéricos; sus versiones originales se encuentran en `manifest.json`. Si se modifica el código del modelo, el script exige volver a la versión compatible con los hashes del manifiesto.

`python iciv/main.py --no-fetch` por sí solo utiliza `iciv/data/raw/`: reproduce el snapshot corriente, no selecciona automáticamente una release histórica.

## Interpretación del alcance

- Universo anual: 21 variables, de las cuales 20 pueden aportar al puntaje; luminosidad solo permanece en el denominador de cobertura.
- Los pesos del diccionario son nominales. La renormalización por variables y dimensiones disponibles determina la contribución efectiva en cada año.
- La serie oficial comienza en 2012, pero los años finales pueden tener dimensiones faltantes. En 2025 falta capital humano; 2026 es provisional con cobertura de 41,1 %.
- La robustez conserva principalmente el orden temporal. No acredita invariancia de niveles o categorías.
- Los contrastes externos son asociaciones retrospectivas. HAC, Holm y leave-one-out no demuestran causalidad, independencia completa de fuentes ni validez de constructo.
- No se realizaron un panel experto, anotación humana del sentimiento ni estudio de usuarios. Son limitaciones y trabajo futuro.
