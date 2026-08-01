#!/usr/bin/env python3
"""Calibración del cruzador (B-01): borrador vs preconciliación real.

Compara el PRECONCILIACION_BORRADOR.xlsx generado por cruzador_pagos.py
contra la preconciliación que el equipo MS concilió a mano (ej:
"06 PRECONCILIACIÓN JUNIO 26.xlsx") y mide:

  - cuántos RUT propuestos por el cruzador coinciden con el asignado a mano,
  - cuáles propuso mal (falsos positivos: los importantes),
  - cuántos no propuso pero el equipo sí identificó (aprendibles),
  - cuadratura de los abonos Transbank y PAC.

Además exporta el diccionario nombre→RUT aprendido de la conciliación
real (`diccionario_nombre_rut.csv`) para mejorar el match de los meses
siguientes.

Uso:
    python3 calibrar_preconciliacion.py \
        --real "…/06 PRECONCILIACIÓN JUNIO 26.xlsx" \
        --borrador salida-junio/PRECONCILIACION_BORRADOR.xlsx \
        --salida salida-junio
"""

import argparse
import csv
import re
import sys
from pathlib import Path

from cruzador_pagos import (GLOSA_PAC, GLOSA_TRANSBANK, GLOSA_TRASPASO,
                            _norm_encabezado, leer_tabla, parse_fecha,
                            parse_monto)

RUT_EN_TEXTO = re.compile(r"\b(\d{1,2}\.?\d{3}\.?\d{3}-[\dkK])\b|\b(\d{6,8}-[\dkK])\b")


def _norm_rut(texto):
    t = str(texto or "").replace(".", "").replace(" ", "").strip().upper()
    return t if re.fullmatch(r"\d{1,8}-[\dK]", t) else ""


def _ruts_en_celda(texto):
    """Una celda RUT de la preconciliación real puede traer 1 o varios RUT."""
    encontrados = []
    for m in RUT_EN_TEXTO.finditer(str(texto or "")):
        r = _norm_rut(m.group(0))
        if r:
            encontrados.append(r)
    return encontrados


def leer_preconciliacion(ruta):
    """Filas con fecha/descripcion/abono/cargo/rut/concepto, mapeando las
    columnas por encabezado (tolera columnas corridas y celdas combinadas)."""
    mapa, filas = None, []
    for fila in leer_tabla(ruta):
        celdas = list(fila) + [""] * 20
        normas = [_norm_encabezado(c) for c in celdas]
        if "FECHA" in normas and any(n.startswith("DESCRIPCION") for n in normas):
            mapa = {}
            for i, n in enumerate(normas):
                if n == "FECHA":
                    mapa.setdefault("fecha", i)
                elif n.startswith("DESCRIPCION"):
                    mapa.setdefault("descripcion", i)
                elif n.startswith("CARGO"):
                    mapa.setdefault("cargo", i)
                elif n.startswith("ABONO"):
                    mapa.setdefault("abono", i)
                elif n == "RUT":
                    mapa.setdefault("rut", i)
                elif n.startswith("CONCEPTO"):
                    mapa.setdefault("concepto", i)
                elif n.startswith("CLASIFICACION"):
                    mapa.setdefault("clasificacion", i)
                elif n.startswith("CONFIANZA"):
                    mapa.setdefault("confianza", i)
            continue
        if not mapa:
            continue
        fecha = parse_fecha(celdas[mapa["fecha"]])
        if fecha is None:
            continue
        filas.append({
            "fecha": fecha,
            "descripcion": str(celdas[mapa["descripcion"]] or "").strip(),
            "cargo": parse_monto(celdas[mapa.get("cargo")]) if "cargo" in mapa else 0,
            "abono": parse_monto(celdas[mapa.get("abono")]) if "abono" in mapa else 0,
            "rut_celda": celdas[mapa["rut"]] if "rut" in mapa else "",
            "ruts": _ruts_en_celda(celdas[mapa["rut"]]) if "rut" in mapa else [],
            "concepto": str(celdas[mapa.get("concepto", 0)] or "").strip()
            if "concepto" in mapa else "",
            "clasificacion": str(celdas[mapa.get("clasificacion", 0)] or "").strip()
            if "clasificacion" in mapa else "",
            "confianza": str(celdas[mapa.get("confianza", 0)] or "").strip()
            if "confianza" in mapa else "",
        })
    if not filas:
        print(f"AVISO: no se reconoció el encabezado de {Path(ruta).name}. "
              "Primeras filas para diagnóstico:")
        for i, fila in enumerate(leer_tabla(ruta)):
            print(f"  {i}: {[str(c)[:20] for c in list(fila)[:12]]}")
            if i > 20:
                break
    return filas


def emparejar(reales, borrador):
    """Match por (fecha, abono, cargo); ante duplicados usa la descripción."""
    libres = list(range(len(reales)))
    pares, sin_par = [], []
    for b in borrador:
        candidatos = [i for i in libres
                      if reales[i]["fecha"] == b["fecha"]
                      and reales[i]["abono"] == b["abono"]
                      and reales[i]["cargo"] == b["cargo"]]
        if len(candidatos) > 1:
            mejor = [i for i in candidatos
                     if reales[i]["descripcion"][:25].upper()
                     == b["descripcion"][:25].upper()]
            candidatos = mejor or candidatos
        if candidatos:
            i = candidatos[0]
            libres.remove(i)
            pares.append((reales[i], b))
        else:
            sin_par.append(b)
    return pares, sin_par


def main(argv=None):
    ap = argparse.ArgumentParser(description="Calibración borrador vs real (B-01)")
    ap.add_argument("--real", type=Path, required=True)
    ap.add_argument("--borrador", type=Path, required=True)
    ap.add_argument("--salida", type=Path, default=Path("."))
    args = ap.parse_args(argv)

    reales = leer_preconciliacion(args.real)
    borrador = leer_preconciliacion(args.borrador)
    if not reales or not borrador:
        print("ERROR: no se pudieron leer los archivos.", file=sys.stderr)
        return 1
    print(f"Real: {len(reales)} filas · Borrador: {len(borrador)} filas")

    pares, sin_par = emparejar(reales, borrador)
    print(f"Emparejadas por fecha+monto: {len(pares)} · sin par: {len(sin_par)}")

    # --- calibración de transferencias (el corazón del match) ---
    aciertos, errores, no_propuso, multi, sin_rut_real = [], [], [], [], []
    for real, b in pares:
        if not GLOSA_TRASPASO.match(b["descripcion"]):
            continue
        propuesto = _norm_rut(b["rut_celda"])
        reales_r = real["ruts"]
        if len(reales_r) > 1:
            multi.append((b, reales_r))
            continue
        if not reales_r:
            sin_rut_real.append(b)
            continue
        if propuesto and propuesto == reales_r[0]:
            aciertos.append((b, propuesto))
        elif propuesto:
            errores.append((b, propuesto, reales_r[0]))
        else:
            no_propuso.append((b, reales_r[0]))

    total_eval = len(aciertos) + len(errores) + len(no_propuso)
    print("\n=== TRANSFERENCIAS (vs RUT asignado a mano) ===")
    print(f"  Evaluables: {total_eval} (además {len(multi)} con varios RUT "
          f"en una celda y {len(sin_rut_real)} sin RUT en la real)")
    if total_eval:
        print(f"  Aciertos del cruzador:  {len(aciertos)}")
        print(f"  ERRORES (propuso otro): {len(errores)}  ← revisar abajo")
        print(f"  No propuso (aprendible): {len(no_propuso)}")
    for b, prop, real_r in errores[:15]:
        print(f"    {b['fecha']} ${b['abono']:,} {b['descripcion'][:45]!r}: "
              f"propuso {prop}, real {real_r}")

    # --- Transbank y PAC: cuadratura de totales ---
    for etiqueta, patron in (("ABONOS TRANSBANK", GLOSA_TRANSBANK),
                             ("ABONOS PAC", GLOSA_PAC)):
        tot_real = sum(r["abono"] for r in reales
                       if patron.match(r["descripcion"]))
        tot_borr = sum(b["abono"] for b in borrador
                       if patron.match(b["descripcion"]))
        marca = "OK" if tot_real == tot_borr else "REVISAR"
        print(f"\n=== {etiqueta} ===\n  real ${tot_real:,} · borrador "
              f"${tot_borr:,} → {marca}")

    # --- diccionario nombre→RUT aprendido de la conciliación real ---
    args.salida.mkdir(parents=True, exist_ok=True)
    ruta_dic = args.salida / "diccionario_nombre_rut.csv"
    vistos = {}
    for r in reales:
        m = GLOSA_TRASPASO.match(r["descripcion"])
        if m and len(r["ruts"]) == 1:
            nombre = re.sub(r"\s+", " ", m.group(1)).strip().upper()
            vistos.setdefault(nombre, r["ruts"][0])
    with open(ruta_dic, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["nombre_cartola", "rut"])
        for nombre, rut in sorted(vistos.items()):
            w.writerow([nombre, rut])
    print(f"\nDiccionario aprendido: {ruta_dic} ({len(vistos)} nombres). "
          "Se usará para mejorar el match de los próximos meses.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
