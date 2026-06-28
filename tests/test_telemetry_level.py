import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import awa05.telemetry.level as level


class TelemetryLevelTests(unittest.TestCase):
    def test_tomar_lectura_returns_reading_and_preserves_csv_write(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta_raw = Path(temporal) / "nivel_raw.csv"

            with patch("awa05.telemetry.level.RUTA_RAW", ruta_raw), \
                 patch("awa05.telemetry.level.timestamp_ahora", return_value="2026-06-26 12:00:00"), \
                 patch("awa05.telemetry.level.leer_nivel", return_value=(33.0, 44.0)):
                resultado = level.tomar_lectura()

            self.assertEqual(resultado, (33.0, 44.0))
            self.assertIn("distancia_cm,volumen_litros", ruta_raw.read_text(encoding="utf-8"))

    def test_tomar_lectura_returns_empty_tuple_when_sensor_does_not_answer(self):
        with patch("awa05.telemetry.level.leer_nivel", return_value=(None, None)):
            self.assertEqual(level.tomar_lectura(), (None, None))

    def test_tomar_lectura_reintenta_antes_de_descartar(self):
        calls = []
        sleeps = []

        def leer_fn(sensor=None):
            calls.append(sensor)
            if len(calls) == 1:
                return None, None
            return 33.0, 44.0

        with tempfile.TemporaryDirectory() as temporal:
            ruta_raw = Path(temporal) / "nivel_raw.csv"

            with patch("awa05.telemetry.level.RUTA_RAW", ruta_raw), \
                 patch("awa05.telemetry.level.timestamp_ahora", return_value="2026-06-26 12:00:00"):
                resultado = level.tomar_lectura(
                    sensor="sensor-test",
                    max_attempts=2,
                    retry_delay_s=0.5,
                    sleep_fn=sleeps.append,
                    leer_fn=leer_fn,
                )

        self.assertEqual(resultado, (33.0, 44.0))
        self.assertEqual(calls, ["sensor-test", "sensor-test"])
        self.assertEqual(sleeps, [0.5])

    def test_tomar_lectura_reintenta_runtime_error_y_descarta(self):
        calls = []
        sleeps = []

        def leer_fn(sensor=None):
            calls.append(sensor)
            raise RuntimeError("GPIO no disponible")

        resultado = level.tomar_lectura(
            sensor="sensor-test",
            max_attempts=2,
            retry_delay_s=0,
            sleep_fn=sleeps.append,
            leer_fn=leer_fn,
        )

        self.assertEqual(resultado, (None, None))
        self.assertEqual(calls, ["sensor-test", "sensor-test"])
        self.assertEqual(sleeps, [0.0])


if __name__ == "__main__":
    unittest.main()
