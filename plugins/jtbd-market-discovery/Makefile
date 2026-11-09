# Live tests of the jtbd-market-discovery plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets JTBD_MARKET_DISCOVERY_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name:
# - checkpoint: the Phase 6 checkpoint of /jtbd-market-discovery:discover and 1 resume with continue (2 turns).
# - survey: Phase 6 with a survey file: the scripts run, the scorer reads the result file (1 turn).
# - nosurvey: discover with no survey from Phase 9, then learn (2 turns).
# - wtpcheck: wtp-check with a survey file, then learn, then ask in a new session (2 or 3 turns).
# - quickvalidate: quick-validate, then learn Step 3 (1 or 2 turns).
# Each turn has a --max-budget-usd guard against a runaway turn.
PYTEST := JTBD_MARKET_DISCOVERY_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs -p no:cacheprovider
TIERS := checkpoint survey nosurvey wtpcheck quickvalidate

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=checkpoint|survey|nosurvey|wtpcheck|quickvalidate|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),$(TIERS)),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use checkpoint|survey|nosurvey|wtpcheck|quickvalidate|all"; exit 2
endif
