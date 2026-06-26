#!/usr/bin/env bash
#
# AWA05 Telemetry - Ready-to-use QEMU Launch Script
#
# Boots a Raspberry Pi OS image using QEMU's native raspi machine models.
# Tailored for testing the AWA05 project in an isolated environment.
#
# Features:
# - Uses qcow2 overlay (base image is never modified)
# - SSH port forward (host:2222 → guest:22)
# - Project Flask port forward (host:7777 → guest:7777)
# - Optional 9p mount of the project directory
# - Sensible defaults for memory/CPU
#
# Prerequisites:
#   sudo apt install qemu-system-aarch64 qemu-utils
#   ./../prepare-image.sh   (run once)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EMULATION_ROOT="$(dirname "${SCRIPT_DIR}")"
IMAGES_DIR="${EMULATION_ROOT}/images"
OVERLAYS_DIR="${EMULATION_ROOT}/overlays"

# --- Configuration (override via environment variables) ---
QEMU_MACHINE="${QEMU_MACHINE:-raspi3b}"
MEMORY="${MEMORY:-1G}"
SMP="${SMP:-4}"

# Base image and kernel (produced by prepare-image.sh)
# Auto-detect the latest .img if not explicitly set
if [[ -z "${BASE_IMAGE:-}" || ! -f "${BASE_IMAGE}" ]]; then
    BASE_IMAGE=$(find "${IMAGES_DIR}" -maxdepth 1 -name '*.img' -type f | sort | tail -1)
fi
KERNEL="${KERNEL:-${IMAGES_DIR}/kernel/kernel8.img}"
DTB="${DTB:-${IMAGES_DIR}/kernel/bcm2710-rpi-3-b-plus.dtb}"
KERNEL_APPEND="${KERNEL_APPEND:-rw earlyprintk loglevel=8 console=ttyAMA0,115200 console=ttyS0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 rootdelay=1 rootwait dwc_otg.lpm_enable=0}"

if [[ -z "${OVERLAY:-}" ]]; then
    OVERLAY=$(find "${OVERLAYS_DIR}" -maxdepth 1 -name '*.qcow2' -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
fi
OVERLAY="${OVERLAY:-${OVERLAYS_DIR}/awa05-pi-overlay.qcow2}"

# Networking & port forwards
SSH_PORT="${SSH_PORT:-2222}"
FLASK_PORT="${FLASK_PORT:-7777}"
QEMU_LOG="${QEMU_LOG:-${EMULATION_ROOT}/qemu-boot.log}"

# Project mount (host path). Set to empty to disable 9p mount.
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${EMULATION_ROOT}/.." && pwd)}"
MOUNT_TAG="${MOUNT_TAG:-awa05}"

# User / password for the image (Raspberry Pi OS default)
GUEST_USER="${GUEST_USER:-pi}"
GUEST_PASS="${GUEST_PASS:-raspberry}"

# Extra QEMU options
EXTRA_ARGS="${EXTRA_ARGS:-}"

port_is_free() {
    local port="$1"
    python3 - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", port))
except PermissionError:
    sys.exit(2)
except OSError:
    sys.exit(1)
finally:
    try:
        sock.close()
    except NameError:
        pass
PY
}

require_free_port() {
    local name="$1"
    local port="$2"
    set +e
    port_is_free "${port}"
    local status=$?
    set -e
    if [[ "${status}" == "2" ]]; then
        echo "WARNING: Could not pre-check host ${name} port ${port}; continuing."
        return
    fi
    if [[ "${status}" != "0" ]]; then
        echo "ERROR: Host ${name} port ${port} is already in use."
        echo
        echo "Fix options:"
        echo "  1. Pick another port:"
        echo "       ${name}_PORT=<free-port> ./qemu/launch.sh"
        echo "  2. For Flask only, disable that forward:"
        echo "       FLASK_PORT=0 ./qemu/launch.sh"
        echo "  3. Stop the process currently using the port, then retry."
        exit 1
    fi
}

# --- Validation ---
if [[ ! -f "${OVERLAY}" ]]; then
    echo "ERROR: Overlay image not found: ${OVERLAY}"
    echo "Please run ../prepare-image.sh first."
    exit 1
fi

if [[ ! -f "${KERNEL}" ]]; then
    echo "WARNING: Kernel not found at ${KERNEL}"
    echo "You may need to extract it manually or use a different kernel."
    # Still try to boot (some images can boot with -kernel not strictly required on raspi machines)
fi

echo "=== AWA05 Raspberry Pi Emulation ==="
echo "Machine : ${QEMU_MACHINE}"
echo "Memory  : ${MEMORY}"
echo "Cores   : ${SMP}"
echo "Overlay : ${OVERLAY}"
echo "SSH     : localhost:${SSH_PORT}"
if [[ "${FLASK_PORT}" == "0" || -z "${FLASK_PORT}" ]]; then
    echo "Flask   : disabled"
else
    echo "Flask   : localhost:${FLASK_PORT}"
fi
echo "Project : ${PROJECT_ROOT} (tag=${MOUNT_TAG})"
echo "Boot log: ${QEMU_LOG}"
echo "Append  : ${KERNEL_APPEND}"
echo

require_free_port "SSH" "${SSH_PORT}"
if [[ "${FLASK_PORT}" != "0" && -n "${FLASK_PORT}" ]]; then
    require_free_port "FLASK" "${FLASK_PORT}"
fi

# Build QEMU command
HOSTFWD="tcp::${SSH_PORT}-:22"
if [[ "${FLASK_PORT}" != "0" && -n "${FLASK_PORT}" ]]; then
    HOSTFWD="${HOSTFWD},hostfwd=tcp::${FLASK_PORT}-:7777"
fi

QEMU_CMD=(
    qemu-system-aarch64
    -M "${QEMU_MACHINE}"
    -m "${MEMORY}"
    -smp "${SMP}"
    -drive "file=${OVERLAY},format=qcow2,if=sd"
    -kernel "${KERNEL}"
    -dtb "${DTB}"
    -append "${KERNEL_APPEND}"
    -device "usb-net,netdev=net0"
    -netdev "user,id=net0,hostfwd=${HOSTFWD}"
    -nographic
    -no-reboot
)

# Optional 9p mount for the project (read-write from guest)
# IMPORTANT: raspi* machines in QEMU have very limited bus support.
# virtio-9p (both -pci and -device) usually fails with "No 'virtio-bus' bus found".
# We disable 9p by default for raspi machines and recommend scp/sshfs instead.
if [[ -n "${PROJECT_ROOT}" && -d "${PROJECT_ROOT}" && "${QEMU_MACHINE}" != raspi* ]]; then
    QEMU_CMD+=(
        -fsdev "local,id=fsdev0,path=${PROJECT_ROOT},security_model=mapped"
        -device "virtio-9p-device,fsdev=fsdev0,mount_tag=${MOUNT_TAG}"
    )
    echo "9p mount enabled: host ${PROJECT_ROOT} → guest /mnt/${MOUNT_TAG}"
else
    echo "9p mount disabled (not supported on ${QEMU_MACHINE} in QEMU)"
    echo "Use scp or sshfs after logging in via SSH."
fi

QEMU_CMD+=(${EXTRA_ARGS})

# Check that qemu-system-aarch64 is installed
if ! command -v qemu-system-aarch64 >/dev/null 2>&1; then
    echo "ERROR: qemu-system-aarch64 not found on this system."
    echo
    echo "Install it with:"
    echo "  Ubuntu / Debian / Pop!_OS / Linux Mint:"
    echo "      sudo apt update"
    echo "      sudo apt install qemu-system-aarch64 qemu-utils"
    echo
    echo "  Fedora / RHEL / Rocky:"
    echo "      sudo dnf install qemu-system-aarch64"
    echo
    echo "  Arch Linux:"
    echo "      sudo pacman -S qemu-system-aarch64"
    echo
    echo "After installing, re-run:"
    echo "  ./qemu/launch.sh"
    exit 1
fi

echo "Starting QEMU..."
echo "  To login: ssh -p ${SSH_PORT} ${GUEST_USER}@localhost   (password: ${GUEST_PASS})"
echo ""
echo "  Recommended: copy project from HOST terminal (while QEMU is running):"
echo "      scp -P ${SSH_PORT} -r . ${GUEST_USER}@localhost:/home/pi/awa05-telemetria"
echo ""
echo "  Then inside guest:"
echo "      cd /home/pi/awa05-telemetria"
echo "      python3 -m venv .venv && source .venv/bin/activate"
echo "      pip install -r requirements.txt"
echo "      # Run Phase 1 tests..."
echo ""
echo "Press Ctrl+A then X to quit QEMU (in -nographic mode)"
echo
echo ">>> QEMU starting - serial console output from the Pi will appear here <<<"
echo
echo "Boot output is also written to: ${QEMU_LOG}"
echo

start_seconds=${SECONDS}
"${QEMU_CMD[@]}" 2>&1 | tee "${QEMU_LOG}"
status=${PIPESTATUS[0]}
elapsed=$((SECONDS - start_seconds))
echo
echo "QEMU exited with status ${status}. Boot log: ${QEMU_LOG}"
if (( elapsed < 15 )); then
    echo
    echo "QEMU exited after ${elapsed}s, before a normal Raspberry Pi OS boot can finish."
    echo "If the log only shows repeated 'usbnet: failed control transaction' lines,"
    echo "this host QEMU raspi3b machine is probably not compatible with the selected"
    echo "Raspberry Pi OS kernel/DTB combination. Try a Bookworm Legacy/Lite image or"
    echo "use the Docker/virt-based emulation path for Phase tests."
fi
exit "${status}"
