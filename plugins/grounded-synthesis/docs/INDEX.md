# grounded-synthesis docs

## C4 diagrams

- [C4 Level 1 — Context](diagrams/context.md) — who uses grounded-synthesis and what it touches
- [C4 Level 2 — Container](diagrams/container.md) — the skill, the command, the agents, and the library modules

## Architecture decision records

| ADR | Topic | Status |
|-----|-------|--------|
| [ADR-001](adr/ADR-001-plugin-form-vs-nested-skill.md) | Plugin form, not a skill alone | Accepted |
| [ADR-002](adr/ADR-002-fact-extraction-design.md) | Fact extraction design | Accepted |
| [ADR-003](adr/ADR-003-synchronous-parallel-task-batch.md) | Parallel batch of agent calls in one message | Accepted |
| [ADR-005](adr/ADR-005-handoff-file.md) | Write a generic handoff.json | Accepted |
| [ADR-006](adr/ADR-006-session-storage-location.md) | Session folder in the home folder, with a 30-day sweep | Accepted |
| [ADR-007](adr/ADR-007-caller-contract.md) | The caller contract | Accepted |

The number ADR-004 is not used. The source plugin used it for a decision that this plugin does not have.
