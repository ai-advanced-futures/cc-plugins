---
description: Answers a question about the market discovery runs from the jtbd graph - which outcomes are most underserved, which segment values an outcome most, what a segment will pay, how a job changed between runs, and which result rests on a default. Use for "/jtbd-market-discovery:ask" and "which needs are underserved".
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Agent, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(bash *probe-plugin.sh *)
---

# Ask the jtbd graph

The question is: **$ARGUMENTS**

Never write a page, because the person confirms a run through the
`jtbd-market-discovery:learn` skill. Answer from the graph only.

`J` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root "$(git rev-parse --show-toplevel)"`.
Find the root of the knowledge plugin with
`bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh knowledge scripts/knowledge.py`.
It prints the root. `K` is the file `knowledge.py` in the `scripts` folder of that root,
started with `uv run` and the option `--root "$(git rev-parse --show-toplevel)"`.
When the probe exits 1, stop with: "jtbd-market-discovery:ask needs the
knowledge plugin. Install it: claude plugin install knowledge@cc-plugins."

## Step 1: the shortcuts

Use the first shortcut that fits the question. Each one gives start nodes.

| Question | Shortcut |
|---|---|
| Which outcomes are most underserved? | `$J results --latest`. Keep the `opportunity_score` results, and follow their `about` links to the Outcome pages. |
| Which segment values outcome X most? | `$K neighbors jtbd:/outcomes/<X>.md`. Keep the `in` rows of type Segment. |
| What will segment S pay? | `$K neighbors jtbd:/segments/<S>.md`. Keep the `in` rows of type WtpValidation. |
| How did job J change between runs? | `$J pages Run`. Keep the Run pages with the same `subject`, then read the Job page of each. |
| Which result rests on a default? | `$J results --latest`. Keep each entry with `rests_on_default: true`. |

## Step 2: the generic procedure

Load the `knowledge:ask` skill. Give it the question and the start nodes of
Step 1 (or `jtbd:/index.md` when no shortcut fits). It walks the graph one
step at a time.

## Step 3: answer

Cite each page with its graph and path, for example
`(jtbd:/outcomes/OUTCOME-03.md)`. Write `(draft)` after each draft page.
When the graph has no run, say so, and tell the person to run
`/jtbd-market-discovery:discover`.
