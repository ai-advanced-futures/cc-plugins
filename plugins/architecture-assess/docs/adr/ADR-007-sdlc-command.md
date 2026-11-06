# ADR-007 — Architect v2.7.0: Agentic SDLC Command

**Status:** Accepted
**Date:** 2026-03-21
**Plugin Version:** architect v2.7.0

---

## Context

The architect plugin assesses code architecture but has no visibility into the organization's
software development lifecycle (SDLC) maturity. Users ask "what should we adopt next?" after
an architecture assessment, but the plugin has no lifecycle framework to answer this.

---

## Decision Drivers

1. Architecture assessments naturally surface SDLC gaps (missing CI/CD, no testing harness, no observability)
2. Users need actionable toolchain recommendations grounded in their current maturity
3. Plugins cover the full SDLC but there is no guide connecting them to lifecycle phases
4. Users need public marketplace plugin recommendations, found at run time

---

## Decision Outcome

**Add the `sdlc` command** (`/architecture-assess:sdlc` after the port) with two new agents:
- `sdlc-assessor` (constructive, sonnet) — 9-step assessment flow, writes `sdlc-spec.md`
- `sdlc-challenger` (adversarial, sonnet) — challenges assessor findings, writes `challenge-flags.json`

**Auto-chain at Step 4.7** in the orchestrator — runs automatically after every `/architecture-assess:assess`
and `/architecture-assess:design` session using the produced ADR draft as input.

**Section-marker loading** in `docs/sdlc-frameworks.md` — 14 markers, loaded on demand.
Agents never load the full file.

**Dynamic toolchain discovery** via WebSearch against `§toolchain-sources` URLs — never hardcoded.
Extensibility: adding a new marketplace = one line in `§toolchain-sources`, no agent code change.

---

## Simplicity Gate Verdict

**PASS.** Two agents sharing one framework file. Sequential dispatch (assessor → challenger).
No new wave-orchestrator and no team. SDLC assessment is additive to
the existing flow — Step 4.7 failure does not fail the architect session. Minimum viable
implementation of a lifecycle assessment layer.

---

## Consequences

**What becomes easier:**
- Architecture assessments now produce an actionable SDLC roadmap automatically
- Users get toolchain recommendations grounded in their actual maturity tier

**What becomes harder:**
- `orchestrator.md` is longer by ~30 lines (Step 4.7 block)
- `sdlc-frameworks.md` must be maintained as the SDLC methodology evolves

**Known trade-offs:**
- Dynamic WebSearch for toolchain discovery means recommendations are only as current as
  the marketplace repos — a gap of hours to days is acceptable
- sdlc-challenger is skipped when no ADR is available — standalone use gets no adversarial review
