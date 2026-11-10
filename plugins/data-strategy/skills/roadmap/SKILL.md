---
name: roadmap
description: Writes the data deliverables again from an earlier data strategy assessment (the strategy report, the data platform ADR, and the data roadmap with 4 effort and impact groups). Use when a synthesis.md file already exists. Asks the person nothing.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py *)
---

# Data strategy: roadmap from an earlier assessment

This skill needs the session id of an earlier run (`--session <id>`) or the path of a `synthesis.md` file. Take it from `$ARGUMENTS`.

Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next step is then refused.

Run each command on its own, in one Bash call. Write no heredoc, no `; echo`, and no loop, because the tool refuses a joined command.

Test the `output_dir` before you build any command line with it, because the text comes from `$ARGUMENTS`. The whole value must match `[A-Za-z0-9._/-]{1,100}` and must have no `..` part. When the test fails, say that the value is not allowed, start no agent, and stop.

1. Rename each of `strategy-report.md`, `data-platform-adr.md`, and `data-roadmap.md` that exists in the `output_dir` to `<name>.prev.md`, so that an old file is not read as a new one. If the person gave a `synthesis.md` path, the `output_dir` is the folder of that file.
2. Start the agent `data-strategy:deliverable-generator` with the `Agent` tool, in the foreground: set `run_in_background: false`, and wait for it to finish. Give it the field `session_id` and `output_dir` (`.data-strategy-tmp/<id>`), or the field `synthesis_path` and `output_dir` (the folder of that file).
3. Check the 3 files in the `output_dir`: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files '<output_dir>' strategy-report.md data-platform-adr.md data-roadmap.md`. If the exit code is 0, the run is done: show the 3 paths. Else show the last lines of the agent and say that the run failed. The line `DONE: deliverable-generator` is a second sign. Do not fail a run because the line is missing when the 3 files exist.
