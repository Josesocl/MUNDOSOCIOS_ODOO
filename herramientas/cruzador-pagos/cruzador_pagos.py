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
from datetime import date, timedelta
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
        ws = load_workbook(io.BytesIO(datos), read_only=True, data_only=True).active
        return [["" if c is None else c for c in fila] for fila in ws.iter_rows(values_only=True)]
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
    if isinstance(celda, date):
        return celda
    s = str(celda or "").strip()
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


def leer_cartola(ruta: Path):
    """Extrae los movimientos de la cartola (todas sus 'páginas')."""
    movimientos = []
    for fila in leer_tabla(ruta):
        celdas = [str(c).strip() if not isinstance(c, (int, float)) else c
                  for c in fila]
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


def leer_resumen_transbank(ruta: Path):
    """Filas del 'Resumen histórico de abonos': fecha, total abono, nº ventas."""
    abonos = []
    for fila in leer_tabla(ruta):
        celdas = list(fila) + [""] * 10
        fecha = parse_fecha(celdas[0])
        if fecha is None:
            continue
        total = parse_monto(celdas[7])
        n_ventas = parse_monto(celdas[9])
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


def clasificar(mov, resumen_transbank, socios):
    """→ (clasificacion, rut, concepto, estado, confianza, nota)."""
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
            socio, score = match_socio(m.group(1), socios)
            if socio and score >= 0.75:
                return ("TRANSFERENCIA", socio["rut"], "PROPUESTA: " + socio["nombre"],
                        "P", "alta", f"match nombre {score:.0%} — confirmar contra deuda")
            if socio and score >= 0.5:
                return ("TRANSFERENCIA", socio["rut"], "PROPUESTA: " + socio["nombre"],
                        "P", "media", f"match nombre {score:.0%} — revisar")
            return ("TRANSFERENCIA", "", "DEPOSITO POR IDENTIFICAR",
                    "P", "", f"pagador: {m.group(1)}")
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
    ap.add_argument("--salida", type=Path, default=Path("."))
    args = ap.parse_args(argv)

    movimientos = leer_cartola(args.cartola)
    if not movimientos:
        print("ERROR: no se encontraron movimientos en la cartola.", file=sys.stderr)
        return 1
    resumen = leer_resumen_transbank(args.transbank_resumen) if args.transbank_resumen else []
    socios = leer_maestro(args.maestro) if args.maestro else []

    contadores = {}
    for mov in movimientos:
        (mov["clasificacion"], mov["rut"], mov["concepto"], mov["estado"],
         mov["confianza"], mov["nota"]) = clasificar(mov, resumen, socios)
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
