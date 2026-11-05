---
description: Give the sofa team a new request or a question
argument-hint: "<what you want, or your question>"
---

Read the team prefix in `docs/adlc.md` (section 1). Send this message with `SendMessage` to `<prefix>-requests` (load SendMessage with ToolSearch first):

```
REQUEST · <your session name> → <prefix>-requests · terminal
From: <git config user.name>
$ARGUMENTS
```

If `<prefix>-requests` is not live (`ListAgents`), tell the user to start the team with `/sofa:start`. Tell the user that requests will reply in this session.
