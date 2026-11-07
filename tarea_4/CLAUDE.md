# Agente de investigación socioeconómica del Perú

Este proyecto investiga con dos fuentes oficiales: el BCRP, por el servidor MCP `bcrp`, y la ENAHO 2024 del INEI, por las Skills `limpiando-enaho`, `graficando-enaho` y `mapeando-enaho`.

## Reglas de cada respuesta

1. **Toda cifra sale de una herramienta.** Del BCRP con `buscar_series`, `serie`, `resumen`, `episodios_fuera_de_rango` o `comparar_series`; de la ENAHO con las Skills. Nunca de memoria ni con cuentas hechas a mano.
2. **Cita el origen.** BCRP: código de serie, periodo, unidad y URL. ENAHO: módulo, factor de expansión y archivo de `salidas/`.
3. **Respeta la unidad de análisis.** Pobreza nacional, por área y por departamento: sumaria con `factor07 × mieperho`, que reproduce la tasa oficial del INEI. Pobreza por sexo o edad: residentes habituales con `facpob07`. Los dos valores están en `salidas/indicadores.csv`.
4. **Asociar no es causar.** La inflación del BCRP es una serie mensual de Lima Metropolitana; la ENAHO 2024 es un corte anual nacional. Se presentan como contexto, sin afirmar que una explique a la otra.
5. **Si algo falla, dilo.** Una herramienta sin datos, una validación `FALLIDO` o una serie inexistente se informan tal cual. No se inventa ni se ajusta ningún resultado para acercarlo a una referencia.

## Rutas

- Datos crudos: `datos/` (no se versionan; se bajan con `uv run python scripts/descargar_datos.py`).
- Salidas: `salidas/`, `figuras/`, `mapas/`.
- Informe: `informes/informe_final.md`, con imágenes en rutas relativas (`../figuras/...`).
- No se publica nada en GitHub sin aprobación del estudiante.
