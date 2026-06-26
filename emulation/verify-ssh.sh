#!/usr/bin/env bash
#
# Launch the QEMU Raspberry Pi emulation and verify SSH becomes reachable.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_PORT="${SSH_PORT:-2223}"
FLASK_PORT="${FLASK_PORT:-0}"
GUEST_USER="${GUEST_USER:-pi}"
GUEST_PASS="${GUEST_PASS:-raspberry}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"
QEMU_LOG="${QEMU_LOG:-${SCRIPT_DIR}/qemu-boot.log}"
VERIFY_LOG="${VERIFY_LOG:-${SCRIPT_DIR}/qemu-verify.log}"

cd "${SCRIPT_DIR}"

rm -f "${VERIFY_LOG}"

echo "=== AWA05 QEMU SSH verification ==="
echo "SSH     : localhost:${SSH_PORT}"
echo "Flask   : ${FLASK_PORT}"
echo "Timeout : ${TIMEOUT_SECONDS}s"
echo "Log     : ${QEMU_LOG}"
echo

SSH_PORT="${SSH_PORT}" FLASK_PORT="${FLASK_PORT}" ./qemu/launch.sh >"${VERIFY_LOG}" 2>&1 &
qemu_pid=$!

cleanup() {
    if kill -0 "${qemu_pid}" >/dev/null 2>&1; then
        kill "${qemu_pid}" >/dev/null 2>&1 || true
        wait "${qemu_pid}" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

deadline=$((SECONDS + TIMEOUT_SECONDS))
while (( SECONDS < deadline )); do
    if ! kill -0 "${qemu_pid}" >/dev/null 2>&1; then
        echo "ERROR: QEMU exited before SSH became reachable."
        echo
        echo "Last QEMU output:"
        tail -80 "${VERIFY_LOG}" || true
        exit 1
    fi

    if command -v sshpass >/dev/null 2>&1; then
        if sshpass -p "${GUEST_PASS}" ssh \
            -p "${SSH_PORT}" \
            -o StrictHostKeyChecking=no \
            -o UserKnownHostsFile=/dev/null \
            -o ConnectTimeout=3 \
            "${GUEST_USER}@localhost" \
            "echo awa05-ssh-ok" 2>/dev/null | grep -q "awa05-ssh-ok"; then
            echo "SSH verification passed: ${GUEST_USER}@localhost:${SSH_PORT}"
            exit 0
        fi
    else
        if ssh \
            -p "${SSH_PORT}" \
            -o BatchMode=yes \
            -o StrictHostKeyChecking=no \
            -o UserKnownHostsFile=/dev/null \
            -o ConnectTimeout=3 \
            "${GUEST_USER}@localhost" \
            "echo awa05-ssh-ok" 2>/dev/null | grep -q "awa05-ssh-ok"; then
            echo "SSH verification passed: ${GUEST_USER}@localhost:${SSH_PORT}"
            exit 0
        fi
    fi

    sleep 3
done

echo "ERROR: SSH did not become reachable within ${TIMEOUT_SECONDS}s."
echo
echo "Last QEMU output:"
tail -80 "${VERIFY_LOG}" || true
exit 1
