import time

from awa05.config import sensor_retry_config
from awa05.sensors.distance import leer_nivel
from awa05.utils import guardar_csv, ruta_proyecto, timestamp_ahora


RUTA_RAW = ruta_proyecto("data/raw/nivel_raw.csv")


def _intentos_sensor(max_attempts=None, retry_delay_s=None):
    config = sensor_retry_config()
    return {
        "max_attempts": max(1, int(max_attempts or config["max_attempts"])),
        "retry_delay_s": max(
            0.0,
            float(retry_delay_s if retry_delay_s is not None else config["delay_s"]),
        ),
    }


def _leer_nivel_con_reintentos(
    sensor=None,
    max_attempts=None,
    retry_delay_s=None,
    sleep_fn=time.sleep,
    leer_fn=None,
):
    leer_fn = leer_fn or leer_nivel
    retry_config = _intentos_sensor(max_attempts, retry_delay_s)
    ultimo_error = None

    for intento in range(1, retry_config["max_attempts"] + 1):
        try:
            distancia, volumen = leer_fn(sensor=sensor)
        except RuntimeError as exc:
            ultimo_error = exc
            distancia, volumen = None, None

        if distancia is not None:
            return distancia, volumen

        if intento < retry_config["max_attempts"]:
            print(
                "[SENSOR] Lectura de nivel falló; "
                f"reintento {intento + 1}/{retry_config['max_attempts']} "
                f"en {retry_config['retry_delay_s']}s."
            )
            sleep_fn(retry_config["retry_delay_s"])

    if ultimo_error:
        print(f"[SENSOR] Último error de lectura de nivel: {ultimo_error}")
    return None, None


def tomar_lectura(
    sensor=None,
    max_attempts=None,
    retry_delay_s=None,
    sleep_fn=time.sleep,
    leer_fn=None,
):
    distancia, volumen = _leer_nivel_con_reintentos(
        sensor=sensor,
        max_attempts=max_attempts,
        retry_delay_s=retry_delay_s,
        sleep_fn=sleep_fn,
        leer_fn=leer_fn,
    )
    if distancia is None:
        print("[SKIP] Lectura descartada, sin respuesta del sensor.")
        return None, None
    fila = {
        "timestamp": timestamp_ahora(),
        "distancia_cm": distancia,
        "volumen_litros": volumen,
    }
    guardar_csv(RUTA_RAW, fila)
    print(f"[{fila['timestamp']}] Nivel: {distancia} cm | Volumen: {volumen} L")
    return distancia, volumen


if __name__ == "__main__":
    print("Sistema AWA05 iniciado.")
    tomar_lectura()
