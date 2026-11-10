# ADR-006 — Session folder in the home folder, with a 30-day sweep

**Status:** Accepted

## Context

The orchestrator needs a place for the files of each run: `session.json`, the fact files, the coverage files, and `handoff.json`. A folder inside the current project would fill the project with files and would need a `.gitignore` entry.

## Decision

The session folder is `${GROUNDED_SYNTHESIS_HOME:-$HOME/.cache/grounded-synthesis-sessions}/{session_id}/`. The `session_id` is a uuid4, so two runs cannot use the same folder. No project needs a `.gitignore` entry.

The orchestrator runs this command in Step 1:

```
uv run ${CLAUDE_PLUGIN_ROOT}/lib/session_paths.py --resolve --sweep-days 30
```

With `--sweep-days N`, the script first deletes the session folders that are older than N days. With no session id, the script makes the uuid4, makes the new session folder, and prints the session id and the absolute path of the folder, so the agent runs no shell command to make a uuid. With a session id, it prints only the path. Without `--sweep-days`, it deletes nothing.

The session folder holds facts from the source files of the user. It is data of the user, not a path in a repository. The sweep keeps this data for 30 days only.

## Consequences

The files of a run stay out of the project. The sweep stops the folder from growing without limit. The sub-agents get the absolute `session_dir_absolute` in their dispatch context and never read environment variables (a doc-contract test checks this). `GROUNDED_SYNTHESIS_HOME` gives tests and CI their own folder.
