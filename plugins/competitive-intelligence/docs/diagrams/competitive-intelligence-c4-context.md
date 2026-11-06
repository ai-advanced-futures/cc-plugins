# competitive-intelligence - C4 System Context

This diagram shows who uses the plugin and which other systems it uses. The Container diagram (competitive-intelligence-c4-container.md) shows the inside of the plugin.

```mermaid
%%{init: {'theme': 'neutral'}}%%
C4Context
    title System Context - competitive-intelligence

    Person(analyst, "Analyst", "Maps a competitive market, analyzes one competitor, and classifies vendor pricing archetypes")

    System(ci, "competitive-intelligence", "Six-phase competitive analysis, six analysis lenses, and a vendor pricing-archetype classifier")

    System_Ext(claudeCode, "Claude Code", "Runs the skills and starts the agents of the plugin")
    System_Ext(coach, "business-case coach", "Starts the discover runner and the analyze runner with a plugin-run block, and reads the result files")
    System_Ext(readers, "pricing, gtm, business-case", "Read the output files of the plugin")
    System_Ext(jtbd, "jtbd-market-discovery", "Optional input: job-step data for the JTBD lens")
    System_Ext(sources, "Web and data sources", "Public web pages, optional MCP research servers, and the evidence files that the analyst names")

    Rel(analyst, claudeCode, "Starts a skill")
    Rel(claudeCode, ci, "Runs skills and agents")
    Rel(coach, ci, "Starts discover-runner and analyze-runner")
    Rel(ci, coach, "Writes result files", "plugin-result/1")
    Rel(ci, readers, "Writes output files", "JSON")
    Rel(jtbd, ci, "Gives job-step data", "JSON")
    Rel(ci, sources, "Reads and compares competitor data")
```
