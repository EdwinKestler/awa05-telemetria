# Phase 1 Status — Structural Foundations

**Status**: Closed; Phase 2 may proceed.  
**Date**: 2026-06-26  
**Human approval to start**: Granted after Phase 0 approval.
**Human approval to continue**: Granted after real Raspberry Pi validation.

## Completed in this slice

- Added importable package root: `awa05/`.
- Added shared utility module: `awa05.utils`.
- Added GitHub publication module: `awa05.upload.github`.
- Added watchdog module: `awa05.core.watchdog`.
- Added dashboard processing module: `awa05.processing.dashboard`.
- Added configuration helper module: `awa05.config`.
- Scheduler timing is now read from `config/settings.json`.
- Added `python-dotenv` dependency and dotenv-backed environment loading.
- Added functional distance sensor wrapper: `awa05.sensors.distance`.
- Added level telemetry wrapper: `awa05.telemetry.level`.
- Added scheduler/orchestration wrapper: `awa05.core.scheduler`.
- Centralized JSN-SR04T GPIO pins, tank geometry, and sample/timeout parameters
  in `config/settings.json`.
- Added startup-style config validation with explicit `ConfigError` messages.
- Kept historical `scripts/` entry points working as compatibility shims.
- Added `pyproject.toml` package metadata.
- Added package/shim import tests.
- Updated live dashboards to read telemetry JSON from the `data` branch first:
  - `index.html`
  - `dashboard.html`
  - `analisis-estadistico.html`
- Kept local same-origin dashboard JSON as fallback for development.

## Verification performed

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q awa05 scripts tests
git diff --check
env AWA05_DRY_RUN=true AWA05_DATA_BRANCH=data python3 scripts/upload_github.py
env AWA05_DRY_RUN=true AWA05_DATA_BRANCH=data python3 -m awa05.upload.github
```

Observed result:

- Unit tests: 10 passed.
- Unit tests after scheduler config slice: 13 passed.
- Unit tests after package wrapper/config-validation slice: 17 passed.
- Compile check: passed.
- Diff whitespace check: passed.
- Old script uploader dry-run: passed.
- New package uploader dry-run: passed.

## Real Raspberry Pi validation

Code/load-test host:

```text
User: sakitron
Host: 192.168.1.40
Model: Raspberry Pi 3 Model B Rev 1.2
OS: Debian GNU/Linux 12 (bookworm)
Kernel: 6.12.25+rpt-rpi-v8
Python: 3.11.2
RPi.GPIO import: OK
```

Important scope note: this Raspberry Pi is a local dummy/code-testing device.
It does not have the AWA05 sensors attached and should not be treated as actual
field hardware validation.

Commands run on the Pi:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m compileall -q awa05 scripts tests
python -m unittest discover -s tests -v
python -m awa05.config
AWA05_DRY_RUN=true python -m awa05.upload.github
```

Observed result:

- Editable package install passed.
- `RPi.GPIO-0.7.1` built and installed on the Pi.
- Unit tests: 17 passed on the Pi before Phase 2 driver tests were added.
- Compile check: passed.
- Config validation: passed.
- Upload dry-run: passed and did not require GitHub authentication.
- Scheduler smoke test started Flask on `http://192.168.1.40:7777`, then waited
  the configured 10-minute network delay.

Known follow-up:

- Add a scheduler smoke-test override for `scheduler.espera_red_minutos`; the
  attempted env override did not affect this setting because Phase 1 does not
  expose scheduler timing via environment variables.

## Remaining limitations moved to later phases

- Full OOP driver lifecycle belongs to Phase 2.
- Explicit state machine/orchestrator belongs to Phase 3.
- Live dashboard freshness against the remote `data` branch should be checked
  during deployment/release, not during package-structure closure.

## Human gate

Phase 1 is ready for closure. Human approval was given to continue with the
remediation plan; Phase 2 work may proceed.
