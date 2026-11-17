---
name: test-audit
description: "Evaluate test value when writing, changing, reviewing, or removing tests. Find duplicate tests, weak assertions, and production interfaces used only by tests."
---

# Test audit

A useful test detects a distinct fault in observable behavior or an independent
contract. Test removal reduces repeated proof while preserving those contracts;
the number of deleted tests is not a success measure.

## Required results

- For each new or changed test, identify its protected behavior, a fault that
  makes it fail, and the gap in existing tests. Each contract has one primary
  test owner; another layer needs a distinct transport or lifecycle risk.
- Use the [audit criteria](references/audit.md) for test selection and validation.
  A candidate report precedes edits and includes every field in
  [candidate evidence](references/audit.md#candidate-evidence). Missing evidence
  blocks deletion because the test may be the only proof of a contract.
- Preserve the [retained contracts](references/audit.md#retention-bar), including
  independent source checks. A test that fails at baseline is a possible product
  defect, not evidence for removal.
- A regression test fails before the fix at the intended guard and passes after
  it. Report an unavailable baseline. Changes that preserve behavior leave tests
  passing; negative controls fail for the stated reason.
- An audit removes obsolete production interfaces used only by retired tests and
  places retained regressions at their production owner's boundary. Tables and
  shared fixtures replace repeated setup without adding test-only interfaces.
- For a whole subsystem, produce the evidence in [CAMPAIGN.md](CAMPAIGN.md).
  The [source-specific requirements](README.md#source-specific-requirements)
  identify the OpenClaw guides and tools that this skill uses.
- Report causes, removed categories and interfaces, retained contracts, test
  results and cost, production versus test/support line counts, PR state, and
  follow-ups. Commit, push, or merge only with task authority, because these
  actions change shared state.
