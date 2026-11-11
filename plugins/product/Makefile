# Live tests of the product plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets PRODUCT_ITEST=1, the money gate that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: bundle (read-only GitHub reads and dry runs),
# skill (live sessions of /product:roadmap-sync, /product:learn, /product:explore and
# /product:specifying-stories, paid), scratch (a real apply on a scratch
# GitHub Project; needs PRODUCT_ITEST_SCRATCH_DIR and PRODUCT_ITEST_SCRATCH_PROJECT),
# experience (STORY-241: the Experience page run as a user runs it, on the ui_product.py fixture;
# no GitHub, no paid session; the live /product:learn session is in the skill tier).
PYTEST := PRODUCT_ITEST=1 python3 -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=bundle|skill|scratch|experience|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifeq ($(TIER),experience)
	$(PYTEST) -k "test_experience_e2e"
else ifneq ($(filter $(TIER),bundle skill scratch),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use bundle|skill|scratch|experience|all"; exit 2
endif
