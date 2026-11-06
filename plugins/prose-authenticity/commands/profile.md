---
description: Build or update a voice profile from 3+ writing samples so humanize rewrites sound like a specific author
argument-hint: "<name> --samples <file> <file> <file> [<file> ...]"
---

Build a voice profile from the arguments in `$ARGUMENTS`: `<name> --samples <file> [<file> ...]`.

1. Count the sample files. If there are fewer than 3, stop and say how many more
   are needed. A voice that is guessed from thin evidence is wrong.
2. List the files and the word count of each one. Ask the person with
   `AskUserQuestion` to confirm the sample set.
3. Dispatch the agent `prose-authenticity:voice-profiler` with the `Agent` tool.
   Give it these fields: `name` and `samples` (the confirmed paths).
4. Run `uv run ${CLAUDE_PLUGIN_ROOT}/lib/profile_store.py validate .prose-authenticity/profiles/<name>.yaml`.
   The agent has no Bash tool, so you run it.
5. Show the profile path and the voice summary.
