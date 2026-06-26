import random


class SimulatedWeightSensor:
    """Deterministic/random weight sensor for code paths without HX711 hardware."""

    def __init__(self, readings=None, random_fn=None):
        self.readings = list(readings or [])
        self.random_fn = random_fn or random.uniform

    def read(self):
        if self.readings:
            return round(float(self.readings.pop(0)), 3)
        return round(self.random_fn(0.5, 5.0), 3)


class UnavailableWeightSensor:
    """Placeholder for inactive HX711 support.

    Weight readings are not part of the active AWA05 telemetry pipeline yet.
    This class keeps failures explicit instead of silently pretending hardware
    exists.
    """

    def read(self):
        raise RuntimeError(
            "Sensor de peso HX711 no está configurado en el pipeline activo. "
            "Use SimulatedWeightSensor para pruebas o defina requerimientos de hardware."
        )


def leer_peso(sensor=None):
    sensor = sensor or SimulatedWeightSensor()
    return sensor.read()
