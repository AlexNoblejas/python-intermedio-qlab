# Tarea 4: agente de investigación socioeconómica del Perú

Un agente en Claude Code que responde preguntas con datos oficiales: consulta el BCRP por un servidor MCP propio y procesa la ENAHO 2024 del INEI con tres Skills. Cada cifra se puede rastrear hasta su fuente.

**Consigna:** [Issue #201](https://github.com/d2cml-ai/Data-Science-Python/issues/201) · **Informe:** [`informes/informe_final.md`](informes/informe_final.md)

## 1. Objetivo

Responder con evidencia reproducible esta pregunta, que necesita ambas fuentes:

> Entre 2020 y 2024, ¿cuánto tiempo estuvo la inflación de Lima a 12 meses fuera del rango meta del BCRP (1 % a 3 %) y, en 2024, dónde era más alta la pobreza monetaria y dónde vivía la mayor parte de las personas pobres, por área y por departamento?

**Respuesta corta:** 34 de 60 meses, todos sobre 3 % y seguidos (junio de 2021 a marzo de 2024). La tasa es más alta en el área rural (39.3 %) y en Cajamarca (45.0 %), pero el 72.7 % de las personas pobres vive en áreas urbanas y el 32.1 % en el departamento de Lima. Son descripciones: el trabajo no demuestra una relación causal entre inflación y pobreza.

## 2. Arquitectura

```text
                     Pregunta en lenguaje natural
                                  |
                             Claude Code
                 (CLAUDE.md: reglas de cada respuesta)
                    /                          \
        Servidor MCP bcrp                 Skills de la ENAHO
         (mcp/server.py)                  (.claude/skills/)
                |                                  |
        API del BCRP                  limpiando-enaho -> salidas/
                |                     graficando-enaho -> figuras/
         figuras/bcrp_*.png           mapeando-enaho   -> mapas/
                    \                          /
                     informes/informe_final.md
```

Las cuentas las hace Python: el modelo elige la herramienta e interpreta, pero no calcula. Si una validación falla, las Skills se detienen en lugar de entregar una cifra dudosa.

## 3. Herramientas MCP

| Elemento | Nombre | Qué hace |
|---|---|---|
| Herramienta | `buscar_series` | Encuentra series oficiales por palabras clave |
| Herramienta | `serie` | Descarga los datos de un periodo, con su URL de origen |
| Herramienta | `resumen` | Calcula primero, último, cambio, variación, promedio, máximo y mínimo |
| **Herramienta propia** | `episodios_fuera_de_rango` | Cuenta los periodos dentro, sobre o bajo un rango y arma las rachas consecutivas |
| Herramienta adicional | `comparar_series` | Alinea dos series en periodos comunes y calcula su correlación descriptiva |
| Herramienta adicional | `graficar_serie` | Guarda un PNG, con una banda de referencia opcional |
| Recurso | `bcrp://serie/{codigo}` | Ficha descriptiva de una serie |
| Prompt | `informe(tema)` | Plantilla para informar un indicador con cifras verificables |

`.mcp.json` declara `bcrp` y `fetch`, como pide la Sesión 04, sin claves. El experimento y la integración usan solo `bcrp`.

## 4. Skills

| Skill | Entra | Sale |
|---|---|---|
| `limpiando-enaho` | Zips de los módulos 34 y 02 | `salidas/validacion.txt`, `salidas/indicadores.csv`, `salidas/personas_2024.parquet` |
| `graficando-enaho` | Indicadores validados y un pedido | `figuras/*.png`: área, sexo, edad, departamento y concentración |
| `mapeando-enaho` | Indicadores validados y el GeoJSON | `mapas/pobreza_departamento.png` y su comparación con la Sesión 16 |

Las de gráficos y mapas usan primero `limpiando-enaho` si no hay base validada. Un solo pedido («Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024») activó ambas en una carpeta vacía: [`evidencias_ia/skills/resumen_skills.json`](evidencias_ia/skills/resumen_skills.json).

**Qué factor usa cada tasa.** La pobreza nacional, por área y por departamento usa la sumaria con `factor07 × mieperho`, que reproduce la cifra oficial. La pobreza por sexo y edad usa residentes habituales con `facpob07`. `salidas/indicadores.csv` conserva ambas tasas donde aplican.

| Control | Valor | Referencia |
|---|---:|---:|
| Pobreza nacional, sumaria | 27.58 % | 27.6 % |
| Pobreza nacional, personas con `facpob07` | 27.53 % | 27.6 % |
| Urbana y rural, sumaria | 24.81 % y 39.30 % | 24.8 % y 39.3 % |
| Urbana y rural, personas con `facpob07` | 24.74 % y 39.44 % | 24.8 % y 39.3 % |
| Residentes habituales | 108,664 | 108,664 |
| Departamentos con dato | 25 | 25 |
| Diferencia máxima con la Sesión 16, sumaria | 0.049 pp | hasta 0.1 pp |

## 5. Fuentes y descarga de datos

| Fuente | Enlace |
|---|---|
| ENAHO 2024, módulo 34 (sumaria) | [966-Modulo34.zip](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip) |
| ENAHO 2024, módulo 02 (miembros) | [966-Modulo02.zip](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip) |
| Límites departamentales | [GeoJSON del curso](https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson) |
| Series del BCRP | [BCRPData](https://estadisticas.bcrp.gob.pe/estadisticas/series/) |
| Rango meta del BCRP | [Política monetaria](https://www.bcrp.gob.pe/politica-monetaria/) |

Los microdatos no se suben al repositorio. Se bajan con `scripts/descargar_datos.py`, y si el portal del INEI falla, también a mano a `datos/`.

## 6. Instalación con `uv`

Necesita [uv](https://docs.astral.sh/uv/), Git e internet. Para la evaluación y la integración, también [Claude Code](https://code.claude.com/docs) con sesión iniciada.

```bash
git clone https://github.com/AlexNoblejas/python-intermedio-qlab
cd python-intermedio-qlab/tarea_4
uv sync
uv run python scripts/descargar_datos.py
```

## 7. Conectar el MCP a Claude Code

El servidor ya está declarado en `.mcp.json`. Abre `claude` **dentro de `tarea_4/`**, acepta los servidores del proyecto y prueba:

1. `/mcp`: `bcrp` y `fetch` conectados.
2. Una pregunta: «¿Cuántos meses estuvo la inflación de Lima por encima de 3 % entre 2020 y 2024?»
3. El recurso: `@bcrp:bcrp://serie/PN01273PM ¿desde cuándo hay datos?`
4. El prompt: `/mcp__bcrp__informe inflación de Lima`

## 8. Reproducir el procesamiento y las pruebas

```bash
uv run pytest -q mcp                                               # 10 pruebas contra el BCRP real
uv run pytest -q tests                                             # 79 pruebas sin red
uv run python scripts/verificar_contrato_docente.py                # test_server.py igual al del profesor
uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py
uv run python .claude/skills/graficando-enaho/scripts/graficar.py --tipo todos
uv run python .claude/skills/mapeando-enaho/scripts/mapear.py
uv run python scripts/validar_con_referencias.py
```

Con Claude Code real:

```bash
uv run python scripts/probar_skills.py --modelo sonnet             # activación y encadenamiento de Skills
uv run python scripts/probar_integracion.py --modelo sonnet        # borra salidas y corre PROMPT_AGENTE.md
uv run python evaluacion/preparar_verdades.py                      # respuestas esperadas, sin usar al agente
uv run python evaluacion/evaluar.py --modelo sonnet                # experimento 10 x 2
uv run python evaluacion/evaluar.py --modelo sonnet --sin-salida-facil
```

`dashboard.py` es opcional: `uv run streamlit run dashboard.py`.

## 9. Resultados de la evaluación

| Medida | Sin MCP ni Skills | Con MCP y Skills |
|---|---:|---:|
| Correctas | 0 / 10 | 10 / 10 |
| Incorrectas | 0 | 0 |
| No contestadas | 10 | 0 |
| Tiempo promedio | 7.0 s | 25.2 s |

El modo sin herramientas se abstuvo en todo. Al quitarle el permiso explícito de responder `null` dio 2 cifras de memoria, ambas correctas, y se abstuvo en 8. El análisis, con los errores del agente, está en [`evaluacion/comparacion.md`](evaluacion/comparacion.md).

## 10. Limitaciones y problemas encontrados

**Del análisis**
- La inflación es de Lima y mensual; la pobreza es nacional y de un solo año. Se presentan como contexto, sin inferir causas.
- La ENAHO es una muestra y no se calcularon intervalos de confianza: diferencias pequeñas entre departamentos no son interpretables.
- Los conteos absolutos de personas pobres (9.51 millones) difieren cerca de 1.2 % del dato del INEI (9.395 millones). Conviene apoyarse en las tasas y participaciones.
- El informe técnico del INEI no se pudo abrir desde la sesión; sus cifras se cotejaron con Andina y con la referencia del curso.
- El experimento tiene 10 preguntas y una corrida por modo: no es una muestra estadística.

**Encontrados al correr con datos reales, ya corregidos**
- El zip del módulo 34 trae `sumaria-2024.dta` y `sumaria-2024-12g.dta`, y la lectura se detenía.
- La API trimestral del BCRP numera el trimestre (`2025-4` es T4); el servidor pedía otro periodo.
- Con pedidos seguidos, el BCRP responde HTML en lugar de JSON; el servidor espera y reintenta.

**Abiertos**
- Con `claude -p`, `@bcrp:...` no adjunta el recurso. La lectura se demostró con `ReadMcpResourceTool`. El intento interactivo con `@` conectó `bcrp`, pero no tiene respuesta registrada (ver `evidencias_ia/LEEME.md`).
- En 2 de los 6 pedidos del experimento que necesitaban la ENAHO, el modelo corrió el script de la Skill sin invocarla.

## 11. Ejemplo de una ejecución completa

[`PROMPT_AGENTE.md`](PROMPT_AGENTE.md) se ejecutó una vez, desde salidas vacías. La traza registra, en este orden:

1. `mcp__bcrp__buscar_series`: identifica `PN01273PM`.
2. Skill `limpiando-enaho`: corre la limpieza; la validación queda `APROBADO`.
3. `mcp__bcrp__resumen` y `mcp__bcrp__episodios_fuera_de_rango`: 34 meses sobre 3 %, máximo de 8.81 %.
4. `mcp__bcrp__graficar_serie`: guarda el gráfico con la banda de 1 % a 3 %.
5. Skills `graficando-enaho` y `mapeando-enaho`: generan figuras y mapa.
6. `Write`: escribe `informes/informe_final.md`.

Fueron 4 herramientas MCP y 3 Skills en 98 segundos. Traza: [`claude_integracion.jsonl`](evidencias_ia/integracion/claude_integracion.jsonl). Auditoría: [`auditoria_integracion.md`](evidencias_ia/integracion/auditoria_integracion.md).

## 12. Evidencias del uso de IA

[`evidencias_ia/`](evidencias_ia/) guarda las trazas y conversaciones, con claves y correos ocultos:

| Carpeta | Contenido |
|---|---|
| `mcp/` | Las 10 pruebas, el cotejo con el profesor, el cliente MCP y las sesiones con Claude |
| `skills/` | Invocación manual, activación natural y encadenamiento |
| `integracion/` | La ejecución única, su auditoría y el informe original del agente |
| `evaluacion/` | Las 20 trazas y las 10 del experimento extra |
| `desarrollo/` | Sesión de Claude Code y capturas de los chats de claude.ai y ChatGPT; el alcance exacto está en [`LEEME.md`](evidencias_ia/LEEME.md) |

Las verificaciones manuales están en [`auditoria/VERIFICACIONES_MANUALES.md`](auditoria/VERIFICACIONES_MANUALES.md); el cumplimiento requisito por requisito, en [`auditoria/MATRIZ_CUMPLIMIENTO.md`](auditoria/MATRIZ_CUMPLIMIENTO.md); y el prompt que guio el cierre, en [`auditoria/PROMPT_MAESTRO.md`](auditoria/PROMPT_MAESTRO.md).
