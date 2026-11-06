# JTBD Market Discovery — C4 Architecture Diagrams

Standalone diagram file for tooling and index generators.
Source of truth — README.md references these diagrams inline.

## C4 Level 1 — System Context

```mermaid
C4Context
    title JTBD Market Discovery — System Context (C4 L1)
    Person(user, "Product Analyst", "Discovers market opportunities using JTBD methodology")
    System(jtbd, "JTBD Market Discovery", "10-phase orchestrated workflow for identifying validated market opportunities — job discovery, need generation, opportunity scoring, EVC, segmentation, WTP validation")
    System_Ext(claude, "Claude Code", "AI execution environment — Agent tool for sub-agent dispatch")
    System_Ext(product, "Product Plugin", "Turns top opportunity into product requirements")
    System_Ext(gtm, "GTM Plugin", "Builds go-to-market strategy around validated opportunity")
    System_Ext(pricing, "Pricing Plugin", "Computes RIGHT_PRICE from EVC data")
    Rel(user, jtbd, "Invokes /jtbd-market-discovery:discover")
    Rel(jtbd, claude, "Dispatches phase sub-agents via Agent tool")
    Rel(jtbd, product, "Exports final-output.json")
    Rel(jtbd, gtm, "Exports validated opportunities + segments")
    Rel(jtbd, pricing, "Provides EVC data")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## C4 Level 2 — Container

```mermaid
C4Container
    title JTBD Market Discovery — Container Diagram (C4 L2)
    Person(user, "Product Analyst")
    System_Boundary(jtbd, "JTBD Market Discovery Plugin") {
        Container(discover, "discover skill", "Markdown/LLM", "Asks the questions in the main conversation; dispatches the orchestrator; loops while the orchestrator ends with a QUESTIONS line")
        Container(orchestrator, "Orchestrator Agent", "Markdown/LLM", "Coordinates 10 phases; dispatches sub-agents via Agent tool; manages .jtbd-market-discovery/{session}/state.json; writes questions.json at each checkpoint; handles parallel Phase 3 dispatch")
        Container(phase_agents, "Phase Agents (×9)", "Markdown/LLM", "job-identifier, job-decomposer, need-generator(×4 parallel), effort-quantifier, opportunity-scorer, evc-calculator, segmentation-analyst, wtp-validator, output-assembler — each writes pN.json output")
        Container(jtbd_state, "jtbd_state.py", "Python 3.11", "File I/O helper — create_session, load_session, mark_phase_complete, write/read_phase_output with atomic writes and phase validation guards")
        Container(scripts, "Analysis Scripts", "Python/scikit-learn", "opportunity_scorer.py, evc_calculator.py, segmentation_engine.py (K-means), wtp_validator.py (6-layer), composite_scorer.py, survey_adapter.py — run with uv run")
        ContainerDb(session_store, ".jtbd-market-discovery/{session}/", "JSON files", "state.json + p1.json through p9.json + questions.json + answers.json + final-output.json — compact-resilient, survives context compaction")
        Container(skills, "Method Skills", "SKILL.md files", "11 method skills — one per phase + jtbd-core")
        Container(user_skills, "User Skills", "Markdown", "discover, quick-validate, wtp-check — entry points for three workflow modes")
    }
    Rel(user, discover, "Invokes /jtbd-market-discovery:discover")
    Rel(discover, orchestrator, "Dispatches via Agent tool; answers through answers.json")
    Rel(orchestrator, phase_agents, "Dispatches via Agent tool (fresh sub-agent per phase)")
    Rel(orchestrator, jtbd_state, "Reads/writes session state")
    Rel(phase_agents, jtbd_state, "Writes pN.json outputs")
    Rel(jtbd_state, session_store, "Atomic file writes")
    Rel(phase_agents, scripts, "Invokes for Python analysis")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```
