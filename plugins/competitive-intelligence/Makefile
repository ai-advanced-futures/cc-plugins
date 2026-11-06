# Live tests of the competitive-intelligence plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets COMPETITIVE_INTELLIGENCE_ITEST=1, the money gate that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: registration (1 session, the skills and agents it lists),
# discover (1 live /competitive-intelligence:discover quick scan, about 0.87 USD, cap 0.9 USD).
# pluginrun (1 live plugin run of discover, cap 0.9 USD).
# TIER=all can cost up to 2.05 USD (the caps of the 3 sessions).
PYTEST := COMPETITIVE_INTELLIGENCE_ITEST=1 uv run --quiet --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=registration|discover|pluginrun|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),registration discover pluginrun),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use registration|discover|pluginrun|all"; exit 2
endif
