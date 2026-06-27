import json
import tempfile
import unittest
from pathlib import Path

from awa05.core.health import node_health, write_health_status
from awa05.core.orchestrator import TelemetryNode


class HealthTests(unittest.TestCase):
    def test_node_health_serializes_state_context_and_transitions(self):
        node = TelemetryNode(
            read_level=lambda: (12.5, 88.0),
            timestamp_fn=lambda: "2026-06-26 12:00:00",
        )

        self.assertTrue(node.run_telemetry_cycle())

        health = node_health(node, generated_at="2026-06-26 12:01:00")
        self.assertEqual(health["generated_at"], "2026-06-26 12:01:00")
        self.assertEqual(health["state"], "NORMAL")
        self.assertEqual(health["last_distance_cm"], 12.5)
        self.assertEqual(health["last_volume_l"], 88.0)
        self.assertEqual(health["last_successful_read_at"], "2026-06-26 12:00:00")
        self.assertEqual(health["consecutive_sensor_failures"], 0)
        self.assertGreaterEqual(health["transition_count"], 4)
        self.assertIn("recent_transitions", health)

    def test_write_health_status_writes_json_atomically(self):
        node = TelemetryNode(
            read_level=lambda: (10.0, 20.0),
            timestamp_fn=lambda: "2026-06-26 12:00:00",
        )
        node.run_telemetry_cycle()

        with tempfile.TemporaryDirectory() as temporal:
            path = Path(temporal) / "health_status.json"
            written_path = write_health_status(
                node,
                path=path,
                generated_at="2026-06-26 12:01:00",
            )

            self.assertEqual(written_path, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["state"], "NORMAL")
            self.assertEqual(payload["last_distance_cm"], 10.0)
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
