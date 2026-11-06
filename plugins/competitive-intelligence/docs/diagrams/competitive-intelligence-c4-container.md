# competitive-intelligence - C4 Container

This diagram shows the inside of the plugin: the skills that ask the person, the agents that do the work, the lens skills, the scripts, and the files that the plugin writes. The Context diagram (competitive-intelligence-c4-context.md) shows the plugin and the systems around it.

```mermaid
%%{init: {'theme': 'neutral'}}%%
C4Container
    title Container - competitive-intelligence

    Person(analyst, "Analyst")
    System_Ext(coach, "business-case coach", "Starts the two runners with a plugin-run block, and reads the result files")

    Container_Boundary(ci, "competitive-intelligence") {
        Container(fullRun, "Skill competitive-intelligence", "SKILL.md, main conversation", "Runs the six phases, asks the questions, shows each checkpoint, and starts the phase agents with the Agent tool")
        Container(entrySkills, "Skills discover, analyze, monitor, respond, validate", "SKILL.md, main conversation", "Ask the questions of one entry point, then start the agents or follow the lens skills")
        Container(vendorSkill, "Skill vendor-archetype-classify", "SKILL.md, main conversation", "Asks for the vendor and its pricing page, then starts the classifier agent")
        Container(runners, "discover-runner, analyze-runner", "Claude Sonnet / .md", "Take every answer from a plugin-run block, ask nothing, and write the result file")
        Container(phase1, "context-analyst (phase 1)", "Claude Sonnet / .md", "Writes the context configuration from the answers in its dispatch")
        Container(phase2, "ecosystem-mapper (phase 2)", "Claude Sonnet / .md", "Classifies competitors on six dimensions")
        Container(phase3, "intelligence-gatherer (phase 3)", "Claude Sonnet / .md", "Collects, scores, and compares competitive data")
        Container(phase4, "lens-executor (phase 4)", "Claude Sonnet / .md", "Reads each lens skill and follows it, one layer after the other")
        Container(lenses, "Lens skills (6)", "SKILL.md, not user-invocable", "lenses-jtbd-performance, lenses-forces-analysis, lenses-economic-value, lenses-strategic-positioning, lenses-technology-disruption, lenses-loss-churn")
        Container(phase5, "synthesizer (phase 5)", "Claude Opus / .md", "Writes the SWOT, the implications, and the recommendations")
        Container(phase6, "deliverable-generator (phase 6)", "Claude Sonnet / .md", "Writes the chosen deliverables and the rules of the result file")
        Container(vendor, "vendor-archetype-classifier-agent", "Claude Sonnet / .md", "Extracts the pricing signals of one vendor and classifies its archetype")
        Container(scripts, "Python scripts", "Python 3.11", "Result file name, vendor archetype pipeline, and the library modules for scoring, comparison, and schema checks")
        ContainerDb(session, "Session folder", "JSON", ".competitive-intelligence/<session>/ - session.json, a summary file for each phase, and the full data files")
        ContainerDb(results, "Result files", "JSON", ".competitive-intelligence/results/ - one plugin-result/1 file for each run of discover or analyze")
        ContainerDb(vendorFiles, "Vendor archetype files", "JSON", ".competitive-intelligence/vendor-archetype-handoff.json")
    }

    Rel(analyst, fullRun, "Starts")
    Rel(analyst, entrySkills, "Starts")
    Rel(analyst, vendorSkill, "Starts")
    Rel(coach, runners, "Starts with the Agent tool")
    Rel(fullRun, phase1, "Starts with the Agent tool")
    Rel(fullRun, phase2, "Starts with the Agent tool")
    Rel(fullRun, phase3, "Starts with the Agent tool")
    Rel(fullRun, phase4, "Starts with the Agent tool")
    Rel(fullRun, phase5, "Starts with the Agent tool")
    Rel(fullRun, phase6, "Starts with the Agent tool")
    Rel(entrySkills, phase1, "Starts with the Agent tool")
    Rel(entrySkills, phase2, "Starts with the Agent tool")
    Rel(entrySkills, phase3, "Starts with the Agent tool")
    Rel(entrySkills, lenses, "Reads and follows (analyze)")
    Rel(runners, phase1, "Starts with the Agent tool")
    Rel(runners, phase2, "Starts with the Agent tool")
    Rel(runners, phase3, "Starts with the Agent tool")
    Rel(runners, results, "Writes")
    Rel(phase4, lenses, "Reads and follows each lens skill")
    Rel(phase4, session, "Reads six lens summary files for the cross-check")
    Rel(fullRun, session, "Reads the summary file of each phase at a checkpoint")
    Rel(vendorSkill, vendor, "Starts with the Agent tool")
    Rel(vendor, scripts, "Runs the emitter with uv run")
    Rel(scripts, vendorFiles, "Writes")
    Rel(runners, scripts, "Runs result_name.py with uv run")
```
