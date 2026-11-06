# ADR-003 — Automated mode covers intake, mapping and the judge

**Status:** Accepted · **Date:** 2026-10-27 · **Amended:** 2026-10-29 (v0.3.0, the financial figures; v0.3.1, a review that read no `finance.json`); 2026-10-30 (v0.4.0, the amounts a figure run left uncovered; a change after funding)

## Context

A run can have no person. This plugin's whole value is that a person decides each gap and the
funding, in their own words. A run with no person can do the mechanical
parts. It cannot decide anything (spec §10).

## Decision

Automated mode covers three steps: `intake`, `mapping` and `judge`. It records
no decision. It ends with a handoff that names the open items, and then the
line `DONE: business-case`.

The run starts from the arguments of the command, not from a caller:
`/business-case:build <proposal> --automated --offering <name> --market <market>
[--strategy <path>]`. When an argument is absent, the coach prints
`FAILED: business-case — <cause>` and makes no case.

An automated session has no person, so code enforces the rule, not the
prompt:

- `bc.py session --automated` records no name, and code refuses a name for an
  automated session.
- `bc.py decide` and `bc.py evidence` need the session's person, so code
  refuses both in an automated session.
- `bc.py change` records `accepted_by: "automated"` in the change log.

In intake, an automated run records a strategy claim as a `register` entry
with source `strategy` only when the strategy names the alternative it rejects; any other claim goes to `note` with failed test 2.
It records conditions and notes with source `strategy`, never uses source `coach` or `user`, never runs `mark` and never supersedes an entry, because no person is present.

In mapping, an automated run also extracts the financial figures: it
dispatches the figure extractor, records each proposal that passes the checks
as `stated` with `bc.py figure`, and runs `bc.py compute`, but it never
confirms a figure. Code enforces this: a confirmation needs a named person,
and an automated session records only figures with source `extractor` and
never supersedes a confirmed one (ADR-009). The run never proposes or
approves an estimate or an exclusion, and never moves the rubric, because
each of those is a decision. A figure that waits for a person does not
count, so the verdict stays below "supported".

The handoff's `problems` names each proposal that the latest `figure` run
refused, or the refusal of the whole run, and the amounts it left uncovered,
read from `figure-refusals.json` (ADR-012). It also names each finding that a
review's `not_supported` verdict below the ceiling rests on, while no
decision answers it (ADR-010). An automated run changes no figure to answer
such a finding.

An automated run on a case that already exists keeps its work: when `ingest`
refuses because the proposal is already stored, the run transcribes each
section of `business-case.md` that still matched the template before it began,
and keeps each section that differed. It records only the strategy's claims
that `register.jsonl`, `conditions.jsonl` and `notes.jsonl` do not already
hold, then skips the rest of intake and goes straight to mapping.

In an automated run, a refused call that no step names is not run again:
the run carries on, and the handoff names what stays open, with
`needs_human` true. The stops below are the only refusals that end a run
with `FAILED`.

The handoff, `business-case-handoff.json`, lists each open item with its
state. Its `problems` also names a latest independent review that read no
`finance.json`, because a funding decision refuses such a review. It names
a funding decision that no longer matches the files it cites, in `problems`
and in `status`, so a change after funding reopens the handoff. The handoff
sets `needs_human` to true unless the loop is done and `problems` is empty.

An automated run prints `FAILED: business-case — <cause>` in place of the
DONE line, and stops, in three cases:

- It cannot create a case, because it has no proposal, offering or market, or
  cannot read the proposal. No case exists, so it writes no handoff.
- `bc.py init` is refused for a reason other than that the folder already
  holds a case. When the folder already holds a case, the run carries on with
  that case.
- `bc.py handoff` is refused.

## Consequences

- A run with no person (`claude -p`) can run intake, mapping and one judge pass,
  then hand the case to a person.
- An automated run never ends the loop with a funding decision, because the
  funding decision is a `decide` call.
- A person still has to open an interactive session to close the case.
- Automated mode cannot write evidence pages, so the case-text items stay open
  there until a person writes their evidence pages.

## Amendment: no analyst team in an automated run, and the field `evidence_needed`

An automated run starts no analyst team. Nobody is present to answer a
case card. So the run neither dispatches an analyst nor runs a `team-`
subcommand.

The handoff names who owns the work that is left. It gains the field
`evidence_needed`, and its `schema_version` goes from "1" to "2". The field
lists the case's applicable items that are still open, the same set as
`open_items`. An item that does not apply needs no evidence. Each entry holds `item_id`
and `owner`. The owner comes from the plugin map: an analyst's name, "coach", or "the
finance engine". A handoff whose loop status cannot be read holds null.
