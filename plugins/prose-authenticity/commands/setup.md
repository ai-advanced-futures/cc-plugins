---
description: Configure detector tiers — record commercial-API consent, verify keys, check HF model availability, review thresholds
---

Configure the prose-authenticity plugin for this project. Do the steps in order.

1. Ask with `AskUserQuestion` which tiers to turn on: `heuristics` (always on),
   `hf`, `api`.
2. For `api`: say that the document text goes to 3 outside detector services
   (GPTZero, Originality.ai, Sapling). On consent, write `api_consent: true` into
   `.prose-authenticity/config.yaml`. Tell the person to export
   `GPTZERO_API_KEY`, `ORIGINALITY_API_KEY` and `SAPLING_API_KEY`. Keys stay in
   the environment, because a key in a file can reach a commit.
3. For `hf`: say that the first run downloads `torch`, `transformers` and 3
   models. On consent, run
   `uv run --with torch --with transformers ${CLAUDE_PLUGIN_ROOT}/lib/hf_detectors.py`.
   `True` means that the hf tier is ready.
4. Show the configured state.
