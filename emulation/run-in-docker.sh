#!/usr/bin/env bash
# Convenience wrapper: run the emulation tools inside the Docker container
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building/running isolated QEMU environment..."
docker compose -f "${SCRIPT_DIR}/docker-compose.yml" run --rm qemu-rpi "$@"
