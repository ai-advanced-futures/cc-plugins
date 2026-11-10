---
description: Confirms the pages of a market discovery run in the jtbd graph, or saves other results and corrections through jtbd_graph.py. Sets status stable and a verified entry on the Run page and on each page of the run. Use for "/jtbd-market-discovery:learn", "confirm these results", and "correct this outcome".
argument-hint: "[run page or correction]"
allowed-tools: Read, Write, Glob, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(gh api user *), Bash(gh issue create *), Bash(date *)
---

# Learn from a run

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command. Write each path in single quotes, and write each `'` in a path as `'\''`, because inside single quotes the shell runs nothing and keeps a space in the path.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`. Also, do not add an `echo` of the exit code, because the Bash tool shows the exit code of a command that fails.

## Step 0: the guards

1. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' pages Run`. When it exits 2, stop with: "This repository has no
   jtbd graph. Run `/jtbd-market-discovery:setup` first." The output also
   lists the Run pages and their `status`.
2. Run `gh api user --jq .login` on its own. Its output is `<login>`. When
   that command fails, ask the person for a name in chat text. A login is safe
   in a command only when it matches `[A-Za-z0-9-]{1,39}`. When `<login>` does
   not match, it is not a login: do not put it in a command; stop and show it.

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

Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' verify-run '<key>' --by 'human:<login>'`. It sets `status: stable` and
adds one `verified` entry on the Run page and on each page whose `run` is
that page. When it exits 1 or 2, stop and show its output.

## Step 3: save other results

Write pages only through the operations `new`, `set`, `link` and `body` of
`jtbd_graph.py`, each in a command that starts as in Step 0. Never
use `Write` or `Edit` on a file in the bundle folder.

For the result of a quick validation, do these steps in this order:

1. Write a Run page first, so that each item page has its `run` link. Set
   `command` of that page to the plugin name, a colon, and the word
   `quick-validate`.
2. Write the item pages. The `run` field of an item page is the path of the
   Run page, such as `/runs/RUN-01.md`. To see the fields of a page type, read
   `${CLAUDE_PLUGIN_ROOT}/schema/jtbd.yaml` with the Read tool. Give only the
   fields that the `slots` line of the type lists. Write 1 Outcome page for
   each need of the results, with the `importance` and the `satisfaction` of
   that need from the survey.
3. Run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own. Its output is `<time>`. Run
   `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' set '<key>' 'finished_at=<time>'`,
   where `<key>` is the ID of the Run page. Write the time itself in the
   command, because Claude Code cannot check a command with a command
   substitution before it runs.
4. Confirm the run as in Step 2, because the person said yes to the results.

Put each text of the person in single quotes, and write each `'` in it as
`'\''`, because inside single quotes the shell runs nothing.

## Step 4: direct edits

When the save code cannot make a change, edit the page directly. Then write
one Report entry: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' log Report '<operation> failed: <error>. I edited <page>: <edit>. Reason: <reason>.'`
Write each `'` in that text as `'\''`, because inside single quotes the shell
runs nothing, and an error text can hold any character.

## Step 5: both checks

Call `knowledge:checking` with the graph `jtbd`. Never report success while it
returns `CHECKS: FAILED`, because the next session trusts a graph that the
checks reject. Correct the cause and call it again.

## Step 6: report

Report each page that changed, each Report entry, and each ERROR, WARN, and
SKIP line of the checks. When Step 4 wrote a Report entry, offer to open a
GitHub issue in `ai-advanced-futures/cc-plugins`.
After a yes, show the person the full issue body, in a fenced block, as the
command will send it. Then ask a second question: "Open the issue with this
body? `ai-advanced-futures/cc-plugins` is public, so remove each path and
each value of the case that must stay private." When the person changes the
body, show it again and ask again. Open it only after a yes to the second
question, because the first yes is to the offer and not to the text:
`gh issue create --repo ai-advanced-futures/cc-plugins --title "jtbd-market-discovery:learn report" --body-file <file>`.
Make the file with the `Write` tool. Its name holds only the characters
`A-Za-z0-9._/-`; with any other name, stop and show the Report entry.
