---
name: respond
description: Analyzes a competitor move, announcement or threat and plans a response. Use when a competitor launches a product, changes pricing or positioning, or makes a major announcement, or when the person asks "how do we respond to" or says "competitor just announced".
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(git rev-parse *), Bash(date *), Skill
---

# /competitive-intelligence:respond

## Purpose

Analyze and plan response to competitive threats because structured assessment prevents both overreaction to noise and underreaction to genuine strategic shifts.

## Usage

```
/competitive-intelligence:respond [threat-description]
/competitive-intelligence:respond "Competitor X launched AI feature"
/competitive-intelligence:respond competitor pricing change
```

## When to Use

- Competitor makes significant announcement
- Competitor launches new product or feature
- Competitor changes pricing or positioning
- Market shift affects competitive dynamics
- User says "how do we respond to", "competitor just announced"

## Process Overview

Competitive response uses a focused lens configuration:

**Primary Lenses:**
- Strategic Positioning (What's their move and intent?)
- Forces Analysis (Why might customers switch?)
- SWOT (Immediate threats and opportunities)

**Secondary Lenses:**
- JTBD Performance (Where do they now lead?)
- Technology Disruption (Is this a structural shift?)

## Command Implementation

```markdown
1. ORIENT:
   - Parse threat description
   - Check for existing ecosystem mapping (in both .competitive-intelligence/ and .competitive-intel/, newest file first)
   - Determine if this is new competitor or existing
   - Read a file of an earlier run through the graph: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> pages Run`, take the newest run whose `file_meta` names the file, and run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> view <RUN ID> <file name>`, because `ingest` moves the files of a run into the graph. Read a file that is still in a session folder directly.
   - Run `git rev-parse --show-toplevel` on its own (the output is the git root), and `date -u +%Y%m%dT%H%M%SZ` on its own (the output is `{session}`). Write each file of this run to `.competitive-intelligence/{session}/`.

2. THREAT CLASSIFICATION:
   Ask user via AskUserQuestion [q: none]:

   "What type of competitive move is this?"
   - Product/Feature Launch (new capability)
   - Pricing Change (cost structure shift)
   - Positioning Change (new messaging/target)
   - Acquisition/Partnership (capability expansion)
   - Market Entry (new competitor entering)
   - Executive/Team Change (talent shift)

   "What's the urgency level?"
   - Immediate (active deals affected)
   - Near-term (next quarter impact)
   - Strategic (long-term positioning)

3. GATHER THREAT INTELLIGENCE:
   - Collect: Available information about the move
   - Verify: Multiple sources for triangulation
   - Assess: Confidence level of information
   - Flag: Gaps in understanding

4. STRATEGIC POSITIONING ANALYSIS:
   - Analyze: What does this move signal about their strategy?
   - Assess: How does this change their positioning?
   - Evaluate: Moat strengthening or vulnerability exposure?
   - Predict: What might they do next?

5. FORCES ANALYSIS:
   - Assess: Does this increase "Pull" toward competitor?
   - Assess: Does this reduce "Anxiety" about switching?
   - Assess: Does this overcome "Habit" barriers?
   - Calculate: Net impact on customer switching dynamics

6. SWOT ASSESSMENT:
   > **Note:** SWOT here is threat-specific (immediate competitive response view); see synthesizer.md output for full dual SWOT (competitor_swot + your_swot).
   - Immediate Threats: What's at risk right now?
   - Emerging Opportunities: What openings does this create?
   - Your Strengths: What advantages do you retain?
   - Your Weaknesses: What gaps are now exposed?

7. RESPONSE OPTIONS GENERATION:
   Generate 3-4 response options:

   Option 1: Counter
   - Direct competitive response
   - Match or exceed their move
   - Timeline, cost, risk assessment

   Option 2: Flank
   - Indirect response targeting different value
   - Differentiation strategy
   - Timeline, cost, risk assessment

   Option 3: Absorb
   - Accept impact, focus elsewhere
   - Minimize disruption to roadmap
   - Timeline, cost, risk assessment

   Option 4: Wait
   - Monitor before responding
   - Gather more data
   - Decision triggers for action

8. RECOMMENDATION WITH CONFIDENCE:
   Synthesize response recommendation:

   | Option | Likelihood of Success | Effort | Risk | Timeframe |
   |--------|----------------------|--------|------|-----------|
   | Counter | H/M/L | H/M/L | H/M/L | X weeks |
   | Flank | H/M/L | H/M/L | H/M/L | X weeks |
   | Absorb | H/M/L | H/M/L | H/M/L | N/A |
   | Wait | H/M/L | Low | M | X weeks review |

9. CHECKPOINT - Response Review:
   Display to user:
   ```
   Competitive Response Analysis: {threat-description}

   Threat Assessment:
   - Type: {classification}
   - Urgency: {level}
   - Confidence: {H/M/L}

   Impact Analysis:
   - Deals at Risk: {estimate}
   - Customers at Risk: {estimate}
   - Strategic Impact: {assessment}

   Recommended Response: {Option name}

   Reasoning:
   - {key reason 1}
   - {key reason 2}
   - {key reason 3}

   Timeline: {recommended action timeline}

   Generate detailed response plan?
   ```

10. INGEST THE RUN:
   - Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> ingest .competitive-intelligence/{session}` on its own. `<git root>` is the output of `git rev-parse --show-toplevel`, run on its own.
   - When the output holds an `INIT:` line, show that line.
   - When the command exits 1, show its errors, say that the results stay in the session folder, and do not report success.
   - Else show the `ingested` line. Ask one question: "Learn these results?" On yes, run the skill `competitive-intelligence:learn` with `{session}`.
```

## Output Artifacts

- `.competitive-intelligence/{session}/threat-{id}.json` - Threat analysis
- `.competitive-intelligence/{session}/response-options-{id}.json` - Options evaluated
- `.competitive-intelligence/{session}/response-plan-{id}.json` - Recommended plan

## Response Framework

```
                    ┌─────────────────┐
                    │   Assess Threat │
                    │    Severity     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
           High           Medium          Low
           Severity       Severity       Severity
              │              │              │
              ▼              ▼              ▼
         ┌────────┐    ┌────────┐    ┌────────┐
         │Counter │    │ Flank  │    │ Wait   │
         │ or     │    │ or     │    │ and    │
         │ Flank  │    │ Absorb │    │ Monitor│
         └────────┘    └────────┘    └────────┘
              │              │              │
              ▼              ▼              ▼
         Immediate      Next Quarter    Review in
         Action         Action          90 days
```

## Philosophy

### Calibrated response

Not every competitive move requires response.
Overreaction wastes resources and distracts from roadmap.
Underreaction to structural shifts is existential risk.
Data-driven assessment prevents emotional responses.

### Strategic patience

Wait and monitor is a valid response.
Competitors announce; execution takes time.
Your customers' reactions matter more than competitor's announcements.

### Asymmetric advantage

Compete where the competitor is weak.
Find flanking opportunities they've created.
Their focus on X creates opening in Y.

## Transition

On completion:
- User can validate response with `/competitive-intelligence:validate`
- User can deep dive on competitor with `/competitive-intelligence:analyze`
- User can proceed to execution planning
