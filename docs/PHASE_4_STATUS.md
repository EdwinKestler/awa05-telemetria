# Phase 4 Status — Resilience, Safety & Observability

**Status**: Health endpoint slice implemented and validated.
**Date**: 2026-06-26
**Human approval to start**: Granted after Phase 3 scheduler integration review.

## Health/status slice

Approved after review. This slice added a queryable local health/status file
without changing upload policy, thermal shutdown policy, or field hardware
behavior.

Implemented:

- `awa05.core.health.node_health()`
- `awa05.core.health.write_health_status()`
- Health status writes from scheduler startup and scheduler jobs.
- `TelemetryContext.last_successful_read_at`
- Tests for health serialization, health JSON writing, scheduler health hooks,
  and injectable read timestamps.

Default health file:

```text
data/processed/health_status.json
```

The status file includes:

- generation timestamp
- current state
- last level distance/volume
- last successful level-read timestamp
- consecutive sensor failures
- last error
- transition count
- recent state transitions

## Validation expectation

Each Phase 4 slice must pass:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q awa05 scripts tests
git diff --check
```

The dummy Raspberry Pi at `sakitron@192.168.1.40` may be used only for
code/load testing. It has no AWA05 sensors connected, so it does not validate
JSN-SR04T, WS2000, HX711, or field wiring behavior.

## Validation performed for this slice

Local workstation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `git diff --check`

Observed result:

- Unit tests: 46 run; 44 passed; 2 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Diff whitespace check: passed.

Dummy Raspberry Pi code/load test:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q awa05 scripts tests`
- `AWA05_DRY_RUN=true AWA05_SCHEDULER_ESPERA_RED_MINUTOS=0 timeout 30s python scripts/scheduler.py || true`
- `python -m json.tool data/processed/health_status.json`

Observed result:

- Pi unit tests: 46 passed.
- Flask endpoint tests ran on the Pi and passed.
- Pi compile check: passed.
- Scheduler smoke generated `data/processed/health_status.json`.
- Health JSON captured state `NORMAL`, `consecutive_sensor_failures: 1`,
  no last successful read, and the expected boot/network transitions.
- The missing JSN-SR04T response is expected on this dummy Pi because no AWA05
  sensors are attached.

## Human gate

This slice is ready for human review. Request human approval before proceeding
to the next Phase 4 slice.

## WS-2000 receiver hardening slice

This slice hardens the Flask `/data` receiver while preserving backwards
compatibility:

- If no shared secret is configured, `/data` keeps accepting existing WS-2000
  GET/POST payloads.
- If `AWA05_WS2000_SHARED_SECRET` is set, `/data` requires the token through
  one of:
  - `X-AWA05-Token` header
  - `token` query parameter
  - `token` form field
- The token is stripped before payload persistence so it is not written into
  weather CSV rows.
- `MAX_CONTENT_LENGTH` is configured from `config/settings.json` and can be
  overridden with `AWA05_WS2000_MAX_CONTENT_LENGTH_BYTES`.

Configuration:

```json
"ws2000": {
  "shared_secret_env": "AWA05_WS2000_SHARED_SECRET",
  "max_content_length_bytes": 8192
}
```

Local validation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `git diff --check`

Observed result:

- Unit tests: 50 run; 45 passed; 5 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Diff whitespace check: passed.

Dummy Raspberry Pi validation:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q awa05 scripts tests`

Observed result:

- Pi unit tests: 50 passed.
- Flask endpoint tests ran on the Pi and passed, including:
  - default open GET/POST compatibility
  - missing/wrong token rejected when a shared secret is configured
  - correct token accepted through query parameter
  - correct token accepted through `X-AWA05-Token`
  - oversized payload rejected with HTTP 413
- Pi compile check: passed.

## Human gate

This WS-2000 receiver hardening slice was reviewed and approved.

## Structured job-result slice

This slice begins replacing print-only exception swallowing with structured
results while preserving current scheduler behavior.

Implemented:

- `awa05.core.errors.AWA05Error`
- `awa05.core.errors.JobResult`
- `awa05.core.errors.run_safely()`
- `ejecutar_seguro()` now returns a `JobResult` while still catching exceptions
  and printing the existing scheduler error message.
- Tests for successful and failed protected jobs.

Local validation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `git diff --check`

Observed result:

- Unit tests: 51 run; 46 passed; 5 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Diff whitespace check: passed.

Dummy Raspberry Pi validation:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q awa05 scripts tests`

Observed result:

- Pi unit tests: 51 passed.
- Flask endpoint tests ran on the Pi and passed.
- Pi compile check: passed.

## Human gate

This structured job-result slice was reviewed and approved.

## Logging foundation slice

This slice adds central logging configuration while preserving current
operator-facing print output.

Implemented:

- `awa05.core.logging.configure_logging()`
- Rotating file handler with configurable size and backup count.
- Optional console handler.
- Scheduler entrypoint initializes logging.
- `ejecutar_seguro()` writes scheduler job failures to the AWA05 logger when
  logging is configured, while preserving the existing print message.
- Legacy `configurar_log()` delegates to the new logging setup.

Configuration:

```json
"logging": {
  "enabled": true,
  "level": "INFO",
  "path": "logs/awa05.log",
  "max_bytes": 1048576,
  "backup_count": 5
}
```

Environment overrides:

- `AWA05_LOG_ENABLED`
- `AWA05_LOG_LEVEL`
- `AWA05_LOG_PATH`
- `AWA05_LOG_MAX_BYTES`
- `AWA05_LOG_BACKUP_COUNT`

Local validation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `git diff --check`

Observed result:

- Unit tests: 56 run; 51 passed; 5 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Diff whitespace check: passed.

Dummy Raspberry Pi validation:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q awa05 scripts tests`
- `AWA05_DRY_RUN=true AWA05_SCHEDULER_ESPERA_RED_MINUTOS=0 timeout 30s python scripts/scheduler.py || true`
- `test -f logs/awa05.log && ls -l logs/awa05.log`

Observed result:

- Pi unit tests: 56 passed.
- Flask endpoint tests ran on the Pi and passed.
- Pi compile check: passed.
- Scheduler smoke created `logs/awa05.log`.
- Scheduler smoke still reached the expected no-sensor JSN-SR04T warning on
  the dummy Pi.

## Human gate

This logging foundation slice was reviewed and approved.

## Thermal watchdog state slice

This slice models thermal watchdog outcomes as structured data and connects
critical temperature results to the state machine.

Implemented:

- `awa05.core.watchdog.ThermalWatchdogResult`
- `watchdog_termico()` now returns structured thermal status while preserving
  current print/report/shutdown behavior.
- Critical temperature results transition `TelemetryNode` into
  `THERMAL_CRITICAL`.
- Non-critical watchdog results recover from `THERMAL_CRITICAL` back to
  `NORMAL`.
- Watchdog result errors transition to `ERROR` with `context.last_error`.
- Tests for normal, critical, cooldown, and error watchdog outcomes.
- Tests for orchestrator thermal critical/recovery/error transitions.

Local validation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `git diff --check`

Observed result:

- Unit tests: 60 run; 55 passed; 5 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Diff whitespace check: passed.

Dummy Raspberry Pi validation:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q awa05 scripts tests`

Observed result:

- Pi unit tests: 60 passed.
- Flask endpoint tests ran on the Pi and passed.
- Pi compile check: passed.

## Human gate

This thermal watchdog state slice was reviewed and approved.

## GitHub upload retry slice

This slice adds bounded retry/backoff around real GitHub branch/file operations
without changing dry-run behavior, branch-safety policy, or token handling.

Implemented:

- `ConfigPublicacion.upload_retries`
- `ConfigPublicacion.upload_retry_delay_s`
- `AWA05_UPLOAD_RETRIES`
- `AWA05_UPLOAD_RETRY_DELAY_S`
- `_ejecutar_con_reintentos()` retry helper
- Retries around real `_asegurar_branch()` calls.
- Retries around real `_publicar_archivo()` calls.
- Dry-run uploads still avoid token/client/retry calls.
- Tests for retry success, retry exhaustion, env config, dry-run behavior, and
  real dashboard publication path using the retry wrapper.

Local validation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `git diff --check`

Observed result:

- Unit tests: 64 run; 59 passed; 5 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Diff whitespace check: passed.

Dummy Raspberry Pi validation:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q awa05 scripts tests`

Observed result:

- Pi unit tests: 64 passed.
- Flask endpoint tests ran on the Pi and passed.
- Pi compile check: passed.

## Human gate

This GitHub upload retry slice was reviewed and approved.

## Health endpoint slice

This slice exposes the existing scheduler health file through the WS-2000 Flask
server without changing `/data` ingestion behavior.

Implemented:

- `GET /health` on the existing Flask app.
- Reads `data/processed/health_status.json`.
- Returns the health JSON with HTTP 200 when the status file exists.
- Returns HTTP 503 with a small JSON error when health status has not been
  generated yet or cannot be read.
- Uses the same `AWA05_WS2000_SHARED_SECRET` token rule as `/data` when a
  shared secret is configured.
- Tests for successful JSON response, missing status file, and token
  protection.

Local validation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `git diff --check`

Observed result:

- Unit tests: 67 run; 59 passed; 8 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Diff whitespace check: passed.

Dummy Raspberry Pi validation:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q awa05 scripts tests`

Observed result:

- Pi unit tests: 67 passed.
- Flask endpoint tests ran on the Pi and passed, including:
  - `/health` returns scheduler health JSON when the file exists.
  - `/health` returns HTTP 503 when the health file is missing.
  - `/health` requires the configured shared secret token.
- Pi compile check: passed.

## Human gate

This health endpoint slice is ready for human review. Request human approval
before proceeding to the next Phase 4 slice.
