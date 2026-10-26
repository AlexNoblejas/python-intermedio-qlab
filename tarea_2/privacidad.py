"""Protección de textos del corpus. El mapa de identidades es privado y no se publica."""
import json
import re
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def _reglas():
    ruta = Path(__file__).resolve().parent / ".privado" / "seudonimos.json"
    if not ruta.exists():
        raise RuntimeError("Falta el mapa privado de seudónimos. Los resultados públicos ya están protegidos; para reprocesar originales se requiere el mapa local y revisión humana.")
    return json.loads(ruta.read_text(encoding="utf-8"))["reglas"]

def seudonimizar_texto(texto):
    texto = str(texto)
    urls = []
    def conservar(match):
        urls.append(match[0])
        return f"ZZURLPROTEGIDA{len(urls)-1}ZZ"
    texto = re.sub(r'https?://[^\s<>"\)]+', conservar, texto)
    for patron, reemplazo in _reglas():
        texto = re.sub(patron, reemplazo, texto, flags=re.I)
    texto = re.sub(r'\[PERSONA_(\d+)\](?:\s+\[PERSONA_\1\])+', r'[PERSONA_\1]', texto)
    texto = re.sub(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', '[CORREO]', texto, flags=re.I)
    texto = re.sub(r'(?i)\b(?:DNI|celular|tel[eé]fono)\s*[:#-]?\s*\d[\d .-]{6,}\d', '[IDENTIFICADOR]', texto)
    for i, url in enumerate(urls):
        texto = texto.replace(f"ZZURLPROTEGIDA{i}ZZ", url)
    return texto

def seudonimizar_estructura(valor):
    if isinstance(valor, str):
        return seudonimizar_texto(valor)
    if isinstance(valor, list):
        return [seudonimizar_estructura(v) for v in valor]
    if isinstance(valor, dict):
        return {k: seudonimizar_estructura(v) for k, v in valor.items()}
    return valor
