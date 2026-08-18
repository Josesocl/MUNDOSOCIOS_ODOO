"""Tests del Portal Puente MS (sin red, sin servidor). Ejecutar desde
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


class TestParserZoho(unittest.TestCase):
    def test_pegado_extrae_los_campos(self):
        d = portal.parsear_pegado(EJEMPLO_ZOHO)
        self.assertEqual(d["actividad"],
                         "Evento Fomento Participación Comité Inmobiliario")
        self.assertEqual(d["centro_costo"], "FOCO SOCIO")
        self.assertEqual(d["valor_total"], "113.050")
        self.assertEqual(d["rut_proveedor"], "65091028-1Pro")
        self.assertEqual(d["posee_ambas_cotizaciones"], "No")
        self.assertEqual(d["tipo_solicitud"], "Formulario OC")

    def test_csv_mapea_encabezados(self):
        csv_texto = ("Nombre de actividad;Centro de costo;Valor total;"
                     "Rut del proveedor\n"
                     "Taller;MUNDO SALUD;250000;76123456-0\n")
        filas = portal.parsear_csv(csv_texto)
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["centro_costo"], "MUNDO SALUD")
        self.assertEqual(filas[0]["valor_total"], "250000")


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
        self.assertEqual(portal.parse_monto(113050.0), 113050)

    def test_tramos_matriz_vigente(self):
        self.assertIn("Dueño", portal.tramo_de(400_000)[0])
        self.assertIn("Cecilia", portal.tramo_de(800_000)[0])
        self.assertIn("Patricio", portal.tramo_de(3_000_000)[0])
        self.assertIn("Constanza", portal.tramo_de(6_000_000)[0])


class TestChecklist(unittest.TestCase):
    def _datos(self, **extra):
        base = portal.parsear_pegado(EJEMPLO_ZOHO)
        base.update(extra)
        return base

    def test_sin_cotizaciones_es_excepcion_ayf_gg(self):
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO-SII", "01-08-2026 10:00")):
            ev = portal.evaluar_solicitud(self._datos())
        self.assertEqual(ev["errores"], [])
        self.assertTrue(ev["requiere_excepcion"])
        self.assertEqual(set(ev["roles_autorizados"]), {"AYF", "GG"})

    def test_con_ambas_cotizaciones_aprueba_el_tramo(self):
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO-SII", "")):
            ev = portal.evaluar_solicitud(
                self._datos(posee_ambas_cotizaciones="Sí"))
        self.assertFalse(ev["requiere_excepcion"])
        # 113.050 → tramo 1: dueño del presupuesto (cualquier operador)
        self.assertIn("OPERADOR", ev["roles_autorizados"])

    def test_proveedor_no_apto_bloquea(self):
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("NO APTO", "01-08-2026")):
            ev = portal.evaluar_solicitud(self._datos())
        self.assertTrue(any("NO APTO" in e for e in ev["errores"]))

    def test_falta_campo_obligatorio(self):
        datos = self._datos()
        del datos["centro_costo"]
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=(None, "")):
            ev = portal.evaluar_solicitud(datos)
        self.assertTrue(any("Centro de costo" in e for e in ev["errores"]))

    def test_sin_saldo_solo_gerencia(self):
        presupuesto = {"FOCO SOCIO": {"inicial": 100_000}}
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO-SII", "")):
            ev = portal.evaluar_solicitud(
                self._datos(posee_ambas_cotizaciones="Sí"),
                presupuesto=presupuesto)
        self.assertTrue(ev["sin_saldo"])
        self.assertEqual(ev["roles_autorizados"], ["GG"])

    def test_presupuesto_comprometido_descuenta(self):
        solicitudes = {"1": {"estado_portal": "APROBADA",
                             "datos": {"centro_costo": "FOCO SOCIO",
                                       "valor_total": "300.000"}}}
        self.assertEqual(
            portal.comprometido_por_cc(solicitudes, "FOCO SOCIO"), 300000)
        presupuesto = {"FOCO SOCIO": {"inicial": 400_000}}
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO-SII", "")):
            ev = portal.evaluar_solicitud(
                self._datos(posee_ambas_cotizaciones="Sí"),
                solicitudes=solicitudes, presupuesto=presupuesto)
        self.assertTrue(ev["sin_saldo"])   # 400.000 - 300.000 < 113.050


class TestManager(unittest.TestCase):
    def test_archivo_manager_trae_proveedor_y_oc(self):
        datos = portal.parsear_pegado(EJEMPLO_ZOHO)
        with mock.patch.object(portal, "estado_proveedor",
                               return_value=("APTO-SII", "")):
            ev = portal.evaluar_solicitud(datos)
        contenido = portal.archivo_manager(datos, ev)
        self.assertIn("PROVEEDOR;RUT;65091028-1", contenido)
        self.assertIn("OC;Centro de costo;FOCO SOCIO", contenido)
        self.assertIn("OC;Monto total (c/IVA);113050", contenido)


class TestPersistencia(unittest.TestCase):
    def test_guardar_y_leer(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = portal.DATOS
            portal.DATOS = Path(tmp) / "datos"
            try:
                portal.guardar_solicitudes({"1": {"datos": {"actividad": "x"},
                                                  "estado_portal": "LISTA"}})
                self.assertEqual(
                    portal.cargar_solicitudes()["1"]["estado_portal"], "LISTA")
                pres = portal.cargar_presupuesto()
                self.assertIn("MUNDO SALUD", pres)
                portal.bitacora("prueba", "detalle", "Tester")
                self.assertEqual(portal.leer_bitacora()[0]["evento"], "prueba")
            finally:
                portal.DATOS = original


if __name__ == "__main__":
    unittest.main()
