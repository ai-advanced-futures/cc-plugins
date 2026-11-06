# Live tests of the strategic-partnerships plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets STRATEGIC_PARTNERSHIPS_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name:
# escape (1 session, the bad session id ../escape, about 0.07 USD, cap 0.3 USD),
# monetize (the full run, then partnerships-monetize on its session, about 1.1 USD, caps 2.0 + 0.8 USD).
PYTEST := STRATEGIC_PARTNERSHIPS_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=escape|monetize|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),escape monetize),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use escape|monetize|all"; exit 2
endif
