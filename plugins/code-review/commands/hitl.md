---
description: "Walk an engineer through one pull request with plain-language summaries, grounded questions, drill-down, and back navigation. The final approval question is verbal only; this command never writes to GitHub."
argument-hint: "[pr-number | pr-url | branch]"
disable-model-invocation: true
allowed-tools: Skill
---

# /code-review:hitl

Invoke the `code-review:walking-through-prs` Skill with `$ARGUMENTS` verbatim.
The skill owns PR resolution, the walkthrough, session state, and the verbal close.
