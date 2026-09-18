# Correcciones del laboratorio y textos del mapa

Revisión del 17 de septiembre de 2026. Se conserva el diseño editorial del autor.

- Los botones de mejor y peor año seleccionan el máximo/mínimo del ICIV publicado y cargan todas las dimensiones de ese mismo año. No combinan máximos de años diferentes.
- Los faltantes siguen siendo `null`: no se sustituyen por cero ni por el año base. El cálculo renormaliza únicamente los pesos de dimensiones disponibles, como el índice anual. Sin dimensiones disponibles, muestra «Sin datos».
- Los pesos proceden obligatoriamente del AHP calculado: no existe sustitución silenciosa por pesos fijos. Una ausencia o un peso inválido impide generar el dashboard.
- Los controles y puntajes dimensionales usan dos decimales, con incremento de 0,01. Las categorías coinciden con los cortes anuales: 31, 51, 66 y 81.
- Una modificación manual se identifica como escenario hipotético. Se retiró la equivalencia histórica automática y se aclaró que el laboratorio no estima causalidad ni pronostica variables económicas.
- El peso dimensional disponible se distingue explícitamente de la cobertura de indicadores. Los aportes muestran pesos efectivos cuando hay faltantes.
- El mapa describe radiancia registrada y estados con mayor radiancia, sin atribuir directamente actividad económica, apagones o recuperación a la imagen.
- La revocación de la clave EIA anterior queda registrada como confirmación del titular, no como verificación directa del proveedor.

## Verificación

69 pruebas Python y 6 pruebas JavaScript aprobadas. La prueba del payload del dashboard reproduce todos los puntajes anuales publicados con tolerancia de redondeo de 0,005 puntos. Las pruebas cubren faltantes, ceros válidos, ausencia total de datos, extremos históricos, cortes de categoría y precisión decimal. Se incorporaron al flujo de CI.

Comprobación en navegador: base 2024 = 34,25; máximo 2012 = 82,53; mínimo 2020 = 22,76. El movimiento de un control conserva la precisión de 0,01 y activa la etiqueta de escenario hipotético. No se observaron errores de consola durante esta verificación.

El pipeline se ejecutó con `--no-fetch --no-open --no-package`: reproduce el snapshot existente, sin afirmar que las fuentes hayan sido actualizadas. La release anterior conserva sus 54 hashes verificados; no se congeló una nueva entrega ni se redactó la tesis. Las validaciones académicas pendientes continúan en `VALIDACION_PENDIENTE.md`.
