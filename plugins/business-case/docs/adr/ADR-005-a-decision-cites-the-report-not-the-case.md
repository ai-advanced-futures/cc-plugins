# ADR-005 — A decision on a finding cites the report, not the case

**Status:** Accepted · **Date:** 2026-10-27 · **Amended:** 2026-10-29 (v0.3.0, exclusions, the move and the funding snapshot); 2026-10-30 (v0.4.0, a run rate needs no funder approval)

## Context

Each decision cites the files it rests on. A decision stays valid while the
files it cites are unchanged. The question is which files.

A funder accepts a finding, and then the coach fixes another paragraph of
`business-case.md`. If the accept cited `business-case.md`, that edit would
cancel it. The funder would have to accept the same finding again after every
edit. And a finding can only be accepted by a person, so the loop could not
end without asking again.

## Decision

What a decision cites is fixed by its kind and subject.
`lib/decision_record.py` refuses any other cite.

| Kind | Role | About | Cites |
|---|---|---|---|
| `fix` | funder | a finding | the saved report that holds the finding; evidence pages may follow |
| `accept` | funder | a finding | the saved report that holds the finding; evidence pages may follow |
| `waive` | funder | a finding or a proposal | on a finding: the saved report that holds it; on a not-relevant proposal: nothing |
| `approve_estimate` | funder | a proposal | exactly the pages the estimate proposal cites |
| `reject_estimate` | funder | a proposal | exactly the pages the estimate proposal cites |
| `propose_estimate` | proposer | an item | one or more evidence pages, each `estimated` and listing the item, or holding a figure for the item that is graded an estimate |
| `propose_not_relevant` | proposer | an item | nothing, or evidence pages |
| `reject_not_relevant` | funder | a proposal | nothing |
| `propose_exclusion` | proposer | a figure | nothing |
| `approve_exclusion` | funder | a proposal | nothing |
| `reject_exclusion` | funder | a proposal | nothing |
| `move_rubric` | funder | the case | exactly `rubric.json` |
| `fund`, `do_not_fund`, `defer` | funder | the case | the latest saved report, `business-case.md` and that report's snapshot `funding/finance-report-NNN.json` |

A decision on a finding cites the saved report, `judge/report-NNN.json`, and
not `business-case.md`. Nothing the coach edits changes a saved report. So a
fix to the case does not cancel an earlier accept or waive.

No decision cites the raw reply, its receipt, the brief, or a file the coach
keeps for itself: `inputs/`, `changelog.jsonl`, `ledger.json`, `case.json`,
`scope.json` or `decisions.jsonl`.

### An estimate approval names its page through the proposal

The proposer proposes an estimate with `propose_estimate`, citing one or more
evidence pages of grade `estimated` that list the item. The funder answers
that proposal with `approve_estimate` or `reject_estimate`, citing exactly
the same pages. A page is approved for an item when the latest valid answer
to a proposal that cites it is `approve_estimate`. The approval covers that
item and that page only.

A judge's *met* that cites an `estimated` page counts only when the page is
approved for the item, and only when the approval is in the part of
`decisions.jsonl` that the judge read. Otherwise the judge runs again.

A figure can be graded an estimate when its page is not: every terminal
value, and every figure whose page names `business-case.md` as its source.
`propose_estimate` may cite such a page for the figure's item, when a live
figure for that item stands on the page. Code checks this against the
figures as they are today.

### An exclusion approval names its figure through the proposal

An excluded figure with no `restates` that is not a run rate takes money out
of the numbers on a judgment, so the funder must approve it (a run rate
settles on the person's confirmation alone, ADR-009; a `propose_exclusion` on
a run rate is accepted and changes nothing).
`propose_exclusion` is the proposer's decision about that figure: its
subject is the figure's `FIG-NNN`, it has no item, and it cites nothing.
`approve_exclusion` answers that proposal: its subject is the proposal's
`D-NNN`, it has no item, and it cites nothing.
`reject_exclusion` answers the same proposal in the same way, and cites
nothing.
Until the funder approves it, the exclusion covers no amount.

### A rubric move cites the rubric copy

A move to a newer rubric changes the standard the case is judged by, so
the funder records it. `move_rubric` is about the case, has no item, and
cites exactly `rubric.json`. The options are exactly `move_rubric` and
`stay`. Only the move writes this decision, and it writes it last, after it
copies the rubric and updates the case's files. So the decision is the
record that the move is complete. `bc.py decide` refuses the kind.

### A funding decision cites its snapshot

The person cites the latest saved report and `business-case.md`. Before it
appends the decision, the decision record saves the `finance.json` that the
report read as `funding/finance-report-NNN.json`, and adds that snapshot to
the decision's cites (ADR-010). When the record is checked again, the
snapshot must hold the `finance.json` digest that the cited report's
manifest recorded. A person may not cite the snapshot directly. A funding
decision written before 0.3.0 cites only the report and `business-case.md`,
and still counts. A report that read no `finance.json` cannot be funded:
the decision is refused until the independent review runs again.

### A statement page is primary

Some met tests name the case's own text under "Evidence that counts". For
each such item the coach writes one page whose method is
`the proposer's own statement` and whose source is the section that holds
it. Its grade is `primary`: the met test asks only that the statement
exists, and the proposer is its originator, so there is no estimate to
approve. The person confirms the grade as for any page. An item whose met
test asks for the evidence behind a plan, `BC-PRICING-EVOLUTION`, gets no
statement page: a plan is a forecast, so its page is graded by that evidence.

### The assumptions register route

`BC-PRICING-EVOLUTION` accepts an entry in the assumptions register as
evidence when the page's source is `business-case.md §assumptions`, its grade
is `estimated`, and the funder approves the estimate. The judge's `met` counts
only after that approval. Here "register" means the case's `assumptions` section, not
`register.jsonl`.

`evidence.case_source_problem` enforces the source rule, at write time and in
the judge report check. A source that starts with a strategy file name, or a
path to one, is refused. A source that starts with `business-case.md`, or a
path to it, must read `business-case.md §<section>` for a section the case has.
Its page is graded `estimated` unless every item it lists is a statement item.
A case file name counts only as a whole name, whatever mark follows it:
`register.jsonl:3` and `docs/register.jsonl` name the register, while
`meeting-notes.jsonl` and `register.jsonl.bak` name other files. A support page
may name no case file anywhere in its source. A page that supports a register entry or a condition may list no item.

### When a finding counts as decided

Spec §4 step 8 ends the loop only when the latest report "has no finding
without a decision". So each finding needs its own decision.

- A finding is decided by its own latest answer. `accept` and `waive` decide
  it. `fix` does not.
- An `accept` or `waive` on one finding decides only that finding. An item
  can carry a completeness finding and claim findings. Accepting a claim
  does not decide the completeness finding, and it does not close the item.
- The one decision about a whole item is a `waive` of the proposer's
  not-relevant proposal. It decides every finding on that item, in this
  report and in later ones.
- An item is accepted (`accepted_risk`) or waived through its findings only
  when every finding on it in the latest report has its own `accept` or
  `waive`.
- Only the findings of a report that counts as the judge's (ADR-006) let
  answers close an item. An answer to a finding that exists only in a coach
  copy closes nothing.

The plan's first rule let any `accept` on an item decide all its findings.
The final review showed that this ends the loop with a not-met item the
funder never saw, so the rule was dropped (ruling FR-I1).

## Consequences

- An edit to the case never cancels an accept or a waive.
- The funding decision cites `business-case.md` as well as the report, so it
  names the exact case that was funded.
- An accept stays tied to the finding the funder saw. A new judge run with
  new findings needs new answers, except on an item whose not-relevant
  proposal the funder waived. A finding the judge reports again keeps its ID,
  so its earlier answer still counts.
- Code re-checks every recorded decision with the same rules when it decides
  loop end. A record that fails counts as no answer.
