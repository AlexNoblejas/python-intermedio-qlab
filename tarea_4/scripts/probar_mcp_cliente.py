"""Evidencia del servidor MCP por el cliente real de FastMCP y, si se pide, desde Claude Code.

    uv run python scripts/probar_mcp_cliente.py            # herramientas, recurso y prompt
    uv run python scripts/probar_mcp_cliente.py --claude   # pregunta natural, @recurso y /prompt
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from fastmcp import Client

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "mcp"), str(ROOT / "scripts")]
import espacio_limpio
from server import mcp

OUT = ROOT / "evidencias_ia" / "mcp"
PEDIDOS_CLAUDE = {
    "natural": "¿Cuántos meses estuvo la inflación de Lima a 12 meses por encima de 3 % entre enero de 2020 y "
               "diciembre de 2024? Indica el código de la serie, el periodo y la fuente.",
    "recurso": "@bcrp:bcrp://serie/PN01273PM ¿Desde cuándo hay datos de esta serie y con qué frecuencia?",
    "prompt": "/mcp__bcrp__informe inflación de Lima",
}


async def cliente() -> dict:
    async with Client(mcp) as c:
        herramientas = [t.name for t in await c.list_tools()]
        plantillas = [t.uriTemplate for t in await c.list_resource_templates()]
        prompts = [p.name for p in await c.list_prompts()]
        busqueda = (await c.call_tool("buscar_series", {"texto": "ipc 12 meses", "limite": 3})).data
        resumen = (await c.call_tool("resumen", {"codigo": "PN01273PM", "desde": "2020-01", "hasta": "2024-12"})).data
        episodios = (await c.call_tool("episodios_fuera_de_rango", {
            "codigo": "PN01273PM", "desde": "2020-01", "hasta": "2024-12", "minimo": 1, "maximo": 3})).data
        recurso = await c.read_resource("bcrp://serie/PN01273PM")
        prompt = await c.get_prompt("informe", {"tema": "inflacion de Lima"})
    return {"herramientas": herramientas, "plantillas_de_recurso": plantillas, "prompts": prompts,
            "buscar_series": busqueda, "resumen": resumen, "episodios_fuera_de_rango": episodios,
            "recurso": json.loads(recurso[0].text), "prompt": prompt.messages[0].content.text}


def con_claude(modelo: str) -> None:
    for nombre, pedido in PEDIDOS_CLAUDE.items():
        cmd = ["claude", "-p", pedido, "--model", modelo, "--output-format", "stream-json", "--verbose",
               "--no-session-persistence", "--setting-sources", "project,local", "--strict-mcp-config",
               "--mcp-config", str(ROOT / ".mcp.json"), "--allowedTools", "mcp__bcrp__*"]
        proceso = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
                                 stdin=subprocess.DEVNULL, capture_output=True, timeout=600, env=espacio_limpio.entorno())
        (OUT / f"claude_{nombre}.jsonl").write_text(proceso.stdout, encoding="utf-8")
        (OUT / f"claude_{nombre}.stderr.txt").write_text(proceso.stderr, encoding="utf-8")
        print(nombre, "codigo de salida", proceso.returncode, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", action="store_true")
    parser.add_argument("--modelo", default="sonnet")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.claude:
        con_claude(args.modelo)
        return
    datos = asyncio.run(cliente())
    (OUT / "cliente_mcp.json").write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Herramientas:", datos["herramientas"])
    print("Recursos:", datos["plantillas_de_recurso"], "| Prompts:", datos["prompts"])
    print("Episodio mas largo:", datos["episodios_fuera_de_rango"]["episodio_mas_largo"])


if __name__ == "__main__":
    main()
