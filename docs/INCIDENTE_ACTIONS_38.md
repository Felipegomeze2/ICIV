# Corrección de la ejecución 38 de actualización del dashboard

La ejecución programada del 21 de septiembre de 2026 falló en `Verificar vigencia de fuentes Pulse`, antes del pipeline y del despliegue. Los registros muestran FRED con último mes agosto de 2026 y un rezago de 51 días frente al límite de 50. El código calculaba la distancia desde el 1 de agosto, que identifica el periodo mensual; no es su fecha de publicación.

El control ahora mide días desde el último día del mes reportado. Agosto tiene un rezago de 21 días el 21 de septiembre. Se conservan los límites declarados: con el límite FRED de 50 días, julio falla en esa fecha (52 días). Un mes corriente parcial tiene rezago cero; un mes futuro se rechaza. Este control mide antigüedad del periodo observado, no tiempo desde descarga o publicación, ni integridad de un mes parcial.

No se modifican observaciones, no se rellenan faltantes y no se desactiva el control. Se añaden pruebas para el incidente, límites exactos, meses futuros, febrero bisiesto y ausencia de una fuente obligatoria.

## Ejecución manual

En GitHub, abrir Actions → Actualizar Dashboard ICIV → Run workflow y seleccionar `main`. Para repetir la actualización programada, activar `fetch_data`; activar `fetch_anual` solo si se desea refrescar además las fuentes anuales. No usar `Re-run jobs` sobre la ejecución 38, porque conserva el commit antiguo.

El arreglo no dispara manualmente el flujo. La descarga real y el despliegue quedan sujetos a disponibilidad de proveedores, credenciales vigentes en GitHub Secrets y los demás controles del workflow.
