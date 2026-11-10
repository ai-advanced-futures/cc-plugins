---
description: Sets up the ux-hci-design graph of this repository - the bundle at docs/ux-hci-design/, the manifest, the registry entry, and the router block in CLAUDE.md - asks if git keeps the brain, and offers to ingest the earlier results in .ux-artifacts/. Use for "/ux-hci-design:setup".
argument-hint: "[bundle folder]"
disable-model-invocation: true
allowed-tools: Bash, Read, Read(//**/ux-hci-design/**/templates/claude-md-block.md), Skill, AskUserQuestion
---

# Set up the ux-hci-design graph

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
`S` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ux_graph.py --root <git root>`.

## Step 0: the knowledge plugin

Find the knowledge plugin with `bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh knowledge scripts/knowledge.py`. Its output is `<knowledge root>`. Read `<knowledge root>/.claude-plugin/plugin.json`. When the probe exits 1, or the `version` is lower than 1.6.0, stop with: "ux-hci-design:setup needs the knowledge plugin 1.6.0 or later. Install it: claude plugin install knowledge@cc-plugins." Version 1.5.x gives a `K-manifest` error for this graph.

## Step 1: the question

Read `<git root>/.claude/knowledge.json`. A missing file is the same as a file with no `ux-hci-design` entry. Ask 1 question with AskUserQuestion. Say in the question that research findings and personas can hold facts about real people, and that git keeps each pushed fact in its history. The options:

- "Git keeps the UX brain (docs/ux-hci-design/)"
- "Keep the UX brain out of git"
- "No brain now" (only when the entry does not exist)

When the entry exists, the first option is the answer that the entry holds (an entry with `"git": false` holds "Keep the UX brain out of git"; an entry with no `git` key holds "Git keeps the UX brain"), and its text ends with " (the choice of this project)". Offer no "No brain now", because the brain exists. When the question gets no answer (the tool gives an error, or AskUserQuestion is not in your tool set, as in a headless `-p` run) and the entry exists, keep the answer of the entry: in Step 2 run `$S upgrade` with no `--git`, because a run with no person must not change an answer that a person gave. When the entry does not exist, use "Keep the UX brain out of git", and write this line in these words as your own message, because the person looks for it: "The UX brain is in docs/ux-hci-design/, and git does not keep it. Run /ux-hci-design:setup to change this." On "No brain now", stop with: "No brain was made. The results stay in .ux-artifacts/."

## Step 2: make or upgrade the bundle

- When `.claude/knowledge.json` names the graph `ux-hci-design`, run `$S upgrade --git yes` for the answer "Git keeps the UX brain", or `$S upgrade --git no` for the answer "Keep the UX brain out of git". The option `--git` changes the answer of the registry entry and the exclude file of this clone, because `upgrade` with no option keeps the first answer. When the answer is "Keep the UX brain out of git" and the folder is absent (a new clone), run `$S init --git no` in its place. When the answer changes to "Keep the UX brain out of git", run `git ls-files <folder>` on its own. When it lists a file, say: "Git still tracks <n> files of <folder>. Run `git rm -r --cached <folder>` and commit, so that git stops tracking them. The earlier commits keep them." Then write `git: kept out of git (git still tracks <n> files)` in the report.
- When not, run `$S init --git yes` or `$S init --git no`, from the answer. Add `--dir '<folder>'` when the person gave a folder, in single quotes. The command refuses a folder with a character outside `A-Z a-z 0-9 . _ / -`.

When the command exits 1 or 2, stop and show its output. Do not report success, because the command refused or failed, and the graph is not set up.

## Step 3: the router block

Read the bundle folder in `.claude/knowledge.json`. When it holds a character outside `A-Z a-z 0-9 . _ / -`, stop and show the folder, because a repository that you clone can set any text there, and the text goes into a shell command. Else run:

```bash
sed -e 's|{{DIR}}|<folder>|g' < "${CLAUDE_PLUGIN_ROOT}/templates/claude-md-block.md" \
| python3 "${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py" --plugin ux-hci-design --repo-root "<git root>"
```

## Step 4: the earlier results

When `<git root>/.ux-artifacts/` exists, has no `pages.json`, and holds an output file of the plugin (`research_findings.json`, `personas.json`, `journey_maps.json`, `mental_models.mmd`, `design_concepts.json`, `wireframes.json`, `interaction_patterns.json`, `user_flows.mmd`, `evaluation_report.json`), show the list of files. Ask one question: "Save these earlier results in the brain?" On yes, run `$S ingest .ux-artifacts --phase <phase>` for each phase that has a file, in the order empathize, define, ideate, prototype, test, and show each `ingest` error. The save removes each file that it read.

## Step 5: both checks

Call the `knowledge:checking` skill with the graph `ux-hci-design`. Setup is done only when it returns `CHECKS: PASSED`.

## Step 6: report

    ux-hci-design setup complete: <folder>
    case: new | upgraded
    git: kept by git | kept out of git
    CLAUDE.md router: written <path> | unchanged <path> | FAILED exit <n>
    earlier results saved: <number of phases>
    checks: <each ERROR, WARN, and SKIP line, or "none">
