# Product Finance: Documentation Index

This index lists each document in `plugins/product-finance/docs/`.

## Architecture Decision Records (`adr/`)

The numbers 003 and 004 are not used. The plugin does not have those decisions.

| ADR | Topic |
|-----|-------|
| [ADR-001](adr/ADR-001-product-finance-architecture.md) | The plugin architecture: commands, agents, skills, and scripts |
| [ADR-002](adr/ADR-002-charter-cost-coverage.md) | The cost-coverage readout: the math is in this plugin, and the vertical archetype has a +7 step |
| [ADR-005](adr/ADR-005-magic-number-canonicalization.md) | Magic Number: one source of truth in `scripts/utils/magic_number.py` |
| [ADR-006](adr/ADR-006-plugin-result-file.md) | The result file: five runners, stated defaults, the standard-library cost-coverage command, discover checks its result file (amendment v0.13.0), every jtbd read is a read of the jtbd graph (amendment v0.12.0) |
| [ADR-007](adr/ADR-007-assumptions-input-contract.md) | The assumptions input contract: one loader, a mapping table, no invented values, and exit code 3 |
| [ADR-008](adr/ADR-008-shared-input-checker.md) | The shared standard-library input checker: its limits, the go-together rule, plain reasons, and exit code 3 for a refused input |

## Methodology and Reference

| Document | Purpose |
|----------|---------|
| [METHODOLOGY.md](METHODOLOGY.md) | The SaaS metrics methodology and its sources |
| [KPI_DEFINITIONS.md](KPI_DEFINITIONS.md) | The board-level KPI definitions |
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | How the plugin works with the jtbd-market-discovery plugin |

## Diagrams

| Diagram | View |
|---------|------|
| [product-finance-c4-context.md](diagrams/product-finance-c4-context.md) | C4 context diagram |

---

For the commands, the use cases, and the data model, see [`../README.md`](../README.md).
