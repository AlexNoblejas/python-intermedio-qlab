# Comparación: Claude Code sin y con MCP y Skills

**Con el MCP y las Skills, Claude Code acertó las 10 preguntas; sin ellos no contestó ninguna.** Esa diferencia no significa que sin herramientas inventara cifras: se abstuvo, y el experimento extra muestra que siguió sin inventar aun sin el permiso explícito de responder `null`. El costo de las herramientas fue tiempo: 3.6 veces más por pregunta.

## Resultados

| Medida | Modo A: sin MCP ni Skills | Modo B: con MCP y Skills |
|---|---:|---:|
| Correctas | 0 / 10 | 10 / 10 |
| Incorrectas | 0 | 0 |
| No contestadas | 10 | 0 |
| Tiempo promedio por pregunta | 7.0 s | 25.2 s |
| BCRP (4 preguntas), tiempo promedio | 6.1 s | 17.9 s |
| ENAHO (4 preguntas), tiempo promedio | 7.0 s | 28.4 s |
| Mixtas (2 preguntas), tiempo promedio | 9.1 s | 33.3 s |
| Errores de la CLI | 0 | 0 |

Detalle por pregunta: [`resultados.csv`](resultados.csv). Trazas completas: `evidencias_ia/evaluacion/`. Revisión de las mixtas: [`revision_mixtas.csv`](revision_mixtas.csv).

## Por pregunta

| N.º | Tema | Esperado | Modo A | Modo B | Herramientas en el modo B |
|---:|---|---:|---|---:|---|
| 01 | Inflación, setiembre de 2026 | 4.5487 | No contesta | 4.55 | `buscar_series`, `serie` |
| 02 | Máximo de inflación, 2020-2024 | 8.8126 | No contesta | 8.81 | `buscar_series`, `resumen` |
| 03 | Tipo de cambio, 15 de octubre de 2026 | 3.4282 | No contesta | 3.4282 | `buscar_series`, `serie` |
| 04 | Meses sobre 3 % | 34 | No contesta | 34 | `buscar_series`, `episodios_fuera_de_rango` |
| 05 | Pobreza nacional 2024 | 27.5795 | No contesta | 27.58 | Skill `limpiando-enaho` |
| 06 | Pobreza rural 2024 | 39.3028 | No contesta | 39.30 | Skill `limpiando-enaho` |
| 07 | Pobreza en Cusco 2024 | 18.5413 | No contesta | 18.54 | Skill `limpiando-enaho` |
| 08 | Participación de Lima en las personas pobres | 32.1063 | No contesta | 32.11 | Script de la Skill, leído sin invocarla |
| 09 | Mixta: inflación de diciembre de 2024 y pobreza nacional | 1.9663 y 27.5795 | No contesta | 1.97 y 27.58 | `buscar_series`, `serie`, script de la Skill |
| 10 | Mixta: meses sobre 3 % y brecha rural-urbana | 34 y 14.4958 | No contesta | 34 y 14.5 | `buscar_series`, `episodios_fuera_de_rango`, Skill `limpiando-enaho` |

Las 10 mejoraron y ninguna empeoró.

## Diseño

- **Preguntas:** 4 del BCRP, 4 de la ENAHO y 2 mixtas, con tolerancias escritas de antemano en [`preguntas.csv`](preguntas.csv).
- **Respuestas esperadas:** salen de `preparar_verdades.py`, que va directo a la API del BCRP y a los `.dta` del INEI sin usar el servidor ni las Skills. Seis se cotejaron con cifras publicadas por el curso ([`verificacion_verdades.csv`](verificacion_verdades.csv)). Quedaron en el commit `eedfcc3`, anterior a la primera corrida, y no cambiaron después.
- **Mismas condiciones:** mismo modelo (`claude-sonnet-5-5`), misma instrucción y una sesión independiente por pregunta, sin plugins ni ajustes personales.
- **Modo A:** sin herramientas integradas, sin MCP, sin Skills y en una carpeta vacía. La traza inicial lo confirma: la única herramienta disponible es `StructuredOutput`, que da formato a la respuesta.
- **Modo B:** `Bash` (solo `uv run python`), `Read`, `Glob`, `Grep`, `Skill` y el servidor `bcrp`. Cada pregunta corre en una copia limpia, sin salidas previas, sin `preguntas.csv` y sin la referencia del curso, así que las cifras de la ENAHO se calculan cada vez.
- **Control de fugas:** se revisó cada traza y ningún comando apuntó a la carpeta real del proyecto ni a los archivos de respuestas (columna `tocó_archivos_del_proyecto`).
- **Mixtas:** además de las cifras, debían distinguir la serie de Lima de la encuesta nacional y no afirmar causalidad. El criterio está en `preguntas.csv`.

## Experimento extra: sin la salida fácil

Una instrucción permite responder `null`, así que el 0 / 10 podría deberse a ella y no a una falta real de información. Se repitió el modo A quitando esa frase ([`resultados_sin_salida_facil.csv`](resultados_sin_salida_facil.csv)).

| Medida | Modo A con `null` | Modo A sin la frase |
|---|---:|---:|
| Correctas | 0 | 2 |
| Incorrectas | 0 | 0 |
| No contestadas | 10 | 8 |

Las dos cifras dadas (8.81 % de máximo de inflación y 27.6 % de pobreza nacional) son correctas. Salieron de memoria y el modelo advirtió que no pudo verificarlas. Sin herramientas, entonces, responde solo lo que recuerda de hechos publicados y se abstiene en lo reciente (2026), en lo que requiere contar (meses sobre 3 %) y en lo que requiere calcular (participación de Lima, Cusco). No se observó ninguna cifra inventada, pero el resto de la instrucción sigue pidiendo responder solo con evidencia, de modo que esto no prueba que nunca inventaría con otro pedido.

## Errores encontrados

Ninguno cambió una cifra calificada, pero son errores reales del modo B:

1. **Pregunta 07:** llama «3 777 hogares» a lo que son 3,777 personas de la muestra, e intercambia las etiquetas de los dos métodos (la sumaria da 18.541 % y personas 18.539 %, y escribió lo contrario). El origen probable es que la columna `n_muestra` no dice su unidad.
2. **Pregunta 10:** dice que cuatro meses de 2024 pertenecen al episodio; fueron tres, de enero a marzo.
3. **Pregunta 08:** dice «15 validaciones»; en la copia limpia hay 16.
4. **Activación de Skills:** en las preguntas 08 y 09 el modelo leyó `SKILL.md` y corrió el script sin invocar la herramienta `Skill`. El procedimiento fue el mismo, pero la activación automática no se dio en 2 de los 6 pedidos que necesitaban la ENAHO. Los pedidos de gráficos y mapas de `evidencias_ia/skills/` sí activaron las Skills; una descripción que mencione «participación» o «porcentaje de los pobres» podría mejorar esto.
5. **Modo A, pregunta 10:** intentó usar `Bash` y la CLI lo rechazó porque la herramienta no existía en ese modo. No hubo acceso a ningún archivo.

## Conclusión

MCP y Skills fueron útiles donde el modelo no podía responder por sí solo: datos posteriores a su conocimiento, conteos sobre una serie y cálculos con microdatos. Además, cada respuesta quedó con su código, su URL o su archivo. A cambio, cada pregunta tardó unos 18 segundos más.

Tres límites al leer el resultado: son 10 preguntas y una sola corrida por modo, no una muestra estadística; las preguntas se escribieron sabiendo qué herramientas existían, lo que favorece al modo B; y una respuesta numérica correcta puede venir acompañada de errores de redacción, como los de arriba, por lo que el informe sigue necesitando revisión humana.
