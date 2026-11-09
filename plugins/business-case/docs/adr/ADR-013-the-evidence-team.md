# ADR-013 — The evidence team

**Status:** Accepted · **Date:** 2026-11-03

## Context

A case is only as good as its evidence pages. Until v0.5.0 the coach found
that evidence alone, in the person's session, and a page made from a plugin's
output carried whatever grade the person gave it. Nothing in code tied the
grade to the sources behind the output, so a result that rested on a silent
default could be graded `primary`.

Part A of plan 4 gave six plugins one result file shape, with a source and a
method on every result (the plugin-result standard in `schemas/`).
Part B puts a team on top of it. The design is in
`docs/superpowers/specs/2026-10-31-business-case-plan-4-evidence-team-design.md`,
§5.

Three limits of Claude Code shape it:

- Claude Code removes `AskUserQuestion` from every sub-agent (ADR-001). Only
  the main session can ask the person anything.
- A sub-agent's `tools:` list cannot limit its Write to one folder, so a guard
  on a write has to be a plugin hook (ADR-006).
- A plugin command dispatched with the `Agent` tool ran in the background in
  every spike run, in the CLI and in Desktop, even when the prompt asked for
  the foreground.

## Decision

### The roles

The coach is the main session. It is the team lead and the only voice to the
person. It asks code for each brief, asks the cards, runs the plugin commands
and turns results into pages for the person to confirm. A separate
orchestrator sub-agent could not ask the person anything, so the coach is not
one.

The analysts are sub-agents, one file each: `agents/case-*-analyst.md`. Each
owns a set of rubric items, and each one's tools are `Read`, `Glob`, `Grep`,
`WebSearch`, `WebFetch` and `Write`. An analyst has no shell, no `Skill` and
no `Agent`, so it never runs a plugin. It plans which runs and cards its
items need, and later drafts results from what the runs wrote. The
independent review stays outside the team and reads no `team/` file.

### Briefs and the two reply kinds

Code writes every brief, `team/brief-NNN.txt`, with `bc.py team-brief`. The
coach dispatches an analyst with the `Agent` tool, `subagent_type`
`business-case:<name>`, and the brief's exact text as the whole prompt. The
dispatch guard refuses any other prompt, and a `subagent_type` that is not
the analyst type the brief names.

An analyst writes exactly one reply, of one of two reply kinds, the one its
brief names:

- a **plan**: the cards to ask, the commands to run, and any research it
  already has;
- **results**: a result file in the shared shape, with `plugin` set to
  `business-case`, citing each plugin result it rests on by path and result
  `id`.

The coach runs `bc.py team-reply --check` before it reads a reply. When the
check passes, it writes `reply-NNN.check.json` with the sha256 of the reply
and of every file the reply cites. The analyst computes no digest: it copies
its brief's `sha256:` line into the reply's `brief_sha256`, which binds the
reply to its brief (ADR-006).

### The card record

`bc.py team-answers` keeps the card record, `team/cards-NNN.json`: every card
of every merged plan, keyed `<brief NNN>:<id>`, with its round and its
answer. Two plans can both use the id `c1`, and their keys still differ.
Code makes four more kinds of card itself, keyed `code:<n>`:

- a conflict card, when two cards set one input to different values;
- a case card, for a result file that names no case, which is usually a
  person's own run;
- a gap card, for an upstream item that is not settled;
- a rerun card, for a command that already has a result.

The same `team-answers` call writes `answers-NNN.json` in the shared standard's answers shape. A value
the person picked is never replaced by a recommended one.

### The round cap

Each item gets at most two plan rounds; that is the round cap. Code counts
them from the plan briefs on disk, and a cancelled or expired plan brief
counts. After the cap, a card the person skipped takes its recommended option;
a card that is hard to undo is asked once more; a conflict card, or a card
answered in free text, stays open until the person picks an option. Each round
is a new brief and a fresh analyst. The coach never resumes an analyst with
`SendMessage`.

### The budget

Code holds the team's budget, as it holds the independent review's:

- `RUNS_PER_ITEM` is 4: the briefs that may name one item, over the life of
  the case.
- `RUNS_PER_SESSION` is 24: the briefs one case session may write.
- `RUNNING_MAX` is 3: the briefs that may be open at once.

A brief is open until it is answered, cancelled or expired. A cancelled or
expired brief frees its place among the open ones and still counts against the
other two. The expiry runs from the time code wrote the brief, and it is 60
minutes (`BRIEF_EXPIRY_MINUTES`). The 2026-11-03 probe measured three plan
rounds of 30 to 34 seconds, the fastest case: a plan round with no run
possible, on haiku. The 2026-11-04 live run measured all twelve analyst
rounds, plan and results, at 12 to 41 seconds. 60 minutes is a margin for a
person who answers late. A long expiry costs only a held running place, which
`team-brief --cancel` frees.

### The analyst write allow

Every file-tool write into a case folder is refused (ADR-006), with one
exception for the judge. The second is the analyst write allow. An analyst
may `Write` once to its own `team/reply-NNN.json`, under the rules ADR-006
lists. Its brief must be open, and the reply must carry that brief's digest. A
`PostToolUse` receipt records the reply's bytes, and the check refuses a
reply that has no receipt.

### The grade ceiling

`bc.py evidence --from-result` builds a page from a result, and code works
out the grade ceiling: the most the page can be graded. A result is as strong
as its weakest source. A `default`, `model` or `person` source allows at
most `estimated`, a `published` source `secondary`, and only a
`customer_data` source `primary`. The map can set a lower
ceiling for a command and kind, and a result that cites another result is
held to that result's ceiling too. A grade above the ceiling is refused,
never lowered.

The page records the result reference: the file's path and sha256. For a
page from a reply, code checks each file the reply cites against the sha256
in the reply's check record. At write time it hashes every file it read
again, and refuses the page when one has changed since it built the page.

### Four decisions made while writing the analysts

Writing the analysts showed four gaps in the design. Each was settled as
follows. Tier-2 output, below, is what a skill outside the plugin map writes
when the coach runs it.

**The order of work.** The map's order of work now holds two more steps:
packages come after willingness to pay, and price changes come after the
launch price. A package comes from the same pricing run as the launch price,
and that run reads the willingness-to-pay result. A price change assumes a
launch price exists.

**Two commands are the person's runs.** The map marks
`product-finance:cost-coverage` and `value-ip:analyze` `coach_runs: false`.
An analyst may still name one in its plan. Code then records an open entry
for the person and prints the line the coach shows them. The result comes
back through a case card. `value-ip:analyze` raised 52 permission dialogs in
one test. Cost coverage reads pricing's diagnosis and cost readout, and both
are tier-2 output, which never reaches a plan brief. The person runs cost
coverage once both pricing files exist.

**A shared input has one rule.** Some inputs stop a run when they have no
value: a halt input. A halt input that two analysts can card is carded by
both, identically, from a named case text. The recommended value quotes that
text word for word: for `market` of `competitive-intelligence:discover`, which
the baseline and competition analysts both card, it is the first sentence the
case gives under "What we offer". Two identical
cards make no conflict card. A shared input that is not a halt input is
carded by its lead analyst only, and the other analysts leave it alone.

**An analyst's own finding has a cap.** A result in an analyst's reply that
cites no plugin result is off the map, and its page is capped at
`secondary`, whatever source types the result claims. Its source types are
the analyst's own word. A `primary` grade needs a cited plugin result or the
person's own page. A cited result whose command is not on the map, or does not
belong to the file's plugin, caps the page at `estimated`. No version or
ceiling is known for it.

## Alternatives considered

- **A team-lead sub-agent.** Rejected. It could not ask the person anything,
  and every card needs an answer from the person.
- **Analysts that run plugins.** Rejected. A plugin run inside an analyst
  sits one layer deeper, and its dialogs come from an agent the person did
  not start. The coach runs every command, one at a time, and waits for each
  to end.
- **A `SendMessage` resume for the second round.** Rejected. The dispatch
  guard does not see a resume, so the budget and the brief check would not
  hold for it.
- **Cost coverage in the finance analyst's second plan round.** Rejected.
  Pricing's two files are tier-2 output, and no plan brief names tier-2
  output, in either round.

## Consequences

- The person approves more dialogs: each analyst asks a few times to read,
  search and write, on top of each plugin run. The coach warns before the
  first dispatch. Since ADR-016, a hook approves the reads, the script calls
  and the writes of a plugin run in a build session: a live test of the 5 runner
  plugins had no question for these steps. A run still asks for each web
  search (7 times in one test of `competitive-intelligence:discover`).
- A page built from a result can no longer be graded above what its sources
  support. A genuine `primary` finding of an analyst is graded `secondary`
  until a plugin run or the person's own page backs it.
- The person runs cost coverage and the value-ip analysis themselves. When
  they do not, the team names the gap.
- Two analysts can show the person the same card about a halt input. If the
  person picks different options on the two, code makes a conflict card and
  the person settles it.
- All team state is files under `team/`. A session that stops can be picked
  up from them.
- On Windows the team lock, `team/.lock`, which every team call that writes
  holds, does nothing, because Python has no `fcntl` there, so two team
  calls at once can still lose a write.
