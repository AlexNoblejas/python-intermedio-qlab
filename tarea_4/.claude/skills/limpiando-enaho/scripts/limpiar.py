"""Pipeline ENAHO 2024: zip Stata -> residentes -> m:1 -> validacion -> Parquet.

Ejecutar desde cualquier ubicacion con: uv run python RUTA/scripts/limpiar.py
No ajusta las cifras manualmente. La validacion detiene los resultados inconsistentes.
"""
from __future__ import annotations

import argparse
import io
import json
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]
ANCHO_CODIGO = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}
REFERENCIA = ROOT / "referencias" / "pobreza_departamento_2024_profesor.csv"
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Ancash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho",
    "06": "Cajamarca", "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco",
    "11": "Ica", "12": "Junín", "13": "La Libertad", "14": "Lambayeque", "15": "Lima",
    "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura",
    "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}
METODO_HOGARES = "sumaria, factor07 x mieperho"
METODO_PERSONAS = "residentes habituales, facpob07"


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    def nombre(c):
        texto = unicodedata.normalize("NFD", str(c).strip().lower())
        return "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    salida = df.copy()
    salida.columns = [nombre(c) for c in salida.columns]
    if salida.columns.duplicated().any():
        raise ValueError("Hay nombres de columna duplicados tras normalizar.")
    return salida


def normalizar_identificadores(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    salida = df.copy()
    for col in columnas:
        if col not in salida:
            raise ValueError(f"Falta la llave o codigo {col!r}.")
        if salida[col].isna().any():
            raise ValueError(f"La columna {col!r} tiene identificadores nulos.")
        serie = salida[col].astype("string").str.strip().str.replace(r"\.0+$", "", regex=True)
        if (serie == "").any():
            raise ValueError(f"La columna {col!r} tiene identificadores vacios.")
        salida[col] = serie.str.zfill(ANCHO_CODIGO.get(col, 1))
    return salida


def leer_dta_zip(ruta: Path, patron: str) -> pd.DataFrame:
    if not ruta.exists():
        raise FileNotFoundError(f"Falta {ruta}. Descargue la ENAHO desde el INEI.")
    with zipfile.ZipFile(ruta) as archivo:
        # Coincidencia exacta: el zip del modulo 34 trae tambien sumaria-2024-12g.dta.
        opciones = [n for n in archivo.namelist() if Path(n).name.lower() == f"{patron}.dta"]
        if len(opciones) != 1:
            raise ValueError(f"En {ruta.name} se esperaba un solo {patron}.dta; encontrados: {opciones}")
        with archivo.open(opciones[0]) as f:
            datos = io.BytesIO(f.read())
    return normalizar_columnas(pd.read_stata(datos, convert_categoricals=False))


def num(serie: pd.Series, etiqueta: str) -> pd.Series:
    salida = pd.to_numeric(serie, errors="coerce")
    if salida.isna().any():
        raise ValueError(f"Hay valores no numericos o perdidos en {etiqueta}.")
    return salida


def construir_base(personas_brutas: pd.DataFrame, hogares_brutos: pd.DataFrame) -> pd.DataFrame:
    personas = normalizar_columnas(personas_brutas)
    hogares = normalizar_columnas(hogares_brutos)
    for col in ["p204", "p205", "p206", "p207", "p208a", "facpob07", *LLAVES_PERSONA]:
        if col not in personas.columns:
            raise ValueError(f"No se encontro {col} en ENAHO modulo 02.")
    for col in ["pobreza", "ubigeo", "estrato", "factor07", "mieperho", *LLAVES_HOGAR]:
        if col not in hogares.columns:
            raise ValueError(f"No se encontro {col} en ENAHO modulo 34.")
    personas = normalizar_identificadores(personas, LLAVES_PERSONA)
    hogares = normalizar_identificadores(hogares, LLAVES_HOGAR + ["ubigeo"])
    if hogares.duplicated(LLAVES_HOGAR).any():
        raise ValueError("Los hogares tienen llaves repetidas; se cancelara la union m:1.")
    # Las preguntas de residencia tienen saltos legitimos: p205 o p206 pueden ser nulos.
    for col in ("p204", "p205", "p206"):
        personas[col] = pd.to_numeric(personas[col], errors="coerce")
    residentes = personas.loc[
        ((personas.p204 == 1) & (personas.p205 == 2)) |
        ((personas.p204 == 2) & (personas.p206 == 1))
    ].copy()
    if residentes.duplicated(LLAVES_PERSONA).any():
        raise ValueError("Se encontraron identificadores de persona duplicados.")
    hcols = LLAVES_HOGAR + ["pobreza", "ubigeo", "estrato", "factor07", "mieperho"]
    pcols = LLAVES_PERSONA + ["p207", "p208a", "facpob07"]
    base = residentes[pcols].merge(
        hogares[hcols], how="left", on=LLAVES_HOGAR, validate="m:1", indicator=True
    )
    if len(base) != len(residentes) or (base["_merge"] != "both").any():
        raise ValueError("La union de residentes con hogares perdio filas o no encontro hogares.")
    base = base.drop(columns=["_merge"])
    for col in ("facpob07", "factor07", "mieperho", "pobreza", "estrato", "p207", "p208a"):
        base[col] = num(base[col], col)
    if (base.facpob07 <= 0).any() or (base.factor07 <= 0).any():
        raise ValueError("Se encontraron factores de expansion no positivos.")
    if (~base.pobreza.isin([1, 2, 3])).any():
        raise ValueError("Hay categorias de pobreza fuera de {1,2,3}.")
    if (~base.p207.isin([1, 2])).any():
        raise ValueError("Codigos de sexo no previstos en p207.")
    base["departamento"] = base.ubigeo.str[:2]
    base["area"] = base.estrato.le(5).map({True: "Urbana", False: "Rural"})
    base["sexo"] = base.p207.map({1: "Hombre", 2: "Mujer"})
    base["pobre"] = base.pobreza.le(2)
    base["pobre_extremo"] = base.pobreza.eq(1)
    base["grupo_edad"] = pd.cut(base.p208a, bins=[-1, 14, 29, 59, 200],
                                labels=["0-14", "15-29", "30-59", "60 o mas"]).astype(str)
    return base


def construir_hogares(hogares_brutos: pd.DataFrame) -> pd.DataFrame:
    """Sumaria por hogar con el peso que reproduce la tasa oficial del INEI."""
    hogares = normalizar_identificadores(normalizar_columnas(hogares_brutos), LLAVES_HOGAR + ["ubigeo"])
    if hogares.duplicated(LLAVES_HOGAR).any():
        raise ValueError("Los hogares tienen llaves repetidas.")
    for col in ("pobreza", "factor07", "mieperho", "estrato"):
        hogares[col] = num(hogares[col], col)
    hogares["peso"] = hogares.factor07 * hogares.mieperho
    if (hogares.peso <= 0).any():
        raise ValueError("Se encontraron pesos de hogar no positivos.")
    hogares["departamento"] = hogares.ubigeo.str[:2]
    hogares["area"] = hogares.estrato.le(5).map({True: "Urbana", False: "Rural"})
    hogares["pobre"] = hogares.pobreza.le(2)
    hogares["pobre_extremo"] = hogares.pobreza.eq(1)
    return hogares


def pobreza_ponderada(df: pd.DataFrame, factor: str = "facpob07") -> float:
    if df.empty:
        raise ValueError("No hay registros para calcular pobreza.")
    return float(100 * (df["pobre"].astype(float) * df[factor]).sum() / df[factor].sum())


def _tasa_hogares(h: pd.DataFrame, col: str = "pobre") -> float:
    return float(100 * (h[col].astype(float) * h.peso).sum() / h.peso.sum())


def generar_indicadores(base: pd.DataFrame, hogares: pd.DataFrame | None = None) -> pd.DataFrame:
    """Tasas por nivel. Territorio: sumaria si esta disponible; sexo y edad: personas."""
    registros = []
    total_pobres = None if hogares is None else float((hogares.pobre.astype(float) * hogares.peso).sum())

    def fila(nivel, codigo, personas, grupo_hogares):
        tasa_personas = pobreza_ponderada(personas)
        extrema = float(100 * (personas.pobre_extremo * personas.facpob07).sum() / personas.facpob07.sum())
        nueva = {"nivel": nivel, "codigo": codigo, "nombre": DEPARTAMENTOS.get(codigo, codigo),
                 "n_muestra": len(personas), "poblacion_expandida": round(float(personas.facpob07.sum()), 2),
                 "pobreza_personas_pct": round(tasa_personas, 6)}
        if grupo_hogares is None:
            nueva.update(pobreza_pct=round(tasa_personas, 6), pobreza_extrema_pct=round(extrema, 6),
                         pobreza_sumaria_pct="", personas_pobres="", participacion_pobres_pct="",
                         metodo=METODO_PERSONAS)
        else:
            pobres = float((grupo_hogares.pobre.astype(float) * grupo_hogares.peso).sum())
            tasa = _tasa_hogares(grupo_hogares)
            nueva.update(pobreza_pct=round(tasa, 6), pobreza_extrema_pct=round(_tasa_hogares(grupo_hogares, "pobre_extremo"), 6),
                         pobreza_sumaria_pct=round(tasa, 6), personas_pobres=round(pobres),
                         participacion_pobres_pct=round(100 * pobres / total_pobres, 6), metodo=METODO_HOGARES)
        nueva["fuente"] = "INEI, ENAHO 2024, modulos 34 y 02"
        registros.append(nueva)

    fila("Nacional", "PERU", base, hogares)
    for col, nivel in [("area", "Area"), ("departamento", "Departamento")]:
        for clave, parte in base.groupby(col, observed=True):
            fila(nivel, str(clave), parte, None if hogares is None else hogares[hogares[col] == clave])
    for col, nivel in [("sexo", "Sexo"), ("grupo_edad", "Edad")]:
        if col in base:
            for clave, parte in base.groupby(col, observed=True):
                fila(nivel, str(clave), parte, None)
    return pd.DataFrame(registros)


def validar(base: pd.DataFrame, hogares: pd.DataFrame | None = None, filas_modulo02: int | None = None,
            referencia: pd.DataFrame | None = None) -> tuple[bool, str]:
    tasa = pobreza_ponderada(base)

    # Un grupo ausente es un FALLO que se informa, no un error antes de escribir el archivo.
    def tasa_area(area: str) -> float | None:
        subgrupo = base.loc[base.area == area]
        return None if subgrupo.empty else pobreza_ponderada(subgrupo)

    urbana = tasa_area("Urbana")
    rural = tasa_area("Rural")
    checks = [
        ("Residentes habituales: 108664", len(base) == 108664, str(len(base))),
        ("Pobreza nacional por personas (facpob07): +/-0.1 pp de 27.6", abs(tasa - 27.6) <= 0.1, f"{tasa:.4f}%"),
        ("25 departamentos", base.departamento.nunique() == 25, str(base.departamento.nunique())),
        ("Lima (15) y Callao (07) por separado", {"15", "07"}.issubset(set(base.departamento)),
         ",".join(sorted(set(base.departamento) & {"15", "07"}))),
        ("Sin personas duplicadas", not base.duplicated(LLAVES_PERSONA).any(), "conglome+vivienda+hogar+codperso"),
        ("Pesos de persona positivos", bool((base.facpob07 > 0).all()), "facpob07"),
        ("Urbana por personas cercana a 24.8 (+/-0.5)", urbana is not None and abs(urbana - 24.8) <= 0.5,
         f"{urbana:.3f}%" if urbana is not None else "SIN_OBSERVACIONES"),
        ("Rural por personas cercana a 39.3 (+/-0.5)", rural is not None and abs(rural - 39.3) <= 0.5,
         f"{rural:.3f}%" if rural is not None else "SIN_OBSERVACIONES"),
    ]
    if filas_modulo02 is not None:
        checks.append(("Filas del modulo 02: 117721", filas_modulo02 == 117721, str(filas_modulo02)))
    if hogares is not None:
        sumaria = _tasa_hogares(hogares)
        urbana_h = _tasa_hogares(hogares[hogares.area == "Urbana"])
        rural_h = _tasa_hogares(hogares[hogares.area == "Rural"])
        extrema_h = _tasa_hogares(hogares, "pobre_extremo")
        sin_ponderar = float(100 * hogares.pobre.mean())
        checks += [
            ("Hogares unicos en la sumaria: 33691", len(hogares) == 33691, str(len(hogares))),
            ("Pobreza nacional por sumaria (factor07 x mieperho): +/-0.1 pp de 27.6",
             abs(sumaria - 27.6) <= 0.1, f"{sumaria:.4f}%"),
            ("Urbana por sumaria: +/-0.1 pp de 24.8", abs(urbana_h - 24.8) <= 0.1, f"{urbana_h:.3f}%"),
            ("Rural por sumaria: +/-0.1 pp de 39.3", abs(rural_h - 39.3) <= 0.1, f"{rural_h:.3f}%"),
            ("Pobreza extrema por sumaria: +/-0.1 pp de 5.5", abs(extrema_h - 5.5) <= 0.1, f"{extrema_h:.3f}%"),
            ("Factor de expansion aplicado: poblacion representada entre 34 y 35 millones",
             34e6 <= hogares.peso.sum() <= 35e6, f"{hogares.peso.sum():,.0f} personas"),
            ("La tasa ponderada no es el promedio simple de hogares",
             abs(sumaria - sin_ponderar) > 0.1, f"ponderada {sumaria:.2f}% / sin ponderar {sin_ponderar:.2f}%"),
        ]
        if referencia is not None:
            tasas = hogares.groupby("departamento").apply(_tasa_hogares, include_groups=False)
            ref = referencia.set_index(referencia.ccdd.astype(str).str.zfill(2)).pobreza_pct
            dif = (tasas - ref).abs()
            checks.append(("Departamentos contra la referencia de la Sesion 16: difieren como maximo 0.1 pp",
                           len(dif.dropna()) == 25 and float(dif.max()) <= 0.1, f"maximo {float(dif.max()):.3f} pp"))
    aprobado_todo = all(x[1] for x in checks)
    informe = ["Validacion ENAHO 2024",
               f"Metodo por hogares: {METODO_HOGARES} (reproduce la tasa oficial del INEI).",
               f"Metodo por personas: {METODO_PERSONAS}, merge m:1.", ""]
    for nombre, aprobado, valor in checks:
        informe.append(f"{'APROBADO' if aprobado else 'FALLIDO'} | {nombre} | {valor}")
    informe += ["", f"RESULTADO: {'APROBADO' if aprobado_todo else 'FALLIDO'}",
                "Nota: los valores de referencia son controles; no se ajusta ningun resultado para alcanzarlos."]
    return aprobado_todo, "\n".join(informe) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modulo34", type=Path, default=ROOT / "datos" / "966-Modulo34.zip")
    parser.add_argument("--modulo02", type=Path, default=ROOT / "datos" / "966-Modulo02.zip")
    args = parser.parse_args()
    sumaria = leer_dta_zip(args.modulo34, "sumaria-2024")
    miembros = leer_dta_zip(args.modulo02, "enaho01-2024-200")
    base = construir_base(miembros, sumaria)
    hogares = construir_hogares(sumaria)
    referencia = pd.read_csv(REFERENCIA, dtype={"ccdd": str}) if REFERENCIA.is_file() else None
    correcto, texto = validar(base, hogares, len(miembros), referencia)
    salida = ROOT / "salidas"
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "validacion.txt").write_text(texto, encoding="utf-8")
    print(texto)
    if not correcto:
        raise SystemExit("Las validaciones fallaron; revise los datos y validacion.txt.")
    base.to_parquet(salida / "personas_2024.parquet", index=False)
    indicadores = generar_indicadores(base, hogares)
    indicadores.to_csv(salida / "indicadores.csv", index=False, encoding="utf-8")
    print(f"Se guardaron {len(base)} personas y {len(indicadores)} indicadores verificados.")


if __name__ == "__main__":
    main()
