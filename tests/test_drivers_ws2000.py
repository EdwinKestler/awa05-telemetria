import tempfile
import unittest
from pathlib import Path

from awa05.drivers.ws2000 import WS2000Receiver, create_app

try:
    import flask  # noqa: F401

    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


class WS2000ReceiverTests(unittest.TestCase):
    def test_normalizar_mapea_payload_a_fila_clima(self):
        receiver = WS2000Receiver(timestamp_fn=lambda: "2026-06-26 10:00:00")

        fila = receiver.normalizar(
            {
                "tempf": "77.0",
                "humidity": "65",
                "dewptf": "60.0",
                "baromin": "29.92",
                "windspeedmph": "4.2",
                "winddir": "180",
                "rainin": "0.01",
                "solarradiation": "450",
                "UV": "3",
            }
        )

        self.assertEqual(fila["timestamp"], "2026-06-26 10:00:00")
        self.assertEqual(fila["temp_exterior"], "77.0")
        self.assertEqual(fila["humedad"], "65")
        self.assertEqual(fila["punto_rocio"], "60.0")
        self.assertEqual(fila["presion"], "29.92")
        self.assertEqual(fila["viento_vel"], "4.2")
        self.assertEqual(fila["viento_dir"], "180")
        self.assertEqual(fila["lluvia_hora"], "0.01")
        self.assertEqual(fila["radiacion_solar"], "450")
        self.assertEqual(fila["uv"], "3")

    def test_receive_guarda_csv_y_tolera_campos_faltantes(self):
        with tempfile.TemporaryDirectory() as temporal:
            csv_path = Path(temporal) / "clima_raw.csv"
            receiver = WS2000Receiver(
                csv_path=csv_path,
                timestamp_fn=lambda: "2026-06-26 10:00:00",
            )

            fila = receiver.receive({"tempf": "77.0"})

            self.assertEqual(fila["temp_exterior"], "77.0")
            self.assertEqual(fila["humedad"], "N/A")
            contenido = csv_path.read_text(encoding="utf-8")
            self.assertIn("temp_exterior", contenido)
            self.assertIn("77.0", contenido)

    @unittest.skipUnless(HAS_FLASK, "Flask no instalado en este entorno")
    def test_flask_endpoint_acepta_get_y_rechaza_sin_datos(self):
        received = []

        class Receiver:
            def receive(self, datos):
                if not datos:
                    return None
                received.append(dict(datos))
                return {"ok": True}

        app = create_app(Receiver())
        client = app.test_client()

        ok = client.get("/data?tempf=77.0&humidity=65")
        empty = client.get("/data")
        root = client.get("/")

        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.text, "OK")
        self.assertEqual(empty.status_code, 400)
        self.assertEqual(root.status_code, 200)
        self.assertEqual(received, [{"tempf": "77.0", "humidity": "65"}])

    @unittest.skipUnless(HAS_FLASK, "Flask no instalado en este entorno")
    def test_flask_endpoint_acepta_post_form(self):
        received = []

        class Receiver:
            def receive(self, datos):
                received.append(dict(datos))
                return {"ok": True}

        app = create_app(Receiver())
        client = app.test_client()

        response = client.post("/data", data={"tempf": "78.0"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(received, [{"tempf": "78.0"}])


if __name__ == "__main__":
    unittest.main()
