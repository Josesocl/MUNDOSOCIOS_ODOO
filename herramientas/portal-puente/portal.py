#!/usr/bin/env python3
"""Portal Puente MS — flujo de compras y proveedores sin Terminal.

Aplicación web LOCAL para los colaboradores de MundoSocios: corre en un
computador (Mac o Windows) y el resto del equipo la usa desde el
navegador por red local. No reemplaza a Zoho (formularios y adjuntos) ni
a Manager+ (registro contable): cubre el tramo intermedio del puente.

Módulos:
  1. Bandeja de solicitudes de compra — se alimenta pegando el registro
     de Zoho (vista del formulario) o importando el export CSV del
     módulo "Formularios de Solicitud". Checklist automático: campos
     obligatorios, RUT válido, proveedor APTO (SII), tramo y aprobador
     según la matriz vigente, cotizaciones (con la regla de excepción:
     sin ambas cotizaciones solo aprueba Adm. y Finanzas o la Gerencia
     General) y saldo presupuestario del centro de costo.
  2. Alta de proveedor — verificación SII vía SimpleAPI con registro
     fechado (usa herramientas/sii-simpleapi).
  3. Archivo de carga para Manager+ — CSV con los datos de la solicitud
     aprobada y del proveedor, en el orden de las pantallas.
  4. Presupuesto por centro de costo — saldo inicial menos comprometido.
  5. Validador del TXT de nómina (opcional, usa validador-txt-banco).
  6. Bitácora de todo lo anterior.

Uso (el equipo NO usa esto: usa el doble clic de Iniciar_Portal):
    python3 portal.py            # abre en http://localhost:8765
    python3 portal.py --puerto 9000

Sin dependencias externas: Python 3.9+ puro.
"""

import argparse
import csv
import html
import io
import json
import re
import socket
import sys
import unicodedata
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE = Path(__file__).resolve().parent
DATOS = BASE / "datos_portal"
RUTA_SII = BASE.parent / "sii-simpleapi"
RUTA_TXT = BASE.parent / "validador-txt-banco"
for _ruta in (RUTA_SII, RUTA_TXT):
    if _ruta.is_dir():
        sys.path.insert(0, str(_ruta))

try:
    import alta_proveedor
    import cliente_simpleapi
except Exception:            # el portal funciona igual sin el módulo SII
    alta_proveedor = cliente_simpleapi = None
try:
    import validador_txt_banco
except Exception:
    validador_txt_banco = None

# ---------------------------------------------------------------- reglas

# Matriz de aprobación VIGENTE en el puente (CLP bruto c/IVA), definición
# MundoSocios 2026-08-18 (BP Flujo Compras v2.2 §2.5). En Odoo cambia.
TRAMOS = [
    (500_000, "Dueño del presupuesto (centro de costo)", {"OPERADOR", "AYF", "GG"}),
    (1_000_000, "Cecilia Ramírez", {"COMPRAS", "AYF", "GG"}),
    (5_000_000, "Patricio Fernández (Adm. y Finanzas)", {"AYF", "GG"}),
    (None, "Patricio Fernández + Constanza Daniels (GG)", {"GG"}),
]
# Roles con autoridad de EXCEPCIÓN (cotizaciones faltantes): AyF o GG.
ROLES_EXCEPCION = {"AYF", "GG"}
# Sin saldo presupuestario solo aprueba la Gerencia (flujos PF 2026-08).
ROLES_PRESUPUESTO = {"GG"}

CENTROS_DE_COSTO = ["MUNDO DESARROLLO", "MUNDO SALUD", "MUNDO ENCUENTRO",
                    "FOCO SOCIO", "ADMINISTRACIÓN", "MUNDO DIGITAL",
                    "MUNDO FUTURO"]

OPERADORES_INICIALES = [
    {"nombre": "Cecilia Ramírez", "rol": "COMPRAS"},
    {"nombre": "Patricio Fernández", "rol": "AYF"},
    {"nombre": "Constanza Daniels", "rol": "GG"},
    {"nombre": "Marcos Ibarra", "rol": "OPERADOR"},
    {"nombre": "Oriana (recaudación)", "rol": "OPERADOR"},
]

# Etiquetas tal como salen en la vista del registro de Zoho (módulo
# Formularios de Solicitud; verificado contra los campos reales del CRM).
CAMPOS_ZOHO = {
    "Nombre de actividad": "actividad",
    "Correo electrónico": "correo",
    "Fecha de actividad": "fecha_actividad",
    "Tipo de solicitud": "tipo_solicitud",
    "Centro de costo": "centro_costo",
    "Cuenta Contable": "cuenta_contable",
    "Formulario de Solicitud Propietario": "solicitante",
    "Creado por": "creado_por",
    "Estado de solicitud": "estado_zoho",
    "Usuario encargado": "usuario_encargado",
    "¿Posee contrato con proveedor?": "contrato_proveedor",
    "¿Posee contrato con el proveedor?": "contrato_proveedor",
    "Tipo de compra": "tipo_compra",
    "Detalle de productos o servicio (Descriptorio)": "detalle",
    "Fecha acuerdo de pago": "fecha_pago",
    "Valor total": "valor_total",
    "Descripción acuerdo de pago": "descripcion_pago",
    "Justificar cuando se pida OC con poca anticipación": "justificacion_urgencia",
    "Razón social / Nombre": "razon_social",
    "Giro": "giro",
    "Rut del proveedor": "rut_proveedor",
    "Motivo porque se escogió a ese proveedor": "motivo_proveedor",
    "Información complementaria": "info_complementaria",
    "Cotización escogida": "cotizacion_escogida",
    "Cotización adjunto": "cotizacion_adjunto",
    "Cotización respaldo adjunto": "cotizacion_respaldo",
    "¿Posee ambas cotizaciones?": "posee_ambas_cotizaciones",
    "Motivo de selección Proveedor": "motivo_seleccion",
    "Ficha de Proveedores adjunto": "ficha_proveedor_adjunto",
    "Ficha de Proveedores": "ficha_proveedor",
    "Requiere aprobación gerente": "requiere_gerente",
    "Etiqueta": "etiqueta",
}
OBLIGATORIOS = [("actividad", "Nombre de actividad"),
                ("correo", "Correo electrónico"),
                ("tipo_solicitud", "Tipo de solicitud"),
                ("centro_costo", "Centro de costo"),
                ("cuenta_contable", "Cuenta contable"),
                ("valor_total", "Valor total"),
                ("razon_social", "Razón social del proveedor"),
                ("rut_proveedor", "RUT del proveedor")]

# ---------------------------------------------------------------- utilidades


def _sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def normalizar_rut(texto):
    """Extrae y normaliza un RUT desde texto con basura ('65091028-1Pro'
    → '65091028-1'). Devuelve '' si no hay nada con forma de RUT."""
    t = str(texto or "")
    for patron in (r"(\d{1,2}\.\d{3}\.\d{3})\s*-?\s*([\dkK])",  # 12.345.678-9
                   r"(\d{7,8})\s*-\s*([\dkK])",                 # 12345678-9
                   r"(\d{7,8})([\dkK])(?!\d)"):                 # 123456789
        m = re.search(patron, t)
        if m:
            return f"{m.group(1).replace('.', '')}-{m.group(2).upper()}"
    return ""


def rut_valido(rut):
    m = re.fullmatch(r"(\d{7,9})-([\dK])", rut or "")
    if not m:
        return False
    cuerpo, dv = m.groups()
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    esperado = {10: "K", 11: "0"}.get(resto, str(resto))
    return dv == esperado


def parse_monto(texto):
    """'113.050' / '$ 113.050' / '113050,50' → int CLP (redondeado)."""
    if isinstance(texto, (int, float)):
        return int(round(texto))
    limpio = re.sub(r"[^\d,.\-]", "", str(texto or ""))
    if not limpio:
        return 0
    if "," in limpio:                       # coma decimal chilena
        limpio = limpio.replace(".", "").replace(",", ".")
        try:
            return int(round(float(limpio)))
        except ValueError:
            return 0
    puntos = limpio.count(".")
    if puntos:
        partes = limpio.split(".")
        if all(len(p) == 3 for p in partes[1:]):   # miles: 1.113.050
            limpio = "".join(partes)
        else:                                       # decimal: 113050.5
            try:
                return int(round(float(limpio)))
            except ValueError:
                return 0
    try:
        return int(limpio)
    except ValueError:
        return 0


def ahora():
    return datetime.now().strftime("%d-%m-%Y %H:%M")


# ---------------------------------------------------------------- persistencia


def _leer_json(nombre, defecto):
    ruta = DATOS / nombre
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return defecto


def _escribir_json(nombre, datos):
    DATOS.mkdir(exist_ok=True)
    (DATOS / nombre).write_text(
        json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


def cargar_solicitudes():
    return _leer_json("solicitudes.json", {})


def guardar_solicitudes(s):
    _escribir_json("solicitudes.json", s)


def cargar_presupuesto():
    p = _leer_json("presupuesto.json", None)
    if p is None:
        p = {cc: {"inicial": 0} for cc in CENTROS_DE_COSTO}
    return p


def guardar_presupuesto(p):
    _escribir_json("presupuesto.json", p)


def cargar_config():
    c = _leer_json("config.json", None)
    if c is None:
        c = {"operadores": OPERADORES_INICIALES}
        _escribir_json("config.json", c)
    return c


def bitacora(evento, detalle, operador=""):
    DATOS.mkdir(exist_ok=True)
    ruta = DATOS / "bitacora.csv"
    nueva = not ruta.exists()
    with open(ruta, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        if nueva:
            w.writerow(["fecha", "evento", "detalle", "operador"])
        w.writerow([ahora(), evento, detalle, operador])


def leer_bitacora():
    ruta = DATOS / "bitacora.csv"
    if not ruta.exists():
        return []
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


# ---------------------------------------------------------------- Zoho: pegar / CSV


def parsear_pegado(texto):
    """Parsea la vista de un registro de Zoho pegada como texto.
    Las etiquetas vienen como 'Etiqueta :' con el valor al lado o en la
    línea siguiente."""
    datos = {}
    etiquetas = sorted(CAMPOS_ZOHO, key=len, reverse=True)
    lineas = [l.strip() for l in texto.splitlines()]
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        encontrada = None
        for et in etiquetas:
            m = re.match(re.escape(et) + r"\s*:\s*(.*)$", linea)
            if m:
                encontrada = (et, m.group(1).strip())
                break
        if encontrada:
            et, valor = encontrada
            if not valor:                    # valor en la(s) línea(s) siguiente(s)
                j = i + 1
                while j < len(lineas) and not lineas[j]:
                    j += 1
                if j < len(lineas) and not any(
                        re.match(re.escape(e) + r"\s*:", lineas[j])
                        for e in etiquetas):
                    valor = lineas[j]
                    i = j
            valor = re.sub(r"\.(gif|png)\s*$", "", valor).strip()
            if valor and not valor.startswith(("spacer_", "yes_")):
                datos[CAMPOS_ZOHO[et]] = valor
            elif valor.startswith("yes_"):
                datos[CAMPOS_ZOHO[et]] = "Sí"
        i += 1
    return datos


def _clave_encabezado(encabezado):
    plano = _sin_tildes(encabezado or "").lower().strip()
    for etiqueta, clave in CAMPOS_ZOHO.items():
        if _sin_tildes(etiqueta).lower() == plano:
            return clave
    return None


def parsear_csv(contenido):
    """Importa el export CSV del módulo de Zoho. → lista de dicts."""
    muestra = contenido[:2000]
    delim = ";" if muestra.count(";") > muestra.count(",") else ","
    lector = csv.DictReader(io.StringIO(contenido), delimiter=delim)
    filas = []
    for fila in lector:
        datos = {}
        for enc, valor in fila.items():
            clave = _clave_encabezado(enc)
            if clave and valor and valor.strip():
                datos[clave] = valor.strip()
        if datos:
            filas.append(datos)
    return filas


# ---------------------------------------------------------------- proveedor APTO


def estado_proveedor(rut):
    """Busca la verificación SII más reciente del RUT en la bitácora del
    módulo de alta. → ('APTO-SII'|'NO APTO'|None, fecha)."""
    ruta = RUTA_SII / "verificaciones" / "registro_verificaciones.csv"
    if not ruta.exists():
        return None, ""
    ultimo = (None, "")
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            if fila.get("rut") == rut:
                ultimo = (fila.get("resultado"), fila.get("fecha", ""))
    return ultimo


# ---------------------------------------------------------------- checklist


def comprometido_por_cc(solicitudes, cc, excepto=None):
    total = 0
    for sid, s in solicitudes.items():
        if sid == excepto:
            continue
        if s.get("estado_portal", "").startswith("APROBADA") \
                and s.get("datos", {}).get("centro_costo") == cc:
            total += parse_monto(s["datos"].get("valor_total"))
    return total


def tramo_de(monto):
    for limite, aprobador, roles in TRAMOS:
        if limite is None or monto <= limite:
            return aprobador, roles
    return TRAMOS[-1][1], TRAMOS[-1][2]


def evaluar_solicitud(datos, solicitudes=None, presupuesto=None,
                      id_actual=None):
    """Checklist completo de una solicitud. → dict con errores, avisos,
    tramo, roles autorizados y si requiere excepción."""
    solicitudes = solicitudes if solicitudes is not None else {}
    presupuesto = presupuesto if presupuesto is not None else {}
    errores, avisos = [], []

    for clave, nombre in OBLIGATORIOS:
        if not str(datos.get(clave, "")).strip():
            errores.append(f"Falta: {nombre}")

    rut = normalizar_rut(datos.get("rut_proveedor", ""))
    if datos.get("rut_proveedor") and not rut:
        errores.append("RUT del proveedor ilegible")
    elif rut and not rut_valido(rut):
        errores.append(f"RUT del proveedor inválido (módulo 11): {rut}")
    datos["rut_normalizado"] = rut

    apto, fecha_apto = (None, "")
    if rut and rut_valido(rut):
        apto, fecha_apto = estado_proveedor(rut)
        if apto == "APTO-SII":
            avisos.append(f"Proveedor APTO-SII (verificado {fecha_apto})")
        elif apto == "NO APTO":
            errores.append(f"Proveedor NO APTO según verificación SII "
                           f"({fecha_apto}) — no puede entrar a OC")
        else:
            avisos.append("Proveedor sin verificación SII registrada — "
                          "verificarlo en la pestaña Proveedores")

    monto = parse_monto(datos.get("valor_total"))
    aprobador, roles = tramo_de(monto)

    requiere_excepcion = False
    posee = _sin_tildes(str(datos.get("posee_ambas_cotizaciones", ""))).strip().lower()
    if posee != "si":
        requiere_excepcion = True
        motivo = datos.get("motivo_seleccion") or datos.get("motivo_proveedor") or ""
        avisos.append("Sin ambas cotizaciones: solo puede aprobar Adm. y "
                      "Finanzas o la Gerencia General"
                      + (f" (motivo declarado: {motivo})" if motivo else
                         " — SIN motivo declarado"))

    cc = datos.get("centro_costo", "")
    sin_saldo = False
    if cc:
        info_cc = presupuesto.get(cc)
        if info_cc and parse_monto(info_cc.get("inicial")) > 0:
            saldo = parse_monto(info_cc.get("inicial")) - \
                comprometido_por_cc(solicitudes, cc, excepto=id_actual)
            if monto > saldo:
                sin_saldo = True
                avisos.append(
                    f"SIN saldo presupuestario en {cc} (saldo "
                    f"${saldo:,.0f} vs ${monto:,.0f}): solo la Gerencia "
                    "puede aprobar la ampliación/reasignación".replace(",", "."))
            else:
                avisos.append(f"Presupuesto {cc}: saldo disponible "
                              f"${saldo:,.0f}".replace(",", "."))
        else:
            avisos.append(f"Centro de costo {cc} sin presupuesto cargado "
                          "(pestaña Presupuesto) — chequeo omitido")

    roles_autorizados = set(roles)
    if requiere_excepcion:
        roles_autorizados &= ROLES_EXCEPCION
    if sin_saldo:
        roles_autorizados &= ROLES_PRESUPUESTO

    return {"errores": errores, "avisos": avisos, "monto": monto,
            "tramo": aprobador, "roles_autorizados": sorted(roles_autorizados),
            "requiere_excepcion": requiere_excepcion, "sin_saldo": sin_saldo,
            "proveedor_apto": apto == "APTO-SII"}


# ---------------------------------------------------------------- Manager+


def archivo_manager(datos, evaluacion):
    """CSV (;) con los datos en el orden de las pantallas de Manager+:
    bloque proveedor + bloque OC. Layout de carga masiva por confirmar
    con el equipo Manager+; mientras tanto, orden de digitación."""
    rut = datos.get("rut_normalizado") or normalizar_rut(
        datos.get("rut_proveedor", ""))
    salida = io.StringIO()
    w = csv.writer(salida, delimiter=";")
    w.writerow(["BLOQUE", "CAMPO", "VALOR"])
    prov = [("RUT", rut), ("Razón social", datos.get("razon_social", "")),
            ("Giro", datos.get("giro", "")),
            ("Clasificación", "sin clasificación"),
            ("Tipo proveedor", "Nacional (facturas)"),
            ("Plazo de pago", "30 días")]
    for campo, valor in prov:
        w.writerow(["PROVEEDOR", campo, valor])
    oc = [("Fecha solicitud", datos.get("fecha_actividad", "")),
          ("Solicitante", datos.get("solicitante") or datos.get("creado_por", "")),
          ("Centro de costo", datos.get("centro_costo", "")),
          ("Cuenta contable", datos.get("cuenta_contable", "")),
          ("Proveedor (RUT)", rut),
          ("Glosa / detalle", datos.get("detalle", "")),
          ("Monto total (c/IVA)", evaluacion.get("monto", "")),
          ("Fecha acuerdo de pago", datos.get("fecha_pago", "")),
          ("Tramo de aprobación", evaluacion.get("tramo", "")),
          ("Actividad Zoho", datos.get("actividad", ""))]
    for campo, valor in oc:
        w.writerow(["OC", campo, valor])
    return salida.getvalue()


# ---------------------------------------------------------------- HTML


ESTILO = """<style>
body{font-family:-apple-system,Segoe UI,sans-serif;margin:0;background:#f4f4f0;color:#222}
header{background:#1f3a5f;color:#fff;padding:.7em 1.2em;display:flex;gap:1.4em;align-items:baseline;flex-wrap:wrap}
header a{color:#cfe0f5;text-decoration:none;font-size:.95em}
header a.activo,header a:hover{color:#fff;border-bottom:2px solid #fff}
h1{font-size:1.1em;margin:0 1em 0 0}
main{max-width:980px;margin:1.2em auto;padding:0 1em}
.tarjeta{background:#fff;border:1px solid #ddd;border-radius:8px;padding:1em 1.2em;margin-bottom:1em}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #ddd;padding:.4em .6em;text-align:left;font-size:.92em}
th{background:#eef2f7}
.ok{color:#1a7f37;font-weight:600}.err{color:#c62828;font-weight:600}
.warn{color:#9a6700}.chip{display:inline-block;padding:.1em .6em;border-radius:1em;font-size:.85em;font-weight:600}
.c-lista{background:#e6f4ea;color:#1a7f37}.c-inc{background:#fdecea;color:#c62828}
.c-apr{background:#dbeafe;color:#1e40af}.c-rec{background:#eee;color:#666}.c-exc{background:#fef3c7;color:#92400e}
input,select,textarea{font:inherit;padding:.35em;border:1px solid #bbb;border-radius:4px;max-width:100%}
textarea{width:100%;box-sizing:border-box}
button{font:inherit;background:#1f3a5f;color:#fff;border:0;border-radius:5px;padding:.45em 1em;cursor:pointer}
button.sec{background:#666}button.peligro{background:#c62828}
form.inline{display:inline}
.aviso{background:#fef9e7;border:1px solid #f0e0a0;border-radius:6px;padding:.5em .8em;margin:.4em 0;font-size:.92em}
.error{background:#fdecea;border:1px solid #f5c6c6;border-radius:6px;padding:.5em .8em;margin:.4em 0;font-size:.92em}
small{color:#666}
</style>"""


def pagina(titulo, cuerpo, pestana=""):
    tabs = [("/", "Solicitudes"), ("/nueva", "Ingresar solicitud"),
            ("/proveedor", "Proveedores"), ("/presupuesto", "Presupuesto"),
            ("/txt", "TXT banco"), ("/bitacora", "Bitácora")]
    nav = "".join(
        f'<a href="{u}" class="{"activo" if u == pestana else ""}">{t}</a>'
        for u, t in tabs)
    return f"""<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titulo)} — Portal Puente MS</title>{ESTILO}
<body><header><h1>Portal Puente MS</h1>{nav}</header>
<main>{cuerpo}</main>
<footer style="text-align:center;color:#999;font-size:.8em;margin:2em">
Puente operativo hasta la salida en Odoo · MundoSocios / JR Jottar</footer>
</body></html>"""


def _chip(estado):
    clases = {"LISTA": "c-lista", "INCOMPLETA": "c-inc", "APROBADA": "c-apr",
              "APROBADA-EXCEPCION": "c-exc", "RECHAZADA": "c-rec"}
    return f'<span class="chip {clases.get(estado, "")}">{estado}</span>'


def _selector_operador(config, nombre_campo="operador"):
    ops = "".join(f'<option>{html.escape(o["nombre"])}</option>'
                  for o in config["operadores"])
    return f'<select name="{nombre_campo}" required><option value="">— ¿quién opera? —</option>{ops}</select>'


def rol_de(config, nombre):
    for o in config["operadores"]:
        if o["nombre"] == nombre:
            return o.get("rol", "OPERADOR")
    return None


# ---------------------------------------------------------------- servidor


def _leer_cuerpo(handler):
    largo = int(handler.headers.get("Content-Length", 0))
    return handler.rfile.read(largo)


def _parse_multipart(cuerpo, content_type):
    """Parser mínimo de multipart/form-data (para subir CSV y TXT)."""
    m = re.search(r'boundary="?([^";]+)"?', content_type)
    if not m:
        return {}, {}
    frontera = ("--" + m.group(1)).encode()
    campos, archivos = {}, {}
    for parte in cuerpo.split(frontera):
        if b"\r\n\r\n" not in parte:
            continue
        cabecera, contenido = parte.split(b"\r\n\r\n", 1)
        contenido = contenido.rstrip(b"\r\n-")
        cab = cabecera.decode("utf-8", "replace")
        m_nombre = re.search(r'name="([^"]+)"', cab)
        if not m_nombre:
            continue
        nombre = m_nombre.group(1)
        m_archivo = re.search(r'filename="([^"]*)"', cab)
        if m_archivo and m_archivo.group(1):
            archivos[nombre] = (m_archivo.group(1), contenido)
        else:
            campos[nombre] = contenido.decode("utf-8", "replace").strip()
    return campos, archivos


class Portal(BaseHTTPRequestHandler):
    def log_message(self, *a):        # silencioso
        pass

    def _responder(self, cuerpo, tipo="text/html; charset=utf-8",
                   codigo=200, descarga=None):
        datos = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        if descarga:
            self.send_header("Content-Disposition",
                             f'attachment; filename="{descarga}"')
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _redirigir(self, destino):
        self.send_response(303)
        self.send_header("Location", destino)
        self.end_headers()

    # ------------------------------------------------------------ GET

    def do_GET(self):
        ruta = urlparse(self.path)
        q = parse_qs(ruta.query)
        try:
            if ruta.path == "/":
                self._responder(vista_tablero())
            elif ruta.path == "/nueva":
                self._responder(vista_nueva())
            elif ruta.path.startswith("/solicitud/"):
                self._responder(vista_solicitud(ruta.path.split("/")[2]))
            elif ruta.path.startswith("/manager/"):
                sid = ruta.path.split("/")[2].replace(".csv", "")
                sols = cargar_solicitudes()
                s = sols.get(sid)
                if not s:
                    self._responder("No existe", codigo=404)
                    return
                contenido = archivo_manager(s["datos"], s.get("evaluacion", {}))
                nombre = (f"CARGA_MANAGER_{sid}_"
                          f"{datetime.now():%Y%m%d-%H%M}.csv")
                carpeta = DATOS / "manager"
                carpeta.mkdir(parents=True, exist_ok=True)
                (carpeta / nombre).write_text(contenido, encoding="utf-8-sig")
                bitacora("archivo_manager", f"solicitud {sid} → {nombre}")
                self._responder(contenido.encode("utf-8-sig"),
                                "text/csv; charset=utf-8",
                                descarga=nombre)
            elif ruta.path == "/proveedor":
                self._responder(vista_proveedor(q))
            elif ruta.path == "/presupuesto":
                self._responder(vista_presupuesto())
            elif ruta.path == "/txt":
                self._responder(vista_txt())
            elif ruta.path == "/bitacora":
                self._responder(vista_bitacora())
            elif ruta.path.startswith("/descarga_txt/"):
                nombre = Path(ruta.path.split("/", 2)[2]).name
                archivo = DATOS / "txt" / nombre
                if archivo.exists():
                    self._responder(archivo.read_bytes(),
                                    "text/plain; charset=utf-8",
                                    descarga=nombre)
                else:
                    self._responder("No existe", codigo=404)
            else:
                self._responder("No existe", codigo=404)
        except Exception as e:                     # error visible, no caída
            self._responder(pagina("Error", f'<div class="error">Error '
                                   f'interno: {html.escape(str(e))}</div>'),
                            codigo=500)

    # ------------------------------------------------------------ POST

    def do_POST(self):
        tipo = self.headers.get("Content-Type", "")
        cuerpo = _leer_cuerpo(self)
        if tipo.startswith("multipart/form-data"):
            campos, archivos = _parse_multipart(cuerpo, tipo)
        else:
            campos = {k: v[0] for k, v in
                      parse_qs(cuerpo.decode("utf-8", "replace")).items()}
            archivos = {}
        ruta = urlparse(self.path).path
        try:
            if ruta == "/nueva":
                self._post_nueva(campos, archivos)
            elif ruta == "/decidir":
                self._post_decidir(campos)
            elif ruta == "/reevaluar":
                self._post_reevaluar(campos)
            elif ruta == "/proveedor":
                self._post_proveedor(campos)
            elif ruta == "/presupuesto":
                self._post_presupuesto(campos)
            elif ruta == "/txt":
                self._post_txt(campos, archivos)
            else:
                self._responder("No existe", codigo=404)
        except Exception as e:
            self._responder(pagina("Error", f'<div class="error">Error: '
                                   f'{html.escape(str(e))}</div>'), codigo=500)

    def _post_nueva(self, campos, archivos):
        sols = cargar_solicitudes()
        pres = cargar_presupuesto()
        nuevos = []
        if campos.get("pegado", "").strip():
            datos = parsear_pegado(campos["pegado"])
            if datos:
                nuevos.append(datos)
        if "csv" in archivos:
            contenido = archivos["csv"][1].decode("utf-8-sig", "replace")
            nuevos.extend(parsear_csv(contenido))
        if not nuevos:
            self._responder(vista_nueva(
                "No se reconoció ninguna solicitud en lo pegado/importado."))
            return
        ultimo = None
        for datos in nuevos:
            sid = str(max([int(k) for k in sols] + [0]) + 1)
            ev = evaluar_solicitud(datos, sols, pres, sid)
            estado = "INCOMPLETA" if ev["errores"] else "LISTA"
            sols[sid] = {"datos": datos, "evaluacion": ev,
                         "estado_portal": estado, "ingresada": ahora(),
                         "decisiones": []}
            bitacora("solicitud_ingresada",
                     f"{sid}: {datos.get('actividad', '')[:60]}")
            ultimo = sid
        guardar_solicitudes(sols)
        self._redirigir(f"/solicitud/{ultimo}" if len(nuevos) == 1 else "/")

    def _post_reevaluar(self, campos):
        sid = campos.get("id", "")
        sols = cargar_solicitudes()
        if sid in sols:
            ev = evaluar_solicitud(sols[sid]["datos"], sols,
                                   cargar_presupuesto(), sid)
            sols[sid]["evaluacion"] = ev
            if sols[sid]["estado_portal"] in ("INCOMPLETA", "LISTA"):
                sols[sid]["estado_portal"] = \
                    "INCOMPLETA" if ev["errores"] else "LISTA"
            guardar_solicitudes(sols)
        self._redirigir(f"/solicitud/{sid}")

    def _post_decidir(self, campos):
        sid = campos.get("id", "")
        accion = campos.get("accion", "")
        operador = campos.get("operador", "")
        config = cargar_config()
        sols = cargar_solicitudes()
        s = sols.get(sid)
        if not s or not operador:
            self._redirigir(f"/solicitud/{sid}")
            return
        ev = evaluar_solicitud(s["datos"], sols, cargar_presupuesto(), sid)
        s["evaluacion"] = ev
        rol = rol_de(config, operador)
        if accion == "aprobar":
            if ev["errores"]:
                s["nota"] = "No se puede aprobar: la solicitud tiene errores."
            elif rol not in ev["roles_autorizados"]:
                s["nota"] = (f"{operador} no tiene autoridad para este caso "
                             f"(tramo: {ev['tramo']}"
                             + ("; requiere excepción AyF/GG"
                                if ev["requiere_excepcion"] else "")
                             + ("; sin saldo: solo Gerencia"
                                if ev["sin_saldo"] else "") + ").")
            else:
                excepcion = ev["requiere_excepcion"] or ev["sin_saldo"]
                s["estado_portal"] = ("APROBADA-EXCEPCION" if excepcion
                                      else "APROBADA")
                s["nota"] = ""
                s["decisiones"].append(
                    {"fecha": ahora(), "operador": operador,
                     "decision": s["estado_portal"]})
                bitacora("solicitud_aprobada",
                         f"{sid} ({s['estado_portal']})", operador)
        elif accion == "rechazar":
            s["estado_portal"] = "RECHAZADA"
            s["nota"] = ""
            s["decisiones"].append({"fecha": ahora(), "operador": operador,
                                    "decision": "RECHAZADA"})
            bitacora("solicitud_rechazada", sid, operador)
        elif accion == "eliminar":
            del sols[sid]
            guardar_solicitudes(sols)
            bitacora("solicitud_eliminada", sid, operador)
            self._redirigir("/")
            return
        guardar_solicitudes(sols)
        self._redirigir(f"/solicitud/{sid}")

    def _post_proveedor(self, campos):
        if alta_proveedor is None:
            self._responder(vista_proveedor(
                {}, "El módulo sii-simpleapi no está junto al portal."))
            return
        rut = normalizar_rut(campos.get("rut", ""))
        try:
            datos, origen = cliente_simpleapi.consultar_rut(
                rut, mock=bool(campos.get("mock")))
        except RuntimeError as e:
            self._responder(vista_proveedor({}, str(e)))
            return

        class _Args:
            correo_comercial = campos.get("correo", "")
            nombre_fantasia = campos.get("fantasia", "")
        estado, tipo, obs = alta_proveedor.evaluar(datos)
        campos_m = alta_proveedor.campos_manager(datos, _Args)
        ruta = alta_proveedor.escribir_registro(datos, origen, estado, obs,
                                                campos_m)
        bitacora("verificacion_sii", f"{rut}: {estado} [{origen}]",
                 campos.get("operador", ""))
        cuerpo = [f'<div class="tarjeta"><h2>{html.escape(datos.get("razonSocial", ""))} '
                  f'({html.escape(datos.get("rut", ""))})</h2>'
                  f'<p>Resultado: <span class="{ "ok" if estado == "APTO-SII" else "err"}">'
                  f'{estado}</span> <small>[origen: {origen}]</small></p>']
        for o in obs:
            cuerpo.append(f'<div class="aviso">{html.escape(o)}</div>')
        cuerpo.append("<h3>Campos para Manager+</h3><table>")
        for nombre, valor in campos_m:
            cuerpo.append(f"<tr><th>{html.escape(nombre)}</th>"
                          f"<td>{html.escape(str(valor))}</td></tr>")
        cuerpo.append("</table>"
                      f"<p><small>Registro guardado: {html.escape(ruta.name)}"
                      "</small></p></div>")
        self._responder(vista_proveedor({}, extra="".join(cuerpo)))

    def _post_presupuesto(self, campos):
        pres = cargar_presupuesto()
        for clave, valor in campos.items():
            if clave.startswith("cc_"):
                cc = clave[3:]
                pres.setdefault(cc, {})["inicial"] = parse_monto(valor)
        nuevo = campos.get("nuevo_cc", "").strip()
        if nuevo:
            pres.setdefault(nuevo, {})["inicial"] = \
                parse_monto(campos.get("nuevo_monto", 0))
        guardar_presupuesto(pres)
        bitacora("presupuesto_actualizado", "saldos iniciales",
                 campos.get("operador", ""))
        self._redirigir("/presupuesto")

    def _post_txt(self, campos, archivos):
        if validador_txt_banco is None:
            self._responder(vista_txt("El módulo validador-txt-banco no "
                                      "está junto al portal."))
            return
        if "archivo" not in archivos:
            self._responder(vista_txt("Selecciona el archivo TXT."))
            return
        nombre, contenido = archivos["archivo"]
        DATOS.mkdir(exist_ok=True)
        (DATOS / "txt").mkdir(exist_ok=True)
        ruta = DATOS / "txt" / Path(nombre).name
        ruta.write_bytes(contenido)
        lineas, fin, cod = validador_txt_banco.leer_txt(ruta)
        errores, avisos = validador_txt_banco.validar(lineas)
        partes = [f"<h3>{html.escape(nombre)} — {len(lineas)} líneas</h3>"]
        for e in errores:
            partes.append(f'<div class="error">ERROR: {html.escape(e)}</div>')
        for a in avisos:
            partes.append(f'<div class="aviso">{html.escape(a)}</div>')
        fecha = campos.get("fecha_pago", "").strip()
        if fecha:
            try:
                nueva = validador_txt_banco.normalizar_fecha(fecha)
                destino, vieja = validador_txt_banco.corregir_fecha(
                    ruta, lineas, fin, cod, nueva)
                partes.append(
                    f'<div class="aviso ok">Fecha corregida {vieja} → '
                    f'{nueva}. <a href="/descarga_txt/{destino.name}">'
                    "Descargar TXT para el banco</a></div>")
            except RuntimeError as e:
                partes.append(f'<div class="error">{html.escape(str(e))}</div>')
        veredicto = ("NO CARGAR AL BANCO: corregir en Manager+ y regenerar."
                     if errores else "Sin errores.")
        partes.append(f"<p><b>{veredicto}</b></p>")
        bitacora("txt_validado", f"{nombre}: {len(errores)} errores",
                 campos.get("operador", ""))
        self._responder(vista_txt(extra="".join(partes)))


# ---------------------------------------------------------------- vistas


def vista_tablero():
    sols = cargar_solicitudes()
    filas = []
    for sid in sorted(sols, key=int, reverse=True):
        s = sols[sid]
        d = s["datos"]
        ev = s.get("evaluacion", {})
        filas.append(
            f'<tr><td><a href="/solicitud/{sid}">#{sid}</a></td>'
            f"<td>{html.escape(d.get('actividad', ''))}</td>"
            f"<td>{html.escape(d.get('centro_costo', ''))}</td>"
            f"<td style='text-align:right'>${ev.get('monto', 0):,.0f}".replace(",", ".")
            + "</td>"
            f"<td>{html.escape(d.get('razon_social', ''))}</td>"
            f"<td>{_chip(s.get('estado_portal', ''))}</td></tr>")
    tabla = ("<table><tr><th>#</th><th>Actividad</th><th>CC</th>"
             "<th>Monto</th><th>Proveedor</th><th>Estado</th></tr>"
             + "".join(filas) + "</table>") if filas else \
        "<p>No hay solicitudes. Ingresa la primera en «Ingresar solicitud».</p>"
    return pagina("Solicitudes", f'<div class="tarjeta"><h2>Bandeja de '
                  f'solicitudes de compra</h2>{tabla}</div>', "/")


def vista_nueva(mensaje=""):
    aviso = f'<div class="error">{html.escape(mensaje)}</div>' if mensaje else ""
    cuerpo = f"""{aviso}
<div class="tarjeta"><h2>Opción A — Pegar el registro de Zoho</h2>
<p><small>En Zoho abre el Formulario de Solicitud, selecciona todo el texto
del registro (Cmd/Ctrl+A sobre la vista), cópialo y pégalo aquí.</small></p>
<form method="post" action="/nueva">
<textarea name="pegado" rows="12" placeholder="Nombre de actividad : …&#10;Centro de costo : …"></textarea>
<p><button>Ingresar solicitud</button></p></form></div>
<div class="tarjeta"><h2>Opción B — Importar export CSV de Zoho</h2>
<p><small>En Zoho: módulo Formularios de Solicitud → exportar registros a
CSV → sube el archivo aquí. Ingresa todas las filas de una vez.</small></p>
<form method="post" action="/nueva" enctype="multipart/form-data">
<input type="file" name="csv" accept=".csv">
<button>Importar CSV</button></form></div>"""
    return pagina("Ingresar solicitud", cuerpo, "/nueva")


def vista_solicitud(sid):
    sols = cargar_solicitudes()
    s = sols.get(sid)
    if not s:
        return pagina("No existe", '<div class="error">Solicitud no '
                      'encontrada.</div>')
    config = cargar_config()
    d, ev = s["datos"], s.get("evaluacion", {})
    vistos, pares = set(), []
    for etq, clave in CAMPOS_ZOHO.items():
        if clave in d and clave not in vistos and clave != "rut_normalizado":
            vistos.add(clave)
            pares.append((etq, clave))
    filas = "".join(
        f"<tr><th>{html.escape(etq)}</th><td>{html.escape(str(d.get(clave, '')))}</td></tr>"
        for etq, clave in pares)
    checks = []
    for e in ev.get("errores", []):
        checks.append(f'<div class="error">✗ {html.escape(e)}</div>')
    for a in ev.get("avisos", []):
        checks.append(f'<div class="aviso">• {html.escape(a)}</div>')
    nota = (f'<div class="error">{html.escape(s.get("nota", ""))}</div>'
            if s.get("nota") else "")
    decisiones = "".join(
        f"<li>{html.escape(x['fecha'])} — {html.escape(x['decision'])} por "
        f"{html.escape(x['operador'])}</li>" for x in s.get("decisiones", []))
    acciones = f"""
<form method="post" action="/decidir" class="inline">
<input type="hidden" name="id" value="{sid}">
{_selector_operador(config)}
<button name="accion" value="aprobar">Aprobar</button>
<button name="accion" value="rechazar" class="peligro">Rechazar</button>
<button name="accion" value="eliminar" class="sec"
 onclick="return confirm('¿Eliminar la solicitud #{sid}?')">Eliminar</button>
</form>
<form method="post" action="/reevaluar" class="inline">
<input type="hidden" name="id" value="{sid}">
<button class="sec">Re-evaluar checklist</button></form>"""
    descargar = (f'<p><a href="/manager/{sid}.csv"><button>Descargar archivo '
                 'de carga Manager+</button></a></p>'
                 if s.get("estado_portal", "").startswith("APROBADA") else "")
    monto_txt = "$" + format(ev.get("monto", 0), ",.0f").replace(",", ".")
    cuerpo = f"""<div class="tarjeta">
<h2>Solicitud #{sid} {_chip(s.get('estado_portal', ''))}</h2>
<p><b>Tramo:</b> {html.escape(ev.get('tramo', ''))} ·
<b>Monto:</b> {monto_txt}</p>
{''.join(checks)}{nota}
<p>{acciones}</p>{descargar}
{f"<h3>Decisiones</h3><ul>{decisiones}</ul>" if decisiones else ""}
</div>
<div class="tarjeta"><h3>Datos de la solicitud (Zoho)</h3>
<table>{filas}</table>
<p><small>Ingresada al portal: {html.escape(s.get('ingresada', ''))}.
Los adjuntos (cotizaciones, ficha) siguen en Zoho.</small></p></div>"""
    return pagina(f"Solicitud {sid}", cuerpo, "/")


def vista_proveedor(q=None, mensaje="", extra=""):
    config = cargar_config()
    aviso = f'<div class="error">{html.escape(mensaje)}</div>' if mensaje else ""
    estado_cuota = ""
    if cliente_simpleapi is not None:
        try:
            estado = cliente_simpleapi._cargar_estado()
            usadas = cliente_simpleapi.consultas_del_mes(estado)
            estado_cuota = (f"<p><small>Cuota SimpleAPI del mes: {usadas}/"
                            f"{cliente_simpleapi.LIMITE_MENSUAL_RUT} "
                            "consultas usadas (repetir un RUT no gasta)."
                            "</small></p>")
        except Exception:
            pass
    cuerpo = f"""{aviso}{extra}
<div class="tarjeta"><h2>Verificar / dar de alta proveedor (SII)</h2>
{estado_cuota}
<form method="post" action="/proveedor">
<p>RUT: <input name="rut" required placeholder="76123456-7">
Correo comercial: <input name="correo" type="email" placeholder="ventas@…">
Nombre fantasía: <input name="fantasia" placeholder="(opcional)"></p>
<p>{_selector_operador(config)}
<label><input type="checkbox" name="mock" value="1"> prueba (sin gastar
cuota)</label>
<button>Verificar en el SII</button></p></form>
<p><small>APTO-SII habilita al proveedor para OC y nómina. El registro
fechado queda en la bitácora de verificaciones.</small></p></div>"""
    return pagina("Proveedores", cuerpo, "/proveedor")


def vista_presupuesto():
    pres = cargar_presupuesto()
    sols = cargar_solicitudes()
    config = cargar_config()
    filas = []
    for cc in sorted(set(list(pres) + CENTROS_DE_COSTO)):
        inicial = parse_monto(pres.get(cc, {}).get("inicial", 0))
        comp = comprometido_por_cc(sols, cc)
        saldo = inicial - comp
        clase = "err" if inicial and saldo < 0 else ""
        filas.append(
            f"<tr><th>{html.escape(cc)}</th>"
            f'<td><input name="cc_{html.escape(cc)}" value="{inicial}" '
            'style="width:8em;text-align:right"></td>'
            f"<td style='text-align:right'>${comp:,.0f}</td>"
            f"<td style='text-align:right' class='{clase}'>${saldo:,.0f}</td></tr>"
            .replace(",", "."))
    cuerpo = f"""<div class="tarjeta"><h2>Presupuesto por centro de costo</h2>
<p><small>Saldo inicial en CLP (0 = sin control para ese CC). El
comprometido se calcula solo, con las solicitudes aprobadas en el
portal.</small></p>
<form method="post" action="/presupuesto">
<table><tr><th>Centro de costo</th><th>Saldo inicial</th>
<th>Comprometido</th><th>Disponible</th></tr>{''.join(filas)}</table>
<p>Agregar CC: <input name="nuevo_cc" placeholder="nombre">
monto <input name="nuevo_monto" style="width:8em"></p>
<p>{_selector_operador(config)} <button>Guardar presupuesto</button></p>
</form></div>"""
    return pagina("Presupuesto", cuerpo, "/presupuesto")


def vista_txt(mensaje="", extra=""):
    config = cargar_config()
    aviso = f'<div class="error">{html.escape(mensaje)}</div>' if mensaje else ""
    cuerpo = f"""{aviso}{extra}
<div class="tarjeta"><h2>Validar TXT de nómina (Banco de Chile)</h2>
<form method="post" action="/txt" enctype="multipart/form-data">
<p><input type="file" name="archivo" accept=".txt" required></p>
<p>Fecha de abono (opcional, corrige el encabezado):
<input name="fecha_pago" placeholder="DD-MM-AAAA" style="width:9em"></p>
<p>{_selector_operador(config)} <button>Validar</button></p></form>
<p><small>Si hay ERRORES, no cargar al banco: corregir en Manager+ y
regenerar el TXT.</small></p></div>"""
    return pagina("TXT banco", cuerpo, "/txt")


def vista_bitacora():
    filas = "".join(
        f"<tr><td>{html.escape(x['fecha'])}</td><td>{html.escape(x['evento'])}"
        f"</td><td>{html.escape(x['detalle'])}</td>"
        f"<td>{html.escape(x.get('operador', ''))}</td></tr>"
        for x in reversed(leer_bitacora()[-200:]))
    cuerpo = ("<div class='tarjeta'><h2>Bitácora</h2><table><tr><th>Fecha"
              "</th><th>Evento</th><th>Detalle</th><th>Operador</th></tr>"
              f"{filas}</table></div>")
    return pagina("Bitácora", cuerpo, "/bitacora")


# ---------------------------------------------------------------- arranque


def ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def cargar_clave_simpleapi():
    """El doble clic no hereda las variables del shell: si no está
    SIMPLEAPI_API_KEY, la lee de clave_simpleapi.txt junto al portal
    (archivo local del equipo anfitrión; excluido del repositorio)."""
    import os
    if os.environ.get("SIMPLEAPI_API_KEY"):
        return True
    archivo = BASE / "clave_simpleapi.txt"
    if archivo.exists():
        clave = archivo.read_text(encoding="utf-8").strip()
        if clave:
            os.environ["SIMPLEAPI_API_KEY"] = clave
            return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="Portal Puente MS")
    ap.add_argument("--puerto", type=int, default=8765)
    ap.add_argument("--sin-navegador", action="store_true")
    args = ap.parse_args(argv)
    cargar_config()                      # crea config.json la primera vez
    if not cargar_clave_simpleapi():
        print("AVISO: falta la clave de SimpleAPI. Crear el archivo "
              "clave_simpleapi.txt (junto a portal.py) con la clave "
              "adentro, o exportar SIMPLEAPI_API_KEY. Sin ella, la "
              "verificación SII solo funciona en modo prueba.")
    servidor = ThreadingHTTPServer(("0.0.0.0", args.puerto), Portal)
    print("=" * 56)
    print("  Portal Puente MS — en marcha")
    print(f"  En este equipo:   http://localhost:{args.puerto}")
    print(f"  Desde la red MS:  http://{ip_local()}:{args.puerto}")
    print("  Para detenerlo: cerrar esta ventana (o Ctrl+C)")
    print("=" * 56)
    if not args.sin_navegador:
        webbrowser.open(f"http://localhost:{args.puerto}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
