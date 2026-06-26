#!/usr/bin/env bash
#
# Run the non-QEMU Phase 1 simulation checks in Docker.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker CLI not found."
    echo "Use a real Raspberry Pi validation path instead; see docs/RASPBERRY_PI_REMOTE_SETUP.md."
    exit 1
fi

echo "=== AWA05 non-QEMU Docker simulation ==="
echo "Project: ${PROJECT_ROOT}"
echo

if docker compose version >/dev/null 2>&1; then
    docker compose -f emulation/docker-compose.simulation.yml up --build --abort-on-container-exit --exit-code-from awa05-simulation
else
    docker build -f emulation/Dockerfile.simulation -t awa05-phase1-simulation:latest .
    docker run --rm \
        -e AWA05_DRY_RUN=true \
        -e AWA05_ENABLE_SHUTDOWN=false \
        -v "${PROJECT_ROOT}:/workspace" \
        -w /workspace \
        awa05-phase1-simulation:latest \
        bash emulation/simulation/phase1-check.sh
fi
