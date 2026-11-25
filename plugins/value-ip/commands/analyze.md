---
name: value-ip:analyze
description: Full multi-agent debate analysis of any artifact — detects true differentiating value and IP claims
agent: synthesizer
allowed-tools: Task(*), Read(*), Write(*), Glob(*), Grep(*), AskUserQuestion(*), Bash(date *), Bash(git rev-parse *), Bash(python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# /value-ip:analyze

Run only this plugin's own scripts, as `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py" ...`, one command per Bash call. Run no inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), write no script of your own to run, and write every file with the Write tool, because the grants of this command allow nothing else.
Run every agent you dispatch in the foreground and wait for it to finish. A background run (`run_in_background: true`) ends after the command's turn, so the result file would not be written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values. An option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", gives the person no value to pick, so leave it out.

## Purpose

Run the full multi-agent debate analysis on any artifact (plan, PRD, code, competitive analysis, or M&A document) to determine true differentiating value and IP claims.

## Step 0: Load Config and Initialize Pipeline State

**Read the start time and the version** — run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep it as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. When a `date` call is denied or fails, run `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py" now` on its own and use its output as that time.

**Choose the work folder** — The work folder is `.value-ip/<run_id>/` in a plugin run and `.value-ip/<started_at as YYYYMMDDTHHMMSSZ>/` in a person's run, under the git root (run `git rev-parse --show-toplevel` as written, with no `-C` and no path, on its own; when it fails, use the working directory). Write `.value-ip-state.json`, `debate-context/` and `output/` there, so that the working directory stays clean, and name the work folder in every dispatch.

**Read config** — use the Read tool on `${CLAUDE_PLUGIN_ROOT}/config/pipeline-defaults.json`. If the file does not exist or cannot be read, use these defaults:

```json
{
  "auto_mode": false,
  "auto_answers": {
    "artifact_selection": "auto-detect",
    "multiple_artifacts_policy": "ask",
    "continue_rounds_policy": "stop_if_no_tensions",
    "framework_failure_policy": "skip_and_continue",
    "commit_output": false,
    "output_format": "both"
  },
  "pipeline": { "max_rounds": 4, "min_rounds": 2 }
}
```

Store `auto_mode` (boolean) and `auto_answers` in working memory for use throughout this command. When the dispatch context holds a `plugin-run` block, the invocation block wins over the config's `auto_mode`: run as if `auto_mode` were `true`.

**Initialize pipeline state** — at the start of Step 3, once the artifact is known, use the Write tool to write `.value-ip-state.json` in the work folder, with `artifact_path` and `artifact_type` set:

```json
{
  "version": "1.1.0",
  "phase": "INIT",
  "round": 0,
  "max_rounds": 4,
  "artifact_path": null,
  "artifact_type": null,
  "framework_results": {
    "helmer": "pending",
    "blue_ocean": "pending",
    "christensen": "pending",
    "moore": "pending"
  },
  "unresolved_tensions": [],
  "auto_mode": false,
  "started_at": "<started_at>",
  "updated_at": null
}
```

Replace `false` in `"auto_mode"` with the value in effect. Replace `"<started_at>"` with `started_at`.

## Step 1: Identify the Artifact

In a person's run, ask which artifact to analyze unless the person named it when starting this command, and say where the artifact came from. Never reuse a work folder, a `debate-context/`, an `output/` or a `.value-ip-state.json` that another run left behind.

**If `auto_mode: false` and no artifact was provided in the conversation:**

Ask in one chat message which artifact to analyze for true value differentiation and IP: the path or URL of a plan, PRD, code or analysis file, a competitive-intelligence, pricing or corporate-development plugin output, or the plans discussed in this conversation.

**If `auto_mode: true`:**

Skip AskUserQuestion [q: none]. Proceed directly to Step 2 auto-detect. If multiple artifacts are detected and `multiple_artifacts_policy` is `"ask"` but `auto_mode` is `true`, select the first detected artifact automatically.

A named artifact that does not exist halts the run as Step 2 says; ask nothing.

## Step 2: Auto-Detect Context

Run `ArtifactDetector` from `scripts/artifact_detector.py` to find artifacts. Also run `PluginIntegrator` from `scripts/plugin_integrator.py` to find plugin outputs. In a plugin run, skip `PluginIntegrator`: read no other plugin's files, and pass `No plugin outputs detected.` to the framework agents.

**Script logic:** Read `${CLAUDE_PLUGIN_ROOT}/scripts/artifact_detector.py` and `${CLAUDE_PLUGIN_ROOT}/scripts/plugin_integrator.py` and apply their detection logic directly. Run no Python. When you apply `ArtifactDetector`'s logic, skip every folder whose name starts with `.`, `.value-ip/` and every other plugin's folder included, and value-ip's own working folders `debate-context/` and `output/` at the top of the working directory.

**Output wiring:**
- Use `ArtifactDetector` output to identify artifact file(s) and their types.
- Use `PluginIntegrator` summary as supplemental context.
- Pass to each framework agent: (1) full artifact text content, (2) artifact type classification from `ArtifactDetector`, and (3) `PluginIntegrator` summary if any plugin outputs were found.
- If `auto_mode` is `false` and several artifacts are detected, use AskUserQuestion [q: artifact] to ask which one to analyze.
- An artifact found here because nobody named one is a default: tell the synthesizer the run auto-detected it.
- When the named artifact does not exist, or no artifact was given and none is found, the run halts: dispatch the synthesizer once with the halt, the command name `value-ip:analyze`, `started_at`, the `version`, the work folder, and the `plugin-run` block when there is one, skip Steps 3 to 5, and stop after it returns. A halt writes only the result file and the handoff.

Create `debate-context/` in the work folder for all intermediate files.

## Step 3: Dispatch Framework Agents in Parallel

**State transition:** Use the Write tool to update `.value-ip-state.json` with `"phase": "FRAMEWORK_ANALYSIS"` and `"updated_at": <current UTC ISO timestamp>` before dispatching.

**DISPATCH all four framework agents simultaneously** with the artifact context:

1. **helmer-agent** → writes `debate-context/helmer-analysis.md`
2. **blue-ocean-agent** → writes `debate-context/blue-ocean-analysis.md`
3. **christensen-agent** → writes `debate-context/christensen-analysis.md`
4. **moore-agent** → writes `debate-context/moore-analysis.md`

Pass each agent the full path of its lens file, `${CLAUDE_PLUGIN_ROOT}/skills/lenses/<lens>/SKILL.md`, where `<lens>` is `helmer-7-powers`, `blue-ocean-errc`, `christensen-disruption` or `moore-core-context`.

After the four dispatches return, build two lists from this run's dispatch results: `ran`, each framework whose agent returned and wrote its analysis file in this run, and `skipped`, every other framework. Skip each framework in `skipped` and continue (`framework_failure_policy` `skip_and_continue`): set its `framework_results` entry to `"skipped"`.

When `ran` is empty, skip Steps 4 to 6: dispatch the synthesizer once with the halt, the command name, `started_at`, the `version`, the work folder, the `plugin-run` block when there is one, the artifact, and the `ran` and `skipped` lists, with no `debate_rounds`, and stop after it returns.

## Step 4: Debate Coordination

**State transition:** Before each debate round N, use the Write tool to update `.value-ip-state.json` with `"phase": "DEBATE"`, `"round": N`, and `"updated_at": <current UTC ISO timestamp>`. After the coordinator produces its synthesis, also update `"unresolved_tensions"` with a list of unresolved tension descriptions from `debate-context/coordinator-synthesis.md`.

**DISPATCH debate-coordinator** with the analyses of the frameworks in `ran`, and the `ran` list.
Coordinator runs debate rounds (minimum 2, maximum 4).
Stop debate after round 2 if `debate-context/coordinator-synthesis.md` contains no unresolved tensions. Continue to round 3 or 4 only if the coordinator identifies tensions that require further challenge/response. Always stop at round 4 regardless of resolution state.
Writes challenge/response files to `debate-context/`.
When the coordinator returns, keep `debate_rounds`: the number on the `debate_rounds:` line of the coordinator's reply.

## Step 5: Synthesis

**State transition:** Use the Write tool to update `.value-ip-state.json` with `"phase": "SYNTHESIS"` and `"updated_at": <current UTC ISO timestamp>` before dispatching.

**DISPATCH synthesizer** with full debate context. Pass it the command name `value-ip:analyze`, `started_at`, the `version`, the work folder, the `plugin-run` block when there is one, the artifact and whether a person named it or the run auto-detected it, the `ran` and `skipped` lists, and `debate_rounds`.
Synthesizer produces:
- `output/value-ip-scorecard.md` — Value & IP Scorecard
- `output/value-ip-devils-advocate.md` — Devil's Advocate Report

The overall verdict is the mean of the scores of the frameworks that ran: PASS at 3.5 or more, CONDITIONAL from 2.0 to below 3.5, FAIL below 2.0.

The synthesizer ends every run by writing the result file, and the dispatch tells it: Read `${CLAUDE_PLUGIN_ROOT}/agents/synthesizer.md` with the Read tool and follow its `## Result file` section.

## Step 6: Present Results

**State transition:** Use the Write tool to update `.value-ip-state.json` with `"phase": "COMPLETE"` and `"updated_at": <current UTC ISO timestamp>`.

Display the dual output to the user.

**Commit question:**

In a plugin run, skip the commit question and the config's `commit_output`: commit nothing.

If `auto_mode: false`:
  Use AskUserQuestion [q: commit_output] to ask whether to commit the scorecard to the repository.

If `auto_mode: true`:
  Use `auto_answers.commit_output` from config (default: `false`). Skip the commit question.

**State reset:** After COMPLETE, use the Write tool to reset `.value-ip-state.json` to the initial state:

```json
{
  "version": "1.1.0",
  "phase": "INIT",
  "round": 0,
  "max_rounds": 4,
  "artifact_path": null,
  "artifact_type": null,
  "framework_results": {
    "helmer": "pending",
    "blue_ocean": "pending",
    "christensen": "pending",
    "moore": "pending"
  },
  "unresolved_tensions": [],
  "auto_mode": false,
  "started_at": null,
  "updated_at": null
}
```
