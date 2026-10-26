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

PAUSA = 1.5          # segundos de espera entre peticiones a Wikimedia
SR = 16_000          # mono 16 kHz: lo que esperan todos los modelos de voz de la sesión 13
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


def filas_en_disco() -> list[dict]:
    """Reconstruye el inventario a partir de los wav ya convertidos, sin volver a decodificar."""
    import wave
    filas = []
    for cid, nombre, grupo, autor, hablantes, _dur, nota in CORPUS:
        ruta = LISTO / f"{cid}.wav"
        if not ruta.exists():
            continue
        with wave.open(str(ruta)) as w:
            segundos = w.getnframes() / w.getframerate()
        filas.append({"id": cid, "archivo_audio": str(ruta.relative_to(AQUI)).replace("\\", "/"),
                      "duracion_seg": round(segundos, 2), "grupo": grupo,
                      "hablantes_declarados": hablantes, "nota": nota, "autor": autor})
    return filas


def pausas(audio, min_pausa: float = 0.4, marco: float = 0.02) -> list[float]:
    """Centros de las pausas del habla, en segundos.

    Solo numpy: mide la energía (RMS) en marcos de 20 ms y busca rachas de baja energía de al
    menos `min_pausa`. El umbral es relativo al propio audio, así que funciona igual en un
    testimonio grabado en interior y en una entrevista de calle con tráfico de fondo.

    Se hace así, y no con el VAD de faster-whisper, porque ese VAD corre sobre onnxruntime y
    en esta máquina tumbaba el intérprete sin dejar traceback.
    """
    import numpy as np

    n = int(marco * SR)
    if len(audio) < n * 10:
        return []
    marcos = audio[: len(audio) // n * n].reshape(-1, n).astype(np.float64)
    rms = np.sqrt((marcos ** 2).mean(axis=1))
    umbral = max(np.percentile(rms, 20) * 2.5, rms.max() * 0.02)
    silencio = rms < umbral
    minimo_marcos = max(1, int(min_pausa / marco))

    centros, i = [], 0
    while i < len(silencio):
        if not silencio[i]:
            i += 1
            continue
        j = i
        while j < len(silencio) and silencio[j]:
            j += 1
        if j - i >= minimo_marcos:
            centros.append((i + j) / 2 * marco)
        i = j
    return centros



def regiones_de_voz(audio, marco: float = 0.02, max_tramo: float = 25.0,
                    min_pausa: float = 0.5) -> list[tuple[float, float]]:
    """Trozos de audio para mandar al modelo, en segundos: el VAD de repuesto, con numpy.

    Existe porque el VAD de faster-whisper corre sobre onnxruntime y en esta máquina tumba el
    intérprete sin dejar traceback.

    Criterio deliberadamente conservador: **cubre todo el audio**, cortando en las pausas en
    trozos de hasta `max_tramo`, y descarta un trozo solo si está prácticamente en silencio
    absoluto. Un VAD agresivo con umbral relativo parecía mejor, pero medido sobre el `clip_06`
    —una entrevista de calle con tráfico de fondo— se comía el 60 % del audio: en una grabación
    ruidosa el piso de ruido sube y arrastra el umbral por encima de la voz. Perder habla
    arruina el WER mucho más que mandarle al modelo un par de segundos de silencio.
    """
    import numpy as np

    n = int(marco * SR)
    dur = len(audio) / SR
    if len(audio) < n * 10:
        return [(0.0, dur)]

    marcos = audio[: len(audio) // n * n].reshape(-1, n).astype(np.float64)
    rms = np.sqrt((marcos ** 2).mean(axis=1))
    pico = rms.max() or 1.0

    # cortar en pausas, sin dejar huecos: cada trozo empieza donde terminó el anterior
    candidatos = pausas(audio, min_pausa=min_pausa, marco=marco)
    tramos, ini = [], 0.0
    for corte in candidatos:
        if corte - ini >= max_tramo * 0.6:
            tramos.append((ini, corte))
            ini = corte
    tramos.append((ini, dur))

    # si una pausa quedó lejos, partir a lo bruto para no pasar de max_tramo
    salida = []
    for a, b in tramos:
        while b - a > max_tramo:
            salida.append((a, a + max_tramo))
            a += max_tramo
        if b - a > 0.05:
            salida.append((a, b))

    # descartar solo lo que es silencio de verdad (nada que se parezca a voz en todo el trozo)
    utiles = []
    for a, b in salida:
        i, j = int(a / marco), max(int(a / marco) + 1, int(b / marco))
        if rms[i:j].max(initial=0.0) >= pico * 0.01:
            utiles.append((a, b))
    return utiles or [(0.0, dur)]


def diarizar_simple(audio, tramos: list[tuple[float, float]], n_hablantes: int | None = None,
                    umbral: float = 0.9, min_dur: float = 1.0) -> list[int]:
    """Agrupa los tramos por hablante. Devuelve una etiqueta entera por tramo.

    Huella de voz = media y desviación de 20 coeficientes MFCC sobre el tramo, estandarizadas
    entre tramos; después agrupamiento jerárquico con distancia coseno. Es la diarización que
    se puede hacer con lo que ya está instalado (librosa y scikit-learn, que entra con librosa).

    No se usa `voz.diarizar` porque sus huellas vienen de WeSpeaker vía `pyannote.audio`, que no
    está en las dependencias de esta tarea y cuyo modelo está restringido en Hugging Face
    (pide token y aceptar términos). Un MFCC distingue voces peor que un modelo entrenado para
    eso, y así queda dicho en el notebook: sirve para separar turnos en una entrevista, no para
    afirmar identidades.

    Los tramos de menos de `min_dur` no votan en el agrupamiento —"sí", "ajá" dan huellas poco
    fiables— y después se asignan al grupo más parecido.

    Conviene pasar `n_hablantes` cuando la fuente lo dice: medido sobre el `clip_06`, con el
    número declarado (3) el reparto queda en 15/11/5 tramos y alterna como una entrevista real,
    mientras que dejándolo libre el umbral sobre MFCC sobre-segmenta.
    """
    import librosa
    import numpy as np
    from sklearn.cluster import AgglomerativeClustering

    if not tramos:
        return []

    huellas = []
    for a, b in tramos:
        x = audio[int(a * SR):int(b * SR)]
        if len(x) < SR // 4:
            x = np.pad(x, (0, SR // 4 - len(x)))
        m = librosa.feature.mfcc(y=x.astype(np.float32), sr=SR, n_mfcc=20)
        huellas.append(np.concatenate([m.mean(axis=1), m.std(axis=1)]))
    H = np.vstack(huellas)
    H = (H - H.mean(axis=0)) / (H.std(axis=0) + 1e-9)
    H = H / (np.linalg.norm(H, axis=1, keepdims=True) + 1e-9)

    largos = np.array([b - a >= min_dur for a, b in tramos])
    if largos.sum() < 2:
        largos = np.ones(len(tramos), dtype=bool)
    if n_hablantes == 1 or largos.sum() < 2:
        return [0] * len(tramos)

    grupo = AgglomerativeClustering(
        n_clusters=n_hablantes,
        distance_threshold=None if n_hablantes else umbral,
        metric="cosine", linkage="average").fit(H[largos])
    centros = np.vstack([H[largos][grupo.labels_ == k].mean(axis=0)
                         for k in range(grupo.n_clusters_)])
    etiquetas = (H @ centros.T).argmax(axis=1)
    etiquetas[largos] = grupo.labels_

    # numerar por orden de aparición: H1 es quien habla primero
    orden = {k: i for i, k in enumerate(dict.fromkeys(etiquetas.tolist()))}
    return [orden[e] for e in etiquetas.tolist()]

# El clip multihablante no se parte: partirlo repartiría las voces entre bloques y dejaría a la
# diarización sin el caso que el enunciado pide.
NO_PARTIR = {"clip_06"}


def segmentar(filas: list[dict], max_seg: float = 200.0, objetivo: float = 90.0,
              minimo: float = 20.0) -> list[dict]:
    """Parte los audios largos en bloques de ~90 s, siempre en una pausa del habla.

    Solo se parten los dos audios genuinamente largos del corpus: la conferencia de 4,2 min y
    el testimonio de Junín de 8,8 min. Eso sube el número de clips y, sobre todo, permite que
    la muestra de evaluación incluya esas dos fuentes sin obligar a transcribir nueve minutos
    seguidos a mano.

    Devuelve la lista de clips (la unidad de `datos/transcripciones.csv`); cada uno recuerda de
    qué archivo salió y en qué segundo empieza.
    """
    import numpy as np
    from scipy.io import wavfile

    clips = []
    for f in filas:
        if f["duracion_seg"] <= max_seg or f["id"] in NO_PARTIR:
            clips.append({**f, "clip_id": f["id"], "fuente_id": f["id"], "inicio_seg": 0.0})
            continue

        sr, x = wavfile.read(AQUI / f["archivo_audio"])
        x = x.astype(np.float32) / 32768.0 if x.dtype.kind == "i" else x.astype(np.float32)
        dur = len(x) / sr

        cortes, ini = [], 0.0
        for pausa in pausas(x):
            if pausa - ini >= objetivo:
                cortes.append((ini, pausa))
                ini = pausa
        cortes.append((ini, dur))
        if len(cortes) > 1 and cortes[-1][1] - cortes[-1][0] < minimo:
            (a0, _), (_, b1) = cortes[-2], cortes[-1]
            cortes[-2:] = [(a0, b1)]

        for i, (a, b) in enumerate(cortes):
            cid = f"{f['id']}_{chr(ord('a') + i)}"
            salida = LISTO / f"{cid}.wav"
            wavfile.write(salida, SR, (x[int(a * sr):int(b * sr)] * 32767).astype(np.int16))
            clips.append({**f, "clip_id": cid, "fuente_id": f["id"], "inicio_seg": round(a, 2),
                          "archivo_audio": str(salida.relative_to(AQUI)).replace("\\", "/"),
                          "duracion_seg": round(b - a, 2)})
            print(f"  {cid}  {b - a:6.1f} s  (de {f['id']}, desde {a:.0f} s)")
    return clips


def escribir_clips(clips: list[dict]) -> Path:
    """datos/clips.csv: el inventario de clips que consume 01_extraccion.ipynb."""
    columnas = ["clip_id", "fuente_id", "archivo_audio", "duracion_seg", "inicio_seg",
                "grupo", "hablantes_declarados", "autor", "nota"]
    destino = AQUI / "datos" / "clips.csv"
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        w.writerows(clips)
    return destino


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
    ap.add_argument("--segmentar", action="store_true",
                    help="saltarse la descarga: segmentar los wav que ya están en disco")
    args = ap.parse_args()
    if args.listar:
        listar()
    elif args.segmentar:
        filas = filas_en_disco()
        print(f"{len(filas)} wav en disco · {sum(f['duracion_seg'] for f in filas) / 60:.1f} min")
        escribir_fuentes(filas)
        print("\nSegmentando los audios largos…")
        clips = segmentar(filas)
        destino = escribir_clips(clips)
        total = sum(c["duracion_seg"] for c in clips)
        print(f"\n{len(clips)} clips · {total / 60:.1f} min · inventario en {destino}")
    else:
        listar()
        print("\nDescargando…")
        descargar()
        print("\nConvirtiendo a mono 16 kHz…")
        filas = convertir()
        ruta = escribir_fuentes(filas)
        real = sum(f["duracion_seg"] for f in filas)
        print(f"\n{len(filas)} archivos · {real / 60:.1f} min medidos sobre el audio decodificado")
        print(f"fuentes escritas en {ruta}")
        print("\nSegmentando los audios largos…")
        clips = segmentar(filas)
        destino = escribir_clips(clips)
        total = sum(c["duracion_seg"] for c in clips)
        print(f"\n{len(clips)} clips · {total / 60:.1f} min · inventario en {destino}")
