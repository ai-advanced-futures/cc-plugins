# Pricing Plugin — C4 Diagrams

> Charter §13 acceptance criterion — every plugin with >1 agent OR a Python package needs a Context + Container diagram.

## C4 Context

```mermaid
C4Context
  title Pricing Plugin — Context

  Person(operator, "Operator", "PE OP / CPO / pricing strategist")

  System_Boundary(repo, "The pricing plugin folder") {
    System(pricing, "pricing plugin", "EVC + Amadeo formulas; Charter §7 schemas")
    System(libs, "vocabulary_linter", "Package in the plugin — vocabulary discipline")
    SystemDb(schemas, "schemas/agentic-pricing", "7 handoff schemas + vocabulary + pattern catalogue")
  }

  System_Ext(jtbd, "jtbd-market-discovery", "Upstream — outcome data")
  System_Ext(ci, "competitive-intelligence", "Sibling — vendor archetypes")
  System_Ext(pf, "product-finance", "Downstream — cost coverage")
  System_Ext(tc, "Contract tools", "Downstream — clause packages")

  Rel(operator, pricing, "Invokes via Skills + agents")
  Rel(pricing, schemas, "Validates handoffs against")
  Rel(pricing, libs, "Lints agent prose via")
  Rel(jtbd, pricing, "Feeds outcome + WTP data")
  Rel(pricing, pf, "Emits cost-amplifier-readout")
  Rel(pricing, tc, "Emits pattern-selection")
  Rel(ci, pricing, "Provides vendor-archetype-classification")
```

## C4 Container

```mermaid
C4Container
  title Pricing Plugin — Container (v1.3.0)

  Container_Boundary(plugin, "plugins/pricing") {
    Container(agents, "agents/", "Markdown agents", "new-offering-pricer, pricing-auditor (both audience: internal)")
    Container(skills, "skills/", "Skill prose", "value-metric, price, package, audit")
    Container(scripts, "scripts/", "Python package", "pricing_calculator.py, pricing_constants.py, vocabulary_linter.py CLI")
    ContainerDb(tests, "tests/", "pytest", "280 tests + 4 charter test modules + conftest")
    ContainerDb(fixtures, "tests/fixtures/agentic-pricing/", "JSON", "3 handoff artifact fixtures")
    Container(adrs, "docs/adr/", "Markdown", "ADR-001, ADR-007")
    ContainerDb(sentinel, ".charter-conforms", "Plain text", "Charter §11.3.1.1 — schemas pricing produces/consumes")
  }

  Container_Boundary(workspace, "vocabulary_linter") {
    Container(linter_pkg, "vocabulary_linter/", "Python package", "vocabulary.py, terminals.py, __init__.py")
  }

  ContainerDb_Ext(repo_schemas, "schemas/agentic-pricing", "Canonical schemas")
  ContainerDb_Ext(attribution, "ATTRIBUTION.md", "Source attribution + sha256 drift detection")

  Rel(agents, skills, "Invokes Skills (no Task dispatch)")
  Rel(scripts, repo_schemas, "Reads via _load_vocab()")
  Rel(linter_pkg, repo_schemas, "Reads vocabulary.yaml + pattern_catalogue.yaml")
  Rel(tests, repo_schemas, "Validates fixtures against schemas")
  Rel(tests, attribution, "Asserts ATTRIBUTION.md + sha256 drift")
```

## Notes

- pricing v1.3.0 (Charter PR) ships the federation infrastructure. Canonical math (amplifier_composer, value_metric_tree, etc.) lands in pricing v1.4.0 sub-spec.
- `audience: internal` on both agents — outputs are operator-facing diagnostics, not customer-facing artifacts.
- The `.charter-conforms` sentinel makes pricing the bootstrap conforming plugin for `test_charter_cross_plugin.py`.
