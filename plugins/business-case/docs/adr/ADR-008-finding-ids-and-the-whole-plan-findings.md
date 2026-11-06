# ADR-008 — Finding IDs and the whole-plan findings

**Status:** Accepted · **Date:** 2026-10-28 · **Amended:** 2026-10-29 (a pointer to ADR-010)

## Context

In v0.1.0 a finding's ID was a hash that included the item the judge chose. The
judge could pick another item for the same claim in the next run. The ID then
changed, and the funder's earlier answer no longer applied.

Plan 2 adds the whole-plan job. Its findings are about the register, the
conditions, the notes or the plan, and they have no item. Some of them are
facts code can see for itself: an absent category, an unsupported condition, an
orphaned condition. Code must not leave these to the judge.

## Decision

### The ID

A finding's ID is `F-` plus the first ten hex digits of the sha256 of
`job|target_kind|anchor`. Code derives the anchor. The judge does not give it.
The item is not in the hash, so the judge's choice of an item for a claim does
not change the ID.

| Target kind | Anchor |
|---|---|
| `claim` | the section key and a hash of the paragraph's text |
| `missing_item` | the item ID |
| `register_entry`, `condition`, `note` | the ref: `SD-NNN`, `C-NNN` or `N-NNN` |
| `category` | the category key |
| `plan` | the plan ref |
| `amount` | the section key, a hash of the sentence, the position and the written amount |
| `total` | the scenario, the total and the share from estimates, to four places |

The `plan` target names one whole-plan test. `PLAN_REFS` holds the five:
`rumelt-goals`, `rumelt-fluff`, `rumelt-no-focus`, `martin-opposite` and
`eliminates-work`. Any other ref is refused.

### Jobs and targets

| Job | Target kinds |
|---|---|
| `evidence` | `claim` |
| `completeness` | `missing_item`, `amount` |
| `whole_plan` | `register_entry`, `condition`, `category`, `note`, `plan` |
| `investment` | `total` |

A `claim`, `missing_item` or `amount` finding names its item. A whole-plan finding has
`item_id` null, and code refuses an item on one. A `register_entry` or
`condition` target must be a live one. A `category` target is valid only for a
category with no stated or confirmed entry, and it names the category by its
key, not by its title. A `note` target must be a note code counts.

### Code adds the required findings

Code always adds the required findings, with fixed summaries, whatever the
judge gave:

- one for each absent category, with the anchor `key|absent`;
- one for each unsupported condition, with the anchor `C-NNN|unsupported`;
- one for each orphaned condition, with the anchor `C-NNN|orphaned`.

When a condition is both, orphaned wins. A judge finding on the same target has
no state in its anchor, so the two are separate findings, decided apart. The
funder answers each one.

### Code adds the money findings

Only code adds `amount` and `total` findings, and the validator refuses a
reply that gives one. Code adds an `amount` finding on the item `AMOUNT_ITEM`
for each money amount that no confirmed figure covers, when that item applies.
Its anchor is the section key, a hash of the sentence, the position and the
written amount. The second copy of a repeated sentence adds its copy number,
so the two copies are two findings. Code adds a `total` finding, with no item,
for each scenario and total whose share from estimates is above the limit. Its
anchor is `scenario|total|share`, with the share to four places, so a changed
share is a new finding. For a `total` finding, the totals checked against the
estimate limit, and how code computes each share, are in ADR-010.

### One finding for one target

One finding per job, target kind and anchor. Code refuses a reply that gives
two with the same ID. A `not_met` item still needs at least one finding that
names it, and a finding that code adds counts (ruling P3-43).

### How a finding is decided

A finding is decided by its own answer (ruling `FR-I1`). An `accept` or a
`waive` decides it. A `fix` does not. An answer closes only the item it names
(ruling `I-1`), so an accept on one claim never closes an item that has other
findings. When a later report files a decided finding under another item, the
earlier answer still decides the finding, but the new item needs its own
answer: `status` names that item, the finding and the item the answer was for.
A whole-plan finding names no item, so its answer closes no item. A decision on
one names no item, and code refuses one that does.

### The one-time cost

A v0.1.0 case opened with v0.2.0 is not done: its saved report no longer
counts, because every finding ID changed and the eight absent-category findings
are missing, so it needs a new brief. `status` exits 1 and lists all eight
categories as absent. The funder must answer every finding of the new report again,
because no earlier accept or waive names a new ID.

## Consequences

- The judge's choice of an item no longer changes an ID. A finding the judge
  reports again keeps its ID, and its earlier answer still decides it. When the
  judge files it under another item, the funder answers it once more for that
  item, because an answer closes no other item.
- A strategy gap that code can see cannot be missed or dropped by the judge.
- The funder answers each whole-plan finding, and so cannot end the loop with a
  category absent and no word said about it.
- An older case pays this cost once. The next report uses the new IDs.
