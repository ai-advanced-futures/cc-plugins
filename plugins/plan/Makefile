# Real-tool tests are local and optional (ADR-0001). This target installs no bd or Dolt.
SHELL := /bin/bash
TIER ?=
PYTEST := uv run --no-project --python '>=3.11' --with-requirements requirements-dev.txt python -m pytest

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=native|all"; exit 2; }
ifeq ($(TIER),native)
	$(PYTEST) tests/integration -m unbilled -rs
else ifeq ($(TIER),all)
	PLAN_ITEST=1 $(PYTEST) tests/integration -m integration -rs
else
	@echo "unknown TIER '$(TIER)': use native|all"; exit 2
endif
