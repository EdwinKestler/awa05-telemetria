PYTHON ?= python3

.PHONY: check ci compile config diff-check lint run-simulation test upload-dry-run

check: config test compile upload-dry-run diff-check

ci: check

config:
	$(PYTHON) -m awa05.config

test:
	$(PYTHON) -m unittest discover -s tests -v

compile:
	$(PYTHON) -m compileall -q awa05 scripts tests

upload-dry-run:
	AWA05_DRY_RUN=true $(PYTHON) -m awa05.upload.github

diff-check:
	@if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then \
		git diff --check; \
	else \
		echo "[SKIP] git diff --check (not a git checkout)"; \
	fi

lint: compile diff-check

run-simulation:
	AWA05_DRY_RUN=true \
	AWA05_SCHEDULER_ESPERA_RED_MINUTOS=0 \
	AWA05_SENSOR_READ_RETRY_DELAY_S=0 \
	timeout 30s $(PYTHON) scripts/scheduler.py || true
