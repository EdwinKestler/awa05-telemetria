import importlib
import unittest


class PackageImportTests(unittest.TestCase):
    def test_phase_1_package_imports(self):
        modules = [
            "awa05",
            "awa05.config",
            "awa05.utils",
            "awa05.drivers",
            "awa05.drivers.distance",
            "awa05.drivers.system",
            "awa05.drivers.weight",
            "awa05.drivers.ws2000",
            "awa05.sensors.distance",
            "awa05.telemetry.level",
            "awa05.core.context",
            "awa05.core.errors",
            "awa05.core.health",
            "awa05.core.logging",
            "awa05.core.orchestrator",
            "awa05.core.scheduler",
            "awa05.core.states",
            "awa05.processing.dashboard",
            "awa05.upload.github",
            "awa05.core.watchdog",
        ]

        for module in modules:
            with self.subTest(module=module):
                self.assertIsNotNone(importlib.import_module(module))

    def test_script_shims_expose_existing_api(self):
        from scripts.upload_github import ConfigPublicacion, subir_archivos, subir_dashboard
        from scripts.read_distance import distancia_a_volumen, leer_nivel
        from scripts.read_weight import leer_peso, leer_peso_simulado
        from scripts.read_ws2000 import WS2000Receiver, iniciar_servidor
        from scripts.scheduler import iniciar_scheduler
        from awa05.core.watchdog import ThermalWatchdogResult
        from scripts.utils import guardar_csv, ruta_proyecto

        self.assertIsNotNone(ConfigPublicacion)
        self.assertIsNotNone(WS2000Receiver)
        self.assertTrue(callable(subir_archivos))
        self.assertTrue(callable(subir_dashboard))
        self.assertTrue(callable(distancia_a_volumen))
        self.assertTrue(callable(leer_nivel))
        self.assertTrue(callable(leer_peso))
        self.assertTrue(callable(leer_peso_simulado))
        self.assertTrue(callable(iniciar_servidor))
        self.assertTrue(callable(iniciar_scheduler))
        self.assertIsNotNone(ThermalWatchdogResult)
        self.assertTrue(callable(guardar_csv))
        self.assertTrue(callable(ruta_proyecto))


if __name__ == "__main__":
    unittest.main()
