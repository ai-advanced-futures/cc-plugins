---
description: "Delegate legacy ADR migration to the ADR setup skill."
argument-hint: "[--rename]"
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Skill, AskUserQuestion, Edit
---

# /architecture:migrate

Invoke the `architecture:setup` Skill in its migrate mode. Pass `$ARGUMENTS` through.
The skill moves the ADR lifecycle to `lifecycle`, copies the CI scripts again
after a yes, deletes `docs/adr/CLAUDE.md` after a yes, turns navigation on,
and runs `adr.py upgrade`.
