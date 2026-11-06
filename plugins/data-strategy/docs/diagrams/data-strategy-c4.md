# data-strategy: C4 diagrams

## C4 level 1: system context

```mermaid
C4Context
  title data-strategy: system context
  Person(user, "Person", "Asks for a data strategy assessment")
  System(ds, "data-strategy", "Assesses the data strategy of a software company")
  System_Ext(web, "Web search", "Public sources for the domain agents")
  Rel(user, ds, "Answers the intake questions, reads the 3 deliverables")
  Rel(ds, web, "Sends search queries")
```

## C4 level 2: containers

```mermaid
C4Container
  title data-strategy: containers
  Person(user, "Person")
  Container(skill, "skills", "5 skills", "Ask the intake questions, write context.yaml, start an agent")
  Container(orch, "orchestrator", "sonnet", "Starts the agents in order, checks the flags")
  Container(strat, "strategy-assessor", "sonnet", "DAMA-DMBOK and Gartner")
  Container(plat, "platform-auditor", "sonnet", "Data Mesh and engineering lifecycle")
  Container(prod, "product-analyst", "sonnet", "Data products and data contracts")
  Container(synth, "synthesizer", "opus", "Two-pass synthesis")
  Container(deliv, "deliverable-generator", "sonnet", "Writes 3 deliverables")
  Container(scripts, "scripts", "Python, uv run", "Scores, roadmap groups, session flags")
  ContainerDb(files, ".data-strategy-tmp/", "File system", "Session files and .done flags")
  Rel(user, skill, "Answers the questions")
  Rel(skill, files, "Writes context.yaml and session.json")
  Rel(skill, orch, "Starts, full run")
  Rel(skill, strat, "Starts, one domain")
  Rel(skill, plat, "Starts, one domain")
  Rel(skill, prod, "Starts, one domain")
  Rel(skill, deliv, "Starts, roadmap only")
  Rel(orch, strat, "Step 2, 3 calls in one message")
  Rel(orch, plat, "Step 2, 3 calls in one message")
  Rel(orch, prod, "Step 2, 3 calls in one message")
  Rel(orch, synth, "Step 3")
  Rel(orch, deliv, "Step 4")
  Rel(strat, scripts, "Runs dama_scorer, maturity_calculator")
  Rel(plat, scripts, "Runs data_mesh_evaluator")
  Rel(prod, scripts, "Runs product_portfolio_scorer")
  Rel(synth, scripts, "Runs roadmap_builder")
  Rel(strat, files, "Writes strategy.md and strategy.done")
  Rel(plat, files, "Writes platform.md and platform.done")
  Rel(prod, files, "Writes products.md and products.done")
  Rel(synth, files, "Reads the 3 domain files, writes synthesis.md")
  Rel(deliv, files, "Reads synthesis.md, writes 3 deliverables")
```
