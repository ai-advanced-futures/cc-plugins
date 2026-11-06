---
name: competitive-intelligence
description: Runs the full competitive analysis in 6 phases, from the first questions to the final deliverables. Use when the person asks for a competitive analysis, a competitor or market assessment, a feature check against competitors, a technology disruption review, win and loss patterns, or a response to a competitive threat.
---

# Competitive intelligence: the full run

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py <args>`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because the shell grant of a runner covers only `git rev-parse`, `date` and `uv run`.
Run every agent you dispatch in the foreground and wait for it to finish.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", because a person who picks such an option gives no value.

For one phase only, use a smaller skill: `discover` (phases 1 to 3), `analyze` (one competitor), `validate`, `respond` or `monitor`.

## The 6 phases

| Phase | Name | Agent | Done line | Needs |
|---|---|---|---|---|
| 1 | Context discovery | `competitive-intelligence:context-analyst` | `DONE: context` | Nothing |
| 2 | Ecosystem mapping | `competitive-intelligence:ecosystem-mapper` | `DONE: ecosystem` | `context-config.json`, or a context that the person gives |
| 3 | Intelligence gathering | `competitive-intelligence:intelligence-gatherer` | `DONE: intelligence` | `competitive-ecosystem.json` |
| 4 | Multi-lens analysis | `competitive-intelligence:lens-executor` | `DONE: lens-analysis` | `intelligence-data.json` |
| 5 | Synthesis and assessment | `competitive-intelligence:synthesizer` | `DONE: synthesis` | The lens outputs |
| 6 | Deliverable generation | `competitive-intelligence:deliverable-generator` | `DONE: deliverables` | The synthesis outputs |

A phase cannot be skipped, because each later phase depends on it; the person can start at a later phase when the files that it needs exist.

## How a phase runs

Ask the person the open questions with `AskUserQuestion` [q: none], dispatch the agent as `competitive-intelligence:<agent>` with `session_id`, `data_dir` and the answers, wait for its `DONE:` line, and show the summary at the checkpoint (Proceed, Adjust or Cancel).
Read `${CLAUDE_PLUGIN_ROOT}/skills/competitive-intelligence/reference/run-rules.md` for the details: the questions, the dispatch fields, no answer, a change request, the checkpoint options, and a failure.

When an agent writes `open-questions.json` in `data_dir` and returns `QUESTIONS: <path>` as its last line, it has no `DONE:` line yet. The file has the shape of `questions/discover.json`:

```json
{
  "schema": "plugin-questions/1",
  "command": "competitive-intelligence:<agent>",
  "questions": [
    {"input": "<name>", "question": "<text>", "type": "choice",
     "options": [{"value": "<value>", "label": "<text>"}], "default": "<value>"}
  ]
}
```

Read the file, ask each question with `AskUserQuestion` [q: none], dispatch the same agent again with each answer as a dispatch field named by its `input`, and repeat until the agent returns its `DONE:` line.

When an agent fails twice, log the failure to `execution-log.md` and ask with `AskUserQuestion` [q: none]: "Phase [X] failed twice. Retry, Skip or Cancel?"
Offer Skip for a lens only, because a phase cannot be skipped.

## Steps

### 0. Read the start time and the version

1. Run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep the output as `started_at`; when `date` is denied or fails, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and use its output. The session folder `{session}` is `started_at` written as `YYYYMMDDTHHMMSSZ`.
2. Read `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and keep its `version`.
3. Run `git rev-parse --show-toplevel` on its own. Its output is the git root; when it fails, the git root is the working directory.

### 1. Orient

1. Read `.competitive-intelligence/{session}/session.json` if it exists, and use its `phases_complete` to find the next phase.
2. If the folder `.competitive-intelligence/{session}/` does not exist but an older run left `.competitive-intel/{session}/session.json`, continue in that old folder. Use it wherever this skill says `.competitive-intelligence/{session}/`. New sessions never go in the old folder.
   - The old name is for old runs only, because the new name replaced it.
3. Read the earlier analyses in both folders `.competitive-intelligence/` and `.competitive-intel/`, newest file first.
4. If no session exists, create `.competitive-intelligence/{session}/session.json` and an empty `execution-log.md` in the same folder:

```json
{
  "session_id": "{session}",
  "mode": "interactive",
  "started_at": "{started_at}",
  "phases_complete": [],
  "lenses_complete": [],
  "current_phase": "context",
  "competitor_count": 0,
  "lens_failures": {},
  "checkpoints_passed": []
}
```

### 2. Phases 1 to 3: discover

Read `${CLAUDE_PLUGIN_ROOT}/skills/discover/SKILL.md` and follow its steps 1 to 7, because step 0 here did its step 0 and this skill writes no result file (its steps 8 and 9).
After each phase, add its name to `phases_complete` in `session.json`, set `current_phase`, add the checkpoint to `checkpoints_passed`, and log the decision to `execution-log.md`.

### 3. Phase 4: multi-lens analysis

Dispatch `competitive-intelligence:lens-executor` with `session_id` and `data_dir`, wait for `DONE: lens-analysis`, add `lens-analysis` to `phases_complete`, and read `lens-analysis-summary.json` in `data_dir`.
The lens executor reads the trigger of the person and runs only the lenses that fit it. The lens executor file is the one place that holds these rules.
CHECKPOINT - Lens findings: show the 6 lens headlines, the cross-validation agreement in percent, and the contradictions, and ask Proceed / Deep dive / Investigate contradictions.

### 4. Phase 5: synthesis

Dispatch `competitive-intelligence:synthesizer` with `session_id` and `data_dir`, wait for `DONE: synthesis`, add `synthesis` to `phases_complete`, and read `synthesis-summary.json`.
CHECKPOINT - Synthesis: show the top recommendations and the SWOT headline, and ask Proceed / Refine.

### 5. Phase 6: deliverables

1. Ask the person: "Which deliverables do you need?" Allow more than one answer [q: deliverables]. The options are:
   - JSON outputs: structured data for automation (default)
   - Python scripts: custom analysis and charts
   - Executive summary: a one-page overview
   - Battle card: a sales enablement card
   - Full report: a complete document
2. Use JSON outputs when the person gives no answer.
3. Dispatch `competitive-intelligence:deliverable-generator` with `session_id`, `data_dir` and `deliverables` (a list of `json_outputs`, `python_scripts`, `executive_summary`, `battle_card`, `full_report`), wait for `DONE: deliverables`, and add `deliverables` to `phases_complete`.

### 6. Show the completion summary

Show the person the length of the analysis, the number of competitors analyzed, the number of key findings, the confidence levels, and the files that the run made, with their paths. The session folder keeps all the files for later use.

## Checkpoints

The person must confirm each phase before the next phase starts, and can adjust, go back or cancel at any time.
Show a summary at each checkpoint and offer more detail to a person who wants it.
