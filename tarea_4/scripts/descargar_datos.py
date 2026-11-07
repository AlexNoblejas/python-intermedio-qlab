"""Descarga ENAHO 2024 y geometria del curso verificando el contenido.

Las URLs de INEI usan /iinei/ en la ruta; se prueban variantes porque el
servidor del proveedor puede cambiar de ruta o presentar fallos temporales.
No se sobreescriben archivos originales sin intervencion del usuario.
"""
from __future__ import annotations

import argparse
import json
import time
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "datos"
BASE_INEI = "https://proyectos.inei.gob.pe"
GEO = "https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson"

FUENTES = {
    "modulo34": {
        "archivo": "966-Modulo34.zip",
        "urls": [f"{BASE_INEI}/iinei/srienaho/descarga/STATA/966-Modulo34.zip",
                 f"{BASE_INEI}/inei/srienaho/descarga/STATA/966-Modulo34.zip"],
        "patron": "sumaria-2024",
    },
    "modulo02": {
        "archivo": "966-Modulo02.zip",
        "urls": [f"{BASE_INEI}/iinei/srienaho/descarga/STATA/966-Modulo02.zip",
                 f"{BASE_INEI}/inei/srienaho/descarga/STATA/966-Modulo02.zip"],
        "patron": "enaho01-2024-200",
    },
    "geojson": {"archivo": "peru_departamental_simple.geojson", "urls": [GEO], "patron": "geojson"},
}


def verificar_contenido(path: Path, patron: str) -> None:
    """Evita dar por correcto un HTML 200, ZIP dañado o GeoJSON equivocado."""
    if not path.is_file() or path.stat().st_size < 50:
        raise ValueError(f"Archivo inexistente o demasiado pequeno: {path}")
    if patron == "geojson":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError) as e:
            raise ValueError("Descarga GeoJSON no es JSON valido") from e
        features = data.get("features", []) if isinstance(data, dict) else []
        if data.get("type") != "FeatureCollection" or not features:
            raise ValueError("GeoJSON no contiene una FeatureCollection valida")
        props = [ft.get("properties", {}) for ft in features]
        if any("FIRST_IDDP" not in p for p in props):
            raise ValueError("GeoJSON carece de FIRST_IDDP")
        if len({str(p["FIRST_IDDP"]).zfill(2) for p in props}) != 25:
            raise ValueError("GeoJSON no identifica exactamente 25 codigos departamentales")
        return
    if not zipfile.is_zipfile(path):
        raise ValueError("Respuesta no es un ZIP valido: podria ser HTML de error")
    with zipfile.ZipFile(path) as z:
        archivos = [Path(n).name.lower() for n in z.namelist() if n.lower().endswith(".dta")]
        encontradas = [n for n in archivos if n == f"{patron.lower()}.dta"]  # exacto: hay sumaria-2024-12g.dta
        if len(encontradas) != 1:
            raise ValueError(f"ZIP no contiene un unico DTA esperado {patron!r}: {encontradas}")


def descargar(urls: list[str], destino: Path, patron: str, pausas: bool = True) -> str:
    if destino.exists():
        verificar_contenido(destino, patron)
        print(f"Archivo existente verificado: {destino.name}")
        return "existente"
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(destino.suffix + ".parcial")
    ultima = "Sin respuesta"
    for url in urls:
        for intento in range(2):
            try:
                with httpx.stream(
                    "GET", url, timeout=httpx.Timeout(180, connect=30), follow_redirects=True,
                    headers={"User-Agent": "Data-Science-Python/2026 Tarea4"}
                ) as r:
                    r.raise_for_status()
                    with temporal.open("wb") as f:
                        for bloque in r.iter_bytes(chunk_size=1 << 20):
                            f.write(bloque)
                verificar_contenido(temporal, patron)
                temporal.replace(destino)
                print(f"Descargado y verificado: {destino.name} ({destino.stat().st_size/1048576:.2f} MiB)")
                print(f"URL fuente: {url}")
                return url
            except (httpx.HTTPError, OSError, ValueError, zipfile.BadZipFile) as e:
                ultima = f"{type(e).__name__}: {e}"
                temporal.unlink(missing_ok=True)
                print(f"Fallo en {url} (intento {intento+1}/2): {ultima}")
                if pausas and intento == 0:
                    time.sleep(2)
    raise SystemExit(f"No se pudo obtener {destino.name}. Ultimo error: {ultima}. Descargar en el portal INEI y verificar el ZIP.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", nargs="*", choices=sorted(FUENTES), help="Por defecto descarga los tres insumos")
    args = parser.parse_args()
    for nombre in (args.solo or FUENTES):
        meta = FUENTES[nombre]
        descargar(meta["urls"], DATOS / meta["archivo"], meta["patron"])


if __name__ == "__main__":
    main()
