#!/usr/bin/env python3
"""Generador del devengo ANUAL de cuota social para Manager+.

Genera los dos archivos de importación (empresa y persona) con el mismo
formato de 22 columnas del importador, replicando los archivos reales
DEVENGO CUOTA SOCIAL EMPRESA/PERSONA ENE-26.xlsx:

    Empresa: DEBE 1150001 / HABER 3210002, doc CSEMP, CC contrapartida ADM
             monto = 3 UF (hasta 3 miembros) + 1 UF por miembro desde el 4º
             glosa detalle: {RUT} CE {AA} {CÁMARA}
    Persona: DEBE 1150002 / HABER 3210001, doc CSPER, CC contrapartida ADM
             monto = 1 UF
             glosa detalle: {RUT} CP {AA} {CÁMARA}

Uso:
    python3 generador_cuota_social.py --maestro maestro_socios.csv \
        --anio 2026 --uf 39731.77 --salida ./salida

Maestro (CSV ; o ,). Columnas:
    rut           RUT del socio titular
    nombre        Nombre / razón social (para reportes)
    tipo_socio    EMPRESA | PERSONA
    camara        Cámara regional (va en la glosa, ej: SANTIAGO, O'HIGGINS)
    miembros      Solo empresa: nº de miembros (vacío o <=3 => 3 UF)
    monto_clp     Opcional: monto manual que reemplaza el cálculo
                  (para prorrateos/excepciones)
"""

import argparse
import csv
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import rut_utils
from generador_devengos import ENCABEZADO, escribir_xlsx, fecha_contable

TIPOS = {
    "EMPRESA": {
        "cuenta_cxc": "1150001", "cuenta_ingreso": "3210002",
        "tipo_doc": "CSEMP", "sigla": "CE",
        "glosa_comprobante": "DEVENGO CUOTA EMPRESA",
        "archivo": "CUOTA SOCIAL EMPRESA",
    },
    "PERSONA": {
        "cuenta_cxc": "1150002", "cuenta_ingreso": "3210001",
        "tipo_doc": "CSPER", "sigla": "CP",
        "glosa_comprobante": "DEVENGO CUOTA PERSONA",
        "archivo": "CUOTA SOCIAL PERSONA",
    },
}


def unidades_uf(tipo: str, miembros) -> Decimal:
    """UF a devengar: persona 1 UF; empresa 3 UF base, +1 por miembro >3."""
    if tipo == "PERSONA":
        return Decimal(1)
    n = int(miembros) if miembros else 3
    return Decimal(max(3, n))


def leer_maestro(ruta: Path):
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
        requeridas = {"rut", "tipo_socio", "camara"}
        faltantes = requeridas - set(lector.fieldnames or [])
        if faltantes:
            return filas, [f"El maestro no tiene las columnas: {sorted(faltantes)}"]
        for n, fila in enumerate(lector, start=2):
            rut_crudo = (fila.get("rut") or "").strip()
            if not rut_crudo:
                continue
            problemas = []
            rut = None
            try:
                rut = rut_utils.normalizar(rut_crudo)
                if not rut_utils.es_valido(rut):
                    problemas.append(f"RUT {rut_crudo!r}: dígito verificador incorrecto")
            except ValueError:
                problemas.append(f"RUT {rut_crudo!r}: formato no reconocible")
            tipo = (fila.get("tipo_socio") or "").strip().upper()
            if tipo not in TIPOS:
                problemas.append(f"tipo_socio desconocido: {tipo!r} (EMPRESA/PERSONA)")
            camara = (fila.get("camara") or "").strip().upper()
            if not camara:
                problemas.append("camara vacía")
            miembros = (fila.get("miembros") or "").strip()
            if miembros and not miembros.isdigit():
                problemas.append(f"miembros no numérico: {miembros!r}")
            monto_manual = (fila.get("monto_clp") or "").strip()
            if monto_manual and not monto_manual.isdigit():
                problemas.append(f"monto_clp no numérico: {monto_manual!r}")
            if problemas:
                errores.extend(f"Línea {n}: {p}" for p in problemas)
            else:
                filas.append({"rut": rut, "nombre": (fila.get("nombre") or "").strip(),
                              "tipo": tipo, "camara": camara,
                              "miembros": miembros,
                              "monto_manual": int(monto_manual) if monto_manual else None})
    vistos = {}
    for fila in filas:
        clave = (fila["tipo"], fila["rut"])
        vistos[clave] = vistos.get(clave, 0) + 1
    for (tipo, rut), veces in sorted(vistos.items()):
        if veces > 1:
            errores.append(f"RUT {rut} aparece {veces} veces en {tipo}")
    return filas, errores


def construir_filas(socios, tipo: str, anio: int, valor_uf: Decimal):
    cfg = TIPOS[tipo]
    aa = anio % 100
    fecha = fecha_contable(1, anio)
    glosa_comp = f"{cfg['glosa_comprobante']} {anio}"
    filas, total = [], 0
    for i, s in enumerate(socios, start=1):
        if s["monto_manual"] is not None:
            monto = s["monto_manual"]
        else:
            monto = int((unidades_uf(tipo, s["miembros"]) * valor_uf)
                        .quantize(Decimal("1"), ROUND_HALF_UP))
        total += monto
        filas.append([
            "T", "", glosa_comp, fecha, "", "",
            i, "001", f"{s['rut']} {cfg['sigla']} {aa} {s['camara']}", s["rut"],
            "", cfg["cuenta_cxc"], "", monto, 0, cfg["tipo_doc"], fecha,
            "", "", "", "", "",
        ])
    filas.append([
        "T", "", glosa_comp, fecha, "", "",
        len(socios) + 1, "001", glosa_comp, "",
        "", cfg["cuenta_ingreso"], "ADM", 0, total, "", fecha,
        "", "", "", "", "",
    ])
    return filas, total


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--maestro", required=True, type=Path)
    ap.add_argument("--anio", required=True, type=int)
    ap.add_argument("--uf", required=True,
                    help="Valor UF para el devengo anual (ej: 39731.77)")
    ap.add_argument("--salida", type=Path, default=Path("."))
    args = ap.parse_args(argv)

    valor_uf = Decimal(args.uf.replace(",", "."))
    filas, errores = leer_maestro(args.maestro)
    if errores:
        print("ERRORES en el maestro — corregir antes de generar:", file=sys.stderr)
        for e in errores:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if not filas:
        print("ERROR: el maestro no tiene socios.", file=sys.stderr)
        return 1

    args.salida.mkdir(parents=True, exist_ok=True)
    for tipo, cfg in TIPOS.items():
        socios = [f for f in filas if f["tipo"] == tipo]
        if not socios:
            continue
        cuerpo, total = construir_filas(socios, tipo, args.anio, valor_uf)
        nombre = f"DEVENGO {cfg['archivo']} ENE-{args.anio % 100}.xlsx"
        escribir_xlsx(cuerpo, args.salida / nombre)
        monto = f"{total:,}".replace(",", ".")
        print(f"  {nombre}: {len(socios)} socios, total HABER ${monto}")
    print("\nCuadrar totales contra los mantenedores de cuota social antes "
          "de importar en Manager+.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
