# Phase 2 Status — Hardware Abstraction Layer

**Status**: In progress; driver-boundary slices implemented.  
**Date**: 2026-06-26  
**Human approval to start**: Granted after Phase 1 real-Pi validation.

## Completed in this slice

- Added `awa05.drivers` package.
- Added `awa05.drivers.distance.DistanceSensor`.
- Added `awa05.drivers.distance.SimulatedDistanceSensor`.
- Added `awa05.drivers.system.SystemMonitor`.
- Added `awa05.drivers.ws2000.WS2000Receiver`.
- Added `awa05.drivers.weight.SimulatedWeightSensor`.
- Added `awa05.drivers.weight.UnavailableWeightSensor` to make inactive HX711
  support explicit.
- Added context-manager lifecycle for the distance sensor:
  - `setup()`
  - `read()`
  - `read_level()`
  - `cleanup()`
  - `with DistanceSensor() as sensor: ...`
- Preserved legacy compatibility through `awa05.sensors.distance` and
  `scripts/read_distance.py`.
- Added optional sensor injection in `awa05.telemetry.level.tomar_lectura()`.
- Moved dashboard system metrics to `SystemMonitor`.
- Moved watchdog CPU temperature reading to `SystemMonitor`.
- Moved WS-2000 payload normalization and Flask app creation to
  `awa05.drivers.ws2000`.
- Kept `scripts/read_ws2000.py` as a compatibility shim.
- Kept `scripts/read_weight.py` as a compatibility shim around the simulated
  weight boundary.
- Added scheduler timing environment overrides for smoke tests:
  - `AWA05_SCHEDULER_ESPERA_RED_MINUTOS`
  - `AWA05_SCHEDULER_LECTURA_INTERVALO_MINUTOS`
  - `AWA05_SCHEDULER_KPI_INTERVALO_MINUTOS`
  - `AWA05_SCHEDULER_WATCHDOG_INTERVALO_MINUTOS`
- Added tests for driver setup/cleanup, median calculation, simulation reads,
  wrapper simulation without GPIO, system metrics, WS-2000 payload handling,
  Flask endpoint behavior when Flask is installed, weight-sensor simulation,
  explicit unavailable-HX711 behavior, and scheduler overrides.

## Verification performed

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q awa05 scripts tests
git diff --check
```

Observed result:

- Unit tests: 34 passed locally. Flask endpoint tests are skipped on local
  shells where Flask is not installed.
- Compile check: passed.
- Diff whitespace check: passed.

## Raspberry Pi code/load-test validation

Target:

```text
User: sakitron
Host: 192.168.1.40
Model: Raspberry Pi 3 Model B Rev 1.2
OS: Debian GNU/Linux 12 (bookworm)
Python: 3.11.2
```

Important scope note: this Raspberry Pi is a local dummy/code-testing device.
It does not have the JSN-SR04T, WS2000, weight sensor, or AWA05 field wiring
attached. Results from this device validate package/runtime behavior on Pi OS,
not actual sensor hardware behavior.

Commands run after syncing this slice:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q awa05 scripts tests
python scripts/read_weight.py
python - <<'PY'
from awa05.drivers.system import SystemMonitor
snapshot = SystemMonitor().snapshot()
print("cpu_temp_c", snapshot["cpu_temp_c"])
print("uptime", snapshot["uptime"])
print("throttle_flags", snapshot["throttle_flags"])
PY
timeout 20s python scripts/read_distance.py || true
AWA05_DRY_RUN=true AWA05_SCHEDULER_ESPERA_RED_MINUTOS=0 timeout 30s python scripts/scheduler.py || true
```

Observed result:

- Pi unit tests: 26 passed.
- Pi unit tests after WS-2000/weight driver slices: 34 passed.
- Pi compile check: passed.
- Flask endpoint tests ran on the Pi and passed.
- Weight shim smoke test returned a simulated value, e.g.:
  - `[2026-06-26 14:08:59] Peso simulado: 4.972 kg`
- `SystemMonitor` returned live metrics:
  - `cpu_temp_c 53.692`
  - `uptime 0h 49m`
  - `throttle_flags 0x50000`
- Distance sensor wrapper did not hang and failed safely, as expected on this
  sensorless test Pi:
  - `Sin respuesta JSN-SR04T — verificar TRIG(GPIO17)/ECHO(GPIO18) y 5V.`
- Scheduler smoke-test override worked:
  - `Esperando 0 min para que la red levante...`
  - Flask started on `http://192.168.1.40:7777`
  - Initial sensor read attempted and reported no JSN-SR04T response.

## Known limitations

- Distance, system monitor, and WS-2000 receiver boundaries now exist.
- Weight sensor is not part of the active telemetry pipeline; real HX711 support
  is explicitly unavailable until requirements/hardware are approved.
- The physical JSN-SR04T was not connected on this dummy Pi, so the missing
  response is expected and is not evidence of field wiring failure.
- Actual JSN-SR04T/WS2000/weight-sensor behavior still needs validation on the
  real AWA05 hardware or a sensor-equipped bench rig before Phase 2 closure.
- `throttle_flags 0x50000` was observed on the Pi and should be interpreted
  operationally before deployment closure.

## Next recommended Phase 2 task

Add/decide the remaining driver boundaries:

1. Run driver checks on real AWA05 hardware or a sensor-equipped bench rig.
2. Review Flask receiver hardening needs for later security phase.
3. Request human review on whether Phase 2 can close or should add more driver
   abstractions first.

## Human gate

Phase 2 is not ready for closure yet. The implemented driver slices are safe to
review and test, but real hardware verification is still pending.
