# JTBD Market Discovery — C4 Architecture Diagrams

Standalone diagram file for tooling and index generators.
Source of truth — README.md references these diagrams inline.

## C4 Level 1 — System Context

```mermaid
C4Context
    title JTBD Market Discovery — System Context (C4 L1)
    Person(user, "Product Analyst", "Discovers market opportunities using JTBD methodology")
    System(jtbd, "JTBD Market Discovery", "10-phase workflow for identifying validated market opportunities — job discovery, need generation, opportunity scoring, EVC, segmentation, WTP validation")
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
        Container(discover, "discover skill", "Markdown/LLM", "Runs the 10 phases in the main conversation; asks the questions; starts the phase agents one at a time; runs the scripts with uv run between the starts; manages .jtbd-market-discovery/{session}/state.json; writes the result file and the graph pages")
        Container(phase_agents, "Phase Agents (×9)", "Markdown/LLM", "job-identifier, job-decomposer, need-generator (×4, one at a time), effort-quantifier, opportunity-scorer, evc-calculator, segmentation-analyst, wtp-validator, output-assembler — tools Read, Write (Glob for two); no Bash; each reads its input files and writes pN.json")
        Container(jtbd_state, "jtbd_state.py", "Python 3.11", "File I/O helper — create_session, load_session, mark_phase_complete, write/read_phase_output with atomic writes and phase validation guards")
        Container(scripts, "Analysis Scripts", "Python/scikit-learn", "opportunity_scorer.py, evc_calculator.py, segmentation_engine.py (K-means), wtp_validator.py (6-layer), composite_scorer.py, survey_adapter.py, run_phase_6.py to run_phase_9.py — run with uv run by the skills, not by the agents")
        ContainerDb(session_store, ".jtbd-market-discovery/{session}/", "JSON files", "state.json + p1.json through p9.json + questions.json + answers.json + final-output.json — compact-resilient, survives context compaction")
        Container(skills, "Method Skills", "SKILL.md files", "11 method skills — one per phase + jtbd-core")
        Container(user_skills, "User Skills", "Markdown", "discover, quick-validate, wtp-check — entry points for three workflow modes")
    }
    Rel(user, discover, "Invokes /jtbd-market-discovery:discover")
    Rel(discover, phase_agents, "Starts one agent for each phase through the Agent tool; answers through answers.json")
    Rel(discover, jtbd_state, "Reads/writes session state")
    Rel(phase_agents, jtbd_state, "Writes pN.json outputs")
    Rel(jtbd_state, session_store, "Atomic file writes")
    Rel(discover, scripts, "Runs the scripts with uv run and passes the result file to the agent")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```
