"""Rellena los números del README y arma el comentario de entrega.

    python cerrar_entrega.py https://mi-app.streamlit.app

Lee datos/resultados.json (lo escribe 02_evaluacion.ipynb), reemplaza los marcadores
PENDIENTE del README e imprime el comentario con el formato exacto que pide el Issue #190.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RES = AQUI / "datos" / "resultados.json"
README = AQUI / "README.md"


def pct(x):
    return "—" if x is None else f"{round(x * 20)}/20"


def main(url: str | None) -> None:
    if not RES.exists():
        sys.exit("Falta datos/resultados.json: ejecuta 02_evaluacion.ipynb primero")
    r = json.loads(RES.read_text(encoding="utf-8"))

    cer, wer = r.get("CER"), r.get("WER")
    acuerdo = r.get("acuerdo_llm_humano")
    enlace = url or "PENDIENTE"

    texto = README.read_text(encoding="utf-8")
    cambios = {
        "| Dashboard público | `PENDIENTE` |": f"| Dashboard público | {enlace} |",
        "| CER — PaddleOCR sobre 10 documentos | `PENDIENTE` |":
            f"| CER — PaddleOCR sobre 10 documentos | **{cer:.4f}** |" if cer is not None else None,
        "| WER — faster-whisper small sobre 10 clips | `PENDIENTE` |":
            f"| WER — faster-whisper small sobre 10 clips | **{wer:.4f}** |" if wer is not None else None,
        "| Acuerdo LLM–humano | `PENDIENTE`/20 |":
            f"| Acuerdo LLM–humano | **{pct(acuerdo)}** |",
    }
    for viejo, nuevo in cambios.items():
        if nuevo and viejo in texto:
            texto = texto.replace(viejo, nuevo, 1)
    README.write_text(texto, encoding="utf-8")
    faltan = texto.count("PENDIENTE")
    print(f"README actualizado · quedan {faltan} marcadores PENDIENTE")
    if faltan:
        for linea in texto.splitlines():
            if "PENDIENTE" in linea:
                print(f"    {linea.strip()[:100]}")

    print("\n" + "=" * 70)
    print("COMENTARIO PARA EL ISSUE #190 — copiar tal cual")
    print("=" * 70)
    print(f"""Tarea 2 – Individual
Fuentes: Wikimedia Commons (audio, CC BY-SA 4.0) / resoluciones del CEPLAN en gob.pe
(impresos, textos oficiales sin protección por DL 822 art. 9) / capturas propias
(fotos y manuscritos, sin datos personales)
Estudiante: Alexander Noblejas (@AlexNoblejas)
Dashboard público (obligatorio): {enlace}
Carpeta del trabajo: https://github.com/AlexNoblejas/python-intermedio-qlab/tree/main/tarea_2
Resultados Test: WER: {wer:.2f} | CER: {cer:.2f} | Acuerdo LLM-Humano: {pct(acuerdo)}""")
    print("=" * 70)
    print(f"\nCorpus: {r.get('n_documentos')} documentos (3 tipos) · {r.get('n_clips')} clips · "
          f"{r.get('minutos_audio')} min")
    print(f"Modelos: OCR {r.get('modelo_ocr')} vs {r.get('segundo_ocr')} · "
          f"ASR {r.get('modelo_asr')} vs {r.get('segundo_asr')} · LLM {r.get('modelo_llm')}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
