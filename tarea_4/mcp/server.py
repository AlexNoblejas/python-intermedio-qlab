"""Servidor MCP BCRP para la Tarea 4; numeros proceden de la API oficial."""
from __future__ import annotations

import math
import re
from datetime import date
import time
import unicodedata
from functools import lru_cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "datos" / "catalogo_bcrp.csv"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
LEER = {"readOnlyHint": True, "openWorldHint": True}
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12}

mcp = FastMCP(
    "bcrp",
    instructions=(
        "Estadisticas oficiales del BCRP. Identifica codigo con buscar_series. "
        "Usa serie para datos, resumen para estadisticos, episodios_fuera_de_rango para "
        "contar periodos fuera de un rango, comparar_series para alinear dos series y "
        "graficar_serie para producir PNG. "
        "Cita siempre codigo, periodo y URL. No inventes resultados."
    ),
)


def _sin_tildes(valor: object) -> str:
    return unicodedata.normalize("NFD", str(valor).lower()).encode("ascii", "ignore").decode()


@lru_cache(maxsize=1)
def catalogo() -> pd.DataFrame:
    """Descarga y conserva localmente los metadatos oficiales del BCRP."""
    if not CATALOGO.is_file():
        CATALOGO.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = httpx.get(URL_CATALOGO, timeout=120, follow_redirects=True)
            r.raise_for_status()
            CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
        except (httpx.HTTPError, OSError, UnicodeError) as e:
            raise ToolError(f"No fue posible obtener el catalogo BCRP: {e}") from e
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={
        "C\u00f3digo de serie": "codigo", "Categor\u00eda de serie": "categoria",
        "Grupo de serie": "grupo", "Nombre de serie": "nombre",
        "Frecuencia": "frecuencia", "Fecha de actualizaci\u00f3n": "actualizada",
        "Fecha de inicio": "inicio",
    })
    for col in ("codigo", "categoria", "grupo", "nombre", "frecuencia", "actualizada", "inicio"):
        if col not in df.columns:
            raise ToolError(f"Formato del catalogo BCRP inesperado: falta {col!r}")
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo: str) -> dict:
    df = catalogo()
    sel = df.loc[df.codigo == codigo]
    if sel.empty:
        raise ToolError(f"No existe el codigo BCRP {codigo!r}. Buscar con buscar_series.")
    fila = sel.iloc[0]
    return {"codigo": fila.codigo, "nombre": f"{fila.grupo} - {fila.nombre}",
            "categoria": fila.categoria, "frecuencia": fila.frecuencia,
            "inicio": fila.inicio, "actualizada": fila.actualizada}


@mcp.tool(annotations=LEER)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series oficiales BCRP por palabras clave y frecuencia.

    Usar cuando no se conoce el codigo. Exige todas las palabras y devuelve
    codigo, nombre, frecuencia e inicio de la serie con su fuente oficial.
    """
    df = catalogo()
    mascara = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        mascara &= df.texto.str.contains(re.escape(palabra), na=False)
    if frecuencia:
        mascara &= df.frecuencia.str.casefold() == frecuencia.casefold()
    limite = min(max(1, int(limite)), 50)
    seleccion = df.loc[mascara].copy()
    seleccion["antigua"] = seleccion.actualizada < "2025"
    seleccion["longitud"] = (seleccion.grupo + seleccion.nombre).str.len()
    return [_ficha(c) for c in seleccion.sort_values(["antigua", "longitud"]).head(limite).codigo]


def _frecuencia(nombre: str) -> str:
    nombre = _sin_tildes(nombre)
    if "diaria" in nombre or "diario" in nombre:
        return "diaria"
    if "mensual" in nombre:
        return "mensual"
    if "trimestral" in nombre:
        return "trimestral"
    if "anual" in nombre:
        return "anual"
    raise ToolError(f"Frecuencia BCRP no reconocida: {nombre!r}")


def _fecha_api(fecha: str, frecuencia: str) -> str:
    fecha = str(fecha)
    if frecuencia == "diaria" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        try:
            date.fromisoformat(fecha)
            return fecha
        except ValueError:
            raise ToolError(f"Fecha {fecha!r} no existe en el calendario.") from None
    if frecuencia == "mensual" and re.fullmatch(r"\d{4}-(0?[1-9]|1[0-2])", fecha):
        y, m = fecha.split("-")
        return f"{y}-{int(m)}"
    if frecuencia == "trimestral" and re.fullmatch(r"\d{4}-T[1-4]", fecha):
        y, t = fecha.split("-T")
        return f"{y}-{t}"  # la API numera el trimestre: 2025-4 es T4, no abril
    if frecuencia == "anual" and re.fullmatch(r"\d{4}", fecha):
        return fecha
    raise ToolError(f"Fecha {fecha!r} invalida para frecuencia {frecuencia}.")


def _periodo_normalizado(nombre: str, frecuencia: str) -> str:
    valor = str(nombre).strip().replace(" ", "")
    if frecuencia == "mensual":
        m = re.fullmatch(r"([A-Za-z]+)\.(\d{4})", valor)
        if m and _sin_tildes(m.group(1)) in MESES:
            return f"{m.group(2)}-{MESES[_sin_tildes(m.group(1))]:02d}"
    elif frecuencia == "diaria":
        m = re.fullmatch(r"(\d{1,2})\.([A-Za-z]+)\.(\d{2,4})", valor)
        if m and _sin_tildes(m.group(2)) in MESES:
            anio = int(m.group(3))
            if anio < 100:
                anio += 2000 if anio < 80 else 1900
            return f"{anio:04d}-{MESES[_sin_tildes(m.group(2))]:02d}-{int(m.group(1)):02d}"
    elif frecuencia == "trimestral":
        m = re.fullmatch(r"T([1-4])\.(\d{2,4})", valor, re.IGNORECASE)
        if m:
            anio = int(m.group(2))
            if anio < 100:
                anio += 2000 if anio < 80 else 1900
            return f"{anio:04d}-T{m.group(1)}"
    elif frecuencia == "anual" and re.fullmatch(r"\d{4}", valor):
        return valor
    raise ToolError(f"El periodo {nombre!r} del BCRP no se pudo interpretar ({frecuencia}).")


@lru_cache(maxsize=256)
def _obtener_json(codigo: str, inicio: str, final: str) -> dict:
    url = f"{API}/{codigo}/json/{inicio}/{final}"
    ultima = None
    esperas = (1, 3, 6, 12)  # con pedidos seguidos la API responde HTML un rato; hay que esperar
    for intento in range(len(esperas) + 1):
        try:
            r = httpx.get(url, timeout=45, follow_redirects=True)
            r.raise_for_status()
            payload = r.json()
            if not isinstance(payload, dict) or "periods" not in payload:
                raise ValueError("La respuesta no contiene periods")
            return payload
        except (httpx.HTTPError, ValueError) as e:
            ultima = e
            if intento < len(esperas):
                time.sleep(esperas[intento])
    raise ToolError(f"No se recibieron datos JSON validos del BCRP ({codigo}): {ultima}")


@mcp.tool(annotations=LEER)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Descarga observaciones de una serie BCRP dentro del periodo inclusivo.

    Primero identifica el codigo con buscar_series. Fechas: mensual 2025-01,
    diaria 2026-10-15, trimestral 2025-T1, anual 2025. No inventa faltantes.
    """
    ficha = _ficha(codigo)
    frecuencia = _frecuencia(ficha["frecuencia"])
    desde_api = _fecha_api(desde, frecuencia)
    hasta_api = _fecha_api(hasta, frecuencia)
    # La API acepta '2025-1', pero la comparacion se hace en ISO '2025-01'.
    def comparable(fecha: str) -> str:
        if frecuencia == "mensual":
            anio, mes = fecha.split("-")
            return f"{anio}-{int(mes):02d}"
        return fecha

    desde_norm, hasta_norm = comparable(desde), comparable(hasta)
    if desde_norm > hasta_norm:
        raise ToolError(f"Periodo invertido: desde={desde!r}, hasta={hasta!r}")
    data = _obtener_json(codigo, desde_api, hasta_api)
    registros = []
    for item in data.get("periods", []):
        valores = item.get("values") or []
        if not valores:
            continue
        literal = str(valores[0]).strip().replace(",", "")
        if not literal or literal.lower() in {"n.d.", "n.d", "nd", "s.i.", "--", "null"}:
            continue
        try:
            valor = float(literal)
            periodo = _periodo_normalizado(item.get("name", ""), frecuencia)
        except (ValueError, ToolError):
            continue
        if math.isfinite(valor) and desde_norm <= periodo <= hasta_norm:
            registros.append({"periodo": periodo, "valor": valor})
    registros.sort(key=lambda x: x["periodo"])
    return {"codigo": codigo, "nombre": ficha["nombre"], "frecuencia": ficha["frecuencia"],
            "datos": registros,
            "fuente": f"{API}/{codigo}/json/{desde_api}/{hasta_api}"}


@mcp.tool(annotations=LEER)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Calcula en Python media, minimo, maximo, cambio y variacion de una serie BCRP.

    Usar al responder comparaciones temporales. Devuelve extremos con periodo,
    codigo y URL oficial. La variacion relativa es indefinida si el valor inicial es cero.
    """
    datos = serie(codigo, desde, hasta)
    observaciones = datos["datos"]
    if not observaciones:
        raise ToolError(f"BCRP sin observaciones disponibles para {codigo} entre {desde} y {hasta}.")
    primero, ultimo = observaciones[0], observaciones[-1]
    cambio = ultimo["valor"] - primero["valor"]
    variacion = 100 * cambio / abs(primero["valor"]) if primero["valor"] != 0 else None
    return {"codigo": codigo, "nombre": datos["nombre"], "frecuencia": datos["frecuencia"],
            "desde": desde, "hasta": hasta, "n": len(observaciones), "primero": primero,
            "ultimo": ultimo, "cambio": cambio, "variacion_pct": variacion,
            "promedio": sum(o["valor"] for o in observaciones) / len(observaciones),
            "maximo": max(observaciones, key=lambda o: o["valor"]),
            "minimo": min(observaciones, key=lambda o: o["valor"]),
            "fuente": datos["fuente"]}


@mcp.tool(annotations=LEER)
def comparar_series(codigo_a: str, codigo_b: str, desde: str, hasta: str) -> dict:
    """Compara dos series BCRP con la misma frecuencia y periodos compartidos.

    Usar cuando se necesita correlacion descriptiva y contraste de dos indicadores.
    No es inferencia causal. Excluye periodos sin dato y requiere >= 3 puntos.
    """
    a = serie(codigo_a, desde, hasta)
    b = serie(codigo_b, desde, hasta)
    if _frecuencia(a["frecuencia"]) != _frecuencia(b["frecuencia"]):
        raise ToolError("No se comparan frecuencias distintas sin definir una agregacion previa.")
    da = {r["periodo"]: r["valor"] for r in a["datos"]}
    db = {r["periodo"]: r["valor"] for r in b["datos"]}
    comunes = sorted(set(da) & set(db))
    if len(comunes) < 3:
        raise ToolError(f"Solo {len(comunes)} periodos coincidentes; se requieren 3 o mas.")
    xs = pd.Series([da[p] for p in comunes], dtype=float)
    ys = pd.Series([db[p] for p in comunes], dtype=float)
    if xs.nunique() < 2 or ys.nunique() < 2:
        raise ToolError("La correlacion no se define para una serie constante.")
    return {"codigo_a": codigo_a, "codigo_b": codigo_b, "n_periodos": len(comunes),
            "desde_real": comunes[0], "hasta_real": comunes[-1],
            "correlacion_pearson": float(xs.corr(ys)),
            "comparacion": [{"periodo": p, "valor_a": da[p], "valor_b": db[p]} for p in comunes],
            "fuentes": [a["fuente"], b["fuente"]],
            "advertencia": "Asociacion descriptiva temporal; no demuestra causalidad."}


@mcp.tool(annotations=LEER)
def episodios_fuera_de_rango(codigo: str, desde: str, hasta: str, minimo: float, maximo: float) -> dict:
    """Cuenta cuantos periodos estuvo una serie BCRP dentro, sobre o bajo un rango y arma sus episodios.

    Usar para preguntas como "cuantos meses estuvo la inflacion por encima de 3 %" o "cuanto duro
    el episodio fuera de la meta". Ejemplo: codigo="PN01273PM", desde="2020-01", hasta="2024-12",
    minimo=1, maximo=3. Un valor igual a un limite cuenta como dentro del rango. Un episodio es una
    racha de periodos consecutivos con datos en el mismo lado del rango. No explica las causas.
    """
    if not (math.isfinite(minimo) and math.isfinite(maximo)) or minimo >= maximo:
        raise ToolError(f"Rango invalido: minimo={minimo} debe ser menor que maximo={maximo}.")
    datos = serie(codigo, desde, hasta)
    observaciones = datos["datos"]
    if not observaciones:
        raise ToolError(f"BCRP sin observaciones disponibles para {codigo} entre {desde} y {hasta}.")

    def lado(valor: float) -> str:
        return "sobre" if valor > maximo else "bajo" if valor < minimo else "dentro"

    episodios: list[dict] = []
    for o in observaciones:
        tipo = lado(o["valor"])
        if episodios and episodios[-1]["tipo"] == tipo:
            episodios[-1].update(hasta=o["periodo"], n=episodios[-1]["n"] + 1,
                                 extremo=(max if tipo == "sobre" else min)(episodios[-1]["extremo"], o["valor"]))
        else:
            episodios.append({"tipo": tipo, "desde": o["periodo"], "hasta": o["periodo"], "n": 1, "extremo": o["valor"]})
    fuera = [e for e in episodios if e["tipo"] != "dentro"]
    conteo = {tipo: sum(e["n"] for e in episodios if e["tipo"] == tipo) for tipo in ("sobre", "bajo", "dentro")}
    return {"codigo": codigo, "nombre": datos["nombre"], "frecuencia": datos["frecuencia"],
            "rango": {"minimo": minimo, "maximo": maximo}, "n_observaciones": len(observaciones),
            "n_sobre": conteo["sobre"], "n_bajo": conteo["bajo"], "n_dentro": conteo["dentro"],
            "pct_fuera": 100 * (conteo["sobre"] + conteo["bajo"]) / len(observaciones),
            "episodios_fuera": fuera, "episodio_mas_largo": max(fuera, key=lambda e: e["n"]) if fuera else None,
            "fuente": datos["fuente"], "advertencia": "Descripcion de la serie; no identifica causas."}


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True})
def graficar_serie(codigo: str, desde: str, hasta: str, banda_min: float | None = None,
                   banda_max: float | None = None, titulo: str | None = None) -> dict:
    """Guarda en figuras/ un grafico PNG de una serie BCRP para el informe reproducible.

    Usar si se necesita evidencia visual de un indicador. Opcional: banda_min y banda_max sombrean
    un rango de referencia (por ejemplo la meta 1 a 3 de inflacion) y titulo reemplaza el titulo
    por defecto. Devuelve la ruta del archivo, el periodo y la fuente.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    data = serie(codigo, desde, hasta)
    registros = data["datos"]
    if not registros:
        raise ToolError(f"No hay datos del BCRP para graficar {codigo}.")
    if (banda_min is None) != (banda_max is None) or (banda_min is not None and banda_min >= banda_max):
        raise ToolError("banda_min y banda_max van juntos y banda_min debe ser menor que banda_max.")
    destino = ROOT / "figuras" / f"bcrp_{codigo}_{desde}_{hasta}.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    periodos = [x["periodo"] for x in registros]
    valores = [x["valor"] for x in registros]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    if banda_min is not None:
        ax.axhspan(banda_min, banda_max, color="#d8e6d3", label=f"Rango de referencia: {banda_min:g} a {banda_max:g}")
    ax.plot(periodos, valores, lw=2.2, color="#135d80")
    pico = max(range(len(valores)), key=valores.__getitem__)
    ax.annotate(f"Máximo: {valores[pico]:.2f} ({periodos[pico]})", xy=(pico, valores[pico]), xytext=(4, 6),
                textcoords="offset points", size=9)
    ax.set_title(titulo or f"{data['nombre']}, {desde} a {hasta}", loc="left", fontsize=12)
    ax.set_ylabel("Valor en la unidad de la serie (ver ficha BCRP)")
    ax.spines[["top", "right"]].set_visible(False)
    paso = max(1, len(periodos) // 12)
    ax.set_xticks(range(0, len(periodos), paso), periodos[::paso], rotation=45, ha="right", size=8)
    if banda_min is not None:
        ax.legend(frameon=False, loc="upper left")
    fig.text(.01, .005, f"Fuente: BCRP, serie {codigo}. {data['fuente']}", size=7)
    fig.tight_layout(rect=[0, .03, 1, 1])
    fig.savefig(destino, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {"archivo": destino.relative_to(ROOT).as_posix(), "n": len(registros),
            "codigo": codigo, "periodo": f"{desde} a {hasta}", "fuente": data["fuente"]}


@mcp.resource("bcrp://serie/{codigo}")
def ficha_serie(codigo: str) -> dict:
    """Ficha descriptiva oficial de una serie BCRP."""
    ficha = _ficha(codigo)
    ficha["fuente"] = URL_CATALOGO
    return ficha


@mcp.prompt
def informe(tema: str) -> str:
    """Plantilla reproducible para investigar indicadores con cifras verificables."""
    return (
        f"Investiga {tema!r} con cifras del BCRP. Primero usa buscar_series, "
        "luego serie o resumen, y graficar_serie si procede. Cita nombre, "
        "codigo, periodo, frecuencia, unidad y URL. Calcula solo con herramientas. "
        "Si hay datos ausentes, dilo; no inventes cifras ni infieras causalidad."
    )


if __name__ == "__main__":
    mcp.run()
