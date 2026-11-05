---
description: Scaffolds an architecture-decision-record corpus into the repository this is invoked in. Setup can adopt an existing corpus with config only; it vendors deterministic gate tooling only when explicitly requested. Detects a prior corpus and offers greenfield, adopt, or migrate. Use for "/architecture:setup", "set up ADRs in this repo", "scaffold an ADR corpus", "adopt an existing ADR folder", or "migrate legacy ADRs to frontmatter".
argument-hint: "[corpus path]"
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Write, Edit, AskUserQuestion, Skill
---

# setup

Stand up an ADR corpus inside the repository you are invoked in. This writes files into the
**target repo**, never into the plugin. Setup ends green: the register indexes clean and the lint
reports zero errors.

**The bar for what earns an ADR:** record a decision when undoing it later would be expensive.
Cheap to change your mind, no ADR. State this bar plainly during step 3 so the person confirming
the plan sees it.

## Step 1 -- resolve the repository root

```bash
git rev-parse --show-toplevel
```

If this fails, stop: "This is not a git repository. `/architecture:setup` needs one, because the vendored
test suite finds the repository root by walking up to `.git`."

## Step 2 -- detect prior state

```bash
test -f .claude/adr.json && cat .claude/adr.json
```

If `.claude/adr.json` exists, a corpus is already configured -- read `dir` from it, run Step 7
(the CLAUDE.md router) with the stored values, then report the existing setup. Offer `--refresh`;
it refreshes a vendored copy only when the stored gate enables it.

Otherwise, probe for an ADR-shaped folder. Check the corpus-path hint from `$ARGUMENTS` first,
then the common shapes: `docs/adr`, `docs/architecture/adrs`, `doc/adr`, `adr`.

```bash
ls docs/adr 2>/dev/null
ls docs/architecture/adrs 2>/dev/null
```

For any folder found holding `.md` files, report:

- **Folder** -- the path.
- **Naming scheme** -- `NNNN-slug.md` (sequential), `ADR-NNN-slug.md` (legacy sequential, folds to
  sequential), or `YYYY-MM-DD-slug.md` (date). Sample two or three filenames to tell.
- **Metadata style** -- open one file. YAML frontmatter (`---` fences) or legacy bold-key headers
  (`**Status:** Accepted`)?
- **Count** -- how many `.md` files, excluding `README.md` and `CLAUDE.md`.

Finding nothing means greenfield.

## Step 3 -- offer the path

Ask with `AskUserQuestion`, once:

- **Greenfield** -- no existing corpus, or start fresh at a new path. Writes a new corpus at
  `docs/adr/` (or the given path) with an empty register.
- **Adopt** -- a corpus was found. Writes `.claude/adr.json` matching what is already there and
  only `.claude/adr.json` unless the optional deterministic gate is selected. **Modifies no
  existing ADR.**
- **Migrate** -- adopts, then converts legacy bold-key metadata to frontmatter with
  `${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_migrate.py`. Two levers: `--frontmatter`
  (the default) folds bold keys and
  touches no filename; `--rename` also normalises `ADR-002-slug.md` to `0002-slug.md`, which
  changes every link that points at the file, so confirm it separately before running it.
- **Abort** -- stop, no files written.

Also offer the optional PR/CI gate here, whichever path was chosen: ask whether to add
`--gate-deterministic`, or skip (the default). `--gate-deterministic` vendors the scripts, schema,
tests, and CI workflow. The deterministic tier runs `adr_lint.py` and `adr_index.py --check` with
no install step. The optional model tier (`--gate-model`, with the deterministic gate) runs
`/architecture:check` in CI only when `secrets.ANTHROPIC_API_KEY` is present, and its result is
advisory.

## Step 4 -- confirm the manifest, once

Run the dry run and show the exact file list before writing anything:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" --target "$(git rev-parse --show-toplevel)" \
  --dir <dir> --dry-run
```

Confirm every inferred value (corpus path, id scheme, register path) and the full manifest with
the person in the same turn as this dry run. In the same prompt, state that Step 7 adds a short
router block to `CLAUDE.md`, and give the person one way to decline it. No second prompt after
this.

## Step 5 -- write the corpus

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py"` with the chosen mode and print its
receipt verbatim. Append
`--gate-deterministic` and/or `--gate-model` (and `--proposed-verdict <error|warning|off>` if the
person wants a non-default verdict) to any of these when step 3 asked for the gate:

- Greenfield: `--target <root> --dir <dir> --today <YYYY-MM-DD>`
- Adopt: `--target <root> --dir <dir> --id-scheme <sequential|date> --adopt --today <YYYY-MM-DD>`.
  Without `--gate-deterministic`, adoption writes only `.claude/adr.json`.
- A prior corpus already scaffolded and the person wants it brought current:
  `--target <root> --refresh --today <YYYY-MM-DD>` (the gate, if any, is re-read from the existing
  `.claude/adr.json` and refreshed to match -- `--refresh` takes no gate flags of its own).
- Migrate: run the Adopt command above first, then run
  `python3 "${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_migrate.py" [--rename]` from the
  repository root. Show the diff (`git diff -- <dir>`) before saying the migration is done.
  The script writes each change to the working tree and commits nothing, so the diff is what the
  person reviews and commits.

Treat each `register.exclude candidate:` line as information. Classify it as a non-ADR,
intentionally unregistered ADR, or orphan; default an ADR orphan to indexing, not exclusion.

A non-zero exit means it refused (a manifest target already existed, or `--refresh` ran with no
`.claude/adr.json`). Report the refusal and stop. Never delete files to force it through, because
the refusal protects files that the person already has.

## Step 6 -- run the gates and report the receipt

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_index.py" --write --repo-root "$(git rev-parse --show-toplevel)"
python3 "${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_lint.py" --repo-root "$(git rev-parse --show-toplevel)"
```

Print each command with its exit code. Setup is done only when both are green. On any non-zero
exit, report FAILED with the full output.

If `python3` is not on `PATH`, say so, and leave out `adr-gate.yml`. Its scripts are Python, so
the person cannot run the gate before a push.

When both gates are green, run Step 7. When a gate is red, skip Step 7 and close with the receipt
below with `CLAUDE.md router: skipped (gate red)`.

## Step 7 -- add the CLAUDE.md router

Run this step after a write when both gates are green. On the already-configured path of Step 2,
run it directly. When the person declined the block in Step 4, do not run the script, and close
with the receipt below with `CLAUDE.md router: skipped (declined)`.

A fresh or `--refresh` run of `scaffold.py` already writes this block, so on those paths this step
reports `unchanged`. Adoption and an already-configured corpus never reach that write, so this
step is what adds the block for them.

Run one command:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" --target "$(git rev-parse --show-toplevel)" \
  --router-only
```

The script writes only between its own `<!-- adr:router start/end -->` markers, and it creates
`CLAUDE.md` when the file is absent.

The script prints `CLAUDE.md router: written <path>` or `CLAUDE.md router: unchanged <path>` and
exits 0. Any other exit code is a failure: show its stderr in the receipt, and leave `CLAUDE.md`
as it is, because the script owns the block between its markers. On the already-configured path
no question was asked, so say: to remove the block, delete the lines from
`<!-- adr:router start -->` to `<!-- adr:router end -->`.

Close with a receipt on every path: what was written, the corpus path, the id scheme, the two gate
commands' exit codes (on the already-configured path, say that no gate ran), and one line for the
router -- `CLAUDE.md router: written <path>`, `unchanged <path>`, `skipped (declined)`,
`skipped (gate red)`, or `FAILED exit <n>`.

## The brain standard

After the scaffold step (and after an adoption), run:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py --root "$(git rev-parse --show-toplevel)" init
```

It writes `log.md`, runs `adr_index.py --write --nav` (navigation is always
on), and then writes `manifest.md` and the registry entry `adr`.

## Migrate mode

`/architecture:migrate` runs this mode. Do the steps in this order:

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_migrate.py --lifecycle --dry-run`,
   show the list, and ask one question. Only after a yes, run it with `--apply`.
2. When the project has the CI copy (`scripts/adr/`), ask one question:
   "Copy the CI scripts again?" Only after a yes, run
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py --refresh --target <root>`,
   so the `still-proposed` gate reads `lifecycle`.
3. When `docs/adr/CLAUDE.md` exists, show its rules: they are now in the
   router block and the skills. Delete the file only after a yes.
4. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py --root <root> upgrade`.
5. Call the `knowledge:checking` skill with the graph `adr`. Never report
   success while it returns `CHECKS: FAILED`, because a failed check means the graph is broken.
