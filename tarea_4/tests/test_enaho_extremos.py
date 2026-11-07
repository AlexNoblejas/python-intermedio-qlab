"""Additional ENAHO tests; synthetic only, no claim of official-data validation."""
import importlib.util
from pathlib import Path
import zipfile

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


limpiar = load("mod_limpiar", ".claude/skills/limpiando-enaho/scripts/limpiar.py")
graficar = load("mod_graficar", ".claude/skills/graficando-enaho/scripts/graficar.py")
mapear = load("mod_mapear", ".claude/skills/mapeando-enaho/scripts/mapear.py")
audit = load("mod_audit", "scripts/validar_con_referencias.py")


@pytest.fixture
def tiny():
    households = pd.DataFrame({
        "CONGLOME": [1001, 1002], "VIVIENDA": [1, 1], "HOGAR": [1, 1],
        "UBIGEO": [10101, 150101], "POBREZA": [1, 3], "estrato": [7, 1],
        "factor07": [2.0, 1.0], "mieperho": [2.0, 1.0]})
    people = pd.DataFrame({
        "CONGLOME": [1001, 1001, 1002], "VIVIENDA": [1, 1, 1],
        "HOGAR": [1, 1, 1], "CODPERSO": [1, 2, 1],
        "p204": [1, 2, 1], "p205": [2, None, 1], "p206": [None, 1, None],
        "p207": [1, 2, 1], "p208a": [20, 40, 60], "facpob07": [1.0, 2.0, 100.0]})
    return people, households


def test_normalization_and_resident_filter(tiny):
    people, household = tiny
    out = limpiar.construir_base(people, household)
    assert len(out) == 2
    assert out.departamento.tolist() == ["01", "01"]
    assert out.codperso.tolist() == ["01", "02"]
    assert out.conglome.tolist() == ["001001", "001001"]
    assert out.ubigeo.tolist() == ["010101", "010101"]
    assert limpiar.pobreza_ponderada(out) == 100.0


def test_bad_poverty_categories_fail(tiny):
    people, hh = tiny
    hh.loc[0, "POBREZA"] = 5
    with pytest.raises(ValueError, match="pobreza"):
        limpiar.construir_base(people, hh)


def test_negative_person_weights_fail(tiny):
    people, hh = tiny
    people.loc[0, "facpob07"] = -9
    with pytest.raises(ValueError, match="factores"):
        limpiar.construir_base(people, hh)


def test_missing_household_fails(tiny):
    people, hh = tiny
    hh.loc[0, "CONGLOME"] = 9999
    with pytest.raises(ValueError, match="no encontro"):
        limpiar.construir_base(people, hh)


def test_duplicate_person_fails(tiny):
    people, hh = tiny
    people = pd.concat([people, people.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="persona duplicados"):
        limpiar.construir_base(people, hh)


def test_duplicate_columns_after_normalization_fail():
    df = pd.DataFrame([[1, 2]], columns=["A", "a"])
    with pytest.raises(ValueError, match="duplicados"):
        limpiar.normalizar_columnas(df)


def test_duplicate_household_prevents_merge(tiny):
    people, hh = tiny
    hh = pd.concat([hh, hh.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="llaves repetidas"):
        limpiar.construir_base(people, hh)


def test_missing_keys_rejected():
    df = pd.DataFrame({"conglome": [1]})
    with pytest.raises(ValueError, match="Falta la llave"):
        limpiar.normalizar_identificadores(df, limpiar.LLAVES_HOGAR)


def test_reject_dubious_synthetic_validation(tiny):
    out = limpiar.construir_base(*tiny)
    passed, message = limpiar.validar(out)
    assert not passed
    assert "RESULTADO: FALLIDO" in message


def test_dta_zip_nested_roundtrip(tmp_path):
    df = pd.DataFrame({"conglome": ["000001"], "vivienda": ["001"], "hogar": ["01"], "pobreza": [1]})
    raw = tmp_path / "sumaria-2024.dta"
    df.to_stata(raw, write_index=False)
    path = tmp_path / "modulo.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.write(raw, arcname="nested/sumaria-2024.dta")
    recovered = limpiar.leer_dta_zip(path, "sumaria-2024")
    assert recovered.conglome.iloc[0] == "000001"


def test_dta_zip_ambiguous_fails(tmp_path):
    path = tmp_path / "modulo.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("a/sumaria-2024.dta", "dummy")
        z.writestr("b/sumaria-2024.dta", "dummy")
    with pytest.raises(ValueError, match="se esperaba un solo"):
        limpiar.leer_dta_zip(path, "sumaria-2024")


def test_indicators_apply_person_expansion(tiny):
    out = limpiar.construir_base(*tiny)
    r = limpiar.generar_indicadores(out)
    assert r.loc[r.nivel.eq("Nacional"), "pobreza_pct"].iloc[0] == 100.0
    assert r.loc[r.nivel.eq("Sexo"), "n_muestra"].sum() == len(out)


def test_graph_area_creates_png(tmp_path):
    df = pd.DataFrame({"nivel": ["Nacional", "Area", "Area"], "codigo": ["PERU", "Urbana", "Rural"],
                       "nombre": ["PERU", "Urbana", "Rural"], "pobreza_pct": [27.6, 24.8, 39.3]})
    rates = graficar.figura("area", df, tmp_path)
    assert (tmp_path / "pobreza_area_2024.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert list(rates.index) == ["Rural", "Urbana"]  # ordenadas de mayor a menor


def geo25():
    return gpd.GeoDataFrame({"FIRST_IDDP": [f"{n:02d}" for n in range(1, 26)],
                              "NOMBDEP": [f"Departamento {n}" for n in range(1, 26)]},
                             geometry=[box(n, 0, n + .8, .8) for n in range(1, 26)], crs="EPSG:4326")


def tasas25():
    return pd.DataFrame({"codigo": [f"{n:02d}" for n in range(1, 26)], "nombre": [f"D{n}" for n in range(1, 26)],
                         "pobreza_pct": [float(n) for n in range(1, 26)]})


def test_map_25_codes_png(tmp_path):
    destino = tmp_path / "mapa.png"
    union = mapear.unir(geo25(), tasas25())
    mapear.dibujar(union, destino)
    assert len(union) == 25
    assert destino.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert {"07", "15"}.issubset(set(union.FIRST_IDDP))
    assert union.pobreza_pct.notna().all()


def test_map_missing_code_rejected():
    indicadores = tasas25().assign(nivel="Departamento")
    indicadores.loc[24, "codigo"] = "24"
    with pytest.raises(ValueError, match="25 departamentos"):
        mapear.tasas_por_departamento(indicadores)


def test_map_duplicate_shape_code_rejected():
    geo = geo25()
    geo.loc[24, "FIRST_IDDP"] = "01"
    with pytest.raises(ValueError, match="25 codigos"):
        mapear.unir(geo, tasas25())


def test_map_compares_with_course_reference():
    union = mapear.unir(geo25(), tasas25())
    ref = pd.DataFrame({"ccdd": [f"{n:02d}" for n in range(1, 26)], "pobreza_pct": [n + .5 for n in range(1, 26)]})
    tabla = mapear.comparar_con_referencia(union, ref)
    assert (tabla.diferencia_pp == -.5).all()


def test_zip_with_two_sumaria_files_reads_the_exact_one(tmp_path):
    """Regresion: el zip real del INEI trae sumaria-2024.dta y sumaria-2024-12g.dta."""
    import io
    buffer = io.BytesIO()
    pd.DataFrame({"a": [1]}).to_stata(buffer, write_index=False)
    ruta = tmp_path / "m34.zip"
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("966/sumaria-2024.dta", buffer.getvalue())
        z.writestr("966/sumaria-2024-12g.dta", "no debe leerse")
    assert list(limpiar.leer_dta_zip(ruta, "sumaria-2024").columns) == ["a"]


def test_household_method_uses_factor_times_members():
    crudo = pd.DataFrame({"conglome": ["1", "2"], "vivienda": ["1", "1"], "hogar": ["11", "11"],
                          "ubigeo": ["010101", "150101"], "pobreza": [1, 3], "factor07": [10.0, 10.0],
                          "mieperho": [3, 1], "estrato": [1, 8]})
    hogares = limpiar.construir_hogares(crudo)
    assert limpiar._tasa_hogares(hogares) == pytest.approx(75.0)  # sin mieperho daria 50


def test_reference_has_expected_25_codes_and_extremes():
    df = pd.read_csv(ROOT / "referencias/pobreza_departamento_2024_profesor.csv", dtype={"ccdd": str})
    assert len(df) == 25
    assert df.ccdd.tolist() == [f"{n:02d}" for n in range(1, 26)]
    assert df.loc[df.ccdd == "06", "pobreza_pct"].iloc[0] == 45.0
    assert df.loc[df.ccdd == "11", "pobreza_pct"].iloc[0] == 6.0


def test_sumaria_weights_not_simple_mean():
    df = pd.DataFrame({"pobreza": [1, 3], "factor07": [10., 1.], "mieperho": [3, 1],
                       "ubigeo": [10101, 10102]})
    out = audit.sumaria_pobreza_por_departamento(df)
    assert out.sumaria_pct.iloc[0] == pytest.approx(3000/31)
