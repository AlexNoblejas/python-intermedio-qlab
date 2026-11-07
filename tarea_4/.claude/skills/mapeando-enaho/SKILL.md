---
name: mapeando-enaho
description: Construye el mapa coroplético de la pobreza monetaria por departamento del Perú con la ENAHO 2024 del INEI y lo compara con la referencia de la Sesión 16. Une por código (ubigeo[:2] con FIRST_IDDP), exige 25 unidades y mantiene Lima y Callao separados. Úsala cuando pidan un mapa, una coropleta o la distribución territorial de la pobreza.
---

# Mapear la ENAHO

1. Si no existe `salidas/indicadores.csv` o `salidas/validacion.txt` no dice `RESULTADO: APROBADO`, usa primero la skill `limpiando-enaho`.
2. Si falta `datos/peru_departamental_simple.geojson`, corre `uv run python scripts/descargar_datos.py --solo geojson`.
3. Desde la raíz corre exactamente: `uv run python .claude/skills/mapeando-enaho/scripts/mapear.py`
4. Comprueba `mapas/pobreza_departamento.png` y lee `mapas/pobreza_departamento_vs_referencia.csv`. Informa la diferencia máxima con la referencia.
5. Reporta los departamentos con mayor y menor pobreza. El mapa describe 2024; no demuestra causas.

Nunca unas por nombre («APURIMAC» no es «Apurímac»), no fusiones Lima (15) con Callao (07) y no uses tasas sin ponderar. Si el script se detiene por una unión incompleta, informa el error.
