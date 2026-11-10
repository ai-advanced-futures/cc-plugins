# product-finance — C4 Context and Container Diagrams

**Plugin:** product-finance v0.13.4

## C4 Context

```mermaid
C4Context
    title product-finance Plugin Context (v0.13.4)

    Person(engineer, "Product Engineer", "Asks financial questions during product development")
    Person(cfo, "CFO / Finance Lead", "Reviews unit economics, AI ROI, cost-coverage analysis")

    System(product_finance, "product-finance", "AI-aware financial intelligence: unit economics, AI ROI, cost-coverage")

    System_Ext(pricing, "pricing plugin", "Writes agentic-pricing-diagnosis.json and cost-amplifier-readout.json")
    System_Ext(jtbd, "jtbd-market-discovery plugin", "Keeps the jtbd graph that discover reads")
    System_Ext(business_case, "business-case plugin", "Dispatches the runners and reads the result files")

    Rel(engineer, product_finance, "Runs commands", "/product-finance:unit-economics, /product-finance:ai-economics, /product-finance:feature-roi")
    Rel(cfo, product_finance, "Reads outputs", "Markdown and JSON reports")
    Rel(business_case, product_finance, "Dispatches a runner", "plugin-run block with answers_path")
    Rel(product_finance, business_case, "Writes a result file", ".product-finance/results/")
    Rel(pricing, product_finance, "Gives input files", "agentic-pricing-diagnosis.json + cost-amplifier-readout.json")
    Rel(product_finance, jtbd, "Reads the jtbd graph", "scripts/jtbd_read.py")
```

## C4 Container

```mermaid
C4Container
    title product-finance Plugin Containers (v0.13.4)

    Person(engineer, "Engineer / CFO", "")

    Container_Boundary(plugin, "product-finance plugin") {
        Container(agents, "Agents Layer", "11 markdown agents", "ai-economist, financial-analyst, instrumentation-planner, market-analyzer, roi-calculator, cost-coverage-agent; five runners for the adopting commands: discover-runner, feature-roi-runner, unit-economics-runner, ai-economics-runner, cost-coverage-runner")
        Container(commands, "Commands Layer", "9 commands", "ai-economics, discover, feature-roi, health-check, instrumentation, services-model, setup, unit-economics, cost-coverage")
        Container(skills, "Skills Layer", "14 skills", "skills/<group>-<folder>/SKILL.md")
        Container(scripts, "Scripts Layer", "Python scripts", "ai_roi_calculator, market_sizing_calculator, input_check, rule_of_40, simulator, unit_economics, cost_coverage_readout, cost_coverage_core, result_name, bootstrap_cost_coverage_schema_hash")
        Container(schemas, "Schemas", "JSON Schema", "schemas/agentic-pricing/: the three Charter schemas")
    }

    System_Ext(pricing, "pricing plugin", "")
    System_Ext(business_case, "business-case plugin", "")

    Rel(engineer, commands, "Runs")
    Rel(commands, agents, "Dispatches")
    Rel(agents, skills, "Loads")
    Rel(agents, scripts, "Runs", "uv run <plugin root>/scripts/X.py")
    Rel(scripts, schemas, "Checks output against")
    Rel(pricing, scripts, "Gives input files", "diagnosis + amplifier-readout")
    Rel(agents, business_case, "Writes a result file", "audience: internal")
```

## Cost-coverage

The cost-coverage command (v0.4.0) has these parts:
- `cost-coverage-agent`
- `scripts/cost_coverage_readout.py`: the Charter §6.3 re-implementation of S1-S5, the gross margin path, and the multiple compression signals
- `scripts/bootstrap_cost_coverage_schema_hash.py`: the pin of the schema hash
- `.charter-conforms`: it says that the plugin produces `cost-coverage-readout` and consumes `cost-amplifier-readout`
- ADR-002

See `../adr/ADR-002-charter-cost-coverage.md` for the §6.3 re-implementation decision and the source of the +7 step of the vertical archetype.

## Result file (v0.8.0)

Version 0.8.0 adopted the repository result file (ADR-006):
- five runners, `agents/<command>-runner.md`, one for each adopting command: `discover`, `feature-roi`, `unit-economics`, `ai-economics` and `cost-coverage`
- `scripts/cost_coverage_core.py`: the cost-coverage math, with only the standard library
- `result-file.json`, `questions/<command>.json` and the result file in `.product-finance/results/`

## The port (v0.11.0)

Version 0.11.0 moved the plugin into this repository (ADR-006, amendment of v0.11.0). The plugin starts no outside server. No agent asks the person a question. No file reads a path outside the plugin folder.
