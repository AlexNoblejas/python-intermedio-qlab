"""Verifica los respaldos incluidos. No usa la red, no escribe ni entrena."""
from pathlib import Path
import csv
import hashlib
import xml.etree.ElementTree as ET


def nombre_local(tag):
    return tag.rsplit('}', 1)[-1]


def urls_articulos(xml):
    """Solo <url>/<loc> directo: nunca confunde <image:loc> con el artículo."""
    raiz = ET.fromstring(xml)
    return {
        hijo.text.strip()
        for nodo in raiz
        if nombre_local(nodo.tag) == 'url'
        for hijo in nodo
        if nombre_local(hijo.tag) == 'loc' and hijo.text
    }


def main():
    base = Path(__file__).resolve().parent
    evidencia = base / 'datos/evidencia_recoleccion'
    with (base / 'datos/noticias.csv').open(encoding='utf8', newline='') as archivo:
        noticias = list(csv.DictReader(archivo))
    conocidas = {fila['url'] for fila in noticias if fila['medio'] == 'La Republica'}
    with (evidencia / 'resumen_sitemaps_lr.csv').open(encoding='utf8', newline='') as archivo:
        resumen = list(csv.DictReader(archivo))
    todas = set()
    for fila in resumen:
        respaldo = evidencia / fila['respaldo']
        contenido = respaldo.read_bytes()
        assert hashlib.sha256(contenido).hexdigest() == fila['sha256_respaldo'], respaldo.name
        urls = urls_articulos(contenido)
        assert len(urls) == int(fila['urls_articulos']), respaldo.name
        assert len(urls - conocidas) == int(fila['adicionales']), respaldo.name
        todas.update(urls)
        print(f"{respaldo.name}: {len(urls)} artículos, {len(urls - conocidas)} adicionales")
    assert todas == conocidas
    assert len(todas) == 59
    # Comprobación mínima de la corrección del lector XML.
    ejemplo = '<urlset xmlns:image="urn:image"><url><loc>https://diario/nota</loc><image:image><image:loc>https://diario/foto.jpg</image:loc></image:image></url></urlset>'
    assert urls_articulos(ejemplo) == {'https://diario/nota'}
    print('Verificado: 59 artículos únicos; los ocho sitemaps no añaden noticias al CSV.')
    print('Esta evidencia corresponde a los canales y la descarga respaldados, no a todos los canales posibles.')


if __name__ == '__main__':
    main()
