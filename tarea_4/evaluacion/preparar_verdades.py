"""Fija las respuestas esperadas antes de ver a Claude, por un camino independiente del agente.

No importa mcp/server.py ni la Skill de limpieza: va directo a la API del BCRP y a los .dta del INEI.
Despues contrasta con las cifras que el curso publica y guarda el cotejo en
evaluacion/verificacion_verdades.csv.

    uv run python evaluacion/preparar_verdades.py
"""
import csv
import io
import time
import zipfile
from datetime import date
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARCHIVO = ROOT / "evaluacion" / "preguntas.csv"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
# Cifras publicadas por el curso (Sesion 04: preguntas.csv; Sesion 16: README y referencia).
PUBLICADAS = {("01", "bcrp"): 4.5487, ("03", "bcrp"): 3.4282, ("05", "enaho"): 27.6, ("06", "enaho"): 39.3,
              ("07", "enaho"): 18.5, ("09", "enaho"): 27.6}


def _fecha_api(fecha: str) -> str:
    partes = fecha.split("-")
    return f"{partes[0]}-{int(partes[1])}" if len(partes) == 2 else fecha


def valores_bcrp(codigo: str, desde: str, hasta: str) -> tuple[list[float], str]:
    url = f"{API}/{codigo}/json/{_fecha_api(desde)}/{_fecha_api(hasta)}"
    for espera in (2, 5, 10, 20, 0):  # el limite de pedidos del BCRP responde HTML en vez de JSON
        respuesta = httpx.get(url, timeout=60, follow_redirects=True)
        respuesta.raise_for_status()
        try:
            cuerpo = respuesta.json()
            break
        except ValueError:
            if not espera:
                raise
            time.sleep(espera)
    valores = []
    for periodo in cuerpo["periods"]:
        crudo = str(periodo["values"][0]).replace(",", "")
        if crudo not in ("n.d.", ""):
            valores.append(float(crudo))
    return valores, url


def verdad_bcrp(fila: dict) -> tuple[float, str]:
    valores, url = valores_bcrp(fila["codigo_bcrp"], fila["desde"], fila["hasta"])
    operacion = fila["operacion_bcrp"]
    if operacion == "observacion":
        # La API diaria puede traer dias previos si el rango es amplio: aqui desde == hasta.
        if len(valores) != 1:
            raise ValueError(f"Se esperaba una observacion en la pregunta {fila['id']}: {valores}")
        return valores[0], url
    if operacion == "maximo":
        return max(valores), url
    if operacion == "meses_sobre_3":
        return float(sum(v > 3 for v in valores)), url
    raise ValueError(f"Operacion desconocida: {operacion}")


def leer_sumaria() -> pd.DataFrame:
    with zipfile.ZipFile(ROOT / "datos" / "966-Modulo34.zip") as z:
        datos = io.BytesIO(z.read("966-Modulo34/sumaria-2024.dta"))
    s = pd.read_stata(datos, convert_categoricals=False)
    s.columns = [c.lower() for c in s.columns]
    s["w"] = s.factor07.astype(float) * s.mieperho.astype(float)
    s["pobre"] = s.pobreza <= 2
    s["dep"] = s.ubigeo.astype(str).str.zfill(6).str[:2]
    s["urbano"] = s.estrato <= 5
    return s


def tasa(g: pd.DataFrame) -> float:
    return float(100 * (g.pobre * g.w).sum() / g.w.sum())


def verdad_enaho(fila: dict, s: pd.DataFrame) -> float:
    nivel, codigo = fila["nivel_enaho"], fila["codigo_enaho"]
    if nivel == "Nacional":
        return tasa(s)
    if nivel == "Area":
        return tasa(s[s.urbano == (codigo == "Urbana")])
    if nivel == "Departamento":
        return tasa(s[s.dep == codigo])
    if nivel == "Participacion":
        return float(100 * (s.pobre * s.w)[s.dep == codigo].sum() / (s.pobre * s.w).sum())
    if nivel == "Brecha":
        return tasa(s[~s.urbano]) - tasa(s[s.urbano])
    raise ValueError(f"Nivel desconocido: {nivel}")


def main():
    with ARCHIVO.open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    s = leer_sumaria()
    cotejo = []
    fuente_enaho = "INEI ENAHO 2024, sumaria-2024.dta, factor07 x mieperho, calculo directo sobre el .dta"
    for f in filas:
        fuentes = []
        f["verdad_bcrp"] = f["verdad_enaho"] = ""
        if f["codigo_bcrp"]:
            valor, url = verdad_bcrp(f)
            f["verdad_bcrp"] = str(round(valor, 4))
            fuentes.append(url)
        if f["nivel_enaho"]:
            f["verdad_enaho"] = str(round(verdad_enaho(f, s), 4))
            fuentes.append(fuente_enaho)
        f["fuente_verificacion"] = " | ".join(fuentes)
        for campo in ("bcrp", "enaho"):
            publicada = PUBLICADAS.get((f["id"], campo))
            if publicada is None:
                continue
            calculada = float(f["verdad_" + campo])
            tolerancia = float(f["tolerancia_" + campo])
            if abs(calculada - publicada) > tolerancia:
                raise SystemExit(f"Pregunta {f['id']}: {calculada} no coincide con la cifra del curso {publicada}.")
            cotejo.append({"id": f["id"], "campo": campo, "calculada": calculada, "publicada_en_el_curso": publicada,
                           "diferencia": round(calculada - publicada, 4), "fecha": date.today().isoformat()})
    with ARCHIVO.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    pd.DataFrame(cotejo).to_csv(ROOT / "evaluacion" / "verificacion_verdades.csv", index=False)
    for f in filas:
        print(f["id"], f["tipo"], "bcrp =", f["verdad_bcrp"] or "-", "| enaho =", f["verdad_enaho"] or "-")
    print(f"Cotejadas {len(cotejo)} cifras con lo publicado por el curso, sin diferencias fuera de tolerancia.")


if __name__ == "__main__":
    main()
