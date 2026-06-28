# Phase 6 Status — Sustainable Data Strategy & Long-term Architecture

**Status**: Phase 6A implemented and validated for review.
**Date**: 2026-06-28
**Human decision**: Keep GitHub `data` branch as the telemetry store for now,
clean generated data from `main`, and defer cloud storage until the current
architecture is stable.

## Scope

Phase 6A closes the immediate data-history risk without changing the live
telemetry architecture.

Implemented:

- Documented the source/data branch split in `docs/DATA_STRATEGY.md`.
- Kept `data` as the default data/dashboard publication branch.
- Kept `AWA05_ALLOW_MAIN_DATA=false` as the default protection against
  automatic data commits to `main`.
- Removed generated telemetry files from `main` tracking while preserving local
  ignored copies on disk.
- Added tests for:
  - data branch defaults;
  - raw/dashboard publication paths;
  - dashboard source URLs pointing to the `data` branch;
  - generated data ignore rules;
  - no generated data files tracked in `main`.

## Out of scope

- No repository history rewrite.
- No cloud/object storage migration.
- No SQLite/API data-store migration.
- No change to dashboard runtime fetch behavior beyond documenting and testing
  the current contract.

## Validation expectation

Phase 6A changes must pass:

```bash
make check
git ls-files data
```

`git ls-files data` should return no tracked generated telemetry files on
`main`.

## Validation performed

Local workstation:

- `make check`
- `git ls-files data`
- `git diff --check`

Observed result:

- Unit tests: 81 run; 72 passed; 9 Flask endpoint tests skipped because Flask
  is not installed in the local shell.
- Compile check: passed.
- Config validation: passed.
- Upload dry-run: passed.
- Diff whitespace check: passed.
- `git ls-files data`: no tracked generated telemetry files.

Dummy Raspberry Pi validation:

- Repo synced to `/home/sakitron/awa05-telemetria`.
- `python -m pip install -e .`
- `make check`

Observed result:

- Pi unit tests: 81 run; 80 passed; 1 skipped.
- Flask endpoint tests ran on the Pi and passed.
- Pi compile check: passed.
- Pi config validation: passed.
- Pi upload dry-run: passed and skipped raw files because the dummy-Pi rsync
  intentionally excludes `data/raw/*.csv`.
- Pi `diff-check` skipped because the dummy-Pi checkout intentionally excludes
  `.git`.
- The generated-data tracking test skipped on the Pi for the same no-`.git`
  reason; it passed locally in the real git checkout.

## Human gate

This Phase 6A data strategy cleanup is ready for human review. A future Phase
6B can evaluate cloud storage or database-backed telemetry after this baseline
is stable.
