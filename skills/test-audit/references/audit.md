# Audit criteria

These criteria support the [required results](../SKILL.md#required-results).
A candidate needs an independent contract or proof that another retained test
covers that contract. Whole-subsystem evidence is in [CAMPAIGN.md](../CAMPAIGN.md).

## Junk patterns

These patterns identify candidates, not automatic deletions. The retention bar
can justify a test that matches a pattern.

| Pattern | What the test fails to prove |
| --- | --- |
| No assertion, self-comparison, identity copier, or expected value made by the subject | An independent expected result. |
| Copied inventory, manifest, export list, or exact source/import/string search | A contract independent of internal names. |
| Private predicate or call-shape check, repeated invocation, or provider-local replay of a shared helper | A risk distinct from the boundary test. |
| Test-only export, global, wrapper, or production entry point | A path used by production callers. |
| Mock that implements the asserted behavior or treats different APIs as equal | The behavior of the real owner. |
| Fixture that supplies receipts, admission, or callback order that the owner produces | The owner's actual output. |
| Persistence assertion against a path the store does not write | The storage contract. |
| Capability flag in place of delivery or acknowledgement | The promised observable result. |
| Negative control that hits another guard or an unreachable rejection | The intended failure condition. |
| Name that promises behavior absent from inputs or assertions | The behavior stated in the name. |

## Retention bar

Independent contracts include public API, SDK, protocol, configuration,
migration, storage, security, platform, defaults, prompt bytes, generated
cross-language output, package, release, architecture, observable ordering, and
regressions with a reproducible failure.

A source check is valid when it is the least-cost independent guard of a
user-facing key, byte, or path, and survives identifier-only changes. Static
checks and slow tests can satisfy this bar. A baseline failure calls for
reproduction and repair at the production owner, rather than test removal.

## Candidate evidence

Before editing, provide a read-only report with the following fields for each
candidate. Missing evidence keeps the test in place because its contract may
otherwise lose its only proof. Dependency claims use dependency source or types;
repository and folder instructions remain applicable.

| Field | Required content |
| --- | --- |
| Candidate | Exact test name and location, actual assertions, and a detectable fault. |
| Production context | Full test and parameter tables; production owner, entry point, callers, callees, siblings, overlapping tests, and CI routing. |
| Interface use | Non-test callers of the covered production or support interface. |
| Remaining proof | Retained test owner, or why the contract needs no test. |
| History | Why the test exists, with the deletion or simplification it permits. |
| Risk and validation | Risk of the proposed change and a focused validation command. |

Retained regressions belong at their owner's boundary. Obsolete interfaces and
dead paths disappear with their tests; shared package or dependency contracts
have one owner. Success reduces repeated proof and production code used only
by tests, rather than replacing it with checks of internal implementation.

## Validation and handoff

Use the boundary/cost guide and proof policy linked in the
[source-specific requirements](../README.md#source-specific-requirements).
Keep the checkout unchanged while a Vitest run is active, because edits
invalidate its result. Required validation evidence includes:

- Passing owner and sibling tests; an executable or dry-run result for removed
  source searches or plan assertions; targeted formatting and `git diff --check`.
- The changed-gate classification from
  `node scripts/check-changed.mjs --dry-run -- <changed-paths>`, followed by the
  applicable checks.
- All phases of `pnpm deadcode:dependencies`, `pnpm deadcode:unused-files`, and
  `pnpm deadcode:exports` before landing removal batches. Removed tests can leave
  unused support files and exports that ordinary PR CI misses.
- A line-count review with `git diff --numstat`, final autoreview, and the
  [skill report](../SKILL.md#required-results), including retained false positives.

Each later audit batch uses a refreshed `main` and renewed candidate evidence,
because the callers and remaining tests may have changed.
