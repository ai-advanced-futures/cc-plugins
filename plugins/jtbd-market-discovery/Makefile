# Live tests of the jtbd-market-discovery plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets JTBD_MARKET_DISCOVERY_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: checkpoint (the Phase 6 checkpoint of
# /jtbd-market-discovery:discover and 1 resume with continue, 2 turns, guards 1 + 2 USD against a runaway turn).
PYTEST := JTBD_MARKET_DISCOVERY_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=checkpoint|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifeq ($(TIER),checkpoint)
	$(PYTEST) -k "test_checkpoint_"
else
	@echo "unknown TIER '$(TIER)': use checkpoint|all"; exit 2
endif
