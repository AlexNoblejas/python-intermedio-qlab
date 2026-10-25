"""Los 8 impresos nítidos del corpus de documentos: páginas de resoluciones oficiales del CEPLAN.

    python corpus_documentos.py            # baja los PDF y renderiza las páginas a JPG
    python corpus_documentos.py --listar   # solo muestra el inventario

Por qué resoluciones y no informes: el artículo 9 del Decreto Legislativo 822 (Ley sobre el
Derecho de Autor) excluye de protección "los textos oficiales de carácter legislativo,
administrativo o judicial". Una Resolución de Presidencia de Consejo Directivo es exactamente
eso, así que puede usarse y su texto puede publicarse en el dashboard sin problema de licencia.
Los informes y guías del CEPLAN, en cambio, llevan "© Derechos reservados" y quedan fuera.

Se renderiza a 300 dpi, que es la resolución que la sesión 10 recomienda para PaddleOCR.
Las páginas 2 de las resoluciones son las más cortas (solo los artículos y la firma): son las
candidatas naturales para la muestra de 10 documentos con transcripción manual.
"""
from __future__ import annotations

import argparse
import csv
import time
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PDFS = AQUI / "datos" / "raw" / "pdf"
IMGS = AQUI / "datos" / "raw" / "documentos"
FUENTES = AQUI / "datos" / "fuentes.csv"

PAUSA = 1.5
UA = {"User-Agent": "tarea2-qlab-pucp/1.0 (alexander.noblejas@pucp.edu.pe) python-urllib"}
LICENCIA = "Texto oficial de carácter administrativo — sin protección (DL 822, art. 9)"
BASE = "https://cdn.www.gob.pe/uploads/document/file/"

# id, archivo PDF, página (1-based), norma, fecha, url
PLAN = [
    ("impreso_01", "rs_pcd_0372026.pdf", 1, "R. de Presidencia de Consejo Directivo N° 037-2026/CEPLAN/PCD",
     "2026-06-02", BASE + "10084714/8214563-rs_pcd_0372026.pdf"),
    ("impreso_02", "rs_pcd_0372026.pdf", 2, "R. de Presidencia de Consejo Directivo N° 037-2026/CEPLAN/PCD",
     "2026-06-02", BASE + "10084714/8214563-rs_pcd_0372026.pdf"),
    ("impreso_03", "rs_pcd_0332026.pdf", 1, "R. de Presidencia de Consejo Directivo N° 033-2026/CEPLAN/PCD",
     "2026-05-26", BASE + "10046957/8188352-rs_pcd_0332026.pdf"),
    ("impreso_04", "rs_pcd_0332026.pdf", 2, "R. de Presidencia de Consejo Directivo N° 033-2026/CEPLAN/PCD",
     "2026-05-26", BASE + "10046957/8188352-rs_pcd_0332026.pdf"),
    ("impreso_05", "rs_pcd_0032026.pdf", 1, "R. de Presidencia de Consejo Directivo N° 003-2026/CEPLAN/PCD",
     "2026-01-09", BASE + "9270360/7606459-rs_pcd_0032026.pdf"),
    ("impreso_06", "rs_pcd_0032026.pdf", 2, "R. de Presidencia de Consejo Directivo N° 003-2026/CEPLAN/PCD",
     "2026-01-09", BASE + "9270360/7606459-rs_pcd_0032026.pdf"),
    ("impreso_07", "rs_pcd_0482025.pdf", 1, "R. de Presidencia de Consejo Directivo N° 048-2025/CEPLAN/PCD",
     "2025-05-21", BASE + "8100180/6791050-rs_pcd_0482025.pdf"),
    ("impreso_08", "rs_pcd_0762025.pdf", 2, "R. de Presidencia de Consejo Directivo N° 76-2025/CEPLAN/PCD",
     "2025-08-27", BASE + "8559734/7088837-rs_pcd_0762025.pdf"),
]

DPI = 300


def descargar() -> None:
    PDFS.mkdir(parents=True, exist_ok=True)
    vistos = {}
    for _id, archivo, _pag, _norma, _fecha, url in PLAN:
        if archivo in vistos:
            continue
        vistos[archivo] = url
    for archivo, url in vistos.items():
        destino = PDFS / archivo
        if destino.exists() and destino.stat().st_size > 0:
            print(f"  ya está  {archivo}")
            continue
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
            destino.write_bytes(r.read())
        print(f"  bajado   {archivo}  ({destino.stat().st_size / 1e6:.2f} MB)")
        time.sleep(PAUSA)


def renderizar() -> list[dict]:
    """Cada entrada del PLAN -> un JPG a 300 dpi en datos/raw/documentos/."""
    import fitz  # pymupdf

    IMGS.mkdir(parents=True, exist_ok=True)
    filas = []
    for did, archivo, pagina, norma, fecha, url in PLAN:
        pdf = PDFS / archivo
        if not pdf.exists():
            print(f"  FALTA    {archivo} — corre descargar() primero")
            continue
        with fitz.open(pdf) as doc:
            if pagina > doc.page_count:
                print(f"  {did}: {archivo} no tiene página {pagina} (tiene {doc.page_count})")
                continue
            pix = doc[pagina - 1].get_pixmap(dpi=DPI)
            salida = IMGS / f"{did}.jpg"
            pix.save(salida)
        filas.append({"id": did, "archivo": f"datos/raw/documentos/{did}.jpg", "tipo": "impreso",
                      "norma": norma, "fecha_norma": fecha, "pagina": pagina, "fuente_url": url})
        print(f"  {did}  {archivo} p.{pagina}  {pix.width}x{pix.height}")
    return filas


def escribir_fuentes(filas: list[dict]) -> Path:
    """Agrega las filas de documentos a datos/fuentes.csv, conservando las de audio."""
    columnas = ["id", "modalidad", "titulo_fuente", "autor", "fuente_url", "licencia",
                "duracion_seg", "acceso", "nota"]
    previas = []
    if FUENTES.exists():
        with FUENTES.open(encoding="utf-8") as fh:
            previas = [f for f in csv.DictReader(fh) if f.get("modalidad") != "documento"]
    acceso = "python corpus_documentos.py (descarga el PDF de gob.pe y renderiza la página a 300 dpi)"
    with FUENTES.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas)
        w.writeheader()
        for f in previas:
            w.writerow({c: f.get(c, "") for c in columnas})
        for f in filas:
            w.writerow({"id": f["id"], "modalidad": "documento", "titulo_fuente": f["norma"],
                        "autor": "CEPLAN (Presidencia del Consejo Directivo)",
                        "fuente_url": f["fuente_url"], "licencia": LICENCIA, "duracion_seg": "",
                        "acceso": acceso,
                        "nota": f"página {f['pagina']}, resolución del {f['fecha_norma']}"})
    return FUENTES


def listar() -> None:
    print(f"{len(PLAN)} impresos nítidos = páginas de {len({p[1] for p in PLAN})} resoluciones del CEPLAN")
    print(f"  licencia: {LICENCIA}")
    for did, archivo, pagina, norma, *_ in PLAN:
        print(f"  {did}  p.{pagina}  {norma}")
    print("\nFaltan, y los captura el estudiante:")
    print("  foto_01 … foto_08   fotos de celular con sombra o inclinación")
    print("  manu_01 … manu_09   manuscritos propios")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--listar", action="store_true")
    args = ap.parse_args()
    listar()
    if not args.listar:
        print("\nDescargando PDF…")
        descargar()
        print("\nRenderizando páginas a 300 dpi…")
        filas = renderizar()
        print(f"\nfuentes actualizadas en {escribir_fuentes(filas)}")
