# business-case — documentation index

Start with ADR-000. It is the one-page overview of the plugin.

## Diagrams

| File | What it shows |
|---|---|
| [diagrams/context.md](diagrams/context.md) | The user, the coach session, the judge, the guard hooks, the case folder and the product plugin |
| [diagrams/container.md](diagrams/container.md) | The command, the agents, the hooks and their handler, the CLI, every `lib` module, the case files, and how the figures reach the review through `finance.json` |

## Decisions

| ADR | Decision |
|---|---|
| [ADR-000](adr/ADR-000-plugin-architecture-coach-and-gate.md) | Plugin architecture: a coach and a gate, with a wall between them |
| [ADR-001](adr/ADR-001-the-coach-runs-inline-only-the-judge-is-a-sub-agent.md) | The coach runs inline; the sub-agents only read and reply |
| [ADR-002](adr/ADR-002-code-writes-the-judge-brief-and-checks-the-manifest.md) | Code writes the judge brief and checks the manifest |
| [ADR-003](adr/ADR-003-automated-mode-covers-intake-mapping-and-the-judge.md) | Automated mode covers intake, mapping and the judge |
| [ADR-004](adr/ADR-004-the-decision-record-library-lives-in-the-plugin-for-v1.md) | The decision-record library lives in the plugin for v1 |
| [ADR-005](adr/ADR-005-a-decision-cites-the-report-not-the-case.md) | A decision on a finding cites the report, not the case |
| [ADR-006](adr/ADR-006-the-judge-writes-its-own-report.md) | The judge writes its own report; a coach copy cannot end the loop |
| [ADR-007](adr/ADR-007-the-strategy-files-are-hash-chained-and-their-status-is-derived.md) | The strategy files are hash-chained and their status is derived |
| [ADR-008](adr/ADR-008-finding-ids-and-the-whole-plan-findings.md) | Finding IDs and the whole-plan findings |
| [ADR-009](adr/ADR-009-the-financial-figures-file.md) | The financial figures file: its kinds, its twelve checks and the grade rule |
| [ADR-010](adr/ADR-010-the-finance-engine-and-the-verdict-ceiling.md) | The finance engine, the freshness rule and the verdict ceiling |
| [ADR-011](adr/ADR-011-per-version-rubrics-and-the-move.md) | Per-version rubrics and the move to a newer one |
| [ADR-012](adr/ADR-012-the-figure-run-reports-what-it-left-uncovered.md) | The figure run reports what it left uncovered: the `uncovered` record, `figure --clear-refusals` and the extractor's `cannot_read` reply |
| [ADR-013](adr/ADR-013-the-evidence-team.md) | The evidence team: the analysts, the two reply kinds, the card record, the round cap, the budget, the analyst write allow and the grade ceiling |
| [ADR-014](adr/ADR-014-the-plugin-map-and-the-install-check.md) | The plugin map and the install check: the map file, `min_version`, the files Claude Code writes, and each plugin's state |
| [ADR-015](adr/ADR-015-the-case-graph.md) | The case graph: the case folder is the record and the pages are a copy, `publish` at the end of each run, the separate save script, the read of the graphs of 2 other plugins, and the snapshots |
| [ADR-016](adr/ADR-016-the-runner-guard-allows-only-exact-calls.md) | The runner guard: a hook that allows only exact runner script calls in a build session, the `Edit` folder grants, and the temporary folder of each case |
