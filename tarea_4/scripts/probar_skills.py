"""Demuestra con Claude Code real que las tres Skills se invocan y se encadenan.

Cada pedido corre en una copia limpia, sin base procesada: asi un mapa o un grafico tiene que
activar antes la limpieza. Guarda la traza JSONL y una tabla con lo que se observo.

    uv run python scripts/probar_skills.py --modelo sonnet
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import espacio_limpio

OUT = ROOT / "evidencias_ia" / "skills"
PEDIDOS = [
    ("manual_limpiando", "/limpiando-enaho", {"limpiando-enaho"}, ["salidas/validacion.txt"]),
    ("natural_limpiando", "Limpia los módulos de la ENAHO 2024 del INEI y dime si la base quedó validada.",
     {"limpiando-enaho"}, ["salidas/validacion.txt"]),
    ("natural_grafico", "Grafica la pobreza monetaria urbana y rural con ENAHO 2024.",
     {"graficando-enaho", "limpiando-enaho"}, ["figuras/pobreza_area_2024.png"]),
    ("natural_mapa", "Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024.",
     {"mapeando-enaho", "limpiando-enaho"}, ["mapas/pobreza_departamento.png"]),
]


def comando(pedido: str, modelo: str, espacio: Path) -> list[str]:
    return ["claude", "-p", pedido, "--model", modelo, "--output-format", "stream-json", "--verbose",
            "--no-session-persistence", "--setting-sources", "project,local", "--strict-mcp-config",
            "--mcp-config", str(espacio / ".mcp.json"), "--tools", "Bash,Read,Skill,Glob,Grep",
            "--allowedTools", "Read", "Glob", "Grep", "Skill", "mcp__bcrp__*", "Bash(uv run python *)"]


def skills_en_traza(salida: str) -> list[str]:
    vistas = []
    for linea in salida.splitlines():
        try:
            evento = json.loads(linea)
        except json.JSONDecodeError:
            continue
        mensaje = evento.get("message") if isinstance(evento, dict) else None
        if not isinstance(mensaje, dict):
            continue
        for item in mensaje.get("content") or []:
            if isinstance(item, dict) and item.get("type") == "tool_use" and item.get("name") == "Skill":
                entrada = item.get("input") or {}
                vistas.append(str(entrada.get("skill") or entrada.get("name") or "").removeprefix("/"))
    return vistas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="sonnet")
    parser.add_argument("--solo", nargs="*")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    resumen_ruta = OUT / "resumen_skills.json"
    resumen = json.loads(resumen_ruta.read_text(encoding="utf-8")) if resumen_ruta.is_file() else {}
    for nombre, pedido, esperadas, archivos in PEDIDOS:
        if args.solo and nombre not in args.solo:
            continue
        carpeta = espacio_limpio.crear(Path(tempfile.mkdtemp(prefix=f"skills_{nombre}_")), con_referencias=True)
        inicio = time.perf_counter()
        try:
            proceso = subprocess.run(comando(pedido, args.modelo, carpeta), cwd=carpeta, text=True, encoding="utf-8",
                                     errors="replace", capture_output=True, timeout=900, env=espacio_limpio.entorno())
            (OUT / f"{nombre}.jsonl").write_text(proceso.stdout, encoding="utf-8")
            (OUT / f"{nombre}.stderr.txt").write_text(proceso.stderr, encoding="utf-8")
            vistas = skills_en_traza(proceso.stdout)
            sin_slash = nombre.startswith("manual")  # /skill se expande sin llamar a la herramienta Skill
            hay_archivos = {a: (carpeta / a).is_file() for a in archivos}
            resumen[nombre] = {
                "pedido": pedido, "skills_invocadas": vistas, "skills_esperadas": sorted(esperadas),
                "archivos_creados": hay_archivos, "codigo_salida": proceso.returncode,
                "segundos": round(time.perf_counter() - inicio, 1),
                "cumple": all(hay_archivos.values()) and proceso.returncode == 0
                and (sin_slash or esperadas <= set(vistas))}
        finally:
            espacio_limpio.borrar(carpeta)
        print(nombre, resumen[nombre], flush=True)
        resumen_ruta.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    if not all(r["cumple"] for r in resumen.values()):
        raise SystemExit("Hay pedidos que no cumplieron: revisar las trazas antes de declarar nada.")


if __name__ == "__main__":
    main()
