---
description: Use for a standalone Platform and Infrastructure deep-dive. Applies the Serverless-First Ladder, Existing Footprint Rule, and Platform Decision Framework to assess your infrastructure choices against business stage, scale requirements, and economic constraints. Evaluates IaaS/PaaS/SaaS selection for Vercel/Render (pre-PMF), AWS/GCP/Azure (growth+), and multi-cloud scenarios.
---

# /architecture-assess:infrastructure

Standalone deep-dive into your platform and infrastructure architecture.

## When to Use

- "Review our infrastructure choices"
- "Should we use Vercel or AWS for this?"
- "Are we on the right cloud provider?"
- "Is our infrastructure too expensive for our stage?"
- "How do we make our infrastructure ML-ready?"
- "Should we move to Kubernetes?"

## Steps

1. Scan the codebase for infrastructure artifacts (Dockerfiles, k8s manifests, IaC configs, cloud provider configs).
2. Ask with `AskUserQuestion` for business stage and your existing cloud footprint. Skip a question that the text after the command already answers.
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py new`. The command prints the temp folder `.architect-tmp/<id>/`. Keep the path as `output_dir`, and `<id>` as `session_id`.
4. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:infrastructure-assessor`. The prompt gives these fields: `session_id`, `output_dir`, and `business_context` (the answers of step 2).
5. Read the last line of the agent reply.
   - `DONE: infrastructure`: read `<output_dir>/infrastructure.md` and show the assessment (domain ADR section with Serverless-First Ladder assessment, provider recommendations, Well-Architected pillar findings). Show the `constitution_check` value of the YAML header. When it is `indeterminate`, say that the assessor could not decide it from the code, and show its reason.
   - Any other ending: show the last lines of the reply and say that the run failed. Keep the temp folder, and stop.
6. Clean up: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py remove <session_id>`.

> **For a complete architecture assessment (all domains):** Use `/architecture-assess:assess`
>
> **To assess Infrastructure as part of a full design:** Use `/architecture-assess:design`
