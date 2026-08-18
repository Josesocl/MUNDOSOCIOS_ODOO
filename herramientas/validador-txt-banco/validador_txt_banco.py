#!/usr/bin/env python3
"""Validador del TXT de nómina de pagos (Banco de Chile) — MundoSocios.

Automatiza el tramo final del flujo de compras (Manual nóminas de pago):
Manager+ genera el archivo Transfer_CHILE*.txt del pago masivo y hoy hay
que (1) editarle la fecha de pago a mano en Bloc de notas y (2) rezar
para que ningún carácter especial, descripción larga o campo vacío lo
haga rebotar en el banco el día de pago (dolor #1 del diagnóstico,
PC-P1 / DP-08).

Este validador:
  - REVISA el TXT antes de cargarlo al banco: caracteres que el banco
    rechaza, líneas de más de 400 caracteres, montos en negativo
    (anticipos/NC que nunca deben ir en la nómina), estructura de
    registros inconsistente.
  - CORRIGE la fecha de pago del encabezado sin abrir Bloc de notas
    (--fecha-pago), escribiendo un archivo nuevo (el original no se toca).
  - DIAGNOSTICA la estructura (--diagnostico) con los dígitos
    enmascarados, para calibrar las validaciones con un TXT real sin
    exponer montos ni RUTs.

Uso:
    python3 validador_txt_banco.py "Transfer_CHILE$_20260818_1349.txt"
    python3 validador_txt_banco.py archivo.txt --fecha-pago 22-08-2026
    python3 validador_txt_banco.py archivo.txt --diagnostico

Códigos de salida: 0 = OK (cargar al banco) · 2 = errores (NO cargar) ·
1 = error de uso/archivo.
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Caracteres que aceptamos sin reclamar. Todo lo demás (tildes, signos
# raros) se reporta: el manual de nóminas dice que los caracteres
# especiales hacen fallar la carga en el banco.
PERMITIDOS = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    "ÑñÁÉÍÓÚáéíóúÜü .,/@-_()&'#$")
# De los permitidos-con-reserva, estos generan advertencia (no error):
# suelen venir en glosas de factura y conviene revisarlos.
DUDOSOS = set("ÁÉÍÓÚáéíóúÜü&'#$")

LARGO_MAXIMO = 400          # el manual: descripciones sobre 400 rompen la carga
RE_FECHA = re.compile(r"20\d{6}")   # AAAAMMDD


def _es_fecha(t):
    try:
        f = datetime.strptime(t, "%Y%m%d").date()
    except ValueError:
        return False
    return 2020 <= f.year <= 2035


def leer_txt(ruta):
    """Lee el TXT preservando los fines de línea. → (lineas, fin_linea,
    codificacion)."""
    crudo = Path(ruta).read_bytes()
    for cod in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            texto = crudo.decode(cod)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError("No se pudo decodificar el archivo (¿binario?)")
    fin = "\r\n" if "\r\n" in texto else "\n"
    lineas = texto.split(fin)
    if lineas and lineas[-1] == "":
        lineas.pop()
    return lineas, fin, cod


def validar(lineas):
    """→ (errores, advertencias): listas de mensajes con número de línea."""
    errores, advertencias = [], []
    if not lineas:
        return ["el archivo está vacío"], []

    for i, ln in enumerate(lineas, 1):
        if len(ln) > LARGO_MAXIMO:
            errores.append(
                f"línea {i}: {len(ln)} caracteres (máximo {LARGO_MAXIMO}) — "
                "acortar la descripción/glosa en Manager+ y regenerar")
        raros = sorted({c for c in ln if c not in PERMITIDOS})
        if raros:
            errores.append(
                f"línea {i}: caracteres que el banco puede rechazar: "
                + " ".join(repr(c) for c in raros)
                + " — corregir la glosa en Manager+ y regenerar")
        dudosos = sorted({c for c in ln if c in DUDOSOS})
        if dudosos:
            advertencias.append(
                f"línea {i}: caracteres a revisar (tildes/símbolos): "
                + " ".join(repr(c) for c in dudosos))
        if "-" in ln and RE_FECHA.search(ln) is None:
            # guiones fuera de una fecha: puede ser un monto negativo
            # (anticipo/NC, que NUNCA va en nómina) o un guión legítimo
            # de nombre/correo → a revisar.
            if re.search(r"-\d", ln):
                advertencias.append(
                    f"línea {i}: posible monto NEGATIVO (anticipo o nota de "
                    "crédito): estos documentos no van en la nómina — hacer "
                    "el ajuste de tesorería antes de emitir")

    # Consistencia de estructura: los registros del mismo tipo (misma
    # letra/dígito inicial) deberían repetir el mismo patrón de largo.
    largos = defaultdict(Counter)
    for ln in lineas:
        if ln:
            largos[ln[0]][len(ln)] += 1
    for tipo, cuenta in sorted(largos.items()):
        if len(cuenta) > 3:
            advertencias.append(
                f"registros tipo '{tipo}': {len(cuenta)} largos distintos "
                f"({min(cuenta)}–{max(cuenta)}) — revisar en el diagnóstico "
                "si es normal (glosas variables) o hay un registro cortado")
    return errores, advertencias


def fechas_encabezado(lineas):
    """Fechas AAAAMMDD detectadas en la primera línea, con posición."""
    if not lineas:
        return []
    return [(m.start(), m.group()) for m in RE_FECHA.finditer(lineas[0])
            if _es_fecha(m.group())]


def corregir_fecha(ruta, lineas, fin, cod, fecha_nueva):
    """Reemplaza la(s) fecha(s) del encabezado por fecha_nueva y escribe
    <archivo>_pago_<AAAAMMDD>.txt. → ruta nueva."""
    encontradas = fechas_encabezado(lineas)
    if not encontradas:
        raise RuntimeError(
            "no se encontró ninguna fecha AAAAMMDD en el encabezado; "
            "correr --diagnostico y calibrar")
    valores = {v for _, v in encontradas}
    if len(valores) > 1:
        raise RuntimeError(
            "el encabezado tiene varias fechas distintas "
            f"({', '.join(sorted(valores))}); correr --diagnostico para "
            "decidir cuál corresponde a la fecha de pago")
    vieja = valores.pop()
    lineas = list(lineas)
    lineas[0] = lineas[0].replace(vieja, fecha_nueva)
    origen = Path(ruta)
    destino = origen.with_name(f"{origen.stem}_pago_{fecha_nueva}.txt")
    destino.write_bytes((fin.join(lineas) + fin).encode(cod))
    return destino, vieja


def diagnostico(lineas):
    """Imprime la estructura del TXT con dígitos enmascarados (montos y
    RUTs no se exponen; las fechas sí, no son dato sensible)."""
    print(f"Líneas: {len(lineas)}")
    tipos = defaultdict(list)
    for i, ln in enumerate(lineas, 1):
        tipos[ln[0] if ln else "(vacía)"].append((i, ln))
    for tipo, items in sorted(tipos.items()):
        largos = Counter(len(ln) for _, ln in items)
        print(f"\nRegistro tipo {tipo!r}: {len(items)} líneas, "
              f"largos {dict(sorted(largos.items()))}")
        for i, ln in items[:2]:      # 2 ejemplos por tipo bastan
            fechas = [(m.start(), m.group()) for m in RE_FECHA.finditer(ln)
                      if _es_fecha(m.group())]
            forma = []
            for c in ln:
                if c.isdigit():
                    forma.append("9")
                elif c.isalpha():
                    forma.append("A" if c.isupper() else "a")
                else:
                    forma.append(c)
            print(f"  línea {i}: {''.join(forma)}")
            for pos, val in fechas:
                print(f"    fecha detectada en columna {pos}: {val}")


def normalizar_fecha(texto):
    """Acepta DD-MM-AAAA, DD/MM/AAAA o AAAAMMDD → AAAAMMDD."""
    texto = texto.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(texto, fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    raise RuntimeError(f"fecha no reconocida: {texto} (usar DD-MM-AAAA)")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Valida el TXT de nómina antes de cargarlo al banco")
    ap.add_argument("archivo", help="TXT generado por Manager+ (pago masivo)")
    ap.add_argument("--fecha-pago",
                    help="fecha de abono (DD-MM-AAAA): corrige el encabezado "
                         "y escribe un archivo nuevo")
    ap.add_argument("--diagnostico", action="store_true",
                    help="muestra la estructura (dígitos enmascarados) para "
                         "calibrar con un TXT real")
    args = ap.parse_args(argv)

    try:
        lineas, fin, cod = leer_txt(args.archivo)
    except (OSError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.diagnostico:
        diagnostico(lineas)
        return 0

    errores, advertencias = validar(lineas)
    print(f"Archivo: {args.archivo}  ({len(lineas)} líneas, codificación "
          f"{cod}, fin de línea {'CRLF' if fin == chr(13)+chr(10) else 'LF'})")

    fechas = fechas_encabezado(lineas)
    if fechas:
        print("Fecha(s) en el encabezado: "
              + ", ".join(f"{v} (col {p})" for p, v in fechas))

    for e in errores:
        print(f"  ERROR: {e}")
    for a in advertencias:
        print(f"  aviso: {a}")

    if args.fecha_pago:
        try:
            nueva = normalizar_fecha(args.fecha_pago)
            destino, vieja = corregir_fecha(args.archivo, lineas, fin, cod,
                                            nueva)
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        print(f"\nFecha de pago corregida: {vieja} → {nueva}")
        print(f"Archivo para el banco: {destino}")
        print("(el TXT original no se modificó)")

    if errores:
        print(f"\nNO CARGAR AL BANCO: {len(errores)} error(es). Corregir en "
              "Manager+ y regenerar el TXT.")
        return 2
    print("\nSin errores. "
          + ("Revisar los avisos antes de cargar." if advertencias
             else "Listo para cargar al banco."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
