---
name: analyze
description: Analyzes one competitor through the 6 lenses, writes a SWOT and recommendations, and writes one result file. Use when the person wants a deep dive on a named competitor, prepares for a competitive deal or pitch, responds to a competitor move, or says "analyze [competitor]" or "deep dive on [competitor]".
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# /competitive-intelligence:analyze

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py <args>`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input as a text question with `AskUserQuestion` [q: none], 1 question for each call, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them".

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
   - The session folder `{session}` is the `run_id` in a plugin run (after the check of the runner, step 1), and `started_at` written as `YYYYMMDDTHHMMSSZ` in a person's run. In a person's run, `run_id` is absent, whatever the session folder is called.
   - Every lens skill this skill follows gets `session_id` = `{session}` and `data_dir` = `.competitive-intelligence/{session}/` under the git root.

1. ORIENT:
   - Check if competitor exists in ecosystem mapping (in both .competitive-intelligence/ and .competitive-intel/, newest file first)
   - In a person's run, a value taken from another run's ecosystem mapping is a `default` source naming that file, as the result file section says; never write into that run's folder.
   - If no ecosystem: Offer to run /competitive-intelligence:discover first
   - The text after the skill name is the competitor. If no competitor is named, ask with AskUserQuestion which competitor to analyze [q: competitor]
   - Unless the person has named it, ask with AskUserQuestion which product of yours the analysis compares with this competitor [q: offering].
   - Unless the person has named it, ask with AskUserQuestion what evidence about this competitor they have, such as lost deals, churned customers or battle cards, and where the files are [q: available_data].
   - Load existing intelligence data for this competitor
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

8. WRITE THE RESULT FILE:
   - Read `${CLAUDE_PLUGIN_ROOT}/agents/deliverable-generator.md` with the Read tool and follow its `## Result file` section, in every run.
```

## Output Artifacts

- `.competitive-intelligence/{session}/analysis-{competitor}.json` - Full lens outputs
- `.competitive-intelligence/{session}/swot-{competitor}.json` - Competitor SWOT
- `.competitive-intelligence/{session}/recommendations-{competitor}.json` - Actions
- `.competitive-intelligence/results/` - The result file

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
