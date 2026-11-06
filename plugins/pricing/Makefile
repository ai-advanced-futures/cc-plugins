# Live tests of the pricing plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets PRICING_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: agent (the pricer: Path B, no offering, a person's run),
# skill (/pricing:price: an automated run, and a person's run in 2 turns), runner (the plugin-run block).
PYTEST := PRICING_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=agent|skill|runner|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),agent skill runner),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use agent|skill|runner|all"; exit 2
endif
