# ADR-005: Wave Orchestrator, Belt-and-Suspenders Completion, and Model Tier Optimization

**Status:** Accepted
**Date:** 2026-03-11
**Extends:** ADR-003 (file-based inter-agent protocol), ADR-004 (pipeline-safe orchestration)

> **Note on the port.** This ADR first described a live progress path with an agent team. A subagent cannot manage a team: only the main session can. So the wave orchestrator is now a completion sweep with no team. The text below gives the decisions that stay in force.

---

## Context

A cross-plugin architectural comparison covered three plugins of the same authors:

| Plugin | Orchestration Pattern | Progress Signaling | Completion Detection |
|---|---|---|---|
| architect v2.4.0 | Pure subagent dispatch (parallel) | ❌ Silent | Return line `DONE:` only |
| data-strategy v0.1.0 | Hybrid team + subagent dispatch (waves) | ✅ Live relay | Belt-and-suspenders: `.done` files + a second signal |
| talent-finder v1.1.0 (planned) | Pure dispatch → Hybrid | ✅ Live relay on scraping | Return line only → + `.done` |

Three improvement opportunities were identified from the comparison:

### Problem 1: Silent Parallel Execution (UX)

When 2–8 domain agents run in parallel, the user sees nothing for 5–20 minutes. The time depends on codebase size and domain count. There is no feedback loop. Data-strategy solved this with a `wave-orchestrator` team member that relays live progress. The architect plugin has no equivalent.

### Problem 2: Single Completion Signal (Reliability)

Architect relies only on the return value (`DONE: {domain}`) as the completion signal for each domain agent. If an agent crashes before it returns, the orchestrator has no second way to see that a domain is incomplete. Data-strategy uses a belt-and-suspenders pattern: `.done` flag files (always written) plus a second signal.

### Problem 3: Uniform Model Tier (Cost + Speed)

All 8 domain assessors use the same model. Three of these agents do mostly pattern-matching work. They detect configuration files, check framework presence, and scan for logging libraries:

- `cicd-assessor` — finds `.github/workflows/`, `Dockerfile`, `Jenkinsfile`
- `observability-assessor` — finds OpenTelemetry imports, `otel-*.yml`, SLO files
- `testing-assessor` — finds `tests/` dirs, coverage configs, `pact/` directories

These are detection tasks, not reasoning tasks. They do not resolve cross-domain tensions, apply 23 Architecture Principles, or perform multi-framework synthesis. Haiku (3× faster, ~3× cheaper) is appropriate for detection-first domains. The five reasoning-heavy domains (`software-architecture`, `infrastructure`, `aiml`, `data-mesh`, `agentic-plugin`) stay on sonnet.

---

## Decision Drivers

- **Architecture Principle #3 (Model Tier):** Right model for right task — detection domains should not use reasoning-tier models
- **Architecture Principle #5 (Parallel Dispatch):** Parallel execution without a completion check is hard to trust
- **Architecture Principle #15 (Resilience):** A single completion signal is a single point of failure
- **data-strategy ADR-001 D3:** Belt-and-suspenders principle — the file-based signal is primary

---

## Decisions

### D1: Wave Orchestrator (Agent — `architecture-assess:wave-orchestrator`)

The `wave-orchestrator` agent is a **completion sweep with no team**. After the assessors return, the orchestrator dispatches the wave orchestrator 1 time. It receives the temp folder and the confirmed domains. It is a **pure observer**: it does not dispatch domain agents, does not accumulate domain content, and does not gate the dispatch of the synthesizer.

**Role:** Read each `<slug>.done` file → write `wave-timeout.json` with each domain that has no `.done` file → return one line.

**Return line:** `wave-complete: <n> domains verified` or `wave-partial: <n> of <m> domains verified`.

**Thin-agent invariants (Standards Check 23):**
- Tools: `Read`, `Write` only — no `Agent`, `Glob`, `Grep`, `Bash`
- Does NOT read `{domain}.md` files — no domain content in its context
- Does NOT forward domain content to any recipient

**Sweep rule:** The sweep runs 1 time. The agent does not implement a timer loop. A missing domain is a warning, not an error. The synthesizer already handles missing domain files (`status: missing`) and reads `wave-timeout.json`.

**Reason for no team:** The orchestrator is a subagent. Only the main session manages a team. A subagent cannot start a team, so a live progress path cannot run inside the pipeline. If a later Claude Code lets a subagent lead a team, the live progress path can come back as an optional step.

### D2: `.done` Flag Files (Belt-and-Suspenders Completion)

Every domain agent writes a `.done` flag file immediately after writing its primary output file:

```json
{"domain": "{slug}", "constitution_check": "{value}", "top_risks": N}
```

Written to: `{output_dir}/{slug}.done`

**Use cases:**
1. The wave orchestrator reads `.done` files as the second completion check
2. Post-crash recovery — identifies which domains completed before a session failure
3. The synthesizer can tell "agent ran but produced no output" from "agent never ran" (both are `status: missing` from the `session.json` view, but `.done` presence tells them apart)

The orchestrator's primary completion detection stays the return line `DONE: {domain}`.

### D3: Haiku Model Tiers for Pattern-Matching Domains

Three domain assessors move from the sonnet tier to the haiku tier:

| Agent | Rationale |
|---|---|
| `cicd-assessor` | Detection-first: finds pipeline configs, workflow files, Dockerfile presence |
| `observability-assessor` | Detection-first: finds OTel imports, logging configs, SLO definition files |
| `testing-assessor` | Detection-first: finds test directories, coverage configs, chaos tool markers |

Seven agents remain on sonnet:

| Agent | Rationale |
|---|---|
| `orchestrator` | Coordination requires reasoning; bounded scan + domain detection |
| `wave-orchestrator` | File sweep; sonnet is sufficient, haiku adds risk |
| `software-architecture-assessor` | Horizontal methodology guardian — applies all 23 Architecture Principles |
| `infrastructure-assessor` | Serverless-First Ladder + economic analysis — multi-framework reasoning |
| `aiml-assessor` | Karpathy + Huyen + Ng + Weng cross-framework synthesis; Agentic Pipeline Principles AP-1–AP-12 |
| `data-mesh-assessor` | Dehghani domain principle application + Reis/Housley lifecycle reasoning |
| `agentic-plugin-assessor` | 8-phase PLUGIN/BORDERLINE/TEMPLATE scoring; nuanced principle application |

One agent remains on opus:
- `synthesizer` — cross-domain tension resolution, Simplicity Gate, full ADR production

### D4: Orchestrator Dispatch Order

After the assessors return, the orchestrator dispatches `wave-orchestrator` 1 time with the temp folder and the confirmed domains. Then it dispatches the synthesizer. The orchestrator is the only agent that dispatches the wave orchestrator. The wave orchestrator has no other caller.

---

## Architecture (v2.5.0)

### Agent Roster

| Agent | Model | Role | Change |
|---|---|---|---|
| `orchestrator` | sonnet | Coordination, scan, dispatch | + dispatch of the sweep |
| `synthesizer` | opus | Cross-domain synthesis, ADR | Unchanged |
| `wave-orchestrator` | sonnet | Completion sweep | **New** |
| `software-architecture-assessor` | sonnet | Horizontal methodology | + `.done` write |
| `infrastructure-assessor` | sonnet | Platform + economics | + `.done` write |
| `aiml-assessor` | sonnet | AI/ML + AP-1–AP-12 | + `.done` write |
| `data-mesh-assessor` | sonnet | Data pipeline + mesh | + `.done` write |
| `agentic-plugin-assessor` | sonnet | Plugin principles scoring | + `.done` write |
| `cicd-assessor` | **haiku** | Pipeline config detection | + `.done` write, model ↓ |
| `observability-assessor` | **haiku** | OTel/logging detection | + `.done` write, model ↓ |
| `testing-assessor` | **haiku** | Test file/framework detection | + `.done` write, model ↓ |

### Execution Flow

```
orchestrator
  └─ Step 0: temp folder (made by the skill with session.py)
  └─ Step 1: scan for domains (bounded, 3 levels)
  └─ Step 1.5: write session.json
  └─ Step 2: end with NEEDS-INPUT; the skill confirms the plan
  └─ Step 3: dispatch all confirmed domain agents in one message, in the foreground
       ├─ software-architecture-assessor → writes {slug}.md + {slug}.done → DONE:
       ├─ infrastructure-assessor        → writes {slug}.md + {slug}.done → DONE:
       └─ [optional domain agents]      → writes {slug}.md + {slug}.done → DONE:
  └─ Step 3.5: dispatch wave-orchestrator 1 time (completion sweep)
       ├─ reads each {slug}.done file
       └─ writes wave-timeout.json for each missing domain
  └─ Step 4: dispatch synthesizer
  └─ End: DONE: orchestrator — adr_draft=<path>
```

The user sees no live progress during the assessors. The sweep tells the synthesizer which domains are missing.

---

## Component Changes

| Component | Before (v2.4.0) | After (v2.5.0) |
|---|---|---|
| `orchestrator` | No sweep | Dispatches the sweep after the assessors |
| `wave-orchestrator` | — | New agent; sonnet; pure observer; 1 sweep |
| `cicd-assessor` | sonnet | **haiku**; + `.done` write |
| `observability-assessor` | sonnet | **haiku**; + `.done` write |
| `testing-assessor` | sonnet | **haiku**; + `.done` write |
| Remaining 5 domain agents | sonnet; file write + `DONE:` | sonnet; + `.done` write |
| `plugin.json` version | 2.4.0 | 2.5.0 |
| Agent count | 10 | 11 |

---

## Consequences

### Positive
- `.done` files provide post-crash forensics and secondary completion detection
- The synthesizer knows which domains are missing from `wave-timeout.json`
- Haiku downgrade on 3 agents: ~3× faster execution for those domains, ~3× cost reduction
- The wave orchestrator is additive — the pipeline still works if the sweep reports a partial result

### Negative / Trade-offs
- `wave-orchestrator` adds an 11th agent file to maintain
- Haiku domain agents may produce slightly shallower detection analysis — acceptable given their pattern-matching role
- `.done` file write is a new convention that all future domain agents must follow
- There is no live progress while the assessors run

### Risks

- **Haiku detection accuracy (mitigated):** cicd/observability/testing assessors produce `tension_flags` that inform synthesizer Pass 2 reads. If haiku produces fewer or less precise tension flags, synthesizer Pass 1 may miss some cross-domain tensions. Mitigation: monitor synthesizer `tension_pairs` output across runs; revert to sonnet if flag coverage drops.
- **wave-orchestrator context accumulation (mitigated):** If wave-orchestrator inadvertently reads domain `.md` files, it violates Standards Check 23. Mitigation: a test enforces that its tools list has no Glob or Grep; `.md` reads are not in its workflow.

---

## Simplicity Gate Verdict

**Is a new agent justified?** Yes. The wave-orchestrator is a short workflow, not a new infrastructure component. Its only job is to read `.done` files and write one JSON file.

**Could wave-orchestrator be a skill instead?** No — a skill runs in the main conversation, but the sweep runs inside the orchestrator run, between the assessors and the synthesizer.

**Is the `.done` file the right secondary signal?** Yes — it is the established pattern from `data-strategy`. File-based signals are persistent across context compaction events; in-memory signals are not.

---

## References

- ADR-003 — file-based inter-agent protocol
- ADR-004 — pipeline-safe orchestration and model tier foundation
