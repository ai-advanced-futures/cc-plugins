# ADR-007 — Agentic pricing charter

| | |
|---|---|
| Status | Accepted (2026-05-18). Rewritten for the marketplace port (2026-11-06). |
| Context source | JustKeenAI Agentic Pricing Framework v2.1 (see `ATTRIBUTION.md`) |

## Context

The pricing plugin encodes five frameworks (Amadeo, Ramanujam, Campbell, Helmer, Ulwick). The JustKeenAI Agentic Pricing Framework v2.1 is a layer above them. It decides which pricing pattern to choose, and how to defend the price against falling AI costs.

Other plugins use the same framework. Each plugin must ship alone, and the plugins must still agree with each other.

## Decision

**Schema-coupled federation.** The pricing plugin owns the Python code of each framework formula and decision rule. Other plugins build only the part they need. They make their handoff files match the shared JSON Schemas in `schemas/agentic-pricing/`.

**A linter holds the vocabulary.** The package `vocabulary_linter` checks that internal words (cost-coverage equilibrium, vendor margin, two-sided risk) never reach a customer-facing file. An agent file has the frontmatter `audience: internal | customer-facing | mixed`. The linter runs in the tests.

**The source is named.** `ATTRIBUTION.md` records the JustKeenAI v2.1 source and the sha256 of the upstream text. Each file that comes from the framework starts with a line that names it.

**One schema has a new name.** The Charter schema `transition-phase-status` is `agentic-pricing-transition-phase-status`. The new name prevents a clash with the phase schemas of other tools.

**Doc-contract tests hold the rules.** `tests/unit/test_charter_cross_plugin.py` reads the matrix of the Charter. A plugin that follows the Charter has a `.charter-conforms` file.

## Alternatives considered

1. **Pricing as a shared library.** Other plugins would import `pricing/lib/` at run time. Rejected: Claude Code plugins have no safe way to import Python code from another plugin.

2. **Independent builds.** Each plugin builds its own part with no shared schema. Rejected: after some months, "P12" or "amplifier #3" would mean different things in different plugins.

3. **One plugin only.** Rejected: the framework is worth most when a cost diagnostic, a clause package and a plan use the same contracts.

## Consequences

**Good:**

- Each plugin ships and gets its version alone, against schemas that do not change.
- A test holds the vocabulary rule. Review does not need to.
- The source is recorded once and a test checks it.

**Not good:**

- The shared schemas are one more contract to keep.
- The pattern ID check reads `pattern_catalogue.yaml` where no other plugin exports the IDs.

## References

- `ATTRIBUTION.md`
- `schemas/agentic-pricing/README.md`
- `pricing/lib/charter_exports.py`
