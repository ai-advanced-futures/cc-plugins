---
description: Use to evaluate the agentic SDLC maturity of your organization. Maps your codebase to the 21-step agentic SDLC lifecycle (Phase 0–5 + Step 15), classifies the maturity tier (0–4), recommends a toolchain (MCP servers and marketplace plugins found with WebSearch), and runs an adversarial challenger against the findings. It also runs inside /architecture-assess:assess and /architecture-assess:design.
---

# /architecture-assess:sdlc

Evaluate your organization's software development lifecycle through an agentic lens.
Maps your current practices to a 21-step lifecycle, classifies maturity, and delivers
a concrete roadmap for adopting agentic workflows.

## When to Use

- "What phases of the agentic SDLC are we currently doing?"
- "How mature is our agentic SDLC?"
- "What plugins or tools should we adopt for our development workflow?"
- "Assess our SDLC and recommend next steps"

The orchestrator of `/architecture-assess:assess` and `/architecture-assess:design` also runs the SDLC assessor and the challenger.

## What You Get

1. **21-Step Lifecycle Map** — which of the 21 steps you're doing, how automated, and what's missing
2. **Maturity Tier Classification** — Tier 0–4 with file-based evidence
3. **Toolchain Recommendations** — MCP servers and marketplace plugins matched to your gaps
4. **Role Evolution Map** — how each role evolves in an agentic SDLC
5. **Pilot Recommendation** — the best starting point for your next agentic capability
6. **Adversarial Challenge Report** — a challenger agent's pushback on the assessor's findings

## Output Files

- `docs/sdlc/sdlc-spec.md` — the primary assessment output
- `docs/sdlc/sdlc-challenge-report.md` — challenger findings (when an ADR is available)
- `docs/sdlc/challenge-flags.json` — machine-readable challenge flags

## Steps

1. Ask with `AskUserQuestion`: "How long does architecture approval take? Who can approve?" The person can skip this question. Skip it also when the text after the command answers it. Keep the answer as `approval_answer`. When the person skips it, send no `approval_answer`.
2. Find the ADR to challenge: the path in the text after the command, else the newest ADR of the assessment in `docs/architecture-assess/` or `docs/adr/`. Keep it as `adr_path`, or none.
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py new`. The path has the form `.architect-tmp/<id>`. Keep `<id>` as `session_id`.
4. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:sdlc-assessor`. The prompt gives these fields: `session_id`, `adr_path` (when you have one), `approval_answer` (when the person gave one), and `business_context` (when the person gave one). Wait for the line `DONE: sdlc-assessor`.
5. When `adr_path` exists, dispatch `subagent_type: architecture-assess:sdlc-challenger` with `sdlc_spec_path: docs/sdlc/sdlc-spec.md`, `adr_path` and `session_id`. Wait for the line `DONE: sdlc-challenger`. When there is no `adr_path`, skip the challenger and say "No ADR available — challenger skipped".
6. When an agent ends with no `DONE:` line, show the last lines of its reply and say that the run failed.
7. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py remove <session_id>`. Show the paths of the files in `docs/sdlc/`.
