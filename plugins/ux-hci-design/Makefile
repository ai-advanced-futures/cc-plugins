# Live tests of the ux-hci-design plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets UX_HCI_DESIGN_ITEST=1, the money gate that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: test (a live /ux-hci-design:ux-design test run of the
# ai-saas-product example, 2 turns, about 0.65 USD, caps 1.2 USD), foreground (3 sessions of ux-design in the
# default permission mode: the agents run in the foreground, the later prototype session reads the Concept
# from the brain, and the evaluator reads its schema), savelink (the save with the link forms, no model) and
# remove (the remove-questions command with no model, and a live test phase with old reviewer files).
PYTEST := UX_HCI_DESIGN_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=test|foreground|savelink|remove|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),test foreground savelink remove),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use test|foreground|savelink|remove|all"; exit 2
endif
