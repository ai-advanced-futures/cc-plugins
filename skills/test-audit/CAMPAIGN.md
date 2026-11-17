# Subsystem test audit

A campaign covers one subsystem's tests in one PR. The criteria and validation
in [SKILL.md](SKILL.md) apply throughout. Each stage supplies the evidence for
the next; edits depend on the recorded baseline, decisions, and plan.

## Evidence before edits

The baseline records a pinned `main` commit, test/support line counts, and the
result of every in-scope test file. Baseline failures have a separate defect
list, because a failing test can expose a product bug.

The inventory assigns every owned test file and QA/live scenario to one group
based on production ownership, including cases at shared boundaries. A read-only
review of each group covers full tests and parameter tables, production owners,
entry points, callers, history, and CI routing. It produces one decision per
test declaration, based on assertions rather than the name. An `it.each` is one
declaration unless its rows need different decisions.

Each decision has an evidence line and one of these marks:

| Mark | Required evidence |
| --- | --- |
| `R`: retain | The contract and fault detected. A file move retains this mark and records the destination. |
| `F`: repair | The retained contract and the assertion to repair, including a negative assertion that passes with missing items. |
| `C`: combine | The retained test that absorbs the assertion before removal: a table row, boundary suite, or shared owner. |
| `D`: delete | The proof that remains, or why no contract needs proof. |

A second read-only review produces a plan for repeated test layers, rather than
treating the per-test decisions as an edit list. Each group plan names retired
files, a retained suite for each contract, assertions to transfer, corrections
to the decisions, and production interfaces that become unused. A real transport
boundary with a fake network takes precedence over a mocked collaborator when
both cover the same contract.

## Evidence after edits

Each group's retained suites pass. Shared test runners and support files have
one writer. Moved suites remain in CI routing and test inventories; line-count
limits reflect the change; subsystem `AGENTS.md` rules record ownership lessons
from the audit. Retired tests leave no production-only-for-tests parameters,
getters, reset exports, or indirection.

Before completion, independent reviewers for each boundary group compare removed
coverage with retained suites. Their findings include lost contracts and
assertions that pass without reaching the stated condition. Each gap is restored
or rejected with source evidence. Every restored contract has a deliberate
production change that makes its retained test fail, with the source then
restored byte for byte.

Product fixes have separate commits at their production owner, a real user-flow
test, a failing control that reverts the fix, and a passing candidate on the same
test runner. Unrelated defects remain follow-ups.

## Integration and handoff

For a long campaign, merge `main` rather than rebasing its commits, because the
review evidence follows those commits. If `main` edits a retired test, preserve
the deletion and transfer its added contract into the retained suite. Every
regression added on `main` still has a test owner. PR CI runs the subsystem suite
on the merged head; local reruns cover merge-touched tests and CI failures. Live
proof repeats when merged inputs affect its contract.

The handoff extends the [skill report](SKILL.md#required-results) with baseline
and final counts, ownership groups, retired layers, retained suites, preservation
gaps and their detected mutations, and product defects with control/candidate
results. It records review limits such as truncated file lists, and maintainer
decisions about compatibility flags, in PR evidence rather than changing gates.
