import json
from secrets import compare_digest

from awa05.config import ws2000_config
from awa05.core.errors import AWA05Error
from awa05.core.health import DEFAULT_HEALTH_PATH
from awa05.utils import guardar_csv, ruta_proyecto, timestamp_ahora


DEFAULT_ROUTE = "/data"
DEFAULT_HEALTH_ROUTE = "/health"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 7777
RUTA_CLIMA = ruta_proyecto("data/raw/clima_raw.csv")


class InvalidWS2000Payload(AWA05Error):
    """Raised when a WS-2000 payload contains invalid known field values."""


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

    FIELD_RANGES = {
        "tempf": (-60.0, 160.0),
        "humidity": (0.0, 100.0),
        "dewptf": (-80.0, 160.0),
        "baromin": (20.0, 35.0),
        "windspeedmph": (0.0, 250.0),
        "winddir": (0.0, 360.0),
        "rainin": (0.0, 50.0),
        "solarradiation": (0.0, 2000.0),
        "UV": (0.0, 20.0),
    }

    def __init__(
        self,
        csv_path=None,
        guardar=guardar_csv,
        timestamp_fn=timestamp_ahora,
        validate_numeric_ranges=True,
    ):
        self.csv_path = csv_path or RUTA_CLIMA
        self.guardar = guardar
        self.timestamp_fn = timestamp_fn
        self.validate_numeric_ranges = validate_numeric_ranges

    def validar(self, datos):
        if not self.validate_numeric_ranges:
            return True

        for campo, (minimo, maximo) in self.FIELD_RANGES.items():
            valor = datos.get(campo)
            if valor in (None, ""):
                continue
            try:
                numero = float(valor)
            except (TypeError, ValueError) as exc:
                raise InvalidWS2000Payload(
                    f"Campo {campo} debe ser numérico: {valor!r}"
                ) from exc
            if numero < minimo or numero > maximo:
                raise InvalidWS2000Payload(
                    f"Campo {campo} fuera de rango: {numero} "
                    f"(esperado {minimo}..{maximo})"
                )
        return True

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
        self.validar(datos)
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


def _autorizado(request, shared_secret):
    return not shared_secret or compare_digest(
        str(shared_secret),
        _request_token(request),
    )


def _payload_sin_token(datos):
    return {clave: valor for clave, valor in dict(datos).items() if clave != "token"}


def _leer_health_status(path):
    health_path = ruta_proyecto(path)
    try:
        return json.loads(health_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def create_app(
    receiver=None,
    shared_secret=None,
    max_content_length_bytes=None,
    health_path=DEFAULT_HEALTH_PATH,
):
    from flask import Flask, jsonify, request

    config = ws2000_config()
    receiver = receiver or WS2000Receiver(
        validate_numeric_ranges=config["validate_numeric_ranges"],
    )
    if shared_secret is None:
        shared_secret = config["shared_secret"]
    if max_content_length_bytes is None:
        max_content_length_bytes = config["max_content_length_bytes"]

    app = Flask(__name__)
    if max_content_length_bytes and max_content_length_bytes > 0:
        app.config["MAX_CONTENT_LENGTH"] = max_content_length_bytes

    @app.route(DEFAULT_ROUTE, methods=["POST", "GET"])
    def recibir_datos():
        if not _autorizado(request, shared_secret):
            return "No autorizado", 401
        datos = request.args if request.method == "GET" else request.form
        datos = _payload_sin_token(datos)
        try:
            fila = receiver.receive(datos)
        except InvalidWS2000Payload as exc:
            return jsonify({"status": "invalid", "detail": str(exc)}), 400
        if fila is None:
            return "Sin datos", 400
        return "OK", 200

    @app.route("/", methods=["GET"])
    def estado():
        return "Servidor AWA05 activo", 200

    @app.route(DEFAULT_HEALTH_ROUTE, methods=["GET"])
    def health():
        if not _autorizado(request, shared_secret):
            return "No autorizado", 401
        payload = _leer_health_status(health_path)
        if payload is None:
            return (
                jsonify(
                    {
                        "status": "unavailable",
                        "detail": "health status not generated yet",
                    }
                ),
                503,
            )
        return jsonify(payload), 200

    return app


def iniciar_servidor(host=DEFAULT_HOST, port=DEFAULT_PORT, flask_app=None):
    app = flask_app or create_app()
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    iniciar_servidor()
