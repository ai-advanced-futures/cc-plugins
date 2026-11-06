---
name: discover
description: Maps the competitive landscape of a market in 3 phases (context, ecosystem, intelligence) and writes one result file. Use when the person starts a competitive analysis, enters a new market, refreshes old competitive intelligence, or says "map competitors", "competitive landscape" or "who are our competitors".
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# /competitive-intelligence:discover

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py <args>`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because the shell grant of a runner covers only `git rev-parse`, `date` and `uv run`.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written, because the result file needs the output of each agent.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input as a text question (see the steps below), or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", because a person who picks such an option gives no value.

## When to Use

- Starting a new competitive analysis from scratch
- Entering a new market and need landscape overview
- Refreshing stale competitive intelligence
- User says "map competitors", "competitive landscape", "who are our competitors"

## Process Overview

This skill runs the first 3 phases of the workflow:

1. **Context Discovery** (Phase 1) - Gather scope and requirements
2. **Ecosystem Mapping** (Phase 2) - Identify and classify competitors
3. **Intelligence Gathering** (Phase 3) - Collect and validate data

You run in the main conversation, so you ask the person. The agents ask nothing. You dispatch each agent with the `Agent` tool and give it the answers as dispatch fields. Each agent gets `session_id` and `data_dir`.

## Steps

```markdown
0. READ THE START TIME AND THE VERSION:
   - Run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep it as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. When a `date` call is denied or fails, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and use its output as that time. The result file needs both.
   - The session folder `{session}` is the `run_id` in a plugin run (after the check of the runner, step 1), and `started_at` written as `YYYYMMDDTHHMMSSZ` in a person's run. In a person's run, `run_id` is absent, whatever the session folder is called.
   - Every agent this skill dispatches gets `session_id` = `{session}` and `data_dir` = `.competitive-intelligence/{session}/` under the git root.

1. ORIENT:
   - Check current directory for existing analyses
   - Check if .competitive-intelligence/ or .competitive-intel/ exists, and read both, newest file first
   - Look for previous ecosystem mappings

2. ASK THE INTAKE QUESTIONS, THEN DISPATCH THE CONTEXT ANALYST:
   - Ask only the questions whose answer is not yet known. The text after the skill name is the `market`. An answer in the dispatch context is also known.
   - Ask the choice questions b, c, d and e in one AskUserQuestion call [q: none]. Mark the default option "(Recommended)".
   - Ask each text question with AskUserQuestion [q: none], one question for each call.
   - Keep a list of the inputs that you asked in this run, and of the default options that the person picked. The result file step needs the list.
   - When AskUserQuestion is not available [q: none], or the person gives no answer, leave the input out of the dispatch. The context analyst then uses its own default.

   a. If no market was given, ask with AskUserQuestion [q: market] (text): "Which product, market or feature should the analysis cover?"
   b. Ask with AskUserQuestion [q: trigger] (choice): "What led to this analysis?"
      - feature_decision: A decision on whether to build a feature
      - competitor_response: A competitor's move, such as a launch
      - strategic_planning: A full review of the market
      - monitoring: A regular update
   c. Ask with AskUserQuestion [q: scope] (choice): "How wide should the analysis be?"
      - full_market: The full market (default)
      - specific_segment: One segment of the market
      - single_competitor: One competitor
      - specific_feature: One feature or capability
   d. Ask with AskUserQuestion [q: analysis_mode] (choice): "Is the analysis for internal decisions or for sales positioning?"
      - strategic_planning: Internal decisions: honest about weaknesses (default)
      - sales_enablement: Sales positioning: framed for customers
   e. Ask with AskUserQuestion [q: depth] (choice): "How deep should the analysis go?"
      - quick_scan: A quick scan of the key findings
      - standard: Standard depth (default)
      - comprehensive: Every lens, in full detail
   f. Ask with AskUserQuestion [q: available_data] (text): "What evidence about the competitors do you have, such as battle cards, win or loss reports or customer feedback, and where are the files?"
   g. Ask with AskUserQuestion [q: competitors] (text): "Which competitors must the analysis include?"

   Dispatch the context analyst with the `Agent` tool:
   - Agent: `competitive-intelligence:context-analyst`
   - Fields: `session_id`, `data_dir`, and the answers `market`, `trigger`, `scope`, `analysis_mode`, `depth` and `available_data`.
   - Purpose: Determine scope, context, and analysis mode
   - Wait for: `DONE: context`
   - If it returns `QUESTIONS: <path>`, follow the open-question loop of the section "Open questions of an agent" below.

3. CHECKPOINT - Context Validation:
   Read `context-summary.json` in `data_dir`. Display to user:
   ```
   Context Analysis Complete:

   Trigger: {why this analysis}
   Scope: {market/segment/feature}
   Mode: {Strategic Planning | Sales Enablement}
   Depth: {Quick Scan | Standard | Comprehensive}

   Lens Priority:
   1. {primary lens}
   2. {primary lens}
   3. {secondary lens}
   ...

   Proceed with ecosystem mapping?
   ```
   Options: Proceed / Adjust scope / Change mode

4. DISPATCH THE ECOSYSTEM MAPPER:
   - Agent: `competitive-intelligence:ecosystem-mapper`
   - Fields: `session_id`, `data_dir`, and `competitors` when the person named any. With no list, the mapper finds the competitors itself.
   - Purpose: Identify and classify all competitors
   - Wait for: `DONE: ecosystem` and competitive-ecosystem.json generated

5. CHECKPOINT - Ecosystem Validation:
   Read `ecosystem-summary.json` in `data_dir`. Display to user:
   ```
   Ecosystem Mapping Complete:

   Competitors Identified: {count}
   - High Threat: {count} (deep dive)
   - Medium Threat: {count} (standard analysis)
   - Low Threat: {count} (quick scan)

   Classification:
   - Direct: {count}
   - Indirect: {count}
   - Substitute: {count}
   - Tech Disruption: {count}

   Does this ecosystem map look right?
   ```
   Options: Proceed / Add competitors / Reclassify

6. DISPATCH INTELLIGENCE GATHERER:
   - Agent: `competitive-intelligence:intelligence-gatherer`
   - Fields: `session_id`, `data_dir`
   - Purpose: Collect and triangulate competitive data
   - Wait for: `DONE: intelligence` and intelligence gathered with confidence scores

7. CHECKPOINT - Intelligence Validation:
   Read `intelligence-summary.json` in `data_dir`. Display to user:
   ```
   Intelligence Gathering Complete:

   Data Collected:
   - High Confidence: {count} findings
   - Medium Confidence: {count} findings
   - Low Confidence: {count} findings
   - Speculative: {count} findings

   Data Gaps:
   - Critical: {list}
   - Important: {list}

   Proceed to multi-lens analysis or gather more data?
   ```
   Options: Proceed / Gather more / Accept gaps

8. DISPLAY SUMMARY:
   ```
   Discovery Phase Complete!

   Generated:
   - .competitive-intelligence/{session}/context-config.json
   - .competitive-intelligence/{session}/competitive-ecosystem.json
   - .competitive-intelligence/{session}/intelligence-data.json

   Next Steps:
   - Run full analysis: /competitive-intelligence:competitive-intelligence
   - Deep dive: /competitive-intelligence:analyze [competitor]
   - Validate feature: /competitive-intelligence:validate [feature]
   ```

9. WRITE THE RESULT FILE:
   - Read `${CLAUDE_PLUGIN_ROOT}/agents/deliverable-generator.md` with the Read tool and follow its `## Result file` section, in every run.
```

## Checkpoint answers

At a checkpoint, do as the person answers:
- **Proceed**: go to the next step.
- **Adjust scope**, **Change mode**, **Add competitors**, **Reclassify** or **Gather more**: ask what to change with AskUserQuestion [q: none], as a text question. Dispatch the same agent again with the dispatch field `adjustments` set to the words of the person. The agent overwrites its output files.
- **Accept gaps**: go to the next step. Keep the gaps in the summary.
- **Cancel**: stop and tell the person which files exist.

When AskUserQuestion is not available [q: none], choose Proceed.

## Open questions of an agent

An agent asks nothing itself. When an agent needs an answer that it does not have, it writes `open-questions.json` in `data_dir` and returns `QUESTIONS: <path>` as its last line. The file has the shape of `questions/discover.json`: `schema` is `plugin-questions/1`, `command` is the agent name, and `questions` lists `input`, `question`, `type`, and for a choice, `options` and `default`.

When an agent returns `QUESTIONS: <path>`, read the file, ask each question with AskUserQuestion [q: none], dispatch the same agent again with each answer as a dispatch field named by its `input`, and repeat until the agent returns its `DONE:` line.

## When an agent fails

If an agent returns an error or writes no output file:
1. Write the failure to `execution-log.md` in `data_dir`, with the time, the phase and a short summary.
2. Dispatch the agent again one time with the same fields.
3. If it fails again, ask: "Phase [X] failed twice. Retry or Cancel?" A phase cannot be skipped, because each later phase depends on it. When the person cancels, or cannot answer, write the result file with a gap for the phase that failed, as the `## Result file` section says.

## User Interaction Points

| Checkpoint | Purpose | Options |
|------------|---------|---------|
| Context | Validate analysis configuration | Proceed / Adjust scope / Change mode |
| Ecosystem | Validate competitor identification | Proceed / Add competitors / Reclassify |
| Intelligence | Validate data quality | Proceed / Gather more / Accept gaps |

## Output Artifacts

- `.competitive-intelligence/{session}/context-config.json` - Analysis configuration
- `.competitive-intelligence/{session}/competitive-ecosystem.json` - Competitor map
- `.competitive-intelligence/{session}/intelligence-data.json` - Gathered data
- `.competitive-intelligence/results/` - The result file

## Philosophy

<systematic_discovery>
Look for indirect competitors solving the same job differently.
Look for substitutes (manual processes, spreadsheets).
Look for technology disruption threats (AI platforms).
Look for adjacent players who could pivot into market.
</systematic_discovery>

<six_dimensional_classification>
Every competitor classified on:
1. Type (Direct/Indirect/Substitute/Non-consumption)
2. JTBD Alternative (Same/Different approach, Partial, Workaround)
3. Threat Level (High/Medium/Low)
4. Stage (Current/Emerging/Potential)
5. Market Overlap (High/Medium/Low)
6. Technology Disruption Factor
</six_dimensional_classification>

## Transition

On successful completion:
- User can continue to full analysis (Phases 4-6) with `/competitive-intelligence:competitive-intelligence`
- User can run `/competitive-intelligence:analyze [competitor]` for deep dive
- User can run `/competitive-intelligence:validate [feature]` for feature context
