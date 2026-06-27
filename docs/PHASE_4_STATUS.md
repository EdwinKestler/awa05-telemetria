# Phase 4 Status — Resilience, Safety & Observability

**Status**: First health/status slice implemented and validated.
**Date**: 2026-06-26
**Human approval to start**: Granted after Phase 3 scheduler integration review.

## Scope of this slice

This slice adds a queryable local health/status file without changing upload
policy, thermal shutdown policy, or field hardware behavior.

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
