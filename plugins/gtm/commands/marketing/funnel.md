---
description: Analyze and optimize TOFU demand generation — acquisition channels, content performance, and funnel entry health
allowed-tools: ["Read(*)", "Write(*)", "Agent", "Glob(*)", "Grep(*)", "WebSearch(*)", "AskUserQuestion(*)", "Bash(date *)", "Bash(git rev-parse *)", "Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py *)", "mcp__google-analytics__run_report", "mcp__google-analytics__get_realtime_data", "mcp__hubspot__hubspot_get_marketing_emails"]
---

# /gtm:marketing:funnel

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. The permission rule matches only that command line, so inline code (`python3 -c`, `node -e`, a heredoc) and scripts of your own fail. Write each file with the Write tool.
Run each agent you dispatch in the foreground and wait for it to finish, because the result file is written after the agent ends.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask for a number or free text in one chat message. Offer only options that are real values, because an option such as "Type amount" gives the person no value to pick.

## Purpose

Diagnose the health of top-of-funnel demand generation. This command pulls GA4 acquisition and conversion data, analyzes content performance and channel attribution, and identifies the single highest-leverage TOFU bottleneck. Use this command when you need to understand why leads are not converting to MQLs — not when you need full funnel analysis (use `/gtm:funnel` for that).

## Usage

```
/gtm:marketing:funnel
/gtm:marketing:funnel --channel organic    # focus on specific acquisition channel
/gtm:marketing:funnel --period 30d         # analysis window (default: 30d)
```

## Inputs

Ask only for an input the run does not have yet, one question at a time:

- AskUserQuestion [q: product_description]: "What does the product do, and who uses it?" A plugin run with no answer stops and writes its result file with the halt gap.
- AskUserQuestion [q: period]: "Over what window should the funnel be read, for example 30d?"
  - **Default:** `30d` when nobody answers.
- AskUserQuestion [q: visitors]: "How many visitors reached the site in that window?"
- AskUserQuestion [q: signups]: "How many of them signed up?"
- AskUserQuestion [q: activated]: "How many sign-ups reached the product's first value?"
- AskUserQuestion [q: mqls]: "How many leads met the MQL criteria in that window?"
- AskUserQuestion [q: channel_volumes]: "For each acquisition channel, how many visitors and MQLs did it bring in that window?"

A count nobody gives is not filled in: the transitions that need it are left out.

## Process

0. **Read the start time and the version** — run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep it as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. When a `date` call is denied or fails, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and use its output as that time. The result file needs both.

1. **Load `gtm-context.json` funnel metrics** — read existing funnel baseline data including MQL criteria, channel attribution model, and prior period benchmarks. If no baseline exists, prompt user for current session count and MQL volume to establish one.

2. **Pull GA4 conversion data** (if connected) — run `run_report` for the selected time period to retrieve:
   - Sessions by acquisition channel (organic, paid, direct, referral, social)
   - Session → signup conversion rates by channel
   - Signup → activation rates
   - Top landing pages by session volume and conversion rate
   - Geographic and device breakdowns

3. **Pull GA4 real-time data** (if connected) — run `get_realtime_data` to confirm current traffic levels and flag any anomalies (traffic spikes or drops vs. 7-day average).

4. **Pull HubSpot marketing email metrics** (if connected) — retrieve `hubspot_get_marketing_emails` to get open rates, click rates, and unsubscribe rates for active nurture sequences. Identify which email steps are losing contacts.

5. **Run bottleneck detector** — analyze the top-of-funnel funnel stages:
   ```
   Visitors → Signups → Activated → MQL
   ```
   The conversion rate of a transition is the count at the later stage divided by the count at the earlier stage; the primary bottleneck is the transition with the lowest rate. A drop greater than 50% relative to industry benchmarks is flagged as critical.

6. **Analyze content performance** — cross-reference landing page data from GA4 with content calendar (if `content-calendar.md` exists) to identify which content types and topics drive the highest session-to-signup conversion. Flag underperforming content.

7. **Analyze channel attribution** — compare CAC (cost per MQL) across channels. Identify channels that are over-funded relative to MQL output. Identify channels with high organic volume but low conversion (awareness channels vs. intent channels).

8. **Write `funnel-health.md`** — structured TOFU diagnosis report including:
   - Funnel snapshot: volume at each stage with conversion rates
   - Primary bottleneck: single identified constraint with confidence level
   - Channel performance: table of sessions, MQLs, and conversion rate per channel
   - Content performance: top 5 and bottom 5 pages by conversion rate
   - Recommendations: 3-5 prioritized actions to improve TOFU health
   - Benchmarks: comparison to SaaS industry medians where applicable

9. Pass `funnel-health.md` to integrity-agent before delivery — any benchmark statistics or industry claims must survive Truth Tier classification

10. **Write the result file** — Read `${CLAUDE_PLUGIN_ROOT}/agents/funnel-agent.md` with the Read tool and follow its `## Result file` section, in every run.

## Output Artifacts

- `funnel-health.md` — TOFU diagnosis with bottleneck analysis and recommendations
- Updates `gtm-context.json.funnel_metrics.tofu` with current period data

## When to Use vs. `/gtm:funnel`

| Use `/gtm:marketing:funnel` when... | Use `/gtm:funnel` when... |
|-------------------------------------|--------------------------|
| Diagnosing acquisition channel performance | Analyzing full MQL→SQL→SAL→Won flow |
| Content is not converting to leads | Sales is not accepting marketing leads |
| Organic or paid traffic is underperforming | Funnel handoff between marketing and sales is broken |
| Running a marketing-owned TOFU review | Running a revenue operations review |
