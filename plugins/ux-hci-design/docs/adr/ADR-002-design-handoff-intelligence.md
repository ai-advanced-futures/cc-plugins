# ADR-002: Design Handoff Intelligence — Track 3 Output Standard and Handoff-Complete Criterion

**Status:** Accepted
**Date:** 2026-04-29
**Authors:** Luis F. Amadeo
**Context:** ux-hci-design plugin version 1.2.0, design handoff changes. This text is the port of the original ADR to the cc-plugins marketplace. The decision is the same.

---

## Context

Design sessions made output that was correct, but an engineer could not use it without more questions. A developer agent had to make choices that the design phase must make. These are the problems:

- Colors and spacing used relative words ("a warm neutral gray", "generous padding"). They did not give exact values.
- Interaction states had a name only (for example "hover state"). They did not say what changes on screen.
- Design alternatives had no reason. Engineers opened the same choices again.
- Component names and token names were not consistent, or they did not exist. Engineers had to invent names during the build.

The agent `ux-concept-designer` had no completion gate for handoff. It showed a concept when the concept was design-complete (all sections filled). It did not wait until the concept was implementation-ready. A concept can be consistent and still leave questions for the engineer.

The root cause is the same in both cases. The plugin had a definition of "ready for the next design phase". It had no definition of "ready for engineering".

---

## Decision

### Track 3: implementation-ready output in `ux-researcher`

The agent `ux-researcher` has a third output track. The first two tracks are the research synthesis and the persona and journey artifacts.

**Track 3 (Handoff Intelligence)** makes the agent write the following items for each design decision:

1. **Exact values** where a design token applies. Examples: hex codes (`#1A1A2E`), size values (`16px / 1rem`), times in milliseconds (`200ms`), and semantic token names (`color.text.primary`). A description with no exact value is not enough.

2. **Named state branches** for each interactive element. Write each state (default, hover, focus, active, disabled, error, loading) on its own, with its change from the default state. "Has a hover state" is not enough. This is the standard: "hover: background changes to `#F0F4FF`, border color `#4A6CF7`, 150ms ease-out".

3. **Rejected alternatives with the reason.** For each important decision, write the alternatives and why the team rejected each one. Engineers then do not open closed decisions again.

4. **Component names and token names.** Examples: `PrimaryButton`, `SearchInput`, `spacing.lg`, `color.brand.primary`. The team agrees the names before the handoff.

The agent writes the Track 3 output to `implementation_handoff` of `research_findings.json`, and the brain keeps each item as a `ResearchFinding` page with `finding_kind: implementation_handoff`.

### The 8th quality criterion: Handoff-Complete in `ux-concept-designer`

The checklist of `ux-concept-designer` has an 8th criterion that is mandatory:

> **Handoff-Complete**: A developer agent can build the concept with no follow-up questions. A concept passes only when all of these are true: each interactive state has exact values, each component and token has a name, each important design alternative has a reason, and no open question remains that a designer must answer before an engineer can start.

The agent checks this criterion last, after the 7 other criteria. A concept that fails it is revised before the person sees it.

The agent checks the criterion itself. The schema does not check it, because "no open questions" needs judgment and not a structure match.

---

## Alternatives Considered

### Alternative 1: a checklist after the handoff (rejected)

An engineer would use a checklist at the start of the build. The team rejected it for these reasons: it puts the work on engineering, it does not stop a handoff that is not ready, and engineers must go back to designers for missing items. This is the back-and-forth that the change must remove.

### Alternative 2: schema validation for the Track 3 fields (rejected)

A JSON schema would require fields such as a `hex_values` list or a `states` object. The team rejected it. The shape of handoff data changes with the type of decision: a color decision has hex values, a layout decision has spacing values, and an interaction has state changes. A strict schema would be too weak, or it would make agents write output that matches the structure and has no useful content. Agent judgment is more reliable here.

### Alternative 3: a separate handoff agent (rejected)

An agent `ux-handoff-compiler` would process the design artifacts after the fact. The team rejected it for these reasons: it adds a step to the pipeline, the information already exists in the research and concept phases, and the first agent can ground the values in the design reason better than a later agent.

---

## Consequences

### Positive

- Engineers get exact values at the handoff. This removes the most common cause of rework between design and engineering.
- The team records each design decision with its reason at the time of the decision, while the context is fresh.
- The Handoff-Complete criterion gives design and engineering one shared definition of "done".
- The Track 3 output is a living specification that engineers can use during review.

### Negative and trade-offs

- A `ux-researcher` session takes more time, because it must list values that a session can leave unwritten.
- The designer or agent must decide all design choices to the level of exact values before the research is complete. This is the correct bar, but it can show gaps earlier than some workflows expect.
- The Handoff-Complete check adds one reasoning pass before a concept is shown. For a simple concept with no interaction states, the cost is low, but it is not zero.

### Integration points

- A developer agent reads the Track 3 output. When you change how it reads `implementation_handoff` of `research_findings.json` (or the `ResearchFinding` pages that hold it), or which component names and token names it expects, tell the owner of that agent.
