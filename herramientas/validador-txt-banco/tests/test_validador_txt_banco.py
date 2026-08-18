"""Tests del validador del TXT bancario (sin red). Ejecutar desde
validador-txt-banco/:
    python3 -m unittest discover tests
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validador_txt_banco as v


def txt_de_prueba(encabezado="1065091028100280057Nomina de pago 20260818",
                  cuerpo=None, fin="\r\n"):
    lineas = [encabezado] + (cuerpo if cuerpo is not None else [
        "2005707076799430COMERCIALIZADORA SP DIGITAL LIMITADA",
        "300570001EMAventas@spdigital.cl",
        "400570001Brazo articulador soportes de monitor",
    ])
    return fin.join(lineas) + fin


class TestValidador(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _escribir(self, contenido, nombre="Transfer_CHILE_20260818.txt",
                  cod="cp1252"):
        ruta = self.dir / nombre
        ruta.write_bytes(contenido.encode(cod))
        return ruta

    def test_archivo_limpio_pasa(self):
        ruta = self._escribir(txt_de_prueba())
        rc = v.main([str(ruta)])
        self.assertEqual(rc, 0)

    def test_caracter_especial_es_error(self):
        ruta = self._escribir(txt_de_prueba(
            cuerpo=["400570001Reunión de equipo * jornada"]))
        lineas, _, _ = v.leer_txt(ruta)
        errores, _ = v.validar(lineas)
        self.assertTrue(any("'*'" in e for e in errores))
        self.assertEqual(v.main([str(ruta)]), 2)

    def test_tilde_es_solo_aviso(self):
        ruta = self._escribir(txt_de_prueba(
            cuerpo=["400570001Reunión directorio agosto"]))
        lineas, _, _ = v.leer_txt(ruta)
        errores, avisos = v.validar(lineas)
        self.assertEqual(errores, [])
        self.assertTrue(any("revisar" in a for a in avisos))

    def test_linea_larga_es_error(self):
        ruta = self._escribir(txt_de_prueba(cuerpo=["4" + "A" * 450]))
        lineas, _, _ = v.leer_txt(ruta)
        errores, _ = v.validar(lineas)
        self.assertTrue(any("451 caracteres" in e for e in errores))

    def test_monto_negativo_avisa(self):
        ruta = self._escribir(txt_de_prueba(
            cuerpo=["200570-61200NOTA DE CREDITO AJUSTE"]))
        lineas, _, _ = v.leer_txt(ruta)
        _, avisos = v.validar(lineas)
        self.assertTrue(any("NEGATIVO" in a for a in avisos))

    def test_corregir_fecha_crea_archivo_nuevo(self):
        ruta = self._escribir(txt_de_prueba())
        rc = v.main([str(ruta), "--fecha-pago", "22-08-2026"])
        self.assertEqual(rc, 0)
        nuevo = ruta.with_name(f"{ruta.stem}_pago_20260822.txt")
        self.assertTrue(nuevo.exists())
        contenido = nuevo.read_bytes().decode("cp1252")
        self.assertIn("20260822", contenido.split("\r\n")[0])
        self.assertNotIn("20260818", contenido.split("\r\n")[0])
        # el original queda intacto
        self.assertIn("20260818", ruta.read_bytes().decode("cp1252"))
        # y conserva el fin de línea CRLF
        self.assertIn("\r\n", contenido)

    def test_sin_fecha_en_encabezado_reclama(self):
        ruta = self._escribir(txt_de_prueba(encabezado="1SINFECHA"))
        rc = v.main([str(ruta), "--fecha-pago", "22-08-2026"])
        self.assertEqual(rc, 1)

    def test_diagnostico_enmascara_digitos(self):
        ruta = self._escribir(txt_de_prueba())
        lineas, _, _ = v.leer_txt(ruta)
        import contextlib
        import io
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            v.diagnostico(lineas)
        texto = salida.getvalue()
        self.assertNotIn("76799430", texto)      # RUT enmascarado
        self.assertIn("20260818", texto)         # la fecha sí se muestra
        self.assertIn("Registro tipo", texto)

    def test_normalizar_fecha(self):
        self.assertEqual(v.normalizar_fecha("22-08-2026"), "20260822")
        self.assertEqual(v.normalizar_fecha("20260822"), "20260822")
        with self.assertRaises(RuntimeError):
            v.normalizar_fecha("mañana")


if __name__ == "__main__":
    unittest.main()
