---
description: Answers a question about a business case from the business-case graph - what a part of a case says, which evidence a part rests on, what the latest review found, and what the funder decided - and follows links into the jtbd and competitive-intelligence graphs. Use for "/business-case:ask" and "what does the case say about X".
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Skill, Bash(git rev-parse *), Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh *)
---

# Ask the business cases

The question is: **$ARGUMENTS**

Never write a page, because the pages of a case come from its case folder
through `/business-case:build`, and the person confirms them through the
`business-case:learn` skill. Answer from the graphs only.

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`.
Check that the knowledge plugin is installed with
`bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh knowledge scripts/knowledge.py`.
Give each start node to the `knowledge:ask` skill. It runs each `knowledge.py` command and
starts the `knowledge:neighbor-judge` agent under its own grant.
This skill grants no `knowledge.py` command, so Claude Code asks the person before such a
command runs here.
When the probe exits 1, stop with: "business-case:ask needs the knowledge
plugin. Install it: claude plugin install knowledge@cc-plugins."

## Step 1: the shortcuts

Use the first shortcut that fits the question. Each one gives start nodes.
`<ID>` is the ID of the Case page. Read the bundle folder of the graph
`business-case` in `<git root>/.claude/knowledge.json`, then Read the files
`<bundle>/cases/CASE-*.md`. Each one has its `slug` and `offering`.

| Question | Shortcut |
|---|---|
| What does a part of a case say? | The start node is `business-case:/cases/<ID>.md`. Tell `knowledge:ask` to keep the `in` neighbors of type Part whose `part` is the part of the question: `job`, `market`, `competition`, `price`, `gtm`, `finance`, `baseline`, or `strategy`. |
| Which sources does a part rest on? | Read the `evidence` links of the Part page. Then read the `source_results` links of each Evidence page. They go into the `jtbd` and `competitive-intelligence` graphs. |
| What did the latest review find? | Read the `latest_review` link of the Case page. It is the Review page of the case with the highest `report`. Its LINKS block lists 1 `ItemVerdict` page for each item and 1 `Finding` page for each finding. |
| Which items are still open? | Read the LINKS block of the Case page: it lists 1 `OpenItem` page for each open item, with its `state`. |
| What did the funder decide? | Read the `funding_decision` link of the Case page. |

## Step 2: the generic procedure

Load the `knowledge:ask` skill. Give it the question and the start nodes of
Step 1 (or `business-case:/index.md` when no shortcut fits). It walks the
graphs one step at a time, and it follows a `source_results` link into the
jtbd or the competitive-intelligence graph.

## Step 3: answer

Cite each page with its graph and path, for example
`(business-case:/parts/PART-07.md)`. Write `(draft)` after each page with
`status: draft`, because the person has not confirmed it.
