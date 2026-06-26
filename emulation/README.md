# AWA05 Telemetry — Raspberry Pi Emulation Environment

This folder provides tools to run an isolated, reproducible Raspberry Pi-like environment for testing the AWA05 project **without modifying any application code**.

## Why Emulation?

Phase 1 work (and future phases) need to validate:
- Package structure and `python -m awa05.*` entry points
- Config loading
- Dry-run upload
- Scheduler startup (up to hardware-dependent parts)
- Compatibility shims in `scripts/`

A physical Raspberry Pi is the gold standard, but an emulator helps for faster iteration.

## Docker / Container Options (Searched Results)

We evaluated container-based solutions for **isolated + replicable** full Raspberry Pi OS emulation (using QEMU under the hood):

| Project                  | Description                                                                 | Pros                                      | Cons                                      | Recommendation |
|--------------------------|-----------------------------------------------------------------------------|-------------------------------------------|-------------------------------------------|----------------|
| `lukechilds/dockerpi`    | One-command virtualised Raspberry Pi (Raspbian) inside Docker               | Extremely simple, mature                  | Changes lost unless you mount an image    | Good for quick tests |
| `ryankurte/docker-rpi-emu` | Dockerized QEMU environment tailored for Raspberry Pi development         | Good helper scripts, build-focused        | Less "full desktop" experience            | Useful for build/test |
| `ptrsr/pi-ci`            | Modern (2024) Raspberry Pi emulator Docker image for configs & flashing     | Reproducible, commands like `init/start`  | Focused more on image prep than runtime   | Strong for CI-style use |
| `stawiski/qemu-raspberrypi-3b` | Full QEMU Pi 3B inside Docker (from Memfault blog)                        | SSH port forward ready, easy to use       | Older image versions need updating        | Good base |
| `dokmic/rpi`             | Another full QEMU-based Raspberry Pi OS Docker image                      | Configurable, supports different boards   | Less widely documented                    | Viable alternative |
| Custom QEMU-in-Docker    | Run QEMU inside your own container with a real Pi OS `.img`               | Maximum control and reproducibility       | More setup                                | **Our recommended approach below** |

**Key insight**: True isolated replication is best achieved by:
- Running a **full system QEMU emulation** of Raspberry Pi OS (not just `docker --platform linux/arm64` userland).
- Using Docker to package the *QEMU launcher + tools* (or using the images above).
- Using overlay disks (qcow2) so the base image is never mutated.

`docker run --platform linux/arm64` alone is **not sufficient** for our needs because `RPi.GPIO`, `vcgencmd`, and kernel-level Pi specifics require full board emulation.

## Current Recommendation

The QEMU Raspberry Pi board path is currently **not recommended** on the tested
Ubuntu 24.04 host because current Raspberry Pi OS Trixie arm64 images exit
early under `-M raspi3b` before SSH can start.

Use the non-QEMU Docker simulation first:

```bash
cd emulation
./run-simulation.sh
```

This does not emulate Raspberry Pi hardware. It validates Phase 1 code in a
clean Linux/Python container:

- package imports
- config startup
- dry-run upload behavior
- processing/tests
- explicit hardware boundary when GPIO is unavailable

If these checks pass but hardware behavior still needs validation, use a real
Raspberry Pi over SSH. See:

```text
docs/RASPBERRY_PI_REMOTE_SETUP.md
```

## QEMU Approach Kept for Reference

1. **Use Docker** for a reproducible *host environment* that contains QEMU (optional but encouraged).
2. **Use the provided QEMU launch script** (`qemu/launch.sh`) for a tailored, ready-to-use command that boots a real Raspberry Pi OS image.
3. Mount or copy the project code into the guest for testing.

## Quick Start (Docker-based isolation)

If you have Docker:

```bash
# 1. Pull a good base (example using a maintained image)
docker pull lukechilds/dockerpi

# Or use our local helper (see docker-compose.yml)
docker compose -f emulation/docker-compose.yml up --build
```

Many people also do:

```bash
docker run -it --rm \
  -v $(pwd)/emulation/images:/images \
  lukechilds/dockerpi
```

See the individual project READMEs for mounting a real `.img` file.

## Using the Tailored QEMU Launch Script (Recommended for This Project)

```bash
cd emulation
./prepare-image.sh          # one-time: download Pi OS + prepare overlay
./qemu/launch.sh            # boots the emulated Pi
```

`prepare-image.sh` also enables SSH and provisions a default `pi` /
`raspberry` user for modern Raspberry Pi OS images. You can override that with:

```bash
./prepare-image.sh --user awa05 --password 'change-me'
```

**Important**: Image URLs expire. If `./prepare-image.sh` gives 404, run it with `--url` using a fresh link from https://downloads.raspberrypi.org/raspios_arm64/images/

Example (update date as needed):
```bash
./prepare-image.sh --url 'https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64-lite.img.xz'
```

If you previously prepared a Trixie image but the output still said
`2026-06-19-raspios-bookworm-arm64.img`, rebuild cleanly. Older versions of the
helper could keep stale names after `--url`:

```bash
cd emulation
./prepare-image.sh --clean
./prepare-image.sh --url 'https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64-lite.img.xz'
FLASK_PORT=0 ./qemu/launch.sh
```

If the base image changes after an overlay already exists, recreate the overlay
before booting:

```bash
rm -f overlays/*-overlay.qcow2
./prepare-image.sh --url 'https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64-lite.img.xz'
```

For QEMU `raspi3b`, a current Trixie Lite arm64 image is the preferred default
for this project because we only need SSH and Python test execution, not a
desktop environment. If the clean Trixie Lite rebuild still exits after only
early USB probing lines, try an official Bookworm Legacy/Lite arm64 image from
the same Raspberry Pi downloads index.

Inside the guest you can then:

```bash
# Test Phase 1 commands without touching host Python
cd /mnt/awa05   # or wherever you mounted/copied the project
pip install -r requirements.txt
python3 -m awa05.config
AWA05_DRY_RUN=true python3 -m awa05.upload.github
python3 scripts/scheduler.py   # will fail on GPIO (expected without real hardware)
```

Port forwards included by default:
- `2222` → SSH (`pi` / `raspberry` by default, or your provisioned user)
- `7777` → The project's Flask WS2000 receiver (for testing)

If QEMU exits immediately or SSH says `Connection refused`, first disable the
Flask forward because host port `7777` is commonly already used by local tests:

```bash
cd emulation
FLASK_PORT=0 ./qemu/launch.sh
```

If SSH port `2222` is busy, choose another host port:

```bash
SSH_PORT=2223 FLASK_PORT=0 ./qemu/launch.sh
ssh -p 2223 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null pi@localhost
```

To run the emulator and verify SSH automatically from the host:

```bash
SSH_PORT=2223 FLASK_PORT=0 ./verify-ssh.sh
```

The verifier launches QEMU, polls SSH, and prints the last QEMU output if the
guest exits before SSH is reachable.

The launcher writes serial/QEMU output to:

```text
emulation/qemu-boot.log
```

If the shell prompt returns, QEMU exited. Read the last lines with:

```bash
tail -120 emulation/qemu-boot.log
```

### Ubuntu 24.04 / QEMU 8.2 note

On the tested Ubuntu 24.04 host with QEMU 8.2, both the full and Lite
2026-06-18 Raspberry Pi OS Trixie arm64 images were valid downloads and prepared
correctly, but exited under `-M raspi3b` after only:

```text
usbnet: failed control transaction: request 0x8006 value 0x600 index 0x0 length 0xa
```

In that case SSH will always refuse connection because the guest never reaches
userspace. The USB lines are not the root failure; they are the last visible
symptom before the current Pi kernel/DTB and QEMU raspi3b board emulation stop.
Use `./verify-ssh.sh` to confirm this quickly before retrying manual SSH.

## Folder Contents

- `README.md` — this file
- `prepare-image.sh` — downloads a Raspberry Pi OS image, extracts kernel/dtb, creates a safe overlay
- `qemu/launch.sh` — ready-to-use QEMU command tailored for AWA05 (ports, 9p mount option, sane defaults)
- `docker-compose.yml` — optional Docker wrapper to run QEMU in an isolated container
- `images/` — (created by prepare script, gitignored)
- `overlays/` — qcow2 overlays (gitignored)

## Important Notes for AWA05 Testing

- GPIO / ultrasonic sensor will not have real hardware. `RPi.GPIO` will either fail or behave as a no-op depending on the image.
- `vcgencmd` support is partial in QEMU.
- Use `AWA05_DRY_RUN=true` to test upload logic safely.
- The compatibility shims in `scripts/` and new `awa05/` package should run fine.
- For full sensor behavior you still need the physical Raspberry Pi.

## Next Steps / Integration with Remediation Plan

This environment supports Phase 1 closure testing and will be useful for Phase 2 (hardware drivers) and Phase 3 (state machine) when we add simulation modes.

See the root `REMEDIATION_PLAN.md` and `docs/PHASE_1_STATUS.md`.

## Requirements on Host

- Linux (recommended) with `qemu-system-aarch64`
  - Ubuntu / Debian / Pop!_OS: `sudo apt install qemu-system-aarch64 qemu-utils`
- Or use the included `docker-compose.yml` (runs QEMU inside an isolated container)
- `wget`, `unxz`, `qemu-img`

The `qemu/launch.sh` script will now detect if `qemu-system-aarch64` is missing and print the exact install command for your distro.

Run `./prepare-image.sh --help` for options.

## References

- https://github.com/lukechilds/dockerpi
- https://github.com/ryankurte/docker-rpi-emu
- https://github.com/ptrsr/pi-ci
- https://interrupt.memfault.com/blog/emulating-raspberry-pi-in-qemu (great QEMU + Docker example)
- Official QEMU raspi docs

---

**Goal**: Reproducible, isolated testing of the exact current code tree.
