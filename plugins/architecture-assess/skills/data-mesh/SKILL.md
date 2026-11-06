---
description: Use for a standalone Data Pipeline, Data Mesh, and Predictive Intelligence deep-dive. Applies Zhamak Dehghani (four data mesh principles, analytical data product) and Joe Reis + Matt Housley (data engineering lifecycle, feature stores, ground truth engineering) to assess your data architecture and its readiness for ML.
---

# /architecture-assess:data-mesh

Standalone deep-dive into your data pipeline, data mesh, and predictive intelligence architecture.

## When to Use

- "Review our data pipeline architecture"
- "Are we ready for data mesh?"
- "How do we close the production → training data feedback loop?"
- "Is our feature store architecture correct?"
- "What's our path to ML-ready data infrastructure?"

## Steps

1. Scan the codebase for data pipeline signals (Airflow/dbt/Dagster, pipeline directories, feature store configs).
2. Ask with `AskUserQuestion` for your current data volume and your ML goals. Skip a question that the text after the command already answers.
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py new`. The command prints the temp folder `.architect-tmp/<id>/`. Keep the path as `output_dir`, and `<id>` as `session_id`.
4. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:data-mesh-assessor`. The prompt gives these fields: `session_id`, `output_dir`, and `business_context` (the answers of step 2).
5. Read the last line of the agent reply.
   - `DONE: data-mesh`: read `<output_dir>/data-mesh.md` and show the assessment (domain ADR section with lifecycle maturity, data mesh principles assessment, ground truth engineering status). Show the `constitution_check` value of the YAML header. When it is `indeterminate`, say that the assessor could not decide it from the code, and show its reason.
   - Any other ending: show the last lines of the reply and say that the run failed. Keep the temp folder, and stop.
6. Clean up: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py remove <session_id>`.

> **For a complete architecture assessment (all domains):** Use `/architecture-assess:assess`
>
> **To assess Data Mesh as part of a full design:** Use `/architecture-assess:design`
