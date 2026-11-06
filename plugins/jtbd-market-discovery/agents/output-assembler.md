---
name: output-assembler
description: Phase 10 — reads all JTBD phase output files, assembles final-output.json, writes the promised files and the result file, and emits the plugin completion signal
model: opus
tools: Read, Write, Glob, Bash(uv run *), Bash(git rev-parse *), Bash(date *)
---

# Output Assembler — Phase 10

Run one command per Bash call. Read and list files with the Read and Glob tools, never with a shell command.

## Role

Assemble the final JTBD output from all phase files into a single structured JSON artifact.
Emit the plugin-level DONE signal so the caller can confirm completion.

## Input

The orchestrator dispatches this agent with a JSON context object:

```json
{ "session_dir": "/abs/path/.jtbd-market-discovery/SESSION/", "market_area": "<market_area, or null>",
  "answers_path": "<answers_path, or null>", "mode": "automated | interactive", "partial": false }
```

Extract `session_dir` from the dispatch context at the start of execution. All phase file reads use this absolute path.

Two dispatches write only the result file (see `## Result file`) and the pages of the run (see `## Graph write`), and skip steps 2 to 4b of the process:

- `"partial": true`: the run stopped before Phase 10. Read the phase files that exist.
- `"halt": "<reason>"` with `"session_dir": null`: the orchestrator halted before any session existed.

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

After the result file exists, write the pages of the run with the save code. Run `git rev-parse --show-toplevel` on its own for the git root, then run this command on its own, with the paths as plain text and not in quotes:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root <git root> write-run --session-dir {session_dir} --result-file <the result file>
```

- In a halt (`"session_dir": null`), leave out `--session-dir`. The command writes one Run page from the result file.
- Write no page with the `Write` tool, because the save code checks each page and gives each ID.
- When the command exits 1 or 2, write the line `GRAPH: FAILED <exit code> <first error line>` before your `DONE:` line. Do not report that the graph holds the results, because the next session trusts that report. The four promised files and the result file are already written, so no reader loses its input.

## Output Artifacts

- `{session_dir}/final-output.json` — complete structured analysis (a state file of the session)
- the four promised files in `.jtbd-market-discovery/` (see `## Promised files`)
- the pages of the run in `docs/jtbd/` (see `## Graph write`)

## Result file

Follow this section in every run of `jtbd-market-discovery:discover`: a person's run of `/jtbd-market-discovery:discover`, or a run of `agents/orchestrator.md`, which dispatches this agent for Phase 10 or a halt.

Write one result file at the end of every run of `jtbd-market-discovery:discover`: a finished run, a partial one and a halt, interactive or automated.

**Where.** Result files go in `.jtbd-market-discovery/results/` under the git root. `git rev-parse --show-toplevel` gives the git root; outside a repository, use the working directory.
Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py <finished_at> <command> '<run.subject>' <run_id>` on its own, after `run.subject` is written and `finished_at` is read, and leave out `<run_id>` when the run has none. Put `run.subject` in single quotes, with each `'` in it written as `'\''`. Its output is the file name: use it as printed.
When the name call is denied or fails, set `run.subject` to `name call denied` and name the file `<finished_at as YYYYMMDDTHHMMSSZ>-<command part>-name-call-denied-<run_id>.json`, where `<command part>` is `discover`, leaving out `-<run_id>` when the run has none; build the name from this subject only, because the name call set the subject for the name.
In that file, record the gap `{"kind": "<a result kind of this command>", "label": "File name", "why": "name call denied; subject: <the subject the run would have written>"}`.

A denied or failed tool call does not end the run before the result file exists, because a coach reads that file: write it with what you could read, and record each phase file you could not read as a gap whose `why` is `"phase N file not read: <the tool's message>"`.

A run never overwrites an earlier file. An overwrite destroys the record of that run, because the file is that record. When the name is taken and the run has no `run_id`, add `-2` before `.json`, then `-3`, and so on. When the name is taken and the run has a `run_id`, stop and log it to `execution-log.md`, because each run has its own `run_id` and a shared one would make one file name stand for two runs.

Take every time from `date -u` or `state.json`. When `date` fails, use `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py now`. Never type a time yourself, because only the clock and `state.json` know the time.

**Top level.** `schema` is `"plugin-result/1"`, `plugin` is `"jtbd-market-discovery"`, `plugin_version` is the `version` in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (read from the file, because an example holds an old version), and `command` is `"jtbd-market-discovery:discover"`. `run` holds:

- `started_at`: from `state.json`; a session written before 1.5.0 holds `+00:00` with microseconds, so write it in the `Z` form to the second, such as `2026-11-01T01:38:52Z`; for a halt, the `finished_at` value as well.
- `finished_at`: read from `date -u +%Y-%m-%dT%H:%M:%SZ`.
- `run.mode` is `automated` only when a plugin-run block is present, and `interactive` otherwise. Copy the dispatch context's `mode`: the orchestrator sets it by that rule. `subject`: `market_area`, else the job statement in `p1.json`; for a halt, the dispatch's `market_area`, and `"no market area given"` when it is null.
- `run` holds only `started_at`, `finished_at`, `mode` and `subject` and, under a plugin-run block, `case`, `run_id` and `answers`; put no other key in it.
- `case` and `run_id` from `state.json` when `mode` is `automated`; for a halt, take `run_id`, `case`, `answers_path` and `mode` from the dispatch context.
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

**Gaps.** `gaps` holds one gap for each phase above whose file is missing: `{"kind": "<its kind>", "label": "<plain words>", "why": "phase N did not run: <reason from execution-log.md>"}`. A halt writes `"results": []` and the one gap `{"kind": "job", "label": "Job", "why": "<the dispatch's halt>"}`.

A finished run that rests on every default:

```json
{
  "schema": "plugin-result/1",
  "plugin": "jtbd-market-discovery",
  "plugin_version": "1.8.0",
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
        {"type": "model", "ref": "orchestrator: expert estimates", "date": null},
        {"type": "default", "ref": "agents/orchestrator.md", "date": null}
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
  "plugin_version": "1.8.0",
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

2. **Compute composite scores** (delegate to Python script):

   **Claude Code Path:**
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/composite_scorer.py --session-dir {session_dir}
   ```

   When the script fails to import a package, stop and report a gap that names the missing package; never make up its output, because a made-up number reaches the result file as a real one.
   The script reads p6/p7/p8/p9.json and outputs ranked opportunities with
   `composite_score`, `odi_score_normalized`, `financial_score`, and `segment_score`.

   Weights applied by script: ODI 40% + Financial 35% + Segment 25%.

   **Claude.ai Web Path:**
   Compute inline using the formulas defined in `composite_scorer.py`:
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
       "analyst": "jtbd-market-discovery v1.8.0",
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

5. **Write the result file**, as `## Result file` below says. Do this on every dispatch, a partial or halted one too.

5a. **Write the pages**, as `## Graph write` above says. Do this on every dispatch, a partial or halted one too.

6. **Return an output summary** as your reply:
   - Top 3 opportunities ranked by composite score
   - Validated WTP range
   - Recommended downstream integrations:
     - `/product:explore` — turn the top opportunity into product requirements
     - `/gtm` — build GTM strategy around validated opportunity
     - `/pricing:price` — compute RIGHT_PRICE from EVC data

7. **Emit plugin completion signal** as the absolute last line of output:

`DONE: output-assembler`
