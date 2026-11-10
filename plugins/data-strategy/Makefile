# Live tests of the data-strategy plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets DATA_STRATEGY_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: products (the products skill: the object form and the list form of
# products.json), fullroute (the data-strategy skill with an object products.json), scorer (the scorer script
# on the command line, with no model).
PYTEST := DATA_STRATEGY_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=products|fullroute|scorer|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),products fullroute scorer),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use products|fullroute|scorer|all"; exit 2
endif
