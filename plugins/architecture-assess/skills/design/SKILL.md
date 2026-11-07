---
description: Use to design a software architecture from scratch. Asks the business questions first (GTM stage, financial goals, innovation goals, product strategy, team, cloud), shows the domain plan for your confirmation, runs the specialist assessors, and offers to save the verdict as an ADR and the components in the system-design graph.
---

# /architecture-assess:design

Design a software architecture from scratch. Business strategy always comes before technical decisions.

## When to Use

- "We're building something new — how should we architect it?"
- "We're starting a startup / new product / new platform"
- "We need to redesign from the ground up"
- "What's the right architecture for our stage and goals?"

## Steps

1. Business Foundation: ask the 6 business questions with `AskUserQuestion`, in this order. Make no technical decision before the person has answered. Skip a question that the text after the command already answers.
   - GTM stage: "What is the current GTM stage? (A) Pre-PMF — proving the hypothesis (B) Early Growth — scaling what works (C) Scale — multi-market, enterprise customers (D) Expansion — new revenue streams"
   - Financial goals: "What are the financial constraints and goals? (runway months, target ARR, SaaS gross margin target, cost per customer ceiling)"
   - Innovation goals: "What is the innovation and differentiation strategy? What IP or tech moat are you building? New AI-driven revenue streams planned?"
   - Product strategy: "What is the core JTBD being solved? Who are the user personas? What does winning look like competitively?"
   - Team and constraints: "How large is the engineering team? What are the primary skills? Any existing tech stack constraints?"
   - Cloud and infrastructure: "Any cloud provider preference or existing footprint? Any regulatory/compliance requirements?"
2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py clean --older-than 60`. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py new`. The command prints the temp folder `.architect-tmp/<id>/`. Keep the path as `output_dir`, and `<id>` as `session_id`.
3. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:orchestrator`. The prompt gives these fields: `mode: design`, `phase: plan`, `session_id`, `output_dir`, `codebase_root` (the full path of the project folder), `business_context` (the full answers of step 1), and `web_search_directive`. The directive says that agents verify AI/ML, CI/CD, data-pipeline, observability and infrastructure recommendations against current practice with web search before they finish.
4. Read the last line of the agent reply.
   - `NEEDS-INPUT: orchestrator`: read `<output_dir>/session.json`. Show `domains_detected` as the plan. Ask "Proceed?". When the person declines, ask which domains to add or remove, and show the new plan. Repeat until the person agrees, or stop when the person cancels. Do step 3 again with the same fields, with `phase: run` in place of `phase: plan`, and with `confirmed_domains` (the slugs).
   - `DONE: orchestrator — adr_draft=<path>`: go to step 5.
   - Any other ending: show the last lines of the reply, say that the run failed, keep the temp folder, and stop.
5. Read the draft (`adr_draft`). When `thinktank:debate` is available, run it on the `## Simplicity Gate Verdict` of the draft. If not, argue against the verdict yourself. Show the result with the verdict.

The draft holds the unified architecture spec, the C4 diagrams (L1 to L4), the domain event catalog, the decision, and the evolution roadmap. In mode `design`, the run also writes `<output_dir>/design-pages.json`.

## Save the decision

1. Write the draft to `docs/architecture-assess/<date>-<slug>-assessment.md`. `<slug>` is a short name of the system. When `<output_dir>/executive-summary.md` exists, write it to `docs/architecture-assess/<date>-<slug>-executive-summary.md`. If it does not exist, say that the executive summary was not made. These plain files keep the diagrams, the roadmap, the Component Map and the Implementation Pathway.
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

## Save the design pages

Save pages only through `system_design.py` of the `system-design` plugin.

1. Run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh system-design scripts/system_design.py`. It prints the plugin root `<root>`. When it exits 1, `system-design` is not installed: keep the plain files, name the plugin, and go to "Result".
2. Run `uv run <root>/scripts/system_design.py --root <project root> resolve system`. When it exits 2, say "Run `/system-design:setup` first", keep the plain files, and go to "Result".
3. List the `*.md` files of the `components` folder in the folder of the `system.md` path that step 2 printed, with `find '<folder>/components' -name '*.md'` (write each `'` in the folder path as `'\''`). When a `Component` page exists, write no page. Name `/system-design:learn building-blocks` with the plain file as the next step, and go to "Result".
4. Ask with `AskUserQuestion`: "Save the design in the system-design graph?" On yes, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/design_to_graph.py --system-design <root> --root <project root> <output_dir>/design-pages.json`. When it exits 1, show the failed command and its error, list the pages that exist, and name `/system-design:learn building-blocks` to finish. The plain file keeps the full design.
5. Call the `knowledge:checking` skill with the graph `system-design`. Show each ERROR, WARN and SKIP line.
6. When step 4 of "Save the decision" saved an ADR, name `/system-design:learn building-blocks` as the step that adds the row that links the area to the ADR.

## Result

Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py remove <session_id>`, also when the person declined a save. Show the paths of the plain files, the ADR, and the pages. Then show the next steps:

- When the draft has a `## Recommended prerequisite` section, show its line.
- When a skill of `architecture-visualizer` is in the session, ask "Make the interactive diagram?". On yes, call `/architecture-visualizer:architect-bridge` with the design as context.
- Optional: the Implementation Pathway of the draft names `/aiml:decide`, `/agentic:decide` and `superpowers:writing-plans`. Use them when these plugins are installed.
- When `docs/sdlc/sdlc-spec.md` exists, the run also wrote the SDLC files in `docs/sdlc/`: name each file that exists. If it does not exist, say that the SDLC step did not finish.
