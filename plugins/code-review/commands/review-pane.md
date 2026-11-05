---
description: "Open a pane that walks one GitHub PR chunk by chunk, keeps local accept marks and draft comments, answers questions about a chunk, and posts one review verdict at the end."
argument-hint: "[pr-number | pr-url | owner/repo#number]"
disable-model-invocation: true
---

# /code-review:review-pane

The `code-review` hooks module answers this command and opens the pane. This prompt runs only where
the module does not: a build older than Claude Code 2.1.294.

Tell the engineer that the review pane needs Claude Code 2.1.294 or later, and offer
`/code-review:hitl` for a read-only walkthrough in the transcript instead.
