---
description: Make the domain-model bundle of this repository at docs/domain/, and add a router block to CLAUDE.md that tells each session where the bundle is and in which order to read it. A second run changes no byte.
argument-hint: "[bundle directory]"
disable-model-invocation: true
allowed-tools: Read, Bash
---

# Setup: the domain bundle and the CLAUDE.md router

This skill makes the bundle when it is absent, and writes one short block into `CLAUDE.md`.
It writes no domain page.

Run each command with the repository root (`git rev-parse --show-toplevel`) as the current
directory. If that command fails, tell the user: "This is not a git repository. `/business-domain:setup`
needs one." If `uv` is not installed, run `python3` with the same script path.

When a command gives an exit code that is not 0, stop and show its output. Then do not report success,
because the user must see the failure.

## Step 1: make the bundle

If the user gave a directory as the argument, add `--dir <directory>`. The default is
`docs/domain`.

When `.claude/ddd.json` exists, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py upgrade` in
place of `init`.

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py init

The command prints each path that it wrote, or "The bundle exists. init changed nothing." An
exit code of 2 with the words "names <directory>" means that `.claude/ddd.json` names a
different directory. Tell the user to edit that file to move the bundle.

## Step 2: add the CLAUDE.md router

Read `.claude/ddd.json`, and put its `dir` value in place of `<dir>`:

    sed 's#{{dir}}#<dir>#g' ${CLAUDE_PLUGIN_ROOT}/templates/claude-md-block.md \
      | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py --plugin ddd \
          --repo-root "$(git rev-parse --show-toplevel)"

The script writes only between `<!-- ddd:router start -->` and `<!-- ddd:router end -->`, and
prints `CLAUDE.md router: written <path>` or `CLAUDE.md router: unchanged <path>`. Use the
script and not a hand edit, because the script keeps a second run byte-identical.

Call the `knowledge:checking` skill with the graph `ddd`. Do not report success
while it returns `CHECKS: FAILED`, because the user must see the failure.

## Step 3: check the bundle

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py check

Show each `WARN:` line to the user.

## Report

- The paths that `init` wrote, or that the bundle already existed.
- The router line: `written <path>`, `unchanged <path>`, or `FAILED exit <n>`.
- The last line of the `check` output.
- "Ask about the model with `/business-domain:ask`. To add a page, run
  `ddd.py new <Type> --title <title> --description <description>`. After each Write or Edit of
  a bundle page, the plugin hook runs `ddd.py regen` and `ddd.py check`."
