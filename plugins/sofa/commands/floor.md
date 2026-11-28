---
description: Show the factory floor (publish the artifact, open the local live page, or print the terminal view)
argument-hint: "[artifact | live | terminal]"
---

The floor has 3 views of 1 snapshot (STORY-452). The argument selects the view. With no argument, use `artifact`. Run each command from the main folder of the repository. Send no message to the team.

- `artifact`: run `${CLAUDE_PLUGIN_ROOT}/scripts/sofa-floor artifact --out <scratchpad folder>/factory-floor.html`. Then publish that file with the Artifact tool (the `icon` is `chart` on the first publish). In a later run of this session, publish the same path again, so the link stays the same. Give the user the link, and say that the page is a snapshot, not live: it shows the time of the snapshot, and each action on it gives text to paste.
- `live`: run `${CLAUDE_PLUGIN_ROOT}/scripts/sofa-floor serve` in the background. Its first output line is `floor page: <address>`. Give the user that address. The page is only on this computer (127.0.0.1). It takes a new snapshot each 10 seconds and shows each new hand-off as it is logged. Stop the server when the user asks.
- `terminal`: run `${CLAUDE_PLUGIN_ROOT}/scripts/sofa-floor terminal` and show the output as it is. Then say that the pane `/sofa-dashboard` shows the same view and refreshes each 30 seconds.

When the command exits with a code that is not 0, show its 1 line of error. The usual cause is no floor configuration (`.claude/sofa-floor.json`), or no state store yet (start the team with `/sofa:start`).
