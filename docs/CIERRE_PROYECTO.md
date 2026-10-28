# Cierre técnico y académico · v2.1

Estado al 28 de octubre de 2026. Defensa prevista: 28 de noviembre de 2026.

## Sistema terminado

- Pipeline reproducible: `python iciv/main.py --no-fetch --no-open` regenera índice, Pulse, validación, robustez, dashboard y release; `verify_release.py` comprueba hashes y reproduce normalización, AHP y cobertura.
- Actualización automática semanal y mensual en GitHub Actions, con control de vigencia de fuentes y publicación en GitHub Pages.
- 90 pruebas Python y 7 pruebas JavaScript (al 28 de octubre de 2026), ejecutadas en CI.
- Política de datos aplicada en el código: solo fuentes internacionales, faltantes preservados, valores imposibles del proveedor excluidos y registrados, sin sustitución de fuentes.

## Cambios de la versión 2.1 (9 de octubre de 2026)

1. **Corrección del bloque de comercio del Pulse.** Las series FRED IR14270/IR14260 eran índices de precios de importación de oro y zinc. Se reemplazaron por las importaciones de EE.UU. desde Venezuela que publica la EIA (MCRIMUSVE2, MTPIMUSVE2), con validación de identidad en cada descarga. Ver [incidente](INCIDENTE_SERIES_COMERCIO.md).
2. **Control de plausibilidad.** Los ceros de exportaciones del Banco Mundial (2000–2011) se excluyen. La mortalidad infantil repetida 2016–2024 se marca.
3. **Serie oficial 2012–2026** y tramo exploratorio 2000–2011 declarado en datos, dashboard, laboratorio y figura de defensa.
4. **Validación externa por tramo** (serie oficial y serie completa).
5. **Semáforo SATV visible** en la portada, leído en el último mes elegible.
6. **Evidencia sincronizada:** la corrida automática publica `data/processed` y los resultados junto con el dashboard.
7. **Documentación alineada** y figura de defensa regenerada con categorías v2 y eventos de 2026.
8. **Alcance descartado formalizado** (ver abajo).

## Alcance descartado (trabajo futuro)

Escenarios prospectivos 2027–2030, simulación Monte Carlo, indicadores líderes y comparación regional (Colombia, Perú, Ecuador, Bolivia). La escala relativa a la historia venezolana no permite comparar niveles entre países sin rediseñar la normalización.

## Entrega (28 de octubre de 2026)

1. **Release de la tesis congelada:** `tesis-2026-10b`, con datos descargados el 28 de octubre de 2026. Es inmutable y contiene, además de los datos y el manifiesto, la evidencia que citan los documentos (composición anual, plausibilidad y robustez). Verificación: `python iciv/scripts/verify_release.py --release iciv/data/releases/tesis-2026-10b`.
2. **Artículo IEEE** generado desde esa release (DOCX y PDF), junto con la presentación de apoyo, en la carpeta local de entregas `entregables_local/Entrega final/`. Como todas las entregas, no se sube a GitHub (`.gitignore`). Reemplaza al borrador del 9 de octubre, que se retiró del repositorio.
3. **Release reemplazada.** `tesis-2026-10` (congelada horas antes) queda en el repositorio, inmutable, pero no se cita: su auditoría del FMI comparaba el WEO de octubre de los datos con la evidencia de abril, así que ninguna observación del FMI quedaba verificada y el escenario de robustez «sin estimaciones WEO verificadas» no retiraba nada. Los puntajes de ambas releases son idénticos. La auditoría ahora usa el WEO de octubre de 2026 como evidencia (164 de 164 valores coinciden).
4. **Correcciones previas a la congelación** (ver [incidente](INCIDENTE_FRED_VENTANA_MOVIL.md)): el archivo mensual de FRED no se actualizaba desde el 9 de octubre por la ventana móvil de la serie ICE BofA, y el snapshot de titulares de The Guardian no se actualizaba desde el 14 de septiembre. Ninguna observación se modificó.
5. **Historial reescrito (28 de octubre de 2026).** Por la regla de que las entregas no se versionan, se retiraron del historial de GitHub el texto de la tesis y el generador que se habían subido ese día. Cambiaron los SHA de los commits posteriores a `bb16898`. El manifiesto de `tesis-2026-10b` registra como commit base `b7c2871`, que en el historial actual es **`a2c9701`**: mismo código y mismos datos, verificables con los `code_sha256` del manifiesto. El commit base de `tesis-2026-10` (`bb16898`) no cambió.

## Cierre de la entrega individual

El autor confirmó que el único documento académico exigido es el artículo IEEE y que no tiene asesor. La tesis se retiró de la carpeta final y se conservó en un respaldo local fuera de ella. No hay una aprobación de asesor pendiente ni se atribuye aprobación a un panel experto.

Se precisaron el universo de 21 variables (20 activas), los pesos nominales frente a contribuciones efectivas, las limitaciones de los proxies, el reencuadre del Pulse, el vintage WEO de octubre y el alcance exploratorio de las asociaciones externas. La declaración de IA no certifica acciones humanas no acreditadas. Se añade reproducción aislada con comparación de siete salidas y pruebas de no sobrescritura y detección de discrepancias.

El estudio de usuarios, el panel experto y la anotación humana del sentimiento permanecen como trabajo futuro. No existe evidencia de una plantilla institucional o límite de extensión específico en los materiales disponibles; el artículo mantiene formato IEEE a doble columna. La revisión y la presentación final por parte del autor son responsabilidades personales y no se sustituyen con una comprobación automatizada.
