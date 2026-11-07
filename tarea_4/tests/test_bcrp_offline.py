"""Independent business-logic tests with fake FastMCP; NOT the 8 live MCP tests.

This small shim makes unit testing possible in offline environments that cannot
install FastMCP. It does not test the MCP wire protocol or actual BCRP API.
"""
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

SERVER_PATH = Path(__file__).resolve().parents[1] / "mcp" / "server.py"


@pytest.fixture
def backend(monkeypatch):
    module = types.ModuleType("fastmcp")
    exceptions = types.ModuleType("fastmcp.exceptions")

    class ToolError(Exception):
        pass

    class FakeFastMCP:
        def __init__(self, *args, **kwargs):
            self.tools = {}
            self.resources = {}
            self.prompts = {}

        def tool(self, f=None, **kwargs):
            def decorate(func):
                self.tools[func.__name__] = (func, kwargs)
                return func
            return decorate(f) if f is not None else decorate

        def resource(self, uri):
            def decorate(func):
                self.resources[uri] = func
                return func
            return decorate

        def prompt(self, func):
            self.prompts[func.__name__] = func
            return func

    module.FastMCP = FakeFastMCP
    exceptions.ToolError = ToolError
    monkeypatch.setitem(sys.modules, "fastmcp", module)
    monkeypatch.setitem(sys.modules, "fastmcp.exceptions", exceptions)
    spec = importlib.util.spec_from_file_location("bcrp_offline_fixture", SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    return server


def catalog():
    return pd.DataFrame([
        {"codigo": "PN01273PM", "categoria": "Precios", "grupo": "IPC 12 meses", "nombre": "Inflacion de Lima", "frecuencia": "Mensual", "inicio": "2020", "actualizada": "2026", "texto": "precios ipc 12 meses inflacion de lima"},
        {"codigo": "PD04638PD", "categoria": "Tipo de cambio", "grupo": "Interbancario", "nombre": "Venta", "frecuencia": "Diaria", "inicio": "2020", "actualizada": "2026", "texto": "tipo de cambio interbancario venta"},
        {"codigo": "PA00001PA", "categoria": "PBI", "grupo": "Producto", "nombre": "Anual", "frecuencia": "Anual", "inicio": "2020", "actualizada": "2026", "texto": "pbi producto anual"},
        {"codigo": "PQ00001PQ", "categoria": "PBI", "grupo": "Producto", "nombre": "Trimestral", "frecuencia": "Trimestral", "inicio": "2020", "actualizada": "2026", "texto": "pbi producto trimestral"},
    ])


def patch_catalog(backend, monkeypatch):
    monkeypatch.setattr(backend, "catalogo", catalog)


def test_discover_tools_resource_prompt(backend):
    assert {"buscar_series", "serie", "resumen", "comparar_series", "graficar_serie"} <= set(backend.mcp.tools)
    assert "bcrp://serie/{codigo}" in backend.mcp.resources
    assert "informe" in backend.mcp.prompts
    assert backend.mcp.tools["graficar_serie"][1]["annotations"]["readOnlyHint"] is False


def test_catalog_headers_semicolon_and_accents(backend, monkeypatch, tmp_path):
    archivo = tmp_path / "catalog.csv"
    archivo.write_text("Codigo de serie;Categoria de serie\n", encoding="utf-8")
    archivo.write_text("C\u00f3digo de serie;Categor\u00eda de serie;Grupo de serie;Nombre de serie;Frecuencia;Fecha de actualizaci\u00f3n;Fecha de inicio\nPN01273PM;Precios;IPC;Inflaci\u00f3n;Mensual;2026;2000\n", encoding="utf-8")
    monkeypatch.setattr(backend, "CATALOGO", archivo)
    backend.catalogo.cache_clear()
    result = backend.catalogo()
    assert result.loc[0, "codigo"] == "PN01273PM"
    assert "inflacion" in result.loc[0, "texto"]


def test_catalog_bad_headers_rejected(backend, monkeypatch, tmp_path):
    archivo = tmp_path / "catalog.csv"
    archivo.write_text("codigo;incorrecto\nabc;xyz\n", encoding="utf-8")
    monkeypatch.setattr(backend, "CATALOGO", archivo)
    backend.catalogo.cache_clear()
    with pytest.raises(Exception, match="falta"):
        backend.catalogo()


def test_search_catalog_and_ficha(backend, monkeypatch):
    patch_catalog(backend, monkeypatch)
    result = backend.buscar_series("IPC 12 meses", "Mensual")
    assert len(result) == 1
    assert result[0]["codigo"] == "PN01273PM"
    assert backend.buscar_series("cobre inexistente") == []
    assert backend._ficha("PD04638PD")["frecuencia"] == "Diaria"
    with pytest.raises(Exception, match="XX999"):
        backend._ficha("XX999")


@pytest.mark.parametrize("freq,value,expected", [
    ("Mensual", "2025-01", "2025-1"),
    ("Mensual", "2025-12", "2025-12"),
    ("Diaria", "2026-10-15", "2026-10-15"),
    ("Trimestral", "2025-T2", "2025-2"),
    ("Anual", "2024", "2024"),
])
def test_api_dates(backend, freq, value, expected):
    assert backend._fecha_api(value, backend._frecuencia(freq)) == expected


@pytest.mark.parametrize("freq,value,expected", [
    ("Mensual", "Ene.2025", "2025-01"),
    ("Mensual", "Set.2026", "2026-09"),
    ("Mensual", "Dic.2025", "2025-12"),
    ("Diaria", "01.Oct.26", "2026-10-01"),
    ("Diaria", "15.Oct.2026", "2026-10-15"),
    ("Trimestral", "T1.25", "2025-T1"),
    ("Trimestral", "T4.2024", "2024-T4"),
    ("Anual", "2024", "2024"),
])
def test_normalize_period(backend, freq, value, expected):
    assert backend._periodo_normalizado(value, backend._frecuencia(freq)) == expected


def test_invalid_periods_rejected(backend):
    for s, freq in [("2025-13", "mensual"), ("2025-01", "diaria"), ("2025-T5", "trimestral")]:
        with pytest.raises(Exception, match="invalida"):
            backend._fecha_api(s, freq)
    with pytest.raises(Exception, match="no se pudo interpretar"):
        backend._periodo_normalizado("XYZ", "mensual")


def test_serie_filters_missing_and_orders(backend, monkeypatch):
    patch_catalog(backend, monkeypatch)
    payload = {"periods": [
        {"name": "Mar.2025", "values": ["0.81"]},
        {"name": "Ene.2025", "values": ["1.51"]},
        {"name": "Feb.2025", "values": ["n.d."]},
        {"name": "Abr.2025", "values": ["1,234.5"]},
        {"name": "Dic.2024", "values": ["99"]},
    ]}
    monkeypatch.setattr(backend, "_obtener_json", lambda *args: payload)
    result = backend.serie("PN01273PM", "2025-01", "2025-04")
    assert [r["periodo"] for r in result["datos"]] == ["2025-01", "2025-03", "2025-04"]
    assert result["datos"][-1]["valor"] == 1234.5
    assert result["fuente"].endswith("/PN01273PM/json/2025-1/2025-4")
    with pytest.raises(Exception, match="invertido"):
        backend.serie("PN01273PM", "2025-04", "2025-01")


def test_daily_serie_correct_date_and_value(backend, monkeypatch):
    patch_catalog(backend, monkeypatch)
    monkeypatch.setattr(backend, "_obtener_json", lambda *args: {"periods": [
        {"name": "01.Oct.26", "values": ["3.50"]},
        {"name": "15.Oct.26", "values": ["3.428"]},
    ]})
    result = backend.serie("PD04638PD", "2026-10-01", "2026-10-15")
    assert result["datos"][-1] == {"periodo": "2026-10-15", "valor": 3.428}


def example(code, values, freq="Mensual"):
    return {"codigo": code, "nombre": code, "frecuencia": freq, "datos": [
        {"periodo": k, "valor": v} for k, v in values
    ], "fuente": "https://estadisticas.bcrp.gob.pe/example"}


def test_resumen_metrics_and_zero_start(backend, monkeypatch):
    monkeypatch.setattr(backend, "serie", lambda *args: example("X", [("2025-01", 0.0), ("2025-02", -1.0), ("2025-03", 3.0)]))
    r = backend.resumen("X", "2025-01", "2025-03")
    assert r["n"] == 3
    assert r["promedio"] == pytest.approx(2/3)
    assert r["minimo"]["periodo"] == "2025-02"
    assert r["maximo"]["periodo"] == "2025-03"
    assert r["variacion_pct"] is None
    assert r["cambio"] == 3.0


def test_resumen_no_data_rejected(backend, monkeypatch):
    monkeypatch.setattr(backend, "serie", lambda *args: example("X", []))
    with pytest.raises(Exception, match="sin observaciones"):
        backend.resumen("X", "2025-01", "2025-03")


def test_comparison_aligned_and_causal_warning(backend, monkeypatch):
    def fetch(code, *args):
        return example(code, [("2025-01", 1), ("2025-02", 2), ("2025-03", 3), ("2025-04", 4)] if code == "A" else [("2025-02", 6), ("2025-03", 4), ("2025-04", 2), ("2025-05", 0)])
    monkeypatch.setattr(backend, "serie", fetch)
    r = backend.comparar_series("A", "B", "2025-01", "2025-05")
    assert r["n_periodos"] == 3
    assert r["correlacion_pearson"] == pytest.approx(-1.0)
    assert "causalidad" in r["advertencia"].lower()


def test_comparison_different_frequencies_rejected(backend, monkeypatch):
    def fetch(code, *args):
        return example(code, [("2025-01", 1), ("2025-02", 2), ("2025-03", 3)], "Diaria" if code == "B" else "Mensual")
    monkeypatch.setattr(backend, "serie", fetch)
    with pytest.raises(Exception, match="frecuencias distintas"):
        backend.comparar_series("A", "B", "2025-01", "2025-03")


def test_comparison_constant_rejected(backend, monkeypatch):
    def fetch(code, *args):
        return example(code, [("2025-01", 1 if code == "A" else 2), ("2025-02", 1 if code == "A" else 3), ("2025-03", 1 if code == "A" else 4)])
    monkeypatch.setattr(backend, "serie", fetch)
    with pytest.raises(Exception, match="constante"):
        backend.comparar_series("A", "B", "2025-01", "2025-03")


def test_source_failure_after_retries(backend, monkeypatch):
    backend._obtener_json.cache_clear()
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return "<html>not json</html>"
    monkeypatch.setattr(backend.httpx, "get", lambda *args, **kwargs: Response())
    monkeypatch.setattr(backend.time, "sleep", lambda *_: None)
    with pytest.raises(Exception, match="JSON validos"):
        backend._obtener_json("PN01273PM", "2025-1", "2025-12")


def test_graph_is_real_png(backend, monkeypatch, tmp_path):
    monkeypatch.setattr(backend, "ROOT", tmp_path)
    monkeypatch.setattr(backend, "serie", lambda *args: example("X", [("2025-01", 1), ("2025-02", 2), ("2025-03", 3)]))
    r = backend.graficar_serie("X", "2025-01", "2025-03")
    assert (tmp_path / r["archivo"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert r["n"] == 3


def test_resource_prompt(backend, monkeypatch):
    patch_catalog(backend, monkeypatch)
    r = backend.ficha_serie("PN01273PM")
    assert r["codigo"] == "PN01273PM"
    assert r["fuente"] == backend.URL_CATALOGO
    assert "no inventes" in backend.informe("inflacion").lower()


def test_invalid_calendar_day_rejected(backend):
    with pytest.raises(Exception, match="no existe"):
        backend._fecha_api("2026-02-30", "diaria")


def test_single_digit_month_does_not_drop_january(backend, monkeypatch):
    patch_catalog(backend, monkeypatch)
    monkeypatch.setattr(backend, "_obtener_json", lambda *args: {"periods": [
        {"name": "Ene.2025", "values": ["1.1"]},
        {"name": "Feb.2025", "values": ["1.2"]}]})
    ans = backend.serie("PN01273PM", "2025-1", "2025-2")
    assert [x["periodo"] for x in ans["datos"]] == ["2025-01", "2025-02"]


def test_episodes_group_consecutive_periods(backend, monkeypatch):
    datos = [("2025-01", 2), ("2025-02", 4), ("2025-03", 5), ("2025-04", 2), ("2025-05", 0.5), ("2025-06", 3)]
    monkeypatch.setattr(backend, "serie", lambda *args: example("X", datos))
    r = backend.episodios_fuera_de_rango("X", "2025-01", "2025-06", 1, 3)
    assert (r["n_sobre"], r["n_bajo"], r["n_dentro"]) == (2, 1, 3)  # un limite exacto cuenta como dentro
    assert r["episodio_mas_largo"] == {"tipo": "sobre", "desde": "2025-02", "hasta": "2025-03", "n": 2, "extremo": 5}


def test_graph_band_requires_both_limits(backend, monkeypatch, tmp_path):
    monkeypatch.setattr(backend, "ROOT", tmp_path)
    monkeypatch.setattr(backend, "serie", lambda *args: example("X", [("2025-01", 1), ("2025-02", 2)]))
    assert backend.graficar_serie("X", "2025-01", "2025-02", 1, 3)["n"] == 2
    with pytest.raises(Exception, match="banda_min"):
        backend.graficar_serie("X", "2025-01", "2025-02", 1)
