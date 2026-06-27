# Phase 3 Status — Explicit State Machine & Orchestrator

**Status**: Scheduler integration slice implemented and validated.
**Date**: 2026-06-26  
**Human approval to start**: Granted after Phase 2 code/load-test review.

## Scope of approved work

Phase 3 was approved for integration after the initial scaffold slice. The
current slice keeps the existing external scheduler loop and timings, but routes
runtime jobs through the explicit `TelemetryNode` state-machine boundary.

Implemented:

- `awa05.core.states.TelemetryState`
- `awa05.core.context.TelemetryContext`
- `awa05.core.context.StateTransition`
- `awa05.core.orchestrator.TelemetryNode`
- `awa05.core.scheduler.crear_nodo_telemetria()`
- Scheduler job delegation through a shared `TelemetryNode`
- Unit tests for boot/network transitions, telemetry upload flow, degraded
  sensor behavior, recovery, error state handling, system-cycle publishing, and
  watchdog injection.
- Unit tests for scheduler/node integration.

Not implemented yet:

- The external `schedule` loop still owns wall-clock scheduling.
- `scripts/scheduler.py` remains a compatibility launcher into
  `awa05.core.scheduler`.
- Real field hardware behavior has not changed.

## Current state model

Defined states:

- `BOOTING`
- `WAITING_NETWORK`
- `NORMAL`
- `DEGRADED_SENSOR`
- `UPLOADING`
- `THERMAL_CRITICAL`
- `SHUTTING_DOWN`
- `ERROR`

## Validation expectation

Each Phase 3 slice must pass:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q awa05 scripts tests
git diff --check
```

The dummy Raspberry Pi at `sakitron@192.168.1.40` may be used only for
code/load testing. It has no AWA05 sensors connected, so it does not validate
JSN-SR04T, WS2000, HX711, or field wiring behavior.

## Validation performed for scaffold slice

Local workstation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `git diff --check`

Observed result:

- Unit tests: 39 run; 37 passed; 2 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Diff whitespace check: passed.

Dummy Raspberry Pi code/load test:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q awa05 scripts tests`

Observed result:

- Pi unit tests: 39 passed.
- Flask endpoint tests ran on the Pi and passed.
- Pi compile check: passed.

## Validation performed for scheduler integration slice

Local workstation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `git diff --check`

Observed result:

- Unit tests: 43 run; 41 passed; 2 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Diff whitespace check: passed.

Dummy Raspberry Pi code/load test:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q awa05 scripts tests`
- `AWA05_DRY_RUN=true AWA05_SCHEDULER_ESPERA_RED_MINUTOS=0 timeout 30s python scripts/scheduler.py || true`

Observed result:

- Pi unit tests: 43 passed.
- Flask endpoint tests ran on the Pi and passed.
- Pi compile check: passed.
- Scheduler smoke reached startup state transitions:
  - `BOOTING -> WAITING_NETWORK`
  - `WAITING_NETWORK -> NORMAL`
- Scheduler smoke attempted the initial distance read and reported the expected
  no-sensor message on the dummy Pi:
  - `Sin respuesta JSN-SR04T — verificar TRIG(GPIO17)/ECHO(GPIO18) y 5V.`

## Human gate

This integration slice is ready for human review. Request approval before
proceeding to the next Phase 3 slice or Phase 4.
