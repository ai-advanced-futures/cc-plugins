# ADR-003 — Parallel batch of agent calls in one message

**Status:** Accepted

## Context

The audit starts one `fact-extractor` for each source, then one `coverage-checker` for each source. The calls for one wave are independent, so they can run in parallel. A design with background jobs and messages between turns is too complex for the usual case of 5 sources or fewer.

## Decision

The orchestrator makes all calls of one wave with the `Agent` tool, in ONE message. Claude Code runs them in parallel. The orchestrator sees all results in its next message. The orchestrator does not use `run_in_background`, does not send messages between agents, and does not poll for results. It is a thin coordinator: it never reads the output files of the sub-agents.

The agent names are `grounded-synthesis:fact-extractor` and `grounded-synthesis:coverage-checker`. A plugin agent registers with the plugin name in front, so a bare name finds no agent.

## Consequences

The orchestrator text is short and has no polling loop. The `run_in_background` pattern is forbidden. A doc-contract test protects the rule that the orchestrator does not read the output files.
