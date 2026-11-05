---
description: Set up the PRD and roadmap bundles in this repository and add a router block to CLAUDE.md that tells each session where they are and which file to read first. Safe to run again on a repository that already has the bundles; then it only refreshes the router.
disable-model-invocation: true
allowed-tools: AskUserQuestion, Read, Bash, Grep, Glob
---

# Setup — the bundles and the CLAUDE.md router

This skill makes the two bundles when they are absent, and writes one short
block into `CLAUDE.md` that points at them. It writes no PRD page. The
findings of a session go to `/product:learn`.

## Step 0: resolve the repository root

Run this command:

    git rev-parse --show-toplevel

If it fails, stop. Tell the user: "This is not a git repository. `/product:setup`
needs one." Run each later command with the repository root as the current
directory.

## Step 1: the v3 guard

Run this command:

    ls docs/product/prd/index.md

If the file is absent and a v3 PRD file is present in `docs/product/`, stop.
Tell the user: "This repository holds a v3 PRD. Run `/product:migrate` first."
Leave the v3 PRD file as it is, because the migration reads it and a second
copy becomes a second source of truth.

## Step 2: make the bundles, or keep them

If `docs/product/prd/index.md` is present, the bundles exist. Run this
command:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py upgrade

It back-fills `generated`, adds `log.md`, runs `regen`, and writes the
manifest of each bundle and the registry entries `prd` and `roadmap`. Show
its output to the user, tell the user the bundles exist, run no `init`, and
go to Step 3. `prd.py init` refuses to run on an existing bundle, and this
skill does not try.

If the file is absent, and `docs/product/` holds no v3 PRD file, bootstrap:

1. Ask the user for the product name and one sentence that describes the
   product. Use one `AskUserQuestion`. Free text through "Other" is fine. In
   the same question, say that Step 3 adds a short router block to
   `CLAUDE.md`, and give the user one way to decline it.
2. Run this command:

        uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py init --title "<name>" --description "<one sentence>"

   If `uv` is not installed, run `python3` with the same path.
3. The command prints each path that it wrote: the pages, the indexes, the
   manifests, `links.tsv`, and `.claude/knowledge.json`. Show that list to the
   user. If the exit code is not 0, stop and show the output.

## Step 3: add the CLAUDE.md router

Skip this step only when the user declined it; then the receipt says so. The
block tells a future session where the bundles are and which file to read
first. It does not import the bundles: `CLAUDE.md` stays a short map, and a
session reads an index only when it needs it.

The script replaces the block between its own markers when one exists,
appends it when none exists, and creates `CLAUDE.md` when the file is absent.
It changes no text outside its markers.

    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py --plugin prd \
      --repo-root . <<'EOF'
    ## Product requirements and roadmap

    The PRD bundle is `docs/product/prd/`. Read `docs/product/prd/index.md` first, then `docs/product/prd/product.md` for the summary. The roadmap bundle is `docs/product/roadmap/`. Read `docs/product/roadmap/index.md` first. One page holds one requirement or one work item; do not write an ID or a table by hand.
    To find or deepen requirements, run `/product:explore`. To plan work from them, run `/product:plan`. To take one work item, run `/product:work`.
    EOF

The script prints `CLAUDE.md router: written <path>` or
`CLAUDE.md router: unchanged <path>` and exits 0. Any other exit code is a
failure: show its stderr in the receipt. Do not edit `CLAUDE.md` by hand to
work around it, because the receipt must show the failure to the user.

## Step 4: run both checks

Call the `knowledge:checking` skill with the graphs `prd` and `roadmap`.
Setup is done only when it returns `CHECKS: PASSED`. When it returns
`CHECKS: FAILED`, show each `ERROR:`, `WARN:`, and `SKIP:` line to the user
and do not report success, because the bundles are in a state that the checks
reject.

## Report

Tell the user:

- Whether the bundles were made in this run, or already existed.
- One line for the router: `CLAUDE.md router: written <path>`,
  `unchanged <path>`, `skipped (declined)`, or `FAILED exit <n>`.
- When the bundles already existed, no question was asked, so the user had no
  way to decline. Say that, and say: to remove the block, delete the lines from
  `<!-- prd:router start -->` to `<!-- prd:router end -->`. Do not give line
  numbers, because they change when the file changes.
- The result of both checks: `CHECKS: PASSED` or `CHECKS: FAILED` with each
  finding line.

**Recommend**: "Run `/product:explore` to find the requirements, lens by lens."
