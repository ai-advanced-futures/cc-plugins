# Changelog

All notable changes to the pricing plugin will be documented in this file.

The first heading is the version in `.claude-plugin/plugin.json`. A test checks that they agree.

## 1.11.0

- This plugin now lives in the marketplace `cc-plugins`. It ports the private plugin at version 1.10.1.
- The agents run without a person. Only the skills ask questions. When an agent has no value for a required input, it writes `.pricing/open-questions.json` and ends with `DONE: pricing OPEN: .pricing/open-questions.json`.
- Scripts run with `uv run`. Each script holds its own list of packages.
- The files that the plugin needs from the old repository root now live in the plugin: the schemas in `schemas/agentic-pricing/`, the vocabulary checker in `vocabulary_linter/`, and the result-file check in `tests/support/`.
- The plugin writes no handoff file for another system. Each agent writes its own files in `.pricing/`.
- The agents and skills pass `/prompt:revise`: 0 findings and 222 instructions in the 16 files (before the review: 234 instructions and 39 findings).

## v1.6.0 — 2026-05-30

- **Charter §17 publication gate.** New `pricing/lib/charter_publication_gate.py` scanner and a test that runs in CI. Forbidden patterns: `multiplicative score`, `pricing power index`, `pricing risk index`, `single numeric pricing risk` (literal, not case-sensitive).
- **`check42-allow:` directive.** A match on the same line or the line before is allowed when the directive gives a reason. A directive with no reason is a violation. A 4-step parser handles trailing comment-close markers (`-->`, `*/`, `"""`).
- **ADR-008.** 8 numbered decisions: the gate belongs to the pricing plugin, the parser for Contract A, and why the patterns are long.
- **Charter v1.1.0 to v1.2.0.** New §17, a clearer §15.1, and a §15.5 entry for v1.2.0.
- **pyproject.toml.** A test (`test_pricing_v1_6_0_lockstep`) checks that the version in `pyproject.toml` agrees with `plugin.json`.
- `test_charter_contracts.py` expects 8 schemas. `CHARTER_MATRIX` has `amplifier-telemetry-input`, as Charter v1.1.0 says.
