---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up. Optionally send it to a named Claude session.
argument-hint: "[@session-name] What will the next session be used for?"
---

Render a handoff document in your reply that summarises this conversation closely enough for a fresh agent to continue the work. Write no file, because the rendered text is the deliverable the user carries into the next session.

Include a "suggested skills" section that names the skills the next agent should invoke.

Reference existing artifacts (PRDs, plans, ADRs, issues, commits, diffs) by path or URL rather than restating them, because a copy goes stale as soon as the artifact changes.

Redact API keys, passwords, and personally identifiable information.

The argument is `[@session-name] [focus]`. Tailor the document to the focus.

When the argument names a session, send the document to it with `SendMessage`, under the first line "Handoff from session `<this session name>`. Continue this work." Then reply with only the session name and `claude attach <session-name>`, because the session already has the document. If `ListAgents` shows no session with that name, render the document in the reply and say so. If two sessions have the name, ask the user which ref to use.
