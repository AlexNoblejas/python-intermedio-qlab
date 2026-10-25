"""Lee referencias_plantilla.xlsx y escribe texto_referencia en los CSV del corpus.

    python leer_referencias.py                      # usa referencias_plantilla.xlsx
    python leer_referencias.py otro_archivo.xlsx

La transcripción de referencia la hace el estudiante a mano, mirando la imagen y escuchando el
audio, sin ver la salida del OCR ni del ASR. Este script solo traslada lo escrito a
`datos/documentos.csv` y `datos/transcripciones.csv`, y avisa si falta algo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "datos"


def leer_hoja(xlsx: Path, hoja: str, col_id: str = "id") -> dict[str, str]:
    df = pd.read_excel(xlsx, sheet_name=hoja)
    df = df[~df[col_id].astype(str).str.startswith("EJEMPLO")]
    df = df.dropna(subset=["texto_referencia"])
    return {str(r[col_id]).strip(): str(r["texto_referencia"]).strip()
            for _, r in df.iterrows() if str(r["texto_referencia"]).strip()}


def aplicar(csv: Path, referencias: dict[str, str], etiqueta: str) -> None:
    if not csv.exists():
        print(f"  {csv.name} no existe todavía — corre 01_extraccion.ipynb primero")
        return
    df = pd.read_csv(csv)
    if "texto_referencia" not in df.columns:
        df["texto_referencia"] = ""
    df["texto_referencia"] = df["texto_referencia"].fillna("").astype(str)

    puestos, huerfanos = 0, []
    for cid, texto in referencias.items():
        fila = df.id == cid
        if not fila.any():
            huerfanos.append(cid)
            continue
        df.loc[fila, "texto_referencia"] = texto
        puestos += 1
    df.to_csv(csv, index=False)

    con_ref = (df.texto_referencia.str.strip() != "").sum()
    print(f"  {etiqueta}: {puestos} referencias escritas · {con_ref} filas con referencia en total")
    if huerfanos:
        print(f"    ids que no existen en {csv.name}: {', '.join(huerfanos)}")
    if con_ref < 10:
        print(f"    OJO: el enunciado pide 10 y hay {con_ref}")
    palabras = df.loc[df.texto_referencia.str.strip() != "", "texto_referencia"].str.split().str.len()
    if len(palabras):
        print(f"    longitud de las referencias: {palabras.min()}–{palabras.max()} palabras "
              f"(mediana {int(palabras.median())})")


if __name__ == "__main__":
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "referencias_plantilla.xlsx"
    if not xlsx.exists():
        sys.exit(f"No encuentro {xlsx}")
    print(f"Leyendo {xlsx.name}")
    aplicar(DATOS / "documentos.csv", leer_hoja(xlsx, "documentos"), "documentos")
    aplicar(DATOS / "transcripciones.csv", leer_hoja(xlsx, "audio"), "audio")
