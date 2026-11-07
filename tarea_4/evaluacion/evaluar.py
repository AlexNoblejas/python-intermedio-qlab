"""Comparacion reproducible entre Claude Code sin y con MCP + Skills: 10 preguntas en 2 modos.

Modo sin: sin herramientas, sin MCP, sin Skills, en una carpeta vacia.
Modo con: servidor bcrp y Skills, en una copia limpia por pregunta (scripts/espacio_limpio.py), sin
salidas previas ni acceso a preguntas.csv. Las respuestas esperadas se fijan antes de correr esto.

    uv run python evaluacion/evaluar.py --dry-run
    uv run python evaluacion/evaluar.py --modelo sonnet
    uv run python evaluacion/evaluar.py --solo 05 --modos con   # repite sin tocar el resto
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import espacio_limpio

ARCHIVO = ROOT / "evaluacion" / "preguntas.csv"
RESULTADOS = ROOT / "evaluacion" / "resultados.csv"
EVIDENCIA = ROOT / "evidencias_ia" / "evaluacion"
ESQUEMA = {"type": "object", "required": ["bcrp", "enaho", "interpretacion", "fuentes"],
           "properties": {"bcrp": {"type": ["number", "null"]},
                          "enaho": {"type": ["number", "null"]},
                          "interpretacion": {"type": "string"}, "fuentes": {"type": "string"}}}
INSTRUCCION = (
    "Responde solo usando evidencia a la que tengas acceso en esta ejecucion. "
    "Si falta una fuente o no puedes comprobar el valor, devuelve null: nunca estimes. "
    "En bcrp pon el numero que venga del BCRP si se pregunta y en enaho el que venga de la ENAHO si se pregunta. "
    "Da cada cifra en la unidad que pide la pregunta. En interpretacion explica los limites de la respuesta y "
    "evita afirmar causalidad no probada. En fuentes incluye la URL o ruta que permita verificar la cifra.\n\n"
)
CAMPOS = ["id", "tipo", "modo", "pregunta", "esperado_bcrp", "esperado_enaho", "obtenido_bcrp", "obtenido_enaho",
          "tolerancia_bcrp", "tolerancia_enaho", "interpretacion", "fuentes", "herramientas_observadas",
          "skills_observadas", "correcto_numerico", "resultado", "revision_manual_mixta", "segundos", "modelo",
          "tocó_archivos_del_proyecto", "error", "returncode"]


def puntuacion(fila, valor_b, valor_e, interpretacion):
    aciertos = []
    for campo, respuesta in (("bcrp", valor_b), ("enaho", valor_e)):
        if fila["verdad_" + campo]:
            esperado = float(fila["verdad_" + campo])
            tolerancia = float(fila["tolerancia_" + campo])
            try:
                aciertos.append(respuesta is not None and abs(float(respuesta) - esperado) <= tolerancia)
            except (ValueError, TypeError, OverflowError):
                aciertos.append(False)
    numerico = bool(aciertos) and all(aciertos)
    revision = fila["tipo"] == "MIXTA"
    return numerico, revision


def clasificar(fila, valor_b, valor_e, numerico: bool) -> str:
    """acierta, incorrecta o no contesta: esta ultima solo si faltan todas las cifras pedidas."""
    pedidas = [v for campo, v in (("bcrp", valor_b), ("enaho", valor_e)) if fila["verdad_" + campo]]
    if numerico:
        return "acierta"
    return "no contesta" if all(v is None for v in pedidas) else "incorrecta"


def interpretar_eventos(salida: str):
    eventos = []
    for linea in salida.splitlines():
        try:
            eventos.append(json.loads(linea))
        except json.JSONDecodeError:
            pass
    herramientas = []
    datos = None
    for evento in eventos:
        if not isinstance(evento, dict):
            continue
        mensaje = evento.get("message") or {}
        if not isinstance(mensaje, dict):
            mensaje = {}
        for item in (mensaje.get("content") or []):
            if isinstance(item, dict) and item.get("type") == "tool_use":
                herramientas.append(item.get("name", ""))
        if evento.get("type") == "result":
            datos = evento.get("structured_output")
            if not datos and isinstance(evento.get("result"), str):
                try:
                    datos = json.loads(evento["result"])
                except json.JSONDecodeError:
                    pass
    return datos if isinstance(datos, dict) else {}, sorted(set(herramientas))


def detalles_de_traza(salida: str) -> dict:
    """Modelo, Skills y si algun comando apunto a la carpeta real del proyecto."""
    modelo, skills, fuga = "", set(), False
    raiz = str(ROOT).replace("\\", "/").lower()
    for linea in salida.splitlines():
        try:
            evento = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if not isinstance(evento, dict):
            continue
        if evento.get("type") == "system" and evento.get("subtype") == "init":
            modelo = evento.get("model", modelo)
        mensaje = evento.get("message")
        if not isinstance(mensaje, dict):
            continue
        for item in mensaje.get("content") or []:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                entrada = item.get("input") or {}
                if item.get("name") == "Skill":
                    skills.add(str(entrada.get("skill") or entrada.get("name") or "").removeprefix("/"))
                texto = json.dumps(entrada, ensure_ascii=False).replace("\\\\", "/").lower()
                if raiz in texto or "preguntas.csv" in texto or "resultados.csv" in texto:
                    fuga = True
    return {"modelo": modelo, "skills": sorted(skills), "fuga": fuga}


def construir_comando(pregunta: str, modo: str, modelo: str, espacio: Path | None = None) -> list[str]:
    """--tools restringe solo las herramientas integradas; el control apaga aparte MCP y Skills."""
    cmd = ["claude", "-p", INSTRUCCION + pregunta, "--output-format", "stream-json", "--verbose",
           "--json-schema", json.dumps(ESQUEMA), "--no-session-persistence", "--model", modelo,
           "--setting-sources", "project,local"]  # sin plugins ni ajustes personales en ambos modos
    if modo == "sin":
        cmd += ["--strict-mcp-config", "--tools", "", "--disallowedTools", "mcp__*",
                "--disable-slash-commands"]
    elif modo == "con":
        cmd += ["--strict-mcp-config", "--mcp-config", str((espacio or ROOT) / ".mcp.json"),
                "--tools", "Bash,Read,Skill,Glob,Grep",
                "--allowedTools", "Read", "Glob", "Grep", "Skill", "mcp__bcrp__*",
                "Bash(uv run python *)"]
    else:
        raise ValueError("Modo esperado: 'sin' o 'con'")
    return cmd


def preguntar(pregunta: str, modo: str, modelo: str):
    """Cada pregunta corre en su propia sesion y su propia carpeta temporal."""
    carpeta = Path(tempfile.mkdtemp(prefix=f"eval_{modo}_"))
    try:
        if modo == "con":
            espacio_limpio.crear(carpeta)
        start = time.perf_counter()
        try:
            proceso = subprocess.run(construir_comando(pregunta, modo, modelo, carpeta), text=True, encoding="utf-8",
                                     errors="replace", capture_output=True, timeout=600, cwd=carpeta,
                                     env=espacio_limpio.entorno())
            salida, errores, rc = proceso.stdout, proceso.stderr, proceso.returncode
        except subprocess.TimeoutExpired as e:
            salida = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            errores, rc = "Tiempo excedido: 600 s", 124
        duracion = round(time.perf_counter() - start, 2)
    finally:
        espacio_limpio.borrar(carpeta)
    data, herramientas = interpretar_eventos(salida)
    return data, herramientas, duracion, rc, salida, errores


def cargar_previos() -> list[dict]:
    if not RESULTADOS.is_file():
        return []
    with RESULTADOS.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="sonnet")
    parser.add_argument("--modos", nargs="+", choices=["sin", "con"], default=["sin", "con"])
    parser.add_argument("--solo", nargs="*", help="Ids a correr; conserva los demas resultados")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with ARCHIVO.open(encoding="utf-8", newline="") as f:
        preguntas = list(csv.DictReader(f))
    if len(preguntas) != 10:
        raise SystemExit("La bateria debe contener exactamente 10 preguntas.")
    if [sum(p["tipo"] == t for p in preguntas) for t in ("BCRP", "ENAHO", "MIXTA")] != [4, 4, 2]:
        raise SystemExit("La distribucion de las 10 preguntas es incorrecta.")
    if any((p["codigo_bcrp"] and not p["verdad_bcrp"]) or
           (p["nivel_enaho"] and not p["verdad_enaho"]) for p in preguntas):
        raise SystemExit("Faltan respuestas esperadas verificables. Ejecute preparar_verdades.py.")
    if args.dry_run:
        print("Archivo validado. 10 preguntas con verdades y tolerancias listas. No se consulto Claude.")
        return
    if not shutil.which("claude"):
        raise SystemExit("No esta instalada la CLI claude. Instalar Claude Code y autenticarse primero.")
    EVIDENCIA.mkdir(parents=True, exist_ok=True)
    filas = {(r["id"], r["modo"]): r for r in cargar_previos()}
    for pregunta in preguntas:
        if args.solo and pregunta["id"] not in args.solo:
            continue
        for modo in args.modos:
            data, tools, sec, rc, salida, errores = preguntar(pregunta["pregunta"], modo, args.modelo)
            suf = f"{pregunta['id']}_{modo}"
            (EVIDENCIA / f"{suf}.jsonl").write_text(salida, encoding="utf-8")
            (EVIDENCIA / f"{suf}.stderr.txt").write_text(errores, encoding="utf-8")
            detalle = detalles_de_traza(salida)
            correcto, revision = puntuacion(pregunta, data.get("bcrp"), data.get("enaho"), data.get("interpretacion", ""))
            resultado = clasificar(pregunta, data.get("bcrp"), data.get("enaho"), correcto)
            filas[(pregunta["id"], modo)] = {
                "id": pregunta["id"], "tipo": pregunta["tipo"], "modo": modo, "pregunta": pregunta["pregunta"],
                "esperado_bcrp": pregunta["verdad_bcrp"], "esperado_enaho": pregunta["verdad_enaho"],
                "obtenido_bcrp": data.get("bcrp"), "obtenido_enaho": data.get("enaho"),
                "tolerancia_bcrp": pregunta["tolerancia_bcrp"], "tolerancia_enaho": pregunta["tolerancia_enaho"],
                "interpretacion": data.get("interpretacion", ""), "fuentes": data.get("fuentes", ""),
                "herramientas_observadas": ";".join(tools), "skills_observadas": ";".join(detalle["skills"]),
                "correcto_numerico": correcto, "resultado": resultado, "revision_manual_mixta": revision,
                "segundos": sec, "modelo": detalle["modelo"], "tocó_archivos_del_proyecto": detalle["fuga"],
                "error": errores.strip()[-300:] if rc else "", "returncode": rc}
            print(f"{suf}: {resultado}, {sec}s, herramientas: {tools}, skills: {detalle['skills']}", flush=True)
            orden = sorted(filas.values(), key=lambda r: (r["id"], r["modo"] != "sin"))
            with RESULTADOS.open("w", encoding="utf-8", newline="") as f:
                escritor = csv.DictWriter(f, fieldnames=CAMPOS)
                escritor.writeheader()
                escritor.writerows(orden)
    print(f"Guardados {len(filas)} resultados en {RESULTADOS}")


if __name__ == "__main__":
    main()
