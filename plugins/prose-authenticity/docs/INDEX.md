# prose-authenticity — docs index

## Architecture Decision Records

- [ADR-001: Deterministic Loop Control](adr/ADR-001-deterministic-loop-control.md) — the decision to iterate or stop in the humanize loop is in `lib/loop_controller.py`, a tested state machine. It is never in agent prose.
- [ADR-002: Fact-Guard Federation via grounded-synthesis](adr/ADR-002-fact-guard-federation.md) — the plugin dispatches grounded-synthesis to check that a rewrite keeps the facts. It does not build its own fact check. A failed dispatch lowers the loop to 2 iterations and marks the output UNVERIFIED FACTS.
- [ADR-003: Tiered Detectors](adr/ADR-003-tiered-detectors.md) — the heuristics, hf, and api tiers give one verdict. The order is api, then hf, then heuristics. The plugin does not blend the scores.
- [ADR-004: Voice Profiles as User-Project Data](adr/ADR-004-voice-profiles-as-user-data.md) — voice profiles are in the project of the user at `.prose-authenticity/profiles/`. They are not in the plugin.
- [ADR-005: Rhetorical-Question Gate](adr/ADR-005-rhetorical-question-gate.md) — a rhetorical question in expository or binding prose fails `check`, whatever the composite score. This is a fourth verdict input that is not in the composite. Literary and verbatim text are exempt, for different reasons.
- [ADR-006: STE Is a Separate Check](adr/ADR-006-ste-as-separate-check.md) — ASD-STE100 conformance and AI likelihood are two different measures. The checker has its own verdict and its own config file. It does not join the detector composite.
- [ADR-007: Derived STE Subset](adr/ADR-007-derived-ste-subset.md) — the checker covers only the STE rules that a machine can verify exactly. The rules are in the words of this project. They are not copies from the ASD standard.
- [ADR-008: Discipline Map and the Tell-7 Conflict Rule](adr/ADR-008-discipline-map-and-conflict-rule.md) — a discipline map gives each writing surface one of three modes: STE and tells, tells only, or neither. The STE sentence cap and tell 7 conflict. Rule R7 enforces a floor for the standard deviation, and does not pick a winner.
- [ADR-009: Zone Markers in Code Contexts](adr/ADR-009-zone-parser-code-contexts.md) — a marker is real only if it matches the raw source, line by line, outside a closed fence. A separate code mask feeds the guard for malformed markers. It never decides if a marker exists.
- [ADR-010: Prose correctness check](adr/ADR-010-prose-correctness-check.md) — correctness is a third axis with its own verdict. A general dictionary gave only false positives, so the check fires only on a curated list of misspellings.
- [ADR-011: C3 widens by closed list](adr/ADR-011-c3-closed-lists-and-scoped-rules.md) — English picks the article by sound, and the checker sees spelling. C3 grows by closed lists. A general rule is allowed only where an initialism cannot be mistaken for a word.
- [ADR-012: Correctness constraints live in the prompts](adr/ADR-012-correctness-constraints-in-prompts.md) — the humanizer prompt names the faults that its edits can introduce. The report shows the delta against the original. The checks never gate the loop.

## C4 Diagrams

- [System Context](diagrams/prose-authenticity-context.md) — the boundary of the plugin, and the actors and systems outside it: the author, a caller agent, grounded-synthesis, the HuggingFace Hub, and the commercial detector APIs.
- [Container View](diagrams/prose-authenticity-container.md) — the six agents, the scripts, the config, the state of each run, and how they connect.
