# C4 Level 2 — Container diagram

## Containers

```mermaid
graph TD
    SK["grounded-synthesis-audit<br/>(skill)<br/>automatic use"]
    CMD["commands/audit.md<br/>manual use"]
    CALLER["Caller agent<br/>(ADR-007)"]
    ORCH["grounded-synthesis-orchestrator<br/>(agent, sonnet)<br/>thin coordinator"]
    FE["fact-extractor<br/>(agent, sonnet)<br/>12 facts per source"]
    CC["coverage-checker<br/>(agent, sonnet)<br/>PRESENT/MISSING per fact"]
    CONST["lib/constants.py<br/>constants"]
    SL["lib/source_loader.py<br/>file ingest"]
    FS["lib/fact_schema.py<br/>fact file check"]
    HS["lib/handoff_schema.py<br/>handoff.json check"]
    SP["lib/session_paths.py<br/>session folder and sweep"]
    GR["lib/gap_report.py<br/>report assembly and handoff"]

    CMD --> SK
    SK --> ORCH
    CALLER --> ORCH
    ORCH -->|"Wave 1: parallel Agent calls"| FE
    ORCH -->|"Wave 2: parallel Agent calls"| CC
    ORCH -->|"uv run"| SL
    ORCH -->|"uv run"| FS
    ORCH -->|"uv run"| GR
    ORCH -->|"uv run"| SP
    GR --> HS
    FE --> CONST
    CC --> CONST
    GR --> CONST
```

## Design rules

- The orchestrator is a **thin coordinator**. It never reads the output files of the sub-agents.
- The library modules are plain Python. They do not import agents.
- The sub-agents get the absolute `session_dir_absolute` in their dispatch context. They never read environment variables.
- The orchestrator runs each script as `uv run ${CLAUDE_PLUGIN_ROOT}/lib/<file>.py`. Each script has a PEP 723 header that lists its packages.
