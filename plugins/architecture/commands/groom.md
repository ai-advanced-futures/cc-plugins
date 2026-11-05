---
description: "Groom the ADR corpus: merge overlapping ADRs, retire what reality outgrew, compress prose, or archive the dead."
argument-hint: "[merge|retire|compress|archive]"
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Skill, AskUserQuestion, Write, Edit
---

# /architecture:groom

Invoke the `architecture:grooming-adrs` Skill and pass `$ARGUMENTS` through verbatim as the job selector
(`merge`, `retire`, `compress`, or `archive`; ask which job when no argument is given).

The skill owns all four jobs, the plan and the diff that come before each write, and the
path-aware archive and register repair after a move.
