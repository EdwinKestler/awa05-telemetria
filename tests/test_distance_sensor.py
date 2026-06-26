import unittest

from awa05.sensors.distance import distancia_a_volumen


class DistanceSensorTests(unittest.TestCase):
    def test_distancia_a_volumen_usa_config_inyectada(self):
        config = {
            "altura_total_cm": 100.0,
            "altura_max_agua_cm": 50.0,
            "area_base_cm2": 200.0,
        }

        altura, volumen = distancia_a_volumen(75.0, config=config)

        self.assertEqual(altura, 25.0)
        self.assertEqual(volumen, 5.0)

    def test_distancia_a_volumen_limita_altura_maxima(self):
        config = {
            "altura_total_cm": 100.0,
            "altura_max_agua_cm": 50.0,
            "area_base_cm2": 200.0,
        }

        altura, volumen = distancia_a_volumen(10.0, config=config)

        self.assertEqual(altura, 50.0)
        self.assertEqual(volumen, 10.0)


if __name__ == "__main__":
    unittest.main()
