"""Arma datos/ejemplos/: la muestra ligera y publicable que el dashboard sí puede mostrar.

    python preparar_ejemplos.py

El corpus crudo no se versiona (pesa y, en el caso del audio de Commons, no hace falta: se
recupera con corpus_audio.py). Pero el dashboard desplegado necesita poder mostrar una imagen y
reproducir un audio, así que se publica una selección pequeña:

- Imágenes reducidas a 1200 px de ancho y JPEG de calidad 80.
- Clips de audio cortos, tal cual (mono 16 kHz, pocos cientos de KB cada uno).

Qué se puede publicar y por qué:
- Los 8 impresos son páginas de resoluciones del CEPLAN: textos oficiales de carácter
  administrativo, sin protección por el art. 9 del DL 822.
- Las fotos y los manuscritos son capturas propias del estudiante, sin datos personales reales.
- Los audios son CC BY-SA 4.0 de Wikimedia Commons, con su atribución en datos/fuentes.csv.
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "datos"
EJEMPLOS = DATOS / "ejemplos"

ANCHO = 1200
CALIDAD = 80

# una muestra de cada tipo de documento, con los evaluados incluidos
IMAGENES = ["impreso_02", "impreso_04", "impreso_08", "foto_01", "foto_04", "foto_07",
            "manu_01", "manu_03", "manu_06", "manu_09"]
# clips cortos, uno por condición de grabación
AUDIOS = ["clip_08", "clip_07", "clip_23", "clip_25", "clip_26", "clip_03"]


def imagenes() -> list[dict]:
    from PIL import Image

    destino = EJEMPLOS / "imagenes"
    destino.mkdir(parents=True, exist_ok=True)
    filas = []
    for did in IMAGENES:
        origen = next((p for p in (DATOS / "raw" / "documentos").glob(f"{did}.*")), None)
        if origen is None:
            print(f"  falta {did}")
            continue
        img = Image.open(origen)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        if img.width > ANCHO:
            img = img.resize((ANCHO, round(img.height * ANCHO / img.width)), Image.LANCZOS)
        salida = destino / f"{did}.jpg"
        img.save(salida, "JPEG", quality=CALIDAD, optimize=True)
        filas.append({"id": did, "tipo": "imagen",
                      "archivo": f"datos/ejemplos/imagenes/{salida.name}",
                      "kb": round(salida.stat().st_size / 1024)})
        print(f"  {did:12s} {img.width}x{img.height}  {salida.stat().st_size / 1024:6.0f} KB")
    return filas


def audios() -> list[dict]:
    destino = EJEMPLOS / "audio"
    destino.mkdir(parents=True, exist_ok=True)
    filas = []
    for cid in AUDIOS:
        origen = DATOS / "audio_16k" / f"{cid}.wav"
        if not origen.exists():
            print(f"  falta {cid}")
            continue
        salida = destino / f"{cid}.wav"
        shutil.copy2(origen, salida)
        filas.append({"id": cid, "tipo": "audio",
                      "archivo": f"datos/ejemplos/audio/{salida.name}",
                      "kb": round(salida.stat().st_size / 1024)})
        print(f"  {cid:12s} {salida.stat().st_size / 1024:6.0f} KB")
    return filas


if __name__ == "__main__":
    print("Imágenes:")
    filas = imagenes()
    print("\nAudio:")
    filas += audios()

    manifiesto = EJEMPLOS / "manifiesto.csv"
    with manifiesto.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "tipo", "archivo", "kb"])
        w.writeheader()
        w.writerows(filas)
    total = sum(f["kb"] for f in filas)
    print(f"\n{len(filas)} ejemplos · {total / 1024:.1f} MB · manifiesto en {manifiesto}")
