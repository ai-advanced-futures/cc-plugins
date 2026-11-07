---
description: Answers a question about the competitors of a market from the competitive-intelligence graph - which competitors a market has, what a run found, which evidence supports a finding - and follows links into the other graphs. Use for "/competitive-intelligence:ask" and "who are the competitors of X".
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Agent, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh *)
---

# Ask the competitive intelligence

The question is: **$ARGUMENTS**

Never write a page, because the person makes each change through the
`competitive-intelligence:learn` skill or a run. Answer from the graphs only.

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`. Also, do not add an `echo` of the exit code, because the Bash tool shows the exit code of a command that fails.
`C` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root>`.
`K` is `uv run <knowledge plugin>/scripts/knowledge.py --root <git root>`.
Find the knowledge plugin with
`bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh knowledge scripts/knowledge.py`.
When the probe exits 1, stop with: "competitive-intelligence:ask needs the knowledge
plugin. Install it: claude plugin install knowledge@cc-plugins."

## Step 1: the shortcuts

Use the first shortcut that fits the question. Each one gives start nodes.

| Question | Shortcut |
|---|---|
| Which competitors does market X have? | `$C pages Competitor`. Keep each page whose `market` is the page of X. |
| What did the latest run find? | `$C results --latest`. |
| What does the evidence say about competitor X? | `$K neighbors competitive-intelligence:/competitors/<ID>.md`. Keep the `in` rows of type Finding. |
| What are the strengths and weaknesses of competitor X? | `$C pages SwotItem`. Keep each page whose `competitor` is the page of X. |
| What did a run say, as the file it made? | `$C view <RUN ID> <file name>`. |

## Step 2: the generic procedure

Load the `knowledge:ask` skill. Give it the question and the start nodes of
Step 1 (or `competitive-intelligence:/index.md` when no shortcut fits). It walks the
graphs one step at a time, also into the other graphs.

## Step 3: answer

Cite each page with its graph and path, for example
`(competitive-intelligence:/competitors/COMPETITOR-03.md)`. Write `(draft)` after each
page with `status: draft`, because the person has not confirmed it.
