---
description: Use at design review of a new agentic feature to find its cost class. Reads the feature's cost-amplifier-readout (default .aiml/cost-amplifier-readout.json), asks the AI-stack layer, and writes a cost-class-classification (deterministic cost-class band plus advisory remediation).
argument-hint: "[readout path]"
---

# /architecture-assess:cost-class-review

Run at design review of a NEW agentic feature. Given the feature's
`cost-amplifier-readout`, this produces a `cost-class-classification`:
the product's 4-layer AI-stack layer, the deterministic cost-class
band, and an advisory remediation.

## When to Use

- "We're adding a new agentic feature — what's its cost class?"
- "Run the cost-class design-review gate on this readout."
- "Every new agentic feature requires a cost-class declaration at design review."

## Steps

1. Find the readout: the path in the text after the command, else `.aiml/cost-amplifier-readout.json`. When the file does not exist, say so, name `/aiml:cost-amplifier-readout` as the command that writes it, and stop.
2. Ask with `AskUserQuestion` for the AI-stack layer. Offer `foundation_model`, `infrastructure_orchestration`, `application`, `vertical_labor_anchor`, and "explain my product". On "explain my product", ask for a short description of the business model and the customer base, and choose the layer from it. When the business model and the customer base point to different layers, choose by the protection that the customer base gives.
3. Ask for the basis of the layer in one line (`ai_stack_layer_basis`), and for the feature ID (`feature_id`). Skip a question that the text after the command already answers.
4. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:cost-class-gate-agent`. The prompt gives these fields: `readout_path`, `ai_stack_layer`, `ai_stack_layer_basis`, and `feature_id`.
5. Read the last line of the agent reply, then `.architecture/cost-class-handoff.json`. Its `status` is `complete`, `blocked` or `error`.
   - `complete`: show the layer, the cost class, `requires_guardrail` and the remediation from `.architecture/cost-class-classification.json`.
   - `blocked` or `error`: show its `reason`.
   - No `DONE:` line: show the last lines of the reply and say that the run failed.

The band comes from `scripts/cost_class_band.py` and `scripts/cost_class_emitter.py`. The layer is the judgment of the person and the agent. The verdict is **advisory**: `requires_guardrail` flags application-layer high and critical features, and it does not block.

## Result

- `.architecture/cost-class-classification.json`: the classification.
- `.architecture/cost-class-handoff.json`: the status of the run.
