# Live tests of the product-finance plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets PRODUCT_FINANCE_ITEST=1, the live-tier opt-in that tests/integration/conftest.py requires.
SHELL := /bin/bash

TIER ?=

# A tier is the first part of a test name: runner (a caller starts unit-economics-runner with a plugin-run block),
# discover (/product-finance:discover with a jtbd graph), setup (/product-finance:setup with the jtbd option),
# person (3 person runs of /product-finance:discover), partial (discover-runner with no SAM and no market share),
# aieconomics (/product-finance:ai-economics: a person run and a runner run whose figures come from the script)
# and rule40 (the Rule of 40 skill: the target 40, 50 or 60, the split, the not-graded case and the sourced lines).
# -p no:cacheprovider: the text scans of tests/unit read each file of the plugin, and a .pytest_cache makes them fail.
PYTEST := PRODUCT_FINANCE_ITEST=1 uv run --quiet --no-project --with-requirements requirements-dev.txt python -m pytest tests/integration -m integration -rs -p no:cacheprovider

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=runner|discover|setup|person|partial|aieconomics|rule40|all"; exit 2; }
ifeq ($(TIER),all)
	$(PYTEST)
else ifneq ($(filter $(TIER),runner discover setup person partial aieconomics rule40),)
	$(PYTEST) -k "test_$(TIER)_"
else
	@echo "unknown TIER '$(TIER)': use runner|discover|setup|person|partial|aieconomics|rule40|all"; exit 2
endif
