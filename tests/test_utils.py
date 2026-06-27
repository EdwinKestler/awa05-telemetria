import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from awa05.core.logging import configure_logging
from scripts.utils import ejecutar_seguro, guardar_csv


def _cleanup_logger(logger):
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


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

    def test_ejecutar_seguro_registra_error_si_logging_esta_configurado(self):
        with tempfile.TemporaryDirectory() as temporal:
            log_path = Path(temporal) / "awa05.log"
            logger = configure_logging(
                path=log_path,
                max_bytes=1024,
                backup_count=1,
                console=False,
            )

            with patch("builtins.print"):
                resultado = ejecutar_seguro(
                    "demo",
                    lambda: (_ for _ in ()).throw(RuntimeError("boom")),
                )

            for handler in logger.handlers:
                handler.flush()

            self.assertTrue(resultado.failed)
            contenido = log_path.read_text(encoding="utf-8")
            self.assertIn("Error en demo", contenido)
            self.assertIn("RuntimeError: boom", contenido)
            _cleanup_logger(logger)


if __name__ == "__main__":
    unittest.main()
