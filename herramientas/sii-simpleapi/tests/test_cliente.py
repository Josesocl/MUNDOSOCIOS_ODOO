"""Tests del cliente SimpleAPI (sin red). Ejecutar desde sii-simpleapi/:
    python3 -m unittest discover tests
"""

import io
import json
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cliente_simpleapi as cs


class _RespuestaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestCliente(unittest.TestCase):
    def setUp(self):
        self._estado_original = cs.ARCHIVO_ESTADO
        cs.ARCHIVO_ESTADO = Path(__file__).with_name(".estado_test.json")
        if cs.ARCHIVO_ESTADO.exists():
            cs.ARCHIVO_ESTADO.unlink()

    def tearDown(self):
        if cs.ARCHIVO_ESTADO.exists():
            cs.ARCHIVO_ESTADO.unlink()
        cs.ARCHIVO_ESTADO = self._estado_original

    def test_mock_no_gasta_cuota(self):
        datos, origen = cs.consultar_rut("76.123.456-0", mock=True)
        self.assertEqual(origen, "mock")
        self.assertTrue(datos["_mock"])
        self.assertEqual(cs.consultas_del_mes(cs._cargar_estado()), 0)

    def test_rut_invalido(self):
        with self.assertRaises(RuntimeError):
            cs.consultar_rut("76123456-9", mock=True)  # DV incorrecto

    def test_sin_api_key(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                cs.consultar_rut("76123456-0")
        self.assertIn("SIMPLEAPI_API_KEY", str(ctx.exception))

    def test_consulta_cachea_y_cuenta(self):
        cuerpo = json.dumps({"razonSocial": "ACME"}).encode()
        abrir = mock.Mock(return_value=_RespuestaFalsa(cuerpo))
        with mock.patch.dict("os.environ", {"SIMPLEAPI_API_KEY": "k"}):
            datos, origen = cs.consultar_rut("76123456-0", _abrir=abrir)
            self.assertEqual(origen, "api")
            self.assertEqual(datos["razonSocial"], "ACME")
            # Segunda consulta: cache, sin tocar la red ni la cuota
            datos2, origen2 = cs.consultar_rut("76123456-0", _abrir=abrir)
        self.assertEqual(origen2, "cache")
        self.assertEqual(abrir.call_count, 1)
        self.assertEqual(cs.consultas_del_mes(cs._cargar_estado()), 1)

    def test_limite_mensual(self):
        estado = {"mes": cs._mes_actual(), "consultas": cs.LIMITE_MENSUAL_RUT,
                  "cache": {}}
        cs._guardar_estado(estado)
        with mock.patch.dict("os.environ", {"SIMPLEAPI_API_KEY": "k"}):
            with self.assertRaises(RuntimeError) as ctx:
                cs.consultar_rut("76123456-0")
        self.assertIn("Cuota mensual", str(ctx.exception))

    def test_contador_se_reinicia_por_mes(self):
        estado = {"mes": "2026-06", "consultas": 10, "cache": {}}
        cs._guardar_estado(estado)
        self.assertEqual(cs.consultas_del_mes(cs._cargar_estado(),
                                              hoy=date(2026, 7, 31)), 0)


if __name__ == "__main__":
    unittest.main()
