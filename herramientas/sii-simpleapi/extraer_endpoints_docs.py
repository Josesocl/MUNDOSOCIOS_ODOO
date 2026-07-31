#!/usr/bin/env python3
"""Extrae los endpoints de la documentación de SimpleAPI (v2).

La documentación (documentacion.simpleapi.cl) es una colección de
Postman publicada. Este script descarga el JSON completo de la
colección y lista todos los requests: nombre, método y URL — con
detalle extra (headers, body) para los que mencionan RUT.

También guarda la colección completa en `docs_simpleapi_collection.json`
por si hace falta revisarla después.

No usa la API key ni consume cuota: solo lee documentación pública.

Uso (desde el Mac, con internet normal):
    python3 extraer_endpoints_docs.py
"""

import html
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://documentacion.simpleapi.cl"
# Enlace descubierto en la página principal (fallback si cambia: se
# vuelve a buscar dinámicamente).
COLECCION_FALLBACK = ("/api/collections/13819912/UVJk9smg"
                      "?environment=13819912-e04c1727-3153-4a7b-9d0a-bb085d8ad8d9"
                      "&segregateAuth=true&versionTag=latest")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SALIDA_JSON = Path(__file__).with_name("docs_simpleapi_collection.json")


def bajar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def url_coleccion():
    try:
        pagina = html.unescape(bajar(BASE))
        m = re.search(r'(/api/collections/[^\s"\'<>]+)', pagina)
        if m:
            return BASE + m.group(1)
    except Exception:
        pass
    return BASE + COLECCION_FALLBACK


def _url_de(request):
    u = request.get("url")
    if isinstance(u, str):
        return u
    if isinstance(u, dict):
        return u.get("raw") or "/".join(u.get("path", []))
    return "(sin url)"


def caminar(items, ruta, encontrados):
    for it in items or []:
        nombre = it.get("name", "(sin nombre)")
        if "item" in it:                      # carpeta
            caminar(it["item"], ruta + [nombre], encontrados)
        elif "request" in it:
            req = it["request"] or {}
            encontrados.append({
                "carpeta": " > ".join(ruta),
                "nombre": nombre,
                "metodo": req.get("method", "?"),
                "url": _url_de(req),
                "headers": [f"{h.get('key')}: {h.get('value')}"
                            for h in req.get("header", []) or []],
                "body": (req.get("body") or {}).get("raw", "")[:400],
            })


def main():
    url = url_coleccion()
    print(f"Descargando la colección: {url}")
    try:
        crudo = bajar(url)
        datos = json.loads(crudo)
    except Exception as e:
        print(f"ERROR: no se pudo descargar/parsear la colección: {e}",
              file=sys.stderr)
        return 1

    SALIDA_JSON.write_text(crudo)
    print(f"Colección guardada en {SALIDA_JSON.name}")

    col = datos.get("collection", datos)
    info = col.get("info", {})
    print(f"Colección: {info.get('name', '(sin nombre)')}\n")

    encontrados = []
    caminar(col.get("item"), [], encontrados)
    if not encontrados:
        print("No se encontraron requests en la colección; enviar el "
              f"archivo {SALIDA_JSON.name} al chat.")
        return 1

    con_rut = [e for e in encontrados
               if "rut" in (e["carpeta"] + e["nombre"] + e["url"]).lower()]

    print(f"=== {len(encontrados)} endpoints en total ===")
    for e in encontrados:
        print(f"  [{e['metodo']:6s}] {e['carpeta']} > {e['nombre']}")
        print(f"           {e['url']}")

    print(f"\n=== Detalle de los que mencionan RUT ({len(con_rut)}) ===")
    for e in con_rut:
        print(f"\n  {e['carpeta']} > {e['nombre']}")
        print(f"  {e['metodo']} {e['url']}")
        for h in e["headers"]:
            print(f"    header {h}")
        if e["body"]:
            print(f"    body: {e['body']}")

    print("\nCopie TODA esta salida y péguela en el chat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
