# Live tests of the prose-authenticity plugin (ADR-0001). Local, on demand. Not run by CI.
# Sets PROSE_AUTHENTICITY_ITEST=1, the gate that tests/integration/conftest.py requires.
# The live tier downloads torch, transformers and the Hugging Face models.
SHELL := /bin/bash

TIER ?=

# A tier is hf (the live Hugging Face detectors) or all.
PYTEST := PROSE_AUTHENTICITY_ITEST=1 uv run --no-project --with torch --with transformers --with pyyaml --with pytest python -m pytest tests/integration -m integration -rs

.PHONY: itest
itest:
	@test -n "$(TIER)" || { echo "TIER is required: make itest TIER=hf|all"; exit 2; }
ifneq ($(filter $(TIER),hf all),)
	$(PYTEST)
else
	@echo "unknown TIER '$(TIER)': use hf|all"; exit 2
endif
