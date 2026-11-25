---
description: Saves the result file of a value-ip:analyze run in the value-ip graph after the person accepts it, and records the person's confirmation of its pages, through vip_graph.py, then runs both checks and reports. Use for "/value-ip:learn" and the "Learn these results?" offer after /value-ip:analyze.
argument-hint: "[result file | RUN ID]"
allowed-tools: Read, Skill, AskUserQuestion, Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vip_graph.py *), Bash(git rev-parse *), Bash(gh api user *), Bash(gh issue create --repo ai-advanced-futures/cc-plugins *)
---

# Learn into the value-ip graph

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`.
`V` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vip_graph.py --root "<git root>"`. Write the script path with no quotes, because the hook of this plugin runs the checks only after a command that has the script path outside quotes.

## Step 0: the guards

1. Run `$V regen --check`. When it exits 2, stop with: "This repository has no value-ip graph. Run `/value-ip:setup` first." Exit 0 and exit 1 are not a stop, because Step 5 runs the checks.
2. Run `gh api user --jq .login`. The output is `<login>`. When the command fails, ask the person for a login in chat text. A login is safe in a command only when it matches `[A-Za-z0-9-]{1,39}`. When it does not match, stop and show it.

## Step 1: choose the work

- The argument is a RUN ID (`RUN-<digits>`) or a `run_id`: go to Step 4 with that run.
- The argument is a path under `.value-ip/results/` that ends in `.json`: it is `<result file>`. It is safe in a command only when it matches `\.value-ip/results/[A-Za-z0-9._-]{1,200}\.json`. When it does not match, stop and show it. Go to Step 2.
- There is no argument: run `$V pending`. It prints the files of `.value-ip/results/`, oldest first, each with the `run` that holds it, or `null`. The newest file is the last entry. When there is none, stop with: "No result file. Run `/value-ip:analyze` first." Go to Step 2 with that file. When the `run` of that file is not `null`, say so and go to Step 4 with that run.

## Step 2: show the result

Read `<result file>`. Show the person the subject (`run.subject`), the `value` of each `right_to_win` result, the `label` of each `differentiator` result, and each gap with its `why`. Say that each result is the judgement of the model: no result is validated.

Ask one question with AskUserQuestion: "Learn these results?" On no, stop with: "Nothing was saved. The result file stays in `.value-ip/results/`."

## Step 3: save the result

Run `$V ingest <result file>`. It makes one Run page, one page for each result and one page for each gap, all `draft`. When it exits 1 because the file is already in the graph, say so and go to Step 4 with the run that its message names. When it exits 1 or 2 for another reason, stop and show its output. Do not report success, because no page was saved.

## Step 4: confirm the run

Ask one question with AskUserQuestion: "Confirm the pages of this run as read and agreed? They stay the judgement of the model." On no, go to Step 5: the pages stay `draft`. On yes, run `$V verify-run <RUN ID> --by "human:<login>"`. It sets `status: stable` and adds one `verified` entry on the Run page and on each page of the run. A second confirmation adds an entry, it does not replace the first. When it exits 1 or 2, stop and show its output.

## Step 5: both checks

Call the `knowledge:checking` skill with the graph `value-ip`. Never report success while it returns `CHECKS: FAILED`, because the next session trusts a graph that the checks reject. Correct the cause and call it again.

## Step 6: direct edits and report

When the save code cannot make a change, tell the person the operation and its error. Then write one Report entry: `$V log Report '<operation> failed: <error>. Reason: <reason>.' --by "human:<login>"`. Write each `'` in that text as `'\''`. This skill has no file tool that writes, so each change of a page goes through `$V`.

Report each page that changed, each Report entry, and each ERROR, WARN, and SKIP line of the checks. When a Report entry exists, offer to open a GitHub issue in `ai-advanced-futures/cc-plugins`. After a yes, show the person the full issue body in a fenced block, as the command will send it. Then ask a second question: "Open the issue with this body? `ai-advanced-futures/cc-plugins` is public, so remove each path and each value that must stay private." Open it only after a yes to the second question, because the first yes is to the offer and not to the text: `gh issue create --repo ai-advanced-futures/cc-plugins --title 'value-ip:learn report' --body '<the Report entries>'`. Write each `'` in the body as `'\''`.
