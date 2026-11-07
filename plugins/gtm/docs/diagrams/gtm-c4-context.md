# gtm plugin: C4 diagrams

These diagrams show the plugin in its context and its parts. Each outside system in the diagrams is optional. The person adds it.

## C4 Context

```mermaid
C4Context
  title gtm plugin: Context

  Person(operator, "GTM operator", "Founder, marketer, seller, or RevOps lead")

  System_Boundary(mkt, "cc-plugins marketplace") {
    System(gtm, "gtm plugin", "Full-funnel GTM intelligence: orchestrated content, an integrity gate, and a sales-comp gate")
    System_Ext(aiml, "aiml plugin", "Writes the p15-trigger-event file")
    System_Ext(evidence, "competitive-intelligence, jtbd-market-discovery, pricing", "Save graphs (competitive-intelligence, jtbd-market-discovery) and files (pricing) that gtm reads as evidence")
  }

  System_Ext(coach, "Coach plugin (business-case)", "Starts the three marketing commands through runners and reads the result files")
  System_Ext(servers, "MCP servers that the person adds", "hubspot, apollo, ahrefs, canva, google-analytics, notion, slack")
  System_Ext(skills, "Skills of other plugins", "enterprise-search, customer-support, sales, marketing, data, value-ip, tech-contracts")

  Rel(operator, gtm, "Runs /gtm:* commands and skills")
  Rel(coach, gtm, "Starts a runner with the plugin-run block, reads .gtm/results/ and .gtm/sales-comp-gate-handoff.json")
  Rel(aiml, gtm, "Gives the p15-trigger-event file for auto-comms routing")
  Rel(evidence, gtm, "Give graph pages that plugin_integrator.py reads, and files that it finds")
  Rel(gtm, servers, "Reads CRM, prospect, SEO, and analytics data; publishes only in a command that the person runs")
  Rel(gtm, skills, "Calls a skill with the Skill tool when the plugin is in the session; else uses its own path")
```

## C4 Container

```mermaid
C4Container
  title gtm plugin: Container

  Container_Boundary(plugin, "plugins/gtm") {
    Container(commands, "commands/", "Markdown", "13 commands. Each asks the person its questions in the main conversation.")
    Container(orchestrator, "orchestrator.md", "Thin coordinator", "Reads the dispatch fields, runs the waves with foreground Agent calls, and never holds artifact content")
    Container(content, "content agents", "Markdown agents", "brand, marketing, sales, funnel, knowledge, codebase-scanner, research")
    Container(integrity, "integrity-agent.md", "Markdown agent", "Truth Tier gate. It runs after each content agent and is the only writer to gtm-output/")
    Container(runners, "marketing-*-runner.md", "Markdown agents", "Run the brand, launch, and funnel commands for a coach. They follow the Result file section of the writer agent (ADR-005).")
    Container(scgate, "sales-comp-gate-agent.md", "Markdown agent", "Writes the sales-comp gate file with an exact cliff recommendation (ADR-003)")
    Container(skillset, "skills/", "Markdown", "30 skills: frameworks, integrity rules, marketing and sales methods, and the gate skill")
    Container(scripts, "scripts/", "Python", "Exact work: truth_tier_validator, gtm_constants, sales_comp_gate, funnel_analyzer, plugin_integrator, result_name, and more")
    Container(defs, "definitions/ and schemas/", "Markdown and JSON", "Shared concepts, thresholds, and the schemas of the handoff files")
    ContainerDb(tests, "tests/", "pytest", "Unit tests and tests that read the prompt files")
    Container(adrs, "docs/adr/", "Markdown", "ADR-001, ADR-002, ADR-003, ADR-005")
    ContainerDb(ctx, "gtm-context.json", "Session state", "Completion flags, dispatched agents, plugin inputs, and learned knowledge")
    ContainerDb(open, ".gtm/open-questions.json", "Choice file", "Written by the orchestrator when the person must choose")
  }

  Rel(commands, orchestrator, "/gtm:run starts it with the dispatch fields")
  Rel(orchestrator, content, "Dispatches in waves")
  Rel(orchestrator, integrity, "Dispatches after each content agent")
  Rel(orchestrator, ctx, "Reads completion_flags")
  Rel(orchestrator, open, "Writes it and ends with OPEN: when a choice is open")
  Rel(commands, open, "Reads it, asks the person, starts the orchestrator again")
  Rel(content, ctx, "Write drafts and completion_flags")
  Rel(orchestrator, scripts, "Runs truth_tier_validator between the 2 dispatches of each integrity pass")
  Rel(runners, commands, "Read the command file and follow its body")
  Rel(runners, content, "Follow the Result file section of the writer agent")
  Rel(scgate, scripts, "Classifies the cliff with the sales_comp_gate emitter")
  Rel(scgate, defs, "Validates the gate file against the schema in schemas/")
  Rel(skillset, scgate, "sales-comp-gate-review follows the agent file in the main conversation")
  Rel(tests, scripts, "Import the scripts and check that the prose matches the constants")
```

## Notes

- The orchestrator is a thin coordinator. It reads only `completion_flags` and one short `completion_log` line of each agent. It never reads artifact content.
- The integrity agent is the only writer to `gtm-output/`. It gates each artifact on the band that `truth_tier_validator.py` writes. The floor is 0.60 and the target is 0.85. Both values come from `gtm_constants`.
- The deepest chain of agents is `/gtm:run`, then `gtm:orchestrator`, then a content agent or the integrity agent. That is two layers below the main conversation.
- No agent asks the person a question. The commands and the skills ask.
- The three runners dispatch no agent and publish nothing. A person's run of a marketing command writes the same result file as a coach's run.
- The sales-comp gate has one entry for a person (the skill `sales-comp-gate-review`) and one for a dispatched run (the agent with preconditions from the dispatch fields). Both write `.gtm/sales-comp-gate-handoff.json` and end with the line `DONE: gtm`.
- The plugin has no `.mcp.json` file. It starts no outside service.
