# Bitacora vigente del ICIV

Fecha de corte: 2026-07-21.

Esta carpeta conserva solo las decisiones metodologicas vigentes. Las notas
historicas de exploracion, versiones con fuentes descartadas y entregables
antiguos fueron retirados para evitar contradicciones en defensa.

## Decisiones actuales

- El ICIV anual es el indicador estructural defendible.
- El Pulse mensual es un co-indicador de alta frecuencia, no reemplaza al ICIV.
- La IED no entra al score; se usa como outcome externo para validacion.
- No se usan fuentes originadas en Venezuela, ni datos inventados, ni rellenos
  artificiales para ocultar faltantes.
- El dashboard muestra dos lecturas mensuales: ultimo mes disponible y ultimo
  mes confiable por cobertura.
- SATV se alimenta del Pulse mensual, porque su utilidad es monitoreo temprano.
- El laboratorio conserva el simulador interactivo como herramienta pedagogica,
  no como prediccion politica.

## Fuentes fuera del core

Algunas fuentes permanecen en `iciv/data/raw/` como evidencia o backlog, pero no
entran al score vigente si no cumplen cobertura, reproducibilidad o aporte claro.
La lista oficial de variables activas y apartadas esta en
`docs/FUENTES_Y_VARIABLES.md`.

## Regla para futuras bitacoras

Cada nueva decision debe explicar:

1. Que cambia.
2. Por que mejora la defensa del proyecto.
3. Que impacto tiene en cobertura, interpretabilidad o reproducibilidad.
4. Si la fuente entra al score, al Pulse, a validacion externa o queda apartada.
