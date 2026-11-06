---
name: scaffold
description: Use after /aiml:simulate (or after /aiml:plan, if you skip the simulation), to generate runnable starter code into your project from docs/aiml/spec.md and docs/aiml/plan.md. Writes a src/ tree and requirements.txt. Asks the person nothing.
---

# /aiml:scaffold

Generates the code skeleton for your approach. Needs `docs/aiml/spec.md` and `docs/aiml/plan.md`.

## Steps

1. Check that `docs/aiml/spec.md` and `docs/aiml/plan.md` exist. If one is missing, tell the person to run `/aiml:design` or `/aiml:plan` first, and stop.
2. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:scaffold-agent`.
3. Read the last line of the agent reply.
   - `DONE: scaffold-agent`: list the files that the agent wrote, and show the next step (`/aiml:tune` during training).
   - Any other last line: show the reply to the person, and stop.

## Result

A code structure for your approach:

- **LLM:** HuggingFace Transformers and PyTorch. A Trainer or TRL SFTTrainer setup, a PEFT/LoRA config, a datasets loader.
- **ML:** scikit-learn. A pipeline, a data loader, an evaluation harness.
- **Hybrid:** both structures with a shared evaluation layer.
- `requirements.txt` with version ranges that pin the major version.
- `src/utils/metric_calculator.py` and `src/utils/data_validator.py`: copies of two plugin scripts.

The agent also reads `docs/aiml/simulation-report.md` when it exists, and fixes the critical and important findings in the code.

## Optional tool

When a context7 server is connected, the agent reads the current API of each library before it writes code. Without it, the agent writes the code from the spec and the plan. The README of the plugin shows how to add context7.
