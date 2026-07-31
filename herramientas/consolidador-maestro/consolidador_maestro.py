#!/usr/bin/env python3
"""Consolidador del maestro único de MundoSocios (insumo I-06).

Lee los 6 mantenedores reales de la carpeta RECAUDACIÓN Y COBRANZA:

    MANT. PLAN SOCIOS 07-26.xlsx
    MANT. COMPLEMENTARIO 07-26.xlsx
    MANT. CATASTRÓFICO 07-26.xlsx
    MANT. PLAN CARREÑO 07-26.xlsx
    Mantenedor Cuota Social empresa.xlsx
    Mantenedor Cuota Social persona.xlsx

y produce en la carpeta de salida:

    MAESTRO_UNICO_MS.xlsx      todos los productos por socio + hoja resumen
    maestro_seguros.csv        insumo de generador_devengos.py
    maestro_cuota_social.csv   insumo de generador_cuota_social.py

Uso:
    python3 consolidador_maestro.py --carpeta "RUTA/RECAUDACIÓN Y COBRANZA" \
        --salida ./2026-08

Detalles del layout real que este script maneja (levantado 2026-07-31):
  - En los seguros, el factor UF vigente es la columna "VALOR..." MÁS A LA
    DERECHA (VALOR '25 / VALOR UF actual, VALOR 2025 / VALOR 2026, etc.).
  - Debajo del mantenedor principal vienen pegadas las nóminas PAC/PAT y
    los eliminados: se detectan por sus encabezados y NO se consolidan.
  - Hay socios nuevos al final sin "Mod. Pago": quedan como SIN INFO.
  - Cuota social empresa: el N° de miembros solo está anotado si es >3;
    si no hay número se deriva del monto (base + n×valor persona).
  - Filas de totales o leyendas (sin RUT válido) se descartan.
"""

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

try:
    from openpyxl import Workbook, load_workbook
except ImportError:
    sys.exit("Falta openpyxl. Instalar con: pip3 install openpyxl")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "generador-devengos"))
import rut_utils

SEGUROS_ARCHIVO = [
    ("PLAN SOCIOS", re.compile(r"MANT.*PLAN\s*SOCIOS", re.IGNORECASE)),
    ("COMPLEMENTARIO", re.compile(r"MANT.*COMPLEMENTARIO", re.IGNORECASE)),
    ("CATASTROFICO", re.compile(r"MANT.*CATASTR", re.IGNORECASE)),
    ("PLAN CARRENO", re.compile(r"MANT.*CARRE", re.IGNORECASE)),
]
CS_EMPRESA = re.compile(r"CUOTA\s*SOCIAL\s*EMPRESA", re.IGNORECASE)
CS_PERSONA = re.compile(r"CUOTA\s*SOCIAL\s*PERSONA", re.IGNORECASE)

# Encabezados que marcan el inicio de una sección que NO es el mantenedor
# principal (nóminas PAC/PAT, eliminados).
MARCAS_FIN_BLOQUE = ("NOMBRE SEGURO", "ESTADO DE CARGO", "CONVENIO",
                     "FECHA DE ELIMINACION", "INCOBRABLE", "MOTIVO")

RUT_RE = re.compile(r"^\d{1,8}-[\dkK]$")


def _norm(texto):
    """MAYÚSCULAS sin tildes ni espacios repetidos, para comparar."""
    if texto is None:
        return ""
    t = unicodedata.normalize("NFD", str(texto))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t).strip().upper()


def _num(valor):
    """Convierte '$119,195' / '0,4' / 119195.0 a float, o None."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    t = str(valor).strip().replace("$", "").replace(" ", "")
    if not t:
        return None
    # '119,195' => miles con coma; '0,4' => decimal con coma
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", t):
        t = t.replace(",", "")
    elif "," in t and "." not in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _rut_de(celda):
    if celda is None:
        return None
    t = str(celda).strip().replace(".", "").replace(" ", "").upper()
    if RUT_RE.fullmatch(t):
        return t
    return None


def _es_fila_marca_fin(valores):
    fila = " | ".join(_norm(v) for v in valores if v is not None)
    return any(marca in fila for marca in MARCAS_FIN_BLOQUE)


def _buscar_encabezado(ws, requiere):
    """Devuelve (fila, {nombre_norm: col}) del primer encabezado que
    contenga todos los textos de `requiere`."""
    for fila in ws.iter_rows(min_row=1, max_row=60):
        nombres = {}
        for celda in fila:
            n = _norm(celda.value)
            if n:
                nombres.setdefault(n, celda.column)
        if all(any(req in n for n in nombres) for req in requiere):
            return fila[0].row, nombres
    return None, {}


def _col(nombres, *patrones, ultimo=False):
    """Columna cuyo encabezado contiene alguno de los patrones.
    Con ultimo=True devuelve la coincidencia más a la derecha."""
    hits = [c for n, c in nombres.items()
            if any(p in n for p in patrones)]
    if not hits:
        return None
    return max(hits) if ultimo else min(hits)


# ---------------------------------------------------------------- seguros

def leer_mantenedor_seguro(ruta, seguro):
    """Devuelve (filas, avisos). Cada fila: dict rut/nombre/factor/
    medio_pago/estado_pac/estado_pat/observacion."""
    wb = load_workbook(ruta, data_only=True, read_only=True)
    avisos = []
    for ws in wb.worksheets:
        fila_enc, nombres = _buscar_encabezado(ws, ["RUT", "NOMBRE", "VALOR"])
        if not fila_enc:
            continue
        c_rut = _col(nombres, "RUT")
        c_nombre = _col(nombres, "NOMBRE")
        c_factor = _col(nombres, "VALOR", ultimo=True)   # el vigente es el de más a la derecha
        c_medio = _col(nombres, "MOD")
        c_est_pac = _col(nombres, "ESTADO PAC")
        c_est_pat = _col(nombres, "ESTADO PAT")

        filas, sin_rut_seguidas = [], 0
        for fila in ws.iter_rows(min_row=fila_enc + 1):
            valores = [c.value for c in fila]
            if _es_fila_marca_fin(valores):
                break                       # empezó la nómina PAC/PAT/eliminados
            def v(col):
                if col is None or col - 1 >= len(valores):
                    return None
                return valores[col - 1]
            rut = _rut_de(v(c_rut))
            if not rut:
                sin_rut_seguidas += 1
                if sin_rut_seguidas > 25:
                    break                   # se acabó el bloque de datos
                continue
            sin_rut_seguidas = 0
            factor = _num(v(c_factor))
            medio = _norm(v(c_medio))
            obs, nota = [], []
            if not medio:
                nota.append("sin medio de pago (socio nuevo?)")
            if not rut_utils.es_valido(rut):
                obs.append("RUT INVALIDO (módulo 11)")
            if factor is None:
                obs.append("SIN FACTOR UF")
            elif not (0 < factor < 20):
                obs.append(f"FACTOR FUERA DE RANGO ({factor})")
            filas.append({
                "rut": rut,
                "nombre": str(v(c_nombre) or "").strip(),
                "seguro": seguro,
                "factor": factor,
                "medio_pago": medio,
                "estado_pac": _norm(v(c_est_pac)),
                "estado_pat": _norm(v(c_est_pat)),
                # 'observacion' bloquea el paso al CSV; 'nota' es informativa
                "observacion": "; ".join(obs),
                "nota": "; ".join(nota),
            })
        if filas:
            wb.close()
            return filas, avisos
    wb.close()
    return [], [f"{ruta.name}: no se encontró el encabezado del mantenedor"]


# ----------------------------------------------------------- cuota social

def leer_cuota_social(ruta, tipo):
    """tipo: 'EMPRESA' | 'PERSONA'. Devuelve (filas, avisos)."""
    wb = load_workbook(ruta, data_only=True, read_only=True)
    avisos = []
    for ws in wb.worksheets:
        fila_enc, nombres = _buscar_encabezado(ws, ["RUT", "NOMBRE DE SOCIO"])
        if not fila_enc:
            continue
        c_rut = _col(nombres, "RUT")
        c_nombre = _col(nombres, "NOMBRE DE SOCIO")
        c_nsocio = _col(nombres, "NUMERO DE SOCIO")
        c_camara = _col(nombres, "CAMARA")
        c_glosa = _col(nombres, "GLOSA")

        crudas, sin_rut = [], 0
        for fila in ws.iter_rows(min_row=fila_enc + 1):
            valores = [c.value for c in fila]
            def v(col):
                if col is None or col - 1 >= len(valores):
                    return None
                return valores[col - 1]
            rut = _rut_de(v(c_rut))
            if not rut:
                sin_rut += 1
                if sin_rut > 25:
                    break
                continue
            sin_rut = 0
            # entre cámara y glosa viven: monto(s) y, en empresa, el nº de
            # miembros (solo anotado cuando es > 3)
            desde = (c_camara or c_rut)
            hasta = c_glosa - 1 if c_glosa else len(valores)
            montos, enteros = [], []
            for celda in valores[desde:hasta]:
                n = _num(celda)
                if n is None:
                    continue
                if 4 <= n <= 200 and float(n).is_integer():
                    enteros.append(int(n))
                elif n > 1000:
                    montos.append(n)
            crudas.append({
                "rut": rut,
                "nombre": str(v(c_nombre) or "").strip(),
                "n_socio": str(v(c_nsocio) or "").strip(),
                "camara": str(v(c_camara) or "").strip(),
                "monto": montos[0] if montos else None,
                "miembros_anotados": enteros[0] if enteros else None,
            })
        if not crudas:
            continue
        wb.close()

        filas = []
        montos = [f["monto"] for f in crudas if f["monto"]]
        base = Counter(montos).most_common(1)[0][0] if montos else None
        for f in crudas:
            obs, miembros, monto_clp = [], "", ""
            if not rut_utils.es_valido(f["rut"]):
                obs.append("RUT INVALIDO (módulo 11)")
            if tipo == "EMPRESA":
                if f["miembros_anotados"]:
                    miembros = f["miembros_anotados"]
                elif f["monto"] and base and f["monto"] > base * 1.01:
                    # base = 3 UF => 1 UF = base/3; derivar miembros del monto
                    miembros = 3 + round((f["monto"] - base) / (base / 3))
                    obs.append(f"miembros derivados del monto ({f['monto']:,.0f})")
                else:
                    miembros = 3
            else:
                if f["monto"] and base and abs(f["monto"] - base) > 1:
                    monto_clp = round(f["monto"])
                    obs.append(f"monto excepcional (modo={base:,.0f})")
            filas.append({
                "rut": f["rut"], "nombre": f["nombre"],
                "tipo_socio": tipo, "camara": f["camara"],
                "n_socio": f["n_socio"], "miembros": miembros,
                "monto_clp": monto_clp, "observacion": "; ".join(obs),
            })
        return filas, avisos
    wb.close()
    return [], [f"{ruta.name}: no se encontró el encabezado del mantenedor"]


# ------------------------------------------------------------ escritura

def _dedup(filas, clave, avisos, origen):
    vistas, resultado = set(), []
    for f in filas:
        k = clave(f)
        if k in vistas:
            avisos.append(f"{origen}: duplicado {k} — se conserva la primera")
            continue
        vistas.add(k)
        resultado.append(f)
    return resultado


def escribir_salidas(seguros, cs, salida):
    salida.mkdir(parents=True, exist_ok=True)

    # --- MAESTRO_UNICO_MS.xlsx ---
    wb = Workbook()
    ws = wb.active
    ws.title = "MAESTRO"
    ws.append(["RUT", "NOMBRE", "PRODUCTO", "FACTOR_UF", "MIEMBROS",
               "MEDIO_PAGO", "ESTADO_PAC", "ESTADO_PAT", "CAMARA",
               "N_SOCIO", "OBSERVACION"])
    for f in seguros:
        obs = "; ".join(x for x in (f["observacion"], f["nota"]) if x)
        ws.append([f["rut"], f["nombre"], f["seguro"], f["factor"], "",
                   f["medio_pago"], f["estado_pac"], f["estado_pat"], "",
                   "", obs])
    for f in cs:
        ws.append([f["rut"], f["nombre"], f"CUOTA SOCIAL {f['tipo_socio']}",
                   "", f["miembros"], "", "", "", f["camara"],
                   f["n_socio"], f["observacion"]])
    res = wb.create_sheet("RESUMEN")
    res.append(["PRODUCTO", "REGISTROS", "CON OBSERVACION"])
    conteo = Counter()
    con_obs = Counter()
    for f in seguros:
        conteo[f["seguro"]] += 1
        if f["observacion"]:
            con_obs[f["seguro"]] += 1
    for f in cs:
        p = f"CUOTA SOCIAL {f['tipo_socio']}"
        conteo[p] += 1
        if f["observacion"]:
            con_obs[p] += 1
    for producto, n in conteo.items():
        res.append([producto, n, con_obs.get(producto, 0)])
    wb.save(salida / "MAESTRO_UNICO_MS.xlsx")

    # --- maestro_seguros.csv (formato del generador de devengos) ---
    with open(salida / "maestro_seguros.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["rut", "nombre", "seguro", "factor_uf", "medio_pago"])
        for s in seguros:
            if s["observacion"]:            # inválidos no van al generador
                continue
            factor = f"{s['factor']}".replace(".", ",")
            w.writerow([s["rut"], s["nombre"], s["seguro"], factor,
                        s["medio_pago"]])

    # --- maestro_cuota_social.csv ---
    with open(salida / "maestro_cuota_social.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["rut", "nombre", "tipo_socio", "camara", "miembros",
                    "monto_clp"])
        for c in cs:
            if "RUT INVALIDO" in c["observacion"]:
                continue
            w.writerow([c["rut"], c["nombre"], c["tipo_socio"], c["camara"],
                        c["miembros"], c["monto_clp"]])

    return conteo, con_obs


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Consolida los 6 mantenedores en el maestro único (I-06)")
    ap.add_argument("--carpeta", type=Path, required=True,
                    help="Carpeta con los 6 mantenedores (RECAUDACIÓN Y COBRANZA)")
    ap.add_argument("--salida", type=Path, default=Path("."))
    args = ap.parse_args(argv)

    if not args.carpeta.is_dir():
        print(f"ERROR: no existe la carpeta {args.carpeta}", file=sys.stderr)
        return 1

    archivos = [p for p in args.carpeta.iterdir()
                if p.suffix.lower() == ".xlsx" and not p.name.startswith("~")]
    avisos, seguros, cs = [], [], []

    for seguro, patron in SEGUROS_ARCHIVO:
        candidatos = [p for p in archivos if patron.search(p.name)]
        if not candidatos:
            avisos.append(f"FALTA el mantenedor de {seguro} (patrón MANT. ...)")
            continue
        ruta = sorted(candidatos)[-1]
        filas, avs = leer_mantenedor_seguro(ruta, seguro)
        avisos += avs
        filas = _dedup(filas, lambda f: (f["rut"], f["seguro"]), avisos, ruta.name)
        print(f"  {ruta.name}: {len(filas)} pólizas")
        seguros += filas

    for tipo, patron in (("EMPRESA", CS_EMPRESA), ("PERSONA", CS_PERSONA)):
        candidatos = [p for p in archivos if patron.search(_norm(p.name))]
        if not candidatos:
            avisos.append(f"FALTA el mantenedor de Cuota Social {tipo.lower()}")
            continue
        ruta = sorted(candidatos)[-1]
        filas, avs = leer_cuota_social(ruta, tipo)
        avisos += avs
        filas = _dedup(filas, lambda f: f["rut"], avisos, ruta.name)
        print(f"  {ruta.name}: {len(filas)} socios")
        cs += filas

    if not seguros and not cs:
        print("ERROR: no se pudo leer ningún mantenedor.", file=sys.stderr)
        return 1

    conteo, con_obs = escribir_salidas(seguros, cs, args.salida)

    print("\n=== RESUMEN POR PRODUCTO ===")
    for producto, n in conteo.items():
        extra = f" ({con_obs[producto]} con observación)" if con_obs.get(producto) else ""
        print(f"  {producto:24s} {n:5d}{extra}")
    if avisos:
        print("\n=== AVISOS (revisar) ===")
        for a in avisos:
            print(f"  - {a}")
    print(f"\nSalida en {args.salida.resolve()}:")
    print("  MAESTRO_UNICO_MS.xlsx · maestro_seguros.csv · maestro_cuota_social.csv")
    print("Las filas con observación quedan en el maestro Excel pero NO pasan "
          "a los CSV de los generadores: corregir en el mantenedor de origen "
          "y volver a ejecutar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
