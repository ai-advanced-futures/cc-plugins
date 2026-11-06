---
description: Use to assess an existing software architecture across all domains. Asks the business stage and the top concerns, shows the domain plan for your confirmation, runs the specialist assessors in parallel, and offers to save the verdict as an ADR.
---

# /architecture-assess:assess

Orchestrated, multi-agent assessment of your software architecture. All detected domains run in parallel.

## When to Use

- "Assess our current architecture"
- "What's wrong with our architecture?"
- "Do a full architecture review"
- "Assess us across all domains"

## What Runs

The assessors `software-architecture-assessor` (the 7 layers, the Architecture Principles + Fowler + Uncle Bob + Evans) and `infrastructure-assessor` (Serverless-First Ladder, Well-Architected) always run. The domain assessors `aiml-assessor`, `cicd-assessor`, `data-mesh-assessor`, `observability-assessor`, `testing-assessor` and `agentic-plugin-assessor` run when the orchestrator detects their domain.

## Steps

1. Ask with `AskUserQuestion`: "What is the business stage of this product? (Pre-PMF / Early Growth / Scale / Enterprise)". Then ask: "What are the top 1–2 architectural concerns you want me to focus on?" (optional). Skip a question that the text after the command already answers.
2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py clean --older-than 60`. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py new`. The command prints the temp folder `.architect-tmp/<id>/`. Keep the path as `output_dir`, and `<id>` as `session_id`.
3. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:orchestrator`. The prompt gives these fields: `mode: assess`, `phase: plan`, `session_id`, `output_dir`, `codebase_root` (the full path of the project folder), `business_context` (the answers of step 1), and `web_search_directive`. The directive says that agents verify AI/ML, cloud-native, event-streaming and LLMOps/MLOps recommendations against current practice with web search before they finish.
4. Read the last line of the agent reply.
   - `NEEDS-INPUT: orchestrator`: read `<output_dir>/session.json`. Show `domains_detected` as the plan. Ask "Proceed?". When the person declines, ask which domains to add or remove, and show the new plan. Repeat until the person agrees, or stop when the person cancels. Do step 3 again with the same fields, with `phase: run` in place of `phase: plan`, and with `confirmed_domains` (the slugs).
   - `DONE: orchestrator — adr_draft=<path>`: go to "Save".
   - Any other ending: show the last lines of the reply, say that the run failed, keep the temp folder, and stop.

## Save

1. Read the draft (`adr_draft`). Write it to `docs/architecture-assess/<date>-<slug>-assessment.md`. `<slug>` is a short name of the system. When `<output_dir>/executive-summary.md` exists, write it to `docs/architecture-assess/<date>-<slug>-executive-summary.md`. If it does not exist, say that the executive summary was not made. These plain files keep the diagrams, the roadmap, the Component Map and the Implementation Pathway.
2. Show the verdict (`## Decision Outcome`) and the Simplicity Gate verdict. Read the YAML header of each `<output_dir>/<slug>.md` that `session.json` lists. Show each domain with `constitution_check: fail` as a constitution failure. Show each domain with `constitution_check: indeterminate` and its reason. The draft leaves an indeterminate domain out; name `/architecture-assess:<slug>` as the way to include it.
3. Ask with `AskUserQuestion`: "Save this decision as an ADR?"
4. On yes, call the `architecture:learn` skill with the `Skill` tool. The argument is one decision sentence from `## Decision Outcome`. In the same message, give these facts:
   - Context: `## Context` and `## Decision Drivers`.
   - Decision: the verdict.
   - Why: `## Domain Assessment Summary`.
   - Alternatives considered: `### Cross-Domain Trade-offs`.
   - Consequences: `### Consequences` and `## Simplicity Gate Verdict`.
   - Parent spec: the plain file of step 1.

   The first fact that names a principle names the source of the set 1 time: "Architecture Principle #3 (the principle set of architecture-assess, `docs/frameworks.md`)".
5. When `architecture:learn` stops with no ADR, show its line, keep the plain file, say that the ADR is not saved, and name `/architecture:setup`. Else show each ERROR, WARN and SKIP line of the checks that it reports.
6. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py remove <session_id>`, also on no.

## Result

Show the paths of the plain files and the ADR, then the next steps:

- When the draft has a `## Recommended prerequisite` section, show its line.
- When a skill of `architecture-visualizer` is in the session, ask "Make the interactive diagram?". On yes, call `/architecture-visualizer:architect-bridge` with the assessment as context.
- Optional: the Implementation Pathway of the draft names `/aiml:decide`, `/agentic:decide` and `superpowers:writing-plans`. Use them when these plugins are installed.
- When `docs/sdlc/sdlc-spec.md` exists, the run also wrote the SDLC files in `docs/sdlc/`: name each file that exists. If it does not exist, say that the SDLC step did not finish.

> **For a single domain:** `/architecture-assess:aiml`, `:cicd`, `:data-mesh`, `:observability`, `:testing`, `:infrastructure` or `:agentic-plugin`
>
> **For a single decision:** `/architecture-assess:review`
