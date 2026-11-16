---
description: Answers a question about the market discovery runs from the jtbd graph - which outcomes are most underserved, which segment values an outcome most, what a segment will pay, how a job changed between runs, and which result rests on a default. Use for "/jtbd-market-discovery:ask" and "which needs are underserved".
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Skill(knowledge:ask), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py *), Bash(git rev-parse *)
---

# Ask the jtbd graph

The question is: **$ARGUMENTS**

Never write a page, because the person confirms a run through
`jtbd-market-discovery:learn`. Answer from the graph only.

## Normal questions

Load `knowledge:ask` with the question unchanged before page reads, root commands,
or plugin probes. Requires knowledge 2.0.0 or later. This is the normal evidence reader.
The graph name is `jtbd`, not the plugin name. The reader searches local registered
graphs, with no caller-selected nodes or filters. Graph words in a question do not
restrict search. Keep only evidence from `jtbd`; check the requested run and segment
in the source before answering. For an unregistered or remote graph, read local source
files when available and report the coverage gap.

## Exact checks

For latest scores, segment comparisons, willingness to pay, run comparisons, and results
that rest on defaults, use the matching query below instead of ranked search. Otherwise
run a check only when the returned evidence needs it.

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When it fails,
stop with: "This is not a git repository." Use the literal root path in commands.
Write each path in single quotes, and write each `'` in a path as `'\''`.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`.
Also, do not add an `echo` of the exit code, because the Bash tool shows a failed exit code.

| Question | Exact check |
|---|---|
| Which outcomes are most underserved? | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' results --latest`. Keep `opportunity_score` results and read the Outcome source named by each `detail` path. |
| Which segment values outcome X most? | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' pages Segment --outcome '<X>'`. The query keeps Segment pages with X in `top_outcomes`. Compare recorded values for that outcome in the returned sources; segment size is not an outcome valuation. If no comparable values are recorded, say so. |
| What will segment S pay? | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' pages WtpValidation --segment '<S>'`. The query keeps only WtpValidation pages whose `segment` targets S. Check `run`, units, sample size, confidence, and verdict before using a value. |
| How did job J change between runs? | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' pages Run`. Keep runs with the same `subject`, then `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' pages Job --run '<RUN ID>'` for each selected run. Name the runs and their dates. |
| Which result rests on a default? | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' results --latest`. Keep each entry with `rests_on_default: true` and report its `defaults`. |

Add `--run '<RUN ID>'` to the typed page queries when the question names a run. For
`results --latest`, add the supported `--command` or `--case` filter when the question
selects one. Keep that selection, because a later unrelated run answers a different question. Resolve names
or aliases to IDs before exact queries; report ambiguous names instead of guessing.
These checks read source fields, not ignored generic neighbour hints.

## Answer

Cite each page with its graph and path, for example
`(jtbd:/outcomes/OUTCOME-03.md)`. Write `(draft)` after each draft source.
State when the recorded data cannot establish a ranking or current value.
When the graph has no run, say so and suggest `/jtbd-market-discovery:discover`.
