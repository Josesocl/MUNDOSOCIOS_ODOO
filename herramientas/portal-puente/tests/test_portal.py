"""Tests del Portal Puente MS v2 (sin red, sin servidor). Ejecutar desde
portal-puente/:
    python3 -m unittest discover tests
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import portal

# Registro real de Zoho (anonimizado parcialmente) tal como se pega
EJEMPLO_ZOHO = """Información de Formulario de Solicitud
Nombre de actividad :
Evento Fomento Participación Comité Inmobiliario
Correo electrónico :
fbustos@cchc.cl
Fecha de actividad :
13-08-2026
Tipo de solicitud :
Formulario OC
Centro de costo :
FOCO SOCIO
Cuenta Contable :
Fomento Participación Gremial
Formulario de Solicitud Propietario :
Felipe Bustos
Estado de solicitud :
Aprobado
Usuario encargado :
Marcos Ibarra
¿Posee contrato con proveedor? :
No
Tipo de compra :
Compras Normales (Compras que están conforme a lo planificado y presupuestado para el periodo)
Detalle de productos o servicio (Descriptorio) :
Amplificación y proyección Evento Fomento Participación Comité Inmobiliario
Fecha acuerdo de pago :
28-08-2026
Valor total :
113.050
Razón social / Nombre :
PROYECTOS AUDIOVISUALES FELIPE GUZMAN SALGADO EIRL
Giro :
Produccion De Eventos
Rut del proveedor :
65091028-1Pro
Motivo porque se escogió a ese proveedor :
Proveedor oficial edifico CChC Santiago
¿Posee ambas cotizaciones? :
No
Motivo de selección Proveedor :
Proveedor oficial edifico CChC Santiago
"""

FICHA_COMPLETA = {
    "rut": "65091028-1", "razon_social": "PROVEEDOR DE PRUEBA",
    "giro": "SERVICIOS", "correo": "v@p.cl", "tipo_dte": "Factura Electrónica",
    "banco": "Banco de Chile", "tipo_cuenta": "corriente",
    "numero_cuenta": "123456789", "email_aviso_pago": "pagos@p.cl",
    "sii_resultado": "APTO-SII", "sii_fecha": "18-08-2026 10:00",
    "actualizado": "18-08-2026 10:05",
}


class TestParserZoho(unittest.TestCase):
    def test_pegado_extrae_los_campos(self):
        d = portal.parsear_pegado(EJEMPLO_ZOHO)
        self.assertEqual(d["actividad"],
                         "Evento Fomento Participación Comité Inmobiliario")
        self.assertEqual(d["centro_costo"], "FOCO SOCIO")
        self.assertEqual(d["valor_total"], "113.050")
        self.assertEqual(d["rut_proveedor"], "65091028-1Pro")
        self.assertEqual(d["estado_zoho"], "Aprobado")
        self.assertEqual(d["posee_ambas_cotizaciones"], "No")

    def test_csv_mapea_encabezados(self):
        csv_texto = ("Nombre de actividad;Centro de costo;Valor total;"
                     "Rut del proveedor\n"
                     "Taller;MUNDO SALUD;250000;76123456-0\n")
        filas = portal.parsear_csv(csv_texto)
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["centro_costo"], "MUNDO SALUD")


class TestReglas(unittest.TestCase):
    def test_rut_con_basura_se_normaliza_y_valida(self):
        rut = portal.normalizar_rut("65091028-1Pro")
        self.assertEqual(rut, "65091028-1")
        self.assertTrue(portal.rut_valido(rut))
        self.assertFalse(portal.rut_valido("76123456-9"))

    def test_montos_chilenos(self):
        self.assertEqual(portal.parse_monto("113.050"), 113050)
        self.assertEqual(portal.parse_monto("$ 1.113.050"), 1113050)
        self.assertEqual(portal.parse_monto("113050,60"), 113051)


class TestFichaProveedor(unittest.TestCase):
    def test_ficha_completa_es_apto(self):
        estado, faltantes = portal.evaluar_ficha(dict(FICHA_COMPLETA))
        self.assertEqual(estado, "APTO")
        self.assertEqual(faltantes, [])

    def test_sin_datos_bancarios_no_es_apto(self):
        ficha = dict(FICHA_COMPLETA)
        del ficha["numero_cuenta"]
        estado, faltantes = portal.evaluar_ficha(ficha)
        self.assertEqual(estado, "EN VALIDACIÓN")
        self.assertIn("Número de cuenta", faltantes)

    def test_sin_sii_no_es_apto(self):
        ficha = dict(FICHA_COMPLETA)
        ficha["sii_resultado"] = "NO APTO"
        estado, faltantes = portal.evaluar_ficha(ficha)
        self.assertEqual(estado, "EN VALIDACIÓN")
        self.assertIn("Verificación SII vigente (APTO-SII)", faltantes)

    def test_documento_manager_formato_oficial_xlsx(self):
        import io
        import zipfile
        doc = portal.documento_manager_proveedor(dict(FICHA_COMPLETA))
        with zipfile.ZipFile(io.BytesIO(doc)) as z:
            hoja = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        for esperado in ("Razón social", "Email SII", "Cuenta Tipo",
                         "65091028-1", "PROVEEDOR DE PRUEBA", "123456789"):
            self.assertIn(esperado, hoja)
        # fila oficial de 37 columnas con los códigos de Manager+
        fila = portal.fila_manager_proveedor(dict(FICHA_COMPLETA))
        self.assertEqual(len(fila), 37)
        self.assertEqual(len(portal.COLUMNAS_MANAGER), 37)
        idx = {c: i for i, c in enumerate(portal.COLUMNAS_MANAGER)}
        self.assertEqual(fila[idx["Tipo cliente"]], "N")
        self.assertEqual(fila[idx["Tipo proveedor"]], "P")
        self.assertEqual(fila[idx["Cuenta Tipo"]], 3)   # corriente = 3

    def test_codigos_manager(self):
        self.assertEqual(portal.codigo_tipo_cuenta("Cuenta corriente"), 3)
        self.assertEqual(portal.codigo_tipo_cuenta("vista"), 1)
        self.assertEqual(portal.codigo_tipo_cuenta("ahorro"), 2)
        self.assertEqual(
            portal.codigo_tipo_proveedor({"tipo_dte": "Boleta de Honorarios"}),
            "H")
        self.assertEqual(
            portal.codigo_tipo_proveedor({"tipo_dte": "Factura Electrónica"}),
            "P")


class TestChecklist(unittest.TestCase):
    def _datos(self, **extra):
        base = portal.parsear_pegado(EJEMPLO_ZOHO)
        base.update(extra)
        return base

    def test_proveedor_apto_y_zoho_aprobado_queda_lista(self):
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO", "ficha completa")):
            ev = portal.evaluar_solicitud(self._datos())
        self.assertEqual(ev["errores"], [])
        # sin ambas cotizaciones: solo aviso informativo, no bloquea
        self.assertTrue(any("cotizaciones" in a for a in ev["avisos"]))
        self.assertTrue(any("Aprobada en Zoho" in a for a in ev["avisos"]))

    def test_no_aprobada_en_zoho_es_error(self):
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO", "")):
            ev = portal.evaluar_solicitud(
                self._datos(estado_zoho="En espera de aprobación"))
        self.assertTrue(any("Zoho" in e for e in ev["errores"]))

    def test_solo_sii_sin_ficha_es_error(self):
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("SOLO-SII", "verificado")):
            ev = portal.evaluar_solicitud(self._datos())
        self.assertTrue(any("ficha" in e.lower() for e in ev["errores"]))

    def test_falta_campo_obligatorio(self):
        datos = self._datos()
        del datos["centro_costo"]
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO", "")):
            ev = portal.evaluar_solicitud(datos)
        self.assertTrue(any("Centro de costo" in e for e in ev["errores"]))

    def test_sin_saldo_avisa_pero_no_bloquea(self):
        presupuesto = {"FOCO SOCIO": {"inicial": 100_000}}
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO", "")):
            ev = portal.evaluar_solicitud(self._datos(),
                                          presupuesto=presupuesto)
        self.assertTrue(ev["sin_saldo"])
        self.assertTrue(any("SIN saldo" in a for a in ev["avisos"]))
        self.assertEqual(ev["errores"], [])

    def test_comprometido_cuenta_procesadas(self):
        solicitudes = {"1": {"estado_portal": "PROCESADA",
                             "datos": {"centro_costo": "FOCO SOCIO",
                                       "valor_total": "300.000"}}}
        self.assertEqual(
            portal.comprometido_por_cc(solicitudes, "FOCO SOCIO"), 300000)


class TestArchivoSolicitud(unittest.TestCase):
    def test_incluye_solicitud_y_oc(self):
        datos = portal.parsear_pegado(EJEMPLO_ZOHO)
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO", "")):
            ev = portal.evaluar_solicitud(datos)
        oc = {"numero": "OC-1234", "fecha": "20-08-2026", "neto": 95000,
              "iva": 18050, "total": 113050, "expediente": "SP/2026/08",
              "operador": "Cecilia Ramírez"}
        doc = portal.archivo_manager_solicitud(datos, ev, oc)
        self.assertIn("SOLICITUD;RUT proveedor;65091028-1", doc)
        self.assertIn("OC;N° OC (Manager+);OC-1234", doc)
        self.assertIn("OC;TOTAL bruto;113050", doc)


class TestPersistencia(unittest.TestCase):
    def test_guardar_y_leer(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = portal.DATOS
            portal.DATOS = Path(tmp) / "datos"
            try:
                portal.guardar_proveedores({"65091028-1": FICHA_COMPLETA})
                estado, _ = portal.estado_proveedor("65091028-1")
                self.assertEqual(estado, "APTO")
                ficha = dict(FICHA_COMPLETA)
                del ficha["banco"]
                portal.guardar_proveedores({"65091028-1": ficha})
                estado, detalle = portal.estado_proveedor("65091028-1")
                self.assertEqual(estado, "FICHA-INCOMPLETA")
                self.assertIn("Banco", detalle)
                portal.bitacora("prueba", "detalle", "Tester")
                self.assertEqual(portal.leer_bitacora()[0]["evento"], "prueba")
            finally:
                portal.DATOS = original


if __name__ == "__main__":
    unittest.main()
