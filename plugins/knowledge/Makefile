# Live tests of the knowledge plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets KNOWLEDGE_ITEST=1, the money gate that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: setup (live /knowledge:setup sessions),
# move (the move command in a terminal), checkout (the graph of this checkout),
# slug (the new command, as a user types it), learn (live /knowledge:learn sessions),
# link (the link command, as a user types it), body (the body command, as a user types it),
# hook (the hook after a command that a user types), hooklive (1 live session with the hook).
PYTEST := KNOWLEDGE_ITEST=1 python3 -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=setup|move|checkout|slug|learn|link|body|hook|hooklive|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),setup move checkout slug learn link body hook hooklive),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use setup|move|checkout|slug|learn|link|body|hook|hooklive|all"; exit 2
endif
