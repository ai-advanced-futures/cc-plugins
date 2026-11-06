---
description: Use for a standalone AI/ML and Agentic AI deep-dive. Assesses your AI/ML architecture, model selection, post-training pipeline, agentic AI composition, and Responsible AI posture using Karpathy, Chip Huyen, Andrew Ng, and Lilian Weng frameworks. Runs one domain assessor, with no full orchestration.
---

# /architecture-assess:aiml

Standalone deep-dive into your AI/ML and Agentic AI architecture. No full orchestration — just the AI/ML domain.

## When to Use

- "Review our AI architecture specifically"
- "Is our agentic AI design correct?"
- "Are we using the right models and fine-tuning approach?"
- "Is our post-training pipeline sound?"
- "Are our autonomous features designed correctly?"

## Steps

1. Scan the codebase for AI/ML signals in the codebase (ML imports, model configs, agent definitions).
2. Ask with `AskUserQuestion` for business stage and your specific AI/ML goals. Skip a question that the text after the command already answers.
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py new`. The command prints the temp folder `.architect-tmp/<id>/`. Keep the path as `output_dir`, and `<id>` as `session_id`.
4. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:aiml-assessor`. The prompt gives these fields: `session_id`, `output_dir`, and `business_context` (the answers of step 2).
5. Read the last line of the agent reply.
   - `DONE: aiml`: read `<output_dir>/aiml.md` and show the assessment (domain ADR section with findings, recommendations, and Constitution Check). Show the `constitution_check` value of the YAML header. When it is `indeterminate`, say that the assessor could not decide it from the code, and show its reason.
   - Any other ending: show the last lines of the reply and say that the run failed. Keep the temp folder, and stop.
6. Clean up: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py remove <session_id>`.

> **For a complete architecture assessment (all domains):** Use `/architecture-assess:assess`
>
> **To assess AI/ML as part of a full design:** Use `/architecture-assess:design`
