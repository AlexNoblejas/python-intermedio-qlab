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
