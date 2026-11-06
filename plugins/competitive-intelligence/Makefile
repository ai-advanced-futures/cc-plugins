# Live tests of the competitive-intelligence plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets COMPETITIVE_INTELLIGENCE_ITEST=1, the money gate that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: registration (1 session, the skills and agents it lists),
# discover (1 live /competitive-intelligence:discover quick scan, about 0.87 USD, cap 0.9 USD).
# TIER=all can cost up to 1.15 USD (the caps of the 2 sessions).
PYTEST := COMPETITIVE_INTELLIGENCE_ITEST=1 uv run --quiet --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=registration|discover|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),registration discover),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use registration|discover|all"; exit 2
endif
