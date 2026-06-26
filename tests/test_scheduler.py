import unittest
from unittest.mock import Mock, patch

import awa05.core.watchdog as watchdog
import scripts.scheduler as scheduler
from scripts.utils import ejecutar_seguro


class SchedulerTests(unittest.TestCase):
    def test_ejecutar_seguro_no_propaga_error_del_trabajo(self):
        trabajo = Mock(side_effect=RuntimeError("red no disponible"))

        with patch("builtins.print") as imprimir:
            ejecutar_seguro("publicación", trabajo)

        trabajo.assert_called_once_with()
        imprimir.assert_called_once_with(
            "[SCHEDULER] Error en publicación: red no disponible"
        )

    def test_watchdog_critico_no_apaga_si_no_esta_habilitado(self):
        watchdog.reset_estado_watchdog()

        with patch("awa05.core.watchdog.cargar_config", return_value={"watchdog": {}}), \
             patch.dict(
                 "os.environ",
                 {
                     "AWA05_TEMP_CRITICA_C": "50",
                     "AWA05_ENABLE_SHUTDOWN": "false",
                     "AWA05_WATCHDOG_COOLDOWN_MINUTES": "30",
                 },
                 clear=False,
             ), \
             patch("awa05.processing.dashboard.generar_dashboard_json") as generar_dashboard, \
             patch("awa05.upload.github.subir_dashboard") as subir_dashboard, \
             patch("time.sleep") as dormir:
            ejecutar_apagado = Mock()
            scheduler.watchdog_termico(
                leer_temperatura=lambda: 80.0,
                ejecutar_apagado=ejecutar_apagado,
            )

        generar_dashboard.assert_called_once_with()
        subir_dashboard.assert_called_once_with()
        dormir.assert_not_called()
        ejecutar_apagado.assert_not_called()

    def test_watchdog_respeta_cooldown(self):
        watchdog.reset_estado_watchdog()

        with patch("awa05.core.watchdog.cargar_config", return_value={"watchdog": {}}), \
             patch.dict(
                 "os.environ",
                 {
                     "AWA05_TEMP_CRITICA_C": "50",
                     "AWA05_ENABLE_SHUTDOWN": "false",
                     "AWA05_WATCHDOG_COOLDOWN_MINUTES": "30",
                 },
                 clear=False,
             ), \
             patch("awa05.processing.dashboard.generar_dashboard_json") as generar_dashboard, \
             patch("awa05.upload.github.subir_dashboard") as subir_dashboard:
            scheduler.watchdog_termico(leer_temperatura=lambda: 80.0)
            scheduler.watchdog_termico(leer_temperatura=lambda: 80.0)

        generar_dashboard.assert_called_once_with()
        subir_dashboard.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
