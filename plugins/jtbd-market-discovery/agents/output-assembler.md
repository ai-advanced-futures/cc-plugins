---
name: output-assembler
description: Phase 10 — reads all JTBD phase output files, assembles final-output.json, writes the promised files and the result file, and emits the plugin completion signal
model: opus
tools: Read, Write, Glob
---

# Output Assembler — Phase 10

This agent runs no command. The skill that starts it runs the scripts: `composite_scorer.py` before this agent, and `jtbd_state.py place-result` and `jtbd_graph.py write-run` after it. Read and list files with the Read and Glob tools.

## Role

Assemble the final JTBD output from all phase files into a single structured JSON artifact, and write the draft of the result file.
Emit the plugin-level DONE signal so the caller can confirm completion.

## Input

The skill starts this agent with a JSON context object:

```json
{ "session_dir": "/abs/path/.jtbd-market-discovery/SESSION/", "market_area": "<market_area, or null>",
  "answers_path": "<answers_path, or null>", "mode": "automated | interactive", "partial": false,
  "composite_path": "<session_dir>/composite-scores.json, or null", "composite_gap": "<message, or null>" }
```

Extract `session_dir` from the dispatch context at the start of execution. All phase file reads use this absolute path.

One dispatch writes only the result draft (see `## Result file`), and skips steps 2 to 4b of the process: `"partial": true`, the run stopped before Phase 10. Read the phase files that exist. A halt has no session, so the skill writes the draft of a halt itself.

## Promised files

`${CLAUDE_PLUGIN_ROOT}/skills/discover/SKILL.md`, section Deliverables, promises four files. Write them to the `.jtbd-market-discovery/` folder two levels above `session_dir` (`session_dir/../../.jtbd-market-discovery/`). Write nothing into `.jtbd/`, because a new run reads that folder only as a fallback.

Other plugins read these four files today. The graph in `docs/jtbd/` holds the same values (see `## Graph write`). Write no other file of the run into `.jtbd-market-discovery/`, because the graph holds the job, the steps and the segments.

Each file holds the content of its source file. It also holds four top-level keys that identify the run. A key from the source file with the same name is replaced.

- `subject`: the `market_area` of the dispatch context; when absent, the `job_statement` of `p1.json`.
- `session_id`: `session_id` from `state.json` of `session_dir`.
- `case`: `case` from `state.json`; `null` when absent.
- `run_id`: `run_id` from `state.json`; `null` when absent.

When a source file holds a list and not an object, the file holds the list under the key `items`.

| File | Source |
|---|---|
| `customer-needs.json` | `p3.json` |
| `opportunity-scores.json` | `p6.json` |
| `evc-analysis.json` | `p7.json` |
| `wtp-validation.json` | `p9.json` |

A later run overwrites these files.

## Graph write

The skill writes the pages of the run after `place-result` has written the result file (`jtbd_graph.py write-run`). This agent writes no page and runs no command, because the save code checks each page and gives each ID. Write no page with the `Write` tool.

## Output Artifacts

- `{session_dir}/final-output.json` — complete structured analysis (a state file of the session)
- the four promised files in `.jtbd-market-discovery/` (see `## Promised files`)
- `{session_dir}/result-draft.json` — the result file without `run.finished_at` (see `## Result file`)

## Result file

Follow this section in every run of `jtbd-market-discovery:discover`: a person's run of `/jtbd-market-discovery:discover`, or a plugin run. The skill `skills/discover/SKILL.md` starts this agent for Phase 10 and for a partial run.

Write the draft of the result file at the end of every run of `jtbd-market-discovery:discover`: a finished run and a partial one, interactive or automated.

**Where.** Write the draft to `{session_dir}/result-draft.json` with the Write tool. The skill runs `jtbd_state.py place-result` on the draft. That script sets `run.finished_at`, names the file, and writes it to `.jtbd-market-discovery/results/` under the git root. It never overwrites an earlier file, because the file is the record of that run. Do not write `run.finished_at`, a file name, or a time, because the script reads the clock and this agent has none.

A failed read does not end the run before the draft exists, because a coach reads the result file: write the draft with what you could read, and record each phase file you could not read as a gap whose `why` is `"phase N file not read: <the tool's message>"`.

**Top level.** `schema` is `"plugin-result/1"`, `plugin` is `"jtbd-market-discovery"`, `plugin_version` is the `version` in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (read from the file, because an example holds an old version), and `command` is `"jtbd-market-discovery:discover"`. `run` holds:

- `started_at`: from `state.json`; a session written before 1.5.0 holds `+00:00` with microseconds, so write it in the `Z` form to the second, such as `2026-11-01T01:38:52Z`.
- `finished_at`: leave it out. `place-result` sets it.
- `run.mode` is `automated` only when a plugin-run block is present, and `interactive` otherwise. Copy the dispatch context's `mode`: the skill sets it by that rule. `subject`: `market_area`, else the job statement in `p1.json`.
- `run` holds only `started_at`, `mode` and `subject` and, under a plugin-run block, `case`, `run_id` and `answers`; put no other key in it. `place-result` adds `finished_at`.
- `case` and `run_id` from `state.json` when `mode` is `automated`.
- `answers`: the `answers_path`. With no plugin-run block, leave out `case`, `run_id` and `answers`, because a file the run read can hold the values of another run. Leave out a key that has no value.

**Results.** Each result has `id`, `kind`, `label`, `value`, `sources`, `method`, `rests_on_default`, `defaults` and `detail`. Copy each number and string from its phase file as written. Compute, round and estimate nothing, because the phase file is the source of each number and a coach checks the result file against it. Leave out a key of `value` that has no number; never write `null` there, because a coach reads each key of `value` as a number.
A `willingness_to_pay` result needs at least one of `point`, `low` and `high`: for a segment with none, write no result and add a gap:

| Kind | One per | From | `value` | `unit`, `period` |
|---|---|---|---|---|
| `job` | run | `p1.json` | the job statement | none |
| `job_step` | step | `p2.json` | `{"order", "step"}` | none |
| `opportunity_score` | top 10 need | `p6.json` | `{"need", "importance", "satisfaction", "score"}` | none |
| `customer_value` | run | `p7.json` | `total_annual_evc` of the `rank: 1` opportunity | `"USD"`, `"year"` |
| `customer_segment` | segment | `p8.json` | `{"name"}` | none |
| `willingness_to_pay` | segment | `p9.json` | `{"point", "low", "high", "segment"}` | `"USD"`, `"month"` |

`detail` is the phase file in the run's own session, relative to the git root: `.jtbd-market-discovery/<session_id>/pN.json`. It never names the eight promised files at the folder root. A resumed old session keeps its place: the result file still goes to `.jtbd-market-discovery/results/`, and its `detail` names that old session, `.jtbd/<session_id>/pN.json`.

**Sources and defaults.** Every result has a `model` source for what the agents inferred, and a `customer_data` source with the survey file as `ref` when `p5.json` names one.
When the answers file gave `market_area`, the `job` result also has the source `{"type": "person", "ref": "answers:market_area", "date": null}`, or the `default` source of that ref when `settled_by` is `recommended`. The phase files record how each input was settled under `assumption_sources`, one plain string per input:

| `assumption_sources` value | Source | Marker in `defaults` |
|---|---|---|
| `person` | `{"type": "person", "ref": "answers:<input>", "date": null}` | no |
| `recommended` | `{"type": "default", "ref": "answers:<input>", "date": null}` | no |
| `asked` | `{"type": "person", "ref": "asked in this run: <input>", "date": null}` | no |
| `model` | `{"type": "model", "ref": "<agent>: <input>", "date": null}` | no |
| `default` | `{"type": "default", "ref": "agents/<agent>.md", "date": null}` | yes |

The markers, and the results that carry them:

| Input | File | Marker | Results |
|---|---|---|---|
| `ratings_source` | `p5.json` | `importance_satisfaction = expert estimates` | `opportunity_score` |
| `labor_rate` | `p7.json` | `labor_rate = 75` | `customer_value` |
| `average_error_cost` | `p7.json` | `average_error_cost = 50` | `customer_value` |
| `average_revenue` | `p7.json` | `average_revenue = 5000` | `customer_value` |
| `revenue_margin` | `p7.json` | `revenue_margin = 0.20` | `customer_value` |
| `risk_tolerance` | `p7.json` | `risk_tolerance = moderate` | `customer_value` |
| `segment_count` | `p8.json` | `segment_count = 4` | `customer_segment` |

In a person's run, a value the run takes from another plugin's file, or from an earlier run's file, is a `default` source with `ref` `<file>: <key>`, and its marker is `<input> = <value> (<file>)`.
In a person's run, an answer the person picked from an option labelled as the default or as recommended is a `default` source with `ref` `asked in this run: <input>`, and that default's marker goes in `defaults`.
The expert-estimates marker applies only when `p5.json` has `"method": "expert"`. An input in the markers table that its phase file does not record under `assumption_sources` counts as `default`. `rests_on_default` is true when a source has type `default`. It is also true when the `defaults` list of marker strings is not empty; otherwise it is false.

**Gaps.** `gaps` holds one gap for each phase above whose file is missing: `{"kind": "<its kind>", "label": "<plain words>", "why": "phase N did not run: <reason from execution-log.md>"}`. When the dispatch has `composite_gap`, add the gap `{"kind": "opportunity_score", "label": "Ranking", "why": "<composite_gap>"}`.

A finished run that rests on every default:

```json
{
  "schema": "plugin-result/1",
  "plugin": "jtbd-market-discovery",
  "plugin_version": "1.9.1",
  "command": "jtbd-market-discovery:discover",
  "run": {
    "started_at": "2026-10-31T09:00:00Z",
    "finished_at": "2026-10-31T09:15:00Z",
    "mode": "automated",
    "subject": "Invoice automation for mid-size finance teams",
    "case": "business-cases/acme",
    "run_id": "acme-0006"
  },
  "results": [
    {
      "id": "opportunity-1",
      "kind": "opportunity_score",
      "label": "Opportunity: fewer invoice keying errors",
      "value": {"need": "Minimize the number of invoices keyed by hand", "importance": 9, "satisfaction": 3, "score": 15},
      "sources": [
        {"type": "model", "ref": "skill: expert estimates", "date": null},
        {"type": "default", "ref": "skills/discover/SKILL.md", "date": null}
      ],
      "method": "ODI score from importance and satisfaction estimated without a survey.",
      "rests_on_default": true,
      "defaults": ["importance_satisfaction = expert estimates"],
      "detail": ".jtbd-market-discovery/acme-0006/p6.json"
    },
    {
      "id": "value-1",
      "kind": "customer_value",
      "label": "Customer value of the top opportunity",
      "value": 6180,
      "unit": "USD",
      "period": "year",
      "sources": [
        {"type": "model", "ref": "evc-calculator: time and error value", "date": null},
        {"type": "default", "ref": "agents/evc-calculator.md", "date": null}
      ],
      "method": "Time, error, revenue and risk value of the top opportunity, at the default rates.",
      "rests_on_default": true,
      "defaults": ["labor_rate = 75", "average_error_cost = 50", "average_revenue = 5000",
                   "revenue_margin = 0.20", "risk_tolerance = moderate"],
      "detail": ".jtbd-market-discovery/acme-0006/p7.json"
    },
    {
      "id": "segment-1",
      "kind": "customer_segment",
      "label": "Segment: high-volume payables teams",
      "value": {"name": "High-volume payables teams"},
      "sources": [
        {"type": "model", "ref": "segmentation-analyst: segments", "date": null},
        {"type": "default", "ref": "agents/segmentation-analyst.md", "date": null}
      ],
      "method": "Segments drawn from the estimated ratings, starting from the default count.",
      "rests_on_default": true,
      "defaults": ["segment_count = 4"],
      "detail": ".jtbd-market-discovery/acme-0006/p8.json"
    }
  ],
  "gaps": []
}
```

A run whose answers file gave the labor rate (`settled_by: person`), so `labor_rate = 75` is not in `defaults` (only that result shown):

```json
{
  "schema": "plugin-result/1",
  "plugin": "jtbd-market-discovery",
  "plugin_version": "1.9.1",
  "command": "jtbd-market-discovery:discover",
  "run": {
    "started_at": "2026-10-31T09:00:00Z",
    "finished_at": "2026-10-31T09:15:00Z",
    "mode": "automated",
    "subject": "Invoice automation for mid-size finance teams",
    "case": "business-cases/acme",
    "run_id": "acme-0008",
    "answers": "/abs/business-cases/acme/team/answers-002.json"
  },
  "results": [
    {
      "id": "value-1",
      "kind": "customer_value",
      "label": "Customer value of the top opportunity",
      "value": 7400,
      "unit": "USD",
      "period": "year",
      "sources": [
        {"type": "model", "ref": "evc-calculator: time and error value", "date": null},
        {"type": "person", "ref": "answers:labor_rate", "date": null},
        {"type": "default", "ref": "agents/evc-calculator.md", "date": null}
      ],
      "method": "Time, error, revenue and risk value of the top opportunity, at the person's labor rate and the default other rates.",
      "rests_on_default": true,
      "defaults": ["average_error_cost = 50", "average_revenue = 5000", "revenue_margin = 0.20", "risk_tolerance = moderate"],
      "detail": ".jtbd-market-discovery/acme-0008/p7.json"
    }
  ],
  "gaps": []
}
```

## Process

1. **Read all phase outputs from `session_dir`:**
   - p1.json — job identification
   - p2.json — job decomposition
   - p3.json — customer needs (merged from batches)
   - p4.json — effort quantification
   - p5.json — survey design / expert estimates
   - p6.json — opportunity scores (ODI)
   - p7.json — EVC calculation
   - p8.json — segmentation
   - p9.json — WTP validation

2. **Read the composite scores:**

   **With `composite_path`:** read the file. The skill ran `scripts/composite_scorer.py`, which wrote a list of ranked opportunities with `composite_score`, `odi_score_normalized`, `financial_score`, and `segment_score`. Use these numbers as they are, and compute none of them, because the script is the source of each number.

   Weights applied by the script: ODI 40% + Financial 35% + Segment 25%.

   **With no `composite_path`** (the script failed, or the run is partial): record the `composite_gap` as a gap, and rank the opportunities inline with the formulas of `composite_scorer.py`, labeled as an estimate:
   - ODI Score = `opportunity_score / 20 × 100`
   - Financial Score = `need_total_annual_evc / max(all_evc) × 100`
   - Segment Score = `(size_percent / 100) × confidence_weight × 100`
   - Composite = `(ODI × 0.4) + (Financial × 0.35) + (Segment × 0.25)`

3. **Assemble `final-output.json`** using this schema:

   ```json
   {
     "analysis_metadata": {
       "date": "YYYY-MM-DD",
       "job_statement": "...",
       "respondents": 87,
       "analyst": "jtbd-market-discovery v1.9.1",
       "session_dir": "..."
     },
     "job_steps": [...],
     "customer_needs": [...],
     "top_opportunities": [
       {
         "rank": 1,
         "need": "...",
         "importance": 9.0,
         "satisfaction": 2.0,
         "odi_score": 16.0,
         "composite_score": 87,
         "evc_monthly": 1530,
         "wtp_validated": 75,
         "segment": "Crisis Avoiders (43%)"
       }
     ],
     "segments": [...],
     "evc_analysis": {
       "baseline_evc": 0,
       "premium_evc": 0,
       "components": []
     },
     "wtp_validation": {
       "result": "PASS|CHALLENGED|FAIL",
       "validated_wtp": 75,
       "confidence": "high"
     },
     "recommendations": [...]
   }
   ```

4. **Write `final-output.json`** to `session_dir`.

4a. **Validate assembled output** before proceeding:
   - Verify `top_opportunities` list has at least 1 entry
   - Verify `wtp_validation.result` is one of: `PASS`, `CHALLENGED`, `FAIL`
   - Verify `final-output.json` file exists on disk (read it back to confirm)
   - If any check fails: log error to `execution-log.md` in `session_dir`, report
     with message: "Output assembly incomplete — see execution-log.md", then go to step 5. Write the result file as a partial run.

4b. **Write the promised files** to `.jtbd-market-discovery/`, as the `## Promised files` section above says.

5. **Write the result draft**, as `## Result file` above says. Do this on every dispatch, a partial one too.

6. **Return an output summary** as your reply:
   - Top 3 opportunities ranked by composite score
   - Validated WTP range
   - Recommended downstream integrations:
     - `/product:explore` — turn the top opportunity into product requirements
     - `/gtm` — build GTM strategy around validated opportunity
     - `/pricing:price` — compute RIGHT_PRICE from EVC data

7. **Emit plugin completion signal** as the absolute last line of output:

`DONE: output-assembler`
