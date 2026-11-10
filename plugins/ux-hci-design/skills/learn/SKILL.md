---
description: Saves knowledge into the ux-hci-design graph - it confirms the pages of a run after the person accepts them, or it saves a fact that the person gives - through ux_graph.py, then runs both checks and reports. Use for "/ux-hci-design:learn" and the "Learn these results?" offer of the ux-design skill.
argument-hint: "[RUN ID | a fact]"
allowed-tools: Read, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(gh api user --jq .login)
---

# Learn into the ux-hci-design graph

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`. Also, do not add an `echo` of the exit code, because the Bash tool shows the exit code of a command that fails.
`U` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ux_graph.py --root <git root>`.

## Step 0: the guard

Run `$U resolve RUN-01`. When it exits 2, stop with: "This repository has no ux-hci-design graph. Run `/ux-hci-design:setup` first."

## Step 1: the person and the time

Run `gh api user --jq .login`. The output is `<login>`. When the command fails, ask the person for the login. The save code writes the time.

## Step 2: a run

When the argument is a RUN ID:

1. Run `$U verify-run <argument> --by "human:<login>"`. It gives the run page and each page of the run `status: stable` and one more `verified` entry, in one process. A second confirmation adds an entry. It does not replace the first.
2. When the command exits 1 or 2, stop and show its output. Do not report success, because no page is confirmed.

## Step 3: a fact

When the argument is a fact:

1. For each name in the fact (a persona, a screen), run `$U resolve <name>`. A hit through `aliases` is the same page. Change that page, because a second page splits one thing in two.
2. A new page: `$U new <Type> --title "<title>" --description "<one line>" --set KEY=YAML`. A changed field: `$U set <ID> KEY=YAML`. A new link: `$U link <ID> <field> /<folder>/<ID>.md`. A page of each type except `Run` belongs to 1 run: add `--set run=[/runs/RUN-NN.md]`. With no run, `new` writes no page and exits 1.
3. Run `$U verify <ID> --by "human:<login>"` for each page that you made or changed, because the person gave the fact.

## Step 4: both checks

Call the `knowledge:checking` skill with the graph `ux-hci-design`. Never report success while it returns `CHECKS: FAILED`, because the person must see the failure.

## Step 5: report

Report each page that you made or changed, and each ERROR, WARN, and SKIP line of the checks.
