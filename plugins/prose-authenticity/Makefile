# Live tests of the prose-authenticity plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets PROSE_AUTHENTICITY_ITEST=1, the gate that tests/integration/conftest.py requires.
# The tier hf downloads torch, transformers and the Hugging Face models. The tiers check and humanize start paid claude -p sessions.
SHELL := /bin/bash

TIER ?=

# A tier is hf (the live Hugging Face detectors, with torch), check (1 live /prose-authenticity:check
# session, about 0.11 USD), humanize (1 live /prose-authenticity:humanize session with the fact check,
# about 0.71 USD), or all.
PYTEST_HF := PROSE_AUTHENTICITY_ITEST=1 uv run --no-project --with torch --with transformers --with pyyaml --with pytest python -m pytest tests/integration/test_hf_detectors_live.py -m integration -rs
PYTEST_PORT := PROSE_AUTHENTICITY_ITEST=1 uv run --no-project --with pyyaml --with pytest python -m pytest tests/integration/test_live_port.py -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=hf|check|humanize|all"; exit 2; }
ifeq ($(TIER),hf)
	$(PYTEST_HF)
else ifneq ($(filter $(TIER),check humanize),)
	$(PYTEST_PORT) -k "test_$(TIER)_"
else ifeq ($(TIER),all)
	$(PYTEST_HF)
	$(PYTEST_PORT)
else
	@echo "unknown TIER '$(TIER)': use hf|check|humanize|all"; exit 2
endif
