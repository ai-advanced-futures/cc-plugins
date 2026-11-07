# Pricing Plugin — Documentation Index

This file is the discoverability hub for the pricing plugin's documentation. See `README.md` at the plugin root for the user-facing overview; this INDEX lists every ADR, diagram, and reference document.

## Architecture Decision Records (ADRs)

ADRs live in `docs/adr/`. Each ADR records a specific architectural decision with context, rationale, and consequences.

- **[ADR-001-pricing-plugin-architecture](adr/ADR-001-pricing-plugin-architecture.md)** — Original pricing plugin architecture (paths A/B/C, multipliers, frameworks).
- **[ADR-002-lognormal-amplifier-composition](adr/ADR-002-lognormal-amplifier-composition.md)** — Charter §14.1 resolution: closed-form LogNormal composition for the 8 cost amplifiers under the independence assumption.
- **[ADR-003-phase-1-insight-workflow](adr/ADR-003-phase-1-insight-workflow.md)** — New `agentic-pricing-strategist` agent for the framework's Phase 1 Insight diagnostic, alongside `new-offering-pricer` and `pricing-auditor`.
- **[ADR-004-terminal-node-to-pattern-bundle](adr/ADR-004-terminal-node-to-pattern-bundle.md)** — Default mapping from each of the 8 canonical terminal nodes to its recommended pattern bundle (P1-P19 + P12-Light).
- **[ADR-005-inferred-archetype-cost-data](adr/ADR-005-inferred-archetype-cost-data.md)** — `data_source` enum on `EffectiveCostResult` distinguishing framework_table baselines from inferred_v1_4_0 baselines (3 archetypes each).
- **[ADR-006-bounded-product-safety-check](adr/ADR-006-bounded-product-safety-check.md)** — Bounded-product safety check: 5-row cost-ratio override matrix + canonical class slugs; hybrid agent+lib split .
- **[ADR-007-agentic-pricing-charter](adr/ADR-007-agentic-pricing-charter.md)** — Charter that couples the plugins that use the framework by shared schemas, with vocabulary linting.
- **[ADR-008-publication-gate](adr/ADR-008-publication-gate.md)** — Charter §17 publication gate: scanner that runs as a test in CI against `multiplicative score` / `pricing power index` / `pricing risk index` / `single numeric pricing risk` with mandatory-reason `check42-allow:` directive .
- **[ADR-009-gm-trajectory-vertical-alignment](adr/ADR-009-gm-trajectory-vertical-alignment.md)** — Align gm_trajectory vertical-archetype caps to the C4 values (60/70/80, step +7); makes `requires_vertical_anchor_for_70plus` reachable.
- **[ADR-010-plugin-result-file](adr/ADR-010-plugin-result-file.md)** — Adopt the plugin result file for `pricing:price`: the price runner, the Path A gate and person-run confirmation, the grade of a Path A price, and scripts that run with `uv run` from a rooted path.
- **[ADR-011-read-the-upstream-graphs](adr/ADR-011-read-the-upstream-graphs.md)** — `brain_read.py` reads the jtbd graph and the competitive-intelligence graph through the save scripts of their writers; the snapshot a price cites; the session-start note.

## C4 Architecture Diagrams

Diagrams live in `docs/diagrams/`. They follow the C4 model (Context → Container → Component → Code).

- **[pricing-c4-context.md](diagrams/pricing-c4-context.md)** — Level 1: pricing plugin in its system context.

## Reference

- **Plugin manifest:** `.claude-plugin/plugin.json`
- **Release notes:** `CHANGELOG.md` (the first heading is the version in `plugin.json`)
- **Charter sentinel:** `.charter-conforms` (schemas this plugin produces or consumes per Charter §8)
- **Schemas of the Charter:** `schemas/agentic-pricing/` (see its `README.md`)
