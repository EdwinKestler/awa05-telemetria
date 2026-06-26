import unittest

from awa05.drivers.weight import SimulatedWeightSensor, UnavailableWeightSensor, leer_peso


class WeightDriverTests(unittest.TestCase):
    def test_simulated_weight_uses_configured_sequence(self):
        sensor = SimulatedWeightSensor(readings=[1.2345, 2.0])

        self.assertEqual(sensor.read(), 1.234)
        self.assertEqual(sensor.read(), 2.0)

    def test_simulated_weight_can_use_injected_random_source(self):
        sensor = SimulatedWeightSensor(random_fn=lambda low, high: 3.4567)

        self.assertEqual(sensor.read(), 3.457)

    def test_leer_peso_delega_al_sensor_inyectado(self):
        sensor = SimulatedWeightSensor(readings=[4.2])

        self.assertEqual(leer_peso(sensor=sensor), 4.2)

    def test_unavailable_weight_sensor_falla_explicitamente(self):
        with self.assertRaisesRegex(RuntimeError, "HX711 no está configurado"):
            UnavailableWeightSensor().read()


if __name__ == "__main__":
    unittest.main()
