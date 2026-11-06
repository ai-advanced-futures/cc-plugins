# ADR-010 — The finance engine and the verdict ceiling

**Status:** Accepted · **Date:** 2026-10-29 · **Amended:** 2026-10-29 (v0.3.1, a v0.2.0 report in the handoff); 2026-10-30 (v0.4.0, a run rate in the cautious rule; every figure that is not settled, in any scenario, names itself; a sentence written twice; a change after funding; the saved reviews that stop counting)

## Context

Before v0.3.0 every saved report said `"investment_verdict": "undetermined"`,
because nothing computed whether the investment pays. Plan 3 adds the
arithmetic and the verdict. Two rules from the parent design shape it: code
does the arithmetic, and the model computes nothing (spec §6). The
independent review, the `judge` agent, can still see what the numbers cannot:
an evidence page that contradicts the case.

The verdict also has to stay honest over time. A report counts only while the
files it read are current (ADR-002), and the numbers must be the numbers the
review read.

## Decision

### The engine

`lib/finance.py` computes, per scenario, from the figures that count
(ADR-009). It uses only the standard library. Money is `decimal.Decimal` in a
28-digit context (`basis.CONTEXT`), and code rounds only for display.

- A figure's amount is spread evenly over its months, and the last month
  takes the remainder. Cash in is positive; cash out is negative.
- **NPV** is the sum over months *m* of the month's net cash ÷ (1 + *i*)^*m*,
  with *i* = (1 + annual rate)^(1/12) − 1, at the end of each month. A
  terminal value joins the last horizon month.
- **Payback** is the first month *m* where cumulative net cash was below zero
  in some month before *m*, and is zero or above in *m* and every later month
  of the horizon. With no month below zero, the result is "no outflow to pay
  back". When the horizon ends below zero, it is "not within the horizon".
- **Cumulative net cash** and **ROI**, (cash in − cash out) ÷ cash out, are
  over the horizon. With no cash out, ROI is not computable.
- Payback, cumulative net cash and ROI are not discounted, and leave out the
  terminal value, which is a valuation and not cash.
- **Revenue by year** covers each full year of the horizon, and growth is
  (year *n* ÷ year *n*−1) − 1. Growth after a year with no revenue is not
  computable. Growth is shown to the funder and does not enter the ceiling.
- **Grade shares** are gross: each grade's share of the summed absolute
  per-figure, per-month amounts, discounted for NPV. The lowest grade follows
  the order primary, secondary, estimated.

A scenario takes the base figures and replaces each one its own figures name
in `replaces`. A scenario figure replaces a base figure only while it counts.

The engine needs a parsed discount rate, horizon and start month for NPV and
payback. Without them, it records why and computes neither.

### `finance.json` and the cut

Only `bc.py brief` writes `finance.json`. `bc.py brief` holds the decisions
lock from before it computes until it has written the brief, so
`finance.json` and the brief read one length of `decisions.jsonl`. On
Windows the lock does not exist (ADR-007). The brief takes
the manifest of the review's inputs before it computes, and computes with
`decisions.jsonl` and `figures.jsonl` cut at that manifest's lengths. The
brief then refuses, and counts no run, when its own manifest differs from the
inputs `finance.json` records. `bc.py compute` writes only `finance-view.md`,
the person's preview.

`finance.json` holds the input digests, the decisions length, the basis, each
figure's state, each scenario's totals, the cautious cash, the ceiling and
its reason, the findings code adds and the uncovered amounts. It has sorted
keys and no timestamp, so the same files give the same bytes.

`finance.json` is never an input to the arithmetic: compute derives it from
`figures.jsonl`, the case and the decisions. Other code reads it only to check
that it is current or to copy it into the funding snapshot. The independent
review reads it, and `save-report`, the coach copy and the re-derive compute
everything again. Each of them computes with `decisions.jsonl` and `figures.jsonl` cut at the
byte length the brief's manifest recorded. A decision recorded after the
brief, or a figure confirmed after it, therefore never changes what a saved
report says. A figure is still a new line in a file the review judges on its
full digest, so it makes the report not current (ADR-002).

### The verdict ceiling

The ceiling is the highest verdict the numbers allow. The numbers are the base
scenario's. A figure of any scenario that does not count yet keeps the verdict
from reading supported.
Code applies the rules in this order: rule 1, then rule 2, then rule 3, then
rule 4. The first rule that holds sets the ceiling and its reason.

1. `not_supported`, when the cautious NPV is below zero, or the cautious cash
   never pays back within the horizon and no counted terminal value covers
   the cautious cash still owed at its end. The cautious cash counts every
   live base `cost` and `cannibalisation` as stated, settled or not. It counts
   each judgment exclusion that is not settled as cash out, unless a live
   cost or cannibalisation figure quotes the same amount. The cautious cash
   never counts a run rate: a run rate is not cash, and it settles on the
   person's confirmation alone (ADR-009). This reverses 0.3.1's rule that the
   funder must approve leaving a run rate out. It counts only the income that counts.
2. `undetermined`, when any of these holds:
   - the basis is incomplete;
   - a live figure of any scenario is not settled: base figures first, then
     the other scenarios' figures, each by figure ID, and the reason names the
     figure;
   - a money amount code cannot read: no figure can cover it, and the person
     rewrites it in the case;
   - a money amount is written twice in the same words: a sentence that an
     earlier sentence of the same section repeats, and no figure records its
     second copy. Code never guesses whether the copies are one amount or two;
   - a money amount is not covered by a settled figure;
   - NPV or payback cannot be computed;
   - there is no outflow to pay back;
   - the share of NPV or of cumulative net cash that rests on estimates is
     above the rubric's limit;
   - NPV is above zero and the terminal value's share of it is above that
     limit.
3. `not_supported`, when the counted NPV is below zero, or payback is not
   within the horizon and no counted terminal value covers the counted cash
   still owed at its end.
4. `supported`, otherwise.

Nothing unconfirmed, unapproved or rejected can rescue a case whose own
numbers say no. A terminal value lifts the payback test only when it covers
the whole cash still owed, so a token value buys nothing, and rule 2 stops a
case whose NPV leans on its terminal value beyond the limit.

Rule 3 never fires before rule 1: the cautious cash is at most the counted
cash in every month, so a counted NPV below zero, or counted cash that never
pays back, means the cautious one does too. The reason shown is therefore
always the cautious one from rule 1. Code keeps rule 3 as the design states
it, as a backstop if the cautious cash ever changes, and a test reaches it
directly through `ceiling_of` (Task 10 ruling).

The estimate limit is the rubric's `estimated_share_threshold`, read as
`Decimal(str(x))`. A share exactly at the limit is within it. A funder's
accept on a finding does not raise the ceiling.

### The findings code adds

Code adds an `amount` finding, under the completeness job, for each money
amount no confirmed figure covers, when `BC-FIGURES-COMPLETE` applies to the
case. It adds a `total` finding, under the job `investment`,
for each scenario and each of NPV, cumulative net cash and ROI whose share
from estimates is above the limit. The anchors are in ADR-008.
`finance.json` lists each one, so the review can name it as a reason.

### What the independent review decides

The review reads `figures.jsonl` and `finance.json` and computes nothing. Its
reply gives `investment_verdict`, at or below the ceiling, and
`verdict_rests_on`, the findings the verdict rests on. Each finding sets at
most one level, findings never add up, and the verdict is the ceiling or the
lowest level any single finding sets. A `claim` finding on a paragraph that
holds a sentence a counted figure quotes sets `undetermined`.

`agents/judge.md` lets the review go below the ceiling to `not_supported` in
one case only; code checks only that a verdict below the ceiling names a
finding. A
`claim` finding sets `not_supported` when the evidence page that the LARGEST
revenue figure that counts cites states that the figure's basis is false:
buyers will not buy, or a price, a volume or a rate below the one the case
uses. Code names that figure in finance.json under `largest_revenue`: the base
scenario's revenue figure that counts with the largest total over the horizon,
the lowest figure ID on a tie, so the review never ranks figures itself. The
same finding on any other figure sets `undetermined`.

The operator adopted this rule on 2026-10-29 after a test of 15 runs: five
cases at a `supported` ceiling, three independent runs each, gave
`not_supported` in 6 of 6 runs where it was expected and in 0 of 9 runs
elsewhere. The test's set criterion failed only on one clean case, where one
run of three found a real gap and gave `undetermined`; that came from the
existing `undetermined` rule, not from the new one.

Such a finding states the contradiction in plain words: the figure, the
evidence page, and the case's number against the page's. The contradiction
goes back to the person: in an interactive run the coach shows it first and
offers to correct the figure, bring newer evidence or answer it in the case
text, and in an automated run the handoff's `problems` names it while no
decision answers it.

### What the funder reads

`lib/finance_view.py` writes `finance-view.md` in plain words: each scenario's
NPV, payback and ROI with their grade shares, the base scenario's cautious
numbers when they differ from the counted ones, the ceiling and its reason, and each figure that does not
count yet, with why. When the ceiling is `not_supported` and the offering's
own cash never pays back, it adds the operator's sentence (2026-10-29):

> The offering's own cash, including what it is worth at the end, does not pay back what it spends. These numbers do not count value to the rest of the business, such as keeping existing customers or drawing them to other products. A funder may still choose to fund it for that reason.

Code shows it only when the ceiling is `not_supported`, the base payback from
every live figure as stated is not within the horizon, and the terminal value
does not cover the cash still owed (`finance.own_cash_short`, Task 21 ruling
N1). A negative NPV alone does not show it: the ceiling's reason already
explains a negative NPV.

### An older report

A report saved before v0.3.0 keeps counting: its reply gave neither verdict
key, a missing pair reads as `undetermined` with no reasons, and the re-derive
gives the report as v0.2.0 saved it. Its manifest lists no `figures.jsonl`,
so the re-derive reads no figures, and its status is what it was. The funding
decision refuses such a report with "run the independent review again
first", because there is no `finance.json` the report read. Until a new review
is saved, the handoff's `problems` names such a report, so the handoff is
never `done`, even for a case a funder funded under v0.2.0.

A report saved by v0.3.0 or v0.3.1 stops counting when v0.4.0 derives a
different ceiling for its case, which can happen for a case with a run rate, a
cost that replaces a restating total, a sentence written twice in the same
words, a figure of another scenario that is not settled, or an amount code
cannot read, which now has its own ceiling reason. The report keeps counting
only while its saved ceiling, value and reason, equals what today's code
derives. Status then says the report does not count as the judge's report,
and the route is to run the independent review again, which status writes as
`run the judge again with a new brief`. No file is broken, so no file needs a
repair. A funded case reopens: the loop is not done until a new review is
saved. A case that none of the five touches keeps its report.

### The funding snapshot

Under the lock on `decisions.jsonl`, before it appends a funding decision, the decision
record saves the exact `finance.json` bytes the cited report read as
`funding/finance-report-NNN.json`, named after the report. A snapshot with
the same bytes is reused. A snapshot is never rewritten: one with other bytes
refuses the decision. The decision cites the snapshot (ADR-005).

An edit to the snapshot changes its digest, so the decision no longer matches
the files it cites. A forged snapshot whose recorded digest was edited to
match is not counted: code checks the snapshot's recorded digest against the
`finance.json` digest in the cited report's manifest, and `status` names the
decision as not counted. The snapshot is not an input to the review.

When a file the latest funding decision cites changes or is deleted, `status`
and the handoff's `problems` name the change, one line for each file. That is
the latest funding decision in `decisions.jsonl`, counted or not: a deleted
file stops the decision counting, and it is still named. A later hand-written
funding line that still matches its files can hide an earlier change, which
is accepted because `status` names that line as not counted. A changed
snapshot or report reads "restore the file, or run the independent review
again and record a new funding decision": a snapshot often cannot be
restored, and a new review saves a new snapshot. A changed
`business-case.md` reads "the funder decides again". A funding decision from
before v0.3.0 cites no snapshot, so it gets only the `business-case.md` line.
The lines are not reasons: a stale decision never changes `done` in `status`, or it would
block the new funding decision the line asks for. They go when a newer
funding decision matches its files.

`funding_changes` holds those lines. It is a field of `status --json`, and a
status built without it is refused. It never raises for a funding line or a
cited path. The same lines join `problems` in the saved handoff, which then
is not done; `done` in `status` stays as it was.

## Consequences

- The verdict a funder reads is computed by code and checked again at every
  save. A review cannot raise it.
- A case can read "not supported" on its numbers alone, and the funder's view
  says why, beside the cautious number that decided it.
- A growth case whose end value does not cover what it spends reads "not
  supported". The funder's view says that value to the rest of the business
  is not counted, and the funding decision stays the person's.
- The review's own `not_supported` rests on one tested rule, and the person
  can answer it.
- A case from v0.2.0 opens without an error, and must be reviewed again before
  it can be funded.
