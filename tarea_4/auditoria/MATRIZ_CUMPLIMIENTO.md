# Matriz de cumplimiento del Issue #201

Cada fila es un requisito de la consigna, con su evidencia. Es una autoevaluación: la nota la decide el equipo docente.

## Parte 1. Servidor MCP del BCRP (5 puntos)

| Requisito | Pts | Evidencia | Estado |
|---|---:|---|---|
| `buscar_series`, `serie`, `resumen` | 2.0 | `mcp/server.py`; `evidencias_ia/mcp/cliente_mcp.json` | Cumplido |
| Herramienta propia útil, validada y documentada | 1.0 | `episodios_fuera_de_rango`, cotejada con la API en `mcp/test_herramienta_propia.py` | Cumplido |
| Recurso y prompt accesibles | 1.0 | `claude_recurso_lectura.jsonl`, `claude_prompt.jsonl` | Cumplido; el `@` literal está pendiente de una sesión interactiva |
| `.mcp.json` e integración con Claude Code | | `.mcp.json`; `claude_natural.jsonl` (código, periodo y fuente) | Cumplido |
| 8 pruebas originales sin cambios y 2 propias: `10 passed` | 1.0 | `evidencias_ia/mcp/pruebas_10.txt`, `contrato_docente.txt` | Cumplido |

## Parte 2. Skills de la ENAHO (6 puntos)

| Requisito | Pts | Evidencia | Estado |
|---|---:|---|---|
| Leer, normalizar, filtrar residentes, unir con `m:1`, construir indicadores, ponderar, validar | 2.5 | `limpiar.py`; `salidas/validacion.txt`, 17 controles aprobados | Cumplido |
| Llaves como texto y detención si falla una validación | | `limpiar.py`; `tests/` | Cumplido |
| Gráficos: área, sexo, departamentos; ponderados, con título, unidad, periodo y fuente | 1.5 | `figuras/` | Cumplido |
| Mapa: `ubigeo[:2]` con `FIRST_IDDP`, 25 unidades, Lima y Callao, leyenda con unidad | 1.5 | `mapas/pobreza_departamento.png` | Cumplido |
| Comparar con la referencia de la Sesión 16 | | `mapas/pobreza_departamento_vs_referencia.csv`: máximo 0.049 pp | Cumplido |
| Invocación individual, lenguaje natural y encadenamiento | 0.5 | `evidencias_ia/skills/resumen_skills.json`: 4 de 4 | Cumplido |

## Parte 3. Agente (5 puntos)

| Requisito | Pts | Evidencia | Estado |
|---|---:|---|---|
| Pregunta propia con ambas fuentes y plan | 0.5 | `README.md`; `PROMPT_AGENTE.md`; traza | Cumplido |
| Una ejecución con 2 o más herramientas MCP y 2 o más Skills | 2.0 | `evidencias_ia/integracion/auditoria_traza.json`: 4 MCP y 3 Skills | Cumplido |
| Informe con 7 secciones, 3 hallazgos, gráfico BCRP, gráfico ENAHO y mapa | 1.5 | `informes/informe_final.md` | Cumplido |
| 3 o más cifras verificadas de ambas fuentes y manejo de errores | 1.0 | `auditoria/VERIFICACIONES_MANUALES.md`: 6 cifras; sección 8 del informe | **Falta la confirmación del estudiante** |

## Parte 4. Evaluación y reproducibilidad (4 puntos)

| Requisito | Pts | Evidencia | Estado |
|---|---:|---|---|
| 10 preguntas (4, 4 y 2) con respuestas verificadas | 1.0 | `evaluacion/preguntas.csv`, `verificacion_verdades.csv` | Cumplido |
| Dos modos, mismas preguntas, sesiones independientes, sin fugas | 1.5 | `evaluacion/resultados.csv`, 20 trazas | Cumplido |
| Análisis de aciertos, errores, herramientas y tiempo | 0.5 | `evaluacion/comparacion.md` | Cumplido |
| README con 12 puntos | 1.0 | `README.md` | Cumplido |
| Conversaciones completas de IA | | `evidencias_ia/desarrollo/` | **Falta el historial previo a esta sesión** |

## Antes de entregar

| Requisito | Estado |
|---|---|
| Sin microdatos, credenciales ni datos personales en lo publicable | Revisado con `scripts/sanear_evidencias.py`; el estudiante debe revisar las conversaciones |
| Commits descriptivos | Cumplido, solo locales |
| Repositorio público y enlaces funcionando | **Pendiente: requiere push** |
| Comentario de entrega en el Issue | **Pendiente: `ENTREGA_GITHUB.md` listo para pegar** |
