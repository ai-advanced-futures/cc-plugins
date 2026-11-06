---
description: Use for a standalone agentic plugin architecture deep-dive. Assesses whether a project is architected as a genuinely differentiated AI plugin using the Agentic Plugin Principles. Evaluates real data integration, compounding value, artifact delivery, context isolation, quantification, cross-system access, entity intelligence, and outcome learning. Runs one domain assessor, with no full orchestration.
---

# /architecture-assess:agentic-plugin

Standalone deep-dive into your agentic plugin architecture. No full orchestration — just the plugin domain.

## When to Use

- "Is this plugin genuinely differentiated, or just a fancy prompt?"
- "Does our plugin architecture compound value across sessions?"
- "Are we delivering actual artifacts or just describing them?"
- "Does our plugin isolate context or degrade the caller's session?"
- "Are we crossing system boundaries or staying repo-confined?"

## Steps

1. Scan the codebase for plugin signals (plugin.json, .claude-plugin/, agents/, skills/, hooks.json, hooks-handlers/).
2. Ask with `AskUserQuestion` for your target platform(s) and your specific plugin goals. Skip a question that the text after the command already answers.
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py new`. The command prints the temp folder `.architect-tmp/<id>/`. Keep the path as `output_dir`, and `<id>` as `session_id`.
4. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:agentic-plugin-assessor`. The prompt gives these fields: `session_id`, `output_dir`, and `business_context` (the answers of step 2).
5. Read the last line of the agent reply.
   - `DONE: agentic-plugin`: read `<output_dir>/agentic-plugin.md` and show the assessment (domain ADR section with findings, recommendations, and Constitution Check). Show the `constitution_check` value of the YAML header. When it is `indeterminate`, say that the assessor could not decide it from the code, and show its reason.
   - Any other ending: show the last lines of the reply and say that the run failed. Keep the temp folder, and stop.
6. Clean up: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py remove <session_id>`.

> **For a complete architecture assessment (all domains):** Use `/architecture-assess:assess`
>
> **To assess plugin architecture as part of a full design:** Use `/architecture-assess:design`
