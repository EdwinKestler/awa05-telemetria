import tempfile
import unittest
from pathlib import Path

from scripts.utils import ejecutar_seguro, guardar_csv


class UtilsTests(unittest.TestCase):
    def test_guardar_csv_crea_directorio_y_encabezado(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "data" / "lecturas.csv"
            guardar_csv(ruta, {"timestamp": "2026-01-01 00:00:00", "valor": 1})
            guardar_csv(ruta, {"timestamp": "2026-01-01 00:01:00", "valor": 2})

            lineas = ruta.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lineas[0], "timestamp,valor")
            self.assertEqual(len(lineas), 3)

    def test_ejecutar_seguro_devuelve_resultado_exitoso(self):
        llamadas = []

        resultado = ejecutar_seguro("demo", lambda: llamadas.append("ok"))

        self.assertTrue(resultado.ok)
        self.assertFalse(resultado.failed)
        self.assertEqual(resultado.name, "demo")
        self.assertIsNone(resultado.error)
        self.assertEqual(llamadas, ["ok"])


if __name__ == "__main__":
    unittest.main()
