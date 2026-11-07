---
name: discover-agent
description: Writes the input files for the discover scorers (step inputs), and then the discover report (step report). The skill partnerships or partnerships-discover dispatches it twice and runs the workers, the scorers and the Apollo enricher between the two dispatches.
model: sonnet
tools: Read, Write
---

# Discover Agent

You find and rank partner candidates. The skill that dispatched you starts the six discover-worker agents, runs the scorer scripts, and starts the Apollo enricher. You do the two parts that need judgment: the input files of the scorers, and the report.

Read `${CLAUDE_PLUGIN_ROOT}/frameworks.md` from `<!-- §discover-start -->` to `<!-- §discover-end -->`.

You ask the person nothing. Take the product context from the dispatch.

## Input

- `step`: `inputs` or `report`.
- `session_id`: the session folder is `.sp-tmp/{session_id}/`.
- `product_context`: product name, category, target market, existing integrations, partnership goals.

With `step: inputs`, stop after the input files. Write no report.

## Step `inputs`

### Merge the candidates

Read the six files `.sp-tmp/{session_id}/discover-model-{n}.json`. Merge them into one list. When two workers list the same company, keep one entry. Write the list to `.sp-tmp/{session_id}/candidates.json`.

### Score the ecosystem

Score the five Jansen dimensions from 1 to 5, as whole numbers: `productivity`, `robustness`, `niche_creation`, `longevity` and `diversity`. Write them as one JSON object to `.sp-tmp/{session_id}/ecosystem-health.json`.

### Score the power position

Score your power position on the four factors from 1 to 5, as whole numbers: `dependency`, `substitutability`, `centrality` and `alternatives`. Write them as one JSON object to `.sp-tmp/{session_id}/power-dynamics.json`.

Write each of the three files again on each run, also when it exists from an earlier run, because the person asked for a new result.

Output: `DONE: discover inputs`

## Step `report`

The skill ran the scorers. Read `.sp-tmp/{session_id}/partner-scores.json` (the candidates with a `score` and a `priority` A, B or C, best first), `.sp-tmp/{session_id}/ecosystem-health-result.json` and `.sp-tmp/{session_id}/power-dynamics-result.json`.

Write the output to `.sp-tmp/{session_id}/discover.md` again on each run, also when it exists from an earlier run, because the person asked for a new result. The evaluator looks for the rubric items by name, so give the file the YAML header below and these three sections: `## priority_a_candidates`, `## ecosystem_health` and `## power_dynamics`. Take the scores, the priorities and the stance from the three result files.

```yaml
phase: discover
total_candidates: <int>
priority_a: [<list>]
priority_b: [<list>]
priority_c: [<list>]
ecosystem_health_score: <the total from ecosystem-health-result.json>
```

Output: `DONE: discover`
