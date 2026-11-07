# Evidencias del uso de inteligencia artificial

Registros reales de las conversaciones y ejecuciones del proyecto, en orden por carpeta. Antes de publicarlos se ocultaron claves, tokens y correos con `scripts/sanear_evidencias.py`.

| Carpeta | Qué contiene | Cómo se generó |
|---|---|---|
| `desarrollo/` | Conversaciones de desarrollo con asistentes | Exportación de cada conversación |
| `mcp/` | Pruebas, cotejo con el profesor, cliente MCP y sesiones con Claude Code | `pytest`, `scripts/probar_mcp_cliente.py` |
| `skills/` | Invocación manual, activación natural y encadenamiento | `scripts/probar_skills.py` |
| `integracion/` | Ejecución única de MCP y Skills, su auditoría y el informe original del agente | `scripts/probar_integracion.py` |
| `evaluacion/` | 20 trazas del experimento y 10 del experimento extra | `evaluacion/evaluar.py` |

Los archivos `.jsonl` son la salida `stream-json` de Claude Code: un evento por línea, con cada llamada a herramienta y su resultado.

## Historial de desarrollo

| Archivo | Qué es | Qué cubre |
|---|---|---|
| `desarrollo/02_chat_tarea4_001.png` a `003.png` | Capturas del chat «Tarea 4 Python Intermedio» en claude.ai | El pedido inicial, la lectura del Issue y el plan: trampas y cronograma. Son tres pantallas del chat, no la conversación completa |
| `desarrollo/01_sesion_claude_code.jsonl` | Sesión de Claude Code, con claves y correos ocultos | Revisión contra el Issue, correcciones con datos reales, reescritura de limpieza, gráficos, mapa y evaluación, herramienta propia y todas las corridas |

La sesión de Claude Code partió de un paquete de código preparado antes (`TAREA_4_SOLO_PARA_CLAUDE_CODE.zip`). El estudiante declara que no usó ChatGPT, aunque ese paquete menciona un historial con ChatGPT. Las capturas no muestran la preparación del paquete.

`mcp/interactivo_01_mcp.png` es una captura de Claude Code interactivo: `/mcp` reconecta `bcrp`, y el pedido con `@` se detuvo por falta de saldo de una clave de API ajena a las corridas del proyecto. La lectura del recurso quedó demostrada en `mcp/claude_recurso_lectura.jsonl`.
