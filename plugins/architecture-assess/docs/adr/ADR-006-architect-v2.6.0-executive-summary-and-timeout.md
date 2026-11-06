# ADR-006: Architect v2.6.0 — Executive Summary Deliverable and Timeout-Resilient Synthesis

**Status:** Accepted
**Date:** 2026-03-11
**Authors:** Luis F. Amadeo
**Supersedes:** ADR-005 (extends, does not supersede)
**Implemented in:** v2.6.0

---

## Context

After shipping v2.5.0 (wave-orchestrator, .done files, haiku tiers), two gaps remained:

1. **Audience gap:** The unified ADR is a technical artifact. CPOs, CDOs, and board members who need architectural context cannot consume it without translation. The assessment currently produces no stakeholder-facing deliverable.

2. **Timeout gap:** The wave-orchestrator's timeout warning was informational only. Neither the orchestrator nor the synthesizer had a durable artifact recording which domains timed out. The synthesizer had no way to surface timeout information in the ADR, leaving readers unaware that findings may be incomplete.

---

## Decision Drivers

- **Audience coverage:** Architecture decisions affect business stakeholders who are not engineers. They need a one-page summary, not a 50-page ADR.
- **Durability of timeout signal:** Ephemeral log warnings disappear. The synthesizer must be able to read timeout state even after the wave-orchestrator has exited.
- **Additive-not-load-bearing:** Both new features must degrade gracefully — the DONE signal cannot depend on them.
- **Standards Check 23 (non-accumulation):** The orchestrator must not read domain output files. The executive summary agent reads only the ADR (a final artifact), not domain files.

---

## Decisions

### D1 — Executive Summary Agent (P2)

Add `executive-summary-agent.md` as a twelfth agent in the pipeline. It is a pure translation agent:

- **Model:** sonnet (translation is language work, not reasoning-heavy synthesis)
- **Tools:** Read, Write only — no Agent, no domain-scanning tools
- **Input:** the draft of the synthesizer (`unified-adr.md` in the temp folder)
- **Output:** `executive-summary.md` in the temp folder. The skill then writes it to `docs/architecture-assess/<date>-<slug>-executive-summary.md`.
- **Invocation:** Orchestrator Step 4.5 — after synthesizer returns, before DONE signal. The orchestrator always runs it.

**Output structure (fixed template):**
- TL;DR (2–3 sentences, business language)
- Architecture Health Score (5-row table: Foundation, Scalability, AI/ML Readiness, Delivery Velocity, Operational Risk — with 🟢/🟡/🔴 status and business impact)
- Top 3 Risks (each with plain-language title, business impact, probability, urgency)
- Recommended Actions (5-row table with effort S/M/L and expected business outcome)
- Integration Opportunities (downstream plugin routing suggestions)

**Translation rules:**
- All technical jargon replaced with business equivalents
- Every risk must have a business impact statement, not just a technical description
- Effort sizes: S = days, M = 1–4 weeks, L = 1–3 months

**Why not in the synthesizer?** Separation of concerns: the synthesizer produces the authoritative technical artifact; a second agent translates it without contaminating the ADR with business-language approximations. Also preserves the synthesizer's bounded context (it does not need to hold both technical and executive outputs simultaneously).

### D2 — Timeout Artifact (P3 — wave-timeout.json)

Extend the wave-orchestrator sweep to write `{output_dir}/wave-timeout.json` before it exits:

```json
{
  "timed_out_at": "{ISO timestamp}",
  "timed_out_domains": ["{slug-1}", "{slug-2}"],
  "completed_domains": ["{slug-a}", "{slug-b}"]
}
```

The synthesizer checks for this file at the top of Pass 1 (before reading domain headers). If found, it prepends a ⚠️ Timeout Notice to the ADR header listing the timed-out domains and recommending independent re-runs.

**Why a file and not a return value?** The wave-orchestrator does not gate synthesizer dispatch. The orchestrator dispatches the synthesizer independently. A file is the only durable channel that the synthesizer can read later.

### D3 — Orchestrator Safety Net (P3 — belt-and-suspenders)

The orchestrator dispatches the assessors in 1 message, in the foreground, and has each result before it goes on. The `.done` file check of the sweep is the safety net: if a domain agent crashed before it returned, its `.done` file is absent, and the domain is a warning in `wave-timeout.json`.

This completes the three-layer resilience model:
1. **Agent return** — primary completion signal (happy path)
2. **.done file** — secondary completion signal (crash recovery)
3. **wave-timeout.json** — tertiary signal for synthesizer (timeout surface)

---

## Consequences

### Positive

- CPOs and board members get a one-page deliverable without translating the full ADR themselves
- Timeout information is durable and surfaced in the ADR (no silent omissions)
- Three-layer resilience model is now complete
- The executive summary is a plain file in `docs/architecture-assess/`, so other tools can read it

### Negative / Trade-offs

- One additional agent dispatch adds ~30–90 seconds to wall-clock time
- Executive summary accuracy depends on ADR quality — garbage in, garbage out
- The synthesizer's timeout check adds a file-existence read at the top of Pass 1 (negligible cost, but the pass is no longer purely in-memory)

### Neutral

- wave-orchestrator gains Write dependency (was Read only) — acceptable since it already has Read

---

## Alternatives Considered

### Alt-1: Executive Summary as a synthesizer output section

**Rejected.** The synthesizer uses opus and already has high cognitive load (two-pass synthesis, Simplicity Gate, Constitution Gate). Adding a business-language translation layer would increase its context consumption and mix audiences in a single artifact. Separate agent = separate context window = cleaner output.

### Alt-2: Timeout via orchestrator polling loop

**Rejected.** The orchestrator already delegates the completion check to the wave-orchestrator (Standards Check 23). A polling loop in the orchestrator would duplicate that role and violate the thin-coordinator principle. The wave-orchestrator is already the right place to detect timeout — it just needed to write a durable artifact.

### Alt-3: Surfacing timeout in a file that the orchestrator writes after synthesis

**Rejected.** Such a file exists only after synthesis completes. At that point the synthesizer has already finished — it cannot retroactively add a timeout notice to the ADR. The artifact must be written before synthesis begins.

---

## Simplicity Gate Verdict

> *"Is this as simple as it has to be for the problem, the business stage, and the product strategy — and nothing more?"*

**Yes.** Both features are minimal additions:
- The executive summary agent has 2 tools (Read, Write) and a fixed output template. No new dependencies.
- wave-timeout.json is a single JSON file write. The synthesizer adds one file-existence check.
- Neither feature modifies the core assessment pipeline or its outputs.

---

## Cross-Plugin Integration

- **gtm plugin:** Architectural health scores map to positioning claims (evidence for Tier 1 claims)

---

*Written for architect plugin v2.6.0; kept as history of architecture-assess*
