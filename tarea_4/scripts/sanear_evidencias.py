"""Tapa secretos y datos personales en evidencias_ia/ antes de publicar. Falla si algo queda.

    uv run python scripts/sanear_evidencias.py
    uv run python scripts/sanear_evidencias.py --solo-revisar
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATRONES = [
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"), "[CLAVE_OCULTA]"),
    (re.compile(r"\b(?:ghp|gho|github_pat)_[A-Za-z0-9_]{16,}"), "[TOKEN_OCULTO]"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{16,}"), "Bearer [TOKEN_OCULTO]"),
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[CORREO_OCULTO]"),
]
PERMITIDOS = {"noreply@anthropic.com"}
EXTENSIONES = {".jsonl", ".json", ".md", ".txt", ".html", ".csv"}


def sanear(texto: str) -> tuple[str, int]:
    total = 0
    for patron, reemplazo in PATRONES:
        def cambiar(m: re.Match) -> str:
            nonlocal total
            if m.group(0) in PERMITIDOS:
                return m.group(0)
            total += 1
            return reemplazo
        texto = patron.sub(cambiar, texto)
    return texto, total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo-revisar", action="store_true")
    parser.add_argument("--carpeta", type=Path, default=ROOT / "evidencias_ia")
    args = parser.parse_args()
    hallazgos = 0
    for ruta in sorted(args.carpeta.rglob("*")):
        if not ruta.is_file() or ruta.suffix.lower() not in EXTENSIONES:
            continue
        original = ruta.read_text(encoding="utf-8", errors="replace")
        limpio, n = sanear(original)
        if n:
            hallazgos += n
            print(f"{ruta.relative_to(args.carpeta)}: {n} reemplazos")
            if not args.solo_revisar:
                ruta.write_text(limpio, encoding="utf-8")
    print(f"Total: {hallazgos}")
    if args.solo_revisar and hallazgos:
        raise SystemExit("Hay secretos o datos personales sin ocultar.")


if __name__ == "__main__":
    main()
