import unittest

from awa05.core import TelemetryNode, TelemetryState, ThermalWatchdogResult


class TelemetryNodeTests(unittest.TestCase):
    def test_start_and_network_ready_transitions(self):
        node = TelemetryNode(read_level=lambda: (25.0, 100.0))

        self.assertEqual(node.current_state, TelemetryState.BOOTING)

        node.start()
        node.network_ready()

        self.assertEqual(node.current_state, TelemetryState.NORMAL)
        self.assertEqual(
            [(transition.from_state, transition.to_state) for transition in node.context.transitions],
            [
                (TelemetryState.BOOTING, TelemetryState.WAITING_NETWORK),
                (TelemetryState.WAITING_NETWORK, TelemetryState.NORMAL),
            ],
        )

    def test_telemetry_cycle_records_reading_and_uploads(self):
        calls = []
        node = TelemetryNode(
            read_level=lambda: (42.0, 123.4),
            generate_dashboard=lambda: calls.append("dashboard"),
            upload_data=lambda: calls.append("upload_data"),
        )

        result = node.run_telemetry_cycle()

        self.assertTrue(result)
        self.assertEqual(node.current_state, TelemetryState.NORMAL)
        self.assertEqual(node.context.last_distance_cm, 42.0)
        self.assertEqual(node.context.last_volume_l, 123.4)
        self.assertIsNotNone(node.context.last_successful_read_at)
        self.assertEqual(calls, ["dashboard", "upload_data"])
        self.assertIn(
            (TelemetryState.NORMAL, TelemetryState.UPLOADING),
            [(transition.from_state, transition.to_state) for transition in node.context.transitions],
        )

    def test_sensor_failures_enter_degraded_state_and_recover(self):
        readings = iter([(None, None), (None, None), (10.0, 50.0)])
        node = TelemetryNode(read_level=lambda: next(readings), max_sensor_failures=2)
        node.start()
        node.network_ready()

        self.assertFalse(node.run_telemetry_cycle())
        self.assertEqual(node.current_state, TelemetryState.NORMAL)
        self.assertEqual(node.context.consecutive_sensor_failures, 1)

        self.assertFalse(node.run_telemetry_cycle())
        self.assertEqual(node.current_state, TelemetryState.DEGRADED_SENSOR)
        self.assertEqual(node.context.consecutive_sensor_failures, 2)

        self.assertTrue(node.run_telemetry_cycle())
        self.assertEqual(node.current_state, TelemetryState.NORMAL)
        self.assertEqual(node.context.consecutive_sensor_failures, 0)
        self.assertEqual(node.context.last_distance_cm, 10.0)

    def test_successful_read_timestamp_is_injectable(self):
        node = TelemetryNode(
            read_level=lambda: (10.0, 20.0),
            timestamp_fn=lambda: "2026-06-26 12:34:56",
        )

        self.assertTrue(node.run_telemetry_cycle())

        self.assertEqual(node.context.last_successful_read_at, "2026-06-26 12:34:56")

    def test_upload_exception_enters_error_state(self):
        def fail_upload():
            raise RuntimeError("upload unavailable")

        node = TelemetryNode(read_level=lambda: (10.0, 20.0), upload_data=fail_upload)

        self.assertFalse(node.run_telemetry_cycle())
        self.assertEqual(node.current_state, TelemetryState.ERROR)
        self.assertEqual(node.context.last_error, "upload unavailable")

    def test_system_and_watchdog_cycles_are_injectable(self):
        calls = []
        node = TelemetryNode(
            read_level=lambda: (10.0, 20.0),
            generate_dashboard=lambda: calls.append("dashboard"),
            upload_dashboard=lambda: calls.append("upload_dashboard"),
            watchdog=lambda: calls.append("watchdog"),
        )
        node.start()
        node.network_ready()

        self.assertTrue(node.run_system_cycle())
        self.assertTrue(node.run_watchdog_cycle())

        self.assertEqual(node.current_state, TelemetryState.NORMAL)
        self.assertEqual(calls, ["dashboard", "upload_dashboard", "watchdog"])

    def test_watchdog_critical_enters_thermal_state_and_recovers(self):
        results = iter(
            [
                ThermalWatchdogResult(
                    temperature_c=80.0,
                    threshold_c=75.0,
                    critical=True,
                ),
                ThermalWatchdogResult(
                    temperature_c=60.0,
                    threshold_c=75.0,
                    critical=False,
                ),
            ]
        )
        node = TelemetryNode(read_level=lambda: (10.0, 20.0), watchdog=lambda: next(results))
        node.start()
        node.network_ready()

        self.assertTrue(node.run_watchdog_cycle())
        self.assertEqual(node.current_state, TelemetryState.THERMAL_CRITICAL)

        self.assertTrue(node.run_watchdog_cycle())
        self.assertEqual(node.current_state, TelemetryState.NORMAL)

    def test_watchdog_result_error_enters_error_state(self):
        node = TelemetryNode(
            read_level=lambda: (10.0, 20.0),
            watchdog=lambda: ThermalWatchdogResult(error="sensor offline"),
        )

        self.assertFalse(node.run_watchdog_cycle())

        self.assertEqual(node.current_state, TelemetryState.ERROR)
        self.assertEqual(node.context.last_error, "sensor offline")


if __name__ == "__main__":
    unittest.main()
