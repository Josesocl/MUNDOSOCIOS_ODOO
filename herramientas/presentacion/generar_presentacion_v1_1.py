#!/usr/bin/env python3
"""Genera Presentacion_Ejecutiva_MS_JR_V1.1.pptx.

Informe ejecutivo de la asesoría COT-2026-MS-001 (15 h / 45 UF) para la
Gerencia General de MundoSocios, alineado al alcance cotizado:
levantamiento y diagnóstico, automatizaciones inmediatas, coaching y
gestión del cambio, 4 entregables, más el estado del proyecto Odoo.

Uso:  python3 generar_presentacion_v1_1.py [salida.pptx]
"""

import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

AZUL = RGBColor(0x1F, 0x4E, 0x79)      # títulos y acentos
AZUL_CLARO = RGBColor(0xDCE, 0xE6, 0xF2) if False else RGBColor(0xDC, 0xE6, 0xF2)
GRIS = RGBColor(0x59, 0x59, 0x59)
GRIS_CLARO = RGBColor(0xF2, 0xF2, 0xF2)
VERDE = RGBColor(0x2E, 0x7D, 0x32)
AMBAR = RGBColor(0xB26, 0x00, 0x00) if False else RGBColor(0xB5, 0x6A, 0x00)
ROJO = RGBColor(0xB0, 0x2A, 0x2A)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
NEGRO = RGBColor(0x21, 0x21, 0x21)

ANCHO, ALTO = Inches(13.333), Inches(7.5)


def _caja(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tb.text_frame.word_wrap = True
    return tb


def _p(tf, texto, size=14, bold=False, color=NEGRO, first=False, align=PP_ALIGN.LEFT,
       space_after=4, bullet=False):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    r = p.add_run()
    r.text = ("• " if bullet else "") + texto
    f = r.font
    f.size, f.bold, f.color.rgb, f.name = Pt(size), bold, color, "Calibri"
    p.alignment = align
    p.space_after = Pt(space_after)
    return p


def _rect(slide, x, y, w, h, fill, line=None):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line:
        sh.line.color.rgb = line
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def slide_base(prs, titulo, subtitulo=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])   # en blanco
    _rect(s, 0, 0, ANCHO, Inches(0.16), AZUL)
    tb = _caja(s, Inches(0.5), Inches(0.32), Inches(12.3), Inches(0.75))
    _p(tb.text_frame, titulo, size=26, bold=True, color=AZUL, first=True)
    if subtitulo:
        _p(tb.text_frame, subtitulo, size=13, color=GRIS)
    pie = _caja(s, Inches(0.5), Inches(7.08), Inches(12.3), Inches(0.35))
    _p(pie.text_frame, "JR Jottar Consultoría · IB Solución Ltda. · Asesoría COT-2026-MS-001 · Julio 2026",
       size=9, color=GRIS, first=True)
    return s


def tabla(slide, x, y, w, filas, anchos=None, size=11, header_fill=AZUL,
          header_color=BLANCO, row_h=0.32):
    nfilas, ncols = len(filas), len(filas[0])
    shape = slide.shapes.add_table(nfilas, ncols, x, y, w, Inches(row_h * nfilas))
    t = shape.table
    if anchos:
        total = sum(anchos)
        for i, a in enumerate(anchos):
            t.columns[i].width = Emu(int(w * a / total))
    for i, fila in enumerate(filas):
        for j, celda in enumerate(fila):
            c = t.cell(i, j)
            c.margin_top = c.margin_bottom = Pt(2)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.text = str(celda)
            for p in c.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(size)
                    r.font.name = "Calibri"
                    r.font.color.rgb = header_color if i == 0 else NEGRO
                    r.font.bold = i == 0
            c.fill.solid()
            c.fill.fore_color.rgb = header_fill if i == 0 else (GRIS_CLARO if i % 2 == 0 else BLANCO)
    return t


def construir(salida: Path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = ANCHO, ALTO

    # ---- 1. Portada
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(s, 0, 0, ANCHO, ALTO, AZUL)
    tb = _caja(s, Inches(1), Inches(2.2), Inches(11.3), Inches(3.2))
    _p(tb.text_frame, "Asesoría Procesos Financiero-Contables", size=40, bold=True,
       color=BLANCO, first=True)
    _p(tb.text_frame, "MundoSocios — Cámara Chilena de la Construcción", size=22, color=AZUL_CLARO)
    _p(tb.text_frame, "", size=10)
    _p(tb.text_frame, "Informe Ejecutivo para la Gerencia General", size=18, color=BLANCO)
    _p(tb.text_frame, "Levantamiento · Automatizaciones inmediatas · Gestión del cambio · Preparación Odoo",
       size=14, color=AZUL_CLARO)
    tb = _caja(s, Inches(1), Inches(6.3), Inches(11.3), Inches(0.6))
    _p(tb.text_frame, "JR Jottar Consultoría (IB Solución) · Servicio COT-2026-MS-001 · Julio 2026 · V1.1",
       size=12, color=AZUL_CLARO, first=True)

    # ---- 2. Agenda
    s = slide_base(prs, "Agenda")
    items = [
        ("01", "Contexto y objetivo del servicio"),
        ("02", "Alcance cotizado y grado de cumplimiento"),
        ("03", "Levantamiento: procesos, dolores y riesgos"),
        ("04", "Automatizaciones entregadas (quick wins)"),
        ("05", "Automatización del cobro recurrente (cuotas y seguros)"),
        ("06", "Entregables comprometidos vs. entregados"),
        ("07", "Gestión del cambio: equipo de finanzas como aliado"),
        ("08", "Proyecto Odoo: partners, riesgos y decisiones de gerencia"),
        ("09", "Próximos pasos"),
    ]
    tb = _caja(s, Inches(1.2), Inches(1.5), Inches(10.5), Inches(5.3))
    for i, (n, texto) in enumerate(items):
        p = _p(tb.text_frame, f"{n}   {texto}", size=17, first=(i == 0), space_after=10)
        p.runs[0].font.color.rgb = NEGRO

    # ---- 3. Contexto y objetivo
    s = slide_base(prs, "Contexto y objetivo del servicio",
                   "Según cotización COT-2026-MS-001 — 15 horas / 45 UF")
    kpis = [("~1.955", "socios titulares"), ("~4.800", "personas con familias"),
            ("~1.500", "notas de cobro/mes"), ("~233", "movim./cartola mensual")]
    x = Inches(0.5)
    for valor, etiqueta in kpis:
        _rect(s, x, Inches(1.35), Inches(2.95), Inches(0.95), GRIS_CLARO)
        tb = _caja(s, x, Inches(1.4), Inches(2.95), Inches(0.9))
        _p(tb.text_frame, valor, size=22, bold=True, color=AZUL, first=True, align=PP_ALIGN.CENTER, space_after=0)
        _p(tb.text_frame, etiqueta, size=11, color=GRIS, align=PP_ALIGN.CENTER)
        x += Inches(3.12)
    tb = _caja(s, Inches(0.5), Inches(2.6), Inches(12.3), Inches(1.5))
    _p(tb.text_frame,
       "MundoSocios migrará su ecosistema (Zoho One, Manager+, WordPress, planillas Excel) a Odoo Enterprise. "
       "El área financiero-contable es crítica por su complejidad operativa y por su impacto en la viabilidad "
       "del cambio de ERP.", size=14, first=True)
    tb = _caja(s, Inches(0.5), Inches(3.9), Inches(6.0), Inches(2.6))
    _p(tb.text_frame, "Objetivo 1 — Procesos", size=16, bold=True, color=AZUL, first=True)
    _p(tb.text_frame, "Levantar y documentar los procesos financiero-contables actuales, "
       "identificando automatizaciones y eficiencias implementables de inmediato.", size=13)
    tb = _caja(s, Inches(6.9), Inches(3.9), Inches(6.0), Inches(2.6))
    _p(tb.text_frame, "Objetivo 2 — Personas", size=16, bold=True, color=AZUL, first=True)
    _p(tb.text_frame, "Integrar al equipo de finanzas, liderado por Patricio Fernández, como aliado "
       "estratégico del proyecto Odoo: de posible resistencia a participación activa.", size=13)

    # ---- 4. Alcance cotizado vs cumplimiento
    s = slide_base(prs, "Alcance cotizado y grado de cumplimiento")
    filas = [
        ["Bloque cotizado", "Comprometido", "Estado"],
        ["2.1 Levantamiento y diagnóstico", "Entrevistas, documentación de procesos críticos, cuellos de botella, inventario de herramientas",
         "✔ 13 subprocesos y 13 puntos críticos documentados; 3 blueprints AS-IS/TO-BE; guía de entrevistas para cierre"],
        ["2.2 Automatización y eficiencia", "Quick wins en herramientas existentes con alivio visible antes del ERP",
         "✔ 8 quick wins construidos y verificados + 3 herramientas adicionales de cobro recurrente (ver lámina 5)"],
        ["2.3 Coaching y gestión del cambio", "Patricio como referente técnico; caso de mejora; preparación key users; alineamiento con GG",
         "◐ Marco y plan de 3 sesiones listos; sesiones por agendar (requiere agenda del equipo)"],
        ["Entregables", "4 documentos comprometidos", "✔ 4 entregados (.md y .docx) + guía de entrevistas adicional"],
    ]
    tabla(s, Inches(0.5), Inches(1.5), Inches(12.3), filas, anchos=[2.6, 4.4, 5.3], size=11.5, row_h=0.95)

    # ---- 5. Levantamiento
    s = slide_base(prs, "Levantamiento: los dolores que hoy cuestan horas y riesgo")
    filas = [
        ["#", "Dolor detectado", "Impacto"],
        ["1", "TXT bancario frágil: campos vacíos del maestro, caracteres especiales, fecha editada a mano en Bloc de notas", "Crítico — riesgo en pagos"],
        ["2", "Cruce de pagos entre 3 fuentes (Manager+, Zoho, Excel) para rebajar deuda", "~10 hrs/semana"],
        ["3", "Fondos propios (cuota social) vs. de terceros (seguros) separados manualmente", "Riesgo de auditoría"],
        ["4", "Devengos de seguros copiando 4 Excel del mes anterior (errores → reprocesos)", "Alto — reprocesos"],
        ["5", "Dependencia de personas: Cecilia (OC), Patricio (banco), Oriana (recaudación)", "Continuidad operativa"],
        ["6", "Sin proceso sistematizado de morosidad ni métricas de cobranza", "Pérdida de recaudación"],
    ]
    tabla(s, Inches(0.5), Inches(1.5), Inches(12.3), filas, anchos=[0.5, 8.6, 3.2], size=12, row_h=0.62)
    tb = _caja(s, Inches(0.5), Inches(5.7), Inches(12.3), Inches(1.1))
    _p(tb.text_frame, "Documentado en el Informe de Diagnóstico (Entregable 1): 13 subprocesos, 13 puntos críticos, "
       "inventario de 14 sistemas/herramientas, y 3 blueprints AS-IS/TO-BE (Compras, Recaudación, Experiencia).",
       size=12, color=GRIS, first=True)

    # ---- 6. Quick wins
    s = slide_base(prs, "Automatizaciones entregadas (quick wins)",
                   "Construidas sobre las herramientas actuales — alivio antes del ERP, sin macros")
    filas = [
        ["Herramienta", "Qué resuelve", "Estado"],
        ["01 Ficha Proveedor (checklist APTO)", "Bloquea proveedores incompletos que rompen el TXT", "Operativa"],
        ["02 Registro y Plantilla OC", "IVA, total y tramo de aprobación automáticos", "Operativa"],
        ["03 Control Nómina de Pago", "Detecta errores del TXT antes de tocar Manager+; cruza banco/cuenta por RUT", "Operativa"],
        ["04 Cálculo UF Cuota Social", "UF del día en vivo para incorporaciones", "Operativa"],
        ["05 Conciliación Bancaria", "Preconciliación y cuadratura automática", "Operativa"],
        ["Validador SII (RUT + situación tributaria)", "45 tests; proxy en la nube listo; falta token API Gateway (~$10.000/mes)", "Lista — decisión pendiente"],
    ]
    tabla(s, Inches(0.5), Inches(1.6), Inches(12.3), filas, anchos=[3.6, 6.2, 2.5], size=11.5, row_h=0.6)
    tb = _caja(s, Inches(0.5), Inches(5.85), Inches(12.3), Inches(1.0))
    _p(tb.text_frame, "Todas verificadas con recálculo real (0 errores de fórmula). Pendiente: sesión de "
       "entrenamiento al equipo para su adopción semanal (flujo 01→02→03→05).", size=12, color=GRIS, first=True)

    # ---- 7. Cobro recurrente
    s = slide_base(prs, "Automatización del cobro recurrente (cuotas y seguros)",
                   "Construido en julio con los archivos reales del área — validado al peso contra producción")
    filas = [
        ["Herramienta", "Reemplaza", "Beneficio"],
        ["Generador de devengos de seguros", "Copiar 4 Excel del mes anterior y editar 22 columnas a mano",
         "Archivos de importación listos desde un maestro único; valida RUTs y clientes ANTES de importar"],
        ["Generador de cuota social anual", "Armado manual del devengo de enero (~1.080 líneas)",
         "Reglas 2026 aplicadas: 1 UF persona, 3 UF empresa + 1 UF por miembro desde el 4º"],
        ["Cruzador de pagos", "Cruce manual cartola / Transbank / Manager+ (~10 hrs/sem)",
         "Borrador de preconciliación automático: cuadra abonos Transbank y propone RUT de transferencias"],
    ]
    tabla(s, Inches(0.5), Inches(1.6), Inches(12.3), filas, anchos=[3.2, 4.2, 4.9], size=11.5, row_h=0.85)
    tb = _caja(s, Inches(0.5), Inches(5.35), Inches(12.3), Inches(1.6))
    _p(tb.text_frame, "Ahorro estimado del paquete completo: 50–60 horas/mes en el área.", size=15,
       bold=True, color=VERDE, first=True)
    _p(tb.text_frame, "Montos validados al peso contra los archivos productivos (Plan Carreño JUL-26, Cuota "
       "Social ENE-26). Próximo paso: mes en paralelo en agosto. Nada se bota al migrar: el maestro único "
       "de pólizas es el mismo insumo de carga inicial de Odoo Suscripciones.", size=12, color=GRIS)

    # ---- 8. Entregables
    s = slide_base(prs, "Entregables comprometidos vs. entregados")
    filas = [
        ["Entregable cotizado", "Estado", "Observación"],
        ["1. Informe de diagnóstico de procesos financiero-contables", "Entregado",
         "13 subprocesos, 13 puntos críticos, diagramas AS-IS→TO-BE; se cierra con entrevistas"],
        ["2. Plan de automatizaciones inmediatas", "Entregado", "8 quick wins construidos, no solo propuestos"],
        ["3. Requerimientos del área financiera para Odoo", "Entregado",
         "25 requerimientos (RF-01…RF-24 + RF-06b) mapeados a módulos Odoo; insumo directo Fase 0/1"],
        ["4. Reporte de gestión del cambio", "Entregado",
         "Riesgos y estrategia listos; evaluación de disposición se completa en entrevistas"],
        ["Adicionales (sin costo)", "Entregados",
         "Guía de entrevistas · especificación de suscripciones Odoo · política de morosidad (borrador) · "
         "3 herramientas de cobro recurrente"],
    ]
    tabla(s, Inches(0.5), Inches(1.5), Inches(12.3), filas, anchos=[4.6, 1.6, 6.1], size=11.5, row_h=0.8)

    # ---- 9. Gestión del cambio
    s = slide_base(prs, "Gestión del cambio: finanzas como aliado del proyecto",
                   "Objetivo 2 del servicio — transformar resistencia en participación")
    tb = _caja(s, Inches(0.5), Inches(1.5), Inches(6.0), Inches(4.8))
    _p(tb.text_frame, "Estrategia", size=16, bold=True, color=AZUL, first=True)
    _p(tb.text_frame, "Patricio Fernández como key user líder del frente financiero-contable", size=13, bullet=True)
    _p(tb.text_frame, "Los quick wins como \"prueba de buena fe\": la transformación reduce carga, no la aumenta",
       size=13, bullet=True)
    _p(tb.text_frame, "Equipo preparado para la fase de blueprints del implementador", size=13, bullet=True)
    _p(tb.text_frame, "Alineamiento gerencia general ↔ finanzas en expectativas y alcance", size=13, bullet=True)
    _p(tb.text_frame, "", size=8)
    _p(tb.text_frame, "Riesgos vigilados", size=16, bold=True, color=AZUL)
    _p(tb.text_frame, "Dependencia de personas clave (formar segundos key users: Marcos Ibarra ya se integró a recaudación)",
       size=13, bullet=True)
    _p(tb.text_frame, "Expectativas irreales sobre el ERP (restricciones ya transparentadas)", size=13, bullet=True)
    tb = _caja(s, Inches(6.9), Inches(1.5), Inches(6.0), Inches(4.8))
    _p(tb.text_frame, "Plan de 3 sesiones (dentro del servicio)", size=16, bold=True, color=AZUL, first=True)
    _p(tb.text_frame, "S1 — Diagnóstico y dolor: validar el levantamiento con el equipo", size=13, bullet=True)
    _p(tb.text_frame, "S2 — Quick wins: entrenamiento en las herramientas y caso de mejora", size=13, bullet=True)
    _p(tb.text_frame, "S3 — Preparación key user + alineamiento con Gerencia General", size=13, bullet=True)
    _p(tb.text_frame, "", size=8)
    _p(tb.text_frame, "Estado: plan y materiales listos; sesiones por agendar con Patricio.", size=13, color=AMBAR)

    # ---- 10. Recaudación TO-BE
    s = slide_base(prs, "Diseño Odoo — Recaudación y cobro recurrente (TO-BE)",
                   "Suscripciones: compromiso anual, cobro mensual (seguros) o anual (cuota social)")
    filas = [
        ["Producto", "Fondo", "Cta. x cobrar", "Cta. ingreso", "Cobro", "Mix pago"],
        ["Cuota Social Empresa (3 UF + adic.)", "Propio", "1150001", "3210002", "Anual", "80% Webpay/transf."],
        ["Cuota Social Persona (1 UF)", "Propio", "1150002", "3210001", "Anual", "80% Webpay/transf."],
        ["Plan Socios", "Terceros", "1130004", "3310005", "Mensual", "80% PAC/PAT"],
        ["Complementario (UF día 9)", "Terceros", "1130003", "3310003", "Mensual", "80% PAC/PAT"],
        ["Catastrófico (UF cierre mes ant.)", "Terceros", "1130002", "3310001", "Mensual", "80% PAC/PAT"],
        ["Plan Carreño", "Terceros", "1130005", "3310004", "Mensual", "80% PAC/PAT"],
    ]
    tabla(s, Inches(0.5), Inches(1.6), Inches(12.3), filas, anchos=[3.6, 1.2, 1.5, 1.5, 1.1, 2.0], size=11, row_h=0.5)
    tb = _caja(s, Inches(0.5), Inches(5.4), Inches(12.3), Inches(1.4))
    _p(tb.text_frame, "La separación de fondos propios vs. de terceros queda estructural (cuentas por producto y "
       "diarios separados) — deja de depender de disciplina manual. Devengo automático mensual (~1.500 notas), "
       "seguimiento de morosidad paramétrico y conciliación con auto-match ≥78% sin Excel intermedios.",
       size=12.5, first=True)

    # ---- 11. Partners
    s = slide_base(prs, "Proyecto Odoo — Evaluación de partners",
                   "Costo total año 1 (implementación + licencias + hosting), UF neto")
    filas = [
        ["Partner", "Año 1 (UF)", "Lectura"],
        ["Indasoge", "641", "Mejor relación alcance/precio; incluye WhatsApp y Portal; TXT implícito — confirmar por escrito"],
        ["Consulnet", "824", "Más completo y transparente (629 hrs desglosadas); bajo riesgo de extras"],
        ["Odoo MX", "433", "Solo configuración estándar; excluye lo custom; requiere partner local"],
        ["Addval", "572", "Excluye Compras y Helpdesk; sin migración ni custom — alcance incompleto"],
    ]
    tabla(s, Inches(0.5), Inches(1.6), Inches(12.3), filas, anchos=[1.8, 1.3, 9.2], size=12, row_h=0.65)
    tb = _caja(s, Inches(0.5), Inches(5.1), Inches(12.3), Inches(1.5))
    _p(tb.text_frame, "Antes de firmar (a cualquier partner): confirmar hosting Odoo.sh (requisito del TXT "
       "bancario), pasarela PAC/PAT (Toku/Nuvei), cobertura del motor de recaudación y tratamiento de Buk. "
       "Las preguntas ya están redactadas y listas para enviar.", size=13, first=True)

    # ---- 12. Riesgos y decisiones
    s = slide_base(prs, "Riesgos y decisiones que requieren a la Gerencia")
    tb = _caja(s, Inches(0.5), Inches(1.5), Inches(6.0), Inches(5.0))
    _p(tb.text_frame, "Restricciones confirmadas de Odoo", size=16, bold=True, color=AZUL, first=True)
    for texto in [
        "TXT Banco de Chile: NO nativo — requiere Odoo.sh y desarrollo",
        "Webpay / PAC / PAT: NO nativo — vía Toku/Nuvei u otro",
        "Buk (RRHH): sin integración — asiento manual",
        "UF: se muestra en CLP en pantalla y portal",
        "Extracto bancario: importación manual (CSV/OFX)",
    ]:
        _p(tb.text_frame, texto, size=13, bullet=True)
    tb = _caja(s, Inches(6.9), Inches(1.5), Inches(6.0), Inches(5.0))
    _p(tb.text_frame, "Decisiones de gerencia", size=16, bold=True, color=AZUL, first=True)
    for texto in [
        "Partner implementador y modalidad de hosting",
        "Pasarela de pagos para PAC/PAT y Webpay",
        "Política de morosidad y pagos parciales (borrador listo para validar)",
        "Rol de Addval después de la migración",
        "Token API Gateway para validación SII (~$10.000/mes)",
        "Agenda de las 3 sesiones de gestión del cambio",
    ]:
        _p(tb.text_frame, texto, size=13, bullet=True)

    # ---- 13. Próximos pasos + horas
    s = slide_base(prs, "Próximos pasos y cierre del servicio")
    filas = [
        ["Semana", "Acción"],
        ["1–2", "Entrevistas de cierre con el equipo (guía lista) y validación de blueprints"],
        ["2", "Mes en paralelo de las herramientas de cobro recurrente (devengos de agosto)"],
        ["2–3", "Sesiones de gestión del cambio S1–S3 y entrenamiento en quick wins"],
        ["3", "Respuestas de partners a las preguntas críticas → decisión de partner"],
        ["4", "Kick-off con el partner seleccionado — el área de finanzas llega preparada"],
    ]
    tabla(s, Inches(0.5), Inches(1.5), Inches(7.4), filas, anchos=[1.0, 6.4], size=12, row_h=0.55)
    filas = [
        ["Bloque cotizado", "Hrs", "UF"],
        ["Entrevistas y reuniones", "4", "12"],
        ["Análisis y documentación", "3", "9"],
        ["Automatizaciones", "3", "9"],
        ["Coaching y cambio", "3", "9"],
        ["Entregables y presentación", "2", "6"],
        ["TOTAL", "15", "45"],
    ]
    tabla(s, Inches(8.3), Inches(1.5), Inches(4.5), filas, anchos=[2.7, 0.9, 0.9], size=11.5, row_h=0.45)
    tb = _caja(s, Inches(0.5), Inches(5.4), Inches(12.3), Inches(1.2))
    _p(tb.text_frame, "El servicio se ejecutó dentro del marco de 15 horas / 45 UF cotizado, con entregables "
       "adicionales sin costo. Gracias.", size=14, bold=True, first=True)

    prs.save(salida)
    print(f"OK: {salida} ({salida.stat().st_size:,} bytes)")


if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Presentacion_Ejecutiva_MS_JR_V1.1.pptx")
    construir(destino)
