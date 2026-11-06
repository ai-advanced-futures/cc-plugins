---
description: Use for a standalone Monitoring and Observability deep-dive. Applies Charity Majors (structured events, high cardinality, ODD), Cindy Sridharan (three pillars), and Ben Sigelman + Google SRE (OpenTelemetry, SLI/SLO/error budgets, toil elimination) to assess your observability architecture.
---

# /architecture-assess:observability

Standalone deep-dive into your monitoring and observability architecture.

## When to Use

- "Review our observability stack"
- "Are we doing structured logging correctly?"
- "How do we implement SLOs?"
- "Is our distributed tracing set up right?"
- "What's our error budget and how do we track it?"

## Steps

1. Scan the codebase for observability infrastructure (OTel imports, logging configs, monitoring configs).
2. Ask with `AskUserQuestion` for your current observability pain point. Skip a question that the text after the command already answers.
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py new`. The command prints the temp folder `.architect-tmp/<id>/`. Keep the path as `output_dir`, and `<id>` as `session_id`.
4. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:observability-assessor`. The prompt gives these fields: `session_id`, `output_dir`, and `business_context` (the answers of step 2).
5. Read the last line of the agent reply.
   - `DONE: observability`: read `<output_dir>/observability.md` and show the assessment (domain ADR section with three-pillar assessment, OpenTelemetry compliance, SLO status). Show the `constitution_check` value of the YAML header. When it is `indeterminate`, say that the assessor could not decide it from the code, and show its reason.
   - Any other ending: show the last lines of the reply and say that the run failed. Keep the temp folder, and stop.
6. Clean up: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py remove <session_id>`.

> **For a complete architecture assessment (all domains):** Use `/architecture-assess:assess`
>
> **To assess Observability as part of a full design:** Use `/architecture-assess:design`
