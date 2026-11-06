---
name: monitor
description: Tracks the changes in a competitive landscape since the last analysis and updates the intelligence. Use when the person asks "what's changed", wants a competitive update or a check of the competitors, or has a regular review (weekly, monthly or quarterly) or a planning session ahead.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(git rev-parse *), Bash(date *), Skill
---

# /competitive-intelligence:monitor

## Purpose

Perform ongoing competitive monitoring because markets evolve continuously and point-in-time analyses become stale without regular updates.

## Usage

```
/competitive-intelligence:monitor
/competitive-intelligence:monitor --since "2 weeks ago"
/competitive-intelligence:monitor --competitor "Competitor X"
```

## When to Use

- Regular competitive review cadence (weekly, monthly, quarterly)
- Before strategic planning sessions
- User says "what's changed", "competitive update", "check competitors"

## Process Overview

Monitoring uses a focused lens configuration optimized for change detection:

**Primary Lenses:**
- Loss/Churn (What's changing in win rates?)

**Secondary Lenses:**
- JTBD Performance (Are they improving?)
- Technology Disruption (Emerging threats?)
- Strategic Positioning (Major changes only)

## Command Implementation

```markdown
1. ORIENT:
   - Load previous analysis from both .competitive-intelligence/ and .competitive-intel/, newest file first
   - Determine last analysis date
   - Read a file of an earlier run through the graph: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> pages Run`, take the newest run whose `file_meta` names the file, and run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> view <RUN ID> <file name>`, because `ingest` moves the files of a run into the graph. Read a file that is still in a session folder directly.
   - Run `git rev-parse --show-toplevel` on its own (the output is the git root), and `date -u +%Y%m%dT%H%M%SZ` on its own (the output is `{session}`). Write each file of this run to `.competitive-intelligence/{session}/`.
   - Check for user-specified time range or competitors

2. DETERMINE MONITORING SCOPE:
   Ask user via AskUserQuestion:

   "What's your monitoring focus?"
   - Full Ecosystem (all competitors)
   - Priority Competitors (high threat only)
   - Specific Competitor (name it)

   "What time range?"
   - Since last analysis ({date})
   - Last 2 weeks
   - Last month
   - Last quarter
   - Custom range

3. CHANGE DETECTION SCAN:
   For each competitor in scope:

   A. News & Announcements:
      - Search: Recent news, blog posts, press releases
      - Flag: Product launches, pricing changes, partnerships
      - Assess: Significance of changes

   B. Product Changes:
      - Check: Feature updates, new capabilities
      - Compare: Against previous capability assessment
      - Flag: Improvements in job steps they were weak on

   C. Market Signals:
      - Check: Funding, acquisitions, leadership changes
      - Check: Customer wins/losses (public announcements)
      - Check: Review site rating changes

   D. Technology Shifts:
      - Check: AI/tech announcements
      - Check: Platform integrations
      - Flag: Disruption indicators

4. LOSS/CHURN DATA CHECK (if available):
   - Compare: Win rates vs previous period
   - Identify: New loss reasons appearing
   - Identify: Competitors gaining share
   - Flag: Significant trend changes

5. DELTA ANALYSIS:
   Compare current state to previous analysis:

   | Competitor | Previous | Current | Change | Significance |
   |------------|----------|---------|--------|--------------|
   | Comp A | Med Threat | High Threat | +1 | New feature |
   | Comp B | High Threat | High Threat | = | Stable |
   | Comp C | Low Threat | Med Threat | +1 | Funding |
   | New Entrant | N/A | Med Threat | New | Market entry |

6. SYNTHESIZE MONITORING REPORT:
   Generate monitoring summary:

   ## Significant Changes
   - {change 1 with impact assessment}
   - {change 2 with impact assessment}

   ## Threat Level Changes
   - Upgraded: {list}
   - Downgraded: {list}
   - New Entrants: {list}

   ## Recommended Actions
   - Immediate: {if any}
   - Near-term: {if any}
   - Watch: {if any}

   ## Data Gaps
   - {gaps needing investigation}

7. CHECKPOINT - Monitoring Review:
   Display to user:
   ```
   Competitive Monitoring Report
   Period: {start_date} to {end_date}

   Key Changes Detected:
   - {significant change 1}
   - {significant change 2}
   - {significant change 3}

   Threat Level Summary:
   - High Threat: {count} ({+/- from previous})
   - Medium Threat: {count} ({+/- from previous})
   - Low Threat: {count} ({+/- from previous})

   Recommended Actions:
   - {action 1}
   - {action 2}

   Deep dive on any changes?
   ```

8. UPDATE BASELINE:
   - Save monitoring snapshot to .competitive-intelligence/
   - Update last-monitored timestamp
   - Archive previous state for trend analysis

9. INGEST THE RUN:
   - Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root <git root> ingest .competitive-intelligence/{session}` on its own. `<git root>` is the output of `git rev-parse --show-toplevel`, run on its own.
   - When the output holds an `INIT:` line, show that line.
   - When the command exits 1, show its errors, say that the results stay in the session folder, and do not report success.
   - Else show the `ingested` line. Ask one question: "Learn these results?" On yes, run the skill `competitive-intelligence:learn` with `{session}`.
```

## Output Artifacts

- `.competitive-intelligence/{session}/monitoring-{date}.json` - Full monitoring data
- `.competitive-intelligence/{session}/changes-{date}.json` - Detected changes
- `.competitive-intelligence/monitoring-history/` - Historical snapshots

## Monitoring Cadence Recommendations

| Context | Recommended Cadence | Focus |
|---------|---------------------|-------|
| Fast-moving market | Weekly | All competitors |
| Stable market | Monthly | Priority competitors |
| Strategic planning | Quarterly | Full ecosystem refresh |
| Before major decision | Ad-hoc | Specific competitors |

## Change Significance Framework

```
                    ┌─────────────────┐
                    │  Detect Change  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         Product/       Market/         Internal
         Feature        Funding         Changes
              │              │              │
              ▼              ▼              ▼
         ┌────────┐    ┌────────┐    ┌────────┐
         │ Assess │    │ Assess │    │ Assess │
         │ JTBD   │    │Strategic│   │ Exec   │
         │ Impact │    │ Impact │    │ Impact │
         └────┬───┘    └────┬───┘    └────┬───┘
              │              │              │
              ▼              ▼              ▼
         High: They    High: Major    High: Key
         closed gap    funding/       departure
         on weakness   acquisition    /hire
              │              │              │
              └──────────────┴──────────────┘
                             │
                      Flag for Action
```

## Philosophy

### Continuous intelligence

One-time analysis decays rapidly.
Markets shift faster than planning cycles.
Regular monitoring catches changes early.
Small signals predict big moves.

### Signal and noise

Not every announcement matters.
Filter for changes that affect your customers.
Focus on capability changes, not marketing noise.
Validate with loss/churn data when possible.

### Actionable monitoring

Monitoring without action is waste.
Every report should have "so what?"
Clear thresholds for escalation.
Integrate with decision rhythms.

## Transition

On completion:
- User can deep dive: `/competitive-intelligence:analyze [competitor]`
- User can respond to change: `/competitive-intelligence:respond [change]`
- User can schedule next monitoring cycle
