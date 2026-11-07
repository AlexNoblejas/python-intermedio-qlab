"""Asegura formatos Stata y diferencia los tests reales del profesor de pruebas simuladas."""
from __future__ import annotations

import importlib.util
import io
import zipfile
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def cargar(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


contrato = cargar("scripts/verificar_contrato_docente.py", "contrato_docente_test")
limpiar = cargar(".claude/skills/limpiando-enaho/scripts/limpiar.py", "limpiar_dta_test")


def test_contrato_igual_sin_cambiar_asserts():
    local = (ROOT / "mcp/test_server.py").read_text(encoding="utf-8")
    assert contrato.contrastar(local, local)[0]


def test_contrato_rechaza_alteracion_de_assert():
    original = "def test_x():\n    assert 10 == 10\n"
    adulterado = "def test_x():\n    assert 10 == 11\n"
    igual, diff = contrato.contrastar(original, adulterado)
    assert not igual
    assert "-    assert 10 == 10" in diff
    assert "+    assert 10 == 11" in diff


def empaquetar_dta(path, df, nombre):
    buffer = io.BytesIO()
    df.to_stata(buffer, write_index=False, version=118)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(nombre, buffer.getvalue())


def test_lectura_verdadera_de_formato_stata_desde_zip(tmp_path):
    """Usa bytes .dta reales generados por pandas, no una falsa extension .dta."""
    hogar = pd.DataFrame({
        "conglome": ["000123", "000124"],
        "vivienda": ["001", "001"], "hogar": ["01", "01"],
        "ubigeo": ["010101", "070101"], "estrato": [2, 7],
        "pobreza": [1, 3], "factor07": [12., 18.], "mieperho": [2, 2],
    })
    personas = pd.DataFrame({
        "conglome": ["000123", "000123", "000124", "000124"],
        "vivienda": ["001"]*4, "hogar": ["01"]*4, "codperso": ["01", "02", "01", "02"],
        "p204": [1, 2, 1, 2], "p205": [2, 0, 2, 0], "p206": [0, 1, 0, 1],
        "p207": [1, 2, 1, 2], "p208a": [20, 21, 25, 26],
        "facpob07": [12., 12., 18., 18.],
    })
    zip_hog = tmp_path / "m34.zip"
    zip_per = tmp_path / "m02.zip"
    empaquetar_dta(zip_hog, hogar, "carpeta/sumaria-2024.dta")
    empaquetar_dta(zip_per, personas, "carpeta/enaho01-2024-200.dta")
    household_loaded = limpiar.leer_dta_zip(zip_hog, "sumaria-2024")
    person_loaded = limpiar.leer_dta_zip(zip_per, "enaho01-2024-200")
    base = limpiar.construir_base(person_loaded, household_loaded)
    assert len(base) == 4
    assert base["departamento"].tolist() == ["01", "01", "07", "07"]
    assert base["conglome"].tolist() == ["000123", "000123", "000124", "000124"]
    assert limpiar.pobreza_ponderada(base) == pytest.approx(40.0)
    res = limpiar.generar_indicadores(base)
    assert res.loc[(res.nivel == "Nacional") & (res.codigo == "PERU"), "pobreza_pct"].iloc[0] == pytest.approx(40.0)
    # No simula cumplir las referencias del INEI: valida la capacidad de leer Stata/ZIP real.


def test_rechazo_zip_con_dta_sin_coincidencia(tmp_path):
    destino = tmp_path / "wrong.zip"
    empaquetar_dta(destino, pd.DataFrame({"x": [1]}), "otro.dta")
    with pytest.raises(ValueError, match="un solo"):
        limpiar.leer_dta_zip(destino, "sumaria-2024")
