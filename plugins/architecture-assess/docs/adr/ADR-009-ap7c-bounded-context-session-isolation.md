# ADR-009: AP#7c — Bounded Context Session Isolation

**Status:** Accepted
**Date:** 2026-05-05
**Plugin:** architect v2.9.0 (before the port to architecture-assess)

## Context

Agentic systems (LLM-driven coding agents like Claude Code, Copilot, Cursor) lose reasoning quality when forced to load context from multiple bounded contexts simultaneously. A single root context file (`CLAUDE.md`) for a multi-domain repository pollutes every agent session with irrelevant domain knowledge — terminology from one bounded context bleeds into reasoning about another, ubiquitous-language drift accelerates, and output quality degrades.

Eric Evans's bounded-context principle (Domain-Driven Design, Chapter 14: Maintaining Model Integrity) was originally a code-organization rule. With the rise of LLM agentic systems, the principle extends to the agent session layer: **each bounded context must isolate its own ubiquitous language, domain constraints, and prior decisions in a per-context agent context file.**

A context file for one task or one run is *related* but distinct: it is about temporal scope (one task's work), while AP#7c is about *domain* scope (one bounded context's work). A task may span multiple bounded contexts; a bounded context may span multiple tasks.

## Decision

Each bounded context in a multi-domain repository **must** have its own agent context file (e.g., `<context-slug>/CLAUDE.md`) encoding:

1. The ubiquitous language for that bounded context (canonical terms + definitions).
2. Domain-specific constraints and invariants.
3. Prior architectural and design decisions relevant to that bounded context.

A repository-root `CLAUDE.md` may exist for cross-cutting concerns (test runners, branch policy, code style) but **must not** encode domain-specific terminology that varies across bounded contexts.

This principle is named **AP#7c** in the `docs/frameworks.md` of this plugin, slotted as the third sub-bullet of AP#7 ("AI Architectures Thrive in the Right Software Foundation") in document order, alongside AP#7a (Decoupled Microservices), AP#7b (Domain Driven Design), AP#7d (Event-Driven Architectures), and so on through AP#7i (Responsible AI).

## Consequences

**Positive:**
- Per-bounded-context reasoning quality: agent sessions only see the domain knowledge they need.
- Smaller per-session context windows → lower token cost and faster iteration.
- Clearer error attribution: when an agent makes a mistake in context A, the failure points at context A's CLAUDE.md, not a 50KB monolithic file.
- Onboarding: new contributors can read one bounded context's CLAUDE.md to understand its conventions without absorbing the whole repository.

**Negative:**
- More files to maintain — every bounded context gains a CLAUDE.md.
- Repo-structure discipline required: bounded-context boundaries must be physical (directories), not just conceptual.
- Cross-cutting concerns risk duplication unless explicitly factored into the root CLAUDE.md.

## References

- Eric Evans, *Domain-Driven Design* (2003), Ch. 14: Maintaining Model Integrity (Bounded Context, Continuous Integration, Context Map).
- This plugin's `docs/frameworks.md` AP#7c entry.

## Naming history

This ADR was originally drafted using an aspirational letter (the seventh sub-bullet position) before Round 2 of the design's spec-refining surfaced that AP#7's sub-bullets in `frameworks.md` were unlabelled bare-bold items, not lettered as `b–f`. The natural-position rename to `AP#7c` (3rd sub-bullet in document order) was locked by user decision on 2026-05-05 (refinement-notes.md, Option A).
