# Live tests of the aiml plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets AIML_ITEST=1, the money gate that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: registration (1 session, the skills and agents it lists),
# readout (a live /aiml:cost-amplifier-readout run), decide (a live /aiml:decide run, Opus agent),
# design and simulate (a live run of the skill: the small agents, then the main agent, all Opus).
PYTEST := AIML_ITEST=1 uv run --quiet --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=registration|readout|decide|design|simulate|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),registration readout decide design simulate),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use registration|readout|decide|design|simulate|all"; exit 2
endif
