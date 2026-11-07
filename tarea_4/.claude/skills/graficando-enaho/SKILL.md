---
name: graficando-enaho
description: Grafica la pobreza monetaria ponderada de la ENAHO 2024 por área urbana y rural, sexo, grupo de edad, departamento o concentración de personas pobres, y guarda PNG con título, unidad y fuente en figuras/. Úsala cuando pidan un gráfico, barras, una figura o una comparación de pobreza con la ENAHO o el INEI.
---

# Graficar la ENAHO

1. Si no existe `salidas/indicadores.csv` o `salidas/validacion.txt` no dice `RESULTADO: APROBADO`, usa primero la skill `limpiando-enaho`.
2. Elige la figura según el pedido y corre desde la raíz: `uv run python .claude/skills/graficando-enaho/scripts/graficar.py --tipo TIPO`

   | Pedido | TIPO | Archivo |
   |---|---|---|
   | Urbano y rural | `area` | `figuras/pobreza_area_2024.png` |
   | Hombres y mujeres | `sexo` | `figuras/pobreza_sexo_2024.png` |
   | Niños, jóvenes, adultos, mayores | `edad` | `figuras/pobreza_edad_2024.png` |
   | Comparar departamentos | `departamento` | `figuras/pobreza_departamento_barras_2024.png` |
   | Dónde viven las personas pobres | `concentracion` | `figuras/concentracion_pobres_departamento_2024.png` |
   | Todas | `todos` | Las cinco |

3. Revisa que el archivo exista y describe lo que muestra, con sus cifras, sin atribuir causas.

Las reglas ya están en el script: barras desde cero y ordenadas, un solo color, valor escrito en cada barra, título con el hallazgo y el periodo, unidad en el eje, fuente al pie y 200 dpi. No las rehagas a mano.
