# Bitacora vigente del ICIV

Fecha de corte: 2026-10-09 (versión metodológica 2.1).

Esta carpeta conserva solo las decisiones metodologicas vigentes. Las notas
historicas de exploracion, versiones con fuentes descartadas y entregables
antiguos fueron retirados para evitar contradicciones en defensa.

## Decisiones actuales

- El ICIV anual es el indicador estructural defendible. Serie oficial 2012–2026; 2000–2011 es un tramo exploratorio sin dimensión institucional.
- El Pulse mensual es un co-indicador de alta frecuencia, no reemplaza al ICIV.
- La IED no entra al score; se usa como outcome externo para validacion.
- No se usan fuentes venezolanas, ni datos inventados, ni rellenos artificiales
  para ocultar faltantes. Los valores imposibles del proveedor se excluyen y se
  registran; nunca se reemplazan.
- El dashboard muestra dos lecturas mensuales: ultimo mes disponible y ultimo
  mes confiable por cobertura.
- SATV se alimenta del Pulse mensual y se lee en el último mes elegible.
- El pronóstico público del Pulse es persistencia; SARIMA queda como comparador.
- El laboratorio conserva el simulador interactivo como herramienta pedagogica,
  no como prediccion politica.

## Fuentes fuera del core

Algunas fuentes permanecen en `iciv/data/raw/` como evidencia o backlog, pero no
entran al score vigente si no cumplen cobertura, reproducibilidad o aporte claro.
La lista de variables activas esta en `docs/METODOLOGIA.md` y las capas
auxiliares en `docs/FUENTES_Y_VARIABLES.md`.

## Regla para futuras bitacoras

Cada nueva decision debe explicar:

1. Que cambia.
2. Por que mejora la defensa del proyecto.
3. Que impacto tiene en cobertura, interpretabilidad o reproducibilidad.
4. Si la fuente entra al score, al Pulse, a validacion externa o queda apartada.
