---
description: Use to get an opinionated review of a single architectural decision, pattern, or trade-off. Applies the Architecture Principles plus Fowler, Uncle Bob, Evans DDD, and Cloud Well-Architected to one specific decision. Shows a lightweight ADR with verdict, trade-offs, and Simplicity Gate, and offers to save it as an ADR.
---

# /architecture-assess:review

Opinionated review of a single architectural decision, pattern, or trade-off.

## When to Use

- "Should we use microservices or a monolith for this?"
- "Is this the right database for this use case?"
- "Should we go event-driven here or keep it synchronous?"
- "Is this a good bounded context boundary?"
- "Should we use a frontier model or fine-tune our own?"
- "Is this Clean Architecture? Are we violating the dependency rule?"
- "Is this service decomposition right for our stage?"
- Any single architectural question requiring a principled answer

> **Reviewing a domain-specific pattern?** For deep-dives into AI/ML, CI/CD, data pipeline, observability, testing, or infrastructure specifically — use `/architecture-assess:aiml`, `:cicd`, `:data-mesh`, `:observability`, `:testing`, or `:infrastructure`

## Flow

### Step 1 — Frame the Decision

Ask with `AskUserQuestion` for these 4 items. Skip an item that the text after the command already answers.
- The specific decision or pattern being reviewed (precise description)
- The current or proposed approach (what exists or what is being proposed)
- The alternatives considered (at least one alternative, or ask if none stated)
- Business stage and constraints (brief — enough to calibrate the economic test)

### Step 2 — Apply the Methodology

For the specific decision, apply:

**Architecture Principles check** — which principles are relevant? Apply them:
- Does it align with evolutionary architecture for the current stage? (#1)
- If AI/ML involved: correct use of model architecture, cost/accuracy tradeoff? (#2–#7, #17)
- Serverless-first for the infra component? (#16)
- Economic equation satisfied? (#17)

**Fowler check** — relevant patterns:
- Is this the right time to decompose? (Monolith First)
- Does Event Sourcing/CQRS help here?
- Strangler Fig applicable for migration?

**Uncle Bob check** — structural integrity:
- Does this respect the Dependency Rule?
- SOLID violations?
- Component coupling/cohesion implications?

**Evans DDD check** — domain alignment:
- Is this a bounded context boundary or an internal module boundary?
- Does the Ubiquitous Language hold here?
- Is an ACL needed?

**Cloud Well-Architected check** — operational impact:
- Any of the six pillars negatively impacted?

### Step 3 — Simplicity Gate

Before writing the ADR, apply the Simplicity Gate:

> *"Is this the simplest decision that solves the problem at this stage — nothing more?"*

If `thinktank:debate` is available, invoke it. If not, argue rigorously against your own recommendation before finalizing.

> **Technology currency note:** For decisions involving fast-moving technology choices — AI/ML frameworks, cloud-native tooling, event streaming platforms, LLMOps/MLOps pipelines, database options — use web search to verify that recommendations reflect current best practice. Training data has a cutoff; the ecosystem does not.

### Step 4 — Show the Lightweight ADR

Show this in the conversation. Write no file.

```
# ADR-NNN: [Decision Title]
Status: Proposed | Accepted
Date: YYYY-MM-DD

## Context
[The situation and decision being made]

## Decision Drivers
[Architecture Principles and framework criteria applied]

## Considered Options
- Option A: [description]
- Option B: [description]
- Option C: [description] (if applicable)

## Decision Outcome
**Recommended:** [Option X]

**Verdict:** [Clear, direct statement of the recommendation and primary reason]

### Why This Option
[2-4 sentences explaining the reasoning grounded in methodology]

### Consequences
- What becomes easier:
- What becomes harder:
- When to revisit this decision:

### Trade-offs
[Framework tensions surfaced, if any]

## Diagrams
[Optional: include a C4 diagram or sequence diagram if it clarifies the decision. For simple decisions this section may be omitted.]

## Simplicity Gate Verdict
[Is this as simple as it needs to be? What was ruled out and why?]
```

The first principle name in the ADR names the source of the set 1 time: "Architecture Principle #3 (the principle set of architecture-assess, `docs/frameworks.md`)".

### Step 5 — Save

1. Ask with `AskUserQuestion`: "Save this decision as an ADR?"
2. On yes, call the `architecture:learn` skill with the `Skill` tool. The argument is one decision sentence from `## Decision Outcome`. In the same message, give these facts:
   - Context: `## Context` and `## Decision Drivers`.
   - Decision: the verdict.
   - Why: `### Why This Option`.
   - Alternatives considered: `## Considered Options`.
   - Consequences: `### Consequences` and `## Simplicity Gate Verdict`.

   The first fact that names a principle names the source of the set 1 time, as in Step 4.
3. When `architecture:learn` stops with no ADR, show its line, say that the ADR is not saved, and name `/architecture:setup`. Else show each ERROR, WARN and SKIP line of the checks that it reports.

## Tone

Be direct. Give the recommendation, the reasoning, the trade-offs, and the time to revisit. When the answer depends on a fact, name the fact and give the decision tree.
