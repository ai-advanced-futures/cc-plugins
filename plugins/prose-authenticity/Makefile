# Live tests of the prose-authenticity plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets PROSE_AUTHENTICITY_ITEST=1, the gate that tests/integration/conftest.py requires.
# The tier hf downloads torch, transformers and the Hugging Face models. The tiers check, humanize and grants start paid claude -p sessions.
SHELL := /bin/bash

TIER ?=

# A tier is hf (the live Hugging Face detectors, with torch), check (1 live /prose-authenticity:check
# session, about 0.11 USD), humanize (1 live /prose-authenticity:humanize session with the fact check,
# about 0.71 USD), grants (3 default-mode sessions with the calls of the lib files in the prompt, and the real
# flows of check and humanize in acceptEdits mode, 5 to 9 sessions, about 3 USD), or all.
PYTEST_HF := PROSE_AUTHENTICITY_ITEST=1 uv run --no-project --with torch==2.15.0 --with transformers==5.22.2 --with pyyaml --with pytest python -m pytest tests/integration/test_hf_detectors_live.py -m integration -rs
PYTEST_PORT := PROSE_AUTHENTICITY_ITEST=1 uv run --no-project --with pyyaml --with pytest python -m pytest tests/integration/test_live_port.py -m integration -rs
PYTEST_GRANTS := PROSE_AUTHENTICITY_ITEST=1 uv run --no-project --with pyyaml --with pytest python -m pytest tests/integration/test_live_grants.py -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=hf|check|humanize|grants|all"; exit 2; }
ifeq ($(TIER),hf)
	$(PYTEST_HF)
else ifneq ($(filter $(TIER),check humanize),)
	$(PYTEST_PORT) -k "test_$(TIER)_"
else ifeq ($(TIER),grants)
	$(PYTEST_GRANTS) -k "test_grants_"
else ifeq ($(TIER),all)
	$(PYTEST_HF)
	$(PYTEST_PORT)
	$(PYTEST_GRANTS)
else
	@echo "unknown TIER '$(TIER)': use hf|check|humanize|grants|all"; exit 2
endif
