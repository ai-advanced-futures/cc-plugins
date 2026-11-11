# Live tests of the competitive-intelligence plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets COMPETITIVE_INTELLIGENCE_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=
TIERS := registration discover pluginrun analyzerun analyze lens

# A tier is the first part of a test name: registration (1 session, the skills and agents it lists),
# discover (1 live /competitive-intelligence:discover quick scan, cap 0.9 USD, then 1 /competitive-intelligence:learn of that run, cap 0.5 USD),
# pluginrun (1 live plugin run of discover, cap 0.9 USD),
# analyzerun (1 live plugin run of analyze, cap 1.5 USD),
# analyze (1 live person's run of analyze after an ingested discover run, in the default mode, cap 1.5 USD).
# lens (STORY-284: 1 to 4 live plugin runs of analyze for the 2nd competitor of an earlier run, cap 1.5 USD each, until 1 run wrote
# technology-disruption.json; then the replay of its files, with no model).
# TIER=all is at most 11.55 USD at list price (the caps of the 5 sessions, and of 4 runs of the lens tier).
PYTEST := COMPETITIVE_INTELLIGENCE_ITEST=1 uv run --quiet --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rsxX -p no:cacheprovider

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=registration|discover|pluginrun|analyzerun|analyze|lens|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),$(TIERS)),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use registration|discover|pluginrun|analyzerun|analyze|lens|all"; exit 2
endif
