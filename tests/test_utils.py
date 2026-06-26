import tempfile
import unittest
from pathlib import Path

from scripts.utils import guardar_csv


class UtilsTests(unittest.TestCase):
    def test_guardar_csv_crea_directorio_y_encabezado(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "data" / "lecturas.csv"
            guardar_csv(ruta, {"timestamp": "2026-01-01 00:00:00", "valor": 1})
            guardar_csv(ruta, {"timestamp": "2026-01-01 00:01:00", "valor": 2})

            lineas = ruta.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lineas[0], "timestamp,valor")
            self.assertEqual(len(lineas), 3)


if __name__ == "__main__":
    unittest.main()
