# Tarea 4 — Agente de investigación socioeconómica (BCRP + ENAHO)

> **Estado: listo para completar las verificaciones reales en Claude Code; NO es una entrega final aprobada.** Inicio para Claude: leer `CLAUDE.md`.

## Consigna y pregunta

- Issue: https://github.com/d2cml-ai/Data-Science-Python/issues/201
- Plazo del curso: 8 de noviembre de 2026, 23:59 (Perú)
- Pregunta: ¿Cómo evolucionó la inflación de Lima a 12 meses entre 2020 y 2024 y qué diferencias urbano-rurales y departamentales presentaba la pobreza monetaria del Perú en 2024?

## Contenido del proyecto

- `mcp/server.py`: FastMCP del BCRP. Herramientas `buscar_series`, `serie`, `resumen`, `comparar_series`, `graficar_serie`; recurso y prompt.
- `mcp/test_server.py`: **ocho pruebas del profesor, sin cambiar**; `mcp/test_herramienta_propia.py`: dos propias.
- `.claude/skills/`: `limpiando-enaho`, `graficando-enaho`, `mapeando-enaho` con scripts ejecutables.
- `scripts/`: descarga, validación, comparación con referencias, creación de informe, diagnóstico y puerta de calidad.
- `evaluacion/`: diez preguntas, verdades esperadas derivadas de datos, experimento sin/con herramientas, resultado y comparación.
- `informes/`, `figuras/`, `mapas/`, `salidas/`: entregables de análisis; `evidencias_ia/`: registros íntegros a revisar antes de publicar.
- `dashboard.py`: interfaz Streamlit **opcional**; el Issue no exige entrenamiento de un modelo ML.

## Instalación (Python 3.11+, uv, Git, Internet y Claude Code)

Desde **esta** carpeta `tarea_4`:

```powershell
uv sync
uv run python scripts/descargar_datos.py
uv run pytest -q tests
uv run pytest -q mcp
uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py
uv run python scripts/validar_con_referencias.py
uv run python .claude/skills/graficando-enaho/scripts/graficar.py --tipo todos
uv run python .claude/skills/mapeando-enaho/scripts/mapear.py
```

Descargas oficiales en `scripts/descargar_datos.py` (INEI módulos 34/02, geometría del curso). Los microdatos se guardan en `datos/` y **no se suben al repositorio**. Los scripts se detienen o advierten si los resultados no superan controles esenciales; no inventar ni fijar cifras a mano.

Para la integración en Claude Code, usa la configuración `.mcp.json`, abre `/mcp`, utiliza `PROMPT_AGENTE.md` y registra una sesión con **al menos dos herramientas MCP diferentes y dos Skills diferentes**.

## Evaluación

```powershell
uv run python evaluacion/preparar_verdades.py
uv run python evaluacion/evaluar.py --dry-run
uv run python scripts/probar_integracion.py --modelo sonnet
uv run python evaluacion/evaluar.py --modelo sonnet --modos sin con
uv run python scripts/generar_informe.py
uv run python scripts/validar_entrega.py --exigir-completo
```

Estos comandos de integración/evaluación requieren la **CLI `claude`** autenticada en el PATH (además de Claude Code Desktop si se usa); `Code` de escritorio por sí solo no garantiza que exista el ejecutable. Conserva los logs reales, y si un parámetro cambia con una versión nueva, revísalo antes de modificar scripts. **No publiques** si falta verificación obligatoria.

## Metodología y reproducibilidad

Se conservan `ubigeo`, `conglome`, `vivienda`, `hogar` como texto; filtro de residentes `((p204==1)&(p205==2))|((p204==2)&(p206==1))`; unión de personas y hogares `m:1`; pobreza monetaria de personas ponderada con `facpob07`; mapa por `ubigeo[:2]` ↔ `FIRST_IDDP` con 25 códigos y Lima/Callao separados. Referencias: 27.6 % nacional, ~24.8 % urbano, ~39.3 % rural, 108664 residentes. Las referencias son **controles**, nunca resultados precargados.

La integración BCRP vs ENAHO compara observaciones de diferente naturaleza: series temporales frente a una encuesta transversal; no presenta relaciones causales. Los hallazgos exigen código, período, unidad y fuente.

**Seguridad y publicación:** respeta `.gitignore`; no publicar ZIP/DTA originales del INEI, secretos ni conversaciones sin ocultar información privada. Guarda el historial **completo** de asistentes usados durante el desarrollo, incluidas conversaciones anteriores al trabajo con Claude. Usa `ENTREGA_GITHUB.md` solo cuando el estudiante autorice la publicación.
