---
description: Designs the system with the person and saves the result in the system-design graph - it finds the areas that need a decision, walks the person through them in blocking order, writes an accepted ADR for each decision that is expensive to undo, and writes each page through system_design.py. It replaces /product:system-design, and it offers to migrate docs/product/system-design.md. Use for "/system-design:learn", "design the system", and "decide the data area".
argument-hint: "[area]"
allowed-tools: Read, Grep, Glob, Skill, Bash(uv run *), Bash(git *), Bash(gh issue create *), Bash(test *)
---

# Learn the system design

`ROOT` is `$(git rev-parse --show-toplevel)`.
`S` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/system_design.py --root "$ROOT"`.

## Step 0: the guards

1. Run `$S resolve system`. When it exits 2, stop with: "This repository has
   no system-design graph. Run `/system-design:setup` first."
2. When `docs/product/system-design.md` exists and the graph has no
   Component page, ask one question: "Migrate the old design file?" On yes,
   run `$S migrate-file docs/product/system-design.md`. Show each
   "not migrated" line. For the area of each such item, read its current
   `open_rows`, append the line, and write the whole list back with
   `$S set <slug> open_rows=<YAML list>`. The old file stays until the person
   deletes it.

## Step 1: read the context

Read the inputs through the `ask` skill of each brain (D1):

- the PRD: `product:ask` (capabilities in scope, constraints, metrics, personas);
- the decisions: `architecture:ask` (the ADRs that bind the design);
- the domain: `business-domain:ask` (the bounded contexts and the terms).

When a brain `ask` is not installed, use `knowledge:ask`. When a graph is not
in `.claude/knowledge.json`, tell the person which input is missing, and go on.

Then read `system.md` and `areas/index.md` of the graph.

## Step 2: chart the map

The blocking order of the areas is:
quality, context, strategy, building-blocks, data, contracts, conventions, deployment.
An area blocks the areas after it.

1. List each area with its `area_state`.
2. The frontier is the first `open` area in blocking order, or the area that
   the person gave in `$ARGUMENTS`.
3. A `fog` area has a question that cannot be stated yet. Only when the
   person states it, read the area's current `fog` list, append the item,
   and write the whole list back with `$S set <slug> fog=<YAML list>`.

## Step 3: work the frontier

For the frontier area, ask one decision at a time, as chat text. Give the
context, the options, and your recommendation. Wait for the answer.

For each decision:

1. Write the pages that the decision makes or changes: `$S new <Type>`,
   `$S set <ID> KEY=YAML`, and `$S link <ID> <field> <target>`. For a
   dependency: `$S link COMPONENT-01 uses /components/COMPONENT-02.md --with style=sync --with technology=HTTPS`.
2. When the decision is expensive to undo, call `architecture:learn` to write an
   accepted ADR. Give it `parent_spec: system-design:/areas/<slug>.md`, and,
   when one component is the subject, `model.element: <COMPONENT-NN>`.
3. Add the decision row:
   `$S link <slug> decisions adr:/<file> --with key=<slug>-<n> --with binds="<what it binds>" --with source=adr`.
   For a decision with no ADR, use `$S set` to add a row with
   `source: "human:<login>, <date>"` and no `adr`.
4. When each row of the area has a decision, run `$S set <slug> area_state=decided`
   and `$S log Settle "<slug> open -> decided"`.

Then go to the next open area in blocking order. Stop when the person stops,
or when no area is open. When no area is `open` or `fog`, ask if the design
is accepted, and on yes run `$S set system design_state=accepted`.

## Step 4: direct edits

When the save code cannot make a change, edit the page directly. Then write
one Report entry: `$S log Report "<operation> failed: <error>. I edited <page>: <edit>. Reason: <reason>."`
Write one Report entry for each recommendation to improve this skill or the
save code.

## Step 5: both checks

Call `knowledge:checking` with the graph `system-design` and with each graph
that changed (for example `adr`). Never report success while it returns
`CHECKS: FAILED`, because the next session trusts a graph that the checks
reject. Correct the cause and call it again.

## Step 6: report

Report each area that changed state, each page that you wrote, each ADR, each
Report entry, and each ERROR, WARN, and SKIP line of the checks. When Step 4
wrote a Report entry, offer to open a GitHub issue in
`ai-advanced-futures/cc-plugins`. After a yes, show the person the full issue
body, in a fenced block, as the command will send it. Then ask a second
question: "Open the issue with this body? `ai-advanced-futures/cc-plugins` is
public, so remove each path and each value of the project that must stay
private." When the person changes the body, show it again and ask again. Open
it only after a yes to the second question, because the first yes is to the
offer and not to the text:
`gh issue create --repo ai-advanced-futures/cc-plugins --title "system-design:learn report" --body-file <file>`.
The file holds only the body that the person accepted.
