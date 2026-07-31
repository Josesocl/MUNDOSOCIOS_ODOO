#!/usr/bin/env python3
"""Extrae los endpoints de la documentación de SimpleAPI.

Descarga documentacion.simpleapi.cl (y sus archivos JS/JSON, donde las
documentaciones tipo SPA guardan el texto), busca todas las URLs y rutas
de API que contengan, y las imprime agrupadas — en particular las de la
API RUT. No usa la API key ni consume cuota: solo lee la documentación
pública.

Uso (desde el Mac, con internet normal):
    python3 extraer_endpoints_docs.py
"""

import re
import sys
import urllib.parse
import urllib.request

BASE = "https://documentacion.simpleapi.cl"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
MAX_ASSETS = 40


def bajar(url, binario=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        datos = r.read()
    return datos if binario else datos.decode("utf-8", errors="replace")


def assets_de(html, base):
    urls = set()
    for m in re.finditer(r'(?:src|href)=["\']([^"\']+\.(?:js|json))(?:\?[^"\']*)?["\']', html):
        urls.add(urllib.parse.urljoin(base + "/", m.group(1)))
    return sorted(urls)


PATRONES = [
    re.compile(r'https?://[a-z0-9.\-]*simpleapi[a-z0-9.\-]*\.cl[^\s"\'<>\\)]*',
               re.IGNORECASE),
    re.compile(r'["\'](/(?:api|servicios)/[^\s"\'<>\\]{2,120})["\']'),
]


def rutas_en(texto):
    encontradas = set()
    for pat in PATRONES:
        for m in pat.finditer(texto):
            r = m.group(1) if pat.groups else m.group(0)
            r = r.rstrip('\\').rstrip('.,;')
            if len(r) < 200:
                encontradas.add(r)
    return encontradas


def main():
    print(f"Descargando {BASE} ...")
    try:
        html = bajar(BASE)
    except Exception as e:
        print(f"ERROR: no se pudo descargar la documentación: {e}",
              file=sys.stderr)
        return 1

    textos = [("(página principal)", html)]
    assets = assets_de(html, BASE)
    print(f"  {len(assets)} archivos JS/JSON referenciados; descargando "
          f"hasta {MAX_ASSETS}...")
    for url in assets[:MAX_ASSETS]:
        try:
            textos.append((url, bajar(url)))
        except Exception as e:
            print(f"  (no se pudo bajar {url}: {e})")

    # sitemap por si la doc es multipágina
    for extra in ("/sitemap.xml", "/sitemap-pages.xml"):
        try:
            sm = bajar(BASE + extra)
            paginas = re.findall(r"<loc>([^<]+)</loc>", sm)
            print(f"  sitemap {extra}: {len(paginas)} páginas")
            for p in paginas[:MAX_ASSETS]:
                try:
                    textos.append((p, bajar(p)))
                except Exception:
                    pass
        except Exception:
            pass

    todas = set()
    for _, t in textos:
        todas |= rutas_en(t)

    if not todas:
        print("\nNo se encontraron rutas de API en el contenido descargado.")
        print("La documentación carga el texto de otra forma; abrirla en el "
              "navegador y copiar el ejemplo de la sección 'API RUT'.")
        return 1

    con_rut = sorted(r for r in todas if "rut" in r.lower())
    resto = sorted(todas - set(con_rut))

    print("\n=== Rutas que mencionan RUT ===")
    for r in con_rut or ["(ninguna)"]:
        print(f"  {r}")
    print("\n=== Todas las demás rutas/URLs encontradas ===")
    for r in resto:
        print(f"  {r}")
    print("\nCopie TODA esta salida y péguela en el chat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
