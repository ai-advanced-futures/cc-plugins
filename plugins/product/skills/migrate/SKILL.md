---
description: Turn a v3 docs/product/prd.md and roadmap.md into the two OKF bundles
argument-hint: "[map-file]"
disable-model-invocation: true
model: opus
agent: prd-analyst
allowed-tools: AskUserQuestion, Read, Write, Edit, Bash, Grep, Glob
---

# Migrate — the v3 documents to the two bundles

Change the v3 files into the PRD bundle and the roadmap bundle. The script does
each exact step. This skill does each step that needs a decision.

Run each command below with the target repository as the current directory. If
`uv` is not installed, run `python3` with the same path. If a command gives an
exit code that is not 0, stop and show the output to the user.

## Step 0: the bundle must not exist

Run this command:

    ls docs/product/prd/index.md

If the file is present, this repository already holds the two bundles. Stop.
Tell the user that `/product:migrate` ran before. Do not run the migration a
second time, because a second run writes a second source of truth.

If the file is absent and `docs/product/` holds no v3 PRD file, this repository
has no PRD. Tell the user to run `/product:explore` first, which bootstraps the
bundle. Then stop.

This skill works on the two bundles through `${CLAUDE_PLUGIN_ROOT}/scripts/prd.py`.

## Step 1: read first

Read these three files, in this order:

1. `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the layout, the page
   format, the IDs, the relationships, and the write rule.
2. `${CLAUDE_SKILL_DIR}/../shared/roadmap-model.md` — the roadmap types, the
   states, and the status tables.
3. `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style. Step 7
   writes the text of each page in this style.

## Step 2: the scan

Run this command:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py migrate --scan

The scan reads the v3 files and writes nothing. Show the full report to the
user.

- Exit code 0: the migration runs with no map. Go to step 5.
- Exit code 1: a map is necessary, or a finding stops the run. Go to step 3 for
  each prefix that the report calls `unknown`, and to step 4 for each finding.

A repository with `docs/product/prd.md` and no `docs/product/roadmap.md` is
valid. The script migrates the PRD and writes the roadmap bundle empty.

## Step 3: the map

The fixed map gives a type to each v3 lens prefix: `PRB`, `PER`, `JRN`, `CAP`,
`SCP`, `MET`, `BIZ`, `GTM`, `RSK`, and `CON`. Every other prefix is `unknown`,
and an `unknown` prefix needs a decision.

For each `unknown` prefix, read the blocks of that prefix and the section of
the PRD that holds them. Propose a type for each group, one section at a time.
The user confirms or changes each group before you go to the next section.

Write the map to a YAML file outside `docs/product/`:

```yaml
prefixes:
  NFR-DP: Constraint            # each ID with this prefix
ids:
  REQ-DP-014: Metric            # one ID. This wins over `prefixes`
```

The script never guesses a type, and it refuses to run while one block has no
type, because a wrong type is a silent defect that no check finds later. Each
value is a PRD page type of the schema. The run copies the map to
`archive/migrate-map.yaml`, so the decision has a record.

## Step 4: a finding that stops the run

- **A duplicate ID**, and **a trace target that is not the ID of a block**.
  These are faults of the v3 files. Ask the user to correct the v3 file and to
  commit it. Then run the scan again.
- **An unmarked difference.** The v3 roadmap marks a drifted trace with `⚠`. A
  trace whose hash does not agree, and that carries no mark, means one of two
  things: the recipe that wrote the hash is not a recipe that the script knows,
  or a PRD edit has no sync after it. The script cannot tell the two apart.
  Show the count and each such trace, and offer the user three actions:
  1. Another recipe: add `--hash-recipe v3`, `--hash-recipe full`, or
     `--hash-recipe no-bullet`, and run the scan again.
  2. The v3 `/product:roadmap-sync` first, which syncs the hashes, and then the
     scan again.
  3. `--accept-unmarked-drift`, which makes each difference a drifted trace.
     A person clears each flag after the migration.

The scan also reports each block of 600 words or more, and the number of lines
that go to the archive only. These two are not findings that stop the run.
Show them to the user: step 7 acts on the long blocks.

## Step 5: the dry run

Run this command:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py migrate --map <file> --dry-run

With no map, run:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py migrate --dry-run

The dry run builds the tree in a temporary directory, runs the five
assertions, deletes the tree, and changes nothing in the repository. Show the
result to the user. If one assertion fails, show the assertion line and stop.

`docs/product/` must hold no change that is not committed. Ask the user to
commit first.

## Step 6: the run

Run this command:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py migrate --map <file>

The run moves the tree into `docs/product/` and archives the two v3 files as
`docs/product/archive/prd-v3.md` and `docs/product/archive/roadmap-v3.md`.
Show the rollback command that it prints, and tell the user that the command
works only before the next commit.

## Step 7: the human work

The script copies each v3 block as it is, and it does not guess a value that
needs judgment. The checker reports each missing value as an error until this
step writes it. Work with the user, one page group at a time, and show each
change before you write the next group:

- `kind` on each Scope page and each Risk page, and `role` on each Metric page.
- `addresses` on each Capability page, and `serves` on each Journey page. Read
  the prose of the page and propose each link.
- Need pages, from the pains and the jobs in the persona text and the journey
  text. The user confirms each one.
- A better title and a better description for each page. The description is the
  router: a reader opens the page from it. For a PRD that had no frontmatter,
  this includes the description of `product.md`.
- The text of each page in the style of `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md`.
  Keep the meaning. Do not change an ID, a link, a frontmatter key, a hash, a
  generated block, or a direct quote. Show each changed page to the user, and
  the user accepts or edits it. Text in `archive/` does not change.
- The milestone dependencies that the script wrote as sentences, because the
  v3 roadmap held them as prose. Show each one to the user.
- Each page that carries the size warning. Propose which text moves to a linked
  file. The user confirms each division.

## Step 8: finish

Run this command:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py migrate --finish

It stores a hash for each trace that was not drifted, writes `drifted` for each
trace that was, runs `prd.py regen`, and adds a **Migrate** line to both logs.
The hashes are stored last, so the rewrite of step 7 gives no false drift.

Exit code 0 means that the command stored the hashes. It is not a clean
verdict. The command prints the findings of the checker. Read each finding,
fix it with the user, and then run:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check

Repeat until `prd.py check` exits 0. Do not report success before it does,
because until then the bundle is in a state that the checks reject.
Show each warning to the user. A warning does not stop you.

## Step 9: v2 files

`docs/prd/*.md` are v2 files. The script has no v2 support. Map the content of
each v2 file to pages by hand: the prefix list of step 3 gives the type of each
v2 ID, and `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` gives the page
format. Write each page with `prd.py new`, and write the text of each page in
the style of the `google-style` skill.

## Report

Tell the user:

- The number of pages of each type that the migration wrote.
- The path of `archive/id-map.md`, which gives the old ID, the new ID, and the
  path of each page.
- Each trace that the finish step marked `drifted`, and who clears it.
- Each finding of `prd.py check` that is still open.

**Recommend**: "Run `/product:setup` to add the router block to `CLAUDE.md`, then
`/product:plan` to promote the next slice of work."
