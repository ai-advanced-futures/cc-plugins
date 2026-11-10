---
description: Learn the findings of a session into the PRD bundle — one page for each finding through prd.py new, the relationships, the product summary, both checks, and the log line
argument-hint: "[lens]"
model: opus
agent: prd-analyst
allowed-tools: Write, Read, Edit, Grep, Glob, Bash, AskUserQuestion
---

# Learn — write the findings into the PRD bundle

Turn the findings of this session into pages of `docs/product/prd/`. One
finding becomes one page. The script writes each page and assigns each ID.

## Step 0: the bundle must exist

Run this command:

    ls docs/product/prd/index.md

If the file is absent and a v3 PRD file is present in `docs/product/`, stop.
Tell the user: "This repository holds a v3 PRD. Run `/product:migrate` first."
Leave the v3 PRD file as it is, because the migration reads it and a second
copy becomes a second source of truth.

If the file is absent and `docs/product/` holds no v3 PRD file, this
repository has no bundle. Tell the user to run `/product:explore` first, which
bootstraps the bundle. Then stop.

This skill works on the two bundles through `${CLAUDE_PLUGIN_ROOT}/scripts/prd.py`.

## Step 1: read the bundle

Read these files, in this order:

1. `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the layout, the page
   format, the IDs, the relationships, and the write rule.
2. `${CLAUDE_SKILL_DIR}/../shared/product-hat.md` — the product guardrail.
3. `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style (Google
   developer documentation style) for each line of PRD text. Its application
   to the bundle is in "Writing style" in `bundle-schema.md`.
4. `docs/product/prd/index.md` — the bundle index.
5. `docs/product/prd/product.md` — the product summary and the `lenses` map.
6. The `index.md` of the directory of each lens that this session touched.
   The lens catalog of `/product:explore` gives the directory of each lens.

Do not read every file of a directory, because a large bundle fills the
context. Open a page only when a finding of this session changes that page.

## Step 2: choose the lens

- If `{{lens}}` was given, learn that lens.
- If no argument was given, name the lens or the lenses that this session
  explored.
- If this session explored nothing, ask the user which lens to learn. Use one
  `AskUserQuestion`.

## Step 3: apply the product-hat filter

Read each finding against the constraint test of `product-hat.md`. A finding
that fails the test gets one of two actions:

- If a product constraint is inside it, take the constraint out and write it
  as a `Constraint` page.
- If no constraint is inside it, drop the finding. Tell the user what you
  dropped, and why.

The PRD holds no architecture, no technology, and no implementation.

## Step 4: write one page for each finding

For each finding, choose one action: a new page, or an edit of one page. A
finding that changes the meaning of an existing page is an edit of that page.
A finding that says something new is a new page.

A new page goes through the script. Run one command for each page:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py new Capability \
  --title "Book a slot in under a minute" \
  --description "A customer books a free slot in less than one minute." \
  --link addresses=/needs/NEED-02.md \
  --body "The customer selects a day and sees each free slot."
```

If `uv` is not installed, run `python3` with the same path. Run each command
with the target repository as the current directory. The command prints the
path that it wrote. If the exit code is not 0, stop and show the output.

Never choose an ID, because `prd.py new` assigns it and a hand-chosen ID can
collide. The script also writes the frontmatter keys in the order of the schema.

To edit a page, open the file and change the body or the typed fields. Keep
the ID. The page type table of `bundle-schema.md` gives the typed field of
each type: `kind` for a Need, a Scope page, and a Risk, `role` for a Metric,
`kano` for a Capability, and `primary` for a Persona.

Never edit an `index.md`, a `closed.md`, a `LINKS` block, or a `STATUS`
block, because the script writes each one and overwrites a hand edit.

## Step 5: write the relationships

Store a relationship one time, on the page of the later lens, and point it to
the earlier lens. Learning one lens does not change the frontmatter of an
older page. The direction rule and the table of the fields are in
"Relationships" in `bundle-schema.md`.

On a new page, `--link <field>=<target>` writes the relationship. Give
`--link` one time for each target. A target is a bundle-relative path that
starts with `/`, as in `/personas/PERSONA-02.md`. For a relationship on an
existing page, use
`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py link <id> <field> <target>`.

## Step 6: write the decisions and the open questions

- Each decision of this session becomes a `Decision` page. Add `--link
  about=<target>` for each page that the decision is about.
- Each open question of this session becomes a `Question` page with
  `--status draft`.

## Step 7: update the product summary

Open `docs/product/prd/product.md` and change three things:

1. The `status` of this lens in the `lenses` map: `in-progress` while a gap
   remains, `complete` when the "done when" of the lens is met. If you are
   not sure, ask the user.
2. The `updated` date of this lens, and the top-level `updated` date. Both
   dates are today, in UTC.
3. One short paragraph for this lens in the body, which says what the lens
   now holds.

## Step 8: check the drift of the pages that changed

Run this command with the ID of each page that this session wrote or
changed:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py drift --ids CAPABILITY-03 NEED-02 --write
```

Read the exit code and stderr:

- Exit code 0: no trace drifted. Go to Step 9.
- Exit code 1 with no `ERROR:` line on stderr: one trace or more is drifted.
  `--write` records each drifted target on the roadmap item that traces to
  it. Show each drifted item to the user. A person clears a flag, not you.
  Tell the user to run `/product:review`.
- Exit code 1 with an `ERROR:` line on stderr: the command failed, for
  example on a page that it cannot read. Stop, and show the output.
- Exit code 2: stop, and show the output.

## Step 9: write the log line

Run this command, with one line of text that names the lens and each page
that changed:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py log Learn "[product](product.md) personas: NEED-04, NEED-05, PERSONA-02"

This writes one line under the `## <YYYY-MM-DD>` heading of today in UTC, of
the form `* **Learn**: <text>, by <actor>, at <timestamp>`. The script adds
the heading, the actor, and the timestamp. Never change a line that is
already there, because the log is append only.

## Both checks and the report

1. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py regen`.
2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check`. Call the
   `knowledge:checking` skill with the graphs `prd` and `roadmap`.
   Do not report success before both checks run, because a check that did
   not run proves nothing. Never report success while either one fails or
   returns `CHECKS: FAILED`, because the bundle is then in a state that the
   checks reject.
3. When `prd.py` cannot make a change, edit the page directly, then write one
   Report entry: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py log Report "<operation> failed: <error>. I edited <page>: <edit>. Reason: <reason>."`
4. Report each page, each Report entry, and each ERROR, WARN, and SKIP line.
   When a Report entry exists, offer to open a GitHub issue in
   `ai-advanced-futures/cc-plugins`. After a yes, show the person the full
   issue body, in a fenced block, as the issue will hold it. Then ask a second
   question: "Open the issue with this body? `ai-advanced-futures/cc-plugins`
   is public, so remove each path and each value of the project that must stay
   private." When the person changes the body, show it again and ask again.
   Open it only after a yes to the second question, because the first yes is
   to the offer and not to the text.

## Writing style

Restyle only the text that this session writes or changes, because a new body
gives a new hash, and a new hash makes each trace to that page drifted.

## Report

Tell the user:

- Each page that you wrote, with its ID and its path.
- The status of each lens, and which spine lenses remain.
- Each drifted item of step 8.

**Recommend next steps**:

- If a spine lens is not complete → "Run `/product:explore` to continue with
  [next lens]."
- If each spine lens is complete and no roadmap bundle exists → "Run
  `/product:simulate` to stress-test the PRD, or `/product:plan` to build the
  roadmap."
- If step 8 flagged an item → "Run `/product:roadmap-sync` to review the flagged
  items."
