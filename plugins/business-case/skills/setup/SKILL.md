---
description: Sets up the business-case graph of this repository - the bundle at docs/business-case/, the manifest, the registry entry, and the router block in CLAUDE.md - and writes the pages of each case folder that the repository has. Use for "/business-case:setup".
argument-hint: "[bundle folder]"
disable-model-invocation: true
allowed-tools: Bash, Read, Skill
---

# Set up the business-case graph

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
`S` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/bc_graph.py --root "<git root>"`. Write the script path with no quotes, because the hook of this plugin runs the checks only after a command that has the script path outside quotes.

## Step 1: make or upgrade the bundle

- When `.claude/knowledge.json` names the graph `business-case`, run `$S upgrade`.
- When not, run `$S init`. Add `--dir '<folder>'` when the person gave a folder, in single quotes. A folder name is safe in a command only when it matches `[A-Za-z0-9._/-]{1,100}`, has no `..` part and does not start with `/`. When it does not match, stop and show it, because the shell runs the text of a command before the save code can refuse it.

When the command exits 1 or 2, stop and show its output. Do not report
success, because the command refused or failed, and the graph is not set up.

## Step 2: the router block

Read the bundle folder in `.claude/knowledge.json`. The rule of Step 1 holds for it too, because a repository that you clone can set any text there. When the folder does not match, stop and show it.

Else read `${CLAUDE_PLUGIN_ROOT}/templates/claude-md-block.md` with the Read tool, and not with a command, because Claude Code refuses a `sed` command on this file. Put the folder in place of each `{{DIR}}`, and give that text to the router script on standard input:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py" --plugin business-case --repo-root "<git root>" <<'EOF'
<the text of the template, with the folder in place of each {{DIR}}>
EOF
```

## Step 3: the cases of the repository

A case is a folder `<git root>/business-cases/<slug>/` that holds `case.json`. `/business-case:build` writes the pages of a case at the end of each run. This step writes the pages of each case that an older version of the plugin made.

For each case, run `$S publish --case business-cases/<slug>`. A slug is safe in a command only when it matches `[a-z0-9][a-z0-9-]*`. Show the folder of each slug that does not match, and run no command for it.

- When `publish` prints a line that starts with `PRIVATE:`, show that line. Git ignores that case folder, so the case gets no page.
- When `publish` exits 1 or 2, show its output, and go on with the next case. The case folder is complete, and the graph does not hold that case.

## Step 4: both checks

Call the `knowledge:checking` skill with the graph `business-case`. Setup is
done only when it returns `CHECKS: PASSED`.

## Step 5: report

    business-case setup complete: <folder>
    case: new | upgraded
    CLAUDE.md router: written <path> | unchanged <path> | FAILED exit <n>
    cases published: <number> of <number>; <each case that failed or that git ignores, or "none">
    checks: <each ERROR, WARN, and SKIP line, or "none">

Tell the person that git tracks the folder by default. A person who does not
want the pages in git adds the folder to `.gitignore`.
