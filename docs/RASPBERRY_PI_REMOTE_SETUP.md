# AWA05 Raspberry Pi remote validation path

Use this path when Raspberry Pi OS/runtime behavior is required or when local
container/QEMU strategies are not enough.

If the Pi is a dummy/code-testing device without sensors attached, treat it as a
runtime/load-test target only. It can validate packaging, imports, Pi OS
dependencies, scheduler startup, Flask binding, dry-run upload, and graceful
sensor failure. It cannot validate actual AWA05 sensor wiring or field readings.

## Goal

Validate the project on Raspberry Pi OS over SSH while keeping the same Phase
gate discipline:

1. Test the phase changes.
2. Document the result.
3. Ask for human approval before the next phase.

## Pi prerequisites

- Raspberry Pi OS installed.
- SSH enabled.
- Network access from your workstation to the Pi.
- Python 3.9+ available.
- Project dependencies installable with `pip`.

## Recommended SSH setup

On the Pi:

```bash
sudo raspi-config
```

Enable:

- Interface Options → SSH
- Interface Options → I2C/SPI only if the deployed hardware needs them

Find the Pi address:

```bash
hostname -I
```

From the workstation:

```bash
ssh pi@<pi-ip-address>
```

Optional but recommended:

```bash
ssh-copy-id pi@<pi-ip-address>
```

## Copy and test the project

From the workstation repository root:

```bash
rsync -av --delete \
  --exclude .git \
  --exclude .venv \
  --exclude __pycache__ \
  --exclude data/processed \
  --exclude data/raw/*.csv \
  ./ pi@<pi-ip-address>:/home/pi/awa05-telemetria/
```

On the Pi:

```bash
cd /home/pi/awa05-telemetria
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Run the Phase 1 checks:

```bash
python -m compileall -q awa05 scripts tests
python -m unittest discover -s tests -v
python -m awa05.config
AWA05_DRY_RUN=true python -m awa05.upload.github
```

For a short scheduler smoke test:

```bash
AWA05_DRY_RUN=true timeout 30s python scripts/scheduler.py || true
```

## What to report before phase approval

Capture:

- Pi model and OS version:

  ```bash
  cat /proc/device-tree/model
  cat /etc/os-release
  python --version
  ```

- Exact commands run.
- Pass/fail output.
- Whether this Pi is sensor-equipped or dummy/code-testing only.
- Any hardware-specific failures, especially GPIO, sensor, or network behavior.
  On a sensorless dummy Pi, missing sensor response is expected if the code
  fails safely and does not hang.
