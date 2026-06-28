# Phase 5 Status — Testing, CI & Quality

**Status**: Implemented and validated for review.
**Date**: 2026-06-28
**Human approval to start**: Granted after Phases 1–4 closeout approval.

## Scope

Phase 5 establishes a repeatable quality gate that does not require a
Raspberry Pi or attached AWA05 sensors.

Implemented:

- GitHub Actions workflow: `.github/workflows/ci.yml`
- Python version matrix:
  - Python 3.11
  - Python 3.12
- CI checks:
  - editable package install
  - configuration validation
  - unit tests
  - compile check
  - GitHub upload dry-run
  - whitespace diff check
- `Makefile` local commands:
  - `make check`
  - `make ci`
  - `make test`
  - `make compile`
  - `make config`
  - `make upload-dry-run`
  - `make diff-check`
  - `make lint`
  - `make run-simulation`
- Quality contract tests that verify the workflow and Makefile keep the
  required Phase 5 checks.

## Validation expectation

Phase 5 changes must pass:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q awa05 scripts tests
python3 -m awa05.config
AWA05_DRY_RUN=true python3 -m awa05.upload.github
git diff --check
make check
```

The dummy Raspberry Pi at `sakitron@192.168.1.40` may be used only for
code/load testing. It has no AWA05 sensors connected, so it does not validate
JSN-SR04T, WS2000, HX711, or field wiring behavior.

## Known limitations

- Phase 5 does not yet add coverage thresholds because the current repository
  uses standard-library `unittest` without a coverage dependency.
- Phase 5 does not yet add ruff/mypy because the first CI gate intentionally
  uses only runtime package dependencies and Python standard-library checks.
- Real hardware validation remains outside this dummy-Pi quality gate.

## Validation performed

Local workstation:

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q awa05 scripts tests`
- `python3 -m awa05.config`
- `AWA05_DRY_RUN=true python3 -m awa05.upload.github`
- `git diff --check`
- `make check`

Observed result:

- Unit tests: 76 run; 67 passed; 9 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Config validation: passed.
- Upload dry-run: passed.
- Diff whitespace check: passed.
- `make check`: passed.

Dummy Raspberry Pi validation:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `make check`

Observed result:

- Pi unit tests: 76 passed.
- Flask endpoint tests ran on the Pi and passed.
- Pi compile check: passed.
- Pi config validation: passed.
- Pi upload dry-run: passed.
- Pi `diff-check` reported:
  - `[SKIP] git diff --check (not a git checkout)`
- The skip is expected for the dummy Pi because the rsync deployment excludes
  `.git`. GitHub Actions and local developer checkouts still run the real
  `git diff --check`.

## Human gate

This Phase 5 quality-gate slice is ready for human review. After approval, the
next planned work is Phase 6 — Sustainable Data Strategy & Long-term
Architecture.
