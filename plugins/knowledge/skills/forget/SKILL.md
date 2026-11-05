---
description: Removes one page from any brain, each page that cannot exist without it, and each reference to it in every graph, after one yes. A protected page, a missing brain plugin, or a graph with no manifest stops it before any change. Use for "/knowledge:forget <graph>:/<path>", "forget this page", and "remove this decision everywhere".
argument-hint: "<graph>:/<path>"
allowed-tools: Read, Edit, Grep, Glob, Skill, AskUserQuestion, Bash(uv run *), Bash(bash *), Bash(git *), Bash(gh issue create *)
---

# Forget a page

The target is: **$ARGUMENTS**

`ROOT` is `$(git rev-parse --show-toplevel)`.
`K` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge.py --root "$ROOT"`.

## Step 1: the plan

Run `$K forget-plan $ARGUMENTS`. Each line has one of these forms:

| Line | Meaning |
|---|---|
| `TARGET <node>` | The page to forget. |
| `REMOVE <node>` | A page of the tree. It goes. |
| `UNLINK <node> <field> <value>` | A link to remove from a page that stays. |
| `EDIT <node>:<line> <text>` | A body mention to edit by hand. |
| `REMOTE <graph> <repo>` | A graph in another repository. |
| `STOP <reason>` | The plan cannot run. |

When the command exits 1, or when the plan has a `STOP` line, show each
`STOP` line and stop. Change nothing. Never change protected, because only a
person sets or removes it.

## Step 2: one yes

Show the full plan: each REMOVE, UNLINK, and EDIT line. Ask one question:
"Forget these pages and remove these references?" On no, stop. Change nothing.
The person gives one yes for the whole tree.

## Step 3: the save code

For each graph of the plan, read `plugin` and `save_code` in its
`manifest.md`, and find the plugin:
`bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh <plugin> <save_code>`.
`S` is `uv run <plugin root>/<save_code> --root "$ROOT"`.

Do the steps in this order, for local graphs only:

1. For each UNLINK line: `$S unlink <path> <field> <value>`.
2. For each REMOVE line, last line first: `$S remove <path>`.
3. For each EDIT line: open the page, and change the mention so that it does
   not name the page. Write one Report entry for each edit:
   `$S log Report "forget: I edited <node> line <line>: <what changed>"`.

When an operation fails, stop, and report the failed command and its output.

## Step 4: remote graphs

For each REMOTE line, ask a separate yes: "Open a pull request in <repo>
that removes these references?" On yes:

1. `$K remote-checkout <graph>`. It prints the clone folder.
2. Do Step 3 with `--root <clone>` for the lines of that graph.
3. `$K remote-publish <graph> --branch knowledge/forget-<date> --title "Forget <target>" --body-file <file>`.

One pull request for each repository. Until it merges, the remote graph can
still link to the page. The general check reports that link as a warning.

## Step 5: both checks

Call the `knowledge:checking` skill with each graph that changed.
Never report success while it returns `CHECKS: FAILED`, because a failed
check means that a page or a link is now broken. Each `remove` already
writes the page ID to `retired_ids` and a Forget entry to `log.md`. No new
page gets that ID.

## Step 6: report

Report each removed page, each removed link, each edit, each pull request,
and each ERROR, WARN, and SKIP line of the checks. When Step 3 wrote a Report
entry, offer to open a GitHub issue in
`ai-advanced-futures/cc-plugins`, and open it only after a yes.
