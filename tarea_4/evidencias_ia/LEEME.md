# Evidencias del uso de inteligencia artificial

Registros reales de las conversaciones y ejecuciones del proyecto, en orden por carpeta. Antes de publicarlos se ocultaron claves, tokens y correos con `scripts/sanear_evidencias.py`.

| Carpeta | Qué contiene | Cómo se generó |
|---|---|---|
| `desarrollo/` | Conversaciones de desarrollo con asistentes | Copia de la sesión y capturas |
| `mcp/` | Pruebas, cotejo con el profesor, cliente MCP y sesiones con Claude Code | `pytest`, `scripts/probar_mcp_cliente.py` |
| `skills/` | Invocación manual, activación natural y encadenamiento | `scripts/probar_skills.py` |
| `integracion/` | Ejecución única de MCP y Skills, su auditoría y el informe original del agente | `scripts/probar_integracion.py` |
| `evaluacion/` | 20 trazas del experimento y 10 del experimento extra | `evaluacion/evaluar.py` |

Los archivos `.jsonl` son la salida `stream-json` de Claude Code: un evento por línea, con cada llamada a herramienta y su resultado.

## Historial de desarrollo

El trabajo pasó por tres conversaciones, en este orden:

| Orden | Archivo | Qué es | Qué cubre |
|---:|---|---|---|
| 1 | `desarrollo/02_chat_tarea4_001.png` a `003.png` | Capturas del chat «Tarea 4 Python Intermedio» en claude.ai | El pedido inicial, la lectura del Issue y el plan: trampas y cronograma |
| 2 | `desarrollo/03_chat_chatgpt_001.png` a `004.png` | Capturas del chat «Resumen Tarea 4» en ChatGPT | La primera versión del proyecto, la auditoría con su prompt y el paquete `TAREA_4_SOLO_PARA_CLAUDE_CODE.zip` para Claude Code |
| 3 | `desarrollo/01_sesion_claude_code.jsonl` | Sesión de Claude Code, con claves y correos ocultos | Revisión contra el Issue, correcciones con datos reales, reescritura de limpieza, gráficos, mapa y evaluación, herramienta propia y todas las corridas |

Las capturas muestran los momentos principales de los chats 1 y 2, no cada mensaje. El registro completo de la conversación 3 está en su archivo.

`mcp/interactivo_01_mcp.png` es una captura de Claude Code interactivo: `/mcp` reconecta `bcrp`, y el pedido con `@` se detuvo por falta de saldo de una clave de API ajena a las corridas del proyecto. La lectura del recurso quedó demostrada en `mcp/claude_recurso_lectura.jsonl`.
