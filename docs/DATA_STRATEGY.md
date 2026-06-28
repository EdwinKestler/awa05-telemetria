# AWA05 Data Strategy

**Status**: Phase 6A baseline. GitHub `data` branch remains the telemetry
store for now; cloud storage is deferred until the current architecture is
stable.

## Source vs. generated data

The repository has two different kinds of content:

- `main`: application source code, configuration templates, dashboards,
  documentation, tests, and deployment helpers.
- `data`: runtime telemetry and generated dashboard artifacts published by the
  Raspberry Pi.

Generated telemetry must not be committed to `main`.

## Current storage decision

For the current stable architecture:

- raw level/weather CSV files are published to the GitHub `data` branch;
- dashboard JSON is published to the GitHub `data` branch;
- dashboards fetch from raw GitHub URLs on the `data` branch first;
- dashboards may fall back to local `data/processed/*.json` for development;
- the Raspberry Pi may keep local CSV/JSON files as runtime cache.

Cloud storage, external databases, and object stores are intentionally deferred
until the package, scheduler, health, and CI foundations remain stable in
operation.

## Branch policy

Default environment:

```text
AWA05_APP_BRANCH=main
AWA05_DATA_BRANCH=data
AWA05_DASHBOARD_BRANCH=data
AWA05_ALLOW_MAIN_DATA=false
```

Automatic commits to `main` are blocked unless
`AWA05_ALLOW_MAIN_DATA=true` is set after explicit human approval.

## Files intentionally ignored on `main`

The following runtime/generated files are ignored in the application branch:

```text
data/raw/*.csv
data/processed/
```

If local development needs sample data, keep it outside git tracking or add a
small synthetic fixture under `tests/fixtures/`.

## Dashboard source contract

Dashboards should load telemetry from the `data` branch first:

```text
https://raw.githubusercontent.com/geograficaaala/awa05-telemetria/data/data/processed/dashboard_data.json
```

Development fallback:

```text
./data/processed/dashboard_data.json
```

The statistical analysis dashboard also expects:

```text
https://raw.githubusercontent.com/geograficaaala/awa05-telemetria/data/data/processed/statistical_analysis.json
```

## Cleanup policy

Phase 6A only removes generated data from `main` going forward. It does not
rewrite repository history.

History rewrite or archival compaction may be considered later only after:

1. backing up existing telemetry data;
2. confirming the `data` branch has the required live artifacts;
3. confirming dashboards still work from the chosen data source;
4. obtaining explicit human approval.

## Future options

After the current architecture is stable, evaluate:

- Google Cloud Storage or another object store;
- a separate telemetry-data repository;
- SQLite on the Raspberry Pi with periodic export;
- a small API endpoint for latest data.

These are not part of Phase 6A.
