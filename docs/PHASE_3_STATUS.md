# Phase 3 Status — Explicit State Machine & Orchestrator

**Status**: First scaffold slice implemented and validated; not yet wired into
the live scheduler.
**Date**: 2026-06-26  
**Human approval to start**: Granted after Phase 2 code/load-test review.

## Scope of this slice

This slice adds the state-machine boundary without changing the production
scheduler entrypoint. It is intentionally reviewable and side-effect-light.

Implemented:

- `awa05.core.states.TelemetryState`
- `awa05.core.context.TelemetryContext`
- `awa05.core.context.StateTransition`
- `awa05.core.orchestrator.TelemetryNode`
- Unit tests for boot/network transitions, telemetry upload flow, degraded
  sensor behavior, recovery, error state handling, system-cycle publishing, and
  watchdog injection.

Not implemented yet:

- The live scheduler still owns runtime scheduling.
- `scripts/scheduler.py` has not been converted into a thin launcher yet.
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

## Validation performed for this slice

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

## Human gate

This slice is ready for human review. Do not replace the scheduler with this
orchestrator until a human approves the next Phase 3 integration slice.
