"""Pruebas de anti-contaminacion, contenido y evaluacion; sin Internet."""
import importlib.util
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


descarga = load("scripts/descargar_datos.py", "descarga_offline")
evaluar = load("evaluacion/evaluar.py", "evaluar_offline")


def test_inei_correct_url_and_fallback():
    for label in ("modulo34", "modulo02"):
        urls = descarga.FUENTES[label]["urls"]
        assert "/iinei/srienaho/descarga/STATA/966-Modulo" in urls[0]
        assert urls[0] != urls[1]


def test_fake_html_response_rejected(tmp_path):
    file = tmp_path / "fake.zip"
    file.write_bytes(b"<html>Lo sentimos</html>" * 200)
    with pytest.raises(ValueError, match="ZIP valido"):
        descarga.verificar_contenido(file, "sumaria-2024")


def test_wrong_module_rejected(tmp_path):
    file = tmp_path / "modulo.zip"
    with zipfile.ZipFile(file, "w") as z:
        z.writestr("another-module-2024.dta", "irrelevant")
    with pytest.raises(ValueError, match="unico DTA esperado"):
        descarga.verificar_contenido(file, "sumaria-2024")


def test_valid_expected_zip_is_accepted(tmp_path):
    file = tmp_path / "modulo.zip"
    with zipfile.ZipFile(file, "w") as z:
        z.writestr("nested/sumaria-2024.dta", "irrelevant")
    descarga.verificar_contenido(file, "sumaria-2024")


def test_bad_geojson_rejected(tmp_path):
    file = tmp_path / "geo.json"
    file.write_text(json.dumps({"type":"FeatureCollection", "features":[{"properties":{"FIRST_IDDP":"01"}}]}))
    with pytest.raises(ValueError, match="25"):
        descarga.verificar_contenido(file, "geojson")


def test_valid_geojson_is_accepted(tmp_path):
    file = tmp_path / "geo.json"
    file.write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type":"Feature", "properties":{"FIRST_IDDP":f"{i:02d}"}, "geometry": None}
        for i in range(1, 26)]}))
    descarga.verificar_contenido(file, "geojson")


def test_no_download_if_existing_archive_is_valid(tmp_path, monkeypatch):
    file = tmp_path / "modulo.zip"
    with zipfile.ZipFile(file, "w") as z:
        z.writestr("sumaria-2024.dta", "irrelevant")
    monkeypatch.setattr(descarga.httpx, "stream", lambda *args, **kw: (_ for _ in ()).throw(AssertionError("network should not be called")))
    assert descarga.descargar(["http://example.invalid"], file, "sumaria-2024") == "existente"


def test_initial_baseline_blocks_three_categories():
    args = evaluar.construir_comando("sample", "sin", "sonnet")
    assert args[args.index("--tools") + 1] == ""
    assert args[args.index("--disallowedTools") + 1] == "mcp__*"
    assert "--disable-slash-commands" in args
    assert "--strict-mcp-config" in args
    assert "--mcp-config" not in args


def test_treatment_loads_only_project_mcp_and_skills():
    args = evaluar.construir_comando("sample", "con", "sonnet")
    assert args[args.index("--mcp-config") + 1] == str(ROOT / ".mcp.json")
    aislado = evaluar.construir_comando("sample", "con", "sonnet", ROOT / "copia")
    assert aislado[aislado.index("--mcp-config") + 1] == str(ROOT / "copia" / ".mcp.json")
    assert "Skill" in args[args.index("--tools") + 1]
    assert "mcp__bcrp__*" in args
    assert "--disable-slash-commands" not in args


def test_invalid_mode_rejected():
    with pytest.raises(ValueError, match="Modo"):
        evaluar.construir_comando("sample", "unknown", "sonnet")


def test_grade_both_sources_required():
    row = {"verdad_bcrp":"4.55", "verdad_enaho":"27.53", "tolerancia_bcrp":"0.05", "tolerancia_enaho":"0.1", "tipo":"MIXTA"}
    assert evaluar.puntuacion(row, 4.55, 27.53, "text") == (True, True)
    assert evaluar.puntuacion(row, 4.55, 20, "text") == (False, True)
    assert evaluar.puntuacion(row, None, 27.53, "text") == (False, True)


def test_read_stream_json_events():
    a = {"type":"assistant", "message":{"content":[{"type":"tool_use", "name":"mcp__bcrp__serie"}]}}
    b = {"type":"result", "structured_output":{"bcrp":4.55, "enaho":None, "interpretacion":"", "fuentes":"BCRP"}}
    data, tools = evaluar.interpretar_eventos(json.dumps(a) + "\n" + json.dumps(b))
    assert data["bcrp"] == pytest.approx(4.55)
    assert tools == ["mcp__bcrp__serie"]

integracion = load("scripts/probar_integracion.py", "integracion_offline")


def test_trace_parser_detects_mcp_and_skills_in_same_run():
    tools = [("mcp__bcrp__buscar_series", {}),
             ("Skill", {"skill": "limpiando-enaho"}),
             ("mcp__bcrp__resumen", {}),
             ("Skill", {"skill": "mapeando-enaho"})]
    events = [json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": name, "input": inp}]}}) for name, inp in tools]
    events.append(json.dumps({"type":"result", "is_error": False}))
    result = integracion.analizar_traza("\n".join(events))
    assert len(result["mcp_unicos"]) == 2
    assert len(result["skills_unicas"]) == 2
    assert result["cumple_minimo_de_invocaciones"]
    assert result["resultado_sin_error"]


def test_trace_parser_rejects_bash_without_actual_skills():
    events = [json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command":"uv run python limpiar.py"}},
        {"type": "tool_use", "name": "mcp__bcrp__buscar_series", "input": {}}]}}),
        json.dumps({"type":"result", "is_error": False})]
    result = integracion.analizar_traza("\n".join(events))
    assert result["skills_unicas"] == []
    assert not result["cumple_minimo_de_invocaciones"]


def test_nonnumeric_results_count_as_wrong_not_exception():
    row = {"verdad_bcrp":"4.55", "verdad_enaho":"", "tolerancia_bcrp":"0.05", "tolerancia_enaho":"0.1", "tipo":"BCRP"}
    assert evaluar.puntuacion(row, "n.d.", None, "") == (False, False)


def test_malformed_json_event_does_not_crash():
    s = "{}\n" + json.dumps({"type":"message", "message":"hello"}) + "\n"
    assert evaluar.interpretar_eventos(s) == ({}, [])


def test_clean_workspace_hides_answers_and_results(tmp_path):
    import espacio_limpio
    copia = espacio_limpio.crear(tmp_path / "copia")
    assert (copia / ".claude/skills/limpiando-enaho/SKILL.md").is_file()
    assert (copia / "mcp/server.py").is_file()
    for ausente in ("evaluacion", "salidas", "informes", "evidencias_ia", "referencias", "auditoria", "CLAUDE.md"):
        assert not (copia / ausente).exists(), ausente


def test_result_classes_separate_silence_from_error():
    fila = {"verdad_bcrp": "4.55", "verdad_enaho": ""}
    assert evaluar.clasificar(fila, 4.55, None, True) == "acierta"
    assert evaluar.clasificar(fila, 9.0, None, False) == "incorrecta"
    assert evaluar.clasificar(fila, None, None, False) == "no contesta"


def test_trace_flags_access_to_project_files():
    linea = json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Read", "input": {"file_path": "evaluacion/preguntas.csv"}}]}})
    assert evaluar.detalles_de_traza(linea)["fuga"] is True
