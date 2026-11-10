---
description: Answers a question about the UX design of the product from the ux-hci-design graph - which personas the product has and on which findings, which screens, state rules and interaction rules the design has, what the evaluation of a screen found - and follows links into the other graphs. Use for "/ux-hci-design:ask" and "which personas does the product have".
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Agent, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh *)
---

# Ask the UX design

The question is: **$ARGUMENTS**

Never write a page, because the person makes each change through the `ux-hci-design:learn` skill or a run. Answer from the graphs only.

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`. Also, do not add an `echo` of the exit code, because the Bash tool shows the exit code of a command that fails.
`U` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ux_graph.py --root <git root>`.
`K` is `uv run <knowledge plugin>/scripts/knowledge.py --root <git root>`.
Find the knowledge plugin with
`bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh knowledge scripts/knowledge.py`.
When the probe exits 1, stop with: "ux-hci-design:ask needs the knowledge plugin. Install it: claude plugin install knowledge@cc-plugins."

## Step 1: the shortcuts

Use the first shortcut that fits the question. Each one gives start nodes.

| Question | Shortcut |
|---|---|
| Which personas does the product have, and on which findings? | `$U pages Persona`. Follow the `findings` links. |
| Which screens, state rules and interaction rules does the design have? | `$U pages Screen`, `$U pages StateRule`, `$U pages InteractionRule`. |
| What did the evaluation of screen X find? | `$K neighbors ux-hci-design:/screens/<ID>.md`. Keep the `in` rows of type Evaluation and EvalFinding. |
| Which journey does flow X belong to? | `$U pages Diagram`. Keep the page of X and follow its `journey` link. |
| What does the PRD need from the behavior results? | `$U behavior`. |
| What did a run say, as the file it made? | `$U view <RUN ID> <file name>`. |

## Step 2: the generic procedure

Load the `knowledge:ask` skill. Give it the question and the start nodes of Step 1 (or `ux-hci-design:/index.md` when no shortcut fits). It walks the graphs one step at a time, also into the other graphs.

## Step 3: answer

Cite each page with its graph and path, for example `(ux-hci-design:/personas/PERSONA-03.md)`. Write `(draft)` after each page with `status: draft`, because the person has not confirmed it.
