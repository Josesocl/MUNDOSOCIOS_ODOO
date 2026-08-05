#!/usr/bin/env python3
"""Cruzador de pagos MundoSocios — genera el borrador de PRECONCILIACIÓN.

Cruza la cartola del Banco de Chile con el resumen histórico de abonos de
Transbank y el maestro de socios, y produce un Excel con la MISMA
estructura del archivo "PRECONCILIACIÓN" que hoy se arma a mano
(dolor PC-01: ~10 h/semana cruzando fuentes), con cada movimiento
clasificado y, donde es posible, identificado:

- Abonos Transbank: match automático contra el "Resumen histórico de
  abonos" (fecha + monto, tolerancia ±2 pesos y ventana ±1 día por el
  desfase crédito/débito), con el nº de ventas del día.
- "Traspaso De:": match difuso del nombre del pagador contra el maestro
  de socios → propone RUT con nivel de confianza (la cartola NUNCA trae
  RUT; esto es una propuesta a revisar, no un dato).
- Recaudación PAC: marcada "POR DISTRIBUIR" (el detalle por socio viene
  en la rendición PAC del banco, fuera de estas fuentes).
- Depósitos con cheque y resto: "POR IDENTIFICAR".
- Cargos: clasificados (proveedores, sueldos, comisiones, etc.).

Uso:
    python3 cruzador_pagos.py --cartola "CARTOLA BANCO CHILE JUNIO 26.xls" \
        --transbank-resumen "INFORME TRANSBANK Resumen_historico_abonos.xls" \
        --maestro maestro_socios.csv \
        --salida ./salida

Los .xls del Banco de Chile y de Transbank suelen ser HTML disfrazado;
este script los lee igual (HTML, xlsx o CSV). Si el archivo es un .xls
binario real, guardarlo como .xlsx desde Excel primero.

Maestro (CSV ; o ,): columnas rut, nombre  (opcional: producto, monto).
"""

import argparse
import csv
import html
import io
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "generador-devengos"))
import rut_utils

ENCABEZADO_SALIDA = [
    "Canal o Sucursal", "Nro. Docto.", "Fecha", "Descripción",
    "Cargos (CLP)", "Abonos (CLP)", "Saldo (CLP)",
    "RUT", "CONCEPTO", "MODULO", "CUENTA", "OT", "CC", "LN", "ESTADO",
    # Columnas del cruzador (no existen en la preconciliación manual):
    "CLASIFICACION", "CONFIANZA", "NOTA CRUZADOR",
]

GLOSA_TRANSBANK = re.compile(r"^Pago:\s*Abonos\s+Debito\s+Y\s+Credito\s+Transbank", re.I)
GLOSA_PAC = re.compile(r"^Pac\s+Multib", re.I)
GLOSA_TRASPASO = re.compile(r"^Traspaso\s+De:\s*(.+)$", re.I)
GLOSA_SPAV_ABONO = re.compile(r"^Transferencia\s+De\s+Otro\s+Banco", re.I)
GLOSA_DEPOSITO = re.compile(r"^(Dep\.?cheq|Deposito\s+Con\s+Cheque)", re.I)

CARGOS = [
    (re.compile(r"^(Provision|Pago):\s*Proveedores", re.I), "CARGO PROVEEDORES"),
    (re.compile(r"^Provision:\s*De\s*Sueldos", re.I), "CARGO SUELDOS"),
    (re.compile(r"^Pago\s+Instituciones\s+Previsionales", re.I), "CARGO PREVISIONALES"),
    (re.compile(r"^Pago\s+Automatico\s+Tarjeta", re.I), "CARGO TARJETA CREDITO"),
    (re.compile(r"^Pac\s+", re.I), "CARGO PAC SERVICIO"),
    (re.compile(r"^Comis", re.I), "CARGO COMISION"),
    (re.compile(r"^Transf\.?\s*A\s*Otro\s*Banco", re.I), "CARGO TRANSFERENCIA"),
]


# ---------------------------------------------------------------- lectura

class _TablasHTML(HTMLParser):
    """Extrae todas las filas de todas las tablas de un HTML plano."""

    def __init__(self):
        super().__init__()
        self.filas, self._fila, self._celda, self._en_celda = [], None, [], False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._fila = []
        elif tag in ("td", "th"):
            self._en_celda, self._celda = True, []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._fila is not None:
            self._fila.append(html.unescape("".join(self._celda)).strip())
            self._en_celda = False
        elif tag == "tr" and self._fila:
            self.filas.append(self._fila)
            self._fila = None

    def handle_data(self, data):
        if self._en_celda:
            self._celda.append(data)


def leer_tabla(ruta: Path):
    """Devuelve las filas (listas de celdas str) de un xlsx, HTML o CSV."""
    datos = ruta.read_bytes()
    if datos[:4] == b"PK\x03\x04":                     # xlsx
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(datos), read_only=True, data_only=True)
        filas = []
        for ws in wb.worksheets:                       # TODAS las hojas: los
            for fila in ws.iter_rows(values_only=True):  # archivos del equipo
                filas.append(["" if c is None else c for c in fila])
        return filas
    if datos[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":  # OLE: xls binario real
        raise SystemExit(f"{ruta.name}: es un .xls binario; guardarlo como "
                         ".xlsx desde Excel y reintentar.")
    texto = datos.decode("utf-8", errors="replace")
    if "<table" in texto.lower() or "<tr" in texto.lower():   # HTML disfrazado
        parser = _TablasHTML()
        parser.feed(texto)
        return parser.filas
    lector = csv.reader(io.StringIO(texto),
                        delimiter=";" if texto.count(";") > texto.count(",") else ",")
    return list(lector)


def parse_monto(celda):
    if celda is None:
        return 0
    if isinstance(celda, (int, float)):
        return int(round(celda))
    s = str(celda).strip().replace("$", "").replace("\xa0", "").strip()
    if not s or s in ("-", "N/A"):
        return 0
    s = re.sub(r"[.,](?=\d{3}(\D|$))", "", s)   # separadores de miles . o ,
    s = s.replace(",", ".")                     # posible decimal restante
    try:
        return int(round(float(s)))
    except ValueError:
        return 0


def parse_fecha(celda):
    if isinstance(celda, datetime):
        return celda.date()       # normalizar: date y datetime deben comparar igual
    if isinstance(celda, date):
        return celda
    s = str(celda or "").strip()
    iso = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T].*)?$", s)
    if iso:                       # celda de fecha real re-convertida a texto
        try:
            return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
    if not m:
        return None
    a, b, anio = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if a > 12:                    # 30/06/2026 → dd/mm
        dia, mes = a, b
    elif b > 12:                  # 6/30/2026 → mm/dd (celdas re-tipeadas)
        dia, mes = b, a
    else:                         # ambiguo: cartola Banco de Chile es dd/mm
        dia, mes = a, b
    try:
        return date(anio, mes, dia)
    except ValueError:
        return None


def _norm_encabezado(celda):
    import unicodedata
    t = unicodedata.normalize("NFD", str(celda or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.strip().upper()


def _mapa_columnas_cartola(fila):
    """Si la fila es el encabezado de movimientos ('Fecha … Descripción …
    Cargos …'), devuelve el índice de cada campo; si no, None.

    Necesario porque al guardar la cartola HTML como .xlsx desde Excel las
    columnas quedan corridas (columna A vacía) y con huecos por celdas
    combinadas — las posiciones fijas 0..6 dejan de valer."""
    normas = [_norm_encabezado(c) for c in fila]
    if "FECHA" not in normas:
        return None
    mapa = {}
    for i, n in enumerate(normas):
        if n == "FECHA":
            mapa.setdefault("fecha", i)
        elif n.startswith("DESCRIPCION") or n.startswith("DETALLE"):
            mapa.setdefault("descripcion", i)
        elif "CANAL" in n or "SUCURSAL" in n:
            mapa.setdefault("canal", i)
        elif "DOCTO" in n or "DOCUMENTO" in n:
            mapa.setdefault("docto", i)
        elif "CARGO" in n and "ABONO" not in n:
            # 'Cargos (CLP)' (cartola web) y 'Cheque o Cargo' (Cartola Emitida)
            mapa.setdefault("cargo", i)
        elif "ABONO" in n:
            # 'Abonos (CLP)' y 'Deposito o Abono'
            mapa.setdefault("abono", i)
        elif n.startswith("SALDO"):
            mapa.setdefault("saldo", i)
    if {"fecha", "descripcion", "cargo", "abono"} <= set(mapa):
        return mapa
    return None


def leer_cartola(ruta: Path):
    """Extrae los movimientos de la cartola (todas sus 'páginas').

    Soporta el .xls original del banco (HTML, columnas 0..6 contiguas) y
    el mismo archivo guardado como .xlsx desde Excel (columnas corridas:
    se ubican por la fila de encabezado 'Fecha/Descripción/…')."""
    movimientos, mapa = [], None
    for fila in leer_tabla(ruta):
        celdas = [str(c).strip() if not isinstance(c, (int, float, date)) else c
                  for c in fila]
        nuevo_mapa = _mapa_columnas_cartola(celdas)
        if nuevo_mapa:
            mapa = nuevo_mapa            # se repite en cada 'página'
            continue

        if mapa:
            def v(campo):
                i = mapa.get(campo)
                return celdas[i] if i is not None and i < len(celdas) else ""
            fecha = parse_fecha(v("fecha"))
            if fecha is None:
                continue
            movimientos.append({
                "fecha": fecha,
                "descripcion": str(v("descripcion")).strip(),
                "canal": str(v("canal")).strip(),
                "docto": str(v("docto")).strip(),
                "cargo": parse_monto(v("cargo")),
                "abono": parse_monto(v("abono")),
                "saldo": parse_monto(v("saldo")),
            })
            continue

        # formato original (sin encabezado detectado): posiciones fijas
        if len(celdas) < 7:
            continue
        fecha = parse_fecha(celdas[0])
        if fecha is None:                 # encabezados repetidos, pie legal…
            continue
        movimientos.append({
            "fecha": fecha,
            "descripcion": str(celdas[1]).strip(),
            "canal": str(celdas[2]).strip(),
            "docto": str(celdas[3]).strip(),
            "cargo": parse_monto(celdas[4]),
            "abono": parse_monto(celdas[5]),
            "saldo": parse_monto(celdas[6]),
        })
    return movimientos


def _mapa_columnas_transbank(fila):
    """Encabezado del 'Resumen histórico de abonos' convertido a .xlsx:
    'Fecha de abono … Total abono … N° de ventas'. Devuelve índices o None."""
    normas = [_norm_encabezado(c) for c in fila]
    mapa = {}
    for i, n in enumerate(normas):
        if n.startswith("FECHA DE ABONO"):
            mapa.setdefault("fecha", i)
        elif n == "TOTAL ABONO":
            mapa.setdefault("total", i)
        elif "VENTAS" in n and ("N°" in n or "NRO" in n or "NUM" in n):
            mapa.setdefault("n_ventas", i)
    if {"fecha", "total"} <= set(mapa):
        return mapa
    return None


def leer_resumen_transbank(ruta: Path):
    """Filas del 'Resumen histórico de abonos': fecha, total abono, nº ventas.

    Soporta el layout original (posiciones fijas 0/7/9) y el archivo
    guardado como .xlsx desde Excel (columnas corridas, ubicadas por el
    encabezado 'Fecha de abono / Total abono / N° de ventas')."""
    filas = [list(f) + [""] * 12 for f in leer_tabla(ruta)]
    # Si el archivo trae el encabezado del resumen EN CUALQUIER hoja, solo
    # valen las filas bajo ese encabezado (los archivos de trabajo del
    # equipo, ej. '07 TRANSBANK JULIO 26.xlsx', traen otras hojas con
    # fechas y montos que NO son abonos del resumen).
    con_encabezado = any(_mapa_columnas_transbank(f) for f in filas)
    abonos, mapa = [], None
    for celdas in filas:
        nuevo_mapa = _mapa_columnas_transbank(celdas)
        if nuevo_mapa:
            mapa = nuevo_mapa
            continue
        if mapa:
            fecha = parse_fecha(celdas[mapa["fecha"]])
            total = parse_monto(celdas[mapa["total"]])
            n_ventas = parse_monto(celdas[mapa["n_ventas"]]) \
                if "n_ventas" in mapa else 0
        elif not con_encabezado:
            fecha = parse_fecha(celdas[0])
            total = parse_monto(celdas[7])
            n_ventas = parse_monto(celdas[9])
        else:
            continue
        if fecha is None:
            continue
        if total > 0:
            abonos.append({"fecha": fecha, "total": total, "n_ventas": n_ventas})
    return abonos


def leer_maestro(ruta: Path):
    socios = []
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        muestra = f.read(4096)
        f.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=";,")
        except csv.Error:
            dialecto = csv.excel
        lector = csv.DictReader(f, dialect=dialecto)
        if lector.fieldnames:
            lector.fieldnames = [c.strip().lower() for c in lector.fieldnames]
        for fila in lector:
            rut, nombre = (fila.get("rut") or "").strip(), (fila.get("nombre") or "").strip()
            if not rut or not nombre:
                continue
            try:
                rut = rut_utils.normalizar(rut)
            except ValueError:
                continue
            socios.append({"rut": rut, "nombre": nombre,
                           "tokens": tokens_nombre(nombre)})
    return socios


# ------------------------------------------------------------ clasificación

def tokens_nombre(nombre: str):
    plano = "".join(c for c in unicodedata.normalize("NFD", nombre.upper())
                    if unicodedata.category(c) != "Mn")
    plano = re.sub(r"[^A-Z ]", " ", plano)
    ignorar = {"DE", "DEL", "LA", "LOS", "LAS", "Y", "E", "LTDA", "SPA", "SA",
               "EIRL", "SOCIEDAD", "EMPRESA", "COMPANIA", "COMERCIAL"}
    return {t for t in plano.split() if len(t) > 1 and t not in ignorar}


def match_socio(nombre_pagador: str, socios):
    """Mejor socio por solapamiento de tokens del nombre. → (socio, score)."""
    pagador = tokens_nombre(nombre_pagador)
    if not pagador or not socios:
        return None, 0.0
    mejor, mejor_score = None, 0.0
    for socio in socios:
        base = socio["tokens"]
        if not base:
            continue
        inter = len(pagador & base)
        score = inter / max(len(base), 1) * (0.5 + 0.5 * inter / max(len(pagador), 1))
        if score > mejor_score:
            mejor, mejor_score = socio, score
    return mejor, mejor_score


def leer_diccionario(ruta: Path):
    """CSV nombre_cartola;rut (lo genera calibrar_preconciliacion.py).
    Clave: tokens del nombre ordenados — insensible a orden y tildes."""
    dic = {}
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            nombre = (fila.get("nombre_cartola") or "").strip()
            rut = (fila.get("rut") or "").strip().upper()
            if nombre and rut:
                dic[" ".join(sorted(tokens_nombre(nombre)))] = rut
    return dic


def clasificar(mov, resumen_transbank, socios, diccionario=None):
    """→ (clasificacion, rut, concepto, estado, confianza, nota)."""
    diccionario = diccionario or {}
    d = mov["descripcion"]
    if mov["abono"] > 0:
        if GLOSA_TRANSBANK.match(d):
            m = _match_abono_transbank(mov, resumen_transbank)
            if m:
                return ("ABONO TRANSBANK", "", f"ABONO TRANSBANK ({m['n_ventas']} ventas)",
                        "listo", "alta",
                        f"cuadra con resumen Transbank {m['fecha']:%d/%m} "
                        f"(${m['total']:,})".replace(",", "."))
            return ("ABONO TRANSBANK", "", "ABONO TRANSBANK SIN CUADRE",
                    "P", "baja", "no cuadra con el resumen Transbank (±2 pesos, ±1 día)")
        if GLOSA_PAC.match(d):
            return ("RECAUDACION PAC", "", "RECAUDACION PAC POR DISTRIBUIR",
                    "P", "alta", "distribuir con la rendición PAC del banco")
        m = GLOSA_TRASPASO.match(d)
        if m:
            pagador = m.group(1)
            # 1º el diccionario histórico (pares pagador→RUT que el equipo ya
            # resolvió en preconciliaciones anteriores). Es la única fuente
            # que acierta cuando paga un tercero (persona por una empresa).
            rut_hist = diccionario.get(" ".join(sorted(tokens_nombre(pagador))))
            if rut_hist:
                return ("TRANSFERENCIA", rut_hist, "HISTORICO: mismo pagador",
                        "P", "alta", "identificado por preconciliaciones anteriores")
            # 2º match difuso contra el maestro — SOLO como pista conservadora:
            # calibración junio-26: proponer con umbral bajo produjo 26
            # propuestas erróneas (pagos de terceros). Nunca 'alta'.
            socio, score = match_socio(pagador, socios)
            if socio and score >= 0.75 and \
                    len(tokens_nombre(pagador) & socio["tokens"]) >= 3:
                return ("TRANSFERENCIA", socio["rut"], "PROPUESTA: " + socio["nombre"],
                        "P", "media", f"match nombre {score:.0%} — confirmar contra deuda")
            return ("TRANSFERENCIA", "", "DEPOSITO POR IDENTIFICAR",
                    "P", "", f"pagador: {pagador}")
        if GLOSA_SPAV_ABONO.match(d):
            return ("TRANSFERENCIA SPAV", "", "ABONO POR IDENTIFICAR", "P", "", "")
        if GLOSA_DEPOSITO.match(d):
            return ("DEPOSITO CHEQUE", "", "DEPOSITO POR IDENTIFICAR",
                    "P", "", f"docto {mov['docto']} suc. {mov['canal']}")
        return ("ABONO OTRO", "", "POR IDENTIFICAR", "P", "", "")
    for patron, etiqueta in CARGOS:
        if patron.match(d):
            return (etiqueta, "", "", "listo", "alta", "")
    return ("CARGO OTRO", "", "", "P", "", "")


def _match_abono_transbank(mov, resumen):
    candidatos = [r for r in resumen
                  if abs((r["fecha"] - mov["fecha"]).days) <= 1
                  and abs(r["total"] - mov["abono"]) <= 2]
    if not candidatos:
        return None
    return min(candidatos, key=lambda r: (abs((r["fecha"] - mov["fecha"]).days),
                                          abs(r["total"] - mov["abono"])))


# ----------------------------------------------------------------- salida

def escribir_borrador(movimientos, ruta: Path):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "PRECONCILIACION BORRADOR"
    ws.append(ENCABEZADO_SALIDA)
    for m in movimientos:
        ws.append([
            m["canal"], m["docto"], m["fecha"], m["descripcion"],
            m["cargo"] or "", m["abono"] or "", m["saldo"],
            m["rut"], m["concepto"], "", "", "", "", "", m["estado"],
            m["clasificacion"], m["confianza"], m["nota"],
        ])
        ws.cell(row=ws.max_row, column=3).number_format = "DD/MM/YYYY"
    wb.save(ruta)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cartola", required=True, type=Path)
    ap.add_argument("--transbank-resumen", type=Path, default=None,
                    help="Informe Transbank 'Resumen histórico de abonos'")
    ap.add_argument("--maestro", type=Path, default=None,
                    help="CSV rut,nombre para identificar transferencias")
    ap.add_argument("--diccionario", type=Path, default=None,
                    help="CSV nombre_cartola;rut aprendido de preconciliaciones "
                         "anteriores (lo genera calibrar_preconciliacion.py)")
    ap.add_argument("--salida", type=Path, default=Path("."))
    args = ap.parse_args(argv)

    movimientos = leer_cartola(args.cartola)
    if not movimientos:
        print("ERROR: no se encontraron movimientos en la cartola.", file=sys.stderr)
        return 1
    resumen = leer_resumen_transbank(args.transbank_resumen) if args.transbank_resumen else []
    socios = leer_maestro(args.maestro) if args.maestro else []
    diccionario = leer_diccionario(args.diccionario) if args.diccionario else {}
    if diccionario:
        print(f"Diccionario histórico: {len(diccionario)} pagadores conocidos")

    contadores = {}
    for mov in movimientos:
        (mov["clasificacion"], mov["rut"], mov["concepto"], mov["estado"],
         mov["confianza"], mov["nota"]) = clasificar(mov, resumen, socios,
                                                     diccionario)
        contadores[mov["clasificacion"]] = contadores.get(mov["clasificacion"], 0) + 1

    args.salida.mkdir(parents=True, exist_ok=True)
    salida = args.salida / "PRECONCILIACION_BORRADOR.xlsx"
    escribir_borrador(movimientos, salida)

    total_abonos = sum(m["abono"] for m in movimientos)
    total_cargos = sum(m["cargo"] for m in movimientos)
    identificados = sum(1 for m in movimientos if m["rut"] or m["estado"] == "listo")
    print(f"{len(movimientos)} movimientos — abonos ${total_abonos:,} / "
          f"cargos ${total_cargos:,}".replace(",", "."))
    for clas, n in sorted(contadores.items(), key=lambda kv: -kv[1]):
        print(f"  {clas}: {n}")
    print(f"Clasificados/propuestos: {identificados}/{len(movimientos)} "
          f"({identificados / len(movimientos):.0%})")
    print(f"Borrador: {salida}")
    print("\nLas propuestas de RUT por nombre son PROPUESTAS: confirmar "
          "contra la deuda del socio antes de rebajar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
