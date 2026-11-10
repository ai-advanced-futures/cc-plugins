---
description: Saves domain knowledge into the ddd graph - a bounded context, a term, an aggregate, an event, a relationship, a question, or a source - through ddd.py, then runs both checks and reports. Use for "/business-domain:learn", "add this term to the domain model", and the "Learn these results?" offer of a domain skill.
argument-hint: "[what to learn]"
allowed-tools: Read, Grep, Glob, Skill, Bash(uv run *), Bash(git *), Bash(gh issue create *)
---

# Learn into the domain model

`D` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py --root "$(git rev-parse --show-toplevel)"`.

## Step 0: the guard

Run `$D resolve CONTEXT-01`. When it exits 2, stop with: "This repository has
no domain bundle. Run `/business-domain:setup` first."

## Step 1: find what exists

For each item to learn, run `$D resolve <name>`. A hit through `aliases` is the
same page. Change that page, because a second page splits one concept in two.

## Step 2: write through ddd.py

- A new page: `ddd.py new <Type> --title "<title>" --description "<one line>" --set KEY=YAML`.
- A changed field: `ddd.py set <ID> KEY=YAML`.
- A new edge: `ddd.py link <ID> <field> /<folder>/<ID>.md`.
- A rename or a merge: `ddd.py merge <FROM> <INTO>` (the old page becomes deprecated).

## Step 3: direct edits

When `ddd.py` cannot make a change, edit the page directly, then write one
Report entry: `ddd.py log Report "<operation> failed: <error>. I edited <page>: <edit>. Reason: <reason>."`
Write one Report entry for each recommendation to improve this skill or `ddd.py`.

## Step 4: both checks

Call the `knowledge:checking` skill with the graph `ddd`. Never report success
while it returns `CHECKS: FAILED`, because the user must see the failure.

## Step 5: report

Report each page that you made or changed, each Report entry, and each ERROR,
WARN, and SKIP line of the checks. When a Report entry exists, offer to open a
GitHub issue in `ai-advanced-futures/cc-plugins`. After a yes, show the person
the full issue body, in a fenced block, as the issue will hold it. Then ask a
second question: "Open the issue with this body?
`ai-advanced-futures/cc-plugins` is public, so remove each path and each value
of the project that must stay private." When the person changes the body, show
it again and ask again. Open it only after a yes to the second question,
because the first yes is to the offer and not to the text.
