# ADR-015 — The case graph

**Status:** Accepted · **Date:** 2026-11-09

## Context

A case lives in its case folder, `business-cases/<slug>/`. Code writes each
file of it, a hash chain protects the append-only files, and the independent
review reads only these files (ADR-002, ADR-006, ADR-007). A later session
can continue a case from the folder. But a person or an agent that asks
"what does the price part of this case say, and where does it come from"
must read many JSON files, and no other plugin can link to a part of a case.

The marketplace has a standard for this: a brain, a knowledge graph of
Markdown pages that the `knowledge` plugin reads. `jtbd-market-discovery`
and `competitive-intelligence` write their results as such graphs from
versions 1.9.2 and 1.10.8. Before, the evidence team read the result file of
each of their runs from `.<plugin>/results/` (ADR-013, ADR-014).

This record states 5 decisions of version 0.9.0.

## Decision

### The case folder is the record, and the pages are a copy

The case folder stays the only record of a case. `bc.py` stays its only
writer, and the independent review reads only the case folder. The graph
`business-case`, in `docs/business-case/`, holds a copy of each case as
pages: 1 `Case` page, 1 `Run` page for each session, 1 `Part` page for each
section, and 1 page for each evidence page, decision, strategy entry,
condition, note, figure, set of numbers and saved review. The pages are for
a reader. No step of the coach and no check of `bc.py` reads a page.

A value of a case changes only in the case folder. The `learn` skill writes
no value of a case page. It confirms the pages of a run (`verify-case
--run`), and it can add a note of the person below the text of the `Case`
page.

### `publish` writes the pages, at the end of each run

`bc_graph.py publish --case <case folder>` reads the case folder through the
read functions of `lib/` and writes the pages. The coach runs it after each
of its 3 `handoff` calls: the end of an automated run, the stop on the
budget, and the end of an interactive run. So the `Case` page holds the
status of the handoff.

`publish` works on a copy of the bundle, runs `regen` and the brain check on
the copy, and moves the pages in only when the check finds no error. It
holds a lock on the manifest while it writes. It finds a page by its alias
and writes only a page whose value changed, so a second `publish` writes
nothing. A new page and a changed page get `status: draft`. `publish` keeps
the note of a person on a `Case` page: each paragraph after the first one is
the text of the person, and it is not a difference.

When `publish` fails, the coach shows `GRAPH: FAILED <exit code> <first
error line>` and ends the run as usual. The case folder is complete, so no
record is lost, and the next run writes the pages.

Only an interactive run that ends with the funding step asks "Learn these
results?". An automated run and a stop on the budget ask nothing, and their
pages stay `draft`.

No agent and no skill writes a page with a file tool. The judge guard does
not change: the save script is a process, not a file tool.

### The save code is a separate script

`scripts/bc_graph.py` and `scripts/bclib/` are the save code. They need
Python 3.11, `pyyaml` and `jsonschema`, and `uv run` gives them from the
PEP 723 block of the script. `lib/` and the judge guard stay on the standard
library and Python 3.9 (ADR-006): `lib/` never imports `bclib`, and the
import closure of the guard does not reach the graph code. `bclib` imports
the read functions of `lib/`, so the 2 sides read a case file in 1 way.

A PostToolUse hook, `hooks/brain-hook.sh`, runs `regen`, the brain check and
the general check of the `knowledge` plugin after a write to the bundle. It
is a byte copy of the hook of the other brains. It blocks no write. It runs
only after a command that has the path of `bc_graph.py` outside quotes, so a
`bc.py` call of the coach does not start it. This hook is the fourth entry of
`hooks/hooks.json`: it is not a guard, and the 3 guard hooks of ADR-000 and
ADR-006 stay as they are.

At the end of an interactive run, the coach loads the skill `business-case:learn`
with the `Skill` tool, and `build.md` grants `Skill(business-case:learn)` for it.
This adds one skill to the routes of ADR-001, which names it.

### `team-run` reads a run of a graph plugin from its graph

For a command of a plugin that has a `graph` key in the plugin map
(`jtbd-market-discovery`, `competitive-intelligence`), `team-run --done` and
`team-run --status` do not look for a result file. `lib/brain_read.py` finds
the save script of the plugin with `scripts/probe-plugin.sh`, and runs its
read operations as a process: `pages Run`, `results --run-id <run_id> --case
<case folder>`, and `pages Result --run <Run page>`. The printed document
has the shape of a result file, and the same checker reads it.

There is no fallback to the result folder of the plugin. When the plugin,
the graph or the run is not found, or the document fails the checker,
`--done` records the run as a gap, and the reason names the graph and the
first line of the error. `--status` leaves the run open. 2 `Run` pages with
1 `run_id` and case refuse the run. The `min_version` of the 2 plugins in
the map is the version that first writes the graph from a run of the coach.

The other plugins of the map have no graph yet. For them, the search for a
result file by its `run_id` does not change.

### The case keeps a snapshot of each run that it uses

`brain_read` writes the printed document of a run to
`team/upstream/<name>` of the case, where `<name>` is the name that the
result standard gives a result file. The run entry of `team/runs.json` gets
this path as `result_file`, with 2 new fields: `graph_run`, the `Run` page
of the run, and `graph_results`, the `Result` page of each entry.

The snapshot is written 1 time. A later read finds the file and does not
write it again. The reason: an evidence page pins the sha256 of the file it
came from, and a funding decision pins the files it cites (ADR-005). A page
of another graph can change after the grade, because a person can edit it or
remove it. So the case must keep the bytes that the person graded.

A cite of an entry names a `Result` page. `brain_read` writes it as the
snapshot path of the run of that page, and it reads that run in the same way
when the case has no snapshot of it. So the walk of the cites reads
snapshots only.

The analysts have no shell, so they cannot read a graph. A results brief
gives an analyst the path of the snapshot, and the analyst reads it with the
Read tool. The cite check lists the snapshots of the case, and it does not
list the result folder of a plugin that has a graph.

`publish` takes the `Result` page of an evidence page from `graph_results`,
and writes it as the link `source_results` of the `Evidence` page. So a part
comes to its source in 2 steps: `Part`, `Evidence`, `Result`. The brain
check compares the value of the `Result` page with the value in the
snapshot, and gives the warning `BC-upstream` when they differ.

## Consequences

- A case needs `uv` for the graph, as it does for `bc.py`. With no `uv`, the
  hook uses `python3`, which then needs Python 3.11, `pyyaml` and
  `jsonschema`.
- The graph needs the `knowledge` plugin for the general check and for the
  `ask` skill. The plugin manifest names it as a dependency.
- The pages hold what the case folder holds: the text of each section, the
  name that the person gave, the reasons, the money figures and the reviews.
  When git ignores the case folder and does not ignore the bundle, `publish`
  writes no page and prints a `PRIVATE:` line.
- A run of `jtbd-market-discovery` or `competitive-intelligence` below the
  `min_version` of the map wrote no graph, so the case cannot use it. Code
  already refuses a result of a version below `min_version` (ADR-014).
- The runners of the 2 plugins still write a result file before they write
  their pages. The command keeps the write grant for that file. business-case
  does not read the file.
- The case keeps a copy of values of another graph, in the snapshots. This
  is the 1 place where it does. The `BC-upstream` warning shows a copy that
  no longer agrees with its source.

## Alternatives rejected

- **The graph as the record, with no case folder.** The hash chain, the
  receipts and the manifest of the independent review are rules on files
  that only code writes. A page can be edited by hand, so a verdict could
  rest on a changed page.
- **A new read of the graph each time a value is needed.** The bytes that a
  person graded could change between 2 reads, and a decision could cite a
  value that no file holds.
- **A fallback to the result file.** 2 sources for 1 run can disagree, and
  the case would not say which one it used.
- **The graph code inside `lib/`.** The judge guard runs on the `python3` of
  the PATH with the standard library. A package in its import closure would
  block each write of a session that has no such package.
