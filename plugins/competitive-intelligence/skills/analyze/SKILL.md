---
name: analyze
description: Analyzes one competitor through the 6 lenses, writes a SWOT and recommendations, and writes one result file. Use when the person wants a deep dive on a named competitor, prepares for a competitive deal or pitch, responds to a competitor move, or says "analyze [competitor]" or "deep dive on [competitor]".
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*), Skill, Edit(/.competitive-intelligence/**)
---

# /competitive-intelligence:analyze

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py <args>`, one command per Bash call, with no pipe (`|`), no `;` and no `&&`. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because only this plugin's scripts run with no question to the person.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written, because the result file needs the output of each agent.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input as a text question with `AskUserQuestion` [q: none], 1 question for each call, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", because a person who picks such an option gives no value.

## Plugin-run block

A run is a plugin run when the arguments of this skill hold a fenced block with the info string `plugin-run`, or when the arguments are 1 line that is the path of a file that holds that block (read the block from that file with the Read tool). Another plugin calls this skill with the `Skill` tool in its own conversation. The block holds `command`, `automated`, `answers_path`, `case`, `run_id` and `inputs_from`. With no block, this is a person's run: skip this section, and ask the person as the steps say.

In a plugin run, the answers file gives each answer. Ask the person nothing. In a plugin run of `competitive-intelligence:analyze`:

- Read the answers file at `answers_path` and use its `competitive-intelligence:analyze` section. A value it gives replaces the default for that input. Each answer has `settled_by`. A value with `settled_by: person` is a source of type `person`; a value with `settled_by: recommended` is a source of type `default`. When an input has no answer, use the default of `${CLAUDE_PLUGIN_ROOT}/result-file.json` and record it in `defaults`.
- The arguments are not the `competitor`: the answers file gives it. Do not call `AskUserQuestion` [q: none] and do not show a checkpoint: skip the questions of steps 1 and 2, the checkpoint of step 6, the question "Retry, Skip or Cancel?" (skip the lens), and the question of step 9.
- `automated: true` in the invocation block wins over any config file's automation setting, so the run skips the checkpoint.
- Read an earlier run's files only through `inputs_from`; with no entry for `competitive-intelligence`, read no earlier session and do not offer to run discover first, because `inputs_from` is the only list of earlier runs and you cannot ask. `case` goes in `run.case`, and `run_id` goes in `run.run_id` and in the file name.
- The session folder is `.competitive-intelligence/<run_id>/`, when the `run_id` passes the check of step 0, under the git root, and it holds every file of the skill.
- When the answers give no `competitor`, run only step 0, step 8 and step 9, and write the result file with the halt gap.
- The run ends with the result file written to `.competitive-intelligence/results/` by the rules of `agents/deliverable-generator.md`. Step 9 then ingests the run, with no question. The last line of your reply is the path of the result file.

## Purpose

Perform comprehensive multi-lens analysis on a specific competitor because focused deep dives reveal strategic insights that broad surveys miss.

## Usage

```
/competitive-intelligence:analyze [competitor-name]
/competitive-intelligence:analyze Competitor X
/competitive-intelligence:analyze "Company Name with Spaces"
```

## When to Use

- Need detailed understanding of a specific competitor
- Preparing for competitive deal or pitch
- Responding to competitor announcement or move
- User says "analyze [competitor]", "deep dive on [competitor]"

## Process Overview

This skill executes Phase 4 (Multi-Lens Analysis) focused on a single competitor:

1. **Load Context** - Check for existing ecosystem mapping
2. **Execute Lenses** - Run all 6 analytical lenses
3. **Cross-Validate** - Check consistency across lenses
4. **Synthesize** - Generate competitor-specific SWOT and insights

You run in the main conversation, so you ask the person. You read each lens skill file and follow it in this session. No agent is needed.

## Steps

```markdown
0. READ THE START TIME AND THE VERSION:
   - Run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep it as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. When a `date` call is denied or fails, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and use its output as that time. The result file needs both.
   - Run `git rev-parse --show-toplevel` on its own. Its output is the git root. When it fails, the git root is the working directory.
   - In a plugin run, check the `run_id`. When it holds a `'`, it is not a plain name: do not put it in a command, because a `'` ends the quotes and the shell runs the rest of the value. Else run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py run-id '<run_id>'` on its own. When the `run_id` holds a `'` or the command exits 2, continue with no `run_id`, as a person's run does. The session folder is the one of a person's run, the result file has no `run.run_id` and no `-<run_id>` in its name, and it records the gap `{"kind": "risk", "label": "run_id", "why": "the run_id of the plugin-run block is not a plain name, or is a name that the plugin uses in .competitive-intelligence/; the run used none"}`. The answers file and the `automated` rule stay. A halt writes this gap too. When the command exits 3, the `run_id` passed the check, but its session folder exists, because an earlier run used this `run_id`: write nothing in that folder. Do not do the rest of step 0 and do not do steps 1 to 7. Do step 8 with no result and this halt gap: `{"kind": "risk", "label": "run_id", "why": "the session folder .competitive-intelligence/<run_id>/ exists: an earlier run used this run_id, and a run never writes over it"}`. The `run_id` goes in `run.run_id` and in the file name. Then do step 9 with no path, because the session folder is the folder of an earlier run.
   - The session folder `{session}` is the `run_id` in a plugin run with a `run_id` that passed the check above, and `started_at` written as `YYYYMMDDTHHMMSSZ` in a person's run. In a person's run, `run_id` is absent, whatever the session folder is called.
   - Every lens skill this skill follows gets `session_id` = `{session}` and `data_dir` = `.competitive-intelligence/{session}/` under the git root.
   - In a plugin run, write `session.json` in that folder: `session_id`, `mode`, `started_at`, `run_id` and `case`, `lenses_complete: []` and `lens_failures: {}`. Record each finished lens in `lenses_complete`, and each lens that did not run in `lens_failures` with the reason.

1. ORIENT:
   - Find the earlier runs: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> pages Run` on its own. Each Run page names the files of its run in `file_meta`. Take the newest Run page (the latest `finished_at`) whose `file_meta` names `competitive-ecosystem.json`. The RUN ID of a Run page is the file name of the page with no `.md`, for example `RUN-01`.
   - In a person's run, a value taken from another run's ecosystem mapping is a `default` source naming that file, as the result file section says; never write into that run's folder.
   - If no Run page names `competitive-ecosystem.json`: offer to run /competitive-intelligence:discover first
   - The text after the skill name is the competitor. If no competitor is named, ask with AskUserQuestion which competitor to analyze [q: competitor]
   - Unless the person has named it, ask with AskUserQuestion which product of yours the analysis compares with this competitor [q: offering].
   - Unless the person has named it, ask with AskUserQuestion what evidence about this competitor they have, such as lost deals, churned customers or battle cards, and where the files are [q: available_data].
   - Read `competitive-ecosystem.json` and `intelligence-data.json` of that run, and find the competitor in them: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> view <RUN ID> <file name>` on its own, 1 file for each call.
   - Read the files of an earlier run only with these 2 commands. Do not read a session folder of an earlier run with `grep`, `cat`, `ls`, `head`, `find`, the Read tool, the Grep tool or the Glob tool, because `ingest` moves most of its files into the graph, and `view` gives each file of `file_meta`, also a file that stays in the folder.
   - Keep a list of the inputs that you asked in this run, and of the default options that the person picked. The result file step needs the list.

2. DETERMINE ANALYSIS SCOPE:
   Ask user via AskUserQuestion [q: analysis_purpose]:
   "What is the analysis for?"
   - strategic_planning: Planning: a full and honest view (default)
   - competitive_deal: A deal against this competitor: positioning
   - threat_assessment: Their strengths and the threat they pose
   - opportunity_finding: Their weaknesses and the openings they leave

   When nobody gives a purpose, use `analysis_purpose = strategic_planning`.

3. EXECUTE LENSES (in dependency order):

   A lens finding with no source is agent inference: mark it `speculative`.

   For each lens, read its skill file and follow it in this session. Do not dispatch an agent for a lens.

   A. JTBD Performance Lens:
      - Read and follow: `${CLAUDE_PLUGIN_ROOT}/skills/lenses-jtbd-performance/SKILL.md`
      - Compare job step performance: Your product vs Competitor
      - Output: Performance gaps, strengths, weaknesses

   B. Forces Analysis Lens:
      - Read and follow: `${CLAUDE_PLUGIN_ROOT}/skills/lenses-forces-analysis/SKILL.md`
      - Assess: Push/Pull/Anxiety/Habit for switching TO competitor
      - Assess: Push/Pull/Anxiety/Habit for switching FROM competitor
      - Output: Switching dynamics

   C. Economic Value Lens:
      - Read and follow: `${CLAUDE_PLUGIN_ROOT}/skills/lenses-economic-value/SKILL.md`
      - Calculate: Their value proposition (Time/Error/Revenue/Risk)
      - Compare: Value-to-price ratio vs your offering
      - Output: Economic comparison

   D. Strategic Positioning Lens:
      - Read and follow: `${CLAUDE_PLUGIN_ROOT}/skills/lenses-strategic-positioning/SKILL.md`
      - Analyze: Business model, target market, moats
      - Identify: Strategic vulnerabilities
      - Output: Positioning assessment

   E. Technology Disruption Lens:
      - Read and follow: `${CLAUDE_PLUGIN_ROOT}/skills/lenses-technology-disruption/SKILL.md`
      - Assess: Their AI/tech capabilities and risks
      - Compare: Disruption posture vs your offering
      - Output: Technology assessment

   F. Loss/Churn Lens (if data available):
      - Read and follow: `${CLAUDE_PLUGIN_ROOT}/skills/lenses-loss-churn/SKILL.md`
      - Read: the files named in `available_data`, when there are any
      - Analyze: Deals lost to this competitor
      - Analyze: Customers churned to this competitor
      - Output: Reality check on other findings

   If a lens fails or writes no output, try it again one time. If it fails again, ask: "The [lens] lens failed twice. Retry, Skip or Cancel?" Skip leaves the lens out and goes on. Cancel stops the analysis. In a plugin run, ask nothing: skip the lens.

4. CROSS-VALIDATE:
   - Check: Do lens findings align?
   - Flag: Contradictions for investigation
   - Weight: Loss/Churn data as ground truth

5. SYNTHESIZE:
   - Generate competitor-specific SWOT (`competitor_swot`: this competitor's strengths/weaknesses/opportunities/threats vs market)
   - Generate your SWOT (`your_swot`: your company's strengths/weaknesses/opportunities/threats relative to this competitor)
   - Both `competitor_swot` AND `your_swot` must be present in swot-{competitor}.json output
   - Use headers: Strengths, Weaknesses, Opportunities, Threats (see synthesizer.md SWOT Format Standard)
   - Identify top 3 threats from this competitor
   - Identify top 3 opportunities against this competitor
   - Create confidence-weighted recommendations

6. CHECKPOINT - Analysis Validation:
   Display to user:
   ```
   Analysis Complete: {Competitor Name}

   Key Findings (High Confidence):
   - {finding 1}
   - {finding 2}

   Performance Comparison:
   - You Lead: {job steps where you're better}
   - They Lead: {job steps where they're better}
   - Tied: {job steps with no significant gap}

   SWOT Summary:
   - Strengths: {count}
   - Weaknesses: {count}
   - Opportunities: {count}
   - Threats: {count}

   Generate detailed report?
   ```
   When AskUserQuestion is not available [q: none], go on to step 7.

7. GENERATE OUTPUTS:
   - .competitive-intelligence/{session}/analysis-{competitor}.json
   - .competitive-intelligence/{session}/swot-{competitor}.json
   - .competitive-intelligence/{session}/recommendations-{competitor}.json
   - In `analysis-{competitor}.json`, record each lens that did not run in `lens_failures`, as `{"<lens>": "<reason>"}`.
   - `{competitor}` in each file name is the name of the competitor in lowercase, with 1 `-` for each run of other characters (`Acme Rival` gives `acme-rival`).
   - At the top level of `analysis-{competitor}.json` and of `swot-{competitor}.json`, write `competitor`, the name of the competitor. When the ecosystem mapping gives the competitor an `id`, also write `competitor_id`, that id. Ingest uses them to link the pages of the files to the competitor.

8. WRITE THE RESULT FILE:
   - When a phase agent says that the web tools were refused, add a gap to the result file with the `kind` `risk`, the label `Web research`, and a `why` that names the refused tools. Give the type `model` to a source that no web call checked, because a reader must not take that finding as checked.
   - Read `${CLAUDE_PLUGIN_ROOT}/agents/deliverable-generator.md` with the Read tool and follow its `## Result file` section, in every run.

9. INGEST THE RUN:
   - Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> ingest .competitive-intelligence/{session} --result .competitive-intelligence/results/<the file name of the result file of step 8>` on its own. `<git root>` is the output of `git rev-parse --show-toplevel`, run on its own. A halt has no session folder of its own: run `ingest --result .competitive-intelligence/results/<the file name of the result file of step 8>` with no path. Give each path relative to the git root, not as an absolute path: `ingest` refuses an absolute path (exit 2).
   - When the output holds an `INIT:` line, show that line.
   - When the command exits 1, show its errors, say that the results stay in the session folder, and do not report success.
   - Else show the `ingested` line. In a person's run, ask one question: "Learn these results?" Ask it with `AskUserQuestion` [q: none], with the options `Yes` and `No`, in this turn. On yes, run the skill `competitive-intelligence:learn` with `{session}`. When you have no `AskUserQuestion` tool, for example in `claude -p`, do not write the question as text, because the answer then comes in a new turn, and the new turn does not have the tools of this skill. Write this line in your reply, on its own line: `Next: /competitive-intelligence:learn {session}`.
```

## Output Artifacts

- `.competitive-intelligence/{session}/analysis-{competitor}.json` - Full lens outputs
- `.competitive-intelligence/{session}/swot-{competitor}.json` - Competitor SWOT
- `.competitive-intelligence/{session}/recommendations-{competitor}.json` - Actions
- `.competitive-intelligence/results/` - The result file
- The pages of the run in the graph `competitive-intelligence`, with `status: draft`

## Lens Execution Order

Lenses execute in dependency order with intelligent cascading:

```
JTBD Performance → Forces Analysis → Economic Value
        ↓               ↓                ↓
        └───────────────┴────────────────┘
                        ↓
              Strategic Positioning
                        ↓
              Technology Disruption
                        ↓
                  Loss/Churn
                    (validates all)
```

## Philosophy

<focused_depth>
Better to deeply understand one competitor than superficially scan many.
Each lens builds on previous findings.
Cross-validation reveals hidden insights.
</focused_depth>

<evidence_based>
Every claim needs supporting evidence.
Confidence scores reflect data quality.
Loss/Churn data trumps speculation.
</evidence_based>

## Transition

On completion:
- User can analyze another competitor
- User can run `/competitive-intelligence:respond` to plan response
- User can proceed to Phase 6 for deliverables with `/competitive-intelligence:competitive-intelligence`
