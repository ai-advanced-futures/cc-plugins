# ADR-009 — The financial figures file

**Status:** Accepted · **Date:** 2026-10-29 · **Amended:** 2026-10-29 (v0.3.1, run rates and the evidence page); 2026-10-30 (v0.4.0, checks 11 and 12; a run rate settles on the person's confirmation; the amounts a figure run left uncovered)

## Context

Plan 3 adds the arithmetic: NPV, payback, ROI and the verdict ceiling
(ADR-010). Arithmetic needs numbers that code can trust. The case states its
money in prose and in tables, and a model that reads them can miss an amount,
misread one, or count one amount twice. A number the funder (the person who
decides whether to fund the offering) relies on must come from a sentence of
the case, must be checked by code, and must be confirmed by the person.

The plan-3 design is in
`docs/superpowers/specs/2026-10-28-business-case-plan-3-finance-design.md`
§4 and §5.

## Decision

### The file and its lines

`figures.jsonl` in the case folder holds every figure the numbers use.
`lib/figures.py` writes and reads it. It is append-only and hash-chained
through `lib/chained_log.py`, as the strategy files are (ADR-007).

The file has two kinds of line, `figure` and `confirm`. A `figure` line
records one figure, `FIG-NNN`. A `confirm` line records the proposer's
answer to the question that confirmed one figure, word for word.

A figure's status is `stated`, `confirmed` or `superseded`. It is never
stored. Readers replay the lines in file order and derive it. A changed
figure is a new `figure` line that names the old one in `supersedes` and
gives a `reason`.

A reader re-applies check 1, checks 7 to 10, the session rules and the
supersede rules to each line, against the lines before it. A line that fails
one does not count, and the reader names the line and the reason. Checks 2
to 6, 9, 11 and 12 are applied again at every compute (below). So a line
appended by hand meets every check before it counts.

### The kinds

| Kind | In the cash flow? | Used for |
|---|---|---|
| `revenue` | in | cash in, with its stream, `new` or `expansion` |
| `cost` | out | build, deliver, operate and run costs, AI inference included |
| `cannibalisation` | out | revenue taken from the company's other products |
| `terminal_value` | NPV only | what the business is worth at the end of the horizon; at most one per scenario; its month is the last horizon month; it feeds `BC-PAYBACK-CASH` only |
| `booking` | no | the year-one bookings of `BC-FORECAST-Y1` only |
| `ask` | no | the investment the case asks for |
| `excluded` | no | an amount the numbers leave out, with its reason |

Cash out is only ever a `cost` or a `cannibalisation`. The ask, a booking
and a restatement never enter the cash flow, so one amount is not counted
twice.

An `excluded` figure is an amount that is not a new cash flow inside the
horizon: a total that restates other figures, an amount outside the horizon,
or an amount that is not cash. It carries `restates` only when its amount is
the sum of other `revenue`, `cost`, `cannibalisation` or `booking` figures
of its scenario. Code checks that sum. An `excluded` figure with no
`restates` that is not a run rate takes money out of the numbers on a
judgment, so it also needs the funder's approval (ADR-005).

### The twelve checks

Code applies these checks when a figure is recorded. A proposal that fails one
is refused, and the refusal names the check.

1. The figure's own fields: a decimal amount with no sign and no thousands
   separator, a known kind, a stream only on `revenue` and `booking`, months
   for a rate, a quote, an evidence page ID, a reason on `excluded`, `restates`
   only on `excluded`, a booking on `BC-FORECAST-Y1` and a terminal value on
   `BC-PAYBACK-CASH`.
2. The currency is the case's currency.
3. A `revenue`, `cost`, `cannibalisation`, `terminal_value` or `booking`
   figure has months inside the horizon, `from` not after `to`. A terminal
   value sits in the last horizon month. An `ask` or an `excluded` figure may
   sit outside the grid.
4. The quote is one whole sentence or table row of the named section of
   `business-case.md`, as `lib/amounts.py` splits it today.
5. The amount written at the quote's position is the figure's amount: as
   written, or a rate times its months, to the cent. The parts of a figure
   built from parts are checked one by one. A scenario figure of amount 0
   that replaces base figures quotes a zero written in its sentence, such as
   `$0`, at its position. When the sentence writes no zero, the figure gives
   no position, and the sentence names its scenario or a line it replaces as
   a whole word.
6. The figure's item applies to the case, and its evidence page exists and
   lists that item. A proposal with no evidence page is refused here.
7. One quoted amount holds at most one live figure that enters NPV (a
   terminal value included) and at most one live `ask` or `booking`. A live
   `excluded` figure holds its amount alone.
8. No two live figures of one scenario have the same line over months that
   overlap, and a scenario has at most one terminal value, counting the one
   it takes from the base.
9. Each figure that `replaces` names is a live base figure. Each figure that
   `restates` names is a live `revenue`, `cost`, `cannibalisation` or `booking`
   figure of the same scenario,
   and they sum to the amount.
10. A scenario name that differs from another only in letter case, spacing or
    punctuation is refused.
11. A run rate, an `excluded` figure with the run-rate reason (below) or a
    correction of one, is on `BC-ASSUMPTIONS`, written `total`, with no months and no `restates`.
12. A figure that enters NPV is refused when the figures it supersedes,
    directly or through earlier supersedes, include an `excluded` figure with
    `restates` whose restated figures still count. A restated figure counts
    while it, or the correction that now stands for it, is still live and
    enters NPV: a total whose parts still count.

Check 7 lets one quoted amount carry one cash figure, one that enters NPV,
and one `ask` or `booking`, so an ask and the cost it pays for may share one sentence. An
`excluded` figure holds its amount alone: it is not a new cash flow, so a second extraction cannot
add a cash figure on an amount the first marked to leave out.

Checks 2 to 6 read today's case files, check 9 reads today's live figures,
and checks 11 and 12 read the figure and the figure it supersedes. Code applies
checks 2 to 6, 9, 11 and 12 again at every compute (`lib/settle.py`). A figure
that fails one stops counting, and the funder's view says that the case no
longer supports it, and why. A reader never applies checks 11 and 12 to the
lines it replays, so a figure recorded before v0.4.0 that breaks one stays in
the file and reads as no longer supported.

### The grade

A figure's grade is its evidence page's grade, with two exceptions. A figure
is graded `estimated` whatever its page says when it is a terminal value, or
when its page's source names `business-case.md`. A value beyond the horizon
is a projection by nature. The proposer's own text is never evidence for a
number. An estimate counts only after the funder approves it, through
`propose_estimate` and `approve_estimate` on the figure's item and page
(ADR-005). Every reader of a page refuses a grade outside `primary`,
`secondary` and `estimated`, so a register entry or a condition whose support
page has a grade outside that list does not count, and code names the page and its grade.

### When a figure counts

A live `revenue`, `cost`, `cannibalisation` or `terminal_value` figure counts
when it is confirmed, it passes checks 2 to 6, 9, 11 and 12 today, and it is not an
estimate or the funder approved it. A figure that is not cash never counts.
It is settled when it is confirmed and passes the same checks, and an
`excluded` figure with no `restates` that is not a run rate also needs the
funder's approval.
ADR-010 records how an unsettled figure limits the verdict.

Every money amount in the money sections needs a figure. A confirmed figure
covers an amount for the `amount` findings (an `excluded` figure with no
`restates` that is not a run rate only once the funder approves it), and only
a settled one covers it for the ceiling (ADR-010). One quoted occurrence covers one amount.

### Who proposes figures

A second sub-agent, `agents/figure-extractor.md`, reads `business-case.md`,
`scope.json` and the evidence pages the coach lists. It returns its proposals
as JSON in its reply, and its only tool is Read. The coach saves the reply
outside the case folder and runs `bc.py figure --proposals-file <path>`. Code
records each proposal that passes the checks as `stated`. `bc.py figure`
writes the refused proposals of its latest run, or the refusal of the whole
run, and the amounts it left uncovered, to `figure-refusals.json`, and the
handoff names each one (ADR-003, ADR-012).

The extractor's isolation is not enforced: the coach writes its prompt and
handles its reply, and `source` is only a label. The guards are the code
checks, the person's confirmation and the grade rule. Only a person confirms
a figure, in the proposer role, by an explicit answer. An automated session
records only figures with source `extractor`, never confirms one, and never
supersedes a confirmed one.

An annual or monthly recurring revenue amount that the case gives no months
for is a rate at a point in time, not money received over a period. The
extractor records it as `excluded`, with no `restates`, and with the reason
`a rate at a point in time, not a cash flow`. An amount the case places in
months is revenue under the rate rules; a date it is reached by is not months.
Code knows a run rate by that exact reason (`figures.is_run_rate`), and also
as a correction: an `excluded` figure on `BC-ASSUMPTIONS` that supersedes a run
rate is a run rate whatever its reason, so check 11 applies to it. Any other
figure with a paraphrased reason is a plain judgment exclusion, which is the
safe side.
A run rate is left out on the person's confirmation alone, like a total that
restates other figures, and it is never counted as cash. This reverses
0.3.1's rule that the funder must approve leaving it out (v0.4.0).

For a `revenue`, `cost` or `cannibalisation` figure, the extractor cites only
a page that lists the item and states the figure in its `source` or `summary`; for any other kind, any page that lists the item qualifies when none states it.
Among those, the highest effective grade wins, and a tie goes to the lowest page number.
With no such page, it cites a page of the case's own text, which code grades
an estimate, or none, which check 6 refuses. Code cannot test what a page
states; the person sees the page and its grade when confirming.

## Consequences

- Every number in the arithmetic traces to one sentence of the case, one
  evidence page and one confirmation by a person.
- An edit to the case can stop a figure counting, and the funder sees why.
- The extractor can miss or misread an amount. A missed amount stays
  uncovered and keeps the verdict from reading "supported". A misread amount
  is refused by a check, or stopped by the person.
- The scan for money amounts reads written forms only (spec §2). An odd form
  the scan cannot read escapes it; the extractor, the confirmation and the
  independent review's evidence job remain the guards for that amount.
