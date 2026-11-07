"""Copia aislada del proyecto para probar al agente sin salidas previas ni respuestas a la vista.

Lleva lo que el agente necesita para trabajar (Skills, servidor, datos crudos) y deja fuera
resultados, preguntas, informes, evidencias y este CLAUDE.md. Asi una respuesta solo puede salir
de ejecutar las herramientas, no de leer un archivo ya calculado.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVOS = ["pyproject.toml", "uv.lock", ".python-version", "mcp/server.py", "scripts/descargar_datos.py"]
SOLO_BCRP = {"mcpServers": {"bcrp": {"type": "stdio", "command": "uv", "args": ["run", "python", "mcp/server.py"]}}}


def crear(destino: Path, con_referencias: bool = False) -> Path:
    """Arma la copia en destino. Las referencias del curso solo van si el pedido las necesita (mapa)."""
    destino.mkdir(parents=True, exist_ok=True)
    for relativo in ARCHIVOS:
        (destino / relativo).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relativo, destino / relativo)
    shutil.copytree(ROOT / ".claude" / "skills", destino / ".claude" / "skills")
    shutil.copytree(ROOT / "datos", destino / "datos")
    if con_referencias:
        shutil.copytree(ROOT / "referencias", destino / "referencias")
    (destino / ".mcp.json").write_text(json.dumps(SOLO_BCRP, indent=2), encoding="utf-8")
    return destino


def entorno() -> dict[str, str]:
    """Reutiliza el entorno ya instalado para que la copia no reinstale paquetes en cada corrida."""
    limpio = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "ANTHROPIC_"))}
    return {**limpio, "UV_PROJECT_ENVIRONMENT": str(ROOT / ".venv"), "PYTHONUTF8": "1"}


def borrar(destino: Path) -> None:
    shutil.rmtree(destino, ignore_errors=True)
