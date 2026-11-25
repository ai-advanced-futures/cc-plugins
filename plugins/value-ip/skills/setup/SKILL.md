---
description: Sets up the value-ip graph of this repository - the bundle at docs/value-ip/, the manifest, the registry entry, and the router block in CLAUDE.md - and offers to save the result files that earlier runs of value-ip:analyze wrote. Use for "/value-ip:setup".
argument-hint: "[bundle folder]"
disable-model-invocation: true
allowed-tools: Read, Skill, AskUserQuestion, Bash(git rev-parse *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vip_graph.py *), Bash(uv run --no-project ${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py *)
---

# Set up the value-ip graph

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`.
`V` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vip_graph.py --root "<git root>"`. Write the script path with no quotes, because the hook of this plugin runs the checks only after a command that has the script path outside quotes.

## Step 1: make or upgrade the bundle

- When `.claude/knowledge.json` names the graph `value-ip`, run `$V upgrade`.
- When not, run `$V init`. Add `--dir '<folder>'` when the person gave a folder, in single quotes. A folder name is safe in a command only when it matches `[A-Za-z0-9._/-]{1,100}`, has no `..` part and does not start with `/`. When it does not match, stop and show it, because the shell runs the text of a command before the save code can refuse it.

When the command exits 1 or 2, stop and show its output. Do not report success, because the command refused or failed, and the graph is not set up.

## Step 2: the router block

Read the bundle folder in `.claude/knowledge.json`. The rule of Step 1 holds for it too, because a repository that you clone can set any text there. When the folder does not match, stop and show it.

Else read `${CLAUDE_PLUGIN_ROOT}/templates/claude-md-block.md` with the Read tool, and not with a command, because Claude Code refuses a command that names a file of a loaded plugin as a file that the command can change. Put the folder in place of each `{{DIR}}`, and give that text to the router script on standard input. Write the script path with no quotes, because the grant of this skill names the path with no quotes:

```bash
uv run --no-project ${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py --plugin value-ip --repo-root "<git root>" <<'EOF'
<the text of the template, with the folder in place of each {{DIR}}>
EOF
```

## Step 3: the earlier results

Run `$V pending`. It prints a JSON list of the files in `.value-ip/results/`, oldest first (the file names start with the time), each with the `run` that holds it, or `null`. Keep the entries with no run. When there is none, go to Step 4.

Else show the list, and ask one question with AskUserQuestion: "Save these earlier results in the graph?" On yes, run `$V ingest <file>` for each entry, in that order. A file name is safe in a command only when it matches `[A-Za-z0-9._-]{1,200}`: show each file that does not match, and run no command for it. When a command exits 1 because the file is already in the graph, say so and go on. When it exits 1 or 2 for another reason, show the output and go on with the next file. The pages stay `draft`: `/value-ip:learn` is the person's confirmation.

## Step 4: both checks

Call the `knowledge:checking` skill with the graph `value-ip`. Setup is done only when it returns `CHECKS: PASSED`.

## Step 5: report

    value-ip setup complete: <folder>
    graph: new | upgraded
    CLAUDE.md router: written <path> | unchanged <path> | FAILED exit <n>
    results saved: <number> of <number>; <each file that failed, or "none">
    checks: <each ERROR, WARN, and SKIP line, or "none">

Tell the person that git tracks the folder by default. A person who does not want the pages in git adds the folder to `.gitignore`.
