---
description: Confirms the pages of a market discovery run in the jtbd graph, or saves other results and corrections through jtbd_graph.py. Sets status stable and a verified entry on the Run page and on each page of the run. Use for "/jtbd-market-discovery:learn", "confirm these results", and "correct this outcome".
argument-hint: "[run page or correction]"
allowed-tools: Read, Write, Glob, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(gh api user *), Bash(gh issue create *)
---

# Learn from a run

`ROOT` is `$(git rev-parse --show-toplevel)`.
`J` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root "$ROOT"`.

## Step 0: the guards

1. Run `$J pages Run`. When it exits 2, stop with: "This repository has no
   jtbd graph. Run `/jtbd-market-discovery:setup` first." The output also
   lists the Run pages and their `status`.
2. `LOGIN` is the output of `gh api user --jq .login`. When that command
   fails, ask the person for a name in chat text. A login is safe in a command
   only when it matches `[A-Za-z0-9-]{1,39}`. When `LOGIN` does not match, it
   is not a login: do not put it in a command; stop and show it.

## Step 1: choose the case

- A run page is in `$ARGUMENTS`, or the person gave no argument: go to Step 2.
  With no argument, the run is the newest Run page with `status: draft`
  in the output of Step 0. When the key does not match `RUN-<digits>` or
  `/runs/RUN-<digits>.md`, it is not a key: do not put it in a command; stop
  and show it, because the shell runs the text of a command before the save
  code can refuse it.
- Other results (the output of a quick validation, or a correction from the
  person): go to Step 3.

## Step 2: confirm a run

Run `$J verify-run <key> --by human:$LOGIN`. It sets `status: stable` and
adds one `verified` entry on the Run page and on each page whose `run` is
that page. When it exits 1 or 2, stop and show its output.

## Step 3: save other results

Write pages only through `$J new`, `$J set`, `$J link`, and `$J body`. Never
use `Write` or `Edit` on a file in the bundle folder.

For the result of a quick validation, write a Run page first, so that each
item page has its `run` link. Set `command` of that page to the plugin name,
a colon, and the word `quick-validate`. Then write the item pages.

Put each text of the person in single quotes, and write each `'` in it as
`'\''`, because inside single quotes the shell runs nothing.

## Step 4: direct edits

When the save code cannot make a change, edit the page directly. Then write
one Report entry: `$J log Report '<operation> failed: <error>. I edited <page>: <edit>. Reason: <reason>.'`
Write each `'` in that text as `'\''`, because inside single quotes the shell
runs nothing, and an error text can hold any character.

## Step 5: both checks

Call `knowledge:checking` with the graph `jtbd`. Never report success while it
returns `CHECKS: FAILED`, because the next session trusts a graph that the
checks reject. Correct the cause and call it again.

## Step 6: report

Report each page that changed, each Report entry, and each ERROR, WARN, and
SKIP line of the checks. When Step 4 wrote a Report entry, offer to open a
GitHub issue in `ai-advanced-futures/cc-plugins`. Open it only after a yes:
`gh issue create --repo ai-advanced-futures/cc-plugins --title "jtbd-market-discovery:learn report" --body-file <file>`.
Make the file with the `Write` tool. Its name holds only the characters
`A-Za-z0-9._/-`; with any other name, stop and show the Report entry.
