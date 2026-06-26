#!/usr/bin/env bash
#
# AWA05 Emulation - Prepare Raspberry Pi OS Image
#
# Downloads a Raspberry Pi OS image, extracts kernel + dtb for QEMU,
# resizes it, and creates a safe qcow2 overlay.
#
# Usage:
#   ./prepare-image.sh
#   ./prepare-image.sh --help
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGES_DIR="${SCRIPT_DIR}/images"
OVERLAYS_DIR="${SCRIPT_DIR}/overlays"

# Configuration (can be overridden by env)
# IMPORTANT: Raspberry Pi OS image URLs change over time.
# Check https://downloads.raspberrypi.org/raspios_arm64/images/ for the latest folders.
# Prefer a current arm64 image URL that actually exists. If raspi3b exits early,
# try a Bookworm Legacy/Lite arm64 image from the official downloads index.
PI_OS_URL="${PI_OS_URL:-https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64-lite.img.xz}"
KERNEL_DIR="${IMAGES_DIR}/kernel"
IMAGE_NAME="${IMAGE_NAME:-}"
BASE_IMAGE="${BASE_IMAGE:-}"
OVERLAY_IMAGE="${OVERLAY_IMAGE:-}"
GUEST_USER="${GUEST_USER:-pi}"
GUEST_PASS="${GUEST_PASS:-raspberry}"
BASE_IMAGE_CHANGED=0

# QEMU machine to target (good balance for Pi 3/4 compatibility)
QEMU_MACHINE="${QEMU_MACHINE:-raspi3b}"

mkdir -p "${IMAGES_DIR}" "${OVERLAYS_DIR}" "${KERNEL_DIR}"

derive_paths() {
    if [[ -z "${IMAGE_NAME}" ]]; then
        IMAGE_NAME=$(basename "${PI_OS_URL}" | sed 's/\.img\.xz$/.img/')
    fi
    if [[ -z "${BASE_IMAGE}" ]]; then
        BASE_IMAGE="${IMAGES_DIR}/${IMAGE_NAME}"
    fi
    if [[ -z "${OVERLAY_IMAGE}" ]]; then
        local overlay_stem="${IMAGE_NAME%.img}"
        OVERLAY_IMAGE="${OVERLAYS_DIR}/${overlay_stem}-overlay.qcow2"
    fi
}

usage() {
    cat <<EOF
AWA05 Raspberry Pi Emulation Image Preparation

Usage: $0 [options]

Options:
  --url URL           Custom Raspberry Pi OS image URL (.img.xz)
                      See https://downloads.raspberrypi.org/raspios_arm64/images/
  --machine NAME      QEMU machine (default: raspi3b)
  --clean             Remove previous downloads and overlays
  --user NAME         Provision guest username (default: pi)
  --password PASS     Provision guest password (default: raspberry)
  --help              Show this help

Examples:
  ./prepare-image.sh
  ./prepare-image.sh --url 'https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64-lite.img.xz'

After preparation, run:
  ./qemu/launch.sh
EOF
}

clean() {
    echo "Cleaning images and overlays..."
    rm -rf "${IMAGES_DIR}" "${OVERLAYS_DIR}"
    echo "Done."
}

download_image() {
    if [[ -f "${BASE_IMAGE}" ]]; then
        echo "Base image already exists: ${BASE_IMAGE}"
        return
    fi

    echo "Downloading Raspberry Pi OS image..."
    local xz_file="${IMAGES_DIR}/$(basename "${PI_OS_URL}")"

    if ! wget -c --show-progress -O "${xz_file}" "${PI_OS_URL}"; then
        echo ""
        echo "ERROR: Failed to download the image."
        echo "The URL may be outdated (Raspberry Pi rotates images frequently)."
        echo ""
        echo "How to fix:"
        echo "  1. Visit: https://downloads.raspberrypi.org/raspios_arm64/images/"
        echo "  2. Pick a recent folder (e.g. raspios_arm64-2026-06-19/)"
        echo "  3. Copy the full .img.xz URL for a Bookworm or Trixie arm64 image."
        echo ""
        echo "Then re-run with:"
        echo "  ./prepare-image.sh --url 'https://downloads.raspberrypi.org/raspios_arm64/images/raspios_arm64-XXXX-XX-XX/YYYY-MM-DD-raspios-...-arm64.img.xz'"
        echo ""
        echo "Recommended for QEMU (raspi3b machine): Trixie is current; Bookworm Legacy/Lite may be more compatible if available."
        exit 1
    fi

    echo "Decompressing..."
    if ! unxz -k -f "${xz_file}"; then
        echo "ERROR: Failed to decompress. Is xz-utils installed?"
        exit 1
    fi

    # The decompressed file usually has .img extension
    local decompressed="${xz_file%.xz}"
    if [[ -f "${decompressed}" ]]; then
        # Always use the actual downloaded filename for BASE_IMAGE
        local actual_name
        actual_name=$(basename "${decompressed}")
        IMAGE_NAME="${actual_name}"
        BASE_IMAGE="${IMAGES_DIR}/${actual_name}"
        if [[ "${decompressed}" != "${BASE_IMAGE}" ]]; then
            mv "${decompressed}" "${BASE_IMAGE}"
        fi
    fi

    echo "Base image ready: ${BASE_IMAGE}"
}

extract_kernel_dtb() {
    local marker="${KERNEL_DIR}/.source-$(basename "${BASE_IMAGE}").stamp"

    if [[ -f "${marker}" && -f "${KERNEL_DIR}/kernel8.img" && -f "${KERNEL_DIR}/bcm2710-rpi-3-b-plus.dtb" ]]; then
        echo "Kernel/DTB already extracted from this image in ${KERNEL_DIR}"
        return
    fi

    echo "Extracting kernel and device tree (requires loop mount or guestfish)..."

    # Preferred: use guestfish if available (from libguestfs-tools)
    if command -v guestfish >/dev/null 2>&1; then
        echo "Using guestfish to extract kernel and dtb..."
        rm -f "${KERNEL_DIR}"/.source-*.stamp
        guestfish --ro -a "${BASE_IMAGE}" -i <<EOF
        copy-out /boot/kernel8.img ${KERNEL_DIR}/
        copy-out /boot/bcm2710-rpi-3-b-plus.dtb ${KERNEL_DIR}/
        copy-out /boot/bcm2710-rpi-3-b.dtb ${KERNEL_DIR}/ || true
EOF
    else
        echo "guestfish not found. Falling back to manual loop mount (requires sudo)..."
        # Simple loop mount method
        local loopdev
        loopdev=$(sudo losetup -f --show -P "${BASE_IMAGE}")
        sleep 1

        # Raspberry Pi OS arm64 usually puts kernel in the first or second partition
        # Try common locations
        sudo mkdir -p /mnt/pi-boot
        if sudo mount "${loopdev}p1" /mnt/pi-boot 2>/dev/null || sudo mount "${loopdev}p2" /mnt/pi-boot 2>/dev/null; then
            rm -f "${KERNEL_DIR}"/.source-*.stamp
            sudo cp /mnt/pi-boot/kernel8.img "${KERNEL_DIR}/" || true
            sudo cp /mnt/pi-boot/*.dtb "${KERNEL_DIR}/" || true
            sudo umount /mnt/pi-boot || true
        fi
        sudo losetup -d "${loopdev}" || true
    fi

    # Fallback: look for kernel in the image using qemu-nbd or just warn
    if [[ ! -f "${KERNEL_DIR}/kernel8.img" ]]; then
        echo "WARNING: Could not automatically extract kernel8.img"
        echo "You may need to:"
        echo "  1. Boot the image once in QEMU"
        echo "  2. Or manually extract using:"
        echo "     sudo apt install libguestfs-tools"
        echo "     or use 'qemu-img' + loop mount manually."
    else
        touch "${marker}"
        echo "Kernel extracted to ${KERNEL_DIR}"
    fi
}

provision_boot_files() {
    local marker="${BASE_IMAGE}.provisioned-${GUEST_USER}"
    if [[ -f "${marker}" ]]; then
        echo "Boot provisioning already applied for user '${GUEST_USER}'"
        return
    fi

    echo "Provisioning first-boot SSH access for ${GUEST_USER}..."

    if ! command -v openssl >/dev/null 2>&1; then
        echo "ERROR: openssl is required to create Raspberry Pi OS userconf.txt"
        echo "Install it with: sudo apt install openssl"
        exit 1
    fi

    local password_hash
    password_hash=$(openssl passwd -6 "${GUEST_PASS}")

    if command -v guestfish >/dev/null 2>&1; then
        local tmpdir
        tmpdir=$(mktemp -d)
        printf '%s:%s\n' "${GUEST_USER}" "${password_hash}" > "${tmpdir}/userconf.txt"
        : > "${tmpdir}/ssh"
        guestfish -a "${BASE_IMAGE}" -m /dev/sda1 <<EOF
        copy-in ${tmpdir}/userconf.txt /
        copy-in ${tmpdir}/ssh /
EOF
        rm -rf "${tmpdir}"
    else
        echo "guestfish not found. Falling back to manual loop mount (requires sudo)..."
        local loopdev
        loopdev=$(sudo losetup -f --show -P "${BASE_IMAGE}")
        sleep 1

        sudo mkdir -p /mnt/pi-boot
        if sudo mount "${loopdev}p1" /mnt/pi-boot; then
            printf '%s:%s\n' "${GUEST_USER}" "${password_hash}" | sudo tee /mnt/pi-boot/userconf.txt >/dev/null
            sudo touch /mnt/pi-boot/ssh
            sudo umount /mnt/pi-boot || true
        else
            sudo losetup -d "${loopdev}" || true
            echo "ERROR: Failed to mount Raspberry Pi OS boot partition for provisioning."
            exit 1
        fi
        sudo losetup -d "${loopdev}" || true
    fi

    touch "${marker}"
    BASE_IMAGE_CHANGED=1
    echo "SSH enabled and userconf.txt written for ${GUEST_USER}."
}

resize_image() {
    local target_size="${BASE_IMAGE_SIZE:-16G}"
    local marker="${BASE_IMAGE}.resized-${target_size}"
    local current_size
    current_size=$(qemu-img info --output=json "${BASE_IMAGE}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["virtual-size"])')
    local target_bytes
    target_bytes=$(python3 - "${target_size}" <<'PY'
import re
import sys

value = sys.argv[1].strip().upper()
match = re.fullmatch(r"(\d+)([KMGTP]?)", value)
if not match:
    raise SystemExit(f"Invalid size: {value}")
number = int(match.group(1))
unit = match.group(2)
scale = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4, "P": 1024**5}[unit]
print(number * scale)
PY
)

    if (( current_size == target_bytes )); then
        echo "Base image already at target SD size: ${target_size}"
        touch "${marker}"
        return
    fi
    if (( current_size > target_bytes )); then
        echo "ERROR: Base image (${current_size} bytes) is larger than target ${target_size}."
        echo "Set BASE_IMAGE_SIZE to a larger power-of-two size, e.g.:"
        echo "  BASE_IMAGE_SIZE=32G ./prepare-image.sh"
        exit 1
    fi

    echo "Resizing base image to QEMU-compatible SD size (${target_size})..."
    if qemu-img resize -f raw "${BASE_IMAGE}" "${target_size}"; then
        rm -f "${BASE_IMAGE}".resized*
        touch "${marker}"
        BASE_IMAGE_CHANGED=1
    else
        echo "Resize skipped or failed (may need qemu-img)"
    fi
}

create_overlay() {
    if [[ -f "${OVERLAY_IMAGE}" ]]; then
        echo "Overlay already exists: ${OVERLAY_IMAGE}"
        if [[ "${BASE_IMAGE_CHANGED}" == "1" ]]; then
            echo "WARNING: The base image changed during this run."
            echo "Recreate the overlay before booting to avoid qcow2 backing-file drift:"
            echo "  rm -f '${OVERLAY_IMAGE}'"
            echo "  ./prepare-image.sh --url '${PI_OS_URL}'"
        fi
        return
    fi

    echo "Creating qcow2 overlay (safe, base image is never modified)..."
    qemu-img create -f qcow2 -b "${BASE_IMAGE}" -F raw "${OVERLAY_IMAGE}"
    echo "Overlay created: ${OVERLAY_IMAGE}"
}

main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --url)
                PI_OS_URL="$2"
                IMAGE_NAME=""
                BASE_IMAGE=""
                OVERLAY_IMAGE=""
                shift 2 ;;
            --machine)
                QEMU_MACHINE="$2"; shift 2 ;;
            --user)
                GUEST_USER="$2"; shift 2 ;;
            --password)
                GUEST_PASS="$2"; shift 2 ;;
            --clean)
                clean; exit 0 ;;
            --help|-h)
                usage; exit 0 ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 1 ;;
        esac
    done

    derive_paths

    echo "=== AWA05 Raspberry Pi Emulation Preparation ==="
    echo "Target machine : ${QEMU_MACHINE}"
    echo "Base image     : ${BASE_IMAGE}"
    echo "Overlay image  : ${OVERLAY_IMAGE}"
    echo

    download_image
    resize_image
    extract_kernel_dtb
    provision_boot_files
    create_overlay

    echo
    echo "Preparation complete!"
    echo
    echo "Next steps:"
    echo "  1. (Optional) Install qemu-system-aarch64 if not present"
    echo "  2. Run the launch script:"
    echo "       ./qemu/launch.sh"
    echo
    echo "  Inside the guest, you can test the project with:"
    echo "       cd /mnt/awa05   # if using 9p mount, or copy the folder"
    echo "       python3 -m awa05.config"
    echo "       AWA05_DRY_RUN=true python3 -m awa05.upload.github"
}

main "$@"
