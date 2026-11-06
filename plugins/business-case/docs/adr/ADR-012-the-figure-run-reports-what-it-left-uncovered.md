# ADR-012 — The figure run reports what it left uncovered

**Status:** Accepted · **Date:** 2026-10-30

## Context

The figure extractor reads the case and its evidence pages and proposes one
figure for each money amount (ADR-009). The coach saves its reply and runs
`bc.py figure --proposals-file`. Before v0.4.0, `figure` on an empty list,
`[]`, rewrote `figure-refusals.json` to `[]`. An extractor that failed, or
that proposed only some of the amounts, then left a handoff that named
nothing about the figures. A case with no amounts and a reply that skipped
every amount looked the same.

The coach also used `figure` on `[]` on purpose, to clear the refusals once
the person had handled them. One command did two jobs, and code could not
tell them apart.

## Decision

### Every run checks what it left uncovered

After `figure --proposals-file` reads a valid array of proposals, `[]`
included, code lists each money amount that no live figure records. This is
the one definition of an amount no figure records
(`settle.amounts_no_figure_records`). The list leaves out three groups:

- a copy of a sentence written twice in the same words in one section: the
  financial view and the ceiling name it;
- an amount code cannot read: the financial view marks it, the ceiling names
  it, and the person rewrites it in the case;
- an amount whose occurrence a refused proposal of the same run quoted: that
  refusal's line already names its sentence.

When any amount remains, the run adds one record to `figure-refusals.json`,
last in the list:

```json
{"kind": "uncovered", "amounts": ["First-year forecast: $50k", "First-year forecast: $120k"]}
```

Each amount names its section by the heading the person reads. `figure` prints
one line for the record and still exits 0:

```
left uncovered: 2 money amounts have no recorded figure: First-year forecast: $50k; First-year forecast: $120k
```

The line lists every amount and is never clipped. With one amount it says
"1 money amount has". The handoff names the record with its own template, and
says that a person records the amounts or the extractor runs again.

The check does not run after a proposals file that is refused, or after the
extractor's failure reply: those already write a record of the refusal of the
whole run. When `business-case.md` cannot be read during the check, the run
adds that refusal, as the refusal of the whole run, after the records of the
proposals it refused, and exits 2.

### The extractor's failure reply

The extractor has one reply for a file it cannot read:
`{"cannot_read": ["<path>", ...]}`. Code accepts it only as an object with
exactly that key and a non-empty list of strings. `figure` records it as the
refusal of the whole run, "the figure extractor could not read: <paths>",
and exits 2. Any other reply that is not an array keeps the refusal
"is not a JSON array of proposals".

### A deliberate clear

`bc.py figure --clear-refusals` rewrites `figure-refusals.json` to `[]` and
records nothing. It prints nothing. `--clear-refusals` and `--proposals-file`
are mutually exclusive, and one of them is required. The clear follows the
same session rule as a run. A clear refused by the session check leaves the
file as it was, on purpose: a run always rewrites the file, because its
record names what happened, but a refused clear did nothing to report.

## Consequences

- An empty reply no longer reads as a case with no amounts. The handoff names
  each amount the extractor left out, so an automated run hands it to a
  person.
- The coach clears the refusals file only with `--clear-refusals`, in an
  interactive run, after the person has handled or set aside every refusal
  and every uncovered line `figure` printed.
- The handoff names a proposal that code refused by whichever of its label
  and its line exists, and drops the brackets when neither does.
- `figure` on `[]` now runs a check that reads `business-case.md` and the
  figures file. A case whose amounts are all recorded gets an empty file, as
  before.
