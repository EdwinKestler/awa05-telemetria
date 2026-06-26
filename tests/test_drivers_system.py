import io
import subprocess
import unittest

from awa05.drivers.system import SystemMonitor


class StatVFS:
    f_bavail = 25
    f_blocks = 100


class SystemMonitorTests(unittest.TestCase):
    def test_snapshot_collects_metrics_with_injected_sources(self):
        files = {
            "/sys/class/thermal/thermal_zone0/temp": "42500",
            "/proc/meminfo": "MemTotal:       1000 kB\nMemAvailable:    250 kB\n",
            "/proc/uptime": "3661.00 0.00\n",
            "/proc/loadavg": "0.10 0.20 0.30 1/100 123\n",
        }
        commands = {
            ("vcgencmd", "measure_volts"): "volt=1.2000V",
            ("vcgencmd", "measure_temp", "core"): "temp=43.8'C",
            ("vcgencmd", "measure_clock", "arm"): "frequency(48)=1200000000",
            ("vcgencmd", "get_throttled"): "throttled=0x0",
            ("iwconfig", "wlan0"): "Signal level=-55 dBm",
            ("tailscale", "ip", "--4"): "100.64.0.10",
        }

        def open_fn(path, encoding=None):
            return io.StringIO(files[path])

        def check_output(args, stderr=None):
            return commands[tuple(args)].encode()

        monitor = SystemMonitor(
            check_output=check_output,
            open_fn=open_fn,
            statvfs_fn=lambda path: StatVFS(),
        )

        snapshot = monitor.snapshot()

        self.assertEqual(snapshot["cpu_temp_c"], 42.5)
        self.assertEqual(snapshot["voltaje_v"], 1.2)
        self.assertEqual(snapshot["ram_uso_pct"], 75.0)
        self.assertEqual(snapshot["disco_uso_pct"], 75.0)
        self.assertEqual(snapshot["uptime"], "1h 1m")
        self.assertEqual(snapshot["gpu_temp_c"], 43.8)
        self.assertEqual(snapshot["freq_cpu_mhz"], 1200)
        self.assertTrue(snapshot["throttle_ok"])
        self.assertEqual(snapshot["throttle_flags"], "0x0")
        self.assertEqual(snapshot["wifi_dbm"], -55)
        self.assertEqual(snapshot["wifi_pct"], 90)
        self.assertEqual(snapshot["load1"], 0.10)
        self.assertEqual(snapshot["load5"], 0.20)
        self.assertEqual(snapshot["load15"], 0.30)
        self.assertEqual(snapshot["tailscale_ip"], "100.64.0.10")

    def test_cpu_temperature_falls_back_to_vcgencmd(self):
        def open_fn(path, encoding=None):
            raise FileNotFoundError(path)

        def check_output(args, stderr=None):
            self.assertEqual(args, ["vcgencmd", "measure_temp"])
            return b"temp=47.1'C"

        monitor = SystemMonitor(check_output=check_output, open_fn=open_fn)

        self.assertEqual(monitor.cpu_temperature_c(), 47.1)

    def test_snapshot_degrades_when_commands_missing(self):
        def check_output(args, stderr=None):
            raise subprocess.CalledProcessError(1, args)

        monitor = SystemMonitor(
            check_output=check_output,
            open_fn=lambda path, encoding=None: io.StringIO(""),
            statvfs_fn=lambda path: (_ for _ in ()).throw(OSError(path)),
        )

        snapshot = monitor.snapshot()

        self.assertIsNone(snapshot["voltaje_v"])
        self.assertIsNone(snapshot["disco_uso_pct"])
        self.assertTrue(snapshot["throttle_ok"])
        self.assertEqual(snapshot["throttle_flags"], "0x0")


if __name__ == "__main__":
    unittest.main()
