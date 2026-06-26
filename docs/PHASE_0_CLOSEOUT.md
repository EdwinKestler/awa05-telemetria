# Phase 0 Closeout — Emergency Stabilization

**Status**: Approved by human reviewer; Phase 1 may begin.  
**Date**: 2026-06-26  
**Scope**: Data publication containment, watchdog guardrails, documentation, and tests.

## What changed

- Automated raw data publication now targets `AWA05_DATA_BRANCH` (`data` by
  default), not `main`.
- Dashboard JSON publication now targets `AWA05_DASHBOARD_BRANCH` (`data` by
  default), not `main`.
- `AWA05_DRY_RUN=true` verifies publication paths without needing a GitHub token
  and without writing to GitHub.
- Automated publication to `main` is blocked unless
  `AWA05_ALLOW_MAIN_DATA=true` is explicitly set after human approval.
- If the data branch does not exist, the uploader can create it from `main`
  when `AWA05_CREATE_DATA_BRANCH=true`.
- Raspberry Pi thermal watchdog now has configurable threshold, cooldown,
  shutdown delay, and shutdown enable/disable flag.
- Automatic Raspberry Pi shutdown is disabled by default.
- The watchdog logs critical-temperature decisions and rate-limits repeated
  critical actions.
- `.env.example` documents operational flags.
- `.gitattributes` marks data/binary assets as binary to reduce diff noise.
- `README.md` documents dry-run, branch behavior, and the shutdown safety rule.
- `docs/REMEDIATION_PLAN.md` now includes mandatory phase gates.

## Safety note

These changes only affect Raspberry Pi telemetry behavior and Pi self-protection.
They do **not** implement direct electrical control of the AWA05 machine. Any
220 V machine stop/start control remains out of scope until separately approved
by manufacturer/electrician review.

## Verification performed

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
git diff --check
env AWA05_DRY_RUN=true AWA05_DATA_BRANCH=data python3 scripts/upload_github.py
```

Observed result:

- Unit tests: 8 passed.
- Compile check: passed.
- Diff whitespace check: passed.
- Dry-run reported raw CSV publication to `geograficaaala/awa05-telemetria@data`.

## Deployment notes for Raspberry Pi

Before deploying to the live Pi:

1. Back up current `data/`.
2. Create/update `.env` from `.env.example`.
3. Keep these defaults unless a human reviewer approves otherwise:
   - `AWA05_DATA_BRANCH=data`
   - `AWA05_DASHBOARD_BRANCH=data`
   - `AWA05_ALLOW_MAIN_DATA=false`
   - `AWA05_ENABLE_SHUTDOWN=false`
4. Run dry-run first:

   ```bash
   AWA05_DRY_RUN=true python3 scripts/upload_github.py
   ```

5. Confirm dashboard consumers know that the live HTML now reads
   `data/processed/dashboard_data.json` from the `data` branch first, with local
   same-origin data as fallback.
6. Start or restart the scheduler only after the dry-run and tests pass on the
   Pi environment.

## Rollback path

- Restore the previous commit or deployment directory on the Raspberry Pi.
- Reset `.env` to the previously used variables.
- If a `data` branch was created during deployment testing, leave it intact
  unless the human reviewer decides to delete it; deleting remote branches is not
  part of this phase.

## Human approval gate

Phase 0 should not be considered closed until a human reviewer confirms:

- [x] Data/dashboard publication target is acceptable.
- [x] Dashboard branch/source implications are understood.
- [x] Automatic commits to `main` remain blocked.
- [x] Watchdog shutdown default (`disabled`) is acceptable.
- [x] Deployment/rollback notes are sufficient.
- [x] Phase 1 may begin.

## Phase 1 readiness

Recommended first Phase 1 task: introduce an importable `awa05/` package while
keeping the current `scripts/` entry points as backward-compatible shims.
