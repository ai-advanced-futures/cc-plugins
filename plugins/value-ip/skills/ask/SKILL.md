---
description: Answers a question about the value and IP findings of this repository from the value-ip graph - which differentiators survived the debate, which frameworks support each, what the overall verdict and mean score were, which results a run did not produce - and follows links into the other graphs. Use for "/value-ip:ask" and "which differentiators survived".
argument-hint: "<question>"
allowed-tools: Read, Skill(knowledge:ask), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vip_graph.py --root * results *), Bash(git rev-parse *)
---

# Ask the value and IP findings

The question is: **$ARGUMENTS**

Write no page, because the pages come from the result files of `/value-ip:analyze` through `/value-ip:learn`, and the person confirms them there. Answer from the graphs only.

## Normal questions

Load `knowledge:ask` with the question unchanged before reading any page. This is the normal evidence reader. It searches the local registered graphs, with no caller-selected nodes or filters, and needs knowledge 2.0.0 or later. A graph name in the question does not restrict the search, so use only the pages of the graph `value-ip` as value and IP evidence. When the graph is unregistered or remote, read its local source files when they exist and report the coverage gap.

## Exact checks

For the latest run, the list of differentiators of a run, or the verdict of a run, use the exact check and not the ranked search, because a ranked search can leave out a page.

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`. Quote a value with single quotes, and write each `'` in it as `'\''`.

`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vip_graph.py --root '<git root>' results` prints the latest run as JSON: the Run page, and its differentiators, verdicts and gaps with their status and their `verified` entries. Add `--run '<RUN ID, run_id, or alias>'` for another run. When the question names a subject, read the Run pages of the folder `runs/` of the bundle first, and pick the run whose `subject` matches. When two runs match, say so and ask which one.

| Question | Exact check |
|---|---|
| Which differentiators survived? | The `differentiators` list of `results`. A run with none has a Gap page that says so: report that gap. |
| What was the verdict? | The `verdicts` list: `recommendation`, `mean_score` and `powers`. |
| Which frameworks support a differentiator? | The `method` field of its page. |
| What did the run not produce? | The `gaps` list, with each `why`. |
| Did a person confirm it? | The `status` and the `verified` list of the page. |

## Answer

Cite each page with its graph and path, for example `(value-ip:/differentiators/DIFF-01.md)`. Write `(draft)` after each draft source. Each page is the judgement of the model, so write "the debate judged". The words "validated" and "proven" claim more than a model judgement gives. Say when a page `rests_on_default`, because then an auto-detected artifact stands behind it. State a missing run, a gap or a draft status instead of filling it in.
