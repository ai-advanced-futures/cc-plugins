# ADR-002 — Code writes the judge brief and checks the manifest

**Status:** Accepted · **Date:** 2026-10-27

## Context

The judge must see the case and its evidence, and nothing from the coaching
conversation (spec §6). If the coach wrote the judge's prompt, it could slant
the judge with one extra sentence. Claude Code cannot limit what a sub-agent
reads through its tool list. So the only way to know what the judge was
asked to read is to fix it in code and check it afterwards.

## Decision

### The brief is a fixed template

`lib/judge_brief.py` writes `judge/brief-NNN.txt` from one template and
nothing else:

- the first line, `business-case judge brief v1`;
- `case_dir`, the case folder;
- `reply_path`, the one file the judge writes, `judge/reply-NNN.json`;
- `manifest_digest`, the sha256 of the input lines below;
- one input line per judge input: its sha256, its length in bytes and its
  path in the case.

The coach dispatches the judge with the brief's text as the whole prompt and
adds nothing. The dispatch guard refuses any other prompt (ADR-006).

### The reply reaches code only as a file

The judge writes its reply to the `reply_path` its brief names. `bc.py
save-report` reads that file, validates it, and saves the report. ADR-006
records who may write that file and how code knows who did.

Validation checks, among other things, that the reply's `manifest_digest` is
this brief's, and that every input in the manifest is still current.

### Code assigns finding IDs

A finding ID is `F-` and the first 10 hex characters of
`sha256(job|target_kind|anchor)`. The item is not in the ID (ADR-008).
Code derives the anchor:

- for a missing item, the anchor is the item ID;
- for a claim, the judge gives a locator: a section key and a 1-based
  paragraph number. Code reads that paragraph from `business-case.md`. The
  anchor is the section key and the first 16 hex characters of the sha256 of
  the paragraph's whitespace-normalized text;
- for a whole-plan target, the anchor is its ref or category key, and a
  finding code adds also carries the state, such as `C-001|unsupported`
  (ADR-008).

The judge's wording is never hashed. A judge run that words the same claim
differently gets the same ID, so an earlier accept still covers it. Two
findings with the same ID in one reply are refused.

### The judge's inputs

The judge reads `business-case.md`, `rubric.json`, `scope.json`,
`evidence/*.json`, `decisions.jsonl`, `register.jsonl`, `conditions.jsonl`,
`notes.jsonl`, `figures.jsonl` and `finance.json`. These are
`paths.JUDGE_INPUT_GLOBS`. A strategy file that does not exist has no lines,
and the brief does not list it.

`figures.jsonl` is judged on its full digest, as the strategy files are: a
figure recorded or confirmed after the brief makes the report not current.
`bc.py brief` alone writes `finance.json`. It holds the decisions lock while
it writes `finance.json` and the brief, so both read one length of
`decisions.jsonl`. `finance.json` is never an input to the arithmetic (ADR-010). `save-report` and the
re-derive compute again from the files, with `decisions.jsonl` and
`figures.jsonl` cut at the lengths the brief's manifest recorded. A manifest
with no `figures.jsonl` line reads no figures.

The three strategy files are judged on their full digest; only
`decisions.jsonl` keeps the prefix rule. `bc.py brief` reads the three files
before `write_brief` counts a run. It refuses, and counts no run, when one
cannot be read or holds a line code ignores. This read is outside
`judge_brief`, so the strategy modules stay out of the hook's import closure.

`scope.json` tells the judge the market and the applicable items. `init`
writes it, and `move-rubric` rewrites it when the funder moves the case to a
newer rubric.

Left out, with the reason:

- `ledger.json` holds the coach's classification of each item. That is a
  proposal, and the judge must not be steered by it.
- `case.json` holds the sessions and their judge-run counts. Code changes it
  each time it writes a brief.
- `inputs/` holds the originals as given. The judge judges the case as it is
  written now, in `business-case.md`.
- `changelog.jsonl` is the history of the coach's changes. It is part of the
  coaching, which the judge never sees.
- `strategy-view.md` is a view code writes from the register. The judge
  reads the register itself.

### The decision record is append-only

`init` creates `decisions.jsonl` empty, so it is in every manifest. A report
is current while the bytes the judge read are still the start of the file. A
decision recorded after the report answers that report, so it must not make
the report out of date. This amends spec §6; spec §14 records the change.

Every other input is current only while its digest matches exactly.

### The session budget

The budget is 5 judge runs per Claude Code session. `case.json` stores it as
`session_budget`. A session is keyed on the Claude Code session ID. A second
`bc.py session` call with a recorded ID resumes that session: it becomes the
case's current session again and keeps its judge-run count (ruling FR-I3).
Nothing resets a count, so the budget per session holds. Resuming a session
for another name, or in another mode, is refused. A person who returns to an
earlier conversation, or works the case in two windows, resumes the session
instead of spending runs on replies that cannot be saved.

A session started under an invented ID gets a fresh count but buys nothing:
`save-report` refuses a reply whose receipt's session ID, which the hook
takes from Claude Code, is not the case's current session. That refusal
starts `the judge's reply is from another session`. It names both sessions
and tells the coach to run `bc.py session` with its own session ID and save
again. It does not ask for a new judge run, because the reply may be good.

A judge run is counted when its brief is written, because the judge's cost is
spent whether or not its reply is accepted. So a crash between the count and
the write counts a run that has no brief. That is the safe side.

### The manifest is the guard on the judge's inputs

Claude Code cannot restrict a sub-agent's Read (spec §6). The judge could
open other files. The manifest check is the guard: a reply counts only for
the inputs its brief lists, at the digests the brief recorded.

### What the validator accepts

v0.1.0 accepted only the jobs `evidence` and `completeness`, and only the
finding targets `claim` and `missing_item`. Plan 2 adds the job
`whole_plan` and its targets `register_entry`, `condition`, `category`,
`note` and `plan` (ADR-008). Plan 3 adds the job `investment` and the
targets `amount` and `total`. Code alone adds a finding on an `amount` or a
`total`: one for each money amount that no confirmed figure covers, and one
for each total whose share from estimates is above the rubric's limit
(ADR-008). The validator refuses a reply that gives one, with an `amount` or
`total` target.
The reply also carries two keys on the investment, both or neither.
`investment_verdict` is `supported`, `undetermined` or `not_supported`. It is
at or below the ceiling that code computes again at save time, from the
case's files and from `decisions.jsonl` cut at the length the brief read.
Code never reads a stored ceiling. `verdict_rests_on` lists the reasons. Each
reason is a finding's number in the reply as sent, counted from 1, or the
anchor of a finding that code adds from the finances. A number that points at
a finding the save drops is refused. A verdict below the ceiling needs at
least one reason. At the ceiling, the verdict rests on the ceiling's own
reason. A reply with neither key reads as `undetermined` with no reasons. It
saves as v0.2.0 saved it, so a report saved before v0.3.0 keeps counting.
Every save path applies these checks: `save-report`, the coach copy, and the
re-derive that loop end runs on a saved report.

### The rubric is pinned per case

A case stays on the rubric version it was opened with, until the funder
moves it. v0.3.0 adds rubric `1.1.0` and the move to it; ADR-011 records
which met tests changed and how a move treats earlier decisions.

## Consequences

- The coach cannot add words to the judge's instructions on the normal path.
- An edit to `business-case.md` or a new evidence page after a report makes
  that report not current, and the loop does not end until the judge runs
  again.
- A decision does not make the report it answers out of date.
- A refused reply costs one judge run from the budget.
- The judge may read files outside the manifest. Nothing stops that. A reply
  still counts only against the inputs the brief named.
