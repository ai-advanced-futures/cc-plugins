# ADR-001 — Plugin form, not a skill alone

**Status:** Accepted

## Context

The audit needs three agents and a Python library. A skill alone (a `SKILL.md` file with no `plugin.json`) cannot hold agents or library modules.

## Decision

Build the audit as a Claude Code plugin. The plugin holds:

- one skill, `skills/grounded-synthesis-audit/SKILL.md`, for automatic use;
- one command, `commands/audit.md`, for manual use;
- three agents;
- a Python library in `lib/`.

## Consequences

The plugin form is the only form that can hold agents and library modules. The skill name is its folder name, `grounded-synthesis-audit`. The command has no `name` key: the user runs it as `/grounded-synthesis:audit`.
