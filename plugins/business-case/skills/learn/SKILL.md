---
description: Confirms the pages of a case in the business-case graph after the person accepts them, or saves a note of the person on the page of a case, through bc_graph.py, then runs both checks and reports. Use for "/business-case:learn" and the "Learn these results?" offer of /business-case:build.
argument-hint: "[case page or correction]"
allowed-tools: Read, Glob, Skill, Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/bc_graph.py *), Bash(git rev-parse *), Bash(gh api user --jq .login), Bash(gh issue create --repo ai-advanced-futures/cc-plugins *)
---

# Learn into the business-case graph

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`.
`B` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/bc_graph.py --root "<git root>"`. Write the script path with no quotes, because the hook of this plugin runs the checks only after a command that has the script path outside quotes.

## Step 0: the guards

1. Run `$B regen --check`. When it exits 2, stop with: "This repository has no
   business-case graph. Run `/business-case:setup` first." Exit 0 and exit 1
   are not a stop, because Step 5 runs the checks.
2. Run `gh api user --jq .login`. The output is `<login>`. When the command
   fails, ask the person for a login in chat text. A login is safe in a
   command only when it matches `[A-Za-z0-9-]{1,39}`. When it does not match,
   stop and show it.
3. Read the bundle folder of the graph `business-case` in
   `<git root>/.claude/knowledge.json`. It is `<bundle>`.

## Step 1: choose the work

- The argument is a Case page (`CASE-<digits>`, `/cases/CASE-<digits>.md`, or
  the slug of a case, which matches `[a-z0-9][a-z0-9-]*`): go to Step 2.
- There is no argument: find the files `<bundle>/runs/RUN-*.md`, and Read the
  one with the highest number. Its `case` field names the Case page. Go to
  Step 2.
- The argument is other text: go to Step 3.

## Step 2: confirm a case

1. Read the Case page. When the argument is a slug, Read the files
   `<bundle>/cases/CASE-*.md`, and use the one whose `slug` field is the
   argument. When no page has it, stop and name the slug. The `case_folder`
   field of the page is the case folder, and its ID is `<CASE ID>`. The folder
   is safe in a command only when it matches `business-cases/[a-z0-9][a-z0-9-]*`.
   When it does not match, stop and show it.
2. Run `$B publish --case <case folder>`, so that the pages hold the values
   that the case folder has now. When it exits 1 or 2, stop and show its
   output. Do not confirm a page, because the person would confirm values
   that the case folder does not have.
3. Find the newest Run page of the case: Read the files `<bundle>/runs/RUN-*.md`
   from the highest number down, and stop at the first one whose `case` field
   names the Case page. Its ID is `<RUN ID>`.
4. Run `$B verify-case <CASE ID> --run <RUN ID> --by human:<login>`. It sets
   `status: stable` and adds one `verified` entry on the Case page, on the Run
   page, and on each `draft` page of the case whose `run` holds that Run page.
   When it exits 1 or 2, stop and show its output. Do not report success,
   because no page is confirmed.

## Step 3: a correction or a note

- A correction of a value of a case (a figure, a grade, a decision, the text
  of a section, a strategy entry, a condition): write no page, because the
  next `publish` writes the value of the case folder over a value that you
  write into a page. Say: "The pages of a case come from its case folder. Run
  `/business-case:build` on the case and make the correction there. The run
  writes the pages again."
- A note of the person about a case: find the Case page from its ID or slug, as
  Step 2 does, or else from the newest Run page, as Step 1 does. Then
  run `$B body <CASE ID> --append --file - --by human:<login> <<< '<note>'`.
  Put the note in single quotes, and write each `'` in it as `'\''`, because
  inside single quotes the shell runs nothing. `publish` keeps the notes of a
  Case page.

## Step 4: direct edits

When the save code cannot make a change, tell the person the operation and
its error. Then write one Report entry:
`$B log Report '<operation> failed: <error>. Reason: <reason>.' --by human:<login>`
Write each `'` in that text as `'\''`. Write one Report entry for each
recommendation to improve this skill or the save code. This skill has no file
tool that writes, so each change of a page goes through `$B`.

## Step 5: both checks

Call the `knowledge:checking` skill with the graph `business-case`. Never
report success while it returns `CHECKS: FAILED`, because the next session
trusts a graph that the checks reject. Correct the cause and call it again.

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
`gh issue create --repo ai-advanced-futures/cc-plugins --title 'business-case:learn report' --body '<the Report entries>'`.
Write each `'` in the body as `'\''`.
