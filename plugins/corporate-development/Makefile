# Live tests of the corporate-development plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets CORPORATE_DEVELOPMENT_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: pipeline (4 live turns of /corporate-development:pipeline,
# list price about 2.3 USD, --max-budget-usd caps 3.5 USD),
# module (python -m corporate_development in an empty folder, no paid session).
PYTEST := CORPORATE_DEVELOPMENT_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=pipeline|module|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),pipeline module),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use pipeline|module|all"; exit 2
endif
