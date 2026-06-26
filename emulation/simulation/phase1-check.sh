#!/usr/bin/env bash
#
# Phase 1 validation for non-Pi simulation environments.
#
set -euo pipefail

export AWA05_DRY_RUN="${AWA05_DRY_RUN:-true}"
export AWA05_ENABLE_SHUTDOWN="${AWA05_ENABLE_SHUTDOWN:-false}"

echo "=== AWA05 Phase 1 simulation checks ==="
python --version
echo

echo "[1/5] Compile package, scripts, and tests"
python -m compileall -q awa05 scripts tests

echo "[2/5] Run unit tests"
python -m unittest discover -s tests -v

echo "[3/5] Validate config entry point"
python -m awa05.config

echo "[4/5] Validate dry-run upload entry point"
AWA05_DRY_RUN=true python -m awa05.upload.github

echo "[5/5] Confirm hardware boundary is explicit"
python - <<'PY'
from awa05.sensors.distance import distancia_a_volumen, leer_nivel

altura, volumen = distancia_a_volumen(
    75.0,
    config={
        "altura_total_cm": 100.0,
        "altura_max_agua_cm": 50.0,
        "area_base_cm2": 200.0,
    },
)
assert (altura, volumen) == (25.0, 5.0)

try:
    leer_nivel()
except RuntimeError as exc:
    print(f"[OK] Hardware access blocked clearly in simulation: {exc}")
else:
    raise SystemExit("Expected leer_nivel() to require Raspberry Pi GPIO")
PY

echo
echo "[OK] Phase 1 simulation checks passed."
