# Live tests of the sofa plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets SOFA_ITEST=1, the money gate that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: rule2 (a live session that runs station Rule 2),
# readiness (readiness.py on fixture repositories, no paid session),
# start (live /sofa:start sessions with a claude stub),
# slack (sofa-slack with the fake Slack API, no paid session),
# slacklive (live /sofa:setup sessions, step 5, with the fake Slack API),
# skillslive (live /sofa:setup sessions, step 2.5, the factory skills; needs the network),
# hitllive (live hitl sessions that post a card with sofa-slack post, with the fake Slack API).
PYTEST := SOFA_ITEST=1 python3 -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=rule2|readiness|start|slack|slacklive|skillslive|hitllive|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),rule2 readiness start slack slacklive skillslive hitllive),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use rule2|readiness|start|slack|slacklive|skillslive|hitllive|all"; exit 2
endif
