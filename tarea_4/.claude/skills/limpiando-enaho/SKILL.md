---
name: limpiando-enaho
description: Limpia y valida los módulos 34 (sumaria) y 02 (miembros) de la ENAHO 2024 del INEI, filtra residentes habituales, une personas y hogares y calcula la pobreza monetaria ponderada. Crea salidas/personas_2024.parquet, salidas/indicadores.csv y salidas/validacion.txt. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza en el Perú a nivel nacional, urbano, rural, por departamento, sexo o edad.
---

# Limpiar la ENAHO

1. Si faltan `datos/966-Modulo34.zip` o `datos/966-Modulo02.zip`, corre `uv run python scripts/descargar_datos.py`.
2. Desde la raíz del proyecto corre exactamente: `uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py`
3. Lee `salidas/validacion.txt`. Si dice `RESULTADO: FALLIDO` o el archivo no existe, **detente** e informa qué control falló.
4. Responde con `salidas/indicadores.csv`, que trae una fila por grupo:
   - `pobreza_pct`: la tasa que se reporta. Nacional, área y departamento usan la sumaria con `factor07 × mieperho`; sexo y edad usan residentes habituales con `facpob07`.
   - `pobreza_personas_pct`: la misma tasa con residentes y `facpob07`, para contrastar.
   - `participacion_pobres_pct`: qué parte de todas las personas pobres vive en ese grupo.
5. Para una tabulación nueva usa `salidas/personas_2024.parquet`, siempre ponderada con `facpob07`. Antes de usar otra variable, lee `reference.md`.
6. Reporta la cifra, el factor y el archivo de origen. No redondees para acercarte a una referencia ni afirmes causas.
