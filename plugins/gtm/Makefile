# Live tests of the gtm plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets GTM_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: command (/gtm:run --scan-codebase). The tier orchestrator went with
# STORY-146, because the waves are text of /gtm:run and the orchestrator agent has no resume fields.
PYTEST := GTM_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=command|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),command),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use command|all"; exit 2
endif
