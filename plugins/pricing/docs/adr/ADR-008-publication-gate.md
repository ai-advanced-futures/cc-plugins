# ADR-008 — Charter §17 publication gate

**Status:** Accepted (2026-05-30). Rewritten for the marketplace port (2026-11-06).

## Context

An earlier design gave a plugin one number, a multiplicative "Agentic Pricing Power" score. A review rejected it for four reasons: it gives false confidence, it loses information, a person can game it, and it fails for the bounded-product exception classes.

ADR-006 closes the fourth reason with the bounded-product safety check. This ADR closes the first three. It writes the ban in Charter §17 and enforces the ban with a test that runs in CI.

Without the test, a later change (by a person or an AI) could add a multiplicative pricing-power score again, and nobody would see it.

## Decision

1. **The pricing plugin owns the gate.** The gate enforces a rule of the pricing method (no multiplicative pricing-power score). The owner of the method is the pricing plugin.

2. **The test is the gate.** `scan_plugin(plugin_root)` runs in the tests of the plugin, and the tests run in CI on each pull request. A person cannot skip it by forgetting a manual audit.

3. **The scanner is `pricing/lib/charter_publication_gate.py`.** It reads the agents, the skills and the Python files of the plugin. It skips `tests/`, `docs/` and folders that start with a dot.

4. **A match is a literal and is not case-sensitive.** `FORBIDDEN_PATTERNS` holds `multiplicative score`, `pricing power index`, `pricing risk index` and `single numeric pricing risk`. The patterns are long on purpose: existing text such as `Path B (multiplicative when data-poor)` must not match.

5. **An allow directive needs a reason.** `check42-allow: <reason>` on the same line or the line before a match suppresses it. A directive with an empty reason is a violation itself, so a person cannot use it to game the gate. Each exception is easy to find with grep and has a reason.

6. **The scanner reads lines, not syntax.** It does not tell a string from a comment. A `check42-allow:` inside a string suppresses a match on the same line. Review of the pull request is the second check.

7. **The quantile names are not on a list.** The patterns are too exact to match `composite_p75` or `composite_p95`. A test checks that §17 names both quantiles.

8. **Charter §15.1 lists a new publication gate as a reason for a minor version.** The change to Charter v1.2.0 follows this rule.

## Consequences

**Good:**

- A pull request that adds a forbidden pattern fails with the file, the line and the pattern.
- The reason parser has 4 steps. A test covers each step. A new comment-close marker is one line in step 3.
- Contract A reads the patterns of §17 up to the first period. Backtick names after the period (such as `charter_publication_gate.py`) do not change the patterns.

**Not good:**

- Charter §17 names the path of the scanner. If the scanner moves, the Charter text must change.
- The scanner is a line scanner. A scanner that reads syntax would change the contract of §17.
- A shorter pattern would match text that exists today. The test `test_scanner_does_not_flag_existing_pricing_prose` stops this.

## References

- Scanner: `pricing/lib/charter_publication_gate.py`
- Test: `tests/unit/test_charter_publication_gate.py`
- ADR-006: `docs/adr/ADR-006-bounded-product-safety-check.md`
- ADR-007: `docs/adr/ADR-007-agentic-pricing-charter.md`
