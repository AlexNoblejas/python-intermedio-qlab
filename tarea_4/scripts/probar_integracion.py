"""Ejecuta y audita la integracion real Claude Code + 2 MCP + 2 Skills.

Requiere instalacion local de Claude Code, sesion autenticada, acceso BCRP y
ENAHO 2024 previamente descargada. No fabrica trazas en caso de bloqueo.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import espacio_limpio

OUT = ROOT / "evidencias_ia" / "integracion"


def analizar_traza(contenido: str) -> dict:
    llamadas_mcp = []
    invocaciones_skill = []
    llamadas_otras = []
    resultados = []
    for linea in contenido.splitlines():
        try:
            ev = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict):
            continue
        if ev.get("type") == "result":
            resultados.append({"is_error": ev.get("is_error"), "subtype": ev.get("subtype")})
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        for item in msg.get("content") or []:
            if not isinstance(item, dict) or item.get("type") != "tool_use":
                continue
            nombre = str(item.get("name") or "")
            args = item.get("input") or {}
            if nombre.startswith("mcp__bcrp__"):
                llamadas_mcp.append(nombre)
            elif nombre == "Skill":
                skill = args.get("skill") or args.get("name") or "desconocida"
                invocaciones_skill.append(str(skill).removeprefix("/"))
            else:
                llamadas_otras.append(nombre)
    mcp_unicos = sorted(set(llamadas_mcp))
    skills_unicos = sorted(set(invocaciones_skill))
    # En el reporte se distinguen eventos observados de ejecuciones que pudieron fallar.
    return {
        "mcp_unicos": mcp_unicos,
        "skills_unicas": skills_unicos,
        "n_mcp": len(llamadas_mcp),
        "n_skills": len(invocaciones_skill),
        "otros": sorted(set(llamadas_otras)),
        "hay_resultado": bool(resultados),
        "resultado_sin_error": bool(resultados) and all(r.get("is_error") is not True for r in resultados),
        "cumple_minimo_de_invocaciones": len(mcp_unicos) >= 2 and len(skills_unicos) >= 2,
    }


def construir_comando(prompt: str, modelo: str) -> list[str]:
    return ["claude", "-p", prompt,
            "--model", modelo,
            "--output-format", "stream-json", "--verbose", "--no-session-persistence",
            "--setting-sources", "project,local", "--strict-mcp-config",
            "--mcp-config", str(OUT / "mcp_solo_bcrp.json"),
            "--tools", "Bash,Read,Skill,Glob,Grep,Write,Edit",
            "--allowedTools", "Read", "Glob", "Grep", "Skill", "Write", "Edit", "mcp__bcrp__*",
            "Bash(uv run python *)"]


def vaciar_salidas() -> None:
    """Lo que el informe use debe generarlo el agente en esta misma ejecucion."""
    for carpeta in ("salidas", "figuras", "mapas"):
        for ruta in (ROOT / carpeta).iterdir():
            if ruta.is_file() and ruta.name != ".gitkeep":
                ruta.unlink()
    (ROOT / "informes" / "informe_final.md").unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--modelo", default="sonnet")
    p.add_argument("--solo-analizar", type=Path, default=None,
                   help="Audita un log JSONL existente sin invocar Claude")
    args = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.solo_analizar is not None:
        registro = args.solo_analizar.read_text(encoding="utf-8")
        duracion, rc = None, None
    else:
        if not shutil.which("claude"):
            raise SystemExit("Claude Code no esta disponible. Ejecutar solo en el PC con Claude instalado.")
        for ruta in [ROOT / "datos" / "966-Modulo34.zip", ROOT / "datos" / "966-Modulo02.zip"]:
            if not ruta.is_file():
                raise SystemExit(f"Falta un insumo para la integracion real: {ruta}")
        prompt = (ROOT / "PROMPT_AGENTE.md").read_text(encoding="utf-8")
        vaciar_salidas()
        (OUT / "mcp_solo_bcrp.json").write_text(json.dumps(espacio_limpio.SOLO_BCRP, indent=2), encoding="utf-8")
        inicio = time.perf_counter()
        proc = subprocess.run(construir_comando(prompt, args.modelo), cwd=ROOT, text=True, encoding="utf-8",
                              errors="replace", stdin=subprocess.DEVNULL, capture_output=True, timeout=1800, env=espacio_limpio.entorno())
        duracion, rc = round(time.perf_counter() - inicio, 2), proc.returncode
        registro = proc.stdout
        (OUT / "claude_integracion.stderr.txt").write_text(proc.stderr, encoding="utf-8")
        (OUT / "claude_integracion.jsonl").write_text(registro, encoding="utf-8")
    r = analizar_traza(registro)
    r["duracion_segundos"] = duracion
    r["codigo_salida"] = rc
    r["estado"] = "APROBADO_PARCIAL" if r["cumple_minimo_de_invocaciones"] and r["resultado_sin_error"] and rc in (0, None) else "NO_VERIFICADO"
    (OUT / "auditoria_traza.json").write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    txt = ["# Auditoria de la integracion real Claude Code", "",
           "Se examinan mensajes tool_use efectivamente registrados, no nombres declarados en el prompt.", "",
           f"- Herramientas MCP distintas: **{len(r['mcp_unicos'])}** (minimo 2): {r['mcp_unicos']}",
           f"- Skills distintas invocadas: **{len(r['skills_unicas'])}** (minimo 2): {r['skills_unicas']}",
           f"- Resultado final sin error de Claude: **{r['resultado_sin_error']}**",
           f"- Salida del CLI: **{rc}**; duracion: **{duracion}** s", "",
           f"**Estado de invocaciones: {r['estado']}**", "",
           "La comprobacion de calidad de cifras y salidas requiere inspeccion independiente. ",
           "Si no se detectan llamadas, revise las trazas y repita la sesion en Claude Code;", 
           "no infiera uso de Skills por la mera ejecucion de comandos Bash."]
    (OUT / "auditoria_integracion.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))
    if r["estado"] != "APROBADO_PARCIAL":
        raise SystemExit("La evidencia no acredita el minimo de integracion MCP + Skills.")


if __name__ == "__main__":
    main()
