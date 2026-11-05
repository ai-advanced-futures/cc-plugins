# C4 Level 1 — Context diagram

## System context

grounded-synthesis is a Claude Code plugin. A user or a caller agent starts it. It audits a draft against primary source files.

```mermaid
graph TD
    User["User<br/>(analyst, consultant, researcher)"]
    Caller["Caller agent<br/>(any agent that starts the audit)"]
    GS["grounded-synthesis<br/>(Claude Code plugin)"]
    FS["File system<br/>(source files, draft, session folder)"]

    User -->|"runs /grounded-synthesis:audit<br/>with draft_path + source_paths"| GS
    Caller -->|"starts the orchestrator agent<br/>with the five dispatch fields (ADR-007)"| GS
    GS -->|"reads source files + draft"| FS
    GS -->|"writes gap report + handoff.json"| FS
```

## Actors

- **User** — runs the command by hand, or asks for the skill.
- **Caller agent** — starts the orchestrator agent and reads `handoff.json`.
- **File system** — holds the source files, the draft, the session folder, and the gap report.
