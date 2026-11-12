# Live tests of the ux-hci-design plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets UX_HCI_DESIGN_ITEST=1, the money gate that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: test (a live /ux-hci-design:ux-design test run of the
# ai-saas-product example, 2 turns, about 0.65 USD, caps 1.2 USD), foreground (3 sessions of ux-design in the
# default permission mode: the helper skills run in the foreground, the later prototype session reads the Concept
# from the brain, and the evaluator reads its schema), interactive (1 full ux-design session in a pane of tmux, with
# its own tmux server; set UX_ITEST_TMUX to the name of the socket; STORY-371, adlc rule 13), savelink (the save with
# the link forms, no model) and remove (the remove-questions command with no model, and a live test phase with old
# reviewer files), learn (12 sessions of `/ux-hci-design:learn` with a `gh` stand-in: a broken PRD page, the
# default-mode save with and without the 4 `Skill` rules, and an App login; about 0.18 USD for each session,
# caps 8 USD each). The tier all runs each tier, so it runs the 12 learn sessions too.
PYTEST := UX_HCI_DESIGN_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=test|foreground|interactive|savelink|remove|learn|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),test foreground interactive savelink remove learn),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use test|foreground|interactive|savelink|remove|learn|all"; exit 2
endif
