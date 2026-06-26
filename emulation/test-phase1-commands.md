# AWA05 Phase 1 Closure Tests — Commands for the Emulated Environment

This document gives you **exact commands** to run **inside** the emulated Raspberry Pi to validate Phase 1 before human closure approval.

The recommended tests are:
1. `pip install -r requirements.txt`
2. `python3 -m awa05.config`
3. `AWA05_DRY_RUN=true python3 -m awa05.upload.github`
4. `python3 scripts/scheduler.py`

---

## 1. Enter the Emulated Environment

### Option A: Native QEMU (recommended for speed)
```bash
cd /path/to/awa05-telemetria/emulation
./prepare-image.sh          # only once
./qemu/launch.sh
```

After boot (you will see the login prompt), log in:
```bash
login: pi
password: raspberry
```

### Option B: Using Docker (more isolated)
```bash
docker compose -f emulation/docker-compose.yml run --rm qemu-rpi
```

Then inside the container:
```bash
cd /app/emulation
./prepare-image.sh
./qemu/launch.sh
```

---

## 2. Inside the Guest — Mount Project and Setup

Assuming you used the 9p mount (recommended), the project should be available at `/mnt/awa05`.

```bash
# 1. Mount the project (if 9p was enabled in launch.sh)
sudo mkdir -p /mnt/awa05
sudo mount -t 9p -o trans=virtio,version=9p2000.L awa05 /mnt/awa05 || true

# 2. Go to the project
cd /mnt/awa05

# Alternative if no 9p: copy the project
# cp -r /path/on/host/awa05-telemetria /home/pi/awa05
# cd /home/pi/awa05

# 3. Create and activate venv (recommended)
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Complete Test Sequence (Recommended Commands)

Run these commands **one by one** and compare against the expected output sections below.

```bash
# === SETUP ===
source .venv/bin/activate
pip install -r requirements.txt

# === TEST 1 ===
python3 -m awa05.config

# === TEST 2 ===
AWA05_DRY_RUN=true python3 -m awa05.upload.github

# === TEST 3 (limited run) ===
timeout 30s python3 scripts/scheduler.py || true
```

Or use the helper script (recommended):

```bash
bash emulation/test-phase1-in-guest.sh
```

---

## 4. Expected Outputs and Pass/Fail Criteria

### SETUP: `pip install -r requirements.txt`

**Command:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

**Expected SUCCESS output (typical):**
```
Collecting Flask
...
Successfully installed Flask-... PyGithub-... python-dotenv-... schedule-...
```

**[SUCCESS]** — All required packages installed (warnings about `RPi.GPIO` are acceptable in emulation).

**[FAILED]** — If it hard-crashes with "No module named" on core packages (Flask, python-dotenv, etc.).

---

### TEST 1: `python3 -m awa05.config`

**Command:**
```bash
python3 -m awa05.config
```

**Expected SUCCESS output:**
```
[OK] config/settings.json válido
```

**[SUCCESS]** — You see the OK message above.

**[FAILED]** — Any traceback, "file not found", or validation error.

---

### TEST 2: `AWA05_DRY_RUN=true python3 -m awa05.upload.github`

**Command:**
```bash
AWA05_DRY_RUN=true python3 -m awa05.upload.github
```

**Expected SUCCESS output (examples):**
```
[DRY_RUN] Would publish to branch 'data'
[SKIP] Dry run mode - no actual upload performed
or
AWA05_DRY_RUN enabled — skipping real GitHub API calls
```

**[SUCCESS]** — It acknowledges dry-run mode and does **not** attempt real authentication/push (or uses the token only for simulation).

**[FAILED]** — It tries to read `.env` and fails with "Token not found" **even with** `AWA05_DRY_RUN=true`, or crashes with network errors.

> Tip: You can also try with branch control:
> `AWA05_DRY_RUN=true AWA05_DATA_BRANCH=data python3 -m awa05.upload.github`

---

### TEST 3: `python3 scripts/scheduler.py`

**Command (safe limited run):**
```bash
timeout 25s python3 scripts/scheduler.py || true
```

**Expected output (first 10-15 seconds):**
```
[SERVIDOR] Flask iniciado en puerto 7777
[SCHEDULER] Esperando 10 min para que la red levante...   (or shorter in new code)
[SCHEDULER] Lectura inicial al arrancar...
[SCHEDULER] Tomando lectura del sensor...
[SKIP] Lectura descartada, sin respuesta del sensor.     ← normal in emulation
[SCHEDULER] Generando y subiendo datos...
...
```

After ~25 seconds it will be killed.

**What to look for in the output / log:**

- Flask server starts → good
- Scheduler prints messages → good
- Sensor read attempts fail gracefully → **EXPECTED**

**[PARTIAL - EXPECTED IN EMULATION]** — Scheduler starts, logs activity, but fails on GPIO / distance sensor.

**[SUCCESS on real Pi]** — Would also complete a full `job_lectura` without crashing on sensor.

**[FAILED]** — Immediate traceback on import, or scheduler never prints any `[SCHEDULER]` or `[SERVIDOR]` messages.

---

## 5. Quick Verification Checklist

After running the commands, check these:

| Step | Command | Must See | Status in Emulation | Status on Real Pi |
|------|---------|----------|---------------------|-------------------|
| Setup | `pip install -r requirements.txt` | Packages installed | SUCCESS (or warnings) | SUCCESS |
| 1 | `python3 -m awa05.config` | `[OK] config/settings.json válido` | SUCCESS | SUCCESS |
| 2 | `AWA05_DRY_RUN=true python3 -m awa05.upload.github` | Dry-run acknowledgment | SUCCESS | SUCCESS |
| 3 | `python3 scripts/scheduler.py` (brief) | Scheduler + Flask messages | PARTIAL (GPIO fail OK) | SUCCESS |

---

## 6. Full Automated Test (Recommended)

Inside the guest, from the project root:

```bash
bash emulation/test-phase1-in-guest.sh
```

This script:
- Sets up venv
- Runs all four tests
- Captures output to a timestamped log
- Clearly marks each step with ✅ [SUCCESS], ❌ [FAILED], or ⚠️ [PARTIAL - EXPECTED IN EMULATION]

At the end it prints a summary.

---

## 7. Final Decision Criteria for Phase 1 Closure

**In Emulation (this environment):**
- Tests 1 and 2 must be **SUCCESS**
- Test 3 can be **PARTIAL** (due to missing hardware)

**On Real Raspberry Pi:**
- All four tests (including full scheduler run) must be **SUCCESS**

When both the emulated and real Pi tests pass according to the criteria above, Phase 1 is ready for human closure approval.

---

## Tips

- Always activate the venv: `source .venv/bin/activate`
- For upload test you can also export a fake token if needed: `GITHUB_TOKEN=fake AWA05_DRY_RUN=true ...`
- Kill long-running scheduler with `Ctrl+C` or `timeout`
- Check logs: `tail -100 scheduler.log` (if the test script was used)

Good luck with the Phase 1 validation!
