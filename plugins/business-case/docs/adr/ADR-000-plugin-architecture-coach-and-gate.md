# ADR-000 — Plugin architecture: a coach and a gate

**Status:** Accepted · **Date:** 2026-10-27

Start here. This page is the overview of the plugin. ADR-001 to ADR-016 each
record one decision in full.

## Context

A person brings the business case they have. It is usually thin. They need a
case that a funder can trust and that a PRD can be written from. One person
plays two parts: the proposer who builds the case, and the funder who decides
on it. A tool that helps the proposer must not also be the voice the funder
trusts.

The design is in `docs/superpowers/specs/2026-10-27-business-case-thin-slice-design.md`.
It is the first build of a larger plan, the product lifecycle system map
(`docs/superpowers/specs/2026-10-26-product-lifecycle-system-map-design.md`).

## Decision

### Coach and gate, with a wall between them

The coach runs inline in the user's own session and helps the proposer. The
judge is the gate for the funder. The coach and the judge never share a
context. The judge is given only a code-written brief, which names its
input files. Claude Code cannot stop a sub-agent from reading other files, so
a report counts only while its manifest equals the current file set (ADR-002,
spec §6). The judge writes only its own reply (ADR-006).

### The sub-agents

The judge is the only sub-agent that judges. From v0.3.0 the figure extractor
is a second sub-agent: it proposes figures from the case and judges nothing
(ADR-009). From v0.5.0 the analysts of the evidence team are sub-agents too.
Each plans or drafts for its own items and writes one reply (ADR-013). Claude
Code removes `AskUserQuestion` from a sub-agent, and every decision needs an
answer from a person. So the coach and every funder decision stay inline
(ADR-001).

### The CLI is the coach's only writer

`lib/bc.py` is the one way the prose layer touches case files,
`business-case.md` included: `bc.py change` replaces one section and logs the
change in the same call. Three writers are not the CLI: the judge writes its
own reply, each analyst writes its own reply (ADR-013), and the `PostToolUse`
hook writes the receipts (ADR-006).

### The case directory

One case per directory, `business-cases/{slug}/`. Code refuses a case folder
whose resolved path is not `<anything>/business-cases/<slug>`.

| File | What it holds |
|---|---|
| `case.json` | slug, offering, market, rubric version, session budget, sessions |
| `scope.json` | market, rubric version and applicable item IDs; written by `init` and by `move-rubric` |
| `rubric.json` | a copy of the pinned rubric version |
| `inputs/proposal.original`, `inputs/strategy.original` | each input as given, never edited |
| `inputs/proposal.text.md`, `inputs/strategy.text.md` | only when that original is not UTF-8: the session's text extraction |
| `changelog.jsonl` | one entry per change to the case; append-only |
| `business-case.md` | the case; created by `init` from the template, then written only through `bc.py change` |
| `evidence/EV-NNN.json` | evidence pages |
| `register.jsonl` | the strategic decisions register: entries and the proposer's confirmations; append-only, hash-chained (ADR-007) |
| `conditions.jsonl` | the conditions list: conditions and the proposer's marks; append-only, hash-chained (ADR-007) |
| `notes.jsonl` | claims that fail the four-part test; append-only, hash-chained (ADR-007) |
| `strategy-view.md` | the strategy view, projected from the register by code; never edited, never a judge input |
| `ledger.json` | the item ledger |
| `decisions.jsonl` | the decision record; append-only; created empty by `init` |
| `judge/brief-NNN.txt` | the brief code writes for one judge run; names the reply path |
| `judge/reply-NNN.json` | the judge's reply, written by the judge only |
| `judge/reply-NNN.receipt.json` | the receipt the hook writes after the judge's Write completed |
| `judge/report-NNN.json` | the validated report, `"written_by": "judge"` or `"coach-copy"` |
| `figures.jsonl` | the financial figures file: figures and the proposer's confirmations; append-only, hash-chained (ADR-009) |
| `figure-refusals.json` | the refused proposals of the latest `bc.py figure` run, or the refusal of the whole run, and the amounts it left uncovered; replaced each run; never a judge input (ADR-012) |
| `finance.json` | the numbers and the verdict ceiling; written only by `bc.py brief`; a judge input, never an input to the arithmetic (ADR-010) |
| `finance-view.md` | the funder's view of the numbers, in plain words; written by code, never a judge input |
| `funding/finance-report-NNN.json` | a funding decision's copy of the `finance.json` its report read; never rewritten (ADR-010) |
| `business-case-handoff.json` | what a run hands to the person and to a later session |

### The guard hooks

Three guard hooks share one handler, `hooks-handlers/judge_guard.py`. `hooks/hooks.json` also holds the 4 hooks of the runner guard, `hooks-handlers/runner_guard.py` (ADR-016), and the brain hook of the case graph (ADR-015). The 3 hooks of the judge guard are:

- a `PreToolUse` write guard on every file-writing tool (`Write`, `Edit`,
  `MultiEdit`, `NotebookEdit`). Code writes every file in a case folder, so the
  write guard refuses those tools anywhere in every case folder, for every
  caller. Two writes are allowed: the judge's own `judge/reply-NNN.json`,
  and an analyst's own `team/reply-NNN.json` (ADR-006);
- a `PreToolUse` dispatch guard on `Agent` (and `Task`). It refuses a
  dispatch of the judge or an analyst whose prompt is not exactly the text
  of an unanswered brief;
- a `PostToolUse` receipt on `Write`. It records the bytes of a completed
  reply Write by the judge or an analyst.

The hooks run in every session with the plugin enabled. The two `PreToolUse`
hooks need Claude Code 2.1.295 or later, for `"onFailure": "block"`. When
`python3` is missing, they block every file-tool write and every sub-agent dispatch in
that session (ADR-006).

### The proposer and funder role switch

In v1 one person does both parts and switches role on purpose. The coach says
the switch aloud. Every decision records its role, and code refuses a
decision made in the wrong role.

### The strategic decisions register and the strategy view

The strategic decisions register is the source of truth for strategy. A
strategy document is an input to a register, not a parallel copy. The strategy
view is a projection of the register: read-only and never edited by hand
(spec §5a). Both ship in Plan 2, in v0.2.0. Their files are hash-chained and
their status is derived (ADR-007).

### The rubric, the item ledger and the decision record

- The rubric is versioned. A case is pinned to the version it was opened
  with, through `rubric.json` and `scope.json`. v0.1.0 ships rubric `1.0.0`.
  v0.3.0 adds rubric `1.1.0` and the funder's move to it (ADR-011).
- The item ledger holds the coach's proposal for each item. It never holds a
  met. Only a current, judge-written report makes an item met.
- The decision record holds who decided what, in which role, with the reason
  in the person's own words. `lib/decision_record.py` is the only writer of
  decisions (ADR-004, ADR-005).

### Code decides

Code decides when the loop ends, assigns finding IDs (ADR-008), derives every
strategy status (ADR-007), and decides whether a report is current. From
Plan 3, code also does the arithmetic. The model does none of these.

### The five delivery plans

From spec §15. Each plan ships a new working version of the plugin.

- **Plan 1:** the thin slice. Files, the rubric, the item ledger, the
  decision record, the loop-end code, the judge's evidence and completeness
  jobs, and the scripted end-to-end test. **v0.1.0 is Plan 1.**
- **Plan 2:** the strategic decisions register, the conditions list, the
  strategy view, and the judge's whole-plan job. **v0.2.0 is Plan 2.**
- **Plan 3:** the financial figures file, the finance engine (the
  arithmetic, the grade rule for totals), the investment verdict, and rubric
  `1.1.0` with the move. **v0.3.0 is Plan 3.**
- **Plan 4:** the plugin map and the install check (ADR-014), and the
  evidence team (ADR-013). **v0.5.0 is Plan 4.**
- **Plan 5:** the live benchmark.

### Where the plugin sits in the product lifecycle system map

The plugin is projects 2–4 of the system map: the strategy builder, the
strategy judge and the decision record, shipped first as one plugin. The
map's amendment §11 records this.

§11 also records what the slice replaced:

- The register replaces the separate strategy-builder step.
- The coach is interactive, and the judge runs unattended. The figure
  extractor and the analysts are sub-agents too, and ask the person nothing.
- The change of the `product` plugin to read cases stays out of v1.

And what else §11 decides:

- No umbrella case. Nesting comes later and is not in v1: a parent case holds
  the shared parts, and each child case covers one offering.
- The business-case format is ours, written from scratch. lineos-sdlc's
  template is inspiration only. The PRD target is the `product` plugin (`/product:explore`).
- The user switches role between proposer and funder, and every decision
  records the role.

### The other decisions

| ADR | Decision |
|---|---|
| [ADR-001](ADR-001-the-coach-runs-inline-only-the-judge-is-a-sub-agent.md) | The coach runs inline; the sub-agents only read and reply |
| [ADR-002](ADR-002-code-writes-the-judge-brief-and-checks-the-manifest.md) | Code writes the judge brief and checks the manifest |
| [ADR-003](ADR-003-automated-mode-covers-intake-mapping-and-the-judge.md) | Automated mode covers intake, mapping and the judge |
| [ADR-004](ADR-004-the-decision-record-library-lives-in-the-plugin-for-v1.md) | The decision-record library lives in the plugin for v1 |
| [ADR-005](ADR-005-a-decision-cites-the-report-not-the-case.md) | A decision on a finding cites the report, not the case |
| [ADR-006](ADR-006-the-judge-writes-its-own-report.md) | The judge writes its own report; a coach copy cannot end the loop |
| [ADR-007](ADR-007-the-strategy-files-are-hash-chained-and-their-status-is-derived.md) | The strategy files are hash-chained and their status is derived |
| [ADR-008](ADR-008-finding-ids-and-the-whole-plan-findings.md) | Finding IDs and the whole-plan findings |
| [ADR-009](ADR-009-the-financial-figures-file.md) | The financial figures file |
| [ADR-010](ADR-010-the-finance-engine-and-the-verdict-ceiling.md) | The finance engine and the verdict ceiling |
| [ADR-011](ADR-011-per-version-rubrics-and-the-move.md) | Per-version rubrics and the move to a newer one |
| [ADR-012](ADR-012-the-figure-run-reports-what-it-left-uncovered.md) | The figure run reports what it left uncovered |
| [ADR-013](ADR-013-the-evidence-team.md) | The evidence team: analysts that plan and draft, and the grade ceiling for pages built from a result |
| [ADR-014](ADR-014-the-plugin-map-and-the-install-check.md) | The plugin map and the install check |
| [ADR-015](ADR-015-the-case-graph.md) | The case graph: the pages of a case, `publish`, and the read of the graphs of 2 other plugins |
| [ADR-016](ADR-016-the-runner-guard-allows-only-exact-calls.md) | The runner guard: a hook that allows only exact runner calls, and the temporary folder of a case |

## Consequences

- A new reader learns the parts from this page, and each part's reasons from
  its own ADR.
- The funder can trust a judge report because the coach cannot write it on
  the normal path. ADR-006 names the routes the hooks do not see.
- The plugin has a hard floor: Claude Code 2.1.295 and a working `python3`.
