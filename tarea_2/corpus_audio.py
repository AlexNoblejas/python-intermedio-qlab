"""Corpus de audio de la Tarea 2: entrevistas y testimonios en español peruano de Wikimedia Commons.

    python corpus_audio.py            # baja el corpus y escribe datos/fuentes.csv
    python corpus_audio.py --listar   # solo muestra el inventario y los totales

Todo el material es CC BY-SA 4.0. Se descarga respetando las condiciones de uso de
Wikimedia: User-Agent descriptivo y pausa de 1,5 s entre peticiones. Los audios crudos
no se versionan (ver .gitignore); este script es la forma documentada de recuperarlos,
que es lo que pide la Tarea 2 para `datos/fuentes.csv`.

Las duraciones de `duracion_commons` vienen de la API de Commons (prop=imageinfo) y se
usan solo para planificar; la duración real se mide sobre el audio decodificado.
"""
from __future__ import annotations

import argparse
import csv
import time
import urllib.parse
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CRUDO = AQUI / "datos" / "raw" / "audio"
LISTO = AQUI / "datos" / "audio_16k"
FUENTES = AQUI / "datos" / "fuentes.csv"

PAUSA = 1.5
UA = {"User-Agent": "tarea2-qlab-pucp/1.0 (alexander.noblejas@pucp.edu.pe) python-urllib"}
FILEPATH = "https://commons.wikimedia.org/wiki/Special:FilePath/"
DESCRIPCION = "https://commons.wikimedia.org/wiki/File:"

LICENCIA = "CC BY-SA 4.0"

# id, archivo en Commons, grupo, autor (atribución), hablantes esperados, duración según Commons, nota
CORPUS = [
    # ── Entrevistas de calle y de espacio público (Wikimedia Perú y colaboradores) ──
    ("clip_01", "Entrevista 1,.wav", "calle", "Gianpier Yair Venegas Ambia", 2, 196.03,
     "Entrevista por el 201 aniversario de la Independencia del Perú"),
    ("clip_02", "Entrevista 2.wav", "calle", "Gianpier Yair Venegas Ambia", 2, 96.13,
     "Entrevista por el 201 aniversario de la Independencia del Perú"),
    ("clip_03", "Entrevista 3.wav", "calle", "Gianpier Yair Venegas Ambia", 2, 77.44,
     "Entrevista por el 201 aniversario de la Independencia del Perú"),
    ("clip_04", "Entrevista 4.wav", "calle", "Gianpier Yair Venegas Ambia", 2, 163.90,
     "Entrevista por el 201 aniversario de la Independencia del Perú"),
    ("clip_05", "Entrevista 1 en la Av. Rivagüero - El Agustino.ogg", "calle",
     "JorgeFlores-pe (Wikimedia Perú)", 2, 136.30,
     "Entrevista en la calle a una vendedora de frutas, previa del repechaje Perú-Australia (2022)"),
    ("clip_06", "Entrevista 2 en la Av. Rivagüero - El Agustino.ogg", "calle",
     "JorgeFlores-pe (Wikimedia Perú)", 3, 189.01,
     "Entrevista en la calle a dos vendedoras de dulces: tres voces, sirve para diarización"),
    ("clip_07", "Entrevista en el medio tiempo.opus", "calle", "Ariana Lucero De La Cruz", 2, 29.93,
     "Impresiones en el medio tiempo del partido Perú vs Australia"),
    ("clip_08", "Impresiones frente al partido Perú vs Australia.opus", "calle",
     "Ariana Lucero De La Cruz", 2, 20.15,
     "Impresiones de hinchas antes del partido Perú vs Australia"),
    ("clip_09", "Entrevista-Aurora Coronado-organización de mujeres indígenas-fiestas patrias.ogg",
     "conferencia", "QM Keen", 2, 250.62,
     "Dirigente de Fenmucarinap (sierra central) en una conferencia de prensa (2022)"),

    # ── Testimonio largo, español andino ──
    ("clip_10", "Testimonio Lucinda Quispealaya - Junín.ogg", "testimonio", "Wikimedia Commons", 1, 526.86,
     "Testimonio de Lucinda Quispealaya, Junín: el audio más largo del corpus (8,8 min)"),

    # ── Proyecto "Resonando Juntas" (WikiAcción Perú + Asimtría): testimonios ya anónimos ──
    ("clip_11", "Testimonio N° 01-Violencia obstétrica en Perú-Usuaria de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 42.62, "Testimonio anónimo leído en voz alta"),
    ("clip_12", "Testimonio N° 5 - Violencia obstétrica en Perú - usuaria de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 82.00, "Testimonio anónimo leído en voz alta"),
    ("clip_13", "Testimonio N° 10 - Violencia obstétrica en Perú - Servidora de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 42.50, "Testimonio anónimo leído en voz alta"),
    ("clip_14", "Testimonio N°12 - Violencia obstétrica en el Perú - Servidora de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 35.38, "Testimonio anónimo leído en voz alta"),
    ("clip_15", "Testimonio N°13 - Violencia obstétrica en el Perú - Servidora de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 47.87, "Testimonio anónimo leído en voz alta"),
    ("clip_16", "Testimonio N° 15-Violencia obstétrica en Perú- Usuaria de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 35.50, "Testimonio anónimo leído en voz alta"),
    ("clip_17", "Testimonio N° 19-Violencia obstétrica en Perú-Usuaria de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 43.00, "Testimonio anónimo leído en voz alta"),
    ("clip_18", "Testimonio N° 24-Violencia obstétrica en Perú-Usuaria de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 46.25, "Testimonio anónimo leído en voz alta"),
    ("clip_19", "Testimonio N°25- violencia obstetrica en Perú- Usuaria de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 52.37, "Testimonio anónimo leído en voz alta"),
    ("clip_20", "Testimonio N° 34-Violencia obstétrica en Perú-Usuaria de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 45.63, "Testimonio anónimo leído en voz alta"),
    ("clip_21", "Testimonio N° 37-Violencia obstétrica en Perú-Servidora de Salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 46.50, "Testimonio anónimo leído en voz alta"),
    ("clip_22", "Testimonio N°39 - Violencia Obstétrica en el Perú - Servidora de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 69.00, "Testimonio anónimo leído en voz alta"),
    ("clip_23", "Testimonio N° 41-Violencia obstétrica en Perú-Servidora de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 33.37, "Testimonio anónimo leído en voz alta"),
    ("clip_24", "Testimonio N° 42-Violencia obstétrica en Perú-Usuaria de salud.wav", "resonando",
     "Lidituo (Resonando Juntas, WikiAcción Perú)", 1, 53.00, "Testimonio anónimo leído en voz alta"),

    # ── Casos difíciles: coros y consignas con ruido de calle y música ──
    ("clip_25", "Alerta Feminista 1.ogg", "ruido", "Wikimedia Commons", 9, 43.43,
     "Consignas coreadas en una marcha: multitud, música y voces superpuestas"),
    ("clip_26", "Madres de Victimas de Feminicidio.ogg", "ruido", "Wikimedia Commons", 9, 56.04,
     "Consignas coreadas en una marcha: multitud, música y voces superpuestas"),
]

# Reserva documentada: entrevistas en quechua de Huaylas (proyecto "Voces y plantas"),
# para el punto de bonificación con MMS. No cuentan para los 30 min de español.
QUECHUA = [
    ("qwh_01", "Elena Figueroa - Entrevista sobre Españolada, Shansha, Áncash, Perú.ogg", 130.03),
    ("qwh_02", "Maricela Figueroa - Entrevista sobre Aurinsha, Shansha, Áncash, Perú.ogg", 96.00),
    ("qwh_03", "Ceferino Figueroa - Entrevista sobre Ratania, Shansha, Áncash, Perú.ogg", 644.41),
]


def _url(nombre: str) -> str:
    return FILEPATH + urllib.parse.quote(nombre.replace(" ", "_"))


def _pagina(nombre: str) -> str:
    return DESCRIPCION + urllib.parse.quote(nombre.replace(" ", "_"))


def descargar(solo_faltantes: bool = True) -> list[Path]:
    """Baja el corpus a datos/raw/audio/. Devuelve las rutas de los archivos crudos."""
    CRUDO.mkdir(parents=True, exist_ok=True)
    rutas = []
    for cid, nombre, *_ in CORPUS:
        destino = CRUDO / f"{cid}{Path(nombre).suffix}"
        rutas.append(destino)
        if solo_faltantes and destino.exists() and destino.stat().st_size > 0:
            print(f"  ya está  {destino.name}")
            continue
        peticion = urllib.request.Request(_url(nombre), headers=UA)
        with urllib.request.urlopen(peticion, timeout=180) as r:
            destino.write_bytes(r.read())
        print(f"  bajado   {destino.name}  ({destino.stat().st_size / 1e6:.1f} MB)")
        time.sleep(PAUSA)
    return rutas


def convertir() -> list[dict]:
    """Decodifica cada audio a mono 16 kHz y lo guarda como wav. Devuelve la duración real."""
    import soundfile as sf
    from voz import SR, cargar_audio

    LISTO.mkdir(parents=True, exist_ok=True)
    filas = []
    for cid, nombre, grupo, autor, hablantes, _dur, nota in CORPUS:
        crudo = CRUDO / f"{cid}{Path(nombre).suffix}"
        if not crudo.exists():
            print(f"  FALTA    {crudo.name} — corre descargar() primero")
            continue
        audio = cargar_audio(crudo)
        salida = LISTO / f"{cid}.wav"
        sf.write(salida, audio, SR)
        filas.append({"id": cid, "archivo_audio": str(salida.relative_to(AQUI)).replace("\\", "/"),
                      "duracion_seg": round(len(audio) / SR, 2), "grupo": grupo,
                      "hablantes_declarados": hablantes, "nota": nota, "autor": autor})
        print(f"  {cid}  {len(audio) / SR:7.1f} s  {grupo}")
    return filas


def escribir_fuentes(filas: list[dict]) -> Path:
    """datos/fuentes.csv con las columnas que pide la Tarea 2, en la modalidad audio."""
    FUENTES.parent.mkdir(parents=True, exist_ok=True)
    por_id = {f["id"]: f for f in filas}
    columnas = ["id", "modalidad", "titulo_fuente", "autor", "fuente_url", "licencia",
                "duracion_seg", "acceso", "nota"]
    acceso = "python corpus_audio.py (descarga desde Wikimedia Commons; el audio crudo no se versiona)"
    with FUENTES.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas)
        w.writeheader()
        for cid, nombre, grupo, autor, _hab, dur, nota in CORPUS:
            w.writerow({"id": cid, "modalidad": "audio", "titulo_fuente": nombre, "autor": autor,
                        "fuente_url": _pagina(nombre), "licencia": LICENCIA,
                        "duracion_seg": por_id.get(cid, {}).get("duracion_seg", dur),
                        "acceso": acceso, "nota": nota})
    return FUENTES


def listar() -> None:
    total = sum(c[5] for c in CORPUS)
    print(f"{len(CORPUS)} clips · {total / 60:.1f} min de español peruano · todo {LICENCIA}")
    for grupo in dict.fromkeys(c[2] for c in CORPUS):
        del_grupo = [c for c in CORPUS if c[2] == grupo]
        print(f"  {grupo:12s} {len(del_grupo):2d} clips  {sum(c[5] for c in del_grupo) / 60:5.1f} min")
    multi = [c[0] for c in CORPUS if c[4] > 2]
    print(f"  multihablante: {', '.join(multi)}")
    print(f"  reserva quechua de Huaylas (bonificación MMS): {len(QUECHUA)} clips")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--listar", action="store_true", help="solo mostrar el inventario")
    args = ap.parse_args()
    if args.listar:
        listar()
    else:
        listar()
        print("\nDescargando…")
        descargar()
        print("\nConvirtiendo a mono 16 kHz…")
        filas = convertir()
        ruta = escribir_fuentes(filas)
        real = sum(f["duracion_seg"] for f in filas)
        print(f"\n{len(filas)} clips · {real / 60:.1f} min medidos sobre el audio decodificado")
        print(f"fuentes escritas en {ruta}")
