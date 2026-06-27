import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import awa05.core.scheduler as core_scheduler
import awa05.core.watchdog as watchdog
import scripts.scheduler as scheduler
from scripts.utils import ejecutar_seguro


class _ScheduledJob:
    def __init__(self, interval, calls):
        self.interval = interval
        self.calls = calls

    @property
    def minutes(self):
        return self

    def do(self, *args):
        self.calls.append((self.interval, args))
        return self


class _ScheduleModule:
    def __init__(self):
        self.calls = []

    def every(self, interval):
        return _ScheduledJob(interval, self.calls)

    def run_pending(self):
        return None


class _FakeNode:
    def __init__(self):
        self.current_state = SimpleNamespace(value="BOOTING")
        self.calls = []

    def start(self):
        self.calls.append("start")
        self.current_state = SimpleNamespace(value="WAITING_NETWORK")

    def network_ready(self):
        self.calls.append("network_ready")
        self.current_state = SimpleNamespace(value="NORMAL")

    def run_telemetry_cycle(self):
        self.calls.append("run_telemetry_cycle")
        return True

    def run_system_cycle(self):
        self.calls.append("run_system_cycle")
        return True

    def run_watchdog_cycle(self):
        self.calls.append("run_watchdog_cycle")
        return True


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

    def test_jobs_delegate_to_shared_node(self):
        node = _FakeNode()
        health_calls = []
        health_writer = lambda node: health_calls.append(node.current_state.value)

        self.assertTrue(core_scheduler.job_lectura(node, health_writer=health_writer))
        self.assertTrue(core_scheduler.job_sistema(node, health_writer=health_writer))
        self.assertTrue(core_scheduler.job_watchdog(node, health_writer=health_writer))

        self.assertEqual(
            node.calls,
            ["run_telemetry_cycle", "run_system_cycle", "run_watchdog_cycle"],
        )
        self.assertEqual(health_calls, ["BOOTING", "BOOTING", "BOOTING"])

    def test_iniciar_scheduler_bootstraps_node_and_schedules_node_jobs(self):
        node = _FakeNode()
        schedule_module = _ScheduleModule()
        health_calls = []

        with patch(
            "awa05.core.scheduler.scheduler_config",
            return_value={
                "espera_red_minutos": 0,
                "lectura_intervalo_minutos": 1,
                "kpi_intervalo_minutos": 2,
                "watchdog_intervalo_minutos": 3,
            },
        ), patch("awa05.core.scheduler.time.sleep") as dormir:
            resultado = core_scheduler.iniciar_scheduler(
                schedule_module=schedule_module,
                node=node,
                run_forever=False,
                health_writer=lambda node: health_calls.append(node.current_state.value),
            )

        self.assertIs(resultado, node)
        self.assertEqual(
            node.calls,
            ["start", "network_ready", "run_telemetry_cycle"],
        )
        self.assertEqual(health_calls, ["NORMAL", "NORMAL"])
        dormir.assert_called_once_with(0)
        self.assertEqual([call[0] for call in schedule_module.calls], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
