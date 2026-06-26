import os
import re
import subprocess


class SystemMonitor:
    """Collect Raspberry Pi/system health metrics with graceful degradation."""

    def __init__(self, check_output=None, open_fn=open, statvfs_fn=os.statvfs):
        self.check_output = check_output or subprocess.check_output
        self.open = open_fn
        self.statvfs = statvfs_fn

    def _command_text(self, args, stderr=None):
        return self.check_output(args, stderr=stderr).decode().strip()

    def _vcgencmd_float(self, args, pattern):
        try:
            output = self._command_text(["vcgencmd", *args])
            return float(re.search(pattern, output).group(1))
        except Exception:
            return None

    def cpu_temperature_c(self):
        try:
            with self.open("/sys/class/thermal/thermal_zone0/temp", encoding="utf-8") as f:
                return int(f.read()) / 1000.0
        except Exception:
            return self._vcgencmd_float(["measure_temp"], r"temp=([\d.]+)")

    def voltage_v(self):
        return self._vcgencmd_float(["measure_volts"], r"volt=([\d.]+)")

    def gpu_temperature_c(self):
        return self._vcgencmd_float(["measure_temp", "core"], r"temp=([\d.]+)")

    def cpu_frequency_mhz(self):
        try:
            output = self._command_text(["vcgencmd", "measure_clock", "arm"])
            return int(re.search(r"frequency\(\d+\)=(\d+)", output).group(1)) // 1000000
        except Exception:
            return None

    def throttling(self):
        try:
            output = self._command_text(["vcgencmd", "get_throttled"])
            flags = re.search(r"throttled=(0x[\da-fA-F]+)", output).group(1)
            return int(flags, 16) == 0, flags
        except Exception:
            return True, "0x0"

    def ram_usage_pct(self):
        try:
            with self.open("/proc/meminfo", encoding="utf-8") as f:
                mem = f.read()
            total = int(re.search(r"MemTotal:\s+(\d+)", mem).group(1))
            available = int(re.search(r"MemAvailable:\s+(\d+)", mem).group(1))
            return round((total - available) / total * 100, 1)
        except Exception:
            return None

    def disk_usage_pct(self, path="/"):
        try:
            st = self.statvfs(path)
            return round((1 - st.f_bavail / st.f_blocks) * 100, 1)
        except Exception:
            return None

    def uptime(self):
        try:
            with self.open("/proc/uptime", encoding="utf-8") as f:
                uptime_s = float(f.read().split()[0])
            hours, minutes = divmod(int(uptime_s // 60), 60)
            return f"{hours}h {minutes}m"
        except Exception:
            return None

    def wifi_signal(self, interface="wlan0"):
        try:
            output = self._command_text(
                ["iwconfig", interface],
                stderr=subprocess.DEVNULL,
            )
            dbm = int(re.search(r"Signal level=(-\d+)", output).group(1))
            return dbm, max(0, min(100, 2 * (dbm + 100)))
        except Exception:
            return None, None

    def load_average(self):
        try:
            with self.open("/proc/loadavg", encoding="utf-8") as f:
                load = f.read().split()
            return float(load[0]), float(load[1]), float(load[2])
        except Exception:
            return None, None, None

    def tailscale_ip(self):
        try:
            return self._command_text(
                ["tailscale", "ip", "--4"],
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            return None

    def snapshot(self):
        throttle_ok, throttle_flags = self.throttling()
        wifi_dbm, wifi_pct = self.wifi_signal()
        load1, load5, load15 = self.load_average()
        return {
            "cpu_temp_c": self.cpu_temperature_c(),
            "voltaje_v": self.voltage_v(),
            "ram_uso_pct": self.ram_usage_pct(),
            "disco_uso_pct": self.disk_usage_pct(),
            "uptime": self.uptime(),
            "gpu_temp_c": self.gpu_temperature_c(),
            "freq_cpu_mhz": self.cpu_frequency_mhz(),
            "throttle_ok": throttle_ok,
            "throttle_flags": throttle_flags,
            "wifi_dbm": wifi_dbm,
            "wifi_pct": wifi_pct,
            "load1": load1,
            "load5": load5,
            "load15": load15,
            "tailscale_ip": self.tailscale_ip(),
        }
