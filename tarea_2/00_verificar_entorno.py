"""Prueba de humo antes de ejecutar los notebooks. Mide y reporta; no escribe nada del corpus.

    python 00_verificar_entorno.py

Contesta cuatro preguntas que deciden la estrategia:
  1. ¿Cuántos documentos y clips hay realmente en disco?
  2. ¿PaddleOCR corre, y cuánto tarda por página en esta máquina?
  3. ¿faster-whisper sobrevive con su VAD de onnxruntime, o lo tumba como tumbó la segmentación?
  4. ¿Cuánto tardaría entonces transcribir los 41 minutos?

El punto 3 se corre en un SUBPROCESO a propósito: un crash nativo no deja traceback y mataría
este script entero, así que lo aislamos y miramos el código de salida.
"""
from __future__ import annotations

# torch va PRIMERO, antes de numpy/pandas/scipy. En Windows, con conda base activo encima del
# venv, cargarlo después de otra librería que ya trajo su propio OpenMP/MKL rompe sus DLL con
# WinError 1114 en c10.dll. Importado primero, gana la carrera y funciona.
try:
    import torch
except Exception as _e:
    torch = None
    print(f"[AVISO] torch no carga: {type(_e).__name__}: {_e}")

import shutil
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "datos"


def titulo(t):
    print(f"\n{'=' * 70}\n{t}\n{'=' * 70}", flush=True)


# ─────────────────────────────────────────────── 1. inventario
titulo("1. Inventario en disco")
imgs = sorted(p for p in (DATOS / "raw" / "documentos").glob("*")
              if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
tipos = {}
for p in imgs:
    tipos[p.stem.split("_")[0]] = tipos.get(p.stem.split("_")[0], 0) + 1
print(f"documentos: {len(imgs)}  ->  {tipos}", flush=True)

import pandas as pd
clips = pd.read_csv(DATOS / "clips.csv") if (DATOS / "clips.csv").exists() else pd.DataFrame()
if len(clips):
    print(f"clips: {len(clips)} · {clips.duracion_seg.sum() / 60:.1f} min · "
          f"grupos {dict(clips.grupo.value_counts())}", flush=True)
MINUTOS = clips.duracion_seg.sum() / 60 if len(clips) else 41.0

xlsx = AQUI / "referencias_plantilla.xlsx"
if xlsx.exists():
    for hoja in ("documentos", "audio"):
        df = pd.read_excel(xlsx, sheet_name=hoja)
        df = df[~df["id"].astype(str).str.startswith("EJEMPLO")].dropna(subset=["texto_referencia"])
        print(f"referencias manuales en '{hoja}': {len(df)}", flush=True)

# ─────────────────────────────────────────────── 2. versiones
titulo("2. Versiones y dispositivo")
if torch is None:
    print("torch NO carga: PaddleOCR con engine=transformers no podrá correr", flush=True)
else:
    print(f"python {sys.version.split()[0]} · torch {torch.__version__} · "
          f"cuda disponible: {torch.cuda.is_available()}", flush=True)
try:
    import paddleocr
    print(f"paddleocr {paddleocr.__version__}", flush=True)
except Exception as e:
    print(f"paddleocr NO importa: {e}", flush=True)
print(f"tesseract en el PATH: {shutil.which('tesseract') or 'NO'}", flush=True)

# ─────────────────────────────────────────────── 3. OCR
titulo("3. PaddleOCR — una página densa y un manuscrito")
OPCIONES = dict(use_doc_orientation_classify=False, use_doc_unwarping=False,
                use_textline_orientation=False)
try:
    import paddleocr
    t0 = time.perf_counter()
    ocr = paddleocr.PaddleOCR(engine="transformers", lang="es", device="cpu", **OPCIONES)
    print(f"modelo cargado en {time.perf_counter() - t0:.1f} s "
          f"(la primera vez baja ~2 GB)", flush=True)

    for nombre in ("impreso_02", "manu_01", "foto_01"):
        cand = [p for p in imgs if p.stem == nombre]
        if not cand:
            print(f"  {nombre}: no está en disco", flush=True)
            continue
        t0 = time.perf_counter()
        r = ocr.predict(str(cand[0]))[0]
        seg = time.perf_counter() - t0
        textos = r["rec_texts"]
        print(f"  {nombre}: {len(textos)} líneas, {sum(len(x) for x in textos)} caracteres, "
              f"{seg:.1f} s", flush=True)
        print(f"    primeras líneas: {textos[:3]}", flush=True)
    print(f"\n  ESTIMADO OCR de {len(imgs)} documentos: ~{len(imgs) * seg / 60:.1f} min", flush=True)
except Exception as e:
    print(f"OCR FALLÓ: {type(e).__name__}: {e}", flush=True)

# ─────────────────────────────────────────────── 4. ASR, el VAD aislado
titulo("4. faster-whisper small en CPU — ¿sobrevive el VAD?")
clip = DATOS / "audio_16k" / "clip_08.wav"
if not clip.exists():
    print("falta datos/audio_16k/clip_08.wav", flush=True)
else:
    GUION = r'''
import sys, time, json
from faster_whisper import WhisperModel
ruta, vad = sys.argv[1], sys.argv[2] == "1"
m = WhisperModel("small", device="cpu", compute_type="int8")
t0 = time.perf_counter()
segs, info = m.transcribe(ruta, language="es", beam_size=5, vad_filter=vad)
texto = " ".join(s.text.strip() for s in segs)
print(json.dumps({"segundos": round(time.perf_counter() - t0, 2),
                  "palabras": len(texto.split()), "texto": texto[:200]}, ensure_ascii=False))
'''
    for etiqueta, bandera in (("VAD encendido", "1"), ("VAD apagado", "0")):
        print(f"\n  --- {etiqueta} ---", flush=True)
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, "-c", GUION, str(clip), bandera],
                           capture_output=True, text=True, timeout=1800)
        if r.returncode != 0:
            print(f"  SE CAYÓ (código {r.returncode}) — esto es el crash nativo de onnxruntime",
                  flush=True)
            print(f"  stderr: {(r.stderr or '').strip()[-300:]}", flush=True)
            continue
        linea = [l for l in r.stdout.strip().splitlines() if l.startswith("{")]
        if not linea:
            print(f"  sin salida JSON. stdout: {r.stdout[-300:]}", flush=True)
            continue
        import json
        d = json.loads(linea[-1])
        factor = d["segundos"] / 20.2
        print(f"  OK · {d['segundos']} s de proceso para 20.2 s de audio "
              f"(x{factor:.2f} tiempo real, incluye cargar el modelo)", flush=True)
        print(f"  {d['palabras']} palabras: {d['texto']!r}", flush=True)
        print(f"  ESTIMADO para {MINUTOS:.0f} min de audio: "
              f"~{MINUTOS * factor:.0f} min (menos, porque el modelo ya está cargado)", flush=True)

titulo("Fin")
