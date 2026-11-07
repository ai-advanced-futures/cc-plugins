# Live tests of the competitive-intelligence plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets COMPETITIVE_INTELLIGENCE_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=
TIERS := registration discover pluginrun analyzerun analyze

# A tier is the first part of a test name: registration (1 session, the skills and agents it lists),
# discover (1 live /competitive-intelligence:discover quick scan, cap 0.9 USD),
# pluginrun (1 live plugin run of discover, cap 0.9 USD),
# analyzerun (1 live plugin run of analyze, cap 1.5 USD),
# analyze (1 live person's run of analyze after an ingested discover run, cap 1.5 USD).
# TIER=all is at most 5.05 USD at list price (the caps of the 5 sessions).
PYTEST := COMPETITIVE_INTELLIGENCE_ITEST=1 uv run --quiet --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rsxX -p no:cacheprovider

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=registration|discover|pluginrun|analyzerun|analyze|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),$(TIERS)),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use registration|discover|pluginrun|analyzerun|analyze|all"; exit 2
endif
