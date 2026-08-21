#!/usr/bin/env python3
"""Portal Puente MS — flujo de compras y proveedores sin Terminal.

Aplicación web LOCAL para los colaboradores de MundoSocios: corre en un
computador (Mac o Windows) y el resto del equipo la usa desde el
navegador por red local. No reemplaza a Zoho (formularios, adjuntos y
APROBACIONES) ni a Manager+ (registro contable): cubre el tramo
intermedio del puente.

Módulos (v2, cambios MundoSocios 2026-08-19):
  1. Bandeja de solicitudes — se alimenta pegando el registro de Zoho o
     importando el export CSV. Checklist de VERIFICACIÓN (no aprueba por
     monto: la aprobación viene de Zoho): campos obligatorios, RUT
     válido, proveedor APTO (ficha completa), estado en Zoho,
     cotizaciones (informativo) y saldo presupuestario del CC.
     Registro de la OC emitida en Manager+ (N°, fecha, neto/IVA/total,
     expediente) según la Plantilla OC.
  2. Proveedores — verificación SII (SimpleAPI) + FICHA COMPLETA del
     proveedor (checklist de campos críticos v2.0: identificación,
     representantes, DTE, datos bancarios, condiciones). Regla de
     avance: APTO solo con SII vigente y datos bancarios completos.
     Para proveedor nuevo genera el documento de carga a Manager+.
  3. Presupuesto por centro de costo (saldo inicial − comprometido).
  4. Bitácora de todo.

(El validador del TXT bancario se quitó del portal por decisión
MundoSocios 2026-08-19: el TXT de pago no se usará. La herramienta
sigue disponible aparte en ../validador-txt-banco.)

Uso (el equipo NO usa esto: usa el doble clic de Iniciar_Portal):
    python3 portal.py            # abre en http://localhost:8765

Sin dependencias externas: Python 3.9+ puro.
"""

import argparse
import csv
import html
import io
import json
import os
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
if RUTA_SII.is_dir():
    sys.path.insert(0, str(RUTA_SII))

try:
    import alta_proveedor
    import cliente_simpleapi
except Exception:            # el portal funciona igual sin el módulo SII
    alta_proveedor = cliente_simpleapi = None

# ---------------------------------------------------------------- reglas

CENTROS_DE_COSTO = ["MUNDO DESARROLLO", "MUNDO SALUD", "MUNDO ENCUENTRO",
                    "FOCO SOCIO", "ADMINISTRACIÓN", "MUNDO DIGITAL",
                    "MUNDO FUTURO"]

OPERADORES_INICIALES = [
    {"nombre": "Cecilia Ramírez", "rol": "COMPRAS"},
    {"nombre": "Patricio Fernández", "rol": "AYF"},
    {"nombre": "Constanza Daniels", "rol": "GG"},
    {"nombre": "Marcos Ibarra", "rol": "OPERADOR"},
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

# Ficha de proveedor (checklist de campos críticos v2.0 — espejo de
# 01_Ficha_Proveedor_MundoSocios). (clave, etiqueta, sección, ¿bloqueante?)
CAMPOS_FICHA = [
    ("rut", "RUT", "1. Identificación", True),
    ("razon_social", "Razón social", "1. Identificación", True),
    ("nombre_fantasia", "Nombre de fantasía", "1. Identificación", False),
    ("giro", "Giro / actividad", "1. Identificación", True),
    ("correo", "Correo", "1. Identificación", True),
    ("direccion", "Dirección", "1. Identificación", False),
    ("comuna", "Comuna", "1. Identificación", False),
    ("ciudad", "Ciudad", "1. Identificación", False),
    ("region", "Región", "1. Identificación", False),
    ("pais", "País", "1. Identificación", False),
    ("telefono", "Teléfono", "1. Identificación", False),
    ("rep1_nombre", "Rep. legal 1: nombre", "2. Representantes", False),
    ("rep1_rut", "Rep. legal 1: RUT", "2. Representantes", False),
    ("rep1_correo", "Rep. legal 1: correo", "2. Representantes", False),
    ("rep1_telefono", "Rep. legal 1: teléfono", "2. Representantes", False),
    ("rep2_nombre", "Rep. legal 2: nombre", "2. Representantes", False),
    ("rep2_rut", "Rep. legal 2: RUT", "2. Representantes", False),
    ("tipo_dte", "Tipo de DTE que emite", "3. Documento tributario", True),
    ("banco", "Banco", "4. Datos bancarios", True),
    ("tipo_cuenta", "Tipo de cuenta", "4. Datos bancarios", True),
    ("numero_cuenta", "Número de cuenta", "4. Datos bancarios", True),
    ("email_aviso_pago", "Email para aviso de pago", "4. Datos bancarios", True),
    ("forma_pago", "Forma de pago", "5. Condiciones", False),
    ("plazo_pago", "Plazo de pago (días)", "5. Condiciones", False),
    ("moneda", "Moneda", "5. Condiciones", False),
    ("contacto_nombre", "Contacto: nombre", "6. Contacto (Manager+)", False),
    ("contacto_cargo", "Contacto: cargo", "6. Contacto (Manager+)", False),
    ("contacto_correo", "Contacto: correo", "6. Contacto (Manager+)", False),
    ("contacto_telefono", "Contacto: teléfono", "6. Contacto (Manager+)", False),
    ("contacto_saludo", "Contacto: saludo (Estimado/a)", "6. Contacto (Manager+)", False),
]

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


def clp(monto):
    return "$" + format(int(monto), ",.0f").replace(",", ".")


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


def cargar_proveedores():
    return _leer_json("proveedores.json", {})


def guardar_proveedores(p):
    _escribir_json("proveedores.json", p)


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
    """Parsea la vista de un registro de Zoho pegada como texto."""
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


# ---------------------------------------------------------------- ficha desde archivo

# Estructura de la Ficha de Proveedor oficial
# (Ficha_Proveedor_MundoSocios_CChC_2026.xlsx): etiquetas por sección;
# el valor está en la celda/texto siguiente.
MAPA_FICHA_ARCHIVO = {
    "DATOS TRIBUTARIOS": {
        "RUT": "rut", "RAZON SOCIAL": "razon_social",
        "NOMBRE DE FANTASIA": "nombre_fantasia", "GIRO": "giro",
        "CORREO": "correo", "DIRECCION": "direccion", "COMUNA": "comuna",
        "CIUDAD": "ciudad", "REGION": "region", "PAIS": "pais",
        "TELEFONO": "telefono"},
    "REPRESENTANTE LEGAL 1": {
        "NOMBRE COMPLETO": "rep1_nombre", "RUT": "rep1_rut",
        "CORREO": "rep1_correo", "TELEFONO": "rep1_telefono"},
    "REPRESENTANTE LEGAL 2": {
        "NOMBRE COMPLETO": "rep2_nombre", "RUT": "rep2_rut"},
    "CONTACTO COMERCIAL": {
        "NOMBRE COMPLETO": "contacto_nombre", "CARGO": "contacto_cargo",
        "CORREO": "contacto_correo", "TELEFONO": "contacto_telefono"},
    "TIPO DE DOCUMENTO": {"DTE": "tipo_dte"},
    "DATOS BANCARIOS": {
        "BANCO": "banco", "CUENTA": "tipo_cuenta",
        "TIPO DE CUENTA": "tipo_cuenta", "NRO": "numero_cuenta"},
}
# Toda etiqueta conocida (de cualquier sección): nunca es un valor.
_ETIQUETAS_FICHA = {e for m in MAPA_FICHA_ARCHIVO.values() for e in m}


def _etiqueta(texto):
    return _sin_tildes(str(texto or "")).upper().strip().rstrip(":").strip()


def _seccion_de(texto):
    plano = _etiqueta(texto)
    for seccion in MAPA_FICHA_ARCHIVO:
        if plano.startswith(seccion):
            return seccion
    return None


def _leer_celdas_xlsx(binario):
    """Lector .xlsx mínimo (librería estándar): devuelve las filas de la
    hoja de la ficha como listas de valores en orden de columna."""
    import xml.etree.ElementTree as ET
    import zipfile
    NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(binario)) as z:
        compartidos = []
        if "xl/sharedStrings.xml" in z.namelist():
            raiz = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in raiz.iter(f"{NS}si"):
                compartidos.append("".join(t.text or ""
                                           for t in si.iter(f"{NS}t")))
        hojas = sorted(n for n in z.namelist()
                       if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))
        mejor = None
        for nombre in hojas:
            raiz = ET.fromstring(z.read(nombre))
            filas = {}
            for c in raiz.iter(f"{NS}c"):
                ref = c.get("r", "")
                m = re.match(r"([A-Z]+)(\d+)", ref)
                if not m:
                    continue
                col = sum((ord(l) - 64) * 26 ** i
                          for i, l in enumerate(reversed(m.group(1))))
                tipo = c.get("t", "")
                if tipo == "s":
                    v = c.find(f"{NS}v")
                    valor = (compartidos[int(v.text)]
                             if v is not None and v.text else "")
                elif tipo == "inlineStr":
                    valor = "".join(t.text or "" for t in c.iter(f"{NS}t"))
                else:
                    v = c.find(f"{NS}v")
                    valor = v.text if v is not None and v.text else ""
                if str(valor).strip():
                    filas.setdefault(int(m.group(2)), []).append(
                        (col, str(valor).strip()))
            listado = [[v for _, v in sorted(filas[n])] for n in sorted(filas)]
            texto = " ".join(v for fila in listado for v in fila).upper()
            if "FICHA PROVEEDOR" in _sin_tildes(texto):
                return listado
            if mejor is None and listado:
                mejor = listado
        return mejor or []


def _texto_pdf(binario):
    """Extracción de texto best-effort de un PDF de texto (como el que
    sale de imprimir/exportar la ficha Excel a PDF)."""
    import zlib
    piezas = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", binario, re.S):
        datos = m.group(1)
        try:
            datos = zlib.decompress(datos)
        except Exception:
            pass
        if b"BT" not in datos:
            continue
        for t in re.finditer(rb"\((?:\\.|[^\\()])*\)", datos):
            crudo = t.group(0)[1:-1]
            crudo = re.sub(rb"\\([0-7]{1,3})",
                           lambda x: bytes([int(x.group(1), 8) & 0xFF]),
                           crudo)
            crudo = (crudo.replace(rb"\(", b"(").replace(rb"\)", b")")
                     .replace(rb"\\", b"\\"))
            texto = crudo.decode("latin-1", "replace").strip()
            if texto:
                piezas.append(texto)
    return piezas


def _parsear_items_ficha(items):
    """Recorre una secuencia de textos (celdas o líneas del PDF) y arma
    el dict de la ficha por sección → etiqueta → valor siguiente."""
    datos = {}
    seccion = None
    i = 0
    while i < len(items):
        texto = items[i]
        s = _seccion_de(texto)
        if s:
            seccion = s
            i += 1
            continue
        if seccion:
            etiquetas = MAPA_FICHA_ARCHIVO[seccion]
            clave = etiquetas.get(_etiqueta(texto))
            if clave and i + 1 < len(items):
                siguiente = items[i + 1]
                if not _seccion_de(siguiente) \
                        and _etiqueta(siguiente) not in _ETIQUETAS_FICHA:
                    if clave not in datos:
                        datos[clave] = str(siguiente).strip()
                    i += 2
                    continue
        i += 1
    return datos


def parsear_ficha_archivo(nombre, binario):
    """Carga la Ficha de Proveedor desde .xlsx o .pdf → dict de campos.
    Lanza RuntimeError con mensaje claro si no se puede leer."""
    extension = Path(nombre).suffix.lower()
    if extension == ".xlsx":
        filas = _leer_celdas_xlsx(binario)
        items = [v for fila in filas for v in fila]
    elif extension == ".pdf":
        items = _texto_pdf(binario)
        if not items:
            raise RuntimeError(
                "No se pudo extraer texto del PDF (¿es un escaneo?). "
                "Usar la ficha en Excel, o un PDF exportado desde Excel.")
    else:
        raise RuntimeError("Formato no soportado: usar .xlsx o .pdf")
    datos = _parsear_items_ficha(items)
    if not datos.get("rut"):
        raise RuntimeError(
            "El archivo no trae el RUT del proveedor (¿es la Ficha de "
            "Proveedor MundoSocios?). Revisar el archivo o digitar a mano.")
    return datos


# ---------------------------------------------------------------- proveedores


def verificacion_sii(rut):
    """Última verificación SII del RUT en la bitácora del módulo de alta.
    → ('APTO-SII'|'NO APTO'|None, fecha)."""
    ruta = RUTA_SII / "verificaciones" / "registro_verificaciones.csv"
    if not ruta.exists():
        return None, ""
    ultimo = (None, "")
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            if fila.get("rut") == rut:
                ultimo = (fila.get("resultado"), fila.get("fecha", ""))
    return ultimo


def evaluar_ficha(ficha):
    """Regla de avance del checklist v2.0: APTO solo con verificación SII
    vigente Y todos los campos bloqueantes (bancarios incluidos)
    completos. → (estado, faltantes)."""
    faltantes = [etiqueta for clave, etiqueta, _, bloqueante in CAMPOS_FICHA
                 if bloqueante and not str(ficha.get(clave, "")).strip()]
    if ficha.get("sii_resultado") != "APTO-SII":
        faltantes.insert(0, "Verificación SII vigente (APTO-SII)")
    return ("APTO" if not faltantes else "EN VALIDACIÓN"), faltantes


def estado_proveedor(rut):
    """Estado del proveedor para el checklist de solicitudes.
    → (estado, detalle): APTO (ficha completa) · FICHA-INCOMPLETA ·
    SOLO-SII · NO-APTO-SII · None."""
    fichas = cargar_proveedores()
    ficha = fichas.get(rut)
    if ficha:
        estado, faltantes = evaluar_ficha(ficha)
        if estado == "APTO":
            return "APTO", f"ficha completa ({ficha.get('actualizado', '')})"
        return "FICHA-INCOMPLETA", "faltan: " + ", ".join(faltantes[:4])
    sii, fecha = verificacion_sii(rut)
    if sii == "APTO-SII":
        return "SOLO-SII", f"verificado SII {fecha}, sin ficha completa"
    if sii == "NO APTO":
        return "NO-APTO-SII", f"verificación SII {fecha}"
    return None, ""


# ---------------------------------------------------------------- checklist

ESTADOS_COMPROMETEN = ("PROCESADA", "APROBADA", "APROBADA-EXCEPCION")


def comprometido_por_cc(solicitudes, cc, excepto=None):
    total = 0
    for sid, s in solicitudes.items():
        if sid == excepto:
            continue
        if s.get("estado_portal", "") in ESTADOS_COMPROMETEN \
                and s.get("datos", {}).get("centro_costo") == cc:
            total += parse_monto(s["datos"].get("valor_total"))
    return total


def evaluar_solicitud(datos, solicitudes=None, presupuesto=None,
                      id_actual=None):
    """Checklist de VERIFICACIÓN de una solicitud. La aprobación por
    monto NO se hace aquí: viene de Zoho (Estado de solicitud)."""
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

    proveedor = (None, "")
    if rut and rut_valido(rut):
        proveedor = estado_proveedor(rut)
        estado_p, detalle_p = proveedor
        if estado_p == "APTO":
            avisos.append(f"Proveedor APTO — {detalle_p}")
        elif estado_p == "FICHA-INCOMPLETA":
            errores.append(f"Ficha de proveedor incompleta — {detalle_p}")
        elif estado_p == "SOLO-SII":
            errores.append(f"Proveedor {detalle_p}: completar la ficha en "
                           "la pestaña Proveedores antes de la OC")
        elif estado_p == "NO-APTO-SII":
            errores.append(f"Proveedor NO APTO en el SII ({detalle_p}) — "
                           "no puede entrar a OC")
        else:
            errores.append("Proveedor sin verificación ni ficha: crearlo en "
                           "la pestaña Proveedores")

    # La aprobación viene de Zoho: aquí solo se refleja.
    estado_zoho = str(datos.get("estado_zoho", "")).strip()
    if estado_zoho:
        if _sin_tildes(estado_zoho).lower() == "aprobado":
            avisos.append("Aprobada en Zoho")
        else:
            errores.append(f"Aún no aprobada en Zoho (estado: {estado_zoho})")
    else:
        avisos.append("Sin estado de Zoho en los datos pegados — confirmar "
                      "la aprobación en Zoho antes de la OC")

    posee = _sin_tildes(str(datos.get("posee_ambas_cotizaciones", ""))).strip().lower()
    if posee != "si":
        motivo = datos.get("motivo_seleccion") or datos.get("motivo_proveedor") or ""
        avisos.append("Sin ambas cotizaciones (la excepción la aprueba Adm. "
                      "y Finanzas o la Gerencia en Zoho)"
                      + (f" — motivo declarado: {motivo}" if motivo else
                         " — SIN motivo declarado"))

    monto = parse_monto(datos.get("valor_total"))
    cc = datos.get("centro_costo", "")
    sin_saldo = False
    if cc:
        info_cc = presupuesto.get(cc)
        if info_cc and parse_monto(info_cc.get("inicial")) > 0:
            saldo = parse_monto(info_cc.get("inicial")) - \
                comprometido_por_cc(solicitudes, cc, excepto=id_actual)
            if monto > saldo:
                sin_saldo = True
                avisos.append(f"SIN saldo presupuestario en {cc} (saldo "
                              f"{clp(saldo)} vs {clp(monto)}): corresponde "
                              "ampliación/reasignación aprobada por la Gerencia")
            else:
                avisos.append(f"Presupuesto {cc}: saldo disponible {clp(saldo)}")
        else:
            avisos.append(f"Centro de costo {cc} sin presupuesto cargado "
                          "(pestaña Presupuesto) — chequeo omitido")

    return {"errores": errores, "avisos": avisos, "monto": monto,
            "sin_saldo": sin_saldo, "proveedor": proveedor[0] or ""}


# ---------------------------------------------------------------- documentos


def _guardar_doc(nombre, contenido):
    carpeta = DATOS / "manager"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre
    if isinstance(contenido, bytes):
        ruta.write_bytes(contenido)
    else:
        ruta.write_text(contenido, encoding="utf-8-sig")
    return nombre


def _col_letra(n):
    letras = ""
    while n:
        n, resto = divmod(n - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def generar_xlsx(filas, hoja="Hoja1"):
    """Genera un .xlsx mínimo (una hoja) solo con la librería estándar."""
    import zipfile

    def celda(ref, valor):
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            return f'<c r="{ref}" t="n"><v>{valor}</v></c>'
        texto = html.escape(str(valor), quote=False)
        return (f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">'
                f"{texto}</t></is></c>")

    filas_xml = []
    for i, fila in enumerate(filas, 1):
        celdas = "".join(celda(f"{_col_letra(j)}{i}", v)
                         for j, v in enumerate(fila, 1) if v != "")
        filas_xml.append(f'<row r="{i}">{celdas}</row>')
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/'
             'spreadsheetml/2006/main"><sheetData>'
             + "".join(filas_xml) + "</sheetData></worksheet>")
    workbook = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/'
                'spreadsheetml/2006/main" xmlns:r="http://schemas.'
                'openxmlformats.org/officeDocument/2006/relationships">'
                f'<sheets><sheet name="{hoja}" sheetId="1" r:id="rId1"/>'
                "</sheets></workbook>")
    rels_wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/'
               'package/2006/relationships"><Relationship Id="rId1" '
               'Type="http://schemas.openxmlformats.org/officeDocument/'
               '2006/relationships/worksheet" Target="worksheets/'
               'sheet1.xml"/></Relationships>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships"><Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>")
    tipos = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Types xmlns="http://schemas.openxmlformats.org/package/'
             '2006/content-types"><Default Extension="rels" ContentType='
             '"application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/xl/workbook.xml" ContentType='
             '"application/vnd.openxmlformats-officedocument.spreadsheetml'
             '.sheet.main+xml"/><Override PartName="/xl/worksheets/'
             'sheet1.xml" ContentType="application/vnd.openxmlformats-'
             'officedocument.spreadsheetml.worksheet+xml"/></Types>')
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", tipos)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", rels_wb)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return salida.getvalue()


# Formato OFICIAL de carga masiva de Manager+ "Cliente y Proveedores"
# (Cliente_y_Proveedores_formatos_1.xlsx, 37 columnas).
COLUMNAS_MANAGER = [
    "RUT", "Razón social", "Nombre de fantasía", "Giro", "RUT Holding",
    "Area de Producción", "Clasificación", "Email", "Email SII",
    "Comentario", "Tipo cliente", "Tipo proveedor", "Vencimiento",
    "Plazo de pago", "Código vendedor", "Código comisionista",
    "Código cobrador", "Lista de precio", "Comentario empresa",
    "Descripción dirección", "Dirección", "Código comuna", "Código ciudad",
    "Atención contacto", "Email contacto", "Teléfono", "Teléfono 2",
    "Cuenta Banco", "Cuenta Tipo", "N° de Cuenta", "ID Extranjero",
    "Texto 1", "Texto 2", "Código de Característica 1",
    "Código de Característica 2", "Monto de Crédito autorizado",
    "Días de mora"]


def codigo_tipo_cuenta(texto):
    """Manager+: 1=Cuenta vista, 2=Cuenta de ahorro, 3=Cuenta corriente,
    4=Vale vista."""
    plano = _sin_tildes(str(texto or "")).lower()
    if "corriente" in plano:
        return 3
    if "ahorro" in plano:
        return 2
    if "vale" in plano:
        return 4
    if "vista" in plano:
        return 1
    return ""


def codigo_tipo_proveedor(ficha):
    """Manager+: N/P/H/E/A. Honorarios si el DTE o el tipo sugerido lo
    indican; si no, P=Proveedor."""
    texto = _sin_tildes(f"{ficha.get('tipo_dte', '')} "
                        f"{ficha.get('tipo_proveedor', '')}").lower()
    return "H" if "honorario" in texto else "P"


def fila_manager_proveedor(ficha):
    """Mapea la ficha del portal a las 37 columnas del formato oficial."""
    comentario = (f"Alta Portal Puente MS — verificación SII "
                  f"{ficha.get('sii_resultado', '')} "
                  f"{ficha.get('sii_fecha', '')}").strip()
    valores = {
        "RUT": ficha.get("rut", ""),
        "Razón social": ficha.get("razon_social", ""),
        "Nombre de fantasía": ficha.get("nombre_fantasia")
        or ficha.get("razon_social", ""),
        "Giro": ficha.get("giro", ""),
        "Email": ficha.get("correo", ""),
        "Email SII": ficha.get("correo_sii", ""),
        "Comentario": comentario,
        "Tipo cliente": "N",
        "Tipo proveedor": codigo_tipo_proveedor(ficha),
        "Plazo de pago": ficha.get("plazo_pago", ""),
        "Descripción dirección": "Comercial",
        "Dirección": ficha.get("direccion", ""),
        "Código comuna": ficha.get("comuna", ""),
        "Código ciudad": ficha.get("ciudad", ""),
        "Atención contacto": ficha.get("contacto_nombre", ""),
        "Email contacto": ficha.get("contacto_correo", ""),
        "Teléfono": ficha.get("telefono", ""),
        "Teléfono 2": ficha.get("contacto_telefono", ""),
        "Cuenta Banco": ficha.get("banco", ""),
        "Cuenta Tipo": codigo_tipo_cuenta(ficha.get("tipo_cuenta")),
        "N° de Cuenta": ficha.get("numero_cuenta", ""),
    }
    return [valores.get(c, "") for c in COLUMNAS_MANAGER]


def documento_manager_proveedor(ficha):
    """Archivo de carga a Manager+ (formato oficial 37 columnas, .xlsx):
    fila 1 encabezados, fila 2 datos del proveedor."""
    return generar_xlsx([COLUMNAS_MANAGER, fila_manager_proveedor(ficha)],
                        hoja="Hoja1")


def archivo_manager_solicitud(datos, evaluacion, oc=None):
    """CSV de la solicitud (y su OC si está registrada) para digitar en
    Manager+."""
    rut = datos.get("rut_normalizado") or normalizar_rut(
        datos.get("rut_proveedor", ""))
    salida = io.StringIO()
    w = csv.writer(salida, delimiter=";")
    w.writerow(["BLOQUE", "CAMPO", "VALOR"])
    filas = [("Solicitud Zoho", datos.get("actividad", "")),
             ("Solicitante", datos.get("solicitante")
              or datos.get("creado_por", "")),
             ("Estado Zoho", datos.get("estado_zoho", "")),
             ("Centro de costo", datos.get("centro_costo", "")),
             ("Cuenta contable", datos.get("cuenta_contable", "")),
             ("Proveedor", datos.get("razon_social", "")),
             ("RUT proveedor", rut),
             ("Glosa / detalle", datos.get("detalle", "")),
             ("Monto total (c/IVA)", evaluacion.get("monto", "")),
             ("Fecha acuerdo de pago", datos.get("fecha_pago", ""))]
    for campo, valor in filas:
        w.writerow(["SOLICITUD", campo, valor])
    if oc:
        for campo, valor in [("N° OC (Manager+)", oc.get("numero", "")),
                             ("Fecha emisión", oc.get("fecha", "")),
                             ("Neto", oc.get("neto", "")),
                             ("IVA (19%)", oc.get("iva", "")),
                             ("TOTAL bruto", oc.get("total", "")),
                             ("Expediente SharePoint",
                              oc.get("expediente", "")),
                             ("Registrada por", oc.get("operador", ""))]:
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
.chip{display:inline-block;padding:.1em .6em;border-radius:1em;font-size:.85em;font-weight:600}
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
.grilla{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:.5em 1em}
.grilla label{display:flex;flex-direction:column;font-size:.88em;color:#444}
</style>"""


def pagina(titulo, cuerpo, pestana=""):
    tabs = [("/", "Solicitudes"), ("/nueva", "Ingresar solicitud"),
            ("/proveedor", "Proveedores"), ("/presupuesto", "Presupuesto"),
            ("/bitacora", "Bitácora")]
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
    clases = {"LISTA": "c-lista", "INCOMPLETA": "c-inc",
              "PROCESADA": "c-apr", "OBSERVADA": "c-exc", "APTO": "c-lista",
              "EN VALIDACIÓN": "c-exc"}
    return f'<span class="chip {clases.get(estado, "c-rec")}">{estado}</span>'


def _selector_operador(config, nombre_campo="operador"):
    ops = "".join(f'<option>{html.escape(o["nombre"])}</option>'
                  for o in config["operadores"])
    return (f'<select name="{nombre_campo}" required>'
            f'<option value="">— ¿quién opera? —</option>{ops}</select>')


# ---------------------------------------------------------------- servidor


def _leer_cuerpo(handler):
    largo = int(handler.headers.get("Content-Length", 0))
    return handler.rfile.read(largo)


def _parse_multipart(cuerpo, content_type):
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
        q = {k: v[0] for k, v in parse_qs(ruta.query).items()}
        try:
            if ruta.path == "/":
                self._responder(vista_tablero())
            elif ruta.path == "/nueva":
                self._responder(vista_nueva())
            elif ruta.path.startswith("/solicitud/"):
                self._responder(vista_solicitud(ruta.path.split("/")[2]))
            elif ruta.path.startswith("/manager/"):
                self._descargar_manager_solicitud(
                    ruta.path.split("/")[2].replace(".xlsx", "").replace(".csv", ""))
            elif ruta.path == "/proveedor":
                self._responder(vista_proveedores())
            elif ruta.path == "/ficha":
                self._responder(vista_ficha(q.get("rut", "")))
            elif ruta.path.startswith("/manager_proveedor/"):
                self._descargar_manager_proveedor(
                    ruta.path.split("/")[2].replace(".xlsx", "").replace(".csv", ""))
            elif ruta.path == "/presupuesto":
                self._responder(vista_presupuesto())
            elif ruta.path == "/bitacora":
                self._responder(vista_bitacora())
            else:
                self._responder("No existe", codigo=404)
        except Exception as e:
            self._responder(pagina("Error", f'<div class="error">Error '
                                   f'interno: {html.escape(str(e))}</div>'),
                            codigo=500)

    def _descargar_manager_solicitud(self, sid):
        sols = cargar_solicitudes()
        s = sols.get(sid)
        if not s:
            self._responder("No existe", codigo=404)
            return
        contenido = archivo_manager_solicitud(
            s["datos"], s.get("evaluacion", {}), s.get("oc"))
        nombre = f"CARGA_MANAGER_SOLICITUD_{sid}_{datetime.now():%Y%m%d-%H%M}.csv"
        _guardar_doc(nombre, contenido)
        bitacora("archivo_manager", f"solicitud {sid} → {nombre}")
        self._responder(contenido.encode("utf-8-sig"),
                        "text/csv; charset=utf-8", descarga=nombre)

    def _descargar_manager_proveedor(self, rut):
        ficha = cargar_proveedores().get(rut)
        if not ficha:
            self._responder("No existe", codigo=404)
            return
        contenido = documento_manager_proveedor(ficha)
        nombre = (f"CARGA_MANAGER_PROVEEDOR_{rut}_"
                  f"{datetime.now():%Y%m%d-%H%M}.xlsx")
        _guardar_doc(nombre, contenido)
        bitacora("archivo_manager_proveedor", f"{rut} → {nombre}")
        self._responder(contenido,
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet", descarga=nombre)

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
            elif ruta == "/oc":
                self._post_oc(campos)
            elif ruta == "/verificar":
                self._post_verificar(campos)
            elif ruta == "/cargar_ficha":
                self._post_cargar_ficha(campos, archivos)
            elif ruta == "/ficha":
                self._post_ficha(campos)
            elif ruta == "/presupuesto":
                self._post_presupuesto(campos)
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
        """Marca el resultado de la VERIFICACIÓN (no aprueba montos:
        eso viene de Zoho)."""
        sid = campos.get("id", "")
        accion = campos.get("accion", "")
        operador = campos.get("operador", "")
        sols = cargar_solicitudes()
        s = sols.get(sid)
        if not s or not operador:
            self._redirigir(f"/solicitud/{sid}")
            return
        ev = evaluar_solicitud(s["datos"], sols, cargar_presupuesto(), sid)
        s["evaluacion"] = ev
        if accion == "procesar":
            if ev["errores"]:
                s["nota"] = ("No se puede marcar procesada: el checklist "
                             "tiene errores pendientes.")
            else:
                s["estado_portal"] = "PROCESADA"
                s["nota"] = ""
                s["decisiones"].append({"fecha": ahora(), "operador": operador,
                                        "decision": "PROCESADA"})
                bitacora("solicitud_procesada", sid, operador)
        elif accion == "observar":
            s["estado_portal"] = "OBSERVADA"
            s["nota"] = campos.get("nota", "")
            s["decisiones"].append({"fecha": ahora(), "operador": operador,
                                    "decision": "OBSERVADA"})
            bitacora("solicitud_observada", sid, operador)
        elif accion == "eliminar":
            del sols[sid]
            guardar_solicitudes(sols)
            bitacora("solicitud_eliminada", sid, operador)
            self._redirigir("/")
            return
        guardar_solicitudes(sols)
        self._redirigir(f"/solicitud/{sid}")

    def _post_oc(self, campos):
        """Registra la OC emitida en Manager+ (Plantilla OC)."""
        sid = campos.get("id", "")
        sols = cargar_solicitudes()
        s = sols.get(sid)
        if not s:
            self._redirigir("/")
            return
        neto = parse_monto(campos.get("neto"))
        iva = round(neto * 0.19)
        s["oc"] = {"numero": campos.get("numero", "").strip(),
                   "fecha": campos.get("fecha", "").strip(),
                   "neto": neto, "iva": iva, "total": neto + iva,
                   "expediente": campos.get("expediente", "").strip(),
                   "operador": campos.get("operador", ""),
                   "registrada": ahora()}
        guardar_solicitudes(sols)
        bitacora("oc_registrada",
                 f"solicitud {sid} → OC {s['oc']['numero']} "
                 f"total {clp(s['oc']['total'])}", campos.get("operador", ""))
        self._redirigir(f"/solicitud/{sid}")

    def _post_verificar(self, campos):
        """Paso 1 del alta: verificación SII. Deja el borrador de ficha
        pre-llenado con los datos del SII."""
        if alta_proveedor is None:
            self._responder(vista_proveedores(
                "El módulo sii-simpleapi no está junto al portal."))
            return
        rut = normalizar_rut(campos.get("rut", ""))
        try:
            datos, origen = cliente_simpleapi.consultar_rut(
                rut, mock=bool(campos.get("mock")))
        except RuntimeError as e:
            self._responder(vista_proveedores(str(e)))
            return

        class _Args:
            correo_comercial = campos.get("correo", "")
            nombre_fantasia = campos.get("fantasia", "")
        estado, tipo, obs = alta_proveedor.evaluar(datos)
        campos_m = alta_proveedor.campos_manager(datos, _Args)
        alta_proveedor.escribir_registro(datos, origen, estado, obs, campos_m)
        bitacora("verificacion_sii", f"{rut}: {estado} [{origen}]",
                 campos.get("operador", ""))

        fichas = cargar_proveedores()
        ficha = fichas.get(rut, {})
        actividades = datos.get("actividadesEconomicas") or []
        dom = (datos.get("domicilios") or [{}])[0]
        ficha.update({
            "rut": rut,
            "razon_social": datos.get("razonSocial", ficha.get("razon_social", "")),
            "nombre_fantasia": campos.get("fantasia")
            or ficha.get("nombre_fantasia") or datos.get("razonSocial", ""),
            "giro": (actividades[0]["descripcion"] if actividades
                     else ficha.get("giro", "")),
            "correo": campos.get("correo") or ficha.get("correo", ""),
            "correo_sii": datos.get("correoIntercambio")
            or ficha.get("correo_sii", ""),
            "direccion": dom.get("direccion") or ficha.get("direccion", ""),
            "comuna": dom.get("comuna") or ficha.get("comuna", ""),
            "ciudad": dom.get("ciudad") or ficha.get("ciudad", ""),
            "pais": ficha.get("pais") or "Chile",
            "plazo_pago": ficha.get("plazo_pago") or "30",
            "moneda": ficha.get("moneda") or "CLP",
            "tipo_proveedor": tipo,
            "sii_resultado": estado, "sii_fecha": ahora(),
            "actualizado": ahora(),
        })
        fichas[rut] = ficha
        guardar_proveedores(fichas)
        self._redirigir(f"/ficha?rut={rut}")

    def _post_cargar_ficha(self, campos, archivos):
        """Carga la Ficha de Proveedor desde el archivo Excel o PDF que
        envió el proveedor y abre la ficha del portal para revisar."""
        if "archivo" not in archivos:
            self._responder(vista_proveedores("Selecciona el archivo de la "
                                              "ficha (.xlsx o .pdf)."))
            return
        nombre, binario = archivos["archivo"]
        try:
            datos = parsear_ficha_archivo(nombre, binario)
        except RuntimeError as e:
            self._responder(vista_proveedores(str(e)))
            return
        rut = normalizar_rut(datos.get("rut", ""))
        if not rut or not rut_valido(rut):
            self._responder(vista_proveedores(
                f"El RUT de la ficha no es válido: {datos.get('rut', '')}"))
            return
        fichas = cargar_proveedores()
        ficha = fichas.get(rut, {})
        for clave, valor in datos.items():
            if str(valor).strip():
                ficha[clave] = str(valor).strip()
        ficha["rut"] = rut
        if not ficha.get("email_aviso_pago") and ficha.get("correo"):
            ficha["email_aviso_pago"] = ficha["correo"]
        ficha.setdefault("plazo_pago", "30")
        ficha.setdefault("moneda", "CLP")
        ficha["actualizado"] = ahora()
        ficha["origen_archivo"] = nombre
        fichas[rut] = ficha
        guardar_proveedores(fichas)
        campos_leidos = sum(1 for v in datos.values() if str(v).strip())
        bitacora("ficha_cargada_archivo",
                 f"{rut} ← {nombre} ({campos_leidos} campos)",
                 campos.get("operador", ""))
        self._redirigir(f"/ficha?rut={rut}")

    def _post_ficha(self, campos):
        """Paso 2 del alta: guardar la ficha completa del proveedor."""
        rut = normalizar_rut(campos.get("rut", ""))
        if not rut:
            self._redirigir("/proveedor")
            return
        fichas = cargar_proveedores()
        ficha = fichas.get(rut, {"rut": rut})
        for clave, *_ in CAMPOS_FICHA:
            if clave in campos:
                ficha[clave] = campos[clave].strip()
        ficha["rut"] = rut
        ficha["actualizado"] = ahora()
        fichas[rut] = ficha
        guardar_proveedores(fichas)
        estado, _ = evaluar_ficha(ficha)
        bitacora("ficha_proveedor",
                 f"{rut} {ficha.get('razon_social', '')} → {estado}",
                 campos.get("operador", ""))
        self._redirigir(f"/ficha?rut={rut}")

    def _post_presupuesto(self, campos):
        pres = cargar_presupuesto()
        for clave, valor in campos.items():
            if clave.startswith("cc_"):
                pres.setdefault(clave[3:], {})["inicial"] = parse_monto(valor)
        nuevo = campos.get("nuevo_cc", "").strip()
        if nuevo:
            pres.setdefault(nuevo, {})["inicial"] = \
                parse_monto(campos.get("nuevo_monto", 0))
        guardar_presupuesto(pres)
        bitacora("presupuesto_actualizado", "saldos iniciales",
                 campos.get("operador", ""))
        self._redirigir("/presupuesto")


# ---------------------------------------------------------------- vistas


def vista_tablero():
    sols = cargar_solicitudes()
    filas = []
    for sid in sorted(sols, key=int, reverse=True):
        s = sols[sid]
        d = s["datos"]
        ev = s.get("evaluacion", {})
        oc = s.get("oc", {})
        filas.append(
            f'<tr><td><a href="/solicitud/{sid}">#{sid}</a></td>'
            f"<td>{html.escape(d.get('actividad', ''))}</td>"
            f"<td>{html.escape(d.get('centro_costo', ''))}</td>"
            f"<td style='text-align:right'>{clp(ev.get('monto', 0))}</td>"
            f"<td>{html.escape(d.get('razon_social', ''))}</td>"
            f"<td>{html.escape(oc.get('numero', ''))}</td>"
            f"<td>{_chip(s.get('estado_portal', ''))}</td></tr>")
    tabla = ("<table><tr><th>#</th><th>Actividad</th><th>CC</th>"
             "<th>Monto</th><th>Proveedor</th><th>OC</th><th>Estado</th></tr>"
             + "".join(filas) + "</table>") if filas else \
        "<p>No hay solicitudes. Ingresa la primera en «Ingresar solicitud».</p>"
    return pagina("Solicitudes", f'<div class="tarjeta"><h2>Bandeja de '
                  f'solicitudes de compra</h2>{tabla}</div>', "/")


def vista_nueva(mensaje=""):
    aviso = f'<div class="error">{html.escape(mensaje)}</div>' if mensaje else ""
    cuerpo = f"""{aviso}
<div class="tarjeta"><h2>Opción A — Pegar el registro de Zoho</h2>
<p><small>En Zoho abre el Formulario de Solicitud, selecciona todo el texto
del registro, cópialo y pégalo aquí.</small></p>
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
    rut = d.get("rut_normalizado") or normalizar_rut(d.get("rut_proveedor", ""))
    link_ficha = (f' <a href="/ficha?rut={rut}">ver/completar ficha del '
                  'proveedor</a>' if rut else "")
    acciones = f"""
<form method="post" action="/decidir" class="inline">
<input type="hidden" name="id" value="{sid}">
{_selector_operador(config)}
<button name="accion" value="procesar">Marcar procesada</button>
<button name="accion" value="observar" class="sec">Observar</button>
<input name="nota" placeholder="nota (al observar)" style="width:12em">
<button name="accion" value="eliminar" class="peligro"
 onclick="return confirm('¿Eliminar la solicitud #{sid}?')">Eliminar</button>
</form>
<form method="post" action="/reevaluar" class="inline">
<input type="hidden" name="id" value="{sid}">
<button class="sec">Re-evaluar checklist</button></form>"""
    oc = s.get("oc", {})
    form_oc = f"""<div class="tarjeta"><h3>Registro de OC (Manager+)</h3>
{f"<p>OC <b>{html.escape(oc.get('numero', ''))}</b> del "
 f"{html.escape(oc.get('fecha', ''))} — neto {clp(oc.get('neto', 0))} · "
 f"IVA {clp(oc.get('iva', 0))} · <b>total {clp(oc.get('total', 0))}</b> · "
 f"expediente: {html.escape(oc.get('expediente', '') or '—')} "
 f"<small>(registrada por {html.escape(oc.get('operador', ''))}, "
 f"{html.escape(oc.get('registrada', ''))})</small></p>" if oc else
 "<p><small>Cuando la OC se emita en Manager+, registra aquí su número "
 "(Plantilla OC): queda vinculada a la solicitud y entra al archivo de "
 "carga.</small></p>"}
<form method="post" action="/oc">
<input type="hidden" name="id" value="{sid}">
<p>N° OC: <input name="numero" value="{html.escape(oc.get('numero', ''))}" style="width:8em" required>
Fecha emisión: <input name="fecha" value="{html.escape(oc.get('fecha', ''))}" placeholder="DD-MM-AAAA" style="width:8em">
Neto: <input name="neto" value="{oc.get('neto', '')}" style="width:8em">
<small>(IVA 19% y total se calculan solos)</small></p>
<p>Expediente SharePoint: <input name="expediente"
 value="{html.escape(oc.get('expediente', ''))}" style="width:22em"></p>
<p>{_selector_operador(config)} <button>{'Actualizar' if oc else 'Registrar'} OC</button></p>
</form></div>"""
    descargar = (f'<p><a href="/manager/{sid}.csv"><button>Descargar archivo '
                 'de carga Manager+</button></a></p>'
                 if s.get("estado_portal") in ("LISTA", "PROCESADA") else "")
    cuerpo = f"""<div class="tarjeta">
<h2>Solicitud #{sid} {_chip(s.get('estado_portal', ''))}</h2>
<p><b>Monto:</b> {clp(ev.get('monto', 0))} ·
<b>Estado en Zoho:</b> {html.escape(d.get('estado_zoho', 'sin dato'))}
<small>(la aprobación se hace en Zoho)</small>{link_ficha}</p>
{''.join(checks)}{nota}
<p>{acciones}</p>{descargar}
{f"<h3>Historial</h3><ul>{decisiones}</ul>" if decisiones else ""}
</div>
{form_oc}
<div class="tarjeta"><h3>Datos de la solicitud (Zoho)</h3>
<table>{filas}</table>
<p><small>Ingresada al portal: {html.escape(s.get('ingresada', ''))}.
Los adjuntos (cotizaciones, ficha) siguen en Zoho.</small></p></div>"""
    return pagina(f"Solicitud {sid}", cuerpo, "/")


def vista_proveedores(mensaje=""):
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
    fichas = cargar_proveedores()
    filas = []
    for rut in sorted(fichas):
        f = fichas[rut]
        estado, _ = evaluar_ficha(f)
        filas.append(f'<tr><td><a href="/ficha?rut={rut}">{rut}</a></td>'
                     f"<td>{html.escape(f.get('razon_social', ''))}</td>"
                     f"<td>{_chip(estado)}</td>"
                     f"<td>{html.escape(f.get('actualizado', ''))}</td>"
                     f'<td><a href="/manager_proveedor/{rut}.xlsx">carga '
                     "Manager+</a></td></tr>")
    lista = ("<h3>Fichas guardadas</h3><table><tr><th>RUT</th><th>Razón "
             "social</th><th>Estado</th><th>Actualizada</th><th>Documento"
             "</th></tr>" + "".join(filas) + "</table>") if filas else \
        "<p><small>Aún no hay fichas guardadas.</small></p>"
    cuerpo = f"""{aviso}
<div class="tarjeta"><h2>Paso 1 — Verificar en el SII</h2>{estado_cuota}
<form method="post" action="/verificar">
<p>RUT: <input name="rut" required placeholder="76123456-7">
Correo comercial: <input name="correo" type="email" placeholder="ventas@…">
Nombre fantasía: <input name="fantasia" placeholder="(opcional)"></p>
<p>{_selector_operador(config)}
<label><input type="checkbox" name="mock" value="1"> prueba (sin gastar
cuota)</label>
<button>Verificar y abrir ficha</button></p></form>
<p><small>La verificación queda registrada y abre la ficha pre-llenada
con los datos del SII (razón social, giro, dirección, correo SII).</small></p>
</div>
<div class="tarjeta"><h2>Paso 2 — Cargar la Ficha de Proveedor (archivo)</h2>
<p><small>Sube la <b>Ficha Proveedor MundoSocios</b> que envió el
proveedor, en Excel (.xlsx) o PDF: el portal lee datos tributarios,
representantes, contacto, DTE y datos bancarios, y abre la ficha para
revisar y guardar. El orden con el Paso 1 da lo mismo.</small></p>
<form method="post" action="/cargar_ficha" enctype="multipart/form-data">
<p><input type="file" name="archivo" accept=".xlsx,.pdf" required>
{_selector_operador(config)} <button>Cargar ficha</button></p></form></div>
<div class="tarjeta">{lista}</div>"""
    return pagina("Proveedores", cuerpo, "/proveedor")


def vista_ficha(rut):
    rut = normalizar_rut(rut)
    fichas = cargar_proveedores()
    ficha = fichas.get(rut)
    if not ficha:
        return pagina("Ficha", '<div class="error">Primero verifica el RUT '
                      'en la pestaña Proveedores.</div>', "/proveedor")
    config = cargar_config()
    estado, faltantes = evaluar_ficha(ficha)
    falta_html = "".join(f'<div class="error">Falta: {html.escape(x)}</div>'
                         for x in faltantes)
    secciones, seccion_actual = [], None
    for clave, etiqueta, seccion, bloqueante in CAMPOS_FICHA:
        if seccion != seccion_actual:
            if seccion_actual is not None:
                secciones.append("</div>")
            secciones.append(f"<h3>{html.escape(seccion)}</h3>"
                             '<div class="grilla">')
            seccion_actual = seccion
        marca = " *" if bloqueante else ""
        secciones.append(
            f"<label>{html.escape(etiqueta)}{marca}"
            f'<input name="{clave}" '
            f'value="{html.escape(str(ficha.get(clave, "")))}"></label>')
    secciones.append("</div>")
    cuerpo = f"""<div class="tarjeta">
<h2>Ficha de proveedor {html.escape(rut)} {_chip(estado)}</h2>
<p>{html.escape(ficha.get('razon_social', ''))} ·
Verificación SII: <b>{html.escape(ficha.get('sii_resultado', 'sin verificar'))}</b>
<small>({html.escape(ficha.get('sii_fecha', ''))})</small> ·
Correo SII: {html.escape(ficha.get('correo_sii', '') or '—')}</p>
{falta_html}
<p><small>* campos bloqueantes (checklist v2.0): sin ellos el proveedor no
queda APTO ni debe entrar a una OC. Los datos bancarios se copian del
formulario/ficha que envió el proveedor.</small></p>
<form method="post" action="/ficha">
<input type="hidden" name="rut" value="{html.escape(rut)}">
{''.join(secciones)}
<p style="margin-top:1em">{_selector_operador(config)}
<button>Guardar ficha</button>
<a href="/manager_proveedor/{rut}.xlsx"><button type="button" class="sec">
Documento de carga Manager+</button></a></p>
</form></div>"""
    return pagina(f"Ficha {rut}", cuerpo, "/proveedor")


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
            f"<td style='text-align:right'>{clp(comp)}</td>"
            f"<td style='text-align:right' class='{clase}'>{clp(saldo)}</td></tr>")
    cuerpo = f"""<div class="tarjeta"><h2>Presupuesto por centro de costo</h2>
<p><small>Saldo inicial en CLP (0 = sin control para ese CC). El
comprometido se calcula solo, con las solicitudes PROCESADAS en el
portal.</small></p>
<form method="post" action="/presupuesto">
<table><tr><th>Centro de costo</th><th>Saldo inicial</th>
<th>Comprometido</th><th>Disponible</th></tr>{''.join(filas)}</table>
<p>Agregar CC: <input name="nuevo_cc" placeholder="nombre">
monto <input name="nuevo_monto" style="width:8em"></p>
<p>{_selector_operador(config)} <button>Guardar presupuesto</button></p>
</form></div>"""
    return pagina("Presupuesto", cuerpo, "/presupuesto")


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


def cargar_clave_simpleapi():
    """El doble clic no hereda las variables del shell: si no está
    SIMPLEAPI_API_KEY, la lee de clave_simpleapi.txt junto al portal
    (archivo local del equipo anfitrión; excluido del repositorio)."""
    if os.environ.get("SIMPLEAPI_API_KEY"):
        return True
    archivo = BASE / "clave_simpleapi.txt"
    if archivo.exists():
        clave = archivo.read_text(encoding="utf-8").strip()
        if clave:
            os.environ["SIMPLEAPI_API_KEY"] = clave
            return True
    return False


def ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


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
