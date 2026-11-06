# ADR-007 — The strategy files are hash-chained and their status is derived

**Status:** Accepted · **Date:** 2026-10-28

## Context

Plan 2 adds three files to each case: `register.jsonl`, `conditions.jsonl` and
`notes.jsonl`. The register holds the strategic decisions. The conditions list
holds what must be true for a decision to work. The notes hold claims that
fail the four-part test for a register entry (spec §5a). The judge reads all
three.

Two risks follow. Someone could edit an earlier line with a shell command, and
change what the judge reads or what the proposer confirmed. And a stored
status field could be edited the same way. The files must show such an edit,
and no status may sit in a field that a session can change.

## Decision

### Three files, one chain

Each line is one JSON object. Its `prev` is the sha256 of every byte before
that line. For line 1 it is the sha256 of no bytes. `lib/chained_log.py` writes
and reads all three files. A reader refuses a file when a `prev` does not
match, when a line is not a JSON object, when a key repeats, or when the last
line has no newline.

The chain detects a change to any line that has a later line. The chain does
not detect a change to the last line, or a cut of whole trailing lines. A brief
records a digest of each judge input, so such a change made after a brief makes
that brief's report refused or stale. A change made before any brief leaves no
trace, and a shell edit can use this gap (ADR-006).

### One writer at a time

On macOS and Linux, `chained_log.append` reads, checks and writes under an
exclusive lock on the file, so two appends at once never share a `prev` or a
number. On Windows the appends are not locked, because `fcntl` does not exist
there, and two appends at once can share a `prev`. A record numbered from the
file's lines is built twice: once before the file is opened, so a refused
record leaves the file as it was, and once under the lock, from the lines it
follows. When only the second build refuses, the file this append created
may stay empty. An empty file reads as no lines. Its digest is new, so a saved
report reads as not current, and the person writes a new brief.

### Status comes from the lines

Status is derived from the lines that pass their write rules when a reader
replays them in file order, and it is never stored. The statuses of an entry
are `stated`, `stated (coach)`, `confirmed` and `superseded`. A condition adds
`unsupported`.

A line that breaks a rule does not count, and the reader names the reason.
`bc.py status` shows each reason. `bc.py brief` is refused while any such line
exists, and it counts no judge run. A forged line that keeps every rule still
counts. The chain shows order, not the writer. A shell edit can use this gap
too (ADR-006).

### Confirm and mark

Confirm and mark lines hold the person's answer verbatim, in the proposer role,
and they stay outside `decisions.jsonl`. They are the proposer's records, not
the funder's (spec §5a). A confirm line sits in the register file. A mark line
sits in the conditions file. Both need a named person. A line that names
`automated`, or any role but the proposer, does not count.

### Supersede rules

A changed choice is a new entry that names the entry it supersedes, with a
reason and a change source. An entry supersedes only an entry of its own
category. Only the newest entry in a chain can be superseded. A line that
names an entry already superseded is refused; it must name the entry that
replaced it. A condition is superseded the same way, with no category rule.

### Orphaned conditions

A live condition whose entry is superseded is orphaned. The `supports` field is
never moved to the successor. The coach records the condition again against the
successor, and so supersedes the orphaned one. A mark on an orphaned condition
is refused at write time.

### Coach entries

An entry with source `coach` has the status `stated (coach)`. A coach entry
fills a category only when a person confirms it. So a category the coach alone
filled stays absent.

### Automated limits

An automated session cannot confirm an entry, mark a condition, record source
`coach` or `user`, or supersede a confirmed entry. No person is present to
state, confirm or change a choice.

### The view

`strategy-view.md` is projected from the register by `bc.py view`, and it is
not a judge input. Nobody edits it. When a view write fails after a line was
appended, the line is recorded, and the message says: run `bc.py view`; do not
record again.

## Consequences

- A shell edit to an earlier line makes `status` exit 1 with a
  reason that names the file and the line, and makes `brief` refuse.
- The residual is the last line and the trailing lines. A person who must
  prove a file untouched compares it with the report's digest.
- No session can edit its way to a status. It can only append a line that
  passes the rules.
- Every new strategy file needs its own entry in `JUDGE_INPUT_GLOBS`, so a
  change to it makes the saved report stale (ADR-002).
