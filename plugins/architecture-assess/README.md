# architecture-assess

Assess an existing architecture. Design a new one. Review one decision. Check the delivery readiness of an organization for agentic work. This is version v1.0.3.

The plugin puts **business strategy before technical decisions**. It covers all layers from UI to AIOps. It applies one method: the Architecture Principles, together with Fowler, Uncle Bob, Evans DDD, and the Cloud Well-Architected frameworks.

This plugin is not the `architecture` plugin of this marketplace. The `architecture` plugin stores decisions. This plugin makes the decisions, and then saves each one through `architecture`.

## Overview

The plugin has two parts.

- **Software architecture.** Assess an existing codebase with up to 8 specialist assessors. Design a new architecture from the business questions. Review one decision. Each run gives a unified ADR draft and a one-page executive summary.
- **Agentic SDLC assessment.** Map an engineering organization to the 21-step agentic SDLC. Classify its maturity on a Tier 0–4 scale. Score its use of 15 harness primitives. Give a plan to improve.

The plugin also classifies the cost of a new agentic feature (`cost-class-review`).

## Install

```bash
claude plugin install architecture-assess@cc-plugins
```

## Needs

| Need | Why |
|---|---|
| `architecture` plugin | Saves each decision as an ADR (`architecture:learn`). |
| `system-design` plugin | Saves design pages (`system_design.py`). |
| `uv` | Runs the scripts of the plugin. The first run downloads `jsonschema`. |

The first two are in `dependencies` of the plugin. Claude Code enables them with this plugin.

Optional plugins. Each run works without them.

| Plugin | Use |
|---|---|
| `thinktank` | `review` and `design` run `thinktank:debate` on the Simplicity Gate verdict. |
| `business-domain` | Holds the bounded contexts. The draft asks for them when no graph exists. |
| `aiml` | Writes the cost-amplifier readout that `cost-class-review` reads. It is also the next step for an AI/ML design (`/aiml:decide`, `/aiml:design`, `/aiml:plan`). |
| `architecture-visualizer` | Makes an interactive diagram of the result. |
| `agentic` | Next step for an agentic design. |
| `value-ip` | Checks IP and differentiation claims in the executive summary. |
| `superpowers` | `superpowers:writing-plans` writes the plan for the Implementation Pathway. |

## Setup in your project

To save the result, the project needs two graphs.

1. Run `/architecture:setup`. This makes the ADR folder that `architecture:learn` writes to.
2. Run `/system-design:setup`. This makes the system-design graph that `design` writes to.

Without them, the plugin still works. It keeps the plain files, and tells you what to run.

## Configuration

The plugin has no settings file. It asks questions when it runs (see "Commands"). It reads these things from your project:

- The codebase, with `Read`, `Glob`, and `Grep`.
- The cost-amplifier readout, for `cost-class-review` (default `.aiml/cost-amplifier-readout.json`).
- `.claude/knowledge.json`, to see if a `ddd` graph exists.

## Quickstart

Assess an architecture:

```
/architecture-assess:assess
```

Design a new architecture from scratch:

```
/architecture-assess:design
```

Review one decision:

```
/architecture-assess:review Should we use one Postgres database or one database for each service?
```

Assess agentic SDLC maturity:

```
/architecture-assess:sdlc
```

A question that you write after the command is not asked again.

## Commands

There are 12 commands. Each command is a skill. The name of the command is the name of the skill folder.

| Command | What it does | What it asks |
|---|---|---|
| `/architecture-assess:assess` | Full assessment. All detected domains run in parallel. Gives an ADR draft and an executive summary. | Business stage. Top concerns. Then: "Proceed?" with the domain plan. |
| `/architecture-assess:design` | Designs a new architecture. Business foundation first. Gives C4 diagrams, a roadmap, an ADR draft, and design pages. | The 6 business questions (GTM stage, financial goals, innovation goals, product strategy, team and constraints, cloud and infrastructure). Then: "Proceed?". |
| `/architecture-assess:review` | Reviews one decision. Applies the Simplicity Gate. | The decision. The current approach. The alternatives. Business stage and constraints. |
| `/architecture-assess:aiml` | AI/ML and agentic AI deep-dive. | Business stage and AI/ML goals. |
| `/architecture-assess:cicd` | CI/CD and delivery deep-dive. | Your key delivery pain point. |
| `/architecture-assess:data-mesh` | Data pipeline, data mesh, and predictive intelligence deep-dive. | Your data volume and ML goals. |
| `/architecture-assess:observability` | Monitoring and observability deep-dive. | Your observability pain point. |
| `/architecture-assess:testing` | Testing at design time and run time. | Your biggest testing pain point. Your language and framework. |
| `/architecture-assess:infrastructure` | Platform and infrastructure deep-dive. | Business stage and your cloud footprint. |
| `/architecture-assess:agentic-plugin` | Agent and plugin design deep-dive. | Your target platforms and plugin goals. |
| `/architecture-assess:sdlc` | Agentic SDLC lifecycle assessment. | "How long does architecture approval take?" You can skip it. |
| `/architecture-assess:cost-class-review` | Finds the cost class of a new agentic feature. Gives an advisory `requires_guardrail` verdict. | The AI-stack layer (or "explain my product"). The basis of the layer. The feature ID. |

Only a skill asks you questions. An agent never asks. When an agent cannot decide a value, it sets `indeterminate`, and the skill shows that value to you.

## Software Architecture

### Assess

The skill makes a temp folder, and dispatches the orchestrator two times.

1. **Plan.** The orchestrator scans the codebase. It writes the domain plan into `session.json`. It ends with `NEEDS-INPUT: orchestrator`.
2. **Confirm.** The skill shows the plan. You say "Proceed?", or you add or remove domains.
3. **Run.** The orchestrator dispatches the confirmed assessors in one message, so they run in parallel. Then it runs the completion sweep (`wave-orchestrator`), the `synthesizer`, the `executive-summary-agent` and `sdlc-assessor`, and last `sdlc-challenger`. It ends with `DONE: orchestrator — adr_draft=<path>`.
4. **Save.** See "Save".

The assessors:

- **Software architecture** (always) — 7-layer evaluation against the Architecture Principles, Fowler, Uncle Bob, Evans, and Cloud Well-Architected.
- **Infrastructure** (always) — platform, cloud, deployment, IaC.
- **AI/ML** (when detected) — model architecture, embedding pipelines, AIOps.
- **CI/CD** (when detected) — pipeline design, delivery risk, artifact hygiene.
- **Data mesh** (when detected) — data pipelines, mesh topology, predictive intelligence.
- **Observability** (when detected) — OTel, logging, alerting, SLO coverage.
- **Testing** (when detected) — test architecture, coverage strategy, runtime quality.
- **Agentic plugins** (when detected) — plugin design, marketplace maturity, harness adoption.

### Design

`design` runs the same way as `assess`. It asks the business questions first:

1. Strategy — what business problem does this solve, and for whom.
2. Stage — where the organization sits (explore, validate, scale, optimize).
3. Constraints — Cost ∝ Speed × Accuracy at the customer's willingness to pay at this stage.
4. Technical decisions — driven by strategy, not trend.

It gives C4 diagrams (Mermaid), an ADR draft, and an evolution roadmap with next-stage triggers. In design mode the synthesizer also writes `design-pages.json` (components and their links) for the system-design graph.

### Review

`review` reviews one decision. It challenges assumptions, shows trade-offs, and applies the Simplicity Gate. It shows a short ADR in the conversation. It writes no plain file.

## Save

After the run, the skill:

1. Writes the full draft to `docs/architecture-assess/<date>-<slug>-assessment.md`. Writes the summary to `docs/architecture-assess/<date>-<slug>-executive-summary.md`. These plain files keep the diagrams, the roadmap, and the Implementation Pathway.
2. Shows the verdict, each constitution failure, and each `indeterminate` value.
3. Asks: "Save this decision as an ADR?" On yes, it calls `architecture:learn` with one decision sentence and the facts for the 5 sections (Context, Decision, Why, Alternatives considered, Consequences). The plain file is the parent spec.
4. For `design` only: finds the `system-design` plugin with `probe-plugin.sh`, and asks "Save the design in the system-design graph?" On yes, `design_to_graph.py` runs `system_design.py` to make one `Component` page for each component and one `uses` link for each relation. It then runs `knowledge:checking` on the graph `system-design`.
5. Removes the temp folder.

If the project has no ADR folder, the skill keeps the plain files and names `/architecture:setup`. If the project has no system-design graph, the skill names `/system-design:setup`. If the graph already has a `Component` page, the skill writes no page. It names `/system-design:learn building-blocks` instead, so two runs do not make two pages for one component. The plugin writes no ADR file and no page file by itself.

The first principle name in an ADR names the source of the set one time: "Architecture Principle #3 (the principle set of architecture-assess, `docs/frameworks.md`)". This tells the reader that the principle is not a rule of the `architecture` plugin.

## Files the plugin writes

In the project of the user:

| File | Written by |
|---|---|
| `.architect-tmp/<id>/` (`session.json`, `<slug>.md`, `<slug>.done`, `wave-timeout.json`, `unified-adr.md`, `executive-summary.md`, `design-pages.json`) | The agents. `session.py` makes it and deletes it. Do not commit it. |
| `docs/architecture-assess/<date>-<slug>-assessment.md` and `…-executive-summary.md` | `assess`, `design` |
| The ADR | `architecture:learn` |
| The design pages | `system_design.py` |
| `docs/sdlc/sdlc-spec.md`, `docs/sdlc/sdlc-challenge-report.md`, `docs/sdlc/challenge-flags.json` | `sdlc`, `assess`, `design` |
| `.architecture/cost-class-classification.json` and `.architecture/cost-class-handoff.json` | `cost-class-review` |

## Agentic SDLC Assessment

`/architecture-assess:sdlc` runs two agents in order: `sdlc-assessor`, then `sdlc-challenger`. It does more than score the present state. It gives a plan to improve. The output is a design document as much as an assessment.

### What it assesses

- Maps the codebase to Steps 0.1–4.5 and Step 15 of the 21-step agentic SDLC lifecycle.
- Scores harness adoption across 15 primitives (score out of 15).
- Classifies organization maturity on the Tier 0–4 scale below.
- Challenges its own findings across 7 dimensions (`sdlc-challenger`).

### Maturity tiers

| Tier | Label | Signature |
|---|---|---|
| Tier 0 | Pre-Agentic | No AI in workflow |
| Tier 1 | AI-Assisted | Point tools (Copilot, ChatGPT) — no systematic harness |
| Tier 2 | Agent-Augmented | Agents in 1–3 phases; CLAUDE.md present; architecture review often a bottleneck |
| Tier 3 | Agent-Collaborative | Strong harness (8+/15 primitives); inner-source plugin marketplace; Fix Preview Agent |
| Tier 4 | Agentic-Native | Autonomous across all phases; full harness (12–15/15 primitives); Platform Repo |

### What it produces

**`sdlc-spec.md`** — the main output. It holds:

- Lifecycle mapping (which steps are present, partial, or absent).
- Maturity tier with evidence.
- Harness score out of 15, with a note for each primitive.
- Role evolution design — current role and recommended role (PM, Eng Lead, Architect, QE).
- Platform team design — size and reason.
- Pilot candidate — the project with the best return for the first agentic pilot.
- A DO NOW / DO LATER / DON'T DO YET grid.
- Toolchain recommendations — MCP servers and marketplace plugins found with WebSearch, for each gap.

**`sdlc-challenge-report.md`** and **`challenge-flags.json`** — the adversarial check across 7 dimensions. They flag overconfident claims, tier claims with no support, and harness primitives that were skipped.

## Architecture

_Horizontal Constitution + Vertical Domain Specialists + File-Based Inter-Agent Protocol_

The plugin has 15 agents (14 in the assessment chain, and the standalone `cost-class-gate-agent`). A file-based protocol keeps the context window of each stage small:

```
docs/frameworks.md          = THE CONSTITUTION (assessors and synthesizer read this)
                               ↓
  skill (main conversation)   ← asks you, shows the plan, saves the result
                               ↓ (temp folder .architect-tmp/<id>/)
  orchestrator (thin)         ← coordinates only; never holds domain content
                               ↓ (one message, foreground, parallel)
  software-architecture-assessor  ← horizontal guardian (always runs)
  infrastructure-assessor         ← platform specialist (always runs)
  aiml-assessor                   ┐
  cicd-assessor                   │ domain specialists
  data-mesh-assessor              │ (run when detected)
  observability-assessor          │ each writes <id>/<domain>.md
  testing-assessor                │ and returns DONE: only
  agentic-plugin-assessor         ┘
                               ↓
  wave-orchestrator           ← completion sweep, 1 time, no team
                               ↓
  synthesizer (opus)          ← two passes: headers first, then targeted narratives;
                                  writes unified-adr.md
  executive-summary-agent     ┐ one message
  sdlc-assessor               ┘
  sdlc-challenger             ← after sdlc-assessor
```

**Horizontal** frameworks (the 23 Architecture Principles, Fowler, Uncle Bob, Evans DDD, Cloud Well-Architected) are the Architecture Constitution. Every assessor applies them.

**Vertical** domain assessors are specialists. Their territories do not overlap. Each has its own thought leaders, and each can run alone.

The Architecture Constitution also has the 12 Agentic Pipeline Principles (AP-1 to AP-12), the 8 Agentic Plugin Principles, and 18 section markers in 9 sections. Assessors load only the section they need.

**File-based protocol.** An assessor never sends its content back to the orchestrator. It writes `<id>/<domain>.md` and returns `DONE: <domain>`. The synthesizer reads the files. The context size stays small for any number of domains. Each run has its own 8-character id, so parallel runs do not collide.

Full C4 diagrams (Context + Container): [`docs/diagrams/architecture-assess-c4.md`](docs/diagrams/architecture-assess-c4.md)

### Context window design

| Stage | Context budget |
|---|---|
| Orchestrator | Codebase scan and coordination only — no domain content |
| Domain assessors | One section of `docs/frameworks.md` (about 90–110 lines, not about 600), the assessment, one file, and `DONE:` |
| Synthesizer Pass 1 | Full `docs/frameworks.md` and the YAML headers only (42 lines at most) |
| Synthesizer Pass 2 | Findings map and full narratives only for domain pairs with a tension |

`session.py new` makes the temp folder. `session.py clean --older-than 60` deletes old ones. `session.py remove <id>` deletes one. It deletes only folders under `.architect-tmp/`. See [ADR-003](docs/adr/ADR-003-architect-context-window-optimization.md).

## Bounded Context Isolation

AP#7c (Bounded Context Session Isolation): each bounded context in a multi-domain repository gets its own `CLAUDE.md` encoding ubiquitous language, domain constraints, and prior decisions — preventing cross-domain context pollution that degrades LLM reasoning in multi-context codebases. Extends Eric Evans's bounded-context principle (DDD Ch. 14) into the LLM agent session layer.

See [ADR-009](docs/adr/ADR-009-ap7c-bounded-context-session-isolation.md). When the project has no bounded-context graph, the draft has a `## Recommended prerequisite` section. It says to run `/business-domain:setup`, then `/business-domain:learn` with the bounded contexts, before you choose the architecture style.

## The Architecture Principles

23 principles for good architecture in the era of AI. They are the base of this plugin. See [`docs/frameworks.md`](docs/frameworks.md) for the full text and the thought-leader frameworks.

Key economic equation: **Cost ∝ Speed × Accuracy at customer WTP at this business stage** (Principle #17)

## Simplicity Gate

Before a result is final, the Simplicity Gate asks:

> *"Is this as simple as it has to be for the problem, stage, and strategy — nothing more?"*

The synthesizer argues against its own result. When `thinktank` is in the session, `review` and `design` also run `thinktank:debate` on the verdict. Complex architectures kill projects. This gate is not optional.

## Methodology Reference

See [`docs/frameworks.md`](docs/frameworks.md) for:

- The Architecture Principles (all 23, full text)
- The Agentic Pipeline Principles (AP-1 to AP-12)
- The Agentic Plugin Principles (8)
- Martin Fowler — key patterns and contributions
- Robert C. Martin (Uncle Bob) — Clean Architecture, SOLID
- Eric Evans — Domain Driven Design
- Cloud Well-Architected Frameworks (AWS/GCP/Azure)
- Diagram standards (C4 Model, Mermaid, Event Storming, ADR format)

The ADRs in [`docs/adr/`](docs/adr/) are the history of the plugin. [`docs/INDEX.md`](docs/INDEX.md) lists them.

## Tests

```bash
cd plugins/architecture-assess && pip install -r requirements-dev.txt && pytest tests/ -q -rs
```

All tests must pass with 0 skips.

## Credit

The plugin is a port of the `architecture` plugin, version 2.10.2, of a private repository. The MIT notice is in [`NOTICE`](NOTICE). See [`CHANGELOG.md`](CHANGELOG.md).
