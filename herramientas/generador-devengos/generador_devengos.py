#!/usr/bin/env python3
"""Generador de archivos de devengo mensual de seguros para Manager+.

Reemplaza el proceso manual de copiar los 4 Excel del mes anterior
(dolor PC-06 del Blueprint de Recaudación): a partir de un maestro único
de pólizas (CSV) genera los archivos de importación de 22 columnas
(Manager+ > Mantenedores > Importador de datos > Comprobantes contables
con documentos > Excel, con encabezado), uno por seguro, y valida ANTES
de importar todo lo que hoy rebota en Manager+ ("Cliente no existe",
RUT mal digitado, K minúscula, montos en cero).

Uso típico:
    python3 generador_devengos.py --maestro maestro_polizas.csv \
        --periodo 07-2026 --uf 39486.29 --clientes clientes_manager.csv \
        --salida ./salida

Maestro (CSV, separador ; o , — se detecta solo). Columnas:
    rut          RUT del socio titular (con o sin puntos; K en cualquier caja)
    nombre       Nombre del socio (solo para el reporte de validación)
    seguro       PLAN SOCIOS | COMPLEMENTARIO | CATASTROFICO | PLAN CARRENO
    factor_uf    Factor UF mensual de la póliza (ej: 3,55)
    medio_pago   (opcional) PAC | PAT | DIRECTA | EMPRESA — informativo

--clientes: CSV con una columna de RUTs existentes en Manager+
(exportador de datos > Clientes y/o proveedores). Si se entrega, el
generador avisa qué socios habría que crear antes de importar.

Formato de salida (según MANUAL CARGA DE DEVENGOS, columnas A–V):
    A Tipo de comprobante = T          B Esquema = (vacío)
    C Glosa comprobante = DEVENGO {SEGURO} {PERIODO}
    D Fecha contable = 01-MM-AAAA      E/F Totales = (vacío)
    G Ítem detalle = correlativo       H Unidad de negocio = 001
    I Glosa detalle = {RUT} {SEG} {PERIODO}
    J RUT cliente (K MAYÚSCULA)        K RUT personal = (vacío)
    L Cuenta contable por cobrar       M Centro de costos = MS (solo última fila)
    N Monto debe = factor_uf × UF      O Monto haber = 0 (última fila: total)
    P Tipo de documento (PSOC/SCOMP/SCAT/PCARR; vacío en la contrapartida)
    Q Fecha de documento = 01-MM-AAAA  R NumDocumento = (vacío)
    S–V Conceptos = (vacío)
Última fila = contrapartida: cuenta de ingreso del seguro, CC MS y el
total del período en HABER.
"""

import argparse
import csv
import sys
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import rut_utils

ENCABEZADO = [
    "Tipo de comprobante", "Esquema", "Glosa comprobante", "Fecha contable",
    "Total debe", "Total haber", "Item detalle comprobante",
    "Código unidad de negocio", "Glosa detalle", "RUT cliente",
    "RUT personal", "Código cuenta contable", "Código centro costos",
    "Monto debe", "Monto haber", "Tipo de documento", "Fecha de documento",
    "NumDocumento", "Concepto 1", "Concepto 2", "Concepto 3", "Concepto 4",
]

# Cuentas y glosas por seguro (fuente: MANUAL CARGA DE DEVENGOS + handoff).
# glosa_comprobante y glosa_detalle son texto libre en Manager+: ajustables.
SEGUROS = {
    "PLAN SOCIOS": {
        "cuenta_cxc": "1130004", "cuenta_ingreso": "3310005",
        "tipo_doc": "PSOC", "glosa_comprobante": "P SOCIOS",
        "glosa_detalle": "P SOC", "archivo": "PLAN SOCIOS",
    },
    "COMPLEMENTARIO": {
        "cuenta_cxc": "1130003", "cuenta_ingreso": "3310003",
        "tipo_doc": "SCOMP", "glosa_comprobante": "COMPLEMENTARIO",
        "glosa_detalle": "COMP", "archivo": "COMPLEMENTARIO",
    },
    "CATASTROFICO": {
        "cuenta_cxc": "1130002", "cuenta_ingreso": "3310001",
        "tipo_doc": "SCAT", "glosa_comprobante": "CATASTROFICO",
        "glosa_detalle": "CAT", "archivo": "CATASTROFICO",
    },
    "PLAN CARRENO": {
        "cuenta_cxc": "1130005", "cuenta_ingreso": "3310004",
        "tipo_doc": "PCARR", "glosa_comprobante": "P CARREÑO",
        "glosa_detalle": "P CARR", "archivo": "PLAN CARREÑO",
    },
}

MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
         "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

MEDIOS_PAGO = {"PAC", "PAT", "DIRECTA", "EMPRESA"}


def _sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def normalizar_seguro(valor: str) -> str:
    """Mapea variantes de nombre de seguro a la clave canónica de SEGUROS."""
    v = _sin_acentos(valor.strip().upper()).replace("_", " ")
    v = " ".join(v.split())
    alias = {
        "PLAN SOCIOS": "PLAN SOCIOS", "P SOCIOS": "PLAN SOCIOS",
        "PSOC": "PLAN SOCIOS", "SOCIOS": "PLAN SOCIOS",
        "COMPLEMENTARIO": "COMPLEMENTARIO", "S COMPLEMENTARIO": "COMPLEMENTARIO",
        "SEGURO COMPLEMENTARIO": "COMPLEMENTARIO", "SCOMP": "COMPLEMENTARIO",
        "CATASTROFICO": "CATASTROFICO", "S CATASTROFICO": "CATASTROFICO",
        "SEGURO CATASTROFICO": "CATASTROFICO", "SCAT": "CATASTROFICO",
        "PLAN CARRENO": "PLAN CARRENO", "P CARRENO": "PLAN CARRENO",
        "CARRENO": "PLAN CARRENO", "PCARR": "PLAN CARRENO",
    }
    if v not in alias:
        raise ValueError(f"Seguro desconocido: {valor!r}")
    return alias[v]


def parse_periodo(periodo: str):
    """'07-2026' -> (7, 2026). Acepta también '2026-07' y '07/2026'."""
    p = periodo.strip().replace("/", "-")
    partes = p.split("-")
    if len(partes) != 2:
        raise ValueError(f"Período inválido: {periodo!r} (use MM-AAAA)")
    a, b = partes
    if len(a) == 4:
        anio, mes = int(a), int(b)
    else:
        mes, anio = int(a), int(b)
    if not (1 <= mes <= 12 and 2000 <= anio <= 2100):
        raise ValueError(f"Período fuera de rango: {periodo!r}")
    return mes, anio


def etiqueta_periodo(mes: int, anio: int) -> str:
    """(7, 2026) -> 'JUL 26' (formato de las glosas del cliente)."""
    return f"{MESES[mes - 1]} {anio % 100:02d}"


def fecha_contable(mes: int, anio: int) -> str:
    """Primer día del mes, formato dd-mm-aaaa como texto (igual al manual)."""
    return f"01-{mes:02d}-{anio}"


def monto_clp(factor_uf: Decimal, valor_uf: Decimal) -> int:
    """Prima mensual en pesos: factor UF × valor UF, redondeado al peso."""
    return int((factor_uf * valor_uf).quantize(Decimal("1"), ROUND_HALF_UP))


def leer_maestro(ruta: Path):
    """Lee el maestro CSV. Devuelve (filas, errores).

    Cada fila válida: dict con rut, nombre, seguro (canónico), factor_uf,
    medio_pago. Los errores refieren número de línea del archivo.
    """
    filas, errores = [], []
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
        requeridas = {"rut", "seguro", "factor_uf"}
        faltantes = requeridas - set(lector.fieldnames or [])
        if faltantes:
            errores.append(f"El maestro no tiene las columnas: {sorted(faltantes)}")
            return filas, errores
        for n, fila in enumerate(lector, start=2):
            rut_crudo = (fila.get("rut") or "").strip()
            nombre = (fila.get("nombre") or "").strip()
            if not rut_crudo and not nombre and not (fila.get("seguro") or "").strip():
                continue  # línea vacía
            problemas = []
            rut = None
            try:
                rut = rut_utils.normalizar(rut_crudo)
                if not rut_utils.es_valido(rut):
                    problemas.append(f"RUT {rut_crudo!r}: dígito verificador incorrecto")
            except ValueError:
                problemas.append(f"RUT {rut_crudo!r}: formato no reconocible")
            seguro = None
            try:
                seguro = normalizar_seguro(fila.get("seguro") or "")
            except ValueError as e:
                problemas.append(str(e))
            factor = None
            crudo_factor = (fila.get("factor_uf") or "").strip().replace(",", ".")
            try:
                factor = Decimal(crudo_factor)
                if factor <= 0:
                    problemas.append(f"factor_uf debe ser > 0 (viene {crudo_factor!r})")
            except Exception:
                problemas.append(f"factor_uf no numérico: {crudo_factor!r}")
            medio = (fila.get("medio_pago") or "").strip().upper()
            if medio and medio not in MEDIOS_PAGO:
                problemas.append(f"medio_pago desconocido: {medio!r}")
            if problemas:
                errores.extend(f"Línea {n}: {p}" for p in problemas)
            else:
                filas.append({"rut": rut, "nombre": nombre, "seguro": seguro,
                              "factor_uf": factor, "medio_pago": medio})
    # Duplicados: mismo RUT dos veces en el mismo seguro
    vistos = {}
    for fila in filas:
        clave = (fila["seguro"], fila["rut"])
        vistos[clave] = vistos.get(clave, 0) + 1
    for (seguro, rut), veces in sorted(vistos.items()):
        if veces > 1:
            errores.append(f"RUT {rut} aparece {veces} veces en {seguro}")
    return filas, errores


def leer_clientes(ruta: Path) -> set:
    """Lee el export de clientes de Manager+ y devuelve el set de RUTs."""
    ruts = set()
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        muestra = f.read(4096)
        f.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=";,")
        except csv.Error:
            dialecto = csv.excel
        for fila in csv.reader(f, dialect=dialecto):
            for celda in fila:
                try:
                    rut = rut_utils.normalizar(celda)
                except ValueError:
                    continue
                if rut_utils.es_valido(rut):
                    ruts.add(rut)
    return ruts


def construir_filas(polizas, seguro: str, mes: int, anio: int, valor_uf: Decimal):
    """Arma las filas (listas de 22 celdas) del archivo de un seguro."""
    cfg = SEGUROS[seguro]
    per = etiqueta_periodo(mes, anio)
    fecha = fecha_contable(mes, anio)
    glosa_comp = f"DEVENGO {cfg['glosa_comprobante']} {per}"
    filas, total = [], 0
    for i, p in enumerate(polizas, start=1):
        monto = monto_clp(p["factor_uf"], valor_uf)
        total += monto
        filas.append([
            "T", "", glosa_comp, fecha, "", "",
            i, "001", f"{p['rut']} {cfg['glosa_detalle']} {per}", p["rut"],
            "", cfg["cuenta_cxc"], "", monto, 0, cfg["tipo_doc"], fecha,
            "", "", "", "", "",
        ])
    # Contrapartida: cuenta de ingreso, CC MS, total en HABER, sin tipo doc.
    filas.append([
        "T", "", glosa_comp, fecha, "", "",
        len(polizas) + 1, "001", glosa_comp, "",
        "", cfg["cuenta_ingreso"], "MS", 0, total, "", fecha,
        "", "", "", "", "",
    ])
    return filas, total


def escribir_xlsx(filas, ruta: Path):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(ENCABEZADO)
    for fila in filas:
        ws.append(fila)
    wb.save(ruta)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--maestro", required=True, type=Path,
                    help="CSV maestro de pólizas (rut,nombre,seguro,factor_uf[,medio_pago])")
    ap.add_argument("--periodo", required=True,
                    help="Período a devengar, MM-AAAA (ej: 07-2026)")
    ap.add_argument("--uf", required=True,
                    help="Valor UF del día en CLP (ej: 39486.29)")
    ap.add_argument("--clientes", type=Path, default=None,
                    help="CSV con RUTs existentes en Manager+ (export de clientes)")
    ap.add_argument("--salida", type=Path, default=Path("."),
                    help="Carpeta de salida (default: actual)")
    args = ap.parse_args(argv)

    mes, anio = parse_periodo(args.periodo)
    valor_uf = Decimal(args.uf.replace(",", "."))
    if not (Decimal("10000") < valor_uf < Decimal("200000")):
        print(f"ERROR: valor UF fuera de rango plausible: {valor_uf}", file=sys.stderr)
        return 2

    filas, errores = leer_maestro(args.maestro)
    if errores:
        print("ERRORES en el maestro — corregir antes de generar:", file=sys.stderr)
        for e in errores:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if not filas:
        print("ERROR: el maestro no tiene pólizas.", file=sys.stderr)
        return 1

    avisos = []
    if args.clientes:
        existentes = leer_clientes(args.clientes)
        faltan = sorted({f["rut"] for f in filas} - existentes)
        if faltan:
            avisos.append(
                f"{len(faltan)} RUT(s) no existen como cliente en Manager+ "
                f"(crear ANTES de importar, ver Manual Creación de Clientes):")
            avisos.extend(f"  - {r}" for r in faltan)

    args.salida.mkdir(parents=True, exist_ok=True)
    per_archivo = etiqueta_periodo(mes, anio).replace(" ", "-")
    resumen = []
    for seguro in SEGUROS:
        polizas = [f for f in filas if f["seguro"] == seguro]
        if not polizas:
            continue
        cuerpo, total = construir_filas(polizas, seguro, mes, anio, valor_uf)
        nombre = f"DEVENGO {SEGUROS[seguro]['archivo']} {per_archivo}.xlsx"
        escribir_xlsx(cuerpo, args.salida / nombre)
        resumen.append((nombre, len(polizas), total))

    print(f"Período {etiqueta_periodo(mes, anio)} — UF {valor_uf} CLP")
    for nombre, n, total in resumen:
        monto = f"{total:,}".replace(",", ".")
        unidad = "póliza" if n == 1 else "pólizas"
        print(f"  {nombre}: {n} {unidad}, total HABER ${monto}")
    if avisos:
        print("\nAVISOS:")
        for a in avisos:
            print(f"  {a}")
    print("\nRevisar totales contra el mantenedor y luego importar en "
          "Manager+ > Mantenedores > Importador de datos > Comprobantes "
          "contables con documentos (con encabezado).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
