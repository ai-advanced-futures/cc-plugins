# C4 Context Diagram — prose-authenticity Plugin

## System Context

This diagram shows the boundary of the prose-authenticity plugin, and the
actors and systems outside it. The plugin finds out if prose reads as written
by a machine. On request, it rewrites the prose to read as human writing. It
keeps the zones that a human marked, and it keeps the facts. The `neutral`
Mermaid theme gives clear contrast on light and dark backgrounds.

```mermaid
%%{init: {'theme': 'neutral'}}%%
C4Context
    title System Context — prose-authenticity Plugin

    Person(user, "Author", "Checks and humanizes prose before it ships — documents, PR descriptions, deliverables")

    System(pa, "prose-authenticity Plugin", "Scores prose authenticity across tiered detectors and runs a deterministic humanize loop")

    System_Ext(caller, "A caller agent", "Starts the plugin from another plugin or workflow; reads prose-authenticity-handoff.json and waits for the DONE signal")
    System_Ext(groundedsynthesis, "grounded-synthesis Plugin", "Validates fact coverage of rewritten prose against source files")
    System_Ext(hfhub, "HuggingFace Hub", "Serves the three active hf-tier detector models (optional, local inference)")
    System_Ext(apidetectors, "GPTZero / Originality.ai / Sapling", "Commercial detection APIs (optional, consent needed)")

    Rel(user, pa, "Starts the /prose-authenticity:* commands")
    Rel(caller, pa, "Dispatches the orchestrator, reads prose-authenticity-handoff.json")
    Rel(pa, groundedsynthesis, "Dispatches its orchestrator for the fact-coverage audit")
    Rel(pa, hfhub, "Downloads and runs detector models locally")
    Rel(pa, apidetectors, "Sends text for scoring after recorded consent")

    classDef ext fill:#1a3a5c,stroke:#0d2137,color:#ffffff
    class caller,groundedsynthesis,hfhub,apidetectors ext
```

## Key Relationships

| Actor | Interaction |
|---|---|
| Author | Starts `/prose-authenticity:check`, `:humanize`, `:profile`, and `:setup` |
| A caller agent | Dispatches the orchestrator with the Agent tool, reads `.prose-authenticity/run-<id>/prose-authenticity-handoff.json`, and waits for `DONE: prose-authenticity` |
| grounded-synthesis | The orchestrator dispatches its orchestrator with the Agent tool. It is the authority for fact coverage during the humanize loop (ADR-002) |
| HuggingFace Hub | Source of the three active hf-tier models in the roster table (README, `config/detectors.yaml`). Optional. Needs `torch` and `transformers` |
| GPTZero / Originality.ai / Sapling | Commercial api-tier detectors. Optional. They need a recorded consent and API keys in the environment |
