---
description: Saves knowledge into the competitive-intelligence graph - it confirms the pages of a run after the person accepts them, or it saves a fact that the person gives - through ci_graph.py, then runs both checks and reports. Use for "/competitive-intelligence:learn" and the "Learn these results?" offer of a competitive-intelligence skill.
argument-hint: "[RUN ID or session id | a fact]"
allowed-tools: Read, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(gh api user *)
---

# Learn into the competitive-intelligence graph

`C` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root "$(git rev-parse --show-toplevel)"`.

## Step 0: the guard

Run `$C resolve RUN-01`. When it exits 2, stop with: "This repository has no
competitive-intelligence graph. Run `/competitive-intelligence:setup` first."

## Step 1: the person and the time

Run `gh api user --jq .login`. The output is `<login>`. When the command fails,
ask the person for the login. The save code writes the time.

## Step 2: a run

When the argument is a RUN ID or a session id:

1. Run `$C verify-run <argument> --by "human:<login>"`. It takes a RUN ID or a session id. It gives the run page and each page of the run `status: stable` and one more `verified` entry, in one process. A second confirmation adds an entry. It does not replace the first.
2. When the command exits 1 or 2, stop and show its output. Do not report success, because no page is confirmed.

## Step 3: a fact

When the argument is a fact:

1. For each name in the fact (a competitor, a market, an offer), run `$C resolve <name>`. A hit through `aliases` is the same page. Change that page, because a second page splits one thing in two.
2. A new page: `$C new <Type> --title "<title>" --description "<one line>" --set KEY=YAML`. A changed field: `$C set <ID> KEY=YAML`. A new link: `$C link <ID> <field> /<folder>/<ID>.md`. A new Market, Competitor, Offer, or Source page needs no `run` link, because the check accepts a page that a person made. A page of each other type belongs to 1 run: add `--set run=[/runs/RUN-NN.md]`. With no run, `new` writes no page and exits 1.
3. Run `$C verify <ID> --by "human:<login>"` for each page that you made or changed, because the person gave the fact.

## Step 4: both checks

Call the `knowledge:checking` skill with the graph `competitive-intelligence`. Never
report success while it returns `CHECKS: FAILED`, because the person must see the failure.

## Step 5: report

Report each page that you made or changed, and each ERROR, WARN, and SKIP line of the checks.
