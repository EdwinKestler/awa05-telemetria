import unittest

from awa05.drivers.distance import DistanceSensor, SimulatedDistanceSensor, distancia_a_volumen
from awa05.sensors.distance import leer_nivel


CONFIG = {
    "trig_gpio": 17,
    "echo_gpio": 18,
    "altura_total_cm": 100.0,
    "altura_max_agua_cm": 50.0,
    "area_base_cm2": 200.0,
    "distancia_min_cm": 50.0,
    "distancia_max_cm": 100.0,
    "num_muestras": 3,
    "pausa_muestras_s": 0.0,
    "timeout_echo_s": 0.1,
}


class FakeGPIO:
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"

    def __init__(self, echo_values):
        self.echo_values = list(echo_values)
        self.calls = []
        self.cleaned = False

    def setmode(self, mode):
        self.calls.append(("setmode", mode))

    def setwarnings(self, enabled):
        self.calls.append(("setwarnings", enabled))

    def setup(self, pin, mode):
        self.calls.append(("setup", pin, mode))

    def output(self, pin, value):
        self.calls.append(("output", pin, value))

    def input(self, pin):
        self.calls.append(("input", pin))
        if not self.echo_values:
            return 0
        return self.echo_values.pop(0)

    def cleanup(self):
        self.cleaned = True
        self.calls.append(("cleanup",))


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def time(self):
        self.now += 0.001
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class DistanceDriverTests(unittest.TestCase):
    def test_context_manager_sets_up_once_and_cleans_gpio(self):
        gpio = FakeGPIO(echo_values=[0, 1, 0])
        clock = FakeClock()
        sensor = DistanceSensor(
            config={**CONFIG, "num_muestras": 1},
            gpio=gpio,
            sleep_fn=clock.sleep,
            time_fn=clock.time,
            settle_seconds=0,
        )

        with sensor as active:
            self.assertIs(active, sensor)
            self.assertTrue(sensor.is_setup)
            distance = sensor.read(samples=1)

        self.assertIsNotNone(distance)
        self.assertFalse(sensor.is_setup)
        self.assertTrue(gpio.cleaned)
        self.assertIn(("setup", 17, "OUT"), gpio.calls)
        self.assertIn(("setup", 18, "IN"), gpio.calls)

    def test_read_uses_median_of_valid_samples(self):
        class StubDistanceSensor(DistanceSensor):
            def __init__(self, values):
                super().__init__(config=CONFIG, sleep_fn=lambda seconds: None)
                self.values = list(values)

            def setup(self):
                self._is_setup = True
                return self

            def _measure_once(self):
                self.setup()
                return self.values.pop(0)

        sensor = StubDistanceSensor([90.0, 70.0, 80.0])

        self.assertEqual(sensor.read(samples=3), 80.0)

    def test_simulated_sensor_returns_configured_sequence(self):
        sensor = SimulatedDistanceSensor(readings=[90.0, 70.0, 80.0], config=CONFIG)

        self.assertEqual(sensor.read(), 90.0)
        self.assertEqual(sensor.read(), 70.0)

    def test_simulated_sensor_returns_level_without_gpio(self):
        sensor = SimulatedDistanceSensor(readings=[75.0], config=CONFIG)

        distancia, volumen = leer_nivel(sensor=sensor)

        self.assertEqual(distancia, 75.0)
        self.assertEqual(volumen, 5.0)
        self.assertFalse(sensor.is_setup)

    def test_distancia_a_volumen_clamps_to_max_level(self):
        altura, volumen = distancia_a_volumen(10.0, config=CONFIG)

        self.assertEqual(altura, 50.0)
        self.assertEqual(volumen, 10.0)


if __name__ == "__main__":
    unittest.main()
