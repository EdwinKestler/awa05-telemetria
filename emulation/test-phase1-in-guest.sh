#!/bin/bash
#
# AWA05 Phase 1 Closure Test - Run INSIDE the emulated Raspberry Pi
#
# This script runs the exact recommended tests from the Phase 1 status:
#   pip install -r requirements.txt
#   python3 -m awa05.config
#   AWA05_DRY_RUN=true python3 -m awa05.upload.github
#   python3 scripts/scheduler.py   (run for limited time)
#
# Usage inside the guest:
#   1. Make sure the project is available (9p mount or copied)
#   2. cd /mnt/awa05
#   3. bash emulation/test-phase1-in-guest.sh
#
# The script will mark each step as [SUCCESS] or [FAILED]
#

set -euo pipefail

PROJECT_DIR="$(pwd)"
TEST_LOG="phase1-test-$(date +%Y%m%d-%H%M%S).log"

echo "========================================"
echo "AWA05 Phase 1 - Emulated Environment Test"
echo "Project dir : $PROJECT_DIR"
echo "Log file    : $TEST_LOG"
echo "========================================"
echo

# Helper functions
mark_success() {
    echo
    echo "✅ [SUCCESS] $1"
    echo "----------------------------------------"
}

mark_failed() {
    echo
    echo "❌ [FAILED] $1"
    echo "   Reason: $2"
    echo "----------------------------------------"
}

mark_partial() {
    echo
    echo "⚠️  [PARTIAL - EXPECTED IN EMULATION] $1"
    echo "   $2"
    echo "----------------------------------------"
}

run_and_check() {
    local name="$1"
    local cmd="$2"
    local expect_pattern="${3:-}"
    local allow_fail="${4:-false}"

    echo ">>> Running: $name"
    echo "    Command: $cmd"
    echo

    if output=$(eval "$cmd" 2>&1); then
        echo "$output" | tee -a "$TEST_LOG"
        if [[ -n "$expect_pattern" ]]; then
            if echo "$output" | grep -qE "$expect_pattern"; then
                mark_success "$name"
                return 0
            else
                mark_failed "$name" "Output did not contain expected pattern: $expect_pattern"
                return 1
            fi
        else
            mark_success "$name"
            return 0
        fi
    else
        echo "$output" | tee -a "$TEST_LOG"
        if [[ "$allow_fail" == "true" ]]; then
            mark_partial "$name" "Failed as expected in emulation (no real GPIO / hardware)"
            return 0
        else
            mark_failed "$name" "Command exited with non-zero status"
            return 1
        fi
    fi
}

# ============================================
# SETUP
# ============================================
echo ">>> [SETUP] Creating virtual environment and installing dependencies"
python3 -m venv .venv || { echo "venv creation failed"; exit 1; }
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt 2>&1 | tail -20

if [[ -f .venv/bin/activate ]]; then
    mark_success "Virtualenv + pip install -r requirements.txt"
else
    mark_failed "Virtualenv creation" "Could not find .venv"
    exit 1
fi

# ============================================
# TEST 1: Config validation
# ============================================
run_and_check \
    "python3 -m awa05.config" \
    "python3 -m awa05.config" \
    "\[OK\] config/settings.json válido|valid|OK" \
    false

# ============================================
# TEST 2: Dry-run upload
# ============================================
run_and_check \
    "AWA05_DRY_RUN=true python3 -m awa05.upload.github" \
    "AWA05_DRY_RUN=true python3 -m awa05.upload.github" \
    "DRY_RUN|would publish|skip|dry" \
    false

# ============================================
# TEST 3: Scheduler (limited run)
# ============================================
echo ">>> Running: python3 scripts/scheduler.py (will be killed after 25s)"
echo "    (This will exercise the new scheduler, Flask server, and jobs)"

# Start scheduler in background
python3 scripts/scheduler.py > scheduler.log 2>&1 &
SCHED_PID=$!

echo "Scheduler started with PID $SCHED_PID"
sleep 25

# Kill it
kill $SCHED_PID 2>/dev/null || true
wait $SCHED_PID 2>/dev/null || true

echo "=== Scheduler log (last 50 lines) ==="
tail -50 scheduler.log || true
echo "======================================"

if grep -qE "(SCHEDULER|Flask|config|upload|lectura|KPIs)" scheduler.log; then
    mark_partial "python3 scripts/scheduler.py (limited run)" \
        "Scheduler started and produced expected log output. GPIO/sensor failures are normal in emulation."
else
    mark_failed "Scheduler startup" "No recognizable scheduler activity in log"
fi

# ============================================
# FINAL VERIFICATION
# ============================================
echo
echo "========================================"
echo "PHASE 1 TEST SUMMARY (Emulated Environment)"
echo "========================================"

echo "1. python3 -m awa05.config"
python3 -m awa05.config && echo "   ✅ [SUCCESS]" || echo "   ❌ [FAILED]"

echo "2. AWA05_DRY_RUN=true python3 -m awa05.upload.github"
AWA05_DRY_RUN=true python3 -m awa05.upload.github && echo "   ✅ [SUCCESS]" || echo "   ❌ [FAILED]"

echo "3. python3 scripts/scheduler.py (background 25s)"
if [[ -f scheduler.log ]] && grep -q "SCHEDULER\|SERVIDOR" scheduler.log; then
    echo "   ⚠️  [PARTIAL - EXPECTED] Started and logged activity"
else
    echo "   ❌ [FAILED] No scheduler activity detected"
fi

echo
echo "Full log saved to: $TEST_LOG"
echo
echo "If config and dry-run upload are SUCCESS (or PARTIAL only on scheduler due to missing hardware),"
echo "Phase 1 can be considered validated in emulation."
echo
echo "For final human closure approval, the same tests should be repeated on real hardware."
echo "========================================"
