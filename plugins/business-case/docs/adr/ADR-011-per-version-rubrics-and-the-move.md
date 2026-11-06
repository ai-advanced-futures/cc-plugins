# ADR-011 — Per-version rubrics and the move to a newer one

**Status:** Accepted · **Date:** 2026-10-29

## Context

A case is pinned to the rubric version it was opened with (ADR-002). Until
v0.3.0 only rubric `1.0.0` shipped, and the item set and the met-test IDs were
fixed in code. Plan 3 adds rubric `1.1.0`, whose met tests ask for what the
finance engine now computes (ADR-010). A case on `1.0.0` must be able to move
to it, and the decisions it already holds must not silently answer a test
that changed.

## Decision

### Items and met tests come from the rubric file

`lib/rubric.py` reads the item set and each item's met-test ID from the
rubric file. A met-test ID is `<item id>.M<n>`. An item may carry
`"computed": true`: code settles its result, and the independent review
only reads it. `rubric/rubric-1.0.0.json` and `rubric/rubric-1.1.0.json` both
ship.

### What rubric 1.1.0 changes

Rubric `1.1.0` differs from `1.0.0` in these items:

- `BC-FIN-BASIS` asks for all five basis lines, the start month included.
- `BC-FORECAST-Y1` asks for confirmed `revenue` and `booking` figures, each
  split by stream, in each quarter of months 1 to 12.
- `BC-PAYBACK-CASH` is computed: `finance.json` holds a base payback result,
  a month or "not within the horizon".
- `BC-SCENARIOS` is computed: `finance.json` holds NPV and payback for the
  base case and at least one other scenario, and the sensitivity inputs are
  stated.
- `BC-CUSTOMER-TYPES` also asks a B2B or both-markets case to name its target
  segments by company size, state the size band of each, and name the
  segments it rules out, or say that it rules out none and why.
- `BC-FIGURES-COMPLETE` is new and computed: every money amount in the money
  sections is covered by a confirmed figure.

Every other item and its met-test ID stay as they were. The items that
keep their met tests include `BC-UNIT-ECONOMICS-B2B` and
`BC-UNIT-ECONOMICS-B2C`, because unit economics arithmetic is not in plan 3.
The estimate limit stays at 0.3.

A met on a computed item cites `finance.json`, plus the evidence pages its met
test asks for, as `BC-SCENARIOS` asks for its sensitivity inputs. Code checks
that its own result holds what the met test names, and checks each page as
for any met.

### The move

`bc.py init` opens a new case on the newest rubric that ships, found from
the rubric files present, unless `--rubric-version` names another. For a
case on an older version, the coach compares that version with the newest
one and offers the move. A move is the
funder's decision, because it changes the standard the case is judged by.

`bc.py move-rubric --to <version>` takes the question and the funder's reason
from files, or the question inline. It runs these steps:

0. It refuses unless the session has a named person, so an automated session
   never moves a rubric.
1. It refuses a version that does not ship and an older one. It refuses the
   current version too, unless an earlier move to it stopped before its
   decision was written.
2. Under the decisions lock, it copies the new rubric into `rubric.json`, then
   updates `scope.json`, then `case.json`, then adds a ledger entry for each
   new item. Each write is atomic.
3. It writes the `move_rubric` decision, in the funder role, about the case,
   citing exactly `rubric.json` (ADR-005).

The decision is written last, after every file has moved, so the decision is
the record that the move is finished. A run that stopped part-way is completed
by running the command again. A finished move says that it is already
recorded, and writes nothing.

The rubric copy is a review input, so a move makes the latest report not
current. The case needs a new independent review, and the coach maps the case
again, because the new rubric can add items.

### Decisions after a move

From 0.3.0, every decision about an item records the item's met-test ID when
it is written. An item decision counts only while the met-test ID it
answered equals the item's met-test ID in today's rubric copy. A decision
written before 0.3.0 has no such field, and code reads it as an answer to
`<item>.M1`, the `1.0.0` test. A decision that no longer counts is listed as
"needs another look" and is never deleted. A new decision on today's test
that answers the same finding or proposal clears it. An answer to a
not-relevant proposal counts only while the proposal it answers counts.

Estimate and exclusion approvals survive a move. They approve a piece of
evidence or an exclusion for a figure, not an answer to a met test, so the
figure keeps counting. Decisions on whole-plan findings, and on items whose
met-test ID did not change, keep counting.

### Cases that stay on 1.0.0

The engine, the ceiling and the verdict apply to every case. The `amount`
findings and `BC-FIGURES-COMPLETE` apply only on `1.1.0` and later, because
only those rubrics have the item. Ceiling rule 2's coverage condition applies
to every case (ADR-010).

A `1.0.0` case can meet `BC-FIN-BASIS`, whose met test asks for four basis
lines, while the engine still needs the `Start month:` line, so the ceiling
reads "the financial basis is incomplete" until the person adds that line.

## Consequences

- A case moves only when the funder says so, and the decision record shows
  when and why.
- A stopped move never leaves a case half on one standard: running the
  command again finishes it.
- After a move, the funder answers again each item whose test changed, and
  keeps every approval of evidence and every exclusion.
- A later rubric version needs only a new rubric file and its tests.
