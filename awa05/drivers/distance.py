import logging
import time
from collections import deque

from awa05.config import sensor_distancia_config


log = logging.getLogger("awa05.drivers.distance")


def cargar_gpio():
    try:
        import RPi.GPIO as GPIO
    except ImportError as exc:
        raise RuntimeError(
            "RPi.GPIO no está instalado. Esta lectura requiere ejecutarse en Raspberry Pi "
            "o usar un sensor simulado."
        ) from exc
    return GPIO


def distancia_a_volumen(distancia_cm, config=None):
    config = config or sensor_distancia_config()
    altura = max(
        0.0,
        min(
            config["altura_total_cm"] - distancia_cm,
            config["altura_max_agua_cm"],
        ),
    )
    return round(altura, 1), round(config["area_base_cm2"] * altura / 1000.0, 2)


class DistanceSensor:
    """Driver for the JSN-SR04T/HC-SR04-style ultrasonic distance sensor.

    The driver owns GPIO setup/cleanup for one configured sensor instance and
    can be used as a context manager:

        with DistanceSensor() as sensor:
            distance_cm = sensor.read()
    """

    def __init__(
        self,
        config=None,
        gpio=None,
        sleep_fn=time.sleep,
        time_fn=time.time,
        settle_seconds=0.5,
    ):
        self.config = config or sensor_distancia_config()
        self.gpio = gpio
        self.sleep = sleep_fn
        self.time = time_fn
        self.settle_seconds = settle_seconds
        self._is_setup = False

    @property
    def is_setup(self):
        return self._is_setup

    def setup(self):
        if self._is_setup:
            return self

        if self.gpio is None:
            self.gpio = cargar_gpio()

        self.gpio.setmode(self.gpio.BCM)
        self.gpio.setwarnings(False)
        self.gpio.setup(self.config["trig_gpio"], self.gpio.OUT)
        self.gpio.setup(self.config["echo_gpio"], self.gpio.IN)
        self.gpio.output(self.config["trig_gpio"], False)
        self.sleep(self.settle_seconds)
        self._is_setup = True
        return self

    def cleanup(self):
        if self.gpio is not None and self._is_setup:
            try:
                self.gpio.cleanup()
            finally:
                self._is_setup = False

    def __enter__(self):
        return self.setup()

    def __exit__(self, exc_type, exc, tb):
        self.cleanup()
        return False

    def _measure_once(self):
        self.setup()
        trig = self.config["trig_gpio"]
        echo = self.config["echo_gpio"]
        timeout = self.config["timeout_echo_s"]

        self.gpio.output(trig, True)
        self.sleep(0.00001)
        self.gpio.output(trig, False)

        deadline = self.time() + timeout
        inicio = self.time()
        while self.gpio.input(echo) == 0:
            inicio = self.time()
            if inicio > deadline:
                log.debug("Timeout flanco ascendente")
                return None

        deadline = self.time() + timeout
        fin = self.time()
        while self.gpio.input(echo) == 1:
            fin = self.time()
            if fin > deadline:
                log.debug("Timeout flanco descendente")
                return None

        return round((fin - inicio) * 34300 / 2, 1)

    def read(self, samples=None):
        samples = samples or self.config["num_muestras"]
        measurements = []
        for i in range(samples):
            value = self._measure_once()
            if value is not None:
                measurements.append(value)
                log.debug("Muestra %s/%s: %s cm", i + 1, samples, value)
            else:
                log.debug("Muestra %s/%s: descartada", i + 1, samples)
            if i < samples - 1:
                self.sleep(self.config["pausa_muestras_s"])

        if not measurements:
            return None

        measurements.sort()
        mid = len(measurements) // 2
        if len(measurements) % 2 == 0:
            return round((measurements[mid - 1] + measurements[mid]) / 2, 1)
        return round(measurements[mid], 1)

    def read_level(self):
        distance = self.read()
        if distance is None:
            log.warning(
                "Sin respuesta JSN-SR04T — verificar TRIG(GPIO%s)/ECHO(GPIO%s) y 5V.",
                self.config["trig_gpio"],
                self.config["echo_gpio"],
            )
            return None, None

        if distance < self.config["distancia_min_cm"]:
            log.warning(
                "Distancia %s cm bajo minimo (%s cm) — recipiente lleno.",
                distance,
                self.config["distancia_min_cm"],
            )
        elif distance > self.config["distancia_max_cm"]:
            log.warning(
                "Distancia %s cm sobre maximo (%s cm) — fuera de rango.",
                distance,
                self.config["distancia_max_cm"],
            )

        altura, volumen = distancia_a_volumen(distance, config=self.config)
        log.info("Distancia: %s cm | Agua: %s cm | Volumen: %s L", distance, altura, volumen)
        return distance, volumen


class SimulatedDistanceSensor:
    """Deterministic distance sensor for tests and non-Pi simulations."""

    def __init__(self, readings=None, config=None):
        self.config = config or sensor_distancia_config()
        self.readings = deque(readings if readings is not None else [self.config["distancia_max_cm"]])
        self._is_setup = False

    @property
    def is_setup(self):
        return self._is_setup

    def setup(self):
        self._is_setup = True
        return self

    def cleanup(self):
        self._is_setup = False

    def __enter__(self):
        return self.setup()

    def __exit__(self, exc_type, exc, tb):
        self.cleanup()
        return False

    def read(self, samples=None):
        self.setup()
        if not self.readings:
            return None
        value = self.readings.popleft()
        if value is None:
            return None
        return round(float(value), 1)

    def read_level(self):
        distance = self.read()
        if distance is None:
            return None, None
        _, volume = distancia_a_volumen(distance, config=self.config)
        return distance, volume
