#!/usr/bin/env python3
"""Alta de proveedor MundoSocios — verificación SII automatizada (SimpleAPI).

Automatiza los pasos 1-3 del proceso actual de creación de proveedor
(BP_Proceso_Creacion_Proveedor, AS-IS):

  1. Verificación de la situación tributaria en el SII — antes: zeus.sii.cl
     con captcha y copy-paste, sin registro (dolor PC-P2). Ahora: consulta
     vía SimpleAPI (con caché de 90 días y control de cuota: 10/mes) que
     deja REGISTRO fechado de la verificación (HTML + bitácora CSV).
  2. Semáforo del checklist v2.0: sin inicio de actividades = NO APTO.
  3. Bloque de campos listo para digitar en Manager+ (Mantenedores >
     Clientes y/o proveedores > Crear cliente/proveedor), copiado del SII
     sin errores de tipeo.

La decisión final y la digitación siguen siendo de una persona; los datos
bancarios y el resto del checklist se completan en la Ficha de Proveedor
como siempre.

Uso:
    python3 alta_proveedor.py --rut 76123456-7
    python3 alta_proveedor.py --rut 76123456-7 --correo-comercial ventas@prov.cl
    python3 alta_proveedor.py --rut 76123456-7 --mock     # prueba sin red/cuota
"""

import argparse
import csv
import html
import sys
from datetime import datetime
from pathlib import Path

import cliente_simpleapi

CARPETA_REGISTROS = Path(__file__).with_name("verificaciones")


def evaluar(datos):
    """Aplica el checklist v2.0 a la respuesta del SII.
    → (estado, tipo_sugerido, observaciones)."""
    obs = []
    actividades = datos.get("actividadesEconomicas") or []
    inicio = bool(datos.get("presentaInicioActividades"))
    if not inicio:
        obs.append("NO presenta inicio de actividades ante el SII")
    if not actividades:
        obs.append("sin actividades económicas registradas")
    estado = "APTO-SII" if inicio and actividades else "NO APTO"

    afecta = any(a.get("afectaIVA") for a in actividades)
    if afecta:
        tipo = "Nacional (facturas)"
    else:
        tipo = "REVISAR: ninguna actividad afecta a IVA — ¿Honorario (boletas) o exento?"
        obs.append("ninguna actividad afecta a IVA")
    return estado, tipo, obs


def campos_manager(datos, args):
    """Los campos mínimos del AS-IS, en el orden de la pantalla de Manager+."""
    actividades = datos.get("actividadesEconomicas") or []
    giro = actividades[0]["descripcion"] if actividades else ""
    dom = (datos.get("domicilios") or [{}])[0]
    direccion = ", ".join(x for x in (dom.get("direccion"), dom.get("comuna"),
                                      dom.get("ciudad")) if x)
    razon = datos.get("razonSocial", "")
    _, tipo, _ = evaluar(datos)
    return [
        ("RUT", datos.get("rut", "")),
        ("Razón social", razon),
        ("Nombre de fantasía", args.nombre_fantasia or razon),
        ("Giro", giro),
        ("Clasificación", "sin clasificación"),
        ("Correo electrónico SII", datos.get("correoIntercambio") or ""),
        ("Correo electrónico comercial", args.correo_comercial or ""),
        ("Tipo proveedor", tipo),
        ("Plazo de pago", "30 días"),
        ("Dirección (según SII)", direccion),
    ]


def escribir_registro(datos, origen, estado, obs, campos):
    """Registro fechado de la verificación (resuelve PC-P2)."""
    CARPETA_REGISTROS.mkdir(exist_ok=True)
    ahora = datetime.now()
    rut = datos.get("rut", "")

    filas_campos = "\n".join(
        f"<tr><th>{html.escape(n)}</th><td>{html.escape(str(v))}</td></tr>"
        for n, v in campos)
    filas_act = "\n".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            html.escape(str(a.get("codigo", ""))),
            html.escape(a.get("descripcion", "")),
            html.escape(a.get("categoria", "")),
            "Sí" if a.get("afectaIVA") else "No")
        for a in datos.get("actividadesEconomicas") or [])
    color = "#1a7f37" if estado == "APTO-SII" else "#c62828"
    obs_html = "".join(f"<li>{html.escape(o)}</li>" for o in obs)

    doc = f"""<!doctype html><html lang="es"><meta charset="utf-8">
<title>Verificación SII {html.escape(rut)}</title>
<body style="font-family:sans-serif;max-width:700px;margin:2em auto">
<h1>Verificación SII — proveedor {html.escape(rut)}</h1>
<p><b>Fecha:</b> {ahora:%d-%m-%Y %H:%M} · <b>Fuente:</b> SimpleAPI
(rut.simpleapi.cl) · <b>Origen:</b> {html.escape(origen)}</p>
<p style="font-size:1.3em"><b>Resultado:</b>
<span style="color:{color}">{html.escape(estado)}</span></p>
{f'<ul>{obs_html}</ul>' if obs else ''}
<p><b>Inicio de actividades:</b>
{"Sí" if datos.get("presentaInicioActividades") else "NO"}
({html.escape(str(datos.get("fechaInicioActividades") or "s/f"))})</p>
<h2>Actividades económicas</h2>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>Código</th><th>Descripción</th><th>Categoría</th><th>Afecta IVA</th></tr>
{filas_act}</table>
<h2>Campos para Manager+</h2>
<table border="1" cellpadding="4" cellspacing="0">{filas_campos}</table>
<p style="color:#666">Registro generado por alta_proveedor.py — proyecto
MundoSocios. Los datos bancarios y el resto del checklist v2.0 se
completan en la Ficha de Proveedor.</p>
</body></html>"""
    ruta_html = CARPETA_REGISTROS / f"VERIFICACION_SII_{rut}_{ahora:%Y%m%d-%H%M%S}.html"
    ruta_html.write_text(doc, encoding="utf-8")

    bitacora = CARPETA_REGISTROS / "registro_verificaciones.csv"
    nueva = not bitacora.exists()
    with open(bitacora, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        if nueva:
            w.writerow(["fecha", "rut", "razon_social", "resultado", "origen",
                        "archivo"])
        w.writerow([f"{ahora:%d-%m-%Y %H:%M}", rut,
                    datos.get("razonSocial", ""), estado, origen,
                    ruta_html.name])
    return ruta_html


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Alta de proveedor: verificación SII con registro")
    ap.add_argument("--rut", required=True)
    ap.add_argument("--correo-comercial", default="")
    ap.add_argument("--nombre-fantasia", default="")
    ap.add_argument("--mock", action="store_true",
                    help="respuesta simulada, sin red ni cuota")
    ap.add_argument("--forzar", action="store_true",
                    help="ignora el límite mensual de la API")
    args = ap.parse_args(argv)

    try:
        datos, origen = cliente_simpleapi.consultar_rut(
            args.rut, mock=args.mock, forzar=args.forzar)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    estado, tipo, obs = evaluar(datos)
    campos = campos_manager(datos, args)
    ruta = escribir_registro(datos, origen, estado, obs, campos)

    print(f"Proveedor {datos.get('rut')} — {datos.get('razonSocial', '')}")
    print(f"Resultado verificación SII: {estado}   [origen: {origen}]")
    for o in obs:
        print(f"  ! {o}")
    print("\n--- Campos para Manager+ (copiar/pegar) ---")
    for nombre, valor in campos:
        print(f"  {nombre}: {valor}")
    print(f"\nRegistro guardado: {ruta}")
    if estado != "APTO-SII":
        print("\nNO APTO: según el checklist v2.0 este proveedor NO debe "
              "crearse en Manager+ ni entrar a una OC. Resolver con el "
              "proveedor y verificar de nuevo.")
    else:
        print("\nSiguiente paso: completar datos bancarios y contacto en la "
              "Ficha de Proveedor; crear en Manager+ solo con la ficha en APTO.")
    return 0 if estado == "APTO-SII" else 2


if __name__ == "__main__":
    sys.exit(main())
