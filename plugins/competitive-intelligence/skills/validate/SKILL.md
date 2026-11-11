---
name: validate
description: Checks a feature decision against the competitive landscape and shows the competitive effect of building or not building it. Use when the person decides whether to build a feature, ranks features under competitive pressure, assesses a "me too" request, or asks "should we build [feature]".
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py *), Bash(git rev-parse *), Bash(date *), Skill, Edit(/.competitive-intelligence/**)
---

# /competitive-intelligence:validate

## Purpose

Validate a feature decision against competitive landscape because understanding competitive context prevents both over-investment in features competitors already excel at and under-investment in differentiating capabilities.

## Usage

```
/competitive-intelligence:validate [feature-description]
/competitive-intelligence:validate "AI-powered report generation"
/competitive-intelligence:validate bulk import functionality
```

## When to Use

- Deciding whether to build a new feature
- Prioritizing features against competitive pressure
- Assessing "me too" feature requests
- User says "should we build [feature]", "competitive need for [feature]"

## Process Overview

Feature validation uses a focused lens configuration:

**Primary Lenses:**
- JTBD Performance (Does competitor do this job better?)
- Economic Value (What's the ROI of building this?)

**Secondary Lenses:**
- Technology Disruption (Will AI make this irrelevant?)
- Loss/Churn (Do we lose because we lack this?)

## Command Implementation

```markdown
1. ORIENT:
   - Parse feature description
   - Check for existing ecosystem mapping (in both .competitive-intelligence/ and .competitive-intel/, newest file first)
   - Check for existing competitive data
   - Read a file of an earlier run through the graph: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> pages Run`, take the newest run whose `file_meta` names the file, and run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> view <RUN ID> <file name>`, because `ingest` moves the files of a run into the graph. Read a file that is still in a session folder directly.
   - Run `git rev-parse --show-toplevel` on its own (the output is the git root), and `date -u +%Y%m%dT%H%M%SZ` on its own (the output is `{session}`). Write each file of this run to `.competitive-intelligence/{session}/`.

2. FEATURE DECOMPOSITION:
   Ask user via AskUserQuestion [q: none]:

   "Which customer job does this feature address?"
   - [List relevant job steps from JTBD framework]

   "What outcome does this feature improve?"
   - Speed (faster completion)
   - Accuracy (fewer errors)
   - Both

3. COMPETITIVE SCAN:
   For each competitor in ecosystem:
   - Check: Do they have this capability?
   - Assess: How well do they execute it? (1-5)
   - Note: When did they add it? (timing)
   - Flag: Is this their differentiator?

4. JTBD PERFORMANCE ANALYSIS:
   - Map feature to specific job step(s)
   - Score: Current performance without feature
   - Score: Expected performance with feature
   - Score: Competitor performance on this job step
   - Calculate: Gap closure potential

5. ECONOMIC VALUE ANALYSIS:
   - Estimate: Value creation if built (Time/Error/Revenue/Risk)
   - Estimate: Development cost
   - Calculate: Expected ROI
   - Compare: ROI vs competitor's offering

6. TECHNOLOGY DISRUPTION CHECK:
   - Assess: Can AI platforms do this job step?
   - Assess: Will this become commoditized?
   - Assess: Investment horizon vs disruption timeline
   - Flag: Build vs Buy vs Partner decision

7. LOSS/CHURN VALIDATION (if data available):
   - Check: Have we lost deals citing this gap?
   - Check: Have customers churned citing this need?
   - Quantify: Revenue impact of missing feature
   - Validate: Is competitive pressure real or perceived?

8. SYNTHESIZE RECOMMENDATION:
   Generate feature validation scorecard:

   | Factor | Score | Confidence | Notes |
   |--------|-------|------------|-------|
   | Competitive Gap | High/Med/Low | H/M/L | {explanation} |
   | JTBD Impact | High/Med/Low | H/M/L | {explanation} |
   | Economic Value | $X/user/month | H/M/L | {calculation} |
   | Disruption Risk | High/Med/Low | H/M/L | {timeline} |
   | Loss Validation | Yes/No/Unknown | H/M/L | {evidence} |

   Overall Recommendation:
   - BUILD: Strong competitive need, high ROI, validated by losses
   - DEFER: Low priority, other investments have better ROI
   - SKIP: Competitors commoditized, or AI will disrupt
   - INVESTIGATE: Need more data before deciding

9. CHECKPOINT - Validation Review:
   Display to user:
   ```
   Feature Validation: {feature-name}

   Competitive Analysis:
   - Competitors with feature: {count}/{total}
   - Best-in-class: {competitor} (score: X/5)
   - Our current capability: {score}/5
   - Gap if we build: {new score}/5

   Strategic Assessment:
   - JTBD Impact: {High/Med/Low}
   - Economic Value: ${X}/user/month
   - Disruption Risk: {High/Med/Low} ({timeline})
   - Loss Validation: {Yes/No/Unknown}

   Recommendation: {BUILD/DEFER/SKIP/INVESTIGATE}
   Confidence: {High/Medium/Low}

   Reasoning: {2-3 sentences}

   Generate detailed report?
   ```

10. INGEST THE RUN:
   - Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> ingest .competitive-intelligence/{session}` on its own. `<git root>` is the output of `git rev-parse --show-toplevel`, run on its own.
   - When the output holds an `INIT:` line, show that line.
   - When the command exits 1, show its errors, say that the results stay in the session folder, and do not report success. Then stop: do not write or change a file in `.competitive-intelligence/` or in the graph, and do not run `ingest` again in this turn, because the graph would then hold data that no step of this skill made.
   - Else show the `ingested` line. Ask one question: "Learn these results?" Ask it with `AskUserQuestion` [q: none], with the options `Yes` and `No`, in this turn. On yes, run the skill `competitive-intelligence:learn` with `{session}`. When you have no `AskUserQuestion` tool, for example in `claude -p`, do not write the question as text, because the answer then comes in a new turn, and the new turn does not have the tools of this skill. Write this line in your reply, on its own line: `Next: /competitive-intelligence:learn {session}`.
```

## Output Artifacts

- `.competitive-intelligence/{session}/validation-{feature}.json` - Full analysis
- `.competitive-intelligence/{session}/validation-scorecard-{feature}.json` - Summary

## Decision Framework

```
                    ┌─────────────────┐
                    │ Competitive Gap │
                    │   (Do they      │
                    │   have it?)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
           Yes, and       Yes, but      No, they
           they're       they're       don't
           better        similar       have it
              │              │              │
              ▼              ▼              ▼
         ┌────────┐    ┌────────┐    ┌────────┐
         │ Check  │    │ Check  │    │ Check  │
         │ Loss   │    │ JTBD   │    │ Will   │
         │ Data   │    │ Impact │    │ they?  │
         └────┬───┘    └────┬───┘    └────┬───┘
              │              │              │
              ▼              ▼              ▼
         Validated?    High Impact?   First-mover
         BUILD         BUILD          advantage?
                                      BUILD/DEFER
```

## Philosophy

<objective_validation>
Features should be built for customer value, not competitive anxiety.
"Competitor has it" is not sufficient justification.
"We lose deals because of it" is strong justification.
"AI will do it better in 18 months" is a red flag.
</objective_validation>

<investment_optimization>
Every feature has opportunity cost.
Build what differentiates, not what commoditizes.
ROI must justify development investment.
</investment_optimization>

## Transition

On completion:
- User can validate another feature
- User can run `/competitive-intelligence:analyze` on best-in-class competitor
- User can proceed to roadmap planning with validated priorities
