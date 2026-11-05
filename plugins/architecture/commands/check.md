---
description: "Check the current branch's diff against the ADR corpus for contradictions and missing decisions."
argument-hint: "[base branch]"
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Skill
---

# /architecture:check

Invoke the `architecture:reviewing-adr-adherence` Skill and pass `$ARGUMENTS` through verbatim as an
optional base-branch override; it owns any configured rules overlay.

The skill is the gate's model tier. It reports findings and exits 0, because its findings are
advisory. The deterministic tier (`adr_lint.py`, `adr_index.py --check`) is what the gate blocks
on.
