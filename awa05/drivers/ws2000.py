from secrets import compare_digest

from awa05.config import ws2000_config
from awa05.utils import guardar_csv, ruta_proyecto, timestamp_ahora


DEFAULT_ROUTE = "/data"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 7777
RUTA_CLIMA = ruta_proyecto("data/raw/clima_raw.csv")


class WS2000Receiver:
    """Receive WS-2000 weather-station updates and persist normalized CSV rows."""

    FIELD_MAP = {
        "temp_exterior": "tempf",
        "humedad": "humidity",
        "punto_rocio": "dewptf",
        "presion": "baromin",
        "viento_vel": "windspeedmph",
        "viento_dir": "winddir",
        "lluvia_hora": "rainin",
        "radiacion_solar": "solarradiation",
        "uv": "UV",
    }

    def __init__(self, csv_path=None, guardar=guardar_csv, timestamp_fn=timestamp_ahora):
        self.csv_path = csv_path or RUTA_CLIMA
        self.guardar = guardar
        self.timestamp_fn = timestamp_fn

    def normalizar(self, datos):
        return {
            "timestamp": self.timestamp_fn(),
            **{
                campo_destino: datos.get(campo_origen, "N/A")
                for campo_destino, campo_origen in self.FIELD_MAP.items()
            },
        }

    def receive(self, datos):
        if not datos:
            return None
        fila = self.normalizar(datos)
        self.guardar(self.csv_path, fila)
        print(
            "[WS2000] Datos recibidos: "
            f"temp={fila['temp_exterior']} humedad={fila['humedad']}"
        )
        return fila


def _request_token(request):
    return (
        request.headers.get("X-AWA05-Token")
        or request.args.get("token")
        or request.form.get("token")
        or ""
    )


def _payload_sin_token(datos):
    return {clave: valor for clave, valor in dict(datos).items() if clave != "token"}


def create_app(receiver=None, shared_secret=None, max_content_length_bytes=None):
    from flask import Flask, request

    receiver = receiver or WS2000Receiver()
    config = ws2000_config()
    if shared_secret is None:
        shared_secret = config["shared_secret"]
    if max_content_length_bytes is None:
        max_content_length_bytes = config["max_content_length_bytes"]

    app = Flask(__name__)
    if max_content_length_bytes and max_content_length_bytes > 0:
        app.config["MAX_CONTENT_LENGTH"] = max_content_length_bytes

    @app.route(DEFAULT_ROUTE, methods=["POST", "GET"])
    def recibir_datos():
        if shared_secret and not compare_digest(
            str(shared_secret),
            _request_token(request),
        ):
            return "No autorizado", 401
        datos = request.args if request.method == "GET" else request.form
        datos = _payload_sin_token(datos)
        fila = receiver.receive(datos)
        if fila is None:
            return "Sin datos", 400
        return "OK", 200

    @app.route("/", methods=["GET"])
    def estado():
        return "Servidor AWA05 activo", 200

    return app


def iniciar_servidor(host=DEFAULT_HOST, port=DEFAULT_PORT, flask_app=None):
    app = flask_app or create_app()
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    iniciar_servidor()
