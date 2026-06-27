import json
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

        app = create_app(Receiver(), shared_secret="")
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

        app = create_app(Receiver(), shared_secret="")
        client = app.test_client()

        response = client.post("/data", data={"tempf": "78.0"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(received, [{"tempf": "78.0"}])

    @unittest.skipUnless(HAS_FLASK, "Flask no instalado en este entorno")
    def test_flask_endpoint_requiere_token_si_hay_secreto_configurado(self):
        received = []

        class Receiver:
            def receive(self, datos):
                received.append(dict(datos))
                return {"ok": True}

        app = create_app(Receiver(), shared_secret="secreto")
        client = app.test_client()

        missing = client.get("/data?tempf=77.0")
        wrong = client.get("/data?tempf=77.0&token=otro")
        ok = client.get("/data?tempf=77.0&token=secreto")

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(received, [{"tempf": "77.0"}])

    @unittest.skipUnless(HAS_FLASK, "Flask no instalado en este entorno")
    def test_flask_endpoint_acepta_token_por_header(self):
        received = []

        class Receiver:
            def receive(self, datos):
                received.append(dict(datos))
                return {"ok": True}

        app = create_app(Receiver(), shared_secret="secreto")
        client = app.test_client()

        response = client.post(
            "/data",
            data={"tempf": "78.0"},
            headers={"X-AWA05-Token": "secreto"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(received, [{"tempf": "78.0"}])

    @unittest.skipUnless(HAS_FLASK, "Flask no instalado en este entorno")
    def test_flask_endpoint_limita_tamano_de_payload(self):
        class Receiver:
            def receive(self, datos):
                return {"ok": True}

        app = create_app(
            Receiver(),
            shared_secret="",
            max_content_length_bytes=8,
        )
        client = app.test_client()

        response = client.post("/data", data={"tempf": "78.0"})

        self.assertEqual(response.status_code, 413)

    @unittest.skipUnless(HAS_FLASK, "Flask no instalado en este entorno")
    def test_health_endpoint_devuelve_status_json(self):
        class Receiver:
            def receive(self, datos):
                return {"ok": True}

        with tempfile.TemporaryDirectory() as temporal:
            health_path = Path(temporal) / "health_status.json"
            health_path.write_text(
                json.dumps(
                    {
                        "state": "NORMAL",
                        "consecutive_sensor_failures": 0,
                    }
                ),
                encoding="utf-8",
            )
            app = create_app(Receiver(), shared_secret="", health_path=health_path)
            client = app.test_client()

            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["state"], "NORMAL")
        self.assertEqual(response.json["consecutive_sensor_failures"], 0)

    @unittest.skipUnless(HAS_FLASK, "Flask no instalado en este entorno")
    def test_health_endpoint_respeta_token_si_hay_secreto_configurado(self):
        class Receiver:
            def receive(self, datos):
                return {"ok": True}

        with tempfile.TemporaryDirectory() as temporal:
            health_path = Path(temporal) / "health_status.json"
            health_path.write_text('{"state": "NORMAL"}', encoding="utf-8")
            app = create_app(
                Receiver(),
                shared_secret="secreto",
                health_path=health_path,
            )
            client = app.test_client()

            missing = client.get("/health")
            wrong = client.get("/health?token=otro")
            ok = client.get("/health", headers={"X-AWA05-Token": "secreto"})

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json["state"], "NORMAL")

    @unittest.skipUnless(HAS_FLASK, "Flask no instalado en este entorno")
    def test_health_endpoint_reporta_no_disponible_si_no_existe(self):
        class Receiver:
            def receive(self, datos):
                return {"ok": True}

        with tempfile.TemporaryDirectory() as temporal:
            health_path = Path(temporal) / "missing-health.json"
            app = create_app(Receiver(), shared_secret="", health_path=health_path)
            client = app.test_client()

            response = client.get("/health")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
