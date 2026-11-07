"""Diagnostico no destructivo del equipo antes de probar la Tarea 4.

Este comando NO confunde dependencias instaladas con integracion funcional.
Uso: python scripts/diagnosticar_entorno.py
"""
from __future__ import annotations

import importlib.util
import json
import platform
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def diagnosticar() -> dict:
    paquetes = ("fastmcp", "pandas", "pyarrow", "geopandas", "matplotlib", "httpx", "pytest", "streamlit")
    binarios = ("python", "uv", "claude", "git")
    rutas = (
        ".mcp.json", "mcp/server.py", "mcp/test_server.py",
        ".claude/skills/limpiando-enaho/SKILL.md",
        ".claude/skills/graficando-enaho/SKILL.md",
        ".claude/skills/mapeando-enaho/SKILL.md",
        "datos/966-Modulo34.zip", "datos/966-Modulo02.zip",
        "datos/peru_departamental_simple.geojson", "uv.lock",
    )
    return {
        "sistema": platform.platform(),
        "version_python": platform.python_version(),
        "binarios_disponibles": {c: bool(shutil.which(c)) for c in binarios},
        "paquetes_disponibles_en_este_python": {p: bool(importlib.util.find_spec(p)) for p in paquetes},
        "archivos_disponibles": {p: (ROOT / p).is_file() for p in rutas},
        "advertencia": (
            "Este diagnostico solo comprueba presencia: NO acredita conexion MCP, "
            "datos INEI, acceso API BCRP, respuestas del agente ni pruebas aprobadas."
        ),
    }


def main() -> None:
    print(json.dumps(diagnosticar(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
