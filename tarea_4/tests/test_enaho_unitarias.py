"""Pruebas sin microdatos para la logica de residencia, uniones y factores."""
import importlib.util
from pathlib import Path
import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".claude/skills/limpiando-enaho/scripts/limpiar.py"
spec = importlib.util.spec_from_file_location("limpiar_enaho", SCRIPT)
limpiar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(limpiar)


def dataframes():
    hogares = pd.DataFrame({"CONGLOME": ["000001", "000002"], "VIVIENDA": ["001", "002"],
                            "HOGAR": ["01", "01"], "UBIGEO": ["010101", "150101"],
                            "POBREZA": [1, 3], "estrato": [6, 2],
                            "factor07": [3.0, 1.0], "mieperho": [2, 1]})
    personas = pd.DataFrame({"conglome": ["000001", "000001", "000002", "000002"],
                             "vivienda": ["001", "001", "002", "002"],
                             "hogar": ["01", "01", "01", "01"], "codperso": ["01", "02", "01", "02"],
                             "p204": [1, 2, 1, 1], "p205": [2, None, 2, 1],
                             "p206": [None, 1, None, None], "p207": [1, 2, 2, 1],
                             "p208a": [22, 53, 19, 12], "facpob07": [3., 3., 1., 1.]})
    return personas, hogares


def test_residentes_union_sin_duplicar():
    base = limpiar.construir_base(*dataframes())
    assert len(base) == 3
    assert base.departamento.tolist() == ["01", "01", "15"]
    assert base.area.tolist() == ["Rural", "Rural", "Urbana"]
    assert limpiar.pobreza_ponderada(base) == pytest.approx(600 / 7)


def test_hogares_duplicados_se_rechazan():
    personas, hogares = dataframes()
    hogares = pd.concat([hogares, hogares.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="llaves repetidas"):
        limpiar.construir_base(personas, hogares)


def test_ceros_a_izquierda_se_conservan():
    df = pd.DataFrame({"conglome": [15009], "vivienda": [1], "hogar": [1]})
    out = limpiar.normalizar_identificadores(df, limpiar.LLAVES_HOGAR)
    assert out.iloc[0].conglome == "015009"
    assert out.iloc[0].vivienda == "001"
