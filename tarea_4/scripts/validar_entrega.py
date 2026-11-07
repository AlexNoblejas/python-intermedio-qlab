"""Puerta de calidad de Tarea 4. No declara aprobacion sin evidencias reales.

Uso: uv run python scripts/validar_entrega.py [--exigir-completo]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def comprobar() -> list[tuple[str, bool, str]]:
    comprobaciones: list[tuple[str, bool, str]] = []

    def registrar(titulo: str, ok: bool, detalle: str):
        comprobaciones.append((titulo, ok, detalle))

    # Estructura: constata que hay implementacion, no que esta ejecutada.
    f = [ROOT / ".mcp.json", ROOT / "mcp/server.py", ROOT / "mcp/test_server.py",
         ROOT / "mcp/test_herramienta_propia.py"]
    registrar("Codigo MCP y configuracion", all(p.is_file() for p in f), "5 herramientas, recurso/prompt: comprobar con cliente real")
    skills = [ROOT / ".claude/skills" / n / "SKILL.md"
              for n in ("limpiando-enaho", "graficando-enaho", "mapeando-enaho")]
    registrar("Tres Skills en el proyecto", all(p.is_file() for p in skills), "Se debe demostrar activacion real")

    # No basta saber que el test existe: el registro debe proceder de pytest real.
    registro = ROOT / "evidencias_ia/mcp/pruebas_10.txt"
    texto = registro.read_text(encoding="utf-8") if registro.is_file() else ""
    registrar("10 tests MCP sobre BCRP real", "10 passed" in texto and "failed" not in texto.lower(),
              str(registro.relative_to(ROOT)))

    val = ROOT / "salidas/validacion.txt"
    txt = val.read_text(encoding="utf-8") if val.is_file() else ""
    registrar("ENAHO real, 108664 y 27.6%", "RESULTADO: APROBADO" in txt and "Residentes habituales: 108664" in txt,
              str(val.relative_to(ROOT)))
    indicadores = ROOT / "salidas/indicadores.csv"
    if indicadores.exists():
        with indicadores.open(encoding="utf-8", newline="") as handle:
            filas = list(csv.DictReader(handle))
        dep = [r for r in filas if r.get("nivel") == "Departamento"]
        ok_25 = len(dep) == 25 and len({r.get("codigo") for r in dep}) == 25
    else:
        ok_25 = False
    registrar("25 indicadores territoriales", ok_25, "salidas/indicadores.csv")
    fig = [ROOT / "figuras/pobreza_area_2024.png", ROOT / "mapas/pobreza_departamento.png"]
    hay_bcrp = bool(list((ROOT / "figuras").glob("bcrp_*.png")))
    registrar("Grafico BCRP + ENAHO + mapa", all(p.is_file() and p.stat().st_size > 3000 for p in fig) and hay_bcrp,
              "figuras/ y mapas/ con resultados oficiales")

    r = ROOT / "evidencias_ia/integracion/auditoria_traza.json"
    try:
        data = json.loads(r.read_text(encoding="utf-8"))
        integrado = (bool(data.get("cumple_minimo_de_invocaciones")) and
                     bool(data.get("resultado_sin_error")) and data.get("codigo_salida") == 0)
    except (ValueError, OSError):
        integrado = False
    registrar("En una sesion: >=2 MCP y >=2 Skills", integrado, "auditoria_traza.json + registro JSONL")

    results = ROOT / "evaluacion/resultados.csv"
    if results.is_file():
        with results.open(encoding="utf-8", newline="") as handle:
            fila_resultados = list(csv.DictReader(handle))
        campos = {(r.get("id"), r.get("modo")) for r in fila_resultados}
        exp = {(f"{i:02d}", modo) for i in range(1, 11) for modo in ("sin", "con")}
        ok_res = campos == exp and len(fila_resultados) == 20 and all(r.get("returncode") == "0" for r in fila_resultados)
    else:
        ok_res = False
    registrar("Experimento 10 x 2, sin errores CLI", ok_res, "evaluacion/resultados.csv y 20 JSONL")

    logs = list((ROOT / "evidencias_ia/evaluacion").glob("*.jsonl"))
    registrar("20 trazas de evaluacion", len(logs) == 20, "evidencias_ia/evaluacion")
    verificaciones = ROOT / "auditoria/VERIFICACIONES_MANUALES.md"
    v_text = verificaciones.read_text(encoding="utf-8") if verificaciones.is_file() else ""
    # Requiere que el alumno sustituya todas las seis casillas PENDIENTE por evidencia.
    hechos = v_text.count("| VALIDADO |") >= 3 and "PENDIENTE" not in v_text
    registrar("Tres afirmaciones verificadas independientemente", hechos,
              "auditoria/VERIFICACIONES_MANUALES.md")
    informe = ROOT / "informes/informe_final.md"
    i_txt = informe.read_text(encoding="utf-8") if informe.is_file() else ""
    registrar("Informe sin verificaciones pendientes", len(i_txt) > 800 and "PENDIENTE" not in i_txt,
              "informes/informe_final.md")
    # No basta que un reporte exista: requiere al menos un transcript real de desarrollo.
    evidencia = [p for p in (ROOT / "evidencias_ia").rglob("*") if p.is_file() and p.suffix.lower() in (".jsonl", ".md", ".txt", ".html") and p.name != "LEEME.md"]
    registrar("Conversaciones IA y evidencias completas", len(evidencia) >= 22,
              "Auditar que incluya historiales de desarrollo y no solo trazas de las pruebas")
    resumen = ROOT / "evidencias_ia/skills/resumen_skills.json"
    try:
        skills_ok = all(r.get("cumple") for r in json.loads(resumen.read_text(encoding="utf-8")).values())
    except (ValueError, OSError):
        skills_ok = False
    registrar("Skills: invocacion manual, natural y encadenada", skills_ok, "evidencias_ia/skills/resumen_skills.json")
    comparacion = ROOT / "evaluacion/comparacion.md"
    registrar("Comparacion del experimento", comparacion.is_file() and comparacion.stat().st_size > 800,
              "evaluacion/comparacion.md")
    desarrollo = list((ROOT / "evidencias_ia/desarrollo").glob("*")) if (ROOT / "evidencias_ia/desarrollo").is_dir() else []
    registrar("Historial de desarrollo con asistentes", len(desarrollo) >= 1, "evidencias_ia/desarrollo/")
    return comprobaciones


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exigir-completo", action="store_true")
    args = parser.parse_args()
    checks = comprobar()
    report = ["# Verificacion automatica previa a publicar", "",
              "El control indica presencia de evidencias; la docente puede evaluar su calidad aparte.", ""]
    for nombre, ok, detalle in checks:
        report.append(f"- [{'x' if ok else ' '}] {nombre}: {detalle}")
    report += ["", f"**Controles completos: {sum(t[1] for t in checks)}/{len(checks)}**", "",
               "**No subir** si falta una prueba obligatoria o una evidencia verificada."]
    out = ROOT / "auditoria/CONTROL_PUBLICACION.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    if args.exigir_completo and not all(x[1] for x in checks):
        raise SystemExit("BLOQUEADO: la entrega aun no supera todos los controles.")


if __name__ == "__main__":
    main()
