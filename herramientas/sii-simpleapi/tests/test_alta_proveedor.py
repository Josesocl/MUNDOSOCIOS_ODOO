"""Tests del alta de proveedor (sin red). Ejecutar desde sii-simpleapi/:
    python3 -m unittest discover tests
"""

import csv
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import alta_proveedor
import cliente_simpleapi


class TestAltaProveedor(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._registros_orig = alta_proveedor.CARPETA_REGISTROS
        alta_proveedor.CARPETA_REGISTROS = Path(self._tmp.name) / "verificaciones"
        self._estado_orig = cliente_simpleapi.ARCHIVO_ESTADO
        cliente_simpleapi.ARCHIVO_ESTADO = Path(self._tmp.name) / ".estado.json"

    def tearDown(self):
        alta_proveedor.CARPETA_REGISTROS = self._registros_orig
        cliente_simpleapi.ARCHIVO_ESTADO = self._estado_orig
        self._tmp.cleanup()

    def test_flujo_apto_genera_registro_y_campos(self):
        rc = alta_proveedor.main(["--rut", "76.123.456-0", "--mock",
                                  "--correo-comercial", "ventas@prov.cl"])
        self.assertEqual(rc, 0)
        registros = list(alta_proveedor.CARPETA_REGISTROS.glob("VERIFICACION_SII_*.html"))
        self.assertEqual(len(registros), 1)
        contenido = registros[0].read_text(encoding="utf-8")
        self.assertIn("APTO-SII", contenido)
        self.assertIn("EMPRESA DE PRUEBA LTDA", contenido)
        self.assertIn("ventas@prov.cl", contenido)
        self.assertIn("Nacional (facturas)", contenido)
        with open(alta_proveedor.CARPETA_REGISTROS / "registro_verificaciones.csv",
                  encoding="utf-8-sig") as f:
            filas = list(csv.DictReader(f, delimiter=";"))
        self.assertEqual(filas[0]["rut"], "76123456-0")
        self.assertEqual(filas[0]["resultado"], "APTO-SII")

    def test_sin_inicio_actividades_es_no_apto(self):
        original = cliente_simpleapi._respuesta_mock

        def sin_inicio(rut):
            d = dict(original(rut))
            d["presentaInicioActividades"] = False
            return d
        with mock.patch.object(cliente_simpleapi, "_respuesta_mock", sin_inicio):
            rc = alta_proveedor.main(["--rut", "76123456-0", "--mock"])
        self.assertEqual(rc, 2)   # código distinto: NO APTO
        registro = next(alta_proveedor.CARPETA_REGISTROS.glob("*.html"))
        self.assertIn("NO APTO", registro.read_text(encoding="utf-8"))

    def test_rut_invalido_no_gasta_ni_registra(self):
        rc = alta_proveedor.main(["--rut", "76123456-9", "--mock"])  # DV malo
        self.assertEqual(rc, 1)
        self.assertFalse(alta_proveedor.CARPETA_REGISTROS.exists())

    def test_evaluar_sin_iva_sugiere_revision(self):
        datos = cliente_simpleapi._respuesta_mock("1-9")
        datos["actividadesEconomicas"][0]["afectaIVA"] = False
        estado, tipo, obs = alta_proveedor.evaluar(datos)
        self.assertEqual(estado, "APTO-SII")
        self.assertIn("REVISAR", tipo)


if __name__ == "__main__":
    unittest.main()
