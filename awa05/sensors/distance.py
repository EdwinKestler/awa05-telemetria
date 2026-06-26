"""Compatibility functions for the ultrasonic level sensor.

Phase 2 introduces class-based drivers in :mod:`awa05.drivers.distance`.
This module keeps the Phase 1 / legacy function API stable while delegating
hardware lifecycle to the driver abstraction.
"""

import logging

from awa05.config import sensor_distancia_config
from awa05.drivers.distance import DistanceSensor, SimulatedDistanceSensor, distancia_a_volumen


log = logging.getLogger("read_distance")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    log.addHandler(handler)
    log.setLevel(logging.INFO)


def _gpio():
    from awa05.drivers.distance import cargar_gpio

    return cargar_gpio()


def setup(config=None, gpio=None):
    sensor = DistanceSensor(config=config, gpio=gpio).setup()
    return sensor.gpio


def _medir_una_vez(config=None, gpio=None):
    sensor = DistanceSensor(config=config, gpio=gpio, settle_seconds=0)
    return sensor._measure_once()


def medir_distancia_promedio(n=None, config=None, gpio=None):
    sensor = DistanceSensor(config=config, gpio=gpio, settle_seconds=0)
    return sensor.read(samples=n)


def leer_nivel(config=None, gpio=None, sensor=None):
    if sensor is not None:
        with sensor:
            return sensor.read_level()

    config = config or sensor_distancia_config()
    with DistanceSensor(config=config, gpio=gpio) as sensor_driver:
        return sensor_driver.read_level()


__all__ = [
    "DistanceSensor",
    "SimulatedDistanceSensor",
    "_gpio",
    "_medir_una_vez",
    "distancia_a_volumen",
    "leer_nivel",
    "medir_distancia_promedio",
    "setup",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    print("=== Prueba JSN-SR04T — AWA05 ===")
    dist, vol = leer_nivel()
    if dist is not None:
        print(f"Resultado: {dist} cm | {vol} L")
    else:
        print("Sin lectura. Revisar conexion del sensor.")
