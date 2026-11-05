---
description: "Regenerate the ADR register and lint the corpus."
argument-hint: "[--nav] [config path]"
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Skill, Edit
---

# /architecture:index

Invoke the `architecture:indexing-adrs` Skill and pass `$ARGUMENTS` through verbatim. The
arguments can hold `--nav`, a config path, or both.

The skill owns the write step, the receipt review, and the lint.
