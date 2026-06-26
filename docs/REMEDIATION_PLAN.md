# AWA05 Telemetría — Remediation Plan by Phases

**Status**: Phase 0 approved; Phase 1 closed; Phase 2 in progress (2026-06-26)  
**Scope**: Python scripts, configuration, testing, data/git strategy, architecture, reliability, and maintainability.  
**Goals**:
- Stop repository bloat and data pollution on `main`.
- Improve runtime safety and reliability on the Raspberry Pi.
- Introduce proper OOP and explicit state machine design.
- Make the system testable, maintainable, and extensible.
- Preserve the ability to run the existing deployment during transition.

---

## Guiding Principles

1. **Stabilize first** — Prevent further damage to the git history and the running device.
2. **Incremental** — Changes must allow the current scheduler to keep running while refactored components are introduced behind flags or new entry points.
3. **OOP + State Machine** — Move from "bag of functions + module globals" toward encapsulated drivers and an explicit state-driven orchestrator.
4. **Testability** — Every phase should increase our ability to test without hardware.
5. **Safety** — Thermal protection, GPIO lifecycle, and error handling must be explicit and controlled.
6. **Data is not code** — Long-term, raw measurements and derived JSON should not live in the primary `main` branch history.

---

## Mandatory Phase Gate

No phase may be closed, merged, deployed to the live Raspberry Pi, or used as
the basis for the next phase until all of the following are true:

1. **Tests passed** — local automated checks for the phase have run and their
   commands/results are documented.
2. **Documentation updated** — README/runbook/config examples and this plan are
   updated for the changed behavior.
3. **Deployment/rollback noted** — the deployment path and rollback path are
   explicit before touching the live Pi.
4. **Operational safety reviewed** — any hardware, thermal, electrical, or
   remote-access impact has been reviewed. Software may request/manualize AWA05
   machine actions, but must not directly control 220 V power without separate
   manufacturer/electrician approval.
5. **Human approval recorded** — a human reviewer approves phase closure and
   separately approves the start of the next phase.
6. **Next phase ready** — open risks, known limitations, and the first task of
   the next phase are written down.

Minimum checks after every code phase:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
git diff --check
```

---

## Phase 0 — Emergency Stabilization (0–7 days)

**Priority**: Critical (P0)  
**Risk if not done**: Repository history continues to grow at ~100–150 commits/day; potential for corrupted or hard-to-recover git state.

### Objectives
- Halt or drastically reduce automated data commits to `main`.
- Add immediate guardrails around destructive operations.
- Make the current system safer to leave running.

### Key Tasks
1. **Data commit containment**
   - Modify or wrap `upload_github.py` to support a "data branch" or "dry-run" mode.
   - Add environment flag `AWA05_DATA_BRANCH` (default to a separate branch like `data` or `raw-telemetry`).
   - Update scheduler to respect the flag immediately.
   - (Recommended) Temporarily disable `subir_archivos()` and `subir_dashboard()` on main via a feature flag until Phase 6.

2. **Quick safety improvements**
   - Add a cooldown and confirmation step (or at least a strong log + configurable threshold) before `sudo shutdown`.
   - Make the critical temperature and shutdown behavior configurable.
   - Log the watchdog decision clearly.
   - Keep automatic Raspberry Pi shutdown disabled unless explicitly enabled
     after human approval.
   - Do not implement AWA05 machine power control in this phase.

3. **Stopgap hygiene**
   - Add a `.gitattributes` to mark data files as binary (reduces diff bloat).
   - Document the current situation in README (temporary measure).

4. **Backup**
   - Create a manual or scripted backup of current `data/` before any history rewrite attempts.

### Affected / New Files
- `scripts/upload_github.py` (add branch + dry-run support)
- `scripts/scheduler.py` (pass flags)
- `.env` / `.env.example`
- `README.md`
- New: `.gitattributes`

### Success Criteria
- No new data commits to `main` (or only via explicit opt-in).
- Thermal watchdog logs decisions and has a cooldown.
- Operators can run the current code without immediate repo growth.

### Verification
```bash
AWA05_DRY_RUN=true AWA05_DATA_BRANCH=data python3 scripts/upload_github.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
git diff --check
```

### Phase 0 Exit Gate
- [ ] Data/dashboard publication no longer targets `main` by default.
- [ ] Dry-run mode shows intended branch and files without using a token.
- [ ] Watchdog threshold, cooldown, and shutdown behavior are configurable.
- [ ] Automatic Raspberry Pi shutdown is disabled by default and documented.
- [ ] README, `.env.example`, and this remediation plan are updated.
- [ ] Human approval recorded before Phase 1 begins.

**Effort**: Low–Medium  
**Dependencies**: None

---

## Phase 1 — Structural Foundations (1–2 weeks)

**Priority**: High  
**Status**: Closed after local, Docker simulation, and Raspberry Pi OS
code/load-test validation on 2026-06-26. The Pi used for validation is a dummy
test device without AWA05 sensors attached, so it validates runtime/package
behavior but not field sensor readings. Scheduler, upload, watchdog, dashboard
processing, level telemetry, and distance sensor wrappers now live in `awa05/`,
while legacy `scripts/` entry points remain as compatibility shims.
**Goal**: Turn the collection of scripts into a proper, importable Python package with clean configuration.

### Objectives
- Eliminate fragile `sys.path.append` hacks.
- Centralize paths, constants, and calibration.
- Improve secret handling.
- Enable running as a module (`python -m awa05.scheduler`).

### Key Tasks
1. **Package layout**
   - Create `src/awa05/` (or `awa05/`) package.
   - Move logic into proper modules: `drivers/`, `core/`, `upload/`, `processing/`.
   - Add `__init__.py` files.
   - Update all internal imports to be relative or package-absolute.

2. **Configuration system**
   - Load tank geometry, sampling rates, paths, and thresholds from `config/settings.json` + `config/calibration.json`.
   - Remove hardcoded values from `read_distance.py`, `process_data.py`, `scheduler.py`.
   - Provide sensible defaults + validation.

3. **Secrets & environment**
   - Create `.env.example` with documented variables.
   - Replace primitive line parsing with `python-dotenv` (add to requirements) or a robust loader.
   - Validate required tokens at startup with clear error messages.

4. **Entry points**
   - Add `pyproject.toml` (or minimal `setup.cfg`) with console scripts if desired.
   - Keep backward-compatible direct script execution during transition.

### Affected / New Files
- New directory structure under `awa05/`
- `config/settings.json`, `config/calibration.json` (expand)
- `.env.example`
- `requirements.txt`
- `pyproject.toml` (new)
- `README.md` (update run instructions)

### Success Criteria
- `from awa05.drivers.distance import DistanceSensor` works without path hacks.
- All constants come from config or are injected.
- `python -m unittest discover -s tests` still passes (or is updated).

### Phase 1 Exit Gate
- [x] Package entry points validated locally.
- [x] Package entry points validated in non-QEMU Docker simulation.
- [x] Package entry points validated on Raspberry Pi OS dummy test device.
- [x] `python-dotenv` installed in the Pi virtual environment.
- [x] `RPi.GPIO` imports successfully on the Pi.
- [x] Human approval received to continue with the remediation plan.

**Effort**: Medium  
**Dependencies**: Phase 0 (for continued safe operation)

---

## Phase 2 — Hardware Abstraction Layer (Drivers)

**Priority**: High (foundational for OOP and reliability)
**Status**: In progress. First slice adds a class-based distance sensor driver
and deterministic simulator while preserving old wrapper functions.

### Objectives
- Encapsulate all hardware access behind classes.
- Fix repeated GPIO setup/cleanup problem.
- Make code runnable (with simulation) on non-Pi machines.

### Key Tasks
1. **Distance sensor driver**
   - Create `awa05/drivers/distance.py` with `class DistanceSensor`.
   - Lifecycle: `__init__`, `setup()`, `read()` (returns distance or None), `cleanup()`, context manager support (`__enter__`/`__exit__`).
   - Move geometry calculations inside the class or take calibration as constructor args.
   - Provide a `SimulatedDistanceSensor` for tests.

2. **Other drivers (as needed)**
   - `WS2000Receiver` (or keep Flask route thin and delegate).
   - Stub or implement `WeightSensor` properly if the feature is kept.
   - `SystemMonitor` class that safely collects Pi metrics (graceful degradation).

3. **GPIO ownership**
   - GPIO mode and pin setup happens once per driver instance.
   - Use `try/finally` or context managers in higher layers.
   - Consider `gpiozero` library as a more modern alternative (evaluate).

### Affected / New Files
- `awa05/drivers/distance.py` (new)
- `awa05/drivers/system.py` (new)
- Update `scripts/read_distance.py` (thin wrapper or deprecate)
- `tests/test_drivers_distance.py` (new)

### Success Criteria
- `with DistanceSensor() as s: dist = s.read()` works cleanly.
- Tests can instantiate simulated sensors without importing `RPi.GPIO`.
- `leer_nivel()` (old) can delegate to the new class during transition.

**Effort**: Medium  
**Dependencies**: Phase 1 (package structure)

---

## Phase 3 — Explicit State Machine & Orchestrator

**Priority**: High (addresses core architectural debt)

### Objectives
- Replace implicit job scheduling with an explicit finite state machine.
- Centralize lifecycle and transitions.
- Make behavior per-state clear and testable.

### Key Tasks
1. **Define states**
   - Example states: `BOOTING`, `WAITING_NETWORK`, `NORMAL`, `DEGRADED_SENSOR`, `UPLOADING`, `THERMAL_CRITICAL`, `SHUTTING_DOWN`, `ERROR`.
   - Use `enum.Enum`.

2. **State machine controller**
   - Create `awa05/core/orchestrator.py` with `TelemetryNode` class.
   - Holds current state + context (last readings, error counts, config).
   - `tick()` or event loop that evaluates timers, sensor results, and temperature → decides on transitions.
   - Entry / exit actions per state.

3. **Migrate scheduler behavior**
   - Keep the external `schedule` library initially or replace with simple timers inside the controller.
   - Move `job_lectura`, `job_sistema`, and watchdog logic into state handlers.
   - The old `iniciar_scheduler()` becomes a thin launcher.

4. **Error as state**
   - Consecutive sensor failures → transition to `DEGRADED_SENSOR` with backoff.
   - Recovery path back to `NORMAL`.

### Affected / New Files
- `awa05/core/states.py` (new enum)
- `awa05/core/orchestrator.py` (new)
- `awa05/core/context.py` (new — holds shared data)
- Refactor `scripts/scheduler.py`
- New tests for state transitions

### Success Criteria
- One can query `node.current_state` at any time.
- State transitions are logged and covered by unit tests.
- The running Pi behavior remains equivalent after migration.

**Effort**: Medium–High  
**Dependencies**: Phase 2 (drivers) — the orchestrator should use abstracted drivers.

---

## Phase 4 — Resilience, Safety & Observability

**Priority**: High

### Objectives
- Replace broad exception swallowing with structured handling.
- Make the watchdog safe and observable.
- Add real logging and health information.

### Key Tasks
1. **Error handling strategy**
   - Define retry policies for uploads and sensor reads.
   - Replace `ejecutar_seguro` with proper exception hierarchy or result objects.
   - Circuit-breaker or backoff for GitHub uploads.

2. **Improved thermal & safety subsystem**
   - Model as part of the state machine (`THERMAL_CRITICAL` state).
   - Configurable thresholds, cooldown periods, and notification hooks (future email/webhook).
   - Never shut down without logging the full context.

3. **Logging & health**
   - Use Python `logging` properly (file + console handlers).
   - Add a simple health endpoint or status file (`awa05 health` or `/health` route).
   - Include current state, last successful read timestamp, consecutive errors, etc.

4. **Flask receiver hardening**
   - Add basic auth or shared secret for `/data` (or document that it must be on a trusted network).
   - Input validation and size limits.

### Affected / New Files
- `awa05/core/errors.py` (new)
- `awa05/core/health.py` (new)
- `scripts/read_ws2000.py` (hardening)
- `config/settings.json` (add safety knobs)
- Logging configuration

### Success Criteria
- No bare `except:` left in core paths.
- Structured logs written to disk with rotation.
- Health status is queryable without parsing print output.

**Effort**: Medium  
**Dependencies**: Phase 3 (or can start in parallel with state machine work)

---

## Phase 5 — Testing, CI & Quality

**Priority**: Medium (but should start early)

### Objectives
- Achieve reliable automated verification without a Raspberry Pi.
- Prevent regressions during refactoring.

### Key Tasks
1. **Test expansion**
   - Mock all hardware (RPi.GPIO, vcgencmd, subprocess, GitHub client).
   - Add tests for new driver classes and state machine transitions.
   - Property-based or table-driven tests for the outlier filter in processing.

2. **CI pipeline**
   - Add `.github/workflows/ci.yml`:
     - Lint (ruff or flake8)
     - Type check (optional mypy)
     - Run tests on every push/PR
     - Build check (compileall or packaging)

3. **Development aids**
   - `make test`, `make lint`, `make run-simulation`.
   - Simulation mode flag that uses all simulated drivers.

### Affected / New Files
- Many new test files under `tests/`
- `.github/workflows/ci.yml` (new)
- `Makefile` or `pyproject.toml` scripts
- `tests/conftest.py` or fixtures for mocks

### Success Criteria
- `pytest` (or unittest) runs cleanly in CI.
- >70% coverage on core modules (drivers + orchestrator).
- A developer can run the full test suite on Linux/macOS without GPIO.

**Effort**: Medium  
**Dependencies**: Phases 1–3 (to have testable units)

---

## Phase 6 — Sustainable Data Strategy & Long-term Architecture

**Priority**: High (P0 long-term), can run partially in parallel with earlier phases.

### Objectives
- Remove raw data and generated JSON from polluting the `main` branch history.
- Decide on the right persistence model for this project.

### Key Tasks
1. **Data branch or external sink**
   - Route automated data updates to a dedicated `data` branch (or `telemetry-data`).
   - Or stop pushing raw CSVs entirely and use GitHub Releases, a separate data repo, or external storage (S3, etc.).

2. **Dashboard consumption**
   - Update HTML dashboards (or document) to fetch from the correct source (raw GitHub URLs on the data branch or a different hosting mechanism).

3. **Cleanup**
   - (Careful) Consider history rewrite or shallow history for old data commits (only after backups).
   - Add clear documentation: "data is not part of application source history".

4. **Optional architectural evolution**
   - Evaluate moving from file-based JSON to a lightweight local DB (SQLite) + periodic export.
   - Add an API to serve latest data instead of relying on committed files.

### Affected / New Files
- Data routing logic in upload module
- Documentation
- Possibly GitHub Pages settings or hosting scripts

### Success Criteria
- Application code commits are small and meaningful.
- Historical data growth is isolated from the main code history.
- Dashboards continue to work.

**Effort**: Medium–High  
**Dependencies**: Phase 0 (containment) + Phase 1 (config)

---

## Parallel / Cross-Cutting Tracks

- **Documentation**: Update README, add architecture diagram, runbook for operators.
- **Weight sensor**: Decide to implement properly (using Phase 2 driver pattern) or explicitly remove dead code.
- **Static analysis**: Add ruff, black formatting, and pre-commit hooks.
- **Dependency hygiene**: Pin versions in `requirements.txt` and separate runtime vs dev dependencies.

---

## High-Level Phased Roadmap (Suggested Order)

| Phase | Focus                        | Duration (est.) | Blocks / Enables          | Criticality |
|-------|------------------------------|-----------------|---------------------------|-------------|
| 0     | Emergency stabilization      | 0–1 week        | Prevents repo damage      | P0          |
| 1     | Packaging + Config           | 1–2 weeks       | Enables all later work    | High        |
| 2     | Hardware drivers (OOP)       | 1–2 weeks       | Required for Phase 3      | High        |
| 3     | State machine orchestrator   | 2–3 weeks       | Core architecture fix     | High        |
| 4     | Resilience, safety, logging  | 1–2 weeks       | Production readiness      | High        |
| 5     | Testing + CI                 | Ongoing         | Regression protection     | Medium      |
| 6     | Data strategy                | 2–4 weeks       | Long-term sustainability  | P0 (long)   |

Phases 0–2 can and should be started immediately. Phases 3+ can overlap once foundations are in place.

---

## How to Execute

1. Start with **Phase 0** items this week (data branch flag + watchdog safety).
2. Create a feature branch per phase or major component (`feat/package-structure`, `feat/distance-driver`, etc.).
3. Keep the original `scripts/` entry points working as thin shims during transition.
4. Update the running Pi only after tests pass and simulation mode works.
5. Re-evaluate the plan after Phase 2 — the state machine design may reveal further simplifications.

---

## Appendix: Current Anti-Patterns Targeted

- `sys.path.append` + `from scripts.xxx` in every file
- Module-level constants for hardware geometry and paths
- Repeated `GPIO.setup` + `GPIO.cleanup()` per reading
- Bare `except:` and `ejecutar_seguro` swallowing errors
- `os.system("sudo shutdown")` with no safeguards
- Unauthenticated Flask receiver
- Thousands of data commits on `main`
- Zero application classes / no state modeling

This plan systematically eliminates each of them.

---

**Next step recommendation**: Approve Phase 0 + Phase 1 scope, then begin implementation on a dedicated branch.
