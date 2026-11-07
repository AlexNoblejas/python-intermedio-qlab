"""Contrasta los ocho tests MCP locales con el contrato publicado por el profesor.

No altera ni reescribe test_server.py. Requiere acceso a GitHub.
Uso: uv run python scripts/verificar_contrato_docente.py
"""
from __future__ import annotations

import difflib
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
ORIGEN = (
    "https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/"
    "sessions/04-mcp-claude-code/proyecto/test_server.py"
)
LOCAL = ROOT / "mcp/test_server.py"


def normalizar(contenido: str) -> list[str]:
    """Ignora solo finales de linea y blancos al final de cada linea.

    Conserva los asserts y la implementacion de las pruebas intactos.
    """
    return [line.rstrip() for line in contenido.replace("\r\n", "\n").splitlines()]


def contrastar(original: str, local: str) -> tuple[bool, str]:
    a, b = normalizar(original), normalizar(local)
    if a == b:
        return True, "Coincidencia exacta tras normalizar fin de linea y espacios finales."
    diff = "\n".join(difflib.unified_diff(a, b, fromfile="profesor/test_server.py", tofile="mcp/test_server.py", lineterm=""))
    return False, diff


def main() -> None:
    if not LOCAL.is_file():
        raise SystemExit("No existe mcp/test_server.py")
    try:
        response = httpx.get(ORIGEN, timeout=30, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SystemExit(f"NO VERIFICADO: no se pudo acceder al original de GitHub: {exc}") from exc
    ok, detalle = contrastar(response.text, LOCAL.read_text(encoding="utf-8"))
    print(detalle)
    if not ok:
        sys.exit("FALLIDO: revisar cambios contra el contrato original. No modificar tests para aprobarlos.")
    print("APROBADO: contrato original conservado.")


if __name__ == "__main__":
    main()
